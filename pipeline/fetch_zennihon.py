# -*- coding: utf-8 -*-
"""全日本学生ヨット連盟（zennihon201809.com）から

1. 水域大会成績ページ（例: /大会成績/水域大会成績/2025年度/）を巡回し、
   公式成績PDFへのリンクを「大会名・水域・クラス・検知日」付きで検知する
   （PDFの中身はダウンロード・解析しない。リンクの一覧化のみ）。
2. 大会日程ページ・全国大会（全日本選手権/個人選手権/女子選手権）の
   最新の大会情報ページへのリンクをカレンダー用に取得する。

データ出典: 全日本学生ヨット連盟
  https://www.zennihon201809.com/
"""
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fetch, nfc
from regions import SUIIKI_LABEL_TO_CODE

BASE = "https://www.zennihon201809.com"
SUIIKI_INDEX_URL = f"{BASE}/%E5%A4%A7%E4%BC%9A%E6%88%90%E7%B8%BE/%E6%B0%B4%E5%9F%9F%E5%A4%A7%E4%BC%9A%E6%88%90%E7%B8%BE/"
SCHEDULE_URL = f"{BASE}/%E5%A4%A7%E4%BC%9A%E6%97%A5%E7%A8%8B/"
SOURCE_LABEL = "全日本学生ヨット連盟"

REGION_HEADING_RE = re.compile(r'>\s*([^<>]{2,10}?水域)\s*<')
DOWNLOAD_HREF_RE = re.compile(r'<a class="j-m-dowload" href="([^"]+\.pdf[^"]*)"')
DOWNLOAD_NAME_RE = re.compile(r'<div class="cc-m-download-file-name">([^<]+)</div>')
YEAR_DIR_RE = re.compile(r'href="(/大会成績/水域大会成績/(\d{4})年度/)"')
DOWNLOAD_ID_RE = re.compile(r'/app/download/(\d+)/')


def classify(filename: str) -> str:
    norm = nfc(filename)
    low = norm.lower()
    if "470" in low:
        return "470級"
    if "snipe" in low or "スナイプ" in norm:
        return "スナイプ級"
    return "総合"


def discover_year_pages(html: str) -> list[tuple[str, str]]:
    """水域大会成績インデックスページから年度別サブページを列挙する。"""
    seen = {}
    for path, year in YEAR_DIR_RE.findall(html):
        seen[year] = urljoin(BASE, path)
    return sorted(seen.items(), key=lambda x: x[0], reverse=True)


def parse_result_pdfs(html: str, page_url: str, year_label: str) -> list[dict]:
    regions = [(m.start(), m.group(1).strip()) for m in REGION_HEADING_RE.finditer(html)]
    hrefs = [(m.start(), m.group(1)) for m in DOWNLOAD_HREF_RE.finditer(html)]
    names = [(m.start(), m.group(1).strip()) for m in DOWNLOAD_NAME_RE.finditer(html)]

    out = []
    for (pos, href), (_, fname) in zip(hrefs, names):
        region_label = None
        for rpos, rname in regions:
            if rpos <= pos:
                region_label = nfc(rname)
            else:
                break
        region_code = SUIIKI_LABEL_TO_CODE.get(region_label or "", "")
        full_url = urljoin(page_url, href)
        m = DOWNLOAD_ID_RE.search(href)
        pdf_id = m.group(1) if m else full_url
        out.append({
            "id": pdf_id,
            "filename": nfc(fname),
            "url": full_url,
            "region": region_code,
            "region_label": region_label or "",
            "class": classify(fname),
            "year_label": year_label,
            "source": SOURCE_LABEL,
            "source_url": page_url,
        })
    return out


def fetch_result_pdfs() -> list[dict]:
    index_html = fetch(SUIIKI_INDEX_URL)
    year_pages = discover_year_pages(index_html)
    if not year_pages:
        # インデックスに一覧が出ない場合でも、既知の2025年度ページへは直接アクセスできる
        year_pages = [("2025", urljoin(BASE, "/大会成績/水域大会成績/2025年度/"))]
    all_pdfs = []
    for year, url in year_pages:
        html = fetch(url)
        pdfs = parse_result_pdfs(html, url, f"{year}年度")
        print(f"zennihon: {year}年度 水域大会成績 PDF {len(pdfs)}件")
        all_pdfs.extend(pdfs)
    return all_pdfs


# ---- 大会日程ページ（全国大会の最新情報 + 水域別スケジュールPDF） ----

NAV_LINK_RE = re.compile(r'<a href="(/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
NATIONAL_CATEGORIES = [
    ("/全日本学生ヨット選手権/", "全日本学生ヨット選手権"),
    ("/全日本学生ヨット個人選手権/", "全日本学生ヨット個人選手権"),
    ("/全日本学生女子ヨット選手権/", "全日本学生女子ヨット選手権"),
]


def _strip_tags(s: str) -> str:
    return nfc(re.sub(r"<[^>]+>", "", s).replace("​", "").strip())


def parse_national_events(html: str) -> list[dict]:
    pairs = [(urljoin(BASE, h), _strip_tags(t)) for h, t in NAV_LINK_RE.findall(html)]
    out = []
    for prefix, label in NATIONAL_CATEGORIES:
        for href, text in pairs:
            full_prefix = urljoin(BASE, prefix)
            if href == full_prefix or not href.startswith(full_prefix):
                continue
            if not text:
                continue
            out.append({
                "category": label,
                "title": text,
                "url": href,
                "source": SOURCE_LABEL,
                "source_url": SCHEDULE_URL,
            })
            break  # ナビ内で一番上（最新）の1件のみ採用
    return out


def parse_schedule_pdfs(html: str) -> list[dict]:
    names = DOWNLOAD_NAME_RE.findall(html)
    hrefs = DOWNLOAD_HREF_RE.findall(html)
    out = []
    for fname, href in zip(names, hrefs):
        out.append({
            "filename": nfc(fname),
            "url": urljoin(BASE, href),
        })
    return out


def fetch_national_calendar() -> tuple[list[dict], list[dict]]:
    html = fetch(SCHEDULE_URL)
    events = parse_national_events(html)
    pdfs = parse_schedule_pdfs(html)
    print(f"zennihon: 全国大会 {len(events)}件 / 日程PDF {len(pdfs)}件 取得")
    return events, pdfs


def main():
    pdfs = fetch_result_pdfs()
    events, sched_pdfs = fetch_national_calendar()
    return pdfs, events, sched_pdfs


if __name__ == "__main__":
    pdfs, events, sched_pdfs = main()
    print(f"合計 PDF {len(pdfs)}件")
    for p in pdfs[:5]:
        print(p)
