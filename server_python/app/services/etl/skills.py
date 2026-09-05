"""Trích kỹ năng từ văn bản tự do bằng từ điển.

Đây là cách thay cho LLM ở bước "job này yêu cầu những kỹ năng gì". Với tên
công nghệ (danh từ riêng) thì tra từ điển chính xác hơn và rẻ hơn hẳn — đó cũng
là cách các sàn tuyển dụng làm trước khi có LLM.

Ba kiểu khớp, vì dữ liệu trộn tiếng Anh và tiếng Nhật:

- alias Latin        -> khớp theo ranh giới từ, KHÔNG phân biệt hoa thường
- alias chứa CJK     -> khớp chuỗi con (tiếng Nhật không có dấu cách)
- case_sensitive     -> ranh giới từ, CÓ phân biệt hoa thường; dành cho những
                        alias trùng với từ thông dụng ("Go", "Rust", "Rails")
"""

import json
import re
from functools import lru_cache
from pathlib import Path

SKILLS_FILE = Path(__file__).resolve().parents[2] / "data" / "skills.json"

# Ranh giới "từ" tự viết thay cho \b: \b không hoạt động với alias kết thúc bằng
# ký tự không phải chữ ("C++", "C#", ".NET") vì \b cần một bên là ký tự chữ.
_BOUNDARY_BEFORE = r"(?<![0-9A-Za-z])"
_BOUNDARY_AFTER = r"(?![0-9A-Za-z])"

_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")


def _has_cjk(text: str) -> bool:
    return bool(_CJK.search(text))


@lru_cache(maxsize=1)
def _load() -> tuple[dict, list[tuple[re.Pattern, str]], list[tuple[str, str]]]:
    """Trả về (metadata theo canonical, danh sách regex, danh sách alias CJK)."""
    data = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))

    meta: dict[str, dict] = {}
    patterns: list[tuple[re.Pattern, str]] = []
    substrings: list[tuple[str, str]] = []

    for skill in data["skills"]:
        canonical = skill["canonical"]
        meta[canonical] = {"category": skill["category"]}

        latin = [a for a in skill.get("aliases", []) if not _has_cjk(a)]
        cjk = [a for a in skill.get("aliases", []) if _has_cjk(a)]
        strict = skill.get("case_sensitive_aliases", [])

        if latin:
            joined = "|".join(re.escape(a) for a in sorted(latin, key=len, reverse=True))
            patterns.append((re.compile(f"{_BOUNDARY_BEFORE}(?:{joined}){_BOUNDARY_AFTER}", re.IGNORECASE), canonical))
        if strict:
            joined = "|".join(re.escape(a) for a in sorted(strict, key=len, reverse=True))
            patterns.append((re.compile(f"{_BOUNDARY_BEFORE}(?:{joined}){_BOUNDARY_AFTER}"), canonical))
        for alias in cjk:
            substrings.append((alias, canonical))

    return meta, patterns, substrings


def extract_skills(*texts: str | None) -> list[str]:
    """Danh sách kỹ năng chuẩn hoá tìm được trong các đoạn văn bản đưa vào.

    Kết quả sắp xếp theo bảng chữ cái để hai lần chạy trên cùng dữ liệu luôn cho
    cùng kết quả — điều kiện để test được và để so sánh giữa các lần crawl.
    """
    blob = "\n".join(t for t in texts if t)
    if not blob:
        return []

    _, patterns, substrings = _load()
    found = {canonical for pattern, canonical in patterns if pattern.search(blob)}
    found.update(canonical for alias, canonical in substrings if alias in blob)
    return sorted(found)


def skill_category(canonical: str) -> str | None:
    meta, _, _ = _load()
    entry = meta.get(canonical)
    return entry["category"] if entry else None


def all_skills() -> list[str]:
    meta, _, _ = _load()
    return sorted(meta)
