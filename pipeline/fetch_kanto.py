# -*- coding: utf-8 -*-
"""関東学生ヨット連盟（kantogakuren.org）の加盟大学一覧を取得する。

データ出典: 関東学生ヨット連盟 加盟大学ページ
  https://kantogakuren.org/members?hsLang=ja-jp
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fetch, nfc
from university_slugs import slug_for

URL = "https://kantogakuren.org/members?hsLang=ja-jp"
SOURCE_LABEL = "関東学生ヨット連盟"
SOURCE_URL = "https://kantogakuren.org/members"

# 加盟大学カード1件: 見出し(日本語大学名) → 本文(<p>英語名<br>クラス<br>拠点</p>) → 公式HPボタン(href)
CARD_RE = re.compile(
    r'card-container__title"[^>]*>([^<]+)</h3>'
    r'.*?card-container__body[^>]*><p>(.*?)</p>'
    r'.*?class="hs-elevate-button[^"]*card-container__button"[^>]*href="([^"]+)"',
    re.DOTALL)


def parse(html: str) -> list[dict]:
    out = []
    for name_raw, body_raw, url in CARD_RE.findall(html):
        name = nfc(name_raw.strip())
        parts = [nfc(p.strip()) for p in re.split(r"<br\s*/?>", body_raw) if p.strip()]
        name_en = parts[0] if len(parts) > 0 else ""
        classes = parts[1] if len(parts) > 1 else ""
        harbor = parts[2] if len(parts) > 2 else ""
        out.append({
            "name": name,
            "name_en": name_en,
            "region": "kanto",
            "classes": classes,
            "harbor": harbor,
            "url": url,
            "slug": slug_for(name),
            "source": SOURCE_LABEL,
            "source_url": SOURCE_URL,
        })
    return out


def main() -> list[dict]:
    html = fetch(URL)
    univs = parse(html)
    print(f"kanto: 加盟大学 {len(univs)}校 取得")
    return univs


if __name__ == "__main__":
    for u in main():
        print(u["name"], u["slug"], u["url"])
