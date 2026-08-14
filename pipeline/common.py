# -*- coding: utf-8 -*-
"""取得スクリプトで共有するヘルパー（ラグビーマニア版を流用）。"""
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from urllib.parse import quote

UA = "Mozilla/5.0 (compatible; YachtManiaBot/1.0; +https://tkoba-piecetimes.github.io/yachtmania/)"


def nfc(s: str) -> str:
    """Unicode正規化（NFC）。取得元サイトによって濁点・半濁点が結合済み/分解済みで
    混在することがあり、文字列比較やスラッグ生成がずれるのを防ぐ。"""
    return unicodedata.normalize("NFC", s) if s else s


def fetch(url: str, retries: int = 3, polite_sleep: float = 1.0) -> str:
    """礼儀正しく（1秒sleep）ページを取得する。

    URL中に生の日本語（未エンコード）が混じっていてもエンコードして送る
    （サイト内リンクを辿った場合、hrefが素のUTF-8文字列のことがあるため）。
    """
    safe_url = quote(url, safe=":/%?=&#")
    req = urllib.request.Request(safe_url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                html = res.read().decode("utf-8", errors="replace")
            if polite_sleep:
                time.sleep(polite_sleep)
            return html
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise
            print(f"[warn] fetch failed ({e}), retrying in {5 * (attempt + 1)}s...", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
