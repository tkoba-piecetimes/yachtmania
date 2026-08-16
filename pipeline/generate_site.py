# -*- coding: utf-8 -*-
"""data/ の正規化JSONから静的サイト「ヨットマニア」（site/）を生成する。

MVPスコープ: 大学ディレクトリ＋大会カレンダー＋成績PDFリンク集。
成績PDFはpipeline/fetch_pdf_results.pyが表構造の解析を試み、成功した分は
site/results/<id>/ にページ内表示用の結果ページを生成する（艇順位・大学名・
得点など）。レイアウトの都合で解析できなかった分は、従来どおりPDFへの
直リンクのみを掲載する。

URL構造:
  site/index.html                      トップ（新着成績PDF＋直近大会カレンダー）
  site/regions/index.html              水域一覧
  site/regions/<code>/index.html       水域ページ（関東・近畿北陸は大学ディレクトリ付き）
  site/universities/<slug>/index.html  大学ページ
  site/calendar/index.html             大会カレンダー全件
  site/results/index.html              成績PDFリンク全件
  site/results/<id>/index.html         成績ページ（表構造の解析に成功した分のみ）
  site/articles/ 等                    全水域共通コンテンツ（現状は空でも動作する）
"""
import json
import re
import shutil
import sys
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regions import REGION_ORDER, REGIONS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content" / "articles"

SITE_BASE = "https://yachtmania.jp/"
GA_MEASUREMENT_ID = "G-SMC597ZSPZ"  # GA4「ヨットマニア」専用プロパティ（550004558）
GSC_VERIFICATION = "0X77J6-cDQak8VJkyt1PGegqMjZwEI2HWAYjkwl3OF0"  # Search Console所有権確認トークン（アカウント共通）

NEW_WITHIN_DAYS = 14  # 「新着成績」として表示する検知日からの日数

# ---------------------------------------------------------------- ツナカレ接続導線
# 設計: crm/docs/部活メディア_ツナカレ接続設計_2026-08.md（D1〜D5）

TUNAKARE_UTM_SOURCE = "yachtmania"

TUNAKARE_BASE = {
    "sponsor_top": "https://tunakare.jp/",
    "listing_lp": "https://lp.tunakare.jp/s01/",
    "media_contact": "https://media.tunakare.jp/contact/student/",
    "shukatsu": "https://shukatsu.tunakare.jp/",
    "career": "https://career.tunakare.jp/",
}


def tunakare_url(base_url: str, campaign: str) -> str:
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}utm_source={TUNAKARE_UTM_SOURCE}&utm_medium=referral&utm_campaign={campaign}"


def tunakare_link(url: str, label: str, cv_event: str, cls: str = "cta") -> str:
    return (f'<a class="{cls}" href="{escape(url)}" target="_blank" rel="noopener sponsored" '
            f"onclick=\"window.gtag&&gtag('event','{cv_event}')\">{escape(label)}</a>")


SPONSOR_CTA_URL = tunakare_url(TUNAKARE_BASE["sponsor_top"], "sponsor")


def build_sponsor_block(*, heading="この部を応援する") -> str:
    """D2改訂版: チームページ（本サイトではハブ型MVPのため大学ページ）の応援ブロック。

    全チーム共通の汎用3導線を表示する。個別部活への協賛ページ直リンク・団体名表示は
    行わない（募集中の部活はツナカレに遷移して初めてわかる設計。案件には締切・停止が
    あり静的サイト側に募集状況を持つと管理不能になるため）。
    """
    body = f'<section class="sponsor"><h2>{escape(heading)} <span class="pr-badge">PR</span></h2>'
    sponsor_top = tunakare_url(TUNAKARE_BASE["sponsor_top"], "sponsor")
    listing_url = tunakare_url(TUNAKARE_BASE["listing_lp"], "listing")
    body += (f'<p>この部活・競技を応援したい方へ: '
             f'{tunakare_link(sponsor_top, "ツナカレで協賛募集中の部活を探す →", "cv_sponsor_click")}</p>'
             f'<p class="note">掲載をご希望の部活関係者の方へ: '
             f'{tunakare_link(listing_url, "協賛募集を無料で掲載する →", "cv_listing_click", cls="cta cta-alt")}</p>')
    media_url = tunakare_url(TUNAKARE_BASE["media_contact"], "media-pr")
    body += (f'<p class="note">取材してほしい部活を募集中: '
             f'{tunakare_link(media_url, "取材を依頼する →", "cv_media_pr_click", cls="cta cta-alt")}</p>')
    body += '</section>'
    return body


# D3: 記事frontmatterの cta 値ごとのCTA帯
CTA_BANDS = {
    "shukatsu": {
        "heading": "部活と就活の両立、ひとりで悩まない",
        "text": "体育会学生向けの無料就活相談。文武両道の悩みを相談できます。",
        "label": "無料で相談する →",
        "base": "shukatsu",
        "campaign": "shukatsu",
        "cv": "cv_shukatsu_click",
    },
    "career": {
        "heading": "体育会出身の転職・キャリアを考える",
        "text": "競技経験を活かしたキャリア相談。OB・OGの転職支援を行っています。",
        "label": "キャリア相談を見る →",
        "base": "career",
        "campaign": "career",
        "cv": "cv_career_click",
    },
    "listing": {
        "heading": "遠征費・運営資金でお困りの部活の方へ",
        "text": "協賛募集の掲載は無料。30万円のオープン協賛枠も用意されています。",
        "label": "協賛募集を無料で掲載する →",
        "base": "listing_lp",
        "campaign": "listing",
        "cv": "cv_listing_click",
    },
    "sponsor": {
        "heading": "この部活・競技を応援したい方へ",
        "text": "体育会学生を支援するプラットフォーム「ツナカレ」で、応援できる部活を探せます。",
        "label": "応援できる部活を探す →",
        "base": "sponsor_top",
        "campaign": "sponsor",
        "cv": "cv_sponsor_click",
    },
}


def cta_band(cta_value: str | None) -> str:
    cfg = CTA_BANDS.get((cta_value or "").strip())
    if not cfg:
        return ""
    url = tunakare_url(TUNAKARE_BASE[cfg["base"]], cfg["campaign"])
    return ('<section class="cta-band">'
            f'<p class="pr-badge">PR</p><h2>{escape(cfg["heading"])}</h2>'
            f'<p>{escape(cfg["text"])}</p>'
            f'<p>{tunakare_link(url, cfg["label"], cfg["cv"])}</p></section>')

_sitemap_paths: list[str] = []


# ---------------------------------------------------------------- data loading

def load_json(name, default):
    f = DATA / name
    if not f.exists():
        return default
    return json.loads(f.read_text(encoding="utf-8"))


PARSED_DIR = DATA / "results_parsed"


def load_data():
    universities = load_json("universities.json", [])
    calendar = load_json("calendar.json", [])
    results = load_json("results_pdfs.json", [])
    schedule_pdfs = load_json("schedule_pdfs.json", [])
    meta = load_json("meta.json", {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                                    "sources": []})

    for r in results:
        r["has_detail"] = (PARSED_DIR / f"{r['id']}.json").exists()

    by_region: dict[str, list] = {code: [] for code in REGION_ORDER}
    for u in universities:
        by_region.setdefault(u["region"], []).append(u)
    for code in by_region:
        by_region[code].sort(key=lambda u: u["name"])

    results_by_region: dict[str, list] = {code: [] for code in REGION_ORDER}
    for r in results:
        results_by_region.setdefault(r.get("region") or "", []).append(r)
    for code in results_by_region:
        results_by_region[code].sort(key=lambda r: (r["first_detected_at"], r["filename"]), reverse=True)

    results_sorted = sorted(results, key=lambda r: (r["first_detected_at"], r["id"]), reverse=True)

    return {
        "universities": universities,
        "by_region": by_region,
        "calendar": calendar,
        "results": results_sorted,
        "results_by_region": results_by_region,
        "schedule_pdfs": schedule_pdfs,
        "meta": meta,
    }


def load_articles():
    if not CONTENT.exists():
        return []
    arts = []
    for f in sorted(CONTENT.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        if raw.count("---") < 2:
            continue
        _, fm, body = raw.split("---", 2)
        a = {"slug": f.stem, "body": body.strip()}
        for line in fm.strip().splitlines():
            k, _, v = line.partition(":")
            a[k.strip()] = v.strip()
        arts.append(a)
    arts.sort(key=lambda a: (a.get("date", ""), a["slug"]), reverse=True)
    return arts


# ---------------------------------------------------------------- text helpers

def is_new(first_detected_at: str) -> bool:
    try:
        d = date.fromisoformat(first_detected_at)
    except (TypeError, ValueError):
        return False
    return (date.today() - d).days <= NEW_WITHIN_DAYS


def date_jp(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return iso or ""
    return f"{d.year}年{d.month}月{d.day}日"


def md_inline(s):
    s = escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def md_to_html(md):
    out, para = [], []
    in_ul = in_ol = in_table = False

    def close_blocks():
        nonlocal in_ul, in_ol, in_table
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []

    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            flush_para()
            if in_ul or in_ol:
                close_blocks()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r"[-: ]+", c) for c in cells):
                continue
            if not in_table:
                out.append('<div class="tbl"><table><thead><tr>'
                           + "".join(f"<th>{md_inline(c)}</th>" for c in cells)
                           + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False
        if not s:
            flush_para()
            close_blocks()
        elif s.startswith("### "):
            flush_para(); close_blocks()
            out.append(f"<h3>{md_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_para(); close_blocks()
            out.append(f"<h2>{md_inline(s[3:])}</h2>")
        elif s.startswith("- "):
            flush_para()
            if not in_ul:
                close_blocks()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{md_inline(s[2:])}</li>")
        elif re.match(r"^\d+\.\s", s):
            flush_para()
            if not in_ol:
                close_blocks()
                out.append("<ol>")
                in_ol = True
            item = re.sub(r"^\d+\.\s", "", s)
            out.append(f"<li>{md_inline(item)}</li>")
        else:
            para.append(s)
    flush_para()
    close_blocks()
    return "\n".join(out)


# ---------------------------------------------------------------- page shell

NAV_ITEMS = [
    ("index.html", "トップ"),
    ("regions/index.html", "水域一覧"),
    ("calendar/index.html", "大会カレンダー"),
    ("results/index.html", "成績PDF"),
]


def page(rel, title, body, meta, *, path="", desc="", extra_head="", og_type="website",
         subnav="", sitemap=True):
    if sitemap:
        _sitemap_paths.append(path)
    else:
        extra_head = '<meta name="robots" content="noindex, nofollow">\n' + extra_head
    desc = desc or "大学ヨット部の加盟大学ディレクトリ・大会カレンダー・成績PDFリンクをまとめる情報メディア。"
    url = SITE_BASE + path
    og_image = ""
    if (ASSETS / "ogp.png").exists():
        og_image = (f'<meta property="og:image" content="{SITE_BASE}assets/ogp.png">\n'
                    '<meta name="twitter:card" content="summary_large_image">\n')
    ga = ""
    if GA_MEASUREMENT_ID:
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>'
              '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
              f"gtag('js',new Date());gtag('config','{GA_MEASUREMENT_ID}');</script>")
    gsc = (f'<meta name="google-site-verification" content="{GSC_VERIFICATION}">\n'
           if GSC_VERIFICATION else "")
    nav = "".join(f'<a href="{rel}{href}">{label}</a>' for href, label in NAV_ITEMS)
    if "sources" in meta:
        src_html = " / ".join(
            f'<a href="{escape(s["url"])}">{escape(s["label"])}</a>' for s in meta["sources"])
    else:
        src_html = ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{gsc}<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{escape(url)}">
<meta property="og:site_name" content="ヨットマニア">
{og_image}<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="canonical" href="{escape(url)}">
{extra_head}{ga}
<link rel="stylesheet" href="{rel}style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{rel}index.html"><span class="brand-tick"></span>ヨットマニア<span class="brand-sub">JAPAN COLLEGE YACHT</span></a>
    <nav class="global-nav">{nav}</nav>
  </div>
</header>
{subnav}
<main>
{body}
</main>
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-brand">ヨットマニア</p>
    <nav class="footer-nav">{nav}</nav>
    <p>データ出典: {src_html}
    （情報更新日: {escape(meta['fetched_at'][:10])}）</p>
    <p>ヨットマニアは大学ヨット部の情報メディアです。大会成績は公式PDFの表構造を元に掲載しており、
    レイアウトの都合で表として読み取れなかった分はPDFへのリンクのみを掲載しています。
    確定情報は必ず各成績PDFおよび各連盟公式の発表をご確認ください。</p>
  </div>
</footer>
</body>
</html>"""


def write_page(path, html):
    out = SITE / path / "index.html" if path else SITE / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- components

def univ_link(u, rel):
    return f'<a href="{rel}universities/{u["slug"]}/index.html">{escape(u["name"])}</a>'


def region_link(code, rel):
    r = REGIONS[code]
    return f'<a href="{rel}regions/{code}/index.html">{escape(r["name"])}水域</a>'


def pdf_row(p, rel, show_region=False):
    badge = '<span class="new-badge">NEW</span> ' if is_new(p["first_detected_at"]) else ""
    region_cell = (f'<td><span class="cat">{escape(REGIONS.get(p["region"], {}).get("name", p.get("region_label", "")))}</span></td>'
                   if show_region else "")
    if p.get("has_detail"):
        link = (f'<a href="{rel}results/{p["id"]}/index.html">{escape(p["filename"])}</a> '
                f'<a class="note" href="{escape(p["url"])}" target="_blank" rel="noopener">(元のPDF)</a>')
    else:
        link = f'<a href="{escape(p["url"])}" target="_blank" rel="noopener">{escape(p["filename"])}</a>'
    return (f'<tr><td>{badge}{link}</td>{region_cell}'
            f'<td><span class="cat cat-alt">{escape(p["class"])}</span></td>'
            f'<td class="note">{escape(p["year_label"])}</td>'
            f'<td class="note">{escape(date_jp(p["first_detected_at"]))}</td></tr>')


def pdf_table(rows, show_region=False):
    region_th = "<th>水域</th>" if show_region else ""
    return (f'<div class="tbl"><table><thead><tr><th>成績PDF</th>{region_th}<th>クラス</th>'
            '<th>年度</th><th>検知日</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def render_boat_table(parsed):
    """tier=boat（艇ごとの個人戦形式）の結果テーブル。"""
    heads = ["艇順位", "Sail#", "大学名", "艇長", "クルー"] + parsed.get("race_labels", []) \
        + ["合計", "得点", "順位", "団体得点", "団体順位"]
    thead = "".join(f"<th>{escape(h)}</th>" for h in heads)
    rows = []
    for b in parsed["boats"]:
        cells = ([b["rank"], b["sail_no"], b["university"], b["skipper"], b["crew"]]
                 + b["races"] + [b["total"], b["boat_score"], b["boat_rank"], b["team_score"], b["team_rank"]])
        rows.append("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")
    return f'<div class="tbl"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def render_summary_table(parsed):
    """tier=summary（大学ごとの最終得点・順位のみ）の結果テーブル。"""
    thead = (f'<th>{escape(parsed["rank_label"])}</th><th>大学名</th><th>Sail#/No</th>'
             f'<th>{escape(parsed["score_label"])}</th>')
    rows = []
    for r in parsed["rows"]:
        cells = [r["rank"], r["name"], r["sail_no"], r["score"]]
        rows.append("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")
    return f'<div class="tbl"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def render_extra_table(rows):
    """レース日・天候・レースオフィサー等の補助テーブル（見出し行なしでそのまま表示）。"""
    body = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="tbl"><table><tbody>{body}</tbody></table></div>'


def calendar_row(e, rel, show_region=True):
    date_cell = escape(e["date_text"]) if e["date_text"] else '<span class="note">日程は大会情報ページを参照</span>'
    region_cell = ""
    if show_region:
        region_cell = (f'<td>{region_link(e["region"], rel)}</td>' if e.get("region")
                       else '<td><span class="note">全国</span></td>')
    return (f'<tr><td>{date_cell}</td>{region_cell}'
            f'<td><a href="{escape(e["source_url"])}" target="_blank" rel="noopener">{escape(e["event"])}</a></td></tr>')


def calendar_table(rows, show_region=True):
    region_th = "<th>水域</th>" if show_region else ""
    return (f'<div class="tbl"><table><thead><tr><th>日程</th>{region_th}<th>大会</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def article_card(a, rel):
    return (f'<div class="digest-card"><p class="cat-line"><span class="cat">{escape(a["category"])}</span>'
            f' <span class="note">{escape(a["date"])}</span></p>'
            f'<h3><a href="{rel}articles/{a["slug"]}/index.html">{escape(a["title"])}</a></h3>'
            f'<p class="note">{escape(a["description"])}</p></div>')


# ---------------------------------------------------------------- portal

def build_portal(data, articles):
    rel = ""
    meta = data["meta"]
    univ_count = len(data["universities"])
    pdf_count = len(data["results"])
    new_pdfs = [p for p in data["results"] if is_new(p["first_detected_at"])][:15]
    region_names = "・".join(REGIONS[c]["name"] for c in REGION_ORDER)

    body = ('<div class="hero">'
            '<img class="hero-img" src="assets/hero.jpg" alt="" width="1440" height="810">'
            '<div class="hero-text">'
            '<p class="hero-kicker">全国9水域の大学ヨット</p>'
            '<h1>大学ヨット部の加盟大学・大会カレンダー・成績PDFをまとめて探せる</h1>'
            f'<p class="hero-sub">加盟大学{univ_count}校・成績PDFリンク{pdf_count}件を毎日巡回・検知　|　'
            f'最終更新 {escape(meta["fetched_at"][:10])}</p>'
            '</div></div>')

    body += ('<section><h2>新着成績PDF</h2>'
             '<p class="lead">全日本学生ヨット連盟の水域大会成績ページで新しく公開された成績PDFへの'
             'リンクをまとめています。表として読み取れた分はページ内で艇順位・大学名・得点を確認できます。</p>')
    if new_pdfs:
        body += pdf_table("".join(pdf_row(p, rel, show_region=True) for p in new_pdfs), show_region=True)
    else:
        body += '<p class="note">直近の新着はありません。</p>'
    body += '<p class="more"><a class="cta" href="results/index.html">成績PDFリンク一覧をすべて見る →</a></p></section>'

    body += '<section><h2>直近の大会カレンダー</h2>'
    cal = data["calendar"][:12]
    if cal:
        body += calendar_table("".join(calendar_row(e, rel) for e in cal))
    else:
        body += '<p class="note">現在表示できる大会日程はありません。近畿北陸学生ヨット連盟の年間予定と全国大会情報のページは'
        body += '<a href="calendar/index.html">大会カレンダー</a>からご確認いただけます。</p>'
    body += '<p class="more"><a class="cta" href="calendar/index.html">大会カレンダーをすべて見る →</a></p></section>'

    body += f'<section><h2>水域から探す</h2><p class="lead">{escape(region_names)}の9水域。</p><div class="digest">'
    for code in REGION_ORDER:
        r = REGIONS[code]
        n_univ = len(data["by_region"].get(code, []))
        n_pdf = len(data["results_by_region"].get(code, []))
        dir_note = f'大学ディレクトリ {n_univ}校' if r["has_directory"] else '大学ディレクトリ 未掲載'
        body += (f'<div class="digest-card"><h3><a href="regions/{code}/index.html">{escape(r["name"])}水域</a></h3>'
                 f'<p class="cat-line"><span class="cat">{escape(dir_note)}</span> '
                 f'<span class="cat">成績PDF {n_pdf}件</span></p></div>')
    body += '</div></section>'

    sponsor_top = tunakare_url(TUNAKARE_BASE["sponsor_top"], "sponsor")
    listing_url = tunakare_url(TUNAKARE_BASE["listing_lp"], "listing")
    media_url = tunakare_url(TUNAKARE_BASE["media_contact"], "media-pr")
    body += ('<section class="support"><h2>ヨットマニアと部活を応援する <span class="pr-badge">PR</span></h2>'
             '<p class="lead">体育会学生を支援するプラットフォーム「ツナカレ」への接続導線です。</p>'
             '<div class="support-cards">'
             '<div class="digest-card"><h3>部活を応援する</h3>'
             '<p class="note">協賛・応援ができる部活を探せます。</p>'
             f'<p>{tunakare_link(sponsor_top, "応援できる部活を探す →", "cv_sponsor_click")}</p></div>'
             '<div class="digest-card"><h3>無料で掲載する</h3>'
             '<p class="note">部活の関係者の方へ。協賛募集ページを無料で掲載できます。</p>'
             f'<p>{tunakare_link(listing_url, "協賛募集を掲載する →", "cv_listing_click", cls="cta cta-alt")}</p></div>'
             '<div class="digest-card"><h3>取材募集</h3>'
             '<p class="note">取材してほしい部活を募集しています。</p>'
             f'<p>{tunakare_link(media_url, "取材を依頼する →", "cv_media_pr_click", cls="cta cta-alt")}</p></div>'
             '</div></section>')

    if articles:
        body += ('<section><h2>読みもの</h2><div class="digest">'
                 + "".join(article_card(a, rel) for a in articles[:3])
                 + '</div><p class="more"><a class="cta" href="articles/index.html">読みもの一覧へ →</a></p></section>')

    write_page("", page(rel, "ヨットマニア | 大学ヨットの加盟大学・大会カレンダー・成績PDF", body, meta,
                        path="",
                        desc=f"{region_names}の大学ヨット部の加盟大学ディレクトリ・大会カレンダー・"
                             "成績PDFリンクを毎日更新。"))


# ---------------------------------------------------------------- regions

def build_regions_index(data):
    rel = "../"
    meta = data["meta"]
    body = ('<h1>水域一覧</h1>'
            '<p class="lead">日本の大学ヨットは全国9水域の学生連盟が大会を運営しています。'
            '大学ディレクトリを公式サイト（HTML）から取得できた水域は関東・近畿北陸の2水域です。'
            'それ以外の水域は、全日本学生ヨット連盟の水域大会成績ページから取得した大会結果リンクのみを掲載しています。</p>')
    cards = ""
    for code in REGION_ORDER:
        r = REGIONS[code]
        n_univ = len(data["by_region"].get(code, []))
        n_pdf = len(data["results_by_region"].get(code, []))
        dir_note = f'大学ディレクトリ {n_univ}校' if r["has_directory"] else '大学ディレクトリ 未掲載'
        cards += (f'<div class="digest-card"><h3><a href="{rel}regions/{code}/index.html">{escape(r["name"])}水域</a></h3>'
                  f'<p class="note">{escape(r["federation"])}</p>'
                  f'<p class="cat-line"><span class="cat">{escape(dir_note)}</span> '
                  f'<span class="cat">成績PDF {n_pdf}件</span></p></div>')
    body += f'<div class="digest">{cards}</div>'
    write_page("regions", page(rel, "水域一覧 | ヨットマニア", body, meta,
                               path="regions/", desc="全国9水域の大学ヨット連盟一覧。大学ディレクトリと大会結果リンク。"))


def build_region(code, data):
    r = REGIONS[code]
    meta = data["meta"]
    rel = R = L = "../../"
    univs = data["by_region"].get(code, [])
    pdfs = data["results_by_region"].get(code, [])
    cal = [e for e in data["calendar"] if e.get("region") == code]

    body = (f'<p class="breadcrumb"><a href="{R}index.html">トップ</a> › '
            f'<a href="{R}regions/index.html">水域一覧</a> › {escape(r["name"])}水域</p>')
    body += f'<h1>{escape(r["name"])}水域の大学ヨット</h1>'
    body += (f'<p class="lead">運営連盟: '
             + (f'<a href="{escape(r["federation_url"])}" target="_blank" rel="noopener">{escape(r["federation"])}</a>'
                if r["federation_url"] else escape(r["federation"]))
             + '</p>')
    if r["note"]:
        body += f'<p class="note">{escape(r["note"])}</p>'

    if r["has_directory"] and univs:
        body += f'<section><h2>加盟大学ディレクトリ（{len(univs)}校）</h2><ul class="team-list">'
        body += "".join(f'<li>{univ_link(u, L)}</li>' for u in univs)
        body += '</ul></section>'
    else:
        body += ('<section><h2>加盟大学ディレクトリ</h2>'
                 '<p class="note">この水域の加盟大学一覧はまだ掲載できていません'
                 '（公式サイトの大学一覧ページが見つからない、または全日本学連の加盟校名簿がPDF・Excel形式でしか'
                 '配布されていないためです）。掲載できる水域は今後増やしていく予定です。大会成績PDFは全水域で掲載しています。</p></section>')

    if cal:
        body += '<section><h2>大会カレンダー</h2>' + calendar_table("".join(calendar_row(e, L, show_region=False) for e in cal), show_region=False) + '</section>'

    body += '<section><h2>大会成績PDFリンク</h2>'
    if pdfs:
        body += ('<p class="note">全日本学生ヨット連盟の水域大会成績ページに掲載されている成績PDFです。'
                 '表として読み取れた分はページ内で結果を確認できます。</p>')
        body += pdf_table("".join(pdf_row(p, L) for p in pdfs))
    else:
        body += '<p class="note">この水域の成績PDFはまだ検知されていません。</p>'
    body += '</section>'

    body += build_sponsor_block(heading=f'{r["name"]}水域の部活を応援する')

    title = f'{r["name"]}水域の大学ヨット 加盟大学・大会成績 | ヨットマニア'
    write_page(f"regions/{code}",
               page(rel, title, body, meta,
                    path=f"regions/{code}/",
                    desc=f'{r["name"]}水域の大学ヨット部。加盟大学ディレクトリと大会成績PDFリンクをまとめています。'))


# ---------------------------------------------------------------- universities

def build_universities(data):
    meta = data["meta"]
    rel, R = "../../", "../../"
    for u in data["universities"]:
        code = u["region"]
        r = REGIONS[code]
        pdfs = data["results_by_region"].get(code, [])
        body = (f'<p class="breadcrumb"><a href="{R}index.html">トップ</a> › '
                f'<a href="{R}regions/{code}/index.html">{escape(r["name"])}水域</a> › {escape(u["name"])}</p>')
        body += f'<h1>{escape(u["name"])}</h1>'
        if u.get("name_en"):
            body += f'<p class="lead">{escape(u["name_en"])} ／ {escape(r["name"])}水域（{escape(r["federation"])}）</p>'
        else:
            body += f'<p class="lead">{escape(r["name"])}水域（{escape(r["federation"])}）</p>'

        if u.get("classes") or u.get("harbor"):
            body += '<section><h2>基本情報</h2><div class="stat-row">'
            if u.get("classes"):
                body += f'<div class="stat"><span class="num">{escape(u["classes"])}</span>出場クラス</div>'
            if u.get("harbor"):
                body += f'<div class="stat"><span class="num">{escape(u["harbor"])}</span>練習拠点</div>'
            body += '</div></section>'

        if u.get("url"):
            body += (f'<section><h2>公式サイト</h2><p><a class="cta" href="{escape(u["url"])}" '
                     f'target="_blank" rel="noopener">{escape(u["name"])} 公式サイトへ →</a></p></section>')

        body += ('<section><h2>大会成績</h2>'
                 '<p class="note">個別大学ごとの戦績データは現時点では集計していません。'
                 f'{escape(r["name"])}水域全体の大会成績PDFリンクから、この大学の名前で検索してご確認ください。</p>')
        if pdfs:
            body += pdf_table("".join(pdf_row(p, R) for p in pdfs[:10]))
            body += (f'<p class="more"><a href="{R}regions/{code}/index.html">'
                     f'{escape(r["name"])}水域の成績PDF一覧へ →</a></p>')
        body += '</section>'

        body += build_sponsor_block()

        write_page(f"universities/{u['slug']}",
                   page(rel, f'{u["name"]} ヨット部 | ヨットマニア', body, meta,
                        path=f"universities/{u['slug']}/",
                        desc=f'{u["name"]}ヨット部。{r["name"]}水域所属。大会成績PDFリンクへの導線。'))


# ---------------------------------------------------------------- calendar / results (全件)

def build_calendar_page(data):
    rel = "../"
    meta = data["meta"]
    body = ('<h1>大会カレンダー</h1>'
            '<p class="lead">近畿北陸学生ヨット連盟の年間予定と、全日本学生ヨット選手権・個人選手権・'
            '女子選手権の最新の大会情報ページへのリンクです。日付は各連盟の発表表記のまま掲載しています。</p>')
    if data["calendar"]:
        body += calendar_table("".join(calendar_row(e, rel) for e in data["calendar"]))
    else:
        body += '<p class="note">現在表示できる大会日程はありません。</p>'
    if data["schedule_pdfs"]:
        body += '<section><h2>全国水域別スケジュール（PDF）</h2><ul>'
        for p in data["schedule_pdfs"]:
            body += f'<li><a href="{escape(p["url"])}" target="_blank" rel="noopener">{escape(p["filename"])}</a></li>'
        body += '</ul></section>'
    write_page("calendar", page(rel, "大会カレンダー | ヨットマニア", body, meta,
                                path="calendar/", desc="大学ヨットの大会日程をまとめたカレンダー。"))


def build_results_page(data):
    rel = "../"
    meta = data["meta"]
    pdf_count = len(data["results"])
    body = ('<h1>成績PDFリンク一覧</h1>'
            '<p class="lead">全日本学生ヨット連盟の水域大会成績ページに掲載されている、'
            f'成績PDF{pdf_count}件です。表として読み取れた分はページ内で艇順位・大学名・得点を確認できます。'
            'レイアウトの都合で読み取れなかった分はPDFへの直リンクのみを掲載しています。</p>')
    for code in REGION_ORDER:
        pdfs = data["results_by_region"].get(code, [])
        if not pdfs:
            continue
        r = REGIONS[code]
        body += f'<section><h2>{escape(r["name"])}水域（{len(pdfs)}件）</h2>'
        body += pdf_table("".join(pdf_row(p, rel) for p in pdfs))
        body += '</section>'
    write_page("results", page(rel, "成績PDFリンク一覧 | ヨットマニア", body, meta,
                               path="results/", desc="大学ヨットの大会成績PDFへのリンク一覧。水域別に毎日更新。"))


def build_result_detail(p, data):
    """成績PDFの表構造の解析に成功した分のページ内結果表示（site/results/<id>/）。"""
    rel = "../../"
    meta = data["meta"]
    parsed = json.loads((PARSED_DIR / f"{p['id']}.json").read_text(encoding="utf-8"))
    region_name = REGIONS.get(p["region"], {}).get("name", p.get("region_label", ""))

    body = (f'<p class="breadcrumb"><a href="{rel}index.html">トップ</a> › '
            f'<a href="{rel}results/index.html">成績PDFリンク一覧</a> › {escape(p["filename"])}</p>')
    body += f'<h1>{escape(p["filename"])}</h1>'
    body += (f'<p class="lead">{escape(p.get("region_label", region_name))} ／ {escape(p["class"])} ／ '
             f'{escape(p["year_label"])}（出典: {escape(p["source"])}）</p>')
    body += (f'<p class="note">検知日: {escape(date_jp(p["first_detected_at"]))} ／ '
             f'<a href="{escape(p["url"])}" target="_blank" rel="noopener">元のPDFを見る →</a></p>')

    if parsed["tier"] == "boat":
        body += '<section><h2>大会結果</h2>' + render_boat_table(parsed) + '</section>'
        extras = parsed.get("extra_tables") or []
        if extras:
            body += '<section><h2>レース情報</h2>'
            body += "".join(render_extra_table(t) for t in extras)
            body += '</section>'
    else:
        body += ('<section><h2>大会結果（大学別）</h2>'
                 '<p class="note">レースごとの内訳までは表として読み取れなかったため、'
                 '大学ごとの最終得点・順位のみを掲載しています。詳細は元のPDFをご確認ください。</p>')
        body += render_summary_table(parsed) + '</section>'

    body += build_sponsor_block(heading=f'{region_name}水域の部活を応援する')

    write_page(f"results/{p['id']}",
               page(rel, f'{p["filename"]} 大会結果 | ヨットマニア', body, meta,
                    path=f"results/{p['id']}/",
                    desc=f'{p["filename"]}（{p["class"]}・{p["year_label"]}）の大会結果ページ。'))


# ---------------------------------------------------------------- global pages

def build_articles(articles, meta):
    if not articles:
        return
    rel = "../"
    cards = "".join(article_card(a, rel) for a in articles)
    body = ('<h1>読みもの</h1>'
            '<p class="lead">大学ヨットの現場で使える知見をまとめています。</p>'
            f'<div class="digest">{cards}</div>')
    write_page("articles",
               page(rel, "読みもの | ヨットマニア", body, meta,
                    path="articles/", desc="大学ヨットに関する記事一覧。"))
    rel = "../../"
    for a in articles:
        others = [x for x in articles if x["slug"] != a["slug"]][:3]
        related = "".join(
            f'<li><a href="../{x["slug"]}/index.html">{escape(x["title"])}</a></li>'
            for x in others)
        body = (f'<p class="breadcrumb"><a href="{rel}index.html">トップ</a> › '
                f'<a href="{rel}articles/index.html">読みもの</a> › {escape(a["category"])}</p>')
        body += (f'<p class="cat-line"><span class="cat">{escape(a["category"])}</span>'
                 f' <span class="note">{escape(a["date"])}</span></p>')
        body += f'<h1>{escape(a["title"])}</h1>'
        body += f'<div class="article">{md_to_html(a["body"])}</div>'
        body += cta_band(a.get("cta"))
        if related:
            body += f'<section><h2>あわせて読む</h2><ul>{related}</ul></section>'
        write_page(f"articles/{a['slug']}",
                   page(rel, f'{a["title"]} | ヨットマニア', body, meta,
                        path=f'articles/{a["slug"]}/', desc=a.get("description", ""), og_type="article"))


DASHBOARD_PATH = "dash-ym-ops"  # 非公開運用ダッシュボード（noindex・sitemap非掲載）


def build_dashboard(data, articles, meta):
    rel = "../"
    today = date.today()

    body = ('<h1>運営ダッシュボード</h1>'
            f'<p class="lead">ヨットマニアの定点観測。毎朝の自動更新で最新化されます。'
            f'ビルド: {today.isoformat()} / データ取得: {escape(meta["fetched_at"][:16].replace("T", " "))}</p>')

    new_pdfs = sum(1 for p in data["results"] if is_new(p["first_detected_at"]))
    body += ('<section><h2>サイト全体</h2><div class="stat-row">'
             f'<div class="stat"><span class="num">{len(_sitemap_paths)}</span>公開ページ</div>'
             f'<div class="stat"><span class="num">{len(REGION_ORDER)}</span>水域</div>'
             f'<div class="stat"><span class="num">{len(data["universities"])}</span>加盟大学</div>'
             f'<div class="stat"><span class="num">{len(data["results"])}</span>成績PDFリンク</div>'
             f'<div class="stat"><span class="num">{new_pdfs}</span>直近{NEW_WITHIN_DAYS}日の新着</div>'
             '</div></section>')

    mfile = DATA / "metrics.json"
    if mfile.exists():
        mx = json.loads(mfile.read_text(encoding="utf-8"))
        ga = mx.get("ga", {})
        gsc = mx.get("gsc", {})
        body += (f'<section><h2>リリース後の実績（{escape(mx.get("release_date", ""))}〜）</h2>'
                 '<div class="stat-row">'
                 f'<div class="stat"><span class="num">{ga.get("total_users", "—")}</span>ユーザー</div>'
                 f'<div class="stat"><span class="num">{ga.get("total_pageviews", "—")}</span>ページビュー</div>'
                 f'<div class="stat"><span class="num">{gsc.get("total_clicks", "—")}</span>検索クリック</div>'
                 '</div>'
                 f'<p class="note">最終取得: {escape(mx.get("updated_at", ""))}</p></section>')
    else:
        body += ('<section><h2>リリース後の実績</h2>'
                 '<p class="note">GA4/Search Console 未連携。連携が完了すると数値が表示されます。</p></section>')

    rows = ""
    for code in REGION_ORDER:
        r = REGIONS[code]
        n_univ = len(data["by_region"].get(code, []))
        n_pdf = len(data["results_by_region"].get(code, []))
        rows += (f'<tr><td><a href="{rel}regions/{code}/index.html">{escape(r["name"])}水域</a></td>'
                 f'<td>{"○" if r["has_directory"] else "—"}</td><td>{n_univ}</td><td>{n_pdf}</td></tr>')
    body += ('<section><h2>水域別の状況</h2>'
             '<div class="tbl"><table><thead><tr><th>水域</th><th>ディレクトリ</th>'
             '<th>加盟大学</th><th>成績PDF</th></tr></thead>'
             f'<tbody>{rows}</tbody></table></div></section>')

    body += ('<section><h2>外部ツール（クリックで開く）</h2><ul>'
             '<li><a href="https://search.google.com/search-console">Search Console</a></li>'
             '<li><a href="https://analytics.google.com/">GA4</a></li>'
             '</ul></section>')

    write_page(DASHBOARD_PATH,
               page(rel, "運営ダッシュボード | ヨットマニア", body, meta,
                    path=f"{DASHBOARD_PATH}/", desc="運営用の内部ダッシュボード。",
                    sitemap=False))


# ---------------------------------------------------------------- misc output

def write_sitemap_and_robots():
    today = date.today().isoformat()
    urls = "".join(
        f"<url><loc>{SITE_BASE}{p}</loc><lastmod>{today}</lastmod></url>"
        for p in _sitemap_paths)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + urls + "</urlset>", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_BASE}sitemap.xml\n", encoding="utf-8")


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#071a33"/>
<path d="M32 10 L32 40" stroke="#1e88a8" stroke-width="3"/>
<path d="M32 14 L46 38 L32 34 Z" fill="#ffffff"/>
<path d="M18 44 Q32 52 46 44 L42 50 Q32 56 22 50 Z" fill="#1e88a8"/>
</svg>
"""

STYLE = """
:root {
  --navy:#071a33; --navy-2:#1d3a63; --accent:#1e88a8; --accent-dark:#166a84;
  --accent-soft:#e3f2f6; --ink:#0f1f33; --sub:#5b6b7b; --line:#dfe5ec;
  --bg:#f8f8f6; --surface:#fff;
}
* { box-sizing:border-box; }
body { margin:0; font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;
  color:var(--ink); background:var(--bg); line-height:1.7; }
a { color:var(--navy-2); }
a:hover { color:var(--accent-dark); }

.site-header { background:var(--surface); border-bottom:1px solid var(--line); }
.header-inner { max-width:960px; margin:0 auto; padding:.7rem 1rem .5rem;
  display:flex; flex-wrap:wrap; align-items:center; gap:.3rem 1.5rem; }
.brand { display:flex; align-items:baseline; gap:.5rem; font-weight:800;
  color:var(--navy); text-decoration:none; font-size:1.25rem; letter-spacing:.02em; }
.brand-tick { width:.55em; height:.55em; background:var(--accent);
  border-radius:2px; align-self:center; }
.brand-sub { font-size:.6rem; color:var(--accent); font-weight:700; letter-spacing:.15em;
  text-transform:uppercase; }
.global-nav { display:flex; gap:.2rem; overflow-x:auto; margin-left:auto; }
.global-nav a { color:var(--navy); text-decoration:none; font-size:.85rem; font-weight:600;
  padding:.35em .7em; border-radius:6px; white-space:nowrap;
  border-bottom:2px solid transparent; }
.global-nav a:hover { border-bottom-color:var(--accent); }

.hero { max-width:960px; margin:0 auto; padding:1.6rem 1rem 0; }
.hero-img { width:100%; height:auto; display:block; border-radius:12px; margin-bottom:1.1rem; }
.hero-text { padding-bottom:1.8rem; }
.hero-kicker { color:var(--accent); font-weight:700; font-size:.85rem;
  letter-spacing:.2em; text-transform:uppercase; margin:0 0 .4rem; }
.hero h1 { font-size:1.5rem; line-height:1.45; margin:0 0 .6rem; color:var(--navy);
  font-weight:900; }
.hero-sub { color:var(--sub); font-size:.85rem; margin:0; }

main { max-width:960px; margin:0 auto; padding:0 1rem 3rem; }
h1 { font-size:1.35rem; line-height:1.45; }
h2 { font-size:1.08rem; border-left:4px solid var(--accent); padding-left:.55em;
  margin-top:2.4em; color:var(--navy); }
h3 { font-size:.95rem; margin-top:1.6em; }

.tbl { overflow-x:auto; background:var(--surface); border:1px solid var(--line);
  border-radius:12px; box-shadow:0 1px 3px rgba(7,26,51,.06); }
table { width:100%; border-collapse:collapse; font-size:.85rem; }
th, td { border-bottom:1px solid var(--line); padding:.5em .7em; text-align:left;
  white-space:nowrap; }
tbody tr:last-child td { border-bottom:none; }
thead th { background:var(--navy); color:#fff; font-weight:600; font-size:.78rem; }
tbody tr:nth-child(even) { background:var(--bg); }
tbody tr:hover { background:var(--accent-soft); }
td.note { color:var(--sub); font-size:.78rem; }
.cat { background:var(--accent-soft); color:var(--navy-2); font-size:.72rem; font-weight:700;
  padding:.15em .5em; border-radius:999px; }
.cat-alt { background:#e7ecf3; color:var(--navy-2); }
.new-badge { display:inline-block; background:var(--accent); color:#fff; font-size:.68rem;
  font-weight:800; padding:.1em .45em; border-radius:5px; letter-spacing:.03em; }

.breadcrumb { font-size:.8rem; color:var(--sub); margin-top:1rem; }
.breadcrumb a { color:var(--sub); }
.lead { color:var(--sub); }
.note { color:var(--sub); font-size:.8rem; }
.more { margin:.9rem 0 0; }
.cta { display:inline-block; background:var(--accent); color:var(--navy); font-weight:700;
  font-size:.85rem; text-decoration:none; padding:.5em 1.1em; border-radius:8px; }
.cta:hover { background:var(--accent-dark); color:#fff; }

.stat-row { display:flex; gap:.8rem; flex-wrap:wrap; }
.stat { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:.7rem 1.1rem; font-size:.75rem; color:var(--sub); min-width:100px;
  text-align:center; box-shadow:0 1px 3px rgba(7,26,51,.06); }
.stat .num { display:block; font-size:1.25rem; font-weight:800; color:var(--navy); }

.digest { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));
  gap:1rem; }
.digest-card { background:var(--surface); border:1px solid var(--line);
  border-radius:12px; padding:.9rem 1rem 1rem; box-shadow:0 1px 3px rgba(7,26,51,.06); }
.digest-card h3 { margin:.1em 0 .6em; }
.digest-card h3 a { text-decoration:none; color:var(--navy); }
.digest-card h3 a:hover { color:var(--accent-dark); }
.digest-card .tbl { border:none; box-shadow:none; }
.team-list { list-style:none; margin:0; padding:0; columns:2; font-size:.9rem; }
.team-list li { margin:.25em 0; break-inside:avoid; }

.sponsor .todo { color:var(--sub); background:var(--surface);
  border:1px dashed var(--line); border-radius:12px; padding:.8rem; font-size:.85rem; }

.pr-badge { display:inline-block; background:#166a8422; color:var(--accent-dark);
  font-size:.62rem; font-weight:800; padding:.12em .5em; border-radius:5px;
  letter-spacing:.05em; vertical-align:middle; margin-left:.3em; }
.cta.cta-alt { background:transparent; border:1px solid var(--accent-dark);
  color:var(--accent-dark); }
.cta.cta-alt:hover { background:var(--accent); color:#fff; border-color:var(--accent); }
.cta-band { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:1.1rem 1.3rem 1.3rem; margin-top:2.2rem; box-shadow:0 1px 3px rgba(7,26,51,.06); }
.cta-band h2 { margin-top:.3em; border:none; padding-left:0; }
.cta-band .pr-badge { margin-left:0; }
.support-cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));
  gap:1rem; }

.cat-line { font-size:.8rem; margin:.4rem 0; }
.article { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:1.4rem 1.6rem 1.6rem; box-shadow:0 1px 3px rgba(7,26,51,.06); }
.article h2 { margin-top:1.8em; }
.article h2:first-child { margin-top:.4em; }
.article li { margin:.3em 0; }

.site-footer { background:var(--navy); color:#a9c8db; font-size:.75rem;
  margin-top:3rem; }
.footer-inner { max-width:960px; margin:0 auto; padding:1.4rem 1rem 2rem; }
.footer-brand { color:#fff; font-weight:800; font-size:.95rem; margin:0 0 .3rem; }
.footer-nav { display:flex; gap:1rem; margin:.2rem 0 .8rem; flex-wrap:wrap; }
.footer-nav a { color:#cfe4ee; text-decoration:none; }
.site-footer a { color:#cfe4ee; }
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    _sitemap_paths.clear()

    data = load_data()
    articles = load_articles()
    if not data["universities"]:
        raise SystemExit("大学データがありません（fetch_all.pyを先に実行）")

    (SITE / "style.css").write_text(STYLE, encoding="utf-8")
    (SITE / "assets").mkdir()
    (SITE / "assets" / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    if ASSETS.exists():
        for f in ASSETS.iterdir():
            shutil.copy(f, SITE / "assets" / f.name)

    build_portal(data, articles)
    build_regions_index(data)
    for code in REGION_ORDER:
        build_region(code, data)
    build_universities(data)
    build_calendar_page(data)
    build_results_page(data)
    for p in data["results"]:
        if p.get("has_detail"):
            build_result_detail(p, data)
    build_articles(articles, data["meta"])
    build_dashboard(data, articles, data["meta"])
    write_sitemap_and_robots()

    print(f"OK: {len(_sitemap_paths)} pages "
          f"({len(REGION_ORDER)} regions, {len(data['universities'])} universities) in {SITE}")


if __name__ == "__main__":
    main()
