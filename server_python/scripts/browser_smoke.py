"""Kiem tra browser trong image co dung duoc voi DUNG code path crawl hay khong.

Chay trong CHINH image production (image test khong tai binary browser):

    docker compose exec -T server python -m scripts.browser_smoke

Ly do ton tai: Dockerfile chi tai `chromium-headless-shell` chu khong tai ban
Chromium day du, dua tren gia dinh "Playwright >= 1.49 dung headless shell cho
che do headless". Gia dinh do chiu luc cho toan bo chuc nang crawl, nhung
test_crawl.py bi skip mac dinh (can internet) nen khong co gi bao ve no.

Quan trong: script goi thang `_get_page_content_and_css` cua controller thay vi
tu mo browser rieng. Neu tu mo, no chi bat duoc truong hop thieu binary; con
truong hop ai do sua crawl.py sang `headless=False` thi van xanh. Goi ham that
bat duoc ca hai. URL dung dang `data:` nen khong cham toi mang ngoai.
"""

import asyncio
import sys

from app.controllers.crawl import _get_page_content_and_css
from app.services.browser import browser_service

PROBE_URL = "data:text/html,<h1 id='probe'>fuurin</h1>"


async def main() -> int:
    try:
        html, _css = await _get_page_content_and_css(PROBE_URL)
        if "fuurin" not in html:
            print(f"FAIL: browser khong render duoc trang thu. HTML nhan duoc: {html[:200]!r}", file=sys.stderr)
            return 1
        print("OK: crawl mo duoc browser va render duoc trang")
        return 0
    finally:
        # Browser dung chung khong tu dong tat khi chay ngoai vong doi cua app;
        # thieu buoc nay thi tien trinh Chromium con lai sau khi script ket thuc.
        await browser_service.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
