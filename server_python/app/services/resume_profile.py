"""Rút ra hồ sơ có cấu trúc từ một CV để so khớp với tin tuyển dụng.

Dùng chung cho ba đường: lúc người dùng lưu CV, lúc backfill dữ liệu cũ, và lúc
sinh CV mẫu để test. Một bản duy nhất để ba đường không lệch nhau.
"""

import hashlib
import re

from app.models.resume import Resume
from app.services.etl.extract import parse_language_level
from app.services.etl.skills import extract_skills

# Người dùng gõ tự do vào ô "Languages": "JP", "Japanese N2", "日本語", "Tiếng Nhật".
_JAPANESE_HINT = re.compile(r"\bjp\b|japan|japanese|日本語|nihongo|tiếng nhật", re.IGNORECASE)
_ENGLISH_HINT = re.compile(r"\ben\b|english|英語|tiếng anh", re.IGNORECASE)

_YEAR_RANGE = re.compile(r"(\d{4})")


def _language_level(entries: list[str], hint: re.Pattern, extra_texts: list[str]) -> str | None:
    """Trình độ ngôn ngữ suy từ mục Languages, có tham chiếu chứng chỉ.

    "JP" đứng một mình không nói gì về trình độ, nhưng nếu trong mục chứng chỉ
    có "JLPT N2" thì đã đủ căn cứ.
    """
    for entry in entries:
        if not hint.search(entry or ""):
            continue
        level = parse_language_level(entry)
        if level:
            return level
        # Có nhắc tới ngôn ngữ mà không nói trình độ -> tìm trong chứng chỉ.
        for text in extra_texts:
            if hint.search(text) or re.search(r"\bN[1-5]\b", text):
                level = parse_language_level(text)
                if level:
                    return level
        # Vẫn không rõ: coi như dùng được ở mức giao tiếp, còn hơn để trống
        # (để trống thì mọi tin yêu cầu ngôn ngữ đó đều bị coi là chưa đạt).
        return "conversational"
    return None


def total_years(experiences: list[dict]) -> int | None:
    """Cộng số năm từ mục kinh nghiệm; chỉ đọc được năm dạng 4 chữ số."""
    years = 0
    counted = False
    for exp in experiences or []:
        start = _YEAR_RANGE.search(str(exp.get("startTime", "")))
        end = _YEAR_RANGE.search(str(exp.get("endTime", "")))
        if not start:
            continue
        start_year = int(start.group(1))
        # Chưa điền ngày kết thúc = đang làm; dùng năm hiện tại là hợp lý hơn
        # bỏ qua hẳn mục đó.
        end_year = int(end.group(1)) if end else start_year + 1
        if end_year >= start_year:
            years += end_year - start_year
            counted = True
    return years if counted else None


def resume_text(resume: Resume) -> str:
    """Văn bản đưa vào embedding.

    Cố ý BỎ tên, email, số điện thoại, địa chỉ: chúng không giúp gì cho việc so
    khớp năng lực, mà lại là dữ liệu cá nhân đi ra khỏi backend.
    """
    parts = [
        resume.position or "",
        "Skills: " + ", ".join(resume.skills_normalized or resume.skills or []),
        resume.objective or "",
        " ".join(f"{e.get('position', '')} {e.get('description', '')}" for e in resume.experiences or []),
        " ".join(f"{p.get('name', '')} {p.get('tech', '')}" for p in resume.projects or []),
        f"{resume.educationMajor or ''} {resume.educationName or ''}",
    ]
    return ". ".join(p.strip() for p in parts if p and p.strip())[:4000]


def profile_fields(resume: Resume) -> dict:
    """Các trường suy ra được từ nội dung CV. Không ghi đè giá trị người dùng tự nhập."""
    certificate_texts = [str(c.get("name", "")) for c in resume.certificates or []]
    extra = certificate_texts + [resume.objective or ""]

    skills = extract_skills(
        " ".join(resume.skills or []),
        resume.objective or "",
        resume.position or "",
        " ".join(f"{p.get('tech', '')} {p.get('description', '')}" for p in resume.projects or []),
        " ".join(f"{e.get('description', '')}" for e in resume.experiences or []),
    )

    return {
        "japanese_level": _language_level(resume.languages or [], _JAPANESE_HINT, extra),
        "english_level": _language_level(resume.languages or [], _ENGLISH_HINT, extra),
        "years_of_experience": total_years(resume.experiences),
        "skills_normalized": skills,
    }


def apply_profile(resume: Resume, *, overwrite: bool = False) -> Resume:
    """Điền các trường suy ra được. Mặc định chỉ điền vào chỗ đang trống."""
    for key, value in profile_fields(resume).items():
        if value in (None, [], ""):
            continue
        if overwrite or not getattr(resume, key, None):
            setattr(resume, key, value)
    return resume


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
