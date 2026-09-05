"""Xây điều kiện tìm kiếm "chứa chuỗi" cho MongoDB.

Trước đây từ khoá người dùng gõ được nhét thẳng vào `{"$regex": search}`. Chỉ
cần gõ một dấu `[` là Mongo ném `Regular expression is invalid` và API trả 500;
một chuỗi như `(a+)+$` còn khiến máy chủ regex chạy rất lâu (ReDoS). Escape
toàn bộ ký tự đặc biệt để từ khoá luôn được hiểu là văn bản thuần.
"""

import re

from unidecode import unidecode

# Từ khoá dài vô hạn không giúp tìm chính xác hơn, chỉ tốn công quét.
MAX_SEARCH_LENGTH = 100

# Client gửi đúng các chuỗi này khi ô tìm kiếm trống.
EMPTY_VALUES = {"", "null", "undefined"}


def normalize_search(search: str | None) -> str | None:
    """Trả về từ khoá đã cắt gọn, hoặc None nếu coi như không tìm kiếm."""
    if not isinstance(search, str):
        return None
    cleaned = search.strip()
    if cleaned.lower() in EMPTY_VALUES:
        return None
    return cleaned[:MAX_SEARCH_LENGTH]


def contains(search: str, *, unaccent: bool = False) -> dict:
    """Điều kiện `chứa`, không phân biệt hoa thường, an toàn với ký tự đặc biệt."""
    keyword = unidecode(search) if unaccent else search
    return {"$regex": re.escape(keyword), "$options": "i"}
