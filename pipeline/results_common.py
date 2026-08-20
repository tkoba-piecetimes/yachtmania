# -*- coding: utf-8 -*-
"""成績PDF一覧（data/results_pdfs.json）から「大会」単位のデータ構造を組み立てる
共通ロジック。generate_articles.py（Type A: 新着成績記事）と
generate_data_articles.py（大学別成績まとめ・水域別シーズン総括）の両方から
利用する（両モジュール間の循環importを避けるための切り出し）。

大会名の抽出はファイル名からのヒューリスティックであり、LLMは使わない。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTENT = ROOT / "content" / "articles"

# ---------------------------------------------------------------- 大会名抽出

# クラス名トークン（長い表記を先に置く。「級」は470_級のように区切られる表記の
# 取りこぼしを拾うための最終フォールバック）
CLASS_TOKEN_RE = re.compile(r"(スナイプ級|470級|スナイプ|Snipe|SNIPE|snipe|470|級)")
# 「成績」「速報」等、大会名の一部ではない定型語（ファイル名中どこにあっても除去）
NOISE_WORD_RE = re.compile(r"(最終成績|団体戦成績|団体成績|成績表|成績|速報|団体戦|団体)")
IDX_SUFFIX_RE = re.compile(r"\s*\(\d+\)\s*$")          # "...(1)" のような重複回避の付番
DATE_SUFFIX_RE = re.compile(r"_?\d{4}_?\d{2}_?\d{2}$")  # "..._2025_10_05" のような末尾日付
TRAIL_BRACKET_RE = re.compile(r"[（(][^）)]{0,10}[）)]\s*$")  # 末尾の短い括弧注記（団体）等


def normalize_event_name(filename: str) -> str:
    """成績PDFのファイル名から「大会名」を抽出するヒューリスティック。

    例:
      【九州インカレ団体戦】スナイプ級最終成績.pdf → 九州インカレ
      【九州インカレ団体戦】470級最終成績.pdf     → 九州インカレ （↑と同じ大会名でまとまる）
      2025年度　関西学生ヨット選手権　snipe.pdf   → 2025年度 関西学生ヨット選手権
    """
    s = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    s = IDX_SUFFIX_RE.sub("", s)
    s = DATE_SUFFIX_RE.sub("", s)
    s = CLASS_TOKEN_RE.sub("", s)
    s = NOISE_WORD_RE.sub("", s)
    while True:
        stripped = TRAIL_BRACKET_RE.sub("", s).strip()
        if stripped == s:
            break
        s = stripped
    s = s.replace("＿", "").replace("_", "")
    s = s.replace("【", "").replace("】", "")
    s = re.sub(r"[\s　]+", " ", s)
    s = s.strip(" -ー_")
    return s or "大会成績"


_kks = None


def romaji_slug(name: str) -> str | None:
    """大会名 → ローマ字スラッグ（大学スラッグと同じくpykakasiを使用、ハッシュにはフォールバックしない）。"""
    global _kks
    try:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        s = "".join(x["hepburn"] for x in _kks.convert(name))
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        if len(s) > 40:
            cut = s[:40].rsplit("-", 1)[0]
            s = cut if len(cut) >= 10 else s[:40]
        return s or None
    except Exception as e:
        print(f"[warn] ローマ字化失敗: {name} ({e})", file=sys.stderr)
        return None


def year_num(year_label: str) -> str:
    m = re.search(r"\d{4}", year_label or "")
    return m.group(0) if m else "0000"


# ---------------------------------------------------------------- data loading

def load_results():
    f = DATA / "results_pdfs.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8"))


def existing_slugs() -> set[str]:
    if not CONTENT.exists():
        return set()
    return {f.stem for f in CONTENT.glob("*.md")}


def group_by_tournament(results):
    """成績PDFを (水域, 年度, 大会名) 単位でグルーピングする。

    戻り値の各要素の "slug" は、新着成績記事(result-*)のslugと同じ決定的な値
    （result-<大会名のローマ字スラッグ>-<年度>）になる。大学別・水域別の新
    ジェネレータはこのslugを使って、既存の新着成績記事へ内部リンクできる。
    """
    groups: dict[tuple, list] = {}
    for r in results:
        stem = normalize_event_name(r["filename"])
        key = (r.get("region", ""), r.get("year_label", ""), stem)
        groups.setdefault(key, []).append(r)

    out = []
    for (region, year_label, event_name), pdfs in groups.items():
        pdfs_sorted = sorted(pdfs, key=lambda p: (p["class"], p["filename"]))
        detected_at = max(p["first_detected_at"] for p in pdfs)
        slug_base = romaji_slug(event_name) or f"g{abs(hash(event_name)) % 10**8}"
        out.append({
            "region": region,
            "year_label": year_label,
            "event_name": event_name,
            "pdfs": pdfs_sorted,
            "detected_at": detected_at,
            "slug": f"result-{slug_base}-{year_num(year_label)}",
        })
    return out
