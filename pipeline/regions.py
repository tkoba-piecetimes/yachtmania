# -*- coding: utf-8 -*-
"""大学ヨットの9水域の静的メタデータ（連盟名・公式サイト・注記）。

大学ディレクトリをHTMLで取得できた水域（関東・近畿北陸）は has_directory=True。
それ以外は「大会結果リンクのみ」の水域ページになる。
federation_url が空の水域は、出典ページ（全日本学生ヨット連盟サイト）上に
連盟名の記載はあるが公式サイトへのリンクが見つからなかったもの。
"""

REGION_ORDER = [
    "kanto", "kinki-hokuriku", "kansai",
    "hokkaido", "tohoku", "chubu", "chugoku", "shikoku", "kyushu",
]

REGIONS = {
    "kanto": {
        "name": "関東",
        "federation": "関東学生ヨット連盟",
        "federation_url": "https://kantogakuren.org/",
        "has_directory": True,
        "note": "",
    },
    "kinki-hokuriku": {
        "name": "近畿北陸",
        "federation": "近畿北陸学生ヨット連盟",
        "federation_url": "https://www.kinhokugakuren.com/",
        "has_directory": True,
        "note": "",
    },
    "kansai": {
        "name": "関西",
        "federation": "関西学生ヨット連盟",
        "federation_url": "https://sites.google.com/view/kansaigakuren-sailing",
        "has_directory": False,
        "note": "公式サイト（Googleサイト）はログインを要求され取得できなかったため、"
                "大学ディレクトリは未掲載です。大会結果は全日本学生ヨット連盟の"
                "水域大会成績ページから取得しています。",
    },
    "hokkaido": {
        "name": "北海道",
        "federation": "北海道学生ヨット連盟",
        "federation_url": "http://hokkaidoyacht.jugem.jp/",
        "has_directory": False,
        "note": "",
    },
    "tohoku": {
        "name": "東北",
        "federation": "東北学生ヨット連盟",
        "federation_url": "",
        "has_directory": False,
        "note": "",
    },
    "chubu": {
        "name": "中部",
        "federation": "中部学生ヨット連盟",
        "federation_url": "https://www.zennihon201809.com/各水域ホームページ/中部学生ヨット連盟/",
        "has_directory": False,
        "note": "",
    },
    "chugoku": {
        "name": "中国",
        "federation": "中国学生ヨット連盟",
        "federation_url": "",
        "has_directory": False,
        "note": "",
    },
    "shikoku": {
        "name": "四国",
        "federation": "四国学生ヨット連盟",
        "federation_url": "",
        "has_directory": False,
        "note": "",
    },
    "kyushu": {
        "name": "九州",
        "federation": "九州学生ヨット連盟",
        "federation_url": "",
        "has_directory": False,
        "note": "",
    },
}

# 全日本学生ヨット連盟「水域大会成績」ページの見出し（例:「北海道水域」）→ 水域コード
SUIIKI_LABEL_TO_CODE = {
    "北海道水域": "hokkaido",
    "東北水域": "tohoku",
    "関東水域": "kanto",
    "中部水域": "chubu",
    "近畿北陸水域": "kinki-hokuriku",
    "関西水域": "kansai",
    "中国水域": "chugoku",
    "四国水域": "shikoku",
    "九州水域": "kyushu",
}
