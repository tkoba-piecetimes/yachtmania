# SERP分析メモ｜ヨット部 肩 腰 怪我 予防

- 調査日: 2026-10-12
- 対象KW: ヨット部 肩 腰 怪我 予防（KW在庫 P7）
- クエリ分類: 部員向け定番（現役部員が「どこを痛めやすいか・どう予防するか」を知りたい）
- 使用ツール: WebSearch（「セーリング 競技 傷害 腰痛 肩 膝 発生部位 調査」「sailing injuries epidemiology Olympic sailors low back pain knee shoulder」「ヨット部 腰痛 肩 怪我 予防 ストレッチ ハイクアウト 体幹」ほか）、WebFetch

## 上位に出ている面（2026-10-12時点）

| # | URL | 種別 | 内容 | 弱点 |
|---|---|---|---|---|
| 1 | https://www.springermedicine.com/the-epidemiology-and-aetiology-of-injuries-in-sailing/23074054 | 学術レビュー（Neville & Folland, 2009） | 競技ヨット傷害の疫学。腰椎・胸椎と膝が最多、反復動作が使いすぎ傷害に結びつく | 英語。大学部活の現場視点がない |
| 2 | https://bjsm.bmj.com/content/50/11/673 | 学術誌（BJSM） | 2014年ISAF世界選手権の質問票。腰29%・膝13%・肩12%・足首10%、58%が使いすぎ | 英語の抄録。WebFetchは403のため検索結果要約で確認 |
| 3 | https://sciencenordic.com/forskningno-injuries-society--culture/swedish-sailors-injure-knees-on-land/1387824 | 報道（ヨーテボリ大学） | 24+21人・144件。水上は20%未満、体力トレーニング中が約1/3 | 海外の選手。日本の部活の文脈がない |
| 4 | https://tokorozawa.w.waseda.jp/kg/doc/20//sotsuron2013/1K10C376.pdf | 大学卒論（早大） | ハイクアウト姿勢の筋バランスと腰痛。402人中175人が腰痛、123人がハイクアウトで痛み（先行調査の引用） | 一般読者向けでない。WebFetchは403のため検索結果要約のみ確認 |
| 5 | https://fittoplay.org/sports/sailing/the-most-common-injuries/ | 傷害予防サイト | 帆走の代表的な傷害6種と予防の方向性 | 出典の記載がなく、部活の文脈もない |
| 6 | その他（一般の腰痛ストレッチ記事） | 一般健康記事 | ハイクアウトに特化していない | ヨット固有の動作を扱っていない |

## 判定

**採用**。理由:

- 上位は英語の学術文献か一般の腰痛記事で、**日本語で「ヨット部員が痛めやすい部位・場面・予防の考え方」を研究の裏付けつきでまとめた記事は見当たらない**。
- 既存の筋トレ記事（yacht-bu-kintore-menu）は「何を鍛えるか」、本記事は「どこを痛めやすいか・痛みが出たらどうするか」で検索意図が異なり、カニバらない。保険記事（yacht-bu-hoken-kanyu）とも内容が別。
- 内部リンクで筋トレ・合宿・栄養・日焼け・安全・保険の既存記事へ回遊させられる。

## 使う一次情報・出典（個人特定なし）

- Neville & Folland（Sports Medicine, 2009）: 五輪クラスで約0.2件/選手/年、腰椎・胸椎と膝が最多、ハイクアウト・グラインド・操舵が使いすぎ傷害に関係
- 2014年ISAF世界選手権 質問票: 760人回答、244人が299件、0.59件/1000h、腰29%・膝13%・肩12%・足首10%、使いすぎ58%、56%が休止
- ヨーテボリ大学: 24人+21人・12か月・144件、水上20%未満、体力トレーニング約1/3、セーリング練習17%、レース12%、膝約20%・すね足首足13%・肩12%、若手は背中胴体・ナショナルは肩、3分の2が個別に筋力トレ
- 早大卒論の引用調査: 402人、約4割（175人）が腰痛、うち123人がハイクアウトで痛み（確認は検索結果要約のみ→本文で「確認できていない」旨を明記）

## 内部リンク候補（実在確認: generate_site.py の write_page）

- `/calendar/`、`/regions/`、`/regions/kanto/`、`/universities/tokyo-tech/`
- 既存記事: yacht-bu-kintore-menu / yacht-bu-gasshuku-naiyou-schedule / yacht-bu-shokuji-eiyou-kanri / yacht-bu-hiyake-taisaku / yacht-bu-hoken-kanyu / daigaku-yacht-bu-oyogenai-anzen-lifejacket / daigaku-yacht-470-snipe-chigai / daigaku-yacht-bu-skipper-crew-chigai

## 一次情報バンクの利用

`yachtmania/docs/primary-sources/` は存在しない。shukatsu-media側の競技別引退時期一覧もヨットは空欄のため利用なし（怪我テーマには無関係）。一般論は「一般的には」と明示した。

## 注意点

- 医療行為の断定をしない。具体的な種目・回数・重量は書かない。
- 大学ディレクトリは関東・近畿北陸のみ対応。
- 協賛案件情報・個人名は書かない。
