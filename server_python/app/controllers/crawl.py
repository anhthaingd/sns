"""Tổng hợp tin tuyển dụng từ các trang ngoài.

Bốn hàm crawl trước đây gần như giống hệt nhau (chỉ khác URL, selector và vài
phép thay chuỗi) nhưng được chép thành 4 bản, kèm 4 khối `try/except` nuốt lỗi
giống nhau. Ở đây mô tả mỗi nguồn bằng dữ liệu (`CrawlSource`) và dùng chung
đúng một hàm xử lý.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from playwright.async_api import Error as PlaywrightError

from app.config.settings import CRAWL_CACHE_TTL_SECONDS
from app.errors import ApiError
from app.services.browser import browser_service
from app.utils.responses import ok
from app.utils.ttl_cache import TTLCache

logger = logging.getLogger("fuurin.crawl")

CRAWL_ERROR_MESSAGE = "Có lỗi xảy ra khi crawl dữ liệu"

# TTL cấu hình ở settings (CRAWL_CACHE_TTL_SECONDS) cùng chỗ với mọi nút khác.
_cache = TTLCache(ttl_seconds=CRAWL_CACHE_TTL_SECONDS, max_entries=64)


@dataclass(frozen=True)
class CrawlSource:
    name: str
    build_url: Callable[[int], str]
    selector: str
    # DaiJob cần cả thẻ bọc ngoài (class của nó mang style); các nguồn khác chỉ
    # lấy phần bên trong vì thẻ bọc chứa link/handler không dùng tới.
    keep_outer_tag: bool = False
    replacements: tuple[tuple[str, str], ...] = field(default_factory=tuple)


DAI_JOB = CrawlSource(
    name="dai_job",
    build_url=lambda page: (
        f"https://www.daijob.com/jobs/search_result?job_post_language=2&job_search_form_hidden=1&page={page}"
    ),
    selector=".job-card-wrap",
    keep_outer_tag=True,
    replacements=(
        ('href="/jobs', 'href="https://www.daijob.com/jobs'),
        ("data-src=", "src="),
    ),
)

LINKED_JP = CrawlSource(
    name="linked_jp_jobs",
    build_url=lambda page: (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        "?currentJobId=3942468982&keywords=information%2Btechnology&location=japan"
        f"&start={(page - 1) * 25}"
    ),
    selector=(
        ".base-card.relative.w-full.hover\\:no-underline.focus\\:no-underline"
        ".base-card--link.base-search-card.base-search-card--link.job-search-card"
    ),
    replacements=(
        ("data-delayed-url", "src"),
        (
            "base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]",
            "base-card__full-link",
        ),
    ),
)

NIHONGO = CrawlSource(
    name="nihongo",
    build_url=lambda page: f"https://nihongo-engineer.com/?page={page}",
    selector=".job-item",
    replacements=(("/upload/image_job", "https://nihongo-engineer.com/upload/image_job"),),
)

GAIJINPOT = CrawlSource(
    name="gaijinpot",
    build_url=lambda page: f"https://jobs.gaijinpot.com/job/index/page/{page}",
    selector=".card.card--premium.gpjs-open-link",
    replacements=(("/job/view", "https://jobs.gaijinpot.com/job/view"),),
)


async def _get_page_content_and_css(url: str) -> tuple[str, str]:
    """Điểm vào duy nhất tới trình duyệt.

    `scripts/browser_smoke.py` gọi đúng hàm này để smoke test đi qua chính code
    path mà crawl dùng thật — đừng đổi tên nếu chưa cập nhật script đó.
    """
    return await browser_service.fetch_page(url)


def _extract(html: str, source: CrawlSource) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for element in soup.select(source.selector):
        el_html = str(element) if source.keep_outer_tag else "".join(str(child) for child in element.children)
        for old, new in source.replacements:
            el_html = el_html.replace(old, new)
        items.append(el_html)
    return items


async def crawl_source(source: CrawlSource, cur_page: int = 1):
    cache_key = (source.name, cur_page)
    cached = _cache.get(cache_key)
    if cached is not None:
        return ok(**cached)

    try:
        html_content, css_content = await _get_page_content_and_css(source.build_url(cur_page))
    except PlaywrightError as err:
        # Trang nguồn timeout / chặn / đổi giao diện là chuyện thường ngày và
        # nằm ngoài tầm kiểm soát -> log ở mức warning, không phải lỗi hệ thống.
        logger.warning("Crawl %s trang %s thất bại: %s", source.name, cur_page, err)
        raise ApiError(502, CRAWL_ERROR_MESSAGE) from err

    payload = {"html": _extract(html_content, source), "css": css_content}
    # Chỉ cache khi thật sự lấy được job: cache một trang rỗng do bị chặn sẽ
    # khoá người dùng ở màn hình trống suốt 10 phút.
    if payload["html"]:
        _cache.set(cache_key, payload)
    return ok(**payload)


async def crawl_dai_job(cur_page: int = 1):
    return await crawl_source(DAI_JOB, cur_page)


async def crawl_linked(cur_page: int = 1):
    return await crawl_source(LINKED_JP, cur_page)


async def crawl_nihongo(cur_page: int = 1):
    return await crawl_source(NIHONGO, cur_page)


async def crawl_gaijinpot(cur_page: int = 1):
    return await crawl_source(GAIJINPOT, cur_page)
