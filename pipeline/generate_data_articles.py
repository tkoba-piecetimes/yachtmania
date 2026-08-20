# -*- coding: utf-8 -*-
"""パース済み成績データ（data/results_parsed/*.json）から、LLMを使わずに
「大学別成績まとめ」「水域別シーズン総括」記事を生成する（Type Aの拡張）。

generate_articles.py（新着成績記事）の在庫が枯渇しても記事在庫を増やせるよう、
既に成功しているPDFパース結果（艇順位/大学名/得点、または大学別最終得点）を
再利用する。加盟大学紹介記事のような、大会成績の裏付けが無い記事は作らない
（generate_articles.py冒頭コメントの方針を踏襲）。

品質ゲート:
- 大学別: パース済み成績データに2大会以上登場する大学のみを対象にする。
- 水域別: パース済み大会（result-*記事の生成単位と同じ「大会」単位）が
  2件以上ある水域のみを対象にする。

個人情報の扱い: 艇長・クルー名は一切使わない（大学名・クラス・順位・得点のみ）。
ツナカレの協賛募集の個別情報（どの部活が募集中か等）も一切書かない。
CTA帯は既存のcta_band仕組み（generate_site.py）任せの汎用導線のみを使う。

slugは以下で決定的に生成し、既存slugは再生成しない（冪等）:
  大学別: univ-results-<大学スラッグ(university_slugs.slug_for)>-<年度>
  水域別: region-season-<水域コード>-<年度>

1回の呼び出しで生成する記事数は run(budget) の budget 引数で上限を制御する
（呼び出し元の generate_articles.py が新着成績記事の残り枠を渡す）。
大学別記事を水域別記事より優先する。
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regions import REGION_ORDER, REGIONS
from results_common import CONTENT, DATA, existing_slugs, group_by_tournament, load_results, year_num
from university_slugs import slug_for

PARSED_DIR = DATA / "results_parsed"

UNIV_MAX_ARTICLES_PER_RUN = 2
REGION_MAX_ARTICLES_PER_RUN = 1
MIN_TOURNAMENTS_UNIV = 2
MIN_TOURNAMENTS_REGION = 2
TOP_N_REGION_TABLE = 3

CATEGORY_UNIV = "大学別成績"
CATEGORY_REGION = "水域まとめ"

CLASS_ORDER = ["470級", "スナイプ級"]


def _class_key(cls: str) -> tuple:
    try:
        return (CLASS_ORDER.index(cls), cls)
    except ValueError:
        return (len(CLASS_ORDER), cls)


def _tournament_order_key(event_name: str) -> tuple:
    """予選→決勝の順に並ぶよう、ヒューリスティックに順序付ける（それ以外は名前順）。"""
    if "予選" in event_name:
        rank = 0
    elif "決勝" in event_name or "本戦" in event_name:
        rank = 1
    else:
        rank = 2
    return (rank, event_name)


def _dash(v: str) -> str:
    v = (v or "").strip()
    return v if v else "-"


# ---------------------------------------------------------------- data loading

def load_universities_by_name() -> dict:
    f = DATA / "universities.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text(encoding="utf-8"))
    return {u["name"]: u for u in data}


def _load_parsed(pdf_id: str):
    pf = PARSED_DIR / f"{pdf_id}.json"
    if not pf.exists():
        return None
    try:
        return json.loads(pf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def collect_university_appearances(groups: list) -> dict:
    """大学名 -> 出場記録（大会・クラスごと）のリスト。

    「大会」は group_by_tournament() が組み立てる単位（水域+年度+大会名）で、
    新着成績記事(result-*)と同じslugを共有する。
    """
    appearances: dict[str, list] = {}
    for g in groups:
        for p in g["pdfs"]:
            d = _load_parsed(p["id"])
            if not d:
                continue
            tier = d.get("tier")
            if tier == "boat":
                rows = [{"name": b.get("university", ""), "rank": b.get("team_rank", ""),
                         "score": b.get("team_score", "")} for b in d.get("boats", [])]
            elif tier == "summary":
                rows = [{"name": r.get("name", ""), "rank": r.get("rank", ""),
                         "score": r.get("score", "")} for r in d.get("rows", [])]
            else:
                rows = []
            seen = set()
            for r in rows:
                name = (r["name"] or "").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                appearances.setdefault(name, []).append({
                    "tournament_slug": g["slug"],
                    "region": g["region"],
                    "year_label": g["year_label"],
                    "event_name": g["event_name"],
                    "class": p["class"],
                    "pdf_id": p["id"],
                    "rank": r["rank"],
                    "score": r["score"],
                    "source": p.get("source", "全日本学生ヨット連盟"),
                    "source_url": p.get("source_url", ""),
                })
    return appearances


def top_n_from_parsed(pdf_id: str, n: int = 3) -> list:
    """1件のPDF（=1クラス分）の成績から、団体上位n校を (順位, 大学名, 得点) で返す。"""
    d = _load_parsed(pdf_id)
    if not d:
        return []
    tier = d.get("tier")
    if tier == "summary":
        rows = [(r.get("rank", ""), r.get("name", ""), r.get("score", ""))
                for r in d.get("rows", []) if (r.get("rank") or "").isdigit()]
        rows.sort(key=lambda r: int(r[0]))
        return rows[:n]
    if tier == "boat":
        seen = {}
        for b in d.get("boats", []):
            uni = (b.get("university") or "").strip()
            tr = (b.get("team_rank") or "").strip()
            if uni and tr.isdigit() and uni not in seen:
                seen[uni] = (int(tr), uni, b.get("team_score", ""))
        rows = sorted(seen.values(), key=lambda r: r[0])
        return [(str(r[0]), r[1], r[2]) for r in rows[:n]]
    return []


# ---------------------------------------------------------------- 大学別成績まとめ

def build_university_article(name: str, apps: list, univ_meta: dict | None, today: str) -> str:
    year = year_num(apps[0]["year_label"])
    region_code = apps[0]["region"]
    region_name = REGIONS.get(region_code, {}).get("name", region_code)

    # 大会（tournament_slug）ごとにグルーピングし、予選→決勝の順に並べる
    by_tournament: dict[str, list] = {}
    for a in apps:
        by_tournament.setdefault(a["tournament_slug"], []).append(a)
    tournaments = sorted(by_tournament.items(),
                          key=lambda kv: _tournament_order_key(kv[1][0]["event_name"]))

    classes = []
    for a in apps:
        if a["class"] not in classes:
            classes.append(a["class"])
    classes.sort(key=_class_key)
    class_str = "・".join(classes) if classes else "各クラス"
    n_tournaments = len(tournaments)

    title = f"{name}ヨット部 大会成績まとめ（{year}年度）"
    description = (f"{name}のヨット部が{year}年度に出場した大会の成績（順位・得点）をまとめています。"
                    f"{class_str}・全{n_tournaments}大会分の成績PDFを集計しました。")

    lines = [
        f"{name}が{year}年度に出場した大会の成績PDFのうち、パースできた分から順位・得点を"
        f"まとめました（{n_tournaments}大会・{class_str}）。",
        "",
        "## 大会成績",
        "",
        "| 大会 | クラス | 順位 | 得点 |",
        "| --- | --- | --- | --- |",
    ]
    detail_links = []
    sources = []
    for tslug, tapps in tournaments:
        tapps_sorted = sorted(tapps, key=lambda a: _class_key(a["class"]))
        event_name = tapps_sorted[0]["event_name"]
        for a in tapps_sorted:
            lines.append(f"| [{event_name}](../../articles/{tslug}/index.html) | {a['class']} | "
                         f"{_dash(a['rank'])} | {_dash(a['score'])} |")
            detail_links.append(
                f"- [{event_name} {a['class']}（成績詳細）](../../results/{a['pdf_id']}/index.html)")
            key = (a["source"], a["source_url"])
            if key not in sources:
                sources.append(key)

    lines += ["", "## 成績PDFの詳細", ""] + detail_links

    meta = univ_meta or {}
    if meta:
        lines += ["", f"## {name}について", ""]
        if meta.get("name_en"):
            lines.append(f"- 大学名（英字）: {meta['name_en']}")
        if meta.get("harbor"):
            lines.append(f"- 主な拠点・ハーバー: {meta['harbor']}")
        if meta.get("classes"):
            lines.append(f"- 登録クラス: {meta['classes']}")
        if meta.get("url"):
            lines.append(f"- 部の公式サイト: [{meta['url']}]({meta['url']})")

    lines += ["", "## 関連リンク", ""]
    if meta.get("slug"):
        lines.append(f"- [{name}のページへ](../../universities/{meta['slug']}/index.html)")
    lines += [
        f"- [{region_name}水域のページへ](../../regions/{region_code}/index.html)",
        "- [成績PDFリンク一覧はこちら](../../results/index.html)",
        "",
        "順位・得点は各大会の公式成績PDFの記載に基づく自動集計です。艇長・クルーなど個人の"
        "成績詳細は各大会の成績PDFをご確認ください。",
        "",
        "## 出典",
        "",
    ]
    for src_name, src_url in sources:
        lines.append(f"- [{src_name}]({src_url})" if src_url else f"- {src_name}")

    body = "\n".join(lines)
    fm = (f"title: {title}\n"
          f"description: {description}\n"
          f"date: {today}\n"
          f"category: {CATEGORY_UNIV}\n"
          f"cta: sponsor\n")
    return f"---\n{fm}---\n{body}\n"


# ---------------------------------------------------------------- 水域別シーズン総括

def build_region_article(region_code: str, groups_in_region: list, today: str) -> str:
    region = REGIONS.get(region_code, {})
    region_name = region.get("name", region_code)
    federation = region.get("federation", "")
    year = year_num(groups_in_region[0]["year_label"])
    ordered = sorted(groups_in_region, key=lambda g: _tournament_order_key(g["event_name"]))
    n_tournaments = len(ordered)

    title = f"{region_name}水域 {year}年度シーズン成績まとめ"
    description = (f"{region_name}水域（{federation}）の{year}年度大会成績をまとめています。"
                    f"パース済みの成績データがある{n_tournaments}大会の上位校を掲載しています。")

    lines = [
        f"{region_name}水域（{federation}）で{year}年度に開催され、成績PDFの表構造をパースできた"
        f"大会は{n_tournaments}件です。大会ごとの上位校（クラス別・上位{TOP_N_REGION_TABLE}校）をまとめました。",
        "",
        "## 大会一覧と上位校",
    ]
    sources = []
    for g in ordered:
        lines += ["", f"### {g['event_name']}（{g['year_label']}）", ""]
        lines.append("| クラス | 順位 | 大学名 | 得点 |")
        lines.append("| --- | --- | --- | --- |")
        classes_sorted = sorted(g["pdfs"], key=lambda p: _class_key(p["class"]))
        for p in classes_sorted:
            top = top_n_from_parsed(p["id"], TOP_N_REGION_TABLE)
            if not top:
                lines.append(f"| {p['class']} | - | データ未取得（[成績PDF]({p['url']})を参照） | - |")
            for rank, uni, score in top:
                lines.append(f"| {p['class']} | {rank} | {uni} | {_dash(score)} |")
            key = (p.get("source", "全日本学生ヨット連盟"), p.get("source_url", ""))
            if key not in sources:
                sources.append(key)
        lines.append("")
        lines.append(f"[{g['event_name']}の記事を読む](../../articles/{g['slug']}/index.html)")

    lines += [
        "",
        "## 関連リンク",
        "",
        f"- [{region_name}水域のページへ](../../regions/{region_code}/index.html)",
        "- [成績PDFリンク一覧はこちら](../../results/index.html)",
        "",
        "順位・得点は各大会の公式成績PDFの記載に基づく自動集計です。艇長・クルーなど個人の"
        "成績詳細は各大会の成績PDFをご確認ください。",
        "",
        "## 出典",
        "",
    ]
    for src_name, src_url in sources:
        lines.append(f"- [{src_name}]({src_url})" if src_url else f"- {src_name}")

    body = "\n".join(lines)
    fm = (f"title: {title}\n"
          f"description: {description}\n"
          f"date: {today}\n"
          f"category: {CATEGORY_REGION}\n"
          f"cta: sponsor\n")
    return f"---\n{fm}---\n{body}\n"


# ---------------------------------------------------------------- candidates

def build_univ_candidates(groups: list, existing: set) -> list:
    appearances = collect_university_appearances(groups)
    univ_meta = load_universities_by_name()
    candidates = []
    for name, apps in appearances.items():
        tset = sorted(set(a["tournament_slug"] for a in apps))
        if len(tset) < MIN_TOURNAMENTS_UNIV:
            continue
        year = year_num(apps[0]["year_label"])
        slug = f"univ-results-{slug_for(name)}-{year}"
        if slug in existing:
            continue
        candidates.append((name, apps, univ_meta.get(name), slug))
    candidates.sort(key=lambda c: c[0])  # 大学名で決定的に並べる
    return candidates


def build_region_candidates(groups: list, existing: set) -> list:
    by_region: dict[str, list] = {}
    for g in groups:
        by_region.setdefault(g["region"], []).append(g)
    candidates = []
    for code, gs in by_region.items():
        if len(gs) < MIN_TOURNAMENTS_REGION:
            continue
        year = year_num(gs[0]["year_label"])
        slug = f"region-season-{code}-{year}"
        if slug in existing:
            continue
        candidates.append((code, gs, slug))

    def sort_key(c):
        try:
            return REGION_ORDER.index(c[0])
        except ValueError:
            return 999
    candidates.sort(key=sort_key)
    return candidates


# ---------------------------------------------------------------- entry point

def run(budget: int) -> list:
    """大学別（優先）→水域別の順に、budget件まで記事を生成してslugのリストを返す。"""
    if budget <= 0:
        return []
    results = load_results()
    if not results:
        return []
    groups = group_by_tournament(results)
    existing = existing_slugs()
    today = date.today().isoformat()

    CONTENT.mkdir(parents=True, exist_ok=True)
    generated = []

    univ_candidates = build_univ_candidates(groups, existing)
    n_univ = min(UNIV_MAX_ARTICLES_PER_RUN, budget, len(univ_candidates))
    for name, apps, meta, slug in univ_candidates[:n_univ]:
        text = build_university_article(name, apps, meta, today)
        (CONTENT / f"{slug}.md").write_text(text, encoding="utf-8")
        generated.append(slug)

    budget_left = budget - len(generated)
    if budget_left > 0:
        # 大学別で使った枠を差し引いた上で existing を更新（同一実行内での二重生成防止）
        existing = existing | set(generated)
        region_candidates = build_region_candidates(groups, existing)
        n_region = min(REGION_MAX_ARTICLES_PER_RUN, budget_left, len(region_candidates))
        for code, gs, slug in region_candidates[:n_region]:
            text = build_region_article(code, gs, today)
            (CONTENT / f"{slug}.md").write_text(text, encoding="utf-8")
            generated.append(slug)

    return generated


if __name__ == "__main__":
    n = run(UNIV_MAX_ARTICLES_PER_RUN + REGION_MAX_ARTICLES_PER_RUN)
    if not n:
        print("大学別・水域別: 生成対象なし（品質ゲート未達 or 生成済み）")
    for s in n:
        print(f"  + {s}.md")
