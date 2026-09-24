# SERP分析メモ: 「ヨット部がある大学 一覧」/「大学 ヨット部 一覧」

調査日: 2026-09-24
担当: ハイブリッド方式（設計・仕上げ=opus／本文=sonnet）
対象記事スラッグ: `daigaku-yacht-bu-ichiran-suiiki`
クエリ類型: 進路系（H群・K1／H17相当。keyword-inventory.md K1「全国9水域 大学ヨット部 加盟大学一覧まとめ」）

## 0. KW差し替えの経緯（重要）

当初の指示KWは keyword-inventory.md の H1「大学ヨット部 強豪」だったが、同KWは
`content/articles/daigaku-yacht-bu-kyougou.md`（2026-09-16公開、SERPメモも
`docs/serp-notes/daigaku-yacht-bu-kyougou.md` に保存済み）で既にカバー済みだった。
SKILL.mdの絶対ルール「1記事＝1キーワード」「重複KW回避」に抵触するため、
同じH群・同じ一次データ（`/universities/`・`/regions/`）を差別化軸に使える
未着手KW（K1／H17クラスタ）へ差し替えた。

- 既存記事 `daigaku-yacht-bu-kyougou.md` の主題: 成績（インカレ総合優勝校・水域別団体上位校）
- 本記事の主題: 加盟大学そのものの一覧（水域・活動拠点ハーバー・出場クラス）
- カニバリ回避: 本記事では順位・強さの話をせず、強豪の話題は既存記事へ内部リンクで送る

## 1. SERP上位（WebSearch 2026-09-24実施）

クエリ「ヨット部がある大学 一覧」上位:
1. spaia.jp/column/sailing/2821 「関東の大学ヨット部はどこが有名？」
2. 東京経済大学 ヨット部（大学公式の部活紹介ページ）
3. 関西大学 ヨット部（同上）
4. 法政大学 ヨット部（同上）
5. 早稲田大学 競技スポーツセンター ヨット部（同上）
6. 中央大学 ヨット部（同上）
7. yumefusen.co.jp/tsujido_yacht/link/univ.htm 「全国大学ヨット部」（個人・団体運営のリンク集）
8. 日本大学ヨット部 公式
9. 全日本学生ヨット連盟「加盟校」ページ
10. 立命館大学体育会ヨット部 公式

クエリ「大学 ヨット部 一覧 加盟校 学生ヨット連盟 水域」上位:
関西大学／早稲田大学／Wikipedia「関東学生ヨット連盟」／関西学生ヨット連盟（Googleサイト）／
全日本学生ヨット連盟トップ／yumefusen リンク集／全日本学連「加盟校」／
全日本学連「加盟水域ホームページリンク」／関東学生ヨット連盟／関東学連 新入生勧誘特設ページ

## 2. 共通点と差別化点（3行）

- 共通点1: 上位のほとんどが「1大学＝1ページ」の各大学公式部活紹介で、**複数大学を横断して比較できる一覧が事実上ない**。横断型はSPAIA（関東のみ・2017年掲載）と古いリンク集の2件だけ。
- 共通点2: 全日本学生ヨット連盟の「加盟校」ページは**年度別PDFへのリンクのみ**（2026年度は7月修正版、2025年度、2024年度8月13日修正版等）で、ページ本文に水域別の大学名が無く、ブラウザ上でそのまま一覧を読めない（WebFetchで確認）。
- 差別化点: 自サイトの `data/universities.json`（2026-09-23取得）から、**関東36校・近畿北陸10校を「水域×活動拠点ハーバー×出場クラス」で整理したHTML一覧**を出し、各校の `/universities/<slug>/` へ内部リンクする。さらに上位陣が一切触れない「どの水域が一覧化できていて、どの水域ができていないのか」を対照表で開示する。

## 3. 一次データの検証結果

- 関東学生ヨット連盟 members ページの掲載校を全件取得して照合 → **36校で当サイトのデータと完全一致**（WebFetchの要約が一度「38大学」と返したが、名称列挙をやり直して36校と確定）。
- 近畿北陸学生ヨット連盟由来は10校。連盟サイトに艇種・拠点の記載が無いため、当サイトでも `classes`・`harbor` は空。
- `data/meta.json`: `fetched_at` = 2026-09-23、`university_count` = 46、`region_count` = 9、`results_pdf_count` = 20、`calendar_count` = 17。
- 全日本学連「加盟水域ホームページリンク」: 関東・中部・近畿北陸・関西の4水域のみリンクあり。北海道・東北・中国・四国・九州は空欄（`pipeline/regions.py` では北海道のみ別途URLを保持）。
- 関西水域は公式サイトがGoogleサイトでログインを要求するため取得不可（`pipeline/regions.py` の note に記録あり）。

## 4. 本記事だけの要素（独自集計）

いずれも関東36校について、関東学生ヨット連盟の掲載値をヨットマニアが集計したもの。

- 活動拠点ハーバー別の延べ校数: 江の島11／八景島11／葉山・葉山新港10／森戸海岸4／稲毛3／霞ヶ浦1（複数拠点の大学は重複計上。防衛大学校は連盟掲載が「神奈川」表記）
- 出場クラス別: 470級・スナイプ級の両方=17校／470級のみ=13校／スナイプ級のみ=6校
- 9水域のカバレッジ対照表（大学ディレクトリ掲載可否×成績PDF掲載）

## 5. 内部リンク方針（必須施策）

実在するURLパスのみ使用（`pipeline/generate_site.py` の `write_page` 呼び出しで確認）。
**`/universities/` の一覧インデックスページは存在しない**ため、`/universities/<slug>/index.html` 個別ページのみリンクする。

- `/regions/index.html`・`/regions/kanto/index.html`・`/regions/kinki-hokuriku/index.html`
- `/results/index.html`・`/calendar/index.html`
- `/universities/<slug>/index.html`（表内の大学名）
- 既存記事: `daigaku-yacht-bu-kyougou`・`daigaku-yacht-bu-erabikata-checklist`・`daigaku-yacht-bu-mikeikensha-guide`・`daigaku-yacht-470-snipe-chigai`
