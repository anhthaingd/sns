"""Test cho tầng chuẩn hoá dữ liệu tin tuyển dụng.

Toàn bộ là hàm thuần nên test chạy được mà không cần server, DB hay mạng.
Mọi chuỗi đầu vào ở đây đều **lấy nguyên văn từ dữ liệu thật đã crawl**, không
phải ví dụ bịa — đó là lý do chúng bắt được lỗi.
"""

import pytest
from app.services.etl.extract import (
    build_search_text,
    clean_text,
    is_remote,
    normalize_company_name,
    parse_employment_type,
    parse_language_level,
    parse_min_years,
    parse_prefecture,
    parse_salary,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # GaijinPot: lương tháng -> phải nhân 12
        ("¥250,000 ~ ¥300,000 / Month", (3_000_000, 3_600_000)),
        ("¥247,590 ~ ¥247,590 / Month", (2_971_080, 2_971_080)),
        # GaijinPot: viết tắt triệu
        ("¥3.8M ~ ¥5.0M / Year Negotiable", (3_800_000, 5_000_000)),
        # Nihongo Engineer
        ("3.6M - 5M JPY", (3_600_000, 5_000_000)),
        # DaiJob: đơn vị 万円
        ("日本・円  350万円 〜 400万円", (3_500_000, 4_000_000)),
        ("月給25万円", (3_000_000, 3_000_000)),
        ("年収400万円以上", (4_000_000, 4_000_000)),
        # Không quy đổi được sang năm -> thà bỏ trống còn hơn bịa
        ("¥5,000 ~ ¥15,000 / Project", (None, None)),
        ("¥1,200 / hour", (None, None)),
        ("Negotiable", (None, None)),
        ("経験と能力に基づく", (None, None)),
        (None, (None, None)),
    ],
)
def test_parse_salary(text, expected):
    assert parse_salary(text) == expected


def test_parse_salary_ignores_dates():
    """Thẻ của GaijinPot có "Date August 21, 2026" ngay cạnh mức lương.

    Từng bị đọc thành lương 2.026 yên/năm. Không có ràng buộc này thì bộ lọc
    "lương tối thiểu" trả về rác.
    """
    assert parse_salary("Date August 21, 2026") == (None, None)
    assert parse_salary("Date September 4, 2026 Company Apex Salary ¥3.8M ~ ¥5.0M / Year") == (
        3_800_000,
        5_000_000,
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("None", "none"),
        ("不問", "none"),
        ("Conversational (preferred)", "conversational"),
        ("日常会話レベル", "conversational"),
        ("Business level", "business"),
        ("ビジネス会話 (TOEIC 735-860)", "business"),
        ("English (Native level)", "native"),
        ("母国語レベル", "native"),
        # JLPT phải thắng phần mô tả bằng lời vì nó chính xác hơn
        ("N1 (ビジネス)", "fluent"),
        ("Conversational (N3)", "conversational"),
        ("N5", "basic"),
        # Không nói gì về trình độ -> không suy diễn
        ("Residing in Japan", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_language_level(text, expected):
    assert parse_language_level(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3+ years of experience", 3),
        ("at least 2 years", 2),
        ("経験1年～OK", 1),
        ("5年以上", 5),
        ("未経験OK", 0),
        ("no experience welcome", 0),
        ("", None),
        (None, None),
    ],
)
def test_parse_min_years(text, expected):
    assert parse_min_years(text) == expected


def test_parse_min_years_takes_the_lowest_requirement():
    """Tin hay nhắc nhiều mốc; mốc THẤP nhất mới là điều kiện bắt buộc."""
    assert parse_min_years("経験3年以上、5年以上あれば尚可") == 3


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Jiyugaoka, Tokyo, Japan", "Tokyo"),
        ("アジア 日本 福岡県", "Fukuoka"),
        ("神奈川県横浜市", "Kanagawa"),
        ("Ebisu, Tokyo", "Tokyo"),
        ("Remote", None),
        (None, None),
    ],
)
def test_parse_prefecture(text, expected):
    assert parse_prefecture(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Full Time Remote work", "full-time"),
        ("正社員", "full-time"),
        ("Part Time", "part-time"),
        ("契約社員", "contract"),
        ("Nationwide Freelance", "freelance"),
        ("", None),
    ],
)
def test_parse_employment_type(text, expected):
    assert parse_employment_type(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Full Time Remote work", True),
        ("リモートワーク可", True),
        ("Partial Remote", True),
        ("At Office", False),
        ("", False),
    ],
)
def test_is_remote(text, expected):
    assert is_remote(text) is expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Mercari, Inc.", "mercari"),
        ("MERCARI", "mercari"),
        ("Mercari Co., Ltd.", "mercari"),
        ("Flexport Japan株式会社", "flexport japan"),
        ("合同会社Amaris Japan", "amaris japan"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_company_name(name, expected):
    assert normalize_company_name(name) == expected


def test_clean_text_removes_repeated_decorations():
    """Nhãn trang trí có ở MỌI thẻ nên không phân biệt được tin nào với tin nào.

    Đo được: để nguyên thì điểm khớp của job đúng tụt từ 0.645 xuống 0.352.
    """
    raw = "NEW HOT 直接採用 ★ ★ スタッフレベル バックエンドエンジニア Python"
    cleaned = clean_text(raw)
    assert "NEW" not in cleaned and "HOT" not in cleaned and "★" not in cleaned
    assert "バックエンドエンジニア" in cleaned and "Python" in cleaned


def test_build_search_text_puts_title_and_skills_first():
    text = build_search_text("Backend Engineer", "Mercari", ["Python", "Go"], "x" * 3000)
    assert text.startswith("Backend Engineer")
    assert "Company: Mercari" in text
    assert "Skills: Python, Go" in text
    # Cắt bớt mô tả: phần đuôi dài chỉ làm loãng vector.
    assert len(text) < 1200


# ---------------------------------------------------------------------------
# Hồi quy: những lỗi thật đã gặp trên dữ liệu crawl được, không phải giả định.
# ---------------------------------------------------------------------------


def test_salary_in_foreign_currency_is_not_read_as_yen():
    """DaiJob có tin trả bằng Ringgit Malaysia.

    "7.8万リンギット" từng bị đọc thành 78.000 YÊN/năm và lọt vào bộ lọc lương
    như một công việc rẻ bất thường.
    """
    assert parse_salary("マレーシア・リンギット 7.8万リンギット 以上") == (None, None)
    # Có ghi rõ là yên thì vẫn đọc bình thường.
    assert parse_salary("日本・円 350万円 〜 400万円") == (3_500_000, 4_000_000)


def test_allowance_after_period_marker_is_not_treated_as_salary():
    """Phần sau "/ Month" là phụ cấp, không phải lương.

    Chuỗi thật của GaijinPot từng cho ra mức tối thiểu 360.000/năm vì nhặt phải
    khoản trợ cấp đi lại 30.000 yên/tháng.
    """
    text = "¥200,000 ~ ¥240,000 / Month Transportation costs will be reimbursed up to 30,000 yen per month"
    assert parse_salary(text) == (2_400_000, 2_880_000)


def test_parenthetical_restatement_is_ignored():
    """Ngoặc chứa số là diễn giải lại con số chính, không phải mức lương thứ hai."""
    text = "日本・円 300万円 （Monthly Salary Range： 日本・円 25万円 *Divided into12 month ）"
    assert parse_salary(text) == (3_000_000, 3_000_000)


def test_pay_per_lesson_is_not_annualised():
    """Trả theo buổi thì không biết một tháng bao nhiêu buổi -> không quy đổi."""
    text = "1,452 - 1,952 yen per 40-minute lesson depending on the day, lesson type and capacity"
    assert parse_salary(text) == (None, None)


def test_clean_text_keeps_words_inside_a_title():
    """Chỉ bỏ nhãn NEW/HOT khi chúng đứng MỘT MÌNH.

    `\\bHOT\\b` từng cắt chữ HOT ngay trong tiêu đề "😍HOT JOB😍..." vì emoji
    không phải ký tự chữ nên ranh giới từ vẫn khớp.
    """
    assert "HOT JOB" in clean_text("😍HOT JOB😍【福岡勤務】韓国語コンテンツチェック")
    assert clean_text("NEW HOT バックエンド") == "バックエンド"
