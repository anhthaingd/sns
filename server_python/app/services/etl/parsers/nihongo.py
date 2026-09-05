"""Nihongo Engineer — nguồn duy nhất có trang hồ sơ doanh nghiệp riêng.

Mỗi tin trỏ tới `/companies/{id}`, và trang đó có mô tả công ty thật, website,
địa điểm, số vị trí đang tuyển. Đây là dữ liệu để trả lời "công ty A làm gì,
cần gì" chứ không chỉ "tin tuyển dụng A yêu cầu gì".
"""

import re

from bs4 import BeautifulSoup

from app.services.etl.parsers.base import (
    RawCompany,
    RawJob,
    absolute_url,
    attr_of,
    text_of,
)

SOURCE = "nihongo"
BASE_URL = "https://nihongo-engineer.com"

_JOB_ID = re.compile(r"/jobs/(\d+)")
_COMPANY_ID = re.compile(r"/companies/(\d+)")
_OPEN_JOBS = re.compile(r"(\d+)\s*open jobs", re.IGNORECASE)

# Thẻ việc làm gắn 3 nhãn không có class phân biệt: địa điểm, lương, hình thức.
# Nhận dạng bằng NỘI DUNG chứ không bằng vị trí, vì thứ tự nhãn có thể đổi.
_SALARY_HINT = re.compile(r"JPY|万|¥|M\b", re.IGNORECASE)
_WORKSTYLE_HINT = re.compile(r"office|remote|hybrid", re.IGNORECASE)


def list_url(page: int) -> str:
    return f"{BASE_URL}/?page={page}"


def company_url(company_source_id: str) -> str:
    return f"{BASE_URL}/companies/{company_source_id}"


def company_list_url(page: int) -> str:
    return f"{BASE_URL}/companies?page={page}"


def parse_company_ids(html: str) -> list[str]:
    """Danh sách id công ty trên trang `/companies`.

    Cần trang này vì trang chủ việc làm bị một công ty môi giới chiếm gần hết:
    5 trang tin chỉ trỏ tới ĐÚNG MỘT hồ sơ doanh nghiệp. Đi từ danh sách công ty
    mới lấy được nhiều hồ sơ thật.
    """
    soup = BeautifulSoup(html, "html.parser")
    ids: list[str] = []
    for link in soup.select('.companies-list-item a[href^="/companies/"]'):
        found = _COMPANY_ID.search(attr_of(link, "href") or "")
        if found and found.group(1) not in ids:
            ids.append(found.group(1))
    return ids


def _classify_tags(tags: list[str]) -> tuple[str | None, str | None, str | None]:
    """Trả về (địa điểm, lương, hình thức làm việc) từ các nhãn không có nhãn tên."""
    location = salary = workstyle = None
    for tag in tags:
        if _SALARY_HINT.search(tag):
            salary = salary or tag
        elif _WORKSTYLE_HINT.search(tag):
            workstyle = workstyle or tag
        else:
            location = location or tag
    return location, salary, workstyle


def parse_jobs(html: str) -> list[RawJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[RawJob] = []

    for item in soup.select("li.job-item"):
        title_link = item.select_one("a.job-item__title")
        href = attr_of(title_link, "href")
        found = _JOB_ID.search(href or "")
        if not found:
            continue

        company_link = item.select_one('a[href^="/companies/"]')
        company_id_match = _COMPANY_ID.search(attr_of(company_link, "href") or "")
        logo = item.select_one(".company-logo__inner")
        logo_style = attr_of(logo, "style") or ""
        logo_url = None
        if "url(" in logo_style:
            raw = logo_style.split("url(", 1)[1].split(")", 1)[0].strip("'\"")
            logo_url = absolute_url(BASE_URL, raw)

        tags = [text_of(t) for t in item.select(".job__tag-desc")]
        location, salary, workstyle = _classify_tags(tags)

        jobs.append(
            RawJob(
                source=SOURCE,
                source_id=found.group(1),
                url=absolute_url(BASE_URL, href) or "",
                title=text_of(title_link),
                company_name=text_of(item.select_one(".job-item__contract-type")),
                company_source_id=company_id_match.group(1) if company_id_match else None,
                company_url=company_url(company_id_match.group(1)) if company_id_match else None,
                logo_url=logo_url or attr_of(logo, "alt"),
                location_text=location,
                salary_text=salary,
                employment_text=workstyle,
                description=text_of(item),
                raw_text=text_of(item),
            )
        )
    return jobs


def parse_company(html: str, source_id: str) -> RawCompany | None:
    soup = BeautifulSoup(html, "html.parser")
    name = text_of(soup.select_one("h1.headline"))
    if not name:
        return None

    website_link = soup.select_one(".company-header a.link")
    logo = soup.select_one("img.company-logo")
    open_jobs = _OPEN_JOBS.search(text_of(soup.select_one(".company-nav")))

    return RawCompany(
        source=SOURCE,
        source_id=source_id,
        name=name,
        url=company_url(source_id),
        website=attr_of(website_link, "href"),
        logo_url=absolute_url(BASE_URL, attr_of(logo, "src")),
        # "Shinjuku, Tokyo, Japan –" — bỏ dấu gạch nối dính ở cuối.
        location=text_of(soup.select_one(".company-header span.ts-quiet")).rstrip(" –-"),
        description=text_of(soup.select_one("article.company-description"), separator="\n"),
        job_count=int(open_jobs.group(1)) if open_jobs else 0,
    )
