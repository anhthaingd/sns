"""DaiJob — tin tiếng Nhật, có mô tả công việc đầy đủ.

Nhãn <dt> gồm: 勤務地 (nơi làm), 年収 (lương năm), 英語能力, 中国語能力, 仕事内容.
**Không có nhãn 日本語能力**: trang này viết cho người đọc tiếng Nhật nên coi
việc đó là mặc định. Vì vậy yêu cầu tiếng Nhật phải dò trong phần 仕事内容 chứ
không có trường sẵn — và nếu không dò được thì để trống, không bịa.
"""

import re

from bs4 import BeautifulSoup

from app.services.etl.parsers.base import RawJob, absolute_url, attr_of, definition_pairs, text_of

SOURCE = "daijob"
BASE_URL = "https://www.daijob.com"

_JOB_ID = re.compile(r"/jobs/detail/(\d+)")
# Cửa sổ văn bản quanh chữ 日本語 để dò trình độ; giới hạn độ dài để không vơ
# nhầm câu khác trong mô tả.
_JAPANESE_WINDOW = re.compile(r"日本語[^。\n]{0,30}")


def list_url(page: int) -> str:
    return f"{BASE_URL}/jobs/search_result?job_post_language=2&job_search_form_hidden=1&page={page}"


# Tin ẩn danh nhà tuyển dụng không bọc tên công ty trong thẻ <a>. Đo được:
# 23/100 tin crawl thật rơi vào trường hợp này và bị mất trắng tên công ty.
_UNDISCLOSED = "Công ty chưa công bố tên"


def _company_name(card) -> str:
    """Tên công ty: ưu tiên link, không có thì lấy text của khối header."""
    link = card.select_one(".job-card__header-info a")
    if link is not None and text_of(link):
        return text_of(link)

    header = card.select_one(".job-card__header-info")
    if header is None:
        return _UNDISCLOSED

    # Bỏ khối pill (直接採用, ★, cấp bậc) để còn lại đúng phần tên.
    tags = header.select_one(".job-card__tags")
    if tags is not None:
        tags.decompose()
    return text_of(header) or _UNDISCLOSED


def _japanese_requirement(text: str) -> str | None:
    found = _JAPANESE_WINDOW.search(text)
    return found.group(0) if found else None


def parse_jobs(html: str) -> list[RawJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[RawJob] = []

    for card in soup.select(".job-card-wrap"):
        title_link = card.select_one(".job-card__title a")
        href = attr_of(title_link, "href")
        found = _JOB_ID.search(href or "")
        if not found:
            continue

        # Truyen CA khoi .job-card__detail chu khong phai thẻ <dl> đầu tiên:
        # DaiJob tách làm hai <dl>, cái thứ hai chứa 仕事内容 (mô tả công việc).
        fields = definition_pairs(card.select_one(".job-card__detail"))
        card_text = text_of(card)
        company_name = _company_name(card)

        jobs.append(
            RawJob(
                source=SOURCE,
                source_id=found.group(1),
                url=absolute_url(BASE_URL, href) or "",
                title=text_of(title_link),
                company_name=company_name,
                location_text=fields.get("勤務地"),
                salary_text=fields.get("年収"),
                employment_text=text_of(card.select_one(".job-card__tags")),
                japanese_text=_japanese_requirement(card_text),
                english_text=fields.get("英語能力"),
                description=fields.get("仕事内容", ""),
                raw_text=card_text,
            )
        )
    return jobs
