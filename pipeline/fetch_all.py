# -*- coding: utf-8 -*-
"""ヨットマニアのデータ取得を一括実行し、data/ 配下に正規化JSONを書き出す。

- data/universities.json   加盟大学ディレクトリ（関東36校・近畿北陸10校）
- data/calendar.json       大会カレンダー（近畿北陸の日程 + 全国大会の最新情報）
- data/results_pdfs.json   成績PDFリンクの検知結果（初検知日を維持しながら日次マージ）
- data/meta.json           取得メタ情報（取得日時・出典一覧）

PDFはダウンロード・解析せず、リンク（URL・大会名・水域・クラス・検知日）のみを保存する。
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_kanto
import fetch_kinki_hokuriku
import fetch_zennihon
from regions import REGIONS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def merge_result_pdfs(new_pdfs: list[dict]) -> list[dict]:
    """既存データに新規取得分をマージし、初検知日(first_detected_at)を保持する。"""
    existing_path = DATA_DIR / "results_pdfs.json"
    existing = {}
    if existing_path.exists():
        for e in json.loads(existing_path.read_text(encoding="utf-8")):
            existing[e["id"]] = e

    today = date.today().isoformat()
    merged = {}
    for p in new_pdfs:
        prev = existing.get(p["id"])
        first_detected = prev["first_detected_at"] if prev else today
        merged[p["id"]] = {
            **p,
            "first_detected_at": first_detected,
            "last_seen_at": today,
        }
    # 今回のクロールで見つからなかった過去分も（リンク切れ確認用に）残しておく
    for pid, prev in existing.items():
        if pid not in merged:
            merged[pid] = prev

    out = sorted(merged.values(), key=lambda e: (e["first_detected_at"], e["id"]), reverse=True)
    return out


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 1. 加盟大学ディレクトリ ----
    kanto_univs = fetch_kanto.main()
    kinki_univs, kinki_events = fetch_kinki_hokuriku.main()
    universities = kanto_univs + kinki_univs

    # ---- 2. 成績PDF・全国大会カレンダー ----
    result_pdfs, national_events, schedule_pdfs = fetch_zennihon.main()

    calendar = kinki_events + [
        {
            "date_text": "",
            "event": f'{e["category"]} {e["title"]}',
            "region": "",
            "source": e["source"],
            "source_url": e["url"],
        }
        for e in national_events
    ]

    merged_pdfs = merge_result_pdfs(result_pdfs)

    # ---- 3. 書き出し ----
    (DATA_DIR / "universities.json").write_text(
        json.dumps(universities, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "calendar.json").write_text(
        json.dumps(calendar, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "results_pdfs.json").write_text(
        json.dumps(merged_pdfs, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA_DIR / "schedule_pdfs.json").write_text(
        json.dumps(schedule_pdfs, ensure_ascii=False, indent=1), encoding="utf-8")

    sources = [
        {"label": "関東学生ヨット連盟", "url": "https://kantogakuren.org/members"},
        {"label": "近畿北陸学生ヨット連盟", "url": "https://www.kinhokugakuren.com/スケジュール"},
        {"label": "全日本学生ヨット連盟", "url": "https://www.zennihon201809.com/"},
    ]
    meta = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "sources": sources,
        "region_count": len(REGIONS),
        "university_count": len(universities),
        "calendar_count": len(calendar),
        "results_pdf_count": len(merged_pdfs),
    }
    (DATA_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    new_today = sum(1 for p in merged_pdfs if p["first_detected_at"] == date.today().isoformat())
    print(f"done: 大学{len(universities)}校 / カレンダー{len(calendar)}件 / "
          f"成績PDF{len(merged_pdfs)}件(本日新着{new_today}件)")


if __name__ == "__main__":
    main()
