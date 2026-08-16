# -*- coding: utf-8 -*-
"""成績PDF（data/results_pdfs.json）の表構造をpdfplumberで解析し、
data/results_parsed/<id>.json に構造化データとして保存する。

PDFのレイアウトは大会・水域・クラス（個人戦/団体戦）ごとに揺れがあるため、
2種類のヘッダーパターンを検出して解析する。どちらにも一致しない、または
データ行が十分に取れない場合は解析失敗として書き出しをスキップし、
サイト側は既存どおりPDFへの直リンクにフォールバックする。

- tier "boat"    : 艇（Sail#）ごとの個人戦形式の結果表。艇順位・大学名・艇長・
                    クルー・レースごとの着順・合計・団体得点/順位まで取れる
                    （見出し行に「艇順位」列があるレイアウト）。
- tier "summary" : 大学（チーム）ごとの最終得点・順位のみの簡易表。
                    レースごとの内訳は列構成のばらつきが大きく個別艇への
                    対応付けが不確実なため、大学名＋最終得点＋最終順位のみを
                    採用する（見出し行に「大学名」等＋ラウンド列があるレイアウト）。

すでに data/results_parsed/<id>.json が存在するPDFは再解析しない
（PDFは公開後に内容が変わらない前提。日次実行では新規検知分のみ解析される）。
"""
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import UA

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "results_parsed"

ROUND_RE = re.compile(r"^第?[0-9]{1,2}[Rr]$")
RANK_RE = re.compile(r"^\d+$")
SUBHEADER_TOKENS = {"着順", "確定", "着", "確", "点", "小計", "順位", "得点"}
UNIV_HEADERS = {"大学名", "所属"}
FULLWIDTH_MAP = str.maketrans("０１２３４５６７８９Ｒ", "0123456789R")


def clean(s):
    """見出し語の照合用: 空白（改行含む）を全て除去した文字列。"""
    return re.sub(r"\s+", "", str(s)) if s else ""


def text(s):
    """表示用の値: 改行を空白に変え前後の空白のみ除去（内部の空白は残す）。"""
    return re.sub(r"\s+", " ", str(s)).strip() if s is not None else ""


def halfwidth(s):
    return s.translate(FULLWIDTH_MAP)


def cell(row, i):
    return row[i] if row and i is not None and 0 <= i < len(row) else None


def header_kind(row):
    cells = [clean(c) for c in row]
    if "艇順位" in cells:
        return "A"
    if any(c in UNIV_HEADERS for c in cells) and any(ROUND_RE.match(halfwidth(c)) for c in cells if c):
        return "B"
    return None


def is_subheader(row):
    vals = [clean(c) for c in row if clean(c)]
    if len(vals) < 2:
        return False
    hits = sum(1 for v in vals if v in SUBHEADER_TOKENS)
    return hits >= max(2, len(vals) // 2)


def col_label(i, *rows):
    parts = []
    for r in rows:
        v = clean(cell(r, i)) if r else ""
        if v and v not in parts:
            parts.append(v)
    return "".join(parts)


# ---------------------------------------------------------------- tier A（艇ごとの個人戦形式）

def parse_tier_a(rows, header_idx):
    group_row = rows[header_idx - 1] if header_idx > 0 else []
    header = rows[header_idx]

    def idx_of(*labels):
        for i, c in enumerate(header):
            if clean(c) in labels:
                return i
        return None

    idx_univ = idx_of("大学名", "所属", "Belongs")
    idx_skipper = idx_of("艇長", "Skipper")
    idx_crew = idx_of("クルー", "Crew")
    idx_sail = next((i for i, c in enumerate(header)
                      if clean(c) and ("Sail" in clean(c) or "セール" in clean(c))), None)
    idx_total = idx_of("合計")

    race_cols = [i for i, c in enumerate(group_row) if ROUND_RE.match(halfwidth(clean(c)))]
    race_labels = [halfwidth(clean(group_row[i])) for i in race_cols]

    tail_pairs = []
    if idx_total is not None:
        i = idx_total + 1
        while i < len(header) and len(tail_pairs) < 2:
            if clean(cell(header, i)) == "得点" and clean(cell(header, i + 1)) == "順位":
                tail_pairs.append((i, i + 1))
                i += 2
            else:
                i += 1

    boats = []
    for row in rows[header_idx + 1:]:
        if not RANK_RE.match(clean(cell(row, 0))):
            continue
        boat = {
            "rank": text(cell(row, 0)),
            "sail_no": text(cell(row, idx_sail)),
            "university": text(cell(row, idx_univ)),
            "skipper": text(cell(row, idx_skipper)),
            "crew": text(cell(row, idx_crew)),
            "races": [text(cell(row, i)) for i in race_cols],
            "total": text(cell(row, idx_total)),
            "boat_score": "", "boat_rank": "", "team_score": "", "team_rank": "",
        }
        if len(tail_pairs) >= 1:
            boat["boat_score"] = text(cell(row, tail_pairs[0][0]))
            boat["boat_rank"] = text(cell(row, tail_pairs[0][1]))
        if len(tail_pairs) >= 2:
            boat["team_score"] = text(cell(row, tail_pairs[1][0]))
            boat["team_rank"] = text(cell(row, tail_pairs[1][1]))
        boats.append(boat)

    # 団体得点・団体順位はセル結合の都合でチーム内の1艇にしか印字されないことがある
    # （先頭艇とは限らない）ため、同一大学が連続する艇グループ内で値を伝播させる。
    i = 0
    while i < len(boats):
        j = i
        while (j < len(boats) and boats[i]["university"]
               and boats[j]["university"] == boats[i]["university"]):
            j += 1
        group = boats[i:j] or [boats[i]]
        team_rank = next((b["team_rank"] for b in group if b["team_rank"]), "")
        team_score = next((b["team_score"] for b in group if b["team_score"]), "")
        for b in group:
            b["team_rank"] = b["team_rank"] or team_rank
            b["team_score"] = b["team_score"] or team_score
        i = max(j, i + 1)

    return {"race_labels": race_labels, "boats": boats}


# ---------------------------------------------------------------- tier B（大学ごとの最終順位のみ）

def parse_tier_b(rows, header_idx):
    header = rows[header_idx]
    ncols = len(header)
    subrow = None
    data_start = header_idx + 1
    if header_idx + 1 < len(rows) and is_subheader(rows[header_idx + 1]):
        subrow = rows[header_idx + 1]
        data_start = header_idx + 2

    idx_name = next((i for i, c in enumerate(header) if clean(c) in UNIV_HEADERS), None)
    if idx_name is None:
        return None
    idx_sail = next((i for i, c in enumerate(header)
                      if clean(c) and ("Sail" in clean(c) or "セール" in clean(c) or "Recall" in clean(c))), None)

    rank_col, score_col = ncols - 1, ncols - 2
    rank_label = col_label(rank_col, header, subrow) or "順位"
    score_label = col_label(score_col, header, subrow) or "得点"
    if "順位" not in rank_label:
        return None

    last_name, out = "", []
    for row in rows[data_start:]:
        name = text(cell(row, idx_name))
        if name:
            last_name = name
        rank = text(cell(row, rank_col))
        score = text(cell(row, score_col))
        if not (last_name and rank):
            continue
        out.append({"name": last_name, "sail_no": text(cell(row, idx_sail)), "score": score, "rank": rank})
    if len(out) < 2:
        return None
    return {"rows": out, "score_label": score_label, "rank_label": rank_label}


# ---------------------------------------------------------------- 表の検出・全体制御

def find_candidates(pages_tables):
    """(tier, table, header_row_index, page_index) のリストを返す。"""
    out = []
    for pi, tables in enumerate(pages_tables):
        for t in tables:
            if len(t) < 3:
                continue
            for i in range(min(4, len(t))):
                kind = header_kind(t[i])
                if kind:
                    out.append((kind, t, i, pi))
                    break
    return out


def extra_tables(pages_tables, page_idx, main_table):
    """個人戦形式（tier A）の補助情報（レース日・天候・レースオフィサー等）。"""
    out = []
    for t in pages_tables[page_idx]:
        if t is main_table or len(t) > 12:
            continue
        out.append([[text(c) for c in row] for row in t])
    return out[:2]


def parse_pdf(data: bytes):
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages_tables = [page.extract_tables() for page in pdf.pages]
    candidates = find_candidates(pages_tables)
    tier_a = [c for c in candidates if c[0] == "A"]
    tier_b = [c for c in candidates if c[0] == "B"]

    if tier_a:
        _, rows, idx, pi = tier_a[0]
        parsed = parse_tier_a(rows, idx)
        if not parsed["boats"]:
            return None, "艇順位の見出しは検出したが、データ行を認識できなかった"
        return {
            "tier": "boat",
            "race_labels": parsed["race_labels"],
            "boats": parsed["boats"],
            "extra_tables": extra_tables(pages_tables, pi, rows),
            "parsed_at": datetime.now().isoformat(timespec="seconds"),
        }, None

    if tier_b:
        all_rows, score_label, rank_label = [], "", ""
        for _, rows, idx, _ in tier_b:
            r = parse_tier_b(rows, idx)
            if r:
                all_rows.extend(r["rows"])
                score_label, rank_label = r["score_label"], r["rank_label"]
        if len(all_rows) < 2:
            return None, "大学名＋ラウンド列の見出しは検出したが、有効な行が2件未満だった"
        all_rows.sort(key=lambda r: (0, int(r["rank"])) if r["rank"].isdigit() else (1, r["rank"]))
        return {
            "tier": "summary",
            "rows": all_rows,
            "score_label": score_label,
            "rank_label": rank_label,
            "parsed_at": datetime.now().isoformat(timespec="seconds"),
        }, None

    return None, "既知の表見出し（艇順位 / 大学名+ラウンド列）が見つからなかった"


# ---------------------------------------------------------------- 取得・書き出し

def fetch_bytes(url: str, retries: int = 3) -> bytes:
    safe_url = quote(url, safe=":/%?=&#")
    req = urllib.request.Request(safe_url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return res.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = json.loads((DATA / "results_pdfs.json").read_text(encoding="utf-8"))

    ok = fail = skip = 0
    fail_log = []
    for e in entries:
        out_path = OUT_DIR / f"{e['id']}.json"
        if out_path.exists():
            skip += 1
            continue
        try:
            pdf_bytes = fetch_bytes(e["url"])
        except Exception as ex:
            fail += 1
            fail_log.append(f"{e['filename']}: ダウンロード失敗 ({ex})")
            continue
        try:
            parsed, reason = parse_pdf(pdf_bytes)
        except Exception as ex:
            parsed, reason = None, f"解析中に例外が発生 ({ex})"
        if parsed:
            parsed["id"] = e["id"]
            out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
            ok += 1
        else:
            fail += 1
            fail_log.append(f"{e['filename']}: {reason}")

    print(f"pdf成績解析: 成功{ok}件 / 失敗{fail}件（PDFリンクへフォールバック） / 解析済みスキップ{skip}件")
    for line in fail_log:
        print(f"  [skip] {line}")


if __name__ == "__main__":
    main()
