# -*- coding: utf-8 -*-
"""近畿北陸学生ヨット連盟（kinhokugakuren.com）のスケジュールページから
加盟大学一覧（フッター掲載）と大会カレンダー（h3=日付 + 直後のp=大会名）を取得する。

データ出典: 近畿北陸学生ヨット連盟 スケジュールページ
  https://www.kinhokugakuren.com/スケジュール
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fetch, nfc
from university_slugs import slug_for

URL = "https://www.kinhokugakuren.com/%E3%82%B9%E3%82%B1%E3%82%B8%E3%83%A5%E3%83%BC%E3%83%AB"
SOURCE_LABEL = "近畿北陸学生ヨット連盟"
SOURCE_URL = "https://www.kinhokugakuren.com/スケジュール"

DATE_EVENT_RE = re.compile(r'<h3[^>]*>(.*?)</h3>.*?<p[^>]*>(.*?)</p>', re.DOTALL)
DATE_LINE_RE = re.compile(r'^\d{1,2}月\d{1,2}日')

# フッターの加盟大学リンク（「○○大学...ヨット部」というテキストの<a>のみ拾う）
MEMBER_LINK_RE = re.compile(r'<a href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return nfc(s.replace("​", "").strip())


def parse_calendar(html: str) -> list[dict]:
    out = []
    for date_raw, event_raw in DATE_EVENT_RE.findall(html):
        date_text = _strip_tags(date_raw)
        event = _strip_tags(event_raw)
        if not DATE_LINE_RE.match(date_text):
            continue
        out.append({
            "date_text": date_text,
            "event": event,
            "region": "kinki-hokuriku",
            "source": SOURCE_LABEL,
            "source_url": SOURCE_URL,
        })
    return out


def parse_universities(html: str) -> list[dict]:
    # 加盟大学へのリンクはサイト全ページ共通のフッター内にまとめられている。
    idx = html.find('id="SITE_FOOTER"')
    if idx == -1:
        idx = 0
    chunk = html[idx:idx + 12000]
    out = []
    seen = set()
    for href, inner in MEMBER_LINK_RE.findall(chunk):
        text = _strip_tags(inner)
        if not text.endswith("ヨット部"):
            continue
        name = re.sub(r"(体育会|学友会体育局|準硬式)?ヨット部$", "", text).strip()
        name = re.sub(r"体育会$", "", name).strip()
        if not name.endswith("大学") or name in seen:
            continue
        seen.add(name)
        out.append({
            "name": name,
            "name_en": "",
            "region": "kinki-hokuriku",
            "classes": "",
            "harbor": "",
            "url": href,
            "slug": slug_for(name),
            "source": SOURCE_LABEL,
            "source_url": SOURCE_URL,
        })
    return out


def main() -> tuple[list[dict], list[dict]]:
    html = fetch(URL)
    univs = parse_universities(html)
    events = parse_calendar(html)
    print(f"kinki-hokuriku: 加盟大学 {len(univs)}校 / 大会日程 {len(events)}件 取得")
    return univs, events


if __name__ == "__main__":
    us, es = main()
    for u in us:
        print("univ:", u["name"], u["slug"], u["url"])
    for e in es:
        print("event:", e["date_text"], e["event"])
