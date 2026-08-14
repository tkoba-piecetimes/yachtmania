# -*- coding: utf-8 -*-
"""data/results_pdfs.json から新着成績PDFを検知し、大会単位で記事(content/articles/*.md)を生成する。

Type A: 新着成績記事のみを生成する。加盟大学紹介記事などデータが薄くなる記事は
意図的に作らない（低品質な記事の量産を避けるための方針判断。fetch元は成績PDFの
リンクのみで、大学ごとの戦績集計や個別コメントが取れないため）。

生成単位: 大会（同一大会名でクラス別のPDFをまとめる）ごとに1記事。
大会名はPDFファイル名から、クラス名（470級/スナイプ級等）・年度の付番・
「成績」「速報」等の定型語を取り除いて抽出する（ヒューリスティック。LLMは使わない）。

slugは `result-<大会名のローマ字スラッグ>-<年度>` で決定的に生成し、
既に同じslugの記事があれば再生成しない（＝重複記事を作らない）。

1回の実行で生成するのは最大2記事（未生成の中で検知日が新しい大会から順に）。
毎日の成績PDF巡回（fetch_all.py）→本スクリプト→generate_site.py の順で実行することで、
新着があった翌朝に記事化される。
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regions import REGION_ORDER, REGIONS

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTENT = ROOT / "content" / "articles"

MAX_ARTICLES_PER_RUN = 2  # 1回の実行での生成上限
CATEGORY = "新着成績"

# ---------------------------------------------------------------- 大会名抽出

# クラス名トークン（長い表記を先に置く。「級」は470_級のように区切られる表記の
# 取りこぼしを拾うための最終フォールバック）
CLASS_TOKEN_RE = re.compile(r"(スナイプ級|470級|スナイプ|Snipe|SNIPE|snipe|470|級)")
# 「成績」「速報」等、大会名の一部ではない定型語（ファイル名中どこにあっても除去）
NOISE_WORD_RE = re.compile(r"(最終成績|団体戦成績|団体成績|成績表|成績|速報|団体戦|団体)")
IDX_SUFFIX_RE = re.compile(r"\s*\(\d+\)\s*$")          # "...(1)" のような重複回避の付番
DATE_SUFFIX_RE = re.compile(r"_?\d{4}_?\d{2}_?\d{2}$")  # "..._2025_10_05" のような末尾日付
TRAIL_BRACKET_RE = re.compile(r"[（(][^）)]{0,10}[）)]\s*$")  # 末尾の短い括弧注記（団体）等


def normalize_event_name(filename: str) -> str:
    """成績PDFのファイル名から「大会名」を抽出するヒューリスティック。

    例:
      【九州インカレ団体戦】スナイプ級最終成績.pdf → 九州インカレ
      【九州インカレ団体戦】470級最終成績.pdf     → 九州インカレ （↑と同じ大会名でまとまる）
      2025年度　関西学生ヨット選手権　snipe.pdf   → 2025年度 関西学生ヨット選手権
    """
    s = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    s = IDX_SUFFIX_RE.sub("", s)
    s = DATE_SUFFIX_RE.sub("", s)
    s = CLASS_TOKEN_RE.sub("", s)
    s = NOISE_WORD_RE.sub("", s)
    while True:
        stripped = TRAIL_BRACKET_RE.sub("", s).strip()
        if stripped == s:
            break
        s = stripped
    s = s.replace("＿", "").replace("_", "")
    s = s.replace("【", "").replace("】", "")
    s = re.sub(r"[\s　]+", " ", s)
    s = s.strip(" -ー_")
    return s or "大会成績"


_kks = None


def romaji_slug(name: str) -> str | None:
    """大会名 → ローマ字スラッグ（大学スラッグと同じくpykakasiを使用、ハッシュにはフォールバックしない）。"""
    global _kks
    try:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        s = "".join(x["hepburn"] for x in _kks.convert(name))
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        if len(s) > 40:
            cut = s[:40].rsplit("-", 1)[0]
            s = cut if len(cut) >= 10 else s[:40]
        return s or None
    except Exception as e:
        print(f"[warn] ローマ字化失敗: {name} ({e})", file=sys.stderr)
        return None


def year_num(year_label: str) -> str:
    m = re.search(r"\d{4}", year_label or "")
    return m.group(0) if m else "0000"


# ---------------------------------------------------------------- data loading

def load_results():
    f = DATA / "results_pdfs.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8"))


def existing_slugs() -> set[str]:
    if not CONTENT.exists():
        return set()
    return {f.stem for f in CONTENT.glob("*.md")}


def group_by_tournament(results):
    groups: dict[tuple, list] = {}
    for r in results:
        stem = normalize_event_name(r["filename"])
        key = (r.get("region", ""), r.get("year_label", ""), stem)
        groups.setdefault(key, []).append(r)

    out = []
    for (region, year_label, event_name), pdfs in groups.items():
        pdfs_sorted = sorted(pdfs, key=lambda p: (p["class"], p["filename"]))
        detected_at = max(p["first_detected_at"] for p in pdfs)
        slug_base = romaji_slug(event_name) or f"g{abs(hash(event_name)) % 10**8}"
        out.append({
            "region": region,
            "year_label": year_label,
            "event_name": event_name,
            "pdfs": pdfs_sorted,
            "detected_at": detected_at,
            "slug": f"result-{slug_base}-{year_num(year_label)}",
        })
    return out


# ---------------------------------------------------------------- article body

def build_article(g: dict) -> str:
    region = REGIONS.get(g["region"], {})
    region_name = region.get("name", g["region"])
    year = year_num(g["year_label"])
    event_name = g["event_name"]

    classes = []
    for p in g["pdfs"]:
        if p["class"] not in classes:
            classes.append(p["class"])
    class_str = "・".join(classes) if classes else "各クラス"

    title = f"{event_name}の成績が公開されました（{year}年度）"
    description = (f"{event_name}（{region_name}水域）の成績PDFが公開されました。"
                    f"{class_str}の成績PDFへのリンクをまとめています。")

    sources = []
    for p in g["pdfs"]:
        key = (p.get("source", "全日本学生ヨット連盟"), p.get("source_url", ""))
        if key not in sources:
            sources.append(key)

    lines = [
        f"{event_name}（{region_name}水域）の成績PDFが、全日本学生ヨット連盟の水域大会成績ページで"
        f"確認できます。{g['year_label']}の大会成績です。",
        "",
        "## 成績PDFリンク",
        "",
    ]
    for p in g["pdfs"]:
        lines.append(f"- **{p['class']}**: [{p['filename']}]({p['url']})")
    lines += [
        "",
        "## 関連リンク",
        "",
        f"- [{region_name}水域のページへ](../../regions/{g['region']}/index.html)",
        "- [成績PDFリンク一覧はこちら](../../results/index.html)",
        "",
        "詳細な順位は上記の公式成績PDFをご確認ください。",
        "",
        "## 出典",
        "",
    ]
    for name, url in sources:
        lines.append(f"- [{name}]({url})" if url else f"- {name}")

    body = "\n".join(lines)
    fm = (f"title: {title}\n"
          f"description: {description}\n"
          f"date: {g['detected_at']}\n"
          f"category: {CATEGORY}\n")
    return f"---\n{fm}---\n{body}\n"


# ---------------------------------------------------------------- main

def main():
    results = load_results()
    if not results:
        print("成績PDFデータがありません（fetch_all.pyを先に実行）")
        return

    groups = group_by_tournament(results)
    existing = existing_slugs()
    candidates = [g for g in groups if g["slug"] not in existing]

    def sort_key(g):
        try:
            region_idx = REGION_ORDER.index(g["region"])
        except ValueError:
            region_idx = 999
        try:
            d = date.fromisoformat(g["detected_at"])
        except (TypeError, ValueError):
            d = date.min
        return (-d.toordinal(), region_idx, g["event_name"])

    candidates.sort(key=sort_key)
    to_generate = candidates[:MAX_ARTICLES_PER_RUN]

    CONTENT.mkdir(parents=True, exist_ok=True)
    generated = []
    for g in to_generate:
        (CONTENT / f"{g['slug']}.md").write_text(build_article(g), encoding="utf-8")
        generated.append(g["slug"])

    print(f"大会単位のストック: {len(groups)}件中 既存記事 {len(existing & {g['slug'] for g in groups})}件 "
          f"/ 今回生成 {len(generated)}件 / 未生成の残り "
          f"{len(groups) - len(existing & {g['slug'] for g in groups}) - len(generated)}件")
    for s in generated:
        print(f"  + {s}.md")


if __name__ == "__main__":
    main()
