"""Làm giàu tin tuyển dụng bằng trang chi tiết.

Vì sao cần: trang danh sách của cả bốn nguồn chỉ có tiêu đề, lương, địa điểm.
Đo được sau khi ETL 420 tin từ trang danh sách:

    biết yêu cầu tiếng Nhật :  87/420  (79% không rõ)
    có kỹ năng              : 231/420
    có mô tả dài            : 117/420

Trong khi trang chi tiết có đủ, ví dụ nihongo-engineer ghi thẳng
"Conversational (N3)" — đúng trường quan trọng nhất của thị trường Nhật.

Cố ý dùng MỘT bộ trích chung cho cả bốn nguồn thay vì viết bốn parser chi tiết:
các hàm trong `extract.py` vốn làm việc trên văn bản thuần, nên chỉ cần bóc
phần nội dung chính của trang là dùng lại được. Ít code hơn, và khi một trang
đổi giao diện thì chỉ mất phần làm giàu chứ tin vẫn còn.
"""

import logging
import re

from bs4 import BeautifulSoup

from app.services.etl.extract import (
    clean_text,
    parse_language_level,
    parse_min_years,
    parse_salary,
)
from app.services.etl.skills import extract_skills

logger = logging.getLogger("fuurin.etl.detail")

# Thẻ chỉ chứa điều hướng/quảng cáo — bỏ đi trước khi đọc text, nếu không kỹ
# năng sẽ bị nhặt từ mục "việc làm liên quan" ở thanh bên.
_NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]

# Cửa sổ quanh từ khoá ngôn ngữ. Giới hạn độ dài để không vơ sang câu khác.
# Có cả emoji cờ: nihongo-engineer hiển thị "🇯🇵 Conversational (N3)" mà không
# hề có chữ "Japanese" nào — chỉ dò theo chữ là mất trắng trường quan trọng nhất.
_JAPANESE_WINDOW = re.compile(r"(?:日本語|Japanese|語学力|🇯🇵)[^。\n]{0,40}", re.IGNORECASE)
_ENGLISH_WINDOW = re.compile(r"(?:英語|English|🇬🇧|🇺🇸)[^。\n]{0,40}", re.IGNORECASE)

# Mã JLPT đủ đặc trưng để dò trên toàn trang mà không sợ khớp nhầm, dùng làm
# phương án dự phòng khi không tìm được cửa sổ ngôn ngữ nào.
_JLPT_ANYWHERE = re.compile(r"\bN[1-5]\b")

MAX_DESCRIPTION_CHARS = 4000


def _main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return clean_text(main.get_text(" ", strip=True))


def enrich_from_detail(html: str) -> dict:
    """Trả về các trường đọc thêm được. Chỉ chứa khoá thực sự có giá trị.

    Caller có nhiệm vụ chỉ ghi đè khi giá trị cũ đang trống — dữ liệu có cấu
    trúc sẵn ở trang danh sách (ví dụ trường `Japanese` của GaijinPot) đáng tin
    hơn phép dò trong văn bản tự do.
    """
    text = _main_text(html)
    if not text:
        return {}

    result: dict = {"description": text[:MAX_DESCRIPTION_CHARS]}

    skills = extract_skills(text)
    if skills:
        result["required_skills"] = skills

    japanese_window = _JAPANESE_WINDOW.search(text)
    japanese_level = parse_language_level(japanese_window.group(0)) if japanese_window else None
    if japanese_level is None:
        jlpt = _JLPT_ANYWHERE.search(text)
        japanese_level = parse_language_level(jlpt.group(0)) if jlpt else None
    if japanese_level:
        result["required_japanese"] = japanese_level

    english_window = _ENGLISH_WINDOW.search(text)
    if english_window:
        level = parse_language_level(english_window.group(0))
        if level:
            result["required_english"] = level

    min_years = parse_min_years(text)
    if min_years is not None:
        result["min_years"] = min_years

    salary_min, salary_max = parse_salary(text)
    if salary_min is not None:
        result["salary_min"] = salary_min
        result["salary_max"] = salary_max

    return result
