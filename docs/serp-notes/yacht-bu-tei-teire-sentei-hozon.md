# SERP分析メモ｜ヨット部 艇 手入れ（洗艇・保管）

- 調査日: 2026-11-27
- 対象KW: ヨット部 艇 手入れ／洗艇（KW在庫のP群「道具の維持費・メンテ」の拡張。P9「セール 手入れ」は既存記事でカバー済みのため、艇体・金具・フォイルに対象を分けた）
- クエリ分類: 部員向け定番（現役・新入部員が練習後に何をすればよいか）
- レーン: P（Sonnet単独）
- 使用ツール: WebSearch（「ヨット部 艇 手入れ 洗艇 練習後 片付け 真水 洗う」「470級 艇 メンテナンス 日本470協会」「RYA dinghy care maintenance」「Snipe class rules hull maintenance」「ILCA dinghy maintenance」）、WebFetch

## 上位に出ている面（2026-11-27時点）

| # | 種別 | 内容 | 弱点 |
| --- | --- | --- | --- |
| 1 | ボート全般の洗艇解説（ship-pitu.com ほか） | 帰港後の真水洗い、金具重点洗い、月1の洗剤洗い | 動力ボート・ゴムボートが前提で、ヨット部の小型ディンギーの運用は扱わない |
| 2 | ヤマハ発動機の船外機のアフターケア | 船外機を真水で洗い、乾燥・防錆剤 | 船外機が対象で、ディンギーの艇体・金具は対象外 |
| 3 | Yahoo!知恵袋・個人ブログ | 塩抜きの是非、個人の経験談 | 根拠が個人の経験で、部活の当番運用の視点がない |
| 4 | 日本470協会（クラス規則和訳・計測手続き） | 規則上の補修の扱い | 手入れ手順の説明ではない |

日本語で「ヨット部の小型艇を部としてどう手入れ・保管するか」を扱う記事は上位に見当たらない。

## 判定

採用。既存の`yacht-sail-teire-hohou`（セール）、`yacht-bu-harbor-teiko-kyouyuu-hiyou`（ハーバー費用）、`yacht-bu-tei-hiyou-shikinchoutatsu`（艇の費用）とはテーマが異なり、カニバらない。

## 共通点（検索意図の正解）と欠けている要素

- 共通点: 毎回真水で塩分を落とす、水気を取る、金具を重点的に洗う。
- 欠けている要素: ディンギーの艇種・部活運用（当番・チェック表）、クラス規則上の補修の扱い（日常整備と計測員確認が必要な補修の区別）、栓の戻し忘れ防止、水域（海・湖）による違い。

## 使う一次情報・出典（WebFetchで確認）

- International Snipe Class Rules（2025-01-01施行）: C.7.1(a)(b)(c)（改造禁止・日常整備は再計測不要・それ以外は計測員確認）、C.7.2(b)（点検ハッチカバーと排水栓を常に所定の位置に）。PDF本文をテキスト抽出して条番号と文言を確認
- 国際470級クラス規則 2016年版和訳（日本470協会）: C.7.1(b)に日常整備、点検ホール・カバーとドレン・プラグの設置条項があることを構造から確認（PDFの日本語文字化けで原文の逐語確認は不可のため、本文では趣旨のみ記述し最新は公式サイト参照と明記）
- Haven KJ「Top 10 winter maintenance tips for you and your dinghy」: 洗剤＋真水で洗う、ロープ洗い、潤滑はシリコン等でグリース・オイルは避ける、金具のガルバニック腐食、フォイルの点検、ビーチ保管の固定
- Rooster「7 Winter Dinghy Maintenance Tips」: 毎セッション後に艇体を流す、GRPのカバー保管、トロリーのパッドを乾かす、ブロック・トラベラーカーを真水で流す、ラダー金具の確認
- 日本語の公的な艇メンテナンス資料は見つからなかった。一般論は英国事業者のガイドである旨と、部の指示優先を本文に明記

## 内部リンク（実在確認）

- /regions/kanto/index.html ・ /regions/kinki-hokuriku/index.html ・ /universities/ritsumeikan/index.html ・ /calendar/index.html ・ /results/index.html
- 既存記事: yacht-bu-tei-hiyou-shikinchoutatsu / yacht-bu-tei-kounyuu-chuko-rental-hiyou / yacht-bu-harbor-teiko-kyouyuu-hiyou / yacht-bu-tei-kizou-fubokai-shien / yacht-bu-ropework-musubikata-kiso / yacht-sail-teire-hohou / yacht-bu-fuyu-offseason-rikutore

## 一次情報バンクの利用

`docs/primary-sources/` はこのリポに存在しない。取材由来の一次情報は未使用。代替としてクラス規則（一次）と英国事業者のガイドを使用し、一般論と部の指示優先を明記した。

## 注意点

- 大学ディレクトリは関東・近畿北陸のみ対応。他水域は準備中と本文に明記
- ツナカレ協賛案件情報・個人名は書かない
