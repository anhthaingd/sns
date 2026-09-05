"""LinkedIn JP — nguồn nghèo dữ liệu nhất và hay bị chặn.

Chỉ lấy được tiêu đề, công ty, địa điểm, ngày đăng. Không có lương, không có
yêu cầu ngôn ngữ. Vẫn giữ vì bổ sung được nhiều vị trí ở công ty lớn mà ba
nguồn kia không có.
"""

import re

from bs4 import BeautifulSoup

from app.services.etl.parsers.base import RawJob, attr_of, text_of

SOURCE = "linkedin"
JOBS_PER_PAGE = 25

_JOB_ID = re.compile(r"urn:li:jobPosting:(\d+)")


def list_url(page: int) -> str:
    offset = (page - 1) * JOBS_PER_PAGE
    return (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        "?currentJobId=3942468982&keywords=information%2Btechnology&location=japan"
        f"&start={offset}"
    )


def parse_jobs(html: str) -> list[RawJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[RawJob] = []

    for card in soup.select(".base-search-card"):
        found = _JOB_ID.search(attr_of(card, "data-entity-urn") or "")
        if not found:
            continue

        link = card.select_one("a.base-card__full-link")
        title = text_of(card.select_one(".base-search-card__title")) or text_of(card.select_one("span.sr-only"))
        if not title:
            continue

        # Bỏ query string theo dõi để URL ổn định giữa các lần crawl — nếu giữ,
        # mỗi lần crawl lại sinh URL khác nhau cho cùng một tin.
        href = (attr_of(link, "href") or "").split("?")[0]

        jobs.append(
            RawJob(
                source=SOURCE,
                source_id=found.group(1),
                url=href,
                title=title,
                company_name=text_of(card.select_one(".base-search-card__subtitle")),
                location_text=text_of(card.select_one(".job-search-card__location")),
                description=title,
                raw_text=text_of(card),
            )
        )
    return jobs
