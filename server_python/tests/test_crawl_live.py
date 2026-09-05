"""Canh selector của trang nguồn — chạy trên trang THẬT, cần internet.

    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm \
        -e RUN_CRAWL_TESTS=1 api-tests python -m pytest tests/test_crawl_live.py

Khác với `test_etl_parsers.py` (chạy trên HTML đã lưu, luôn xanh, chạy trong
CI): bộ này gọi ra trang thật để phát hiện khi trang nguồn đổi giao diện. Đỏ ở
đây nghĩa là **selector đã mục rữa**, không phải code hỏng — nên nó nằm ở
workflow riêng (`crawl-health.yml`) để không làm đỏ badge CI chính.
"""

import os

import pytest
from app.services.browser import browser_service
from app.services.etl.parsers import SOURCES, nihongo


@pytest.fixture(autouse=True, scope="module")
def _close_browser():
    """Đóng Chromium sau khi chạy xong.

    `browser_service` là singleton sống theo vòng đời ứng dụng; trong tiến trình
    pytest không có ai đóng nó, và tiến trình con Chromium còn sống sẽ giữ cho
    pytest không thoát.
    """
    yield
    import asyncio

    asyncio.run(browser_service.stop())


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_CRAWL_TESTS") != "1",
    reason="cần internet, bật bằng RUN_CRAWL_TESTS=1",
)

# Ngưỡng tối thiểu, thấp hơn số thật khá nhiều để không đỏ chỉ vì trang hôm đó
# ít tin hơn thường lệ.
MIN_JOBS = {"gaijinpot": 20, "daijob": 10, "nihongo": 10, "linkedin": 5}


@pytest.mark.parametrize("source", sorted(MIN_JOBS))
async def test_source_still_returns_jobs(source):
    html, _css = await browser_service.fetch_page(SOURCES[source]["list_url"](1))
    jobs = SOURCES[source]["parse"](html)

    assert len(jobs) >= MIN_JOBS[source], (
        f"{source}: chỉ parse được {len(jobs)} tin (tối thiểu {MIN_JOBS[source]}) — selector nhiều khả năng đã lỗi thời"
    )
    assert all(j.title and j.source_id and j.url.startswith("http") for j in jobs)


async def test_nihongo_company_profile_still_parses():
    html, _css = await browser_service.fetch_page(nihongo.company_url("2"))
    company = nihongo.parse_company(html, "2")
    assert company is not None and company.name
    assert company.description, "mất phần mô tả doanh nghiệp — cấu trúc trang đã đổi"


async def test_nihongo_company_list_still_parses():
    html, _css = await browser_service.fetch_page(nihongo.company_list_url(1))
    assert len(nihongo.parse_company_ids(html)) >= 5
