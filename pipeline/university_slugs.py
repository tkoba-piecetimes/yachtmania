# -*- coding: utf-8 -*-
"""大学名 → URLスラッグの対応表とスラッグ解決ロジック（ヨット版）。

解決順: 1) 手動登録の対応表  2) pykakasiによるローマ字化  3) ハッシュフォールバック
"""
import re
import sys

UNIV_SLUGS = {
    # ---- 関東学生ヨット連盟 加盟大学（36校） ----
    "日本大学": "nihon",
    "東京工業大学": "tokyo-tech",
    "獨協大学": "dokkyo",
    "法政大学": "hosei",
    "筑波大学": "tsukuba",
    "東京医科大学": "tokyo-medical",
    "明海大学": "meikai",
    "東洋大学": "toyo",
    "慶應義塾大学": "keio",
    "立教大学": "rikkyo",
    "青山学院大学": "aoyama-gakuin",
    "拓殖大学": "takushoku",
    "東京農工大学": "tokyo-noko",
    "東京大学": "tokyo",
    "上智大学": "sophia",
    "関東学院大学": "kanto-gakuin",
    "千葉大学": "chiba",
    "学習院大学": "gakushuin",
    "東京海洋大学": "tokyo-kaiyo",
    "横浜国立大学": "yokohama-national",
    "芝浦工業大学": "shibaura-it",
    "神奈川大学": "kanagawa",
    "東海大学": "tokai",
    "東京都立大学": "tokyo-metropolitan",
    "成蹊大学": "seikei",
    "専修大学": "senshu",
    "横浜市立大学": "yokohama-city",
    "早稲田大学": "waseda",
    "中央大学": "chuo",
    "明治大学": "meiji",
    "成城大学": "seijo",
    "駒澤大学": "komazawa",
    "電気通信大学": "uec",
    "防衛大学校": "nda",
    "一橋大学": "hitotsubashi",
    "工学院大学": "kogakuin",

    # ---- 近畿北陸学生ヨット連盟 加盟大学（10校） ----
    "金沢大学": "kanazawa",
    "京都大学": "kyoto",
    "京都産業大学": "kyoto-sangyo",
    "京都薬科大学": "kyoto-yakka",
    "滋賀大学": "shiga",
    "滋賀医科大学": "shiga-ika",
    "同志社大学": "doshisha",
    "富山大学": "toyama",
    "立命館大学": "ritsumeikan",
    "龍谷大学": "ryukoku",
}

_kks = None


def _romaji(name: str) -> str | None:
    global _kks
    try:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        base = re.sub(r"(大学院|大学校|大学|高専|高校|高)$", "", name.strip())
        s = "".join(x["hepburn"] for x in _kks.convert(base))
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return s or None
    except Exception:
        return None


def slug_for(name: str) -> str:
    if name in UNIV_SLUGS:
        return UNIV_SLUGS[name]
    r = _romaji(name)
    if r:
        UNIV_SLUGS[name] = r
        return r
    print(f"[warn] スラッグ生成不可の大学名: {name}", file=sys.stderr)
    return f"univ-{abs(hash(name)) % 10**8}"
