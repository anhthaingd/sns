"""Khoá lại các tính chất mà buổi demo phụ thuộc vào.

Không cần Mongo, không cần embedder: chỉ dựng CV bằng đúng hàm mà script seed
dùng rồi kiểm tính chất. Mục đích là để CV demo không âm thầm trôi đi khi có
người sửa nội dung cho "đẹp hơn" mà không nhận ra hệ quả.
"""

import re

import pytest
from app.models.resume import Resume
from app.services.resume_profile import resume_text, total_years
from scripts.seed_demo_user import (
    CONTRAST_ACCOUNT,
    DEMO_ACCOUNT,
    _minimal_pdf,
    fill_resume,
)


def build(account: dict) -> Resume:
    data = account["resume"]
    # Tên chứng chỉ vẫn truyền vào vì nó tham gia vào việc suy ra trình độ ngôn
    # ngữ; chỉ bỏ phần ghi file ra đĩa.
    certificates = [{"name": name, "url": ""} for name, _ in data["certificates"]]
    # `Resume()` đòi Beanie đã init sẵn collection; `model_construct` dựng đối
    # tượng với đúng giá trị mặc định mà không cần Mongo — vừa đủ cho các kiểm
    # tra thuần tuý ở đây.
    return fill_resume(Resume.model_construct(), data, certificates)


@pytest.fixture(scope="module")
def demo() -> Resume:
    return build(DEMO_ACCOUNT)


@pytest.fixture(scope="module")
def contrast() -> Resume:
    return build(CONTRAST_ACCOUNT)


def test_two_demo_accounts_produce_identical_embedding_text(demo, contrast):
    """Hai tài khoản demo chỉ được khác nhau ở trình độ tiếng Nhật.

    Nếu văn bản đem đi embedding khác nhau thì vector khác nhau, và chênh lệch
    điểm giữa hai tài khoản không còn quy được về tiếng Nhật — buổi demo sẽ
    chứng minh nhầm thứ. Đã đo: chỉ sửa một câu trong `objective` là đủ làm
    hỏng phép so sánh này.
    """
    assert resume_text(demo) == resume_text(contrast)


def test_embedding_text_never_mentions_japanese(demo):
    """Tiếng Nhật chỉ được nằm ở mục ngôn ngữ và chứng chỉ, không nằm trong văn bản."""
    text = resume_text(demo).lower()
    for word in ("nhật", "japanese", "jlpt", "日本語"):
        assert word not in text, f"'{word}' lọt vào văn bản embedding của CV demo"


def test_declared_years_match_the_experience_entries(demo):
    """Số năm tự khai phải khớp với mục kinh nghiệm — lệch là người xem hỏi ngay."""
    assert demo.years_of_experience == 4
    assert total_years(demo.experiences) == demo.years_of_experience


def test_language_levels_are_what_the_demo_script_says(demo, contrast):
    assert demo.japanese_level == "conversational"  # N3
    assert demo.english_level == "business"
    assert contrast.japanese_level is None
    assert contrast.english_level == "business"


def test_demo_cv_keeps_the_gaps_it_was_designed_to_show(demo):
    """CV cố ý thiếu vài kỹ năng để chức năng "còn thiếu gì" có nội dung."""
    assert {"Python", "FastAPI", "PostgreSQL", "Docker"} <= set(demo.skills_normalized)
    missing = {"Kubernetes", "Terraform", "Go"}
    assert not (missing & set(demo.skills_normalized)), "CV demo đã hết chỗ để chỉ ra thiếu sót"


def test_every_resume_section_is_filled(demo):
    """Mở trang CV lúc demo không được có mục nào trống."""
    for field in (
        "name",
        "position",
        "birthday",
        "email",
        "address",
        "phone",
        "github",
        "objective",
        "educationName",
        "educationMajor",
        "educationCompletion",
        "educationGPA",
    ):
        assert getattr(demo, field), f"CV demo còn trống mục {field}"
    for field in ("experiences", "projects", "skills", "languages", "certificates"):
        assert getattr(demo, field), f"CV demo còn trống mục {field}"


def test_generated_certificate_is_a_readable_pdf():
    """File chứng chỉ sinh kèm phải mở được — demo bấm vào mà 404/hỏng thì mất điểm."""
    raw = _minimal_pdf(["JLPT N3", "Issued: December 2024"])

    assert raw.startswith(b"%PDF-")
    assert raw.rstrip().endswith(b"%%EOF")

    # Bảng xref phải trỏ đúng vị trí từng object, nếu không trình đọc PDF sẽ báo hỏng.
    start = int(re.search(rb"startxref\s+(\d+)", raw).group(1))
    assert raw[start : start + 4] == b"xref"
    offsets = re.findall(rb"^(\d{10}) 00000 n", raw[start:], re.MULTILINE)
    assert len(offsets) == 5
    for number, offset in enumerate(offsets, start=1):
        assert raw[int(offset) :].startswith(f"{number} 0 obj".encode())
