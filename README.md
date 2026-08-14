# ヨットマニア — 大学ヨット情報メディア（MVP）

大学ヨットの情報メディア「ヨットマニア」（運営: PieceTimes）。

- 公開URL: https://tkoba-piecetimes.github.io/yachtmania/

## MVPのスコープ

大学ヨットは大会がリーグ戦ではなく水域予選→全国大会という選手権（レガッタ）形式で、
成績はほぼPDF配布のため、ラグビーマニア／サッカーマニア等の「試合結果・順位表」型の
サイト構造はそのまま流用できない。そのため本MVPは以下の3本柱に絞っている。

1. **水域別の加盟大学ディレクトリ**（関東36校・近畿北陸10校。HTMLで取得できた水域のみ）
2. **大会カレンダー**（近畿北陸学生ヨット連盟の年間予定＋全国大会の最新情報ページへの導線）
3. **成績PDFへの整理されたリンク集**（全日本学生ヨット連盟の水域大会成績ページを毎日巡回し、
   新着PDFを検知。**PDFの中身（順位・スコア）は解析せず、リンクの一覧化のみ**）

対象:
- 関東（kantogakuren.org）: 加盟大学36校をHTMLディレクトリとして掲載
- 近畿北陸（kinhokugakuren.com）: 加盟大学10校＋年間大会カレンダー14件
- 北海道・東北・中部・関西・中国・四国・九州: 大学ディレクトリは「準備中」
  （公式サイトが未取得またはPDF配布のみ）。大会成績PDFリンクは全水域で掲載
- 詳細・見送った理由は `docs/yacht-sources.md` 参照

## 仕組み

```
kantogakuren.org（関東・加盟大学）
kinhokugakuren.com（近畿北陸・加盟大学＋大会カレンダー）
zennihon201809.com（全国9水域の成績PDFリンク＋全国大会カレンダー）
  → pipeline/fetch_kanto.py / fetch_kinki_hokuriku.py / fetch_zennihon.py
    ※ pipeline/common.py（fetch・Unicode正規化）、pipeline/regions.py（水域メタデータ）、
       pipeline/university_slugs.py（大学名→URLスラッグ）を共有
  → pipeline/fetch_all.py（一括実行・成績PDFの初検知日をマージ）
  → data/*.json
  → pipeline/generate_site.py
  → site/
```

成績PDFリンクは`data/results_pdfs.json`に「初検知日（first_detected_at）」を保持したまま
日次マージされ、直近14日以内に初検知されたものをトップページ・各水域ページで
「NEW」表示する。

## 実行

```
python pipeline/fetch_all.py
python pipeline/generate_site.py
```

ローカル確認: `python -m http.server 8942 -d site`

## 日次自動更新

`.github/workflows/update.yml` が毎日6:00 JSTに以下を実行する。

1. `pipeline/fetch_all.py`（大学ディレクトリ・大会カレンダー・成績PDFリンクを再取得）
2. `pipeline/generate_site.py`（サイト再生成）
3. 変更があれば `data/` `site/` をコミット・push
4. GitHub Pagesへデプロイ

## 未実装・今後の課題

- **成績PDFの中身の解析**（順位表・個人成績の構造化）はスコープ外。PDFレイアウトが
  大会・水域ごとにバラバラなため、汎用パーサーの設計は別途調査が必要
- 関西学生ヨット連盟の公式サイト（Google Sites）はログインが必要で取得不可。
  ログイン不要な代替ソースが見つかれば大学ディレクトリを追加する
- 北海道・東北・中部・中国・四国・九州の大学ディレクトリ（各水域の公式サイトを
  個別調査すれば取得できる可能性がある）
- GA4 / Search Console 連携（GA_MEASUREMENT_ID・GSC_VERIFICATIONは未設定）
- ドメイン取得・GitHub Pages カスタムドメイン設定
- 読みもの記事（`content/articles/` にMarkdownを追加すれば自動で有効化される）
