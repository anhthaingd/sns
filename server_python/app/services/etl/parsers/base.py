"""Kiểu dữ liệu và tiện ích dùng chung cho mọi parser."""

from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import Tag


@dataclass
class RawJob:
    """Tin tuyển dụng còn ở dạng thô — mọi trường vẫn là văn bản.

    Cố ý KHÔNG chuẩn hoá ở đây: parser chỉ biết cấu trúc HTML của một trang cụ
    thể, còn cách hiểu "350万円" hay "ビジネスレベル" là kiến thức chung, để ở
    `extract.py` cho cả bốn nguồn dùng lại.
    """

    source: str
    source_id: str
    url: str
    title: str
    company_name: str = ""
    company_source_id: str | None = None
    company_url: str | None = None
    logo_url: str | None = None
    location_text: str | None = None
    salary_text: str | None = None
    employment_text: str | None = None
    japanese_text: str | None = None
    english_text: str | None = None
    description: str = ""
    # Toàn bộ text của thẻ, dùng để dò kỹ năng và số năm kinh nghiệm khi các
    # trường có cấu trúc không đủ.
    raw_text: str = ""


@dataclass
class RawCompany:
    source: str
    source_id: str
    name: str
    url: str | None = None
    website: str | None = None
    logo_url: str | None = None
    location: str | None = None
    description: str = ""
    job_count: int = 0
    benefits: list[str] = field(default_factory=list)


def text_of(node: Tag | None, separator: str = " ") -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(separator, strip=True).split())


def attr_of(node: Tag | None, name: str) -> str | None:
    if node is None:
        return None
    value = node.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def absolute_url(base: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base, href)


def definition_pairs(container: Tag | None) -> dict[str, str]:
    """Đọc cặp <dt>/<dd> thành dict — cả GaijinPot lẫn DaiJob đều dùng cấu trúc này.

    BeautifulSoup không ghép sẵn dt với dd nên phải duyệt tuần tự: mỗi <dt> ăn
    theo các <dd> đứng sau nó cho tới <dt> kế tiếp.
    """
    if container is None:
        return {}

    pairs: dict[str, str] = {}
    current_label: str | None = None
    for node in container.find_all(["dt", "dd"]):
        if node.name == "dt":
            current_label = text_of(node)
        elif current_label:
            value = text_of(node)
            pairs[current_label] = f"{pairs[current_label]} {value}".strip() if current_label in pairs else value
    return pairs
