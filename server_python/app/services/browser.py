"""Trình duyệt Playwright dùng chung cho chức năng crawl.

Bản đầu gọi `async_playwright()` -> `chromium.launch()` -> `close()` cho MỖI
request. Trang Recruitment gọi 4 nguồn song song nên có lúc 4 tiến trình
Chromium (~300MB/tiến trình) cùng chạy, và mỗi lần khởi động mất 1-2 giây.

Ở đây:
- Một Playwright + một Browser dùng chung, mở/đóng theo vòng đời ứng dụng.
- Mỗi request chỉ mở một BrowserContext (rẻ, cô lập cookie/cache) rồi đóng.
- Semaphore giới hạn số trang mở đồng thời để không nổ RAM.
- Tự hồi phục: nếu tiến trình Chromium chết thì lần gọi sau khởi động lại.
"""

import asyncio
import logging

from playwright.async_api import Browser, async_playwright

from app.config.settings import CRAWL_MAX_CONCURRENT_PAGES, CRAWL_NAVIGATION_TIMEOUT_MS

logger = logging.getLogger("fuurin.browser")

# Trích toàn bộ CSS của trang; try/catch cho stylesheet cross-origin bị chặn.
_COLLECT_CSS_JS = """
    () => Array.from(document.styleSheets)
        .map(styleSheet => {
            try {
                return Array.from(styleSheet.cssRules).map(rule => rule.cssText).join('\\n');
            } catch (error) {
                return '';
            }
        })
        .join('\\n')
"""


class BrowserService:
    def __init__(self, max_concurrent_pages: int = CRAWL_MAX_CONCURRENT_PAGES):
        self._playwright = None
        self._browser: Browser | None = None
        self._start_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent_pages)

    async def start(self) -> None:
        """Khởi động sẵn lúc app start để request đầu tiên không phải chờ."""
        await self._ensure_browser()

    async def stop(self) -> None:
        async with self._start_lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception:
                    logger.exception("Không đóng được browser")
                self._browser = None
            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                except Exception:
                    logger.exception("Không dừng được playwright")
                self._playwright = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is not None and self._browser.is_connected():
            return self._browser

        async with self._start_lock:
            # Kiểm tra lại sau khi giành được lock: có thể coroutine khác vừa khởi động xong.
            if self._browser is not None and self._browser.is_connected():
                return self._browser

            if self._playwright is None:
                self._playwright = await async_playwright().start()

            logger.info("Khởi động Chromium dùng chung cho crawl")
            self._browser = await self._playwright.chromium.launch(
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            return self._browser

    async def fetch_page(
        self,
        url: str,
        timeout_ms: int = CRAWL_NAVIGATION_TIMEOUT_MS,
    ) -> tuple[str, str]:
        """Mở `url`, trả về (html, css). Luôn đóng context kể cả khi lỗi."""
        async with self._semaphore:
            browser = await self._ensure_browser()
            context = await browser.new_context()
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                css_content = await page.evaluate(_COLLECT_CSS_JS)
                html_content = await page.content()
                return html_content, css_content
            finally:
                await context.close()


browser_service = BrowserService()
