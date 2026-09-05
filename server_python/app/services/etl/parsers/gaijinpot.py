"""GaijinPot — nguồn có cấu trúc tốt nhất.

Mỗi thẻ việc làm có sẵn danh sách <dt>/<dd>: Date, Company, Salary, Location,
**Japanese**, **Requirements**. Trường `Japanese` là thứ quý nhất trong cả bốn
nguồn vì nó nói thẳng yêu cầu tiếng Nhật — tiêu chí lọc số một của thị trường
này.
"""

import re

from bs4 import BeautifulSoup

from app.services.etl.parsers.base import RawJob, absolute_url, attr_of, definition_pairs, text_of

SOURCE = "gaijinpot"
BASE_URL = "https://jobs.gaijinpot.com"

_JOB_ID = re.compile(r"/job/(\d+)")


def list_url(page: int) -> str:
    return f"{BASE_URL}/job/index/page/{page}"


def parse_jobs(html: str) -> list[RawJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[RawJob] = []
    # Cùng một tin có thể xuất hiện hai lần trên trang (thẻ nổi bật + thẻ
    # thường). Không loại thì báo cáo ETL đếm thừa và tốn công ghi hai lần.
    seen: set[str] = set()

    # Chọn MỌI thẻ `.gpjs-open-link` chứ không chỉ `.card--premium` như bản
    # crawl cũ: trang có 51 thẻ nhưng chỉ 26 thẻ premium, tức là bản cũ bỏ sót
    # gần một nửa số tin.
    for card in soup.select(".card.gpjs-open-link"):
        link = card.select_one("h3.card-heading a") or card.select_one("a.card-image")
        href = attr_of(link, "href")
        found = _JOB_ID.search(href or "")
        if not found or found.group(1) in seen:
            continue
        seen.add(found.group(1))

        # Truyền cả thẻ: nếu trang tách thành nhiều <dl> thì vẫn gom đủ.
        fields = definition_pairs(card)
        image = card.select_one("img.img-thumbnail")

        jobs.append(
            RawJob(
                source=SOURCE,
                source_id=found.group(1),
                url=absolute_url(BASE_URL, href) or "",
                title=text_of(link),
                company_name=fields.get("Company", "") or (attr_of(image, "title") or ""),
                logo_url=attr_of(image, "src"),
                location_text=fields.get("Location"),
                salary_text=fields.get("Salary"),
                employment_text=text_of(card.select_one(".card-label")),
                japanese_text=fields.get("Japanese"),
                english_text=fields.get("Requirements"),
                description=fields.get("Requirements", ""),
                raw_text=text_of(card),
            )
        )
    return jobs
