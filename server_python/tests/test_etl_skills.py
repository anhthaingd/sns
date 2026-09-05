"""Test bộ trích kỹ năng bằng từ điển."""

import pytest
from app.services.etl.skills import all_skills, extract_skills, skill_category


def test_dictionary_is_loaded():
    assert len(all_skills()) > 100
    assert skill_category("Kubernetes") == "devops"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Backend Engineer. Python, FastAPI, MongoDB, Docker, Kubernetes, AWS.",
            {"AWS", "Docker", "FastAPI", "Kubernetes", "MongoDB", "Python"},
        ),
        # Tiếng Nhật: không có dấu cách nên phải khớp chuỗi con
        (
            "バックエンドエンジニア Python/Go マイクロサービス基盤開発 機械学習",
            {"Go", "Machine Learning", "Microservices", "Python"},
        ),
        # Ký tự đặc biệt trong tên công nghệ
        ("We need C++ and C# and .NET and Next.js", {"ASP.NET", "C#", "C++", "Next.js"}),
        ("海上物流オペレーター", {"Logistics"}),
    ],
)
def test_extract_skills(text, expected):
    assert set(extract_skills(text)) == expected


def test_no_false_positive_on_everyday_words():
    """Nguồn có cả tin logistics và giáo dục, đầy từ trùng tên công nghệ.

    "express delivery", "train rails", "go", "swift", "rust" đều là từ thông
    dụng — nếu khớp không phân biệt hoa thường thì mọi tin vận tải sẽ được gắn
    kỹ năng lập trình.
    """
    assert extract_skills("The express delivery train rails go swift and rust never sleeps") == []


def test_no_false_positive_on_direct_hire_label():
    """`直接採用` (tuyển trực tiếp) có ở MỌI thẻ DaiJob.

    Từng bị đọc thành kỹ năng "Recruiting" và gắn nhầm cho 90/420 tin.
    """
    assert "Recruiting" not in extract_skills("直接採用 スタッフレベル 営業アシスタント")


def test_java_and_javascript_are_distinguished():
    assert extract_skills("Java developer") == ["Java"]
    assert extract_skills("JavaScript developer") == ["JavaScript"]


def test_result_is_sorted_for_stable_output():
    """Hai lần chạy trên cùng dữ liệu phải cho cùng kết quả, nếu không thì
    không so sánh được giữa các lần crawl và test sẽ chập chờn."""
    text = "Docker, AWS, Python, Kubernetes"
    assert extract_skills(text) == sorted(extract_skills(text))
    assert extract_skills(text) == extract_skills(text)
