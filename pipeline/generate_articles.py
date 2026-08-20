# -*- coding: utf-8 -*-
"""data/results_pdfs.json から新着成績PDFを検知し、大会単位で記事(content/articles/*.md)を生成する。

Type A: 「新着成績記事」（本ファイル）に加えて、パース済み成績データ
（data/results_parsed/*.json）に基づく「大学別成績まとめ」「水域別シーズン
総括」記事（generate_data_articles.py）も同じ実行の中で生成する。加盟大学
紹介記事のような、大会成績の裏付けがまったく無い記事は引き続き作らない
（低品質な記事の量産を避けるための方針判断）。大学別・水域別記事は必ず
パース済み成績データ（艇順位/大学名/得点など実データ）にひもづけて生成する。

生成単位: 大会（同一大会名でクラス別のPDFをまとめる）ごとに1記事。
大会名はPDFファイル名から、クラス名（470級/スナイプ級等）・年度の付番・
「成績」「速報」等の定型語を取り除いて抽出する（ヒューリスティック。LLMは使わない）。
このグルーピングロジックは results_common.py に切り出してあり、
generate_data_articles.py と共有する。

slugは `result-<大会名のローマ字スラッグ>-<年度>` で決定的に生成し、
既に同じslugの記事があれば再生成しない（＝重複記事を作らない）。

1回の実行で生成する記事数は、新着成績・大学別・水域別の合計で
TOTAL_MAX_ARTICLES_PER_RUN 件まで（優先順: 新着成績 > 大学別 > 水域別）。
毎日の成績PDF巡回（fetch_all.py → fetch_pdf_results.py）→本スクリプト→
generate_site.py の順で実行することで、新着があった翌朝に記事化される。
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regions import REGION_ORDER, REGIONS
from results_common import CONTENT, existing_slugs, group_by_tournament, load_results, year_num

MAX_ARTICLES_PER_RUN = 2  # 新着成績記事の1回の実行での生成上限
TOTAL_MAX_ARTICLES_PER_RUN = 3  # 新着成績+大学別+水域別の合計上限（1日の記事増加ペースを抑える）
CATEGORY = "新着成績"


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
          f"category: {CATEGORY}\n"
          f"cta: sponsor\n")
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

    # 新着成績記事で使い切らなかった分の枠を、大学別・水域別記事に回す
    # （優先順: 新着成績 > 大学別 > 水域別。合計で TOTAL_MAX_ARTICLES_PER_RUN 件まで）。
    remaining_budget = max(0, TOTAL_MAX_ARTICLES_PER_RUN - len(generated))
    if remaining_budget > 0:
        from generate_data_articles import run as run_data_articles
        extra = run_data_articles(remaining_budget)
        for s in extra:
            print(f"  + {s}.md")
    else:
        extra = []

    print(f"合計生成: {len(generated) + len(extra)}件"
          f"（新着成績{len(generated)}件 / 大学別・水域別{len(extra)}件）")


if __name__ == "__main__":
    main()
