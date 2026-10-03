# 書き戻し指示書: result-kantou2025akiinkarekesshou-2025

- candidateId: cmuknte3x026kle040ehwguw9 / stage: diagnose45 / GSC28日: 表示23・クリック1・平均5.4位
- 対象ファイル: `yachtmania/content/articles/result-kantou2025akiinkarekesshou-2025.md`
- SERPメモ: `yachtmania/docs/serp-notes/result-yacht-rewrite-20261003.md`（3本共通）
- 推定KW: 関東インカレ 決勝 ヨット 2025 結果 / 関東秋インカレ 決勝
- 方式: Sonnet単独で可。予選記事（cmuknte3r026ile04xmyaa0jd）と同時作業・相互リンク

## 禁止事項
- 個人名は書かない。大学名・順位・得点のみ
- `date` は変えない。意図は変えない
- 全日本インカレ出場枠（例:「決勝上位8校」）は2025年度分を関東学生ヨット連盟の要項または大学公式ニュースで確認できた場合のみ、出典付きで書く。確認できなければ「上位校が全日本インカレへ進む」程度にも言い切らず、[水域予選ガイド](../daigaku-yacht-suiiki-yosen-guide/index.html) への誘導に留める
- 「速報PDFに基づく」と明記。確定版があればそちらを正とする

## frontmatter
- title（案）: `関東秋インカレ決勝2025（ヨット）結果｜470級・スナイプ級の大学別順位`
- description（案）: `関東2025秋インカレ決勝（関東学生ヨット連盟）の結果を、470級・スナイプ級の大学別順位と得点で一覧にしました。予選の結果、全日本インカレとのつながり、公式成績PDFもまとめています。`
- `cta: sponsor` を追記

## 本文（H2構成）
1. 冒頭2〜3文: 両クラスの1位校（パース値: 470級=日本大学 134点、スナイプ級=日本大学 139点。PDF確認後に記載）
2. `## 関東秋インカレ決勝とは` — 予選と決勝の2段階、団体戦（低得点方式）。出場枠は確認できた範囲のみ
3. `## 470級の大学別順位` — 表。データ元 `data/results_parsed/16844398022.json`（15校）
4. `## スナイプ級の大学別順位` — 表。`16844398722.json`（15校）
5. `## 全日本インカレへのつながり` — 一次情報で確認できた範囲のみ＋[全日本学生ヨット選手権の観戦ガイド](../zennihon-gakusei-yacht-senshuken-kansen-guide/index.html)
6. `## 予選からの流れ` — [関東秋インカレ予選の結果](../result-kantou2025akiinkareyosen-2025/index.html) へリンクし、予選上位校の決勝順位をデータで確認できる事実のみ1段落
7. `## 公式成績PDF` — 既存2リンクを移す
8. `## よくある質問`（3問）: 予選と決勝の違い／得点の見方（[観戦の見方](../daigaku-yacht-taikai-kansen-mikata/index.html)）／470級とスナイプ級の違い（[470級とスナイプ級の違い](../daigaku-yacht-470-snipe-chigai/index.html)）
9. `## 関連リンク`
   - [関東水域 2025年度シーズン成績まとめ](../region-season-kanto-2025/index.html)
   - 決勝出場校の大学ページ（実在確認済み）: `../../universities/nihon/index.html`、`waseda`、`keio`、`meiji`、`tokyo-tech`、`chuo`、`meikai`、`tokyo`、`rikkyo`、`hosei`、`yokohama-city`、`yokohama-national`、`hitotsubashi`、`tokyo-noko`、`seikei`、`aoyama-gakuin`、`chiba`、`shibaura-it`、`kogakuin`（表の大学名から張るか、関連リンクに主要校のみ）
   - 東京科学大学のページslugは `tokyo-tech`（旧東工大）であることを確認してからリンク
10. `## 出典` — 既存URL＋「速報PDFの記載をもとに編集部が整理」

## 目安
- 本文1,500〜2,500字。ビルド成功を確認してから push
