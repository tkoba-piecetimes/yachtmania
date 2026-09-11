# ヨットマニア — 大学ヨット情報メディア

## 2026-09-12 サイト構成の改善版

ラクロスマニアの導線を参考に、ヨット向けの大会・日程／大会結果／水域／読みもの／成績データベース／部活の協賛／マイチームへ構成を刷新。

- 共通デザイン・トップページを海の青に統一。既存の写真、記事、問い合わせ、公式出典、協賛リンクを継承。
- 結果・データベースは水域／年度／470級・スナイプ級／大会・大学名で検索でき、20件の既存成績表をその場で開ける。大会結果は掲載済み最新年度が初期値、データベースは全年度が初期値。
- 大会日程は開催期間中・予定・終了を日本時間で判定。学連行事と全国大会の公式案内を別に整理。公式ページの年度を取得し、年度不明の日程を現在年度と推定しない。
- マイチームは大学の保存・解除に対応。保存先はブラウザーのlocalStorageで、アカウント同期や通知機能はない。
- 大学ページから大学名での成績検索とマイチーム選択へ直接移動可能。
- 既存URLを維持。`pipeline/experience.py`と`assets/experience.*`を既存の生成処理から利用するので、日次再生成後も改善内容を維持。
- `python -m unittest discover -s pipeline -p 'test_*.py'` で日付処理の回帰チェックを実行。日次ワークフローにも追加。

この変更時点の成績データは2025年度20件、大学ディレクトリは関東・近畿北陸46校。過去年度を追加したという意味ではない。2021年以降の拡張、他水域の大学拡張は公式ソース確認後の追加課題。

本番公開は既存GitHub Pagesのフローを利用する。mainへのpush後、公式データの取得・回帰チェック・サイト生成を経てyachtmania.jpへ公開する。

大学ヨットの情報メディア「ヨットマニア」（運営: PieceTimes）。

- 公開URL: https://tkoba-piecetimes.github.io/yachtmania/

## MVPのスコープ

大学ヨットは大会がリーグ戦ではなく水域予選→全国大会という選手権（レガッタ）形式で、
成績はほぼPDF配布のため、ラグビーマニア／サッカーマニア等の「試合結果・順位表」型の
サイト構造はそのまま流用できない。そのため本MVPは以下の3本柱に絞っている。

1. **水域別の加盟大学ディレクトリ**（関東36校・近畿北陸10校。HTMLで取得できた水域のみ）
2. **大会カレンダー**（近畿北陸学生ヨット連盟の年間予定＋全国大会の最新情報ページへの導線）
3. **成績PDFへのリンク集＋ページ内表示**（全日本学生ヨット連盟の水域大会成績ページを毎日巡回し、
   新着PDFを検知。表構造の解析に成功した分は艇順位・大学名・得点をページ内で確認できる。
   レイアウトの都合で解析できなかった分はPDFへの直リンクのみを掲載）

対象:
- 関東（kantogakuren.org）: 加盟大学36校をHTMLディレクトリとして掲載
- 近畿北陸（kinhokugakuren.com）: 加盟大学10校＋年間大会カレンダー14件
- 北海道・東北・中部・関西・中国・四国・九州: 大学ディレクトリは対応エリア外
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
  → pipeline/fetch_pdf_results.py（新規PDFの表構造をpdfplumberで解析 → data/results_parsed/<id>.json）
  → pipeline/generate_site.py
  → site/
```

成績PDFリンクは`data/results_pdfs.json`に「初検知日（first_detected_at）」を保持したまま
日次マージされ、直近14日以内に初検知されたものをトップページ・各水域ページで
「NEW」表示する。`pipeline/fetch_pdf_results.py`は未解析のPDFのみを対象に表構造を解析し、
成功した分だけ`data/results_parsed/<id>.json`を書き出す（解析済みのPDFは再取得しない）。

## 実行

```
python pipeline/fetch_all.py
python pipeline/fetch_pdf_results.py
python pipeline/generate_site.py
```

ローカル確認: `python -m http.server 8942 -d site`

## 日次自動更新

`.github/workflows/update.yml` が毎日6:00 JSTに以下を実行する。

1. `pipeline/fetch_all.py`（大学ディレクトリ・大会カレンダー・成績PDFリンクを再取得）
2. `pipeline/fetch_pdf_results.py`（新規検知分の成績PDFの表構造を解析）
3. `pipeline/generate_site.py`（サイト再生成）
4. 変更があれば `data/` `site/` をコミット・push
5. GitHub Pagesへデプロイ

## 未実装・今後の課題

- 成績PDFの表構造解析はレイアウトの揺れが大きく、一部のPDFは大学ごとの最終得点・
  順位のみの簡易表示（レース単位の内訳なし）、または解析失敗としてPDF直リンクに
  フォールバックする。解析ロジックの精度向上は継続課題
- 関西学生ヨット連盟の公式サイト（Google Sites）はログインが必要で取得不可。
  ログイン不要な代替ソースが見つかれば大学ディレクトリを追加する
- 北海道・東北・中部・中国・四国・九州の大学ディレクトリ（各水域の公式サイトを
  個別調査すれば取得できる可能性がある）
- GA4 / Search Console 連携（GA_MEASUREMENT_ID・GSC_VERIFICATIONは未設定）
- ドメイン取得・GitHub Pages カスタムドメイン設定
- 読みもの記事（`content/articles/` にMarkdownを追加すれば自動で有効化される）
