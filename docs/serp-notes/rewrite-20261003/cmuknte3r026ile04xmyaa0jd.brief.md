# 書き戻し指示書: result-kantou2025akiinkareyosen-2025

- candidateId: cmuknte3r026ile04xmyaa0jd / stage: diagnose45 / GSC28日: 表示38・クリック3・平均5.9位
- 対象ファイル: `yachtmania/content/articles/result-kantou2025akiinkareyosen-2025.md`
- SERPメモ: `yachtmania/docs/serp-notes/result-yacht-rewrite-20261003.md`（3本共通）
- 推定KW: 関東 秋インカレ ヨット 予選 結果 / 関東2025秋インカレ予選
- 方式: Sonnet単独で可。表の数値は公式PDFとの突合必須。決勝記事（cmuknte3x026kle040ehwguw9）と同時に作業し、相互リンクを張る

## 禁止事項
- 個人名（スキッパー・クルー）は書かない。大学名・順位・得点のみ
- `date` は変えない。意図（この大会の結果）は変えない
- 予選→決勝の進出枠・春インカレのシード・全日本インカレ出場枠は、関東学生ヨット連盟の要項や大学公式ニュース（当該年度分）で確認できた範囲だけ書き、出典を付ける。WebSearchで見つかった「春季上位8校が秋季のシード」「決勝上位8校が全日本へ」は過去年度の大学公式ページの記述で、2025年度の要項では未確認
- 成績PDFのファイル名は「速報」。表には「速報PDFに基づく」と明記し、確定版が連盟ページにあればそちらを正とする

## frontmatter
- title（案）: `関東秋インカレ予選2025（ヨット）結果｜470級・スナイプ級の大学別順位`
- description（案）: `関東2025秋インカレ予選（関東学生ヨット連盟）の結果を、470級・スナイプ級の大学別順位と得点で一覧にしました。決勝・全日本インカレとの関係と、公式成績PDFへのリンクもまとめています。`
- `cta: sponsor` を追記（現状 cta 行が無い）

## 本文（H2構成）
1. 冒頭2〜3文: 大会名・年度・関東水域。470級1位・スナイプ級1位の大学（パース値: 470級=横浜国立大学 86点、スナイプ級=中央大学 64点。PDF確認後に記載）
2. `## 関東秋インカレ予選とは` — 秋季の関東学生ヨット選手権が予選・決勝の2段階で行われること、団体戦（低得点方式）であること。進出枠は確認できた場合のみ
3. `## 470級の大学別順位` — 表「順位｜大学名｜得点」。データ元 `data/results_parsed/16844398522.json`（18校）
4. `## スナイプ級の大学別順位` — 同上。`16844398922.json`（14校）
5. `## 決勝とのつながり` — 予選で上位だった大学が [関東秋インカレ決勝の結果](../result-kantou2025akiinkarekesshou-2025/index.html) で何位だったかを、両データで確認できる事実のみ1段落（例: 予選470級1位校の決勝での順位）。評価的な言い回し（躍進・健闘等）は使わない
6. `## 公式成績PDF` — 既存2リンクを移す
7. `## よくある質問`（3問）
   - Q. 関東秋インカレの予選と決勝の違いは？ → 確認できた範囲で1〜2文＋[水域予選ガイド](../daigaku-yacht-suiiki-yosen-guide/index.html)
   - Q. 得点はどう見る？ → 低い得点ほど上位＋[観戦の見方](../daigaku-yacht-taikai-kansen-mikata/index.html)
   - Q. 470級とスナイプ級の違いは？ → [470級とスナイプ級の違い](../daigaku-yacht-470-snipe-chigai/index.html)
8. `## 関連リンク`
   - [関東水域 2025年度シーズン成績まとめ](../region-season-kanto-2025/index.html)
   - [関東秋インカレ決勝の結果](../result-kantou2025akiinkarekesshou-2025/index.html)
   - [全日本学生ヨット選手権の観戦ガイド](../zennihon-gakusei-yacht-senshuken-kansen-guide/index.html)
   - 大学別成績まとめ記事（実在確認済み）: `univ-results-yokohama-national-2025` / `univ-results-chuo-2025` / `univ-results-hosei-2025` / `univ-results-yokohama-city-2025` / `univ-results-tokyo-2025` / `univ-results-shibaura-it-2025` / `univ-results-chiba-2025` ほか（`../<slug>/index.html`）
   - 既存の関東水域ページ・成績PDF一覧は残す
9. `## 出典` — 既存の全日本学生ヨット連盟URL＋「順位・得点は速報PDFの記載をもとに編集部が整理」

## 目安
- 本文1,500〜2,500字。水増しはしない。ビルド成功を確認してから push
- 統合: 予選・決勝は別クエリで両方5位台のため**今は統合しない**（媒体側で年度横断の大会ハブを作る提案は報告済み）
