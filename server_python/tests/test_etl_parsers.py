"""Test parser trên HTML THẬT đã lưu lại — không cần mạng.

Fixture trong `tests/fixtures/` là trang thật tải về ngày dựng chức năng này.
Nhờ vậy test bắt được lỗi parser mà không phụ thuộc trang nguồn còn sống hay
không, và không làm phiền trang nguồn mỗi lần chạy CI.

Khi một trang nguồn đổi giao diện: test này VẪN XANH (fixture cũ), còn workflow
`crawl-health.yml` chạy trên trang thật mới là chỗ báo động. Hai lớp khác nhau,
cố ý tách rời.
"""

from pathlib import Path

import pytest
from app.services.etl.parsers import SOURCES, nihongo
from app.services.etl.pipeline import normalize_job

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / f"{name}.html").read_text(encoding="utf-8")


# Số tin trên mỗi fixture. Cố định vì fixture là file tĩnh — con số thay đổi
# nghĩa là parser đã đổi hành vi.
# GaijinPot: 51 thẻ trên trang nhưng một tin xuất hiện hai lần (thẻ nổi bật
# + thẻ thường) nên sau khi loại trùng còn 50.
EXPECTED_COUNTS = {"gaijinpot": 50, "daijob": 20, "nihongo": 20, "linkedin": 10}


@pytest.mark.parametrize(("source", "expected"), EXPECTED_COUNTS.items())
def test_parser_finds_all_jobs(source, expected):
    jobs = SOURCES[source]["parse"](load(source))
    assert len(jobs) == expected


def test_gaijinpot_reads_all_cards_not_only_premium():
    """Bản crawl cũ dùng selector `.card--premium` và bỏ sót gần một nửa số tin.

    Trang có 51 thẻ nhưng chỉ 26 thẻ premium.
    """
    assert len(SOURCES["gaijinpot"]["parse"](load("gaijinpot"))) > 26


@pytest.mark.parametrize("source", sorted(EXPECTED_COUNTS))
def test_every_job_has_stable_identity(source):
    """Thiếu id ổn định thì mỗi lần crawl lại nhân bản toàn bộ dữ liệu."""
    jobs = SOURCES[source]["parse"](load(source))
    ids = [j.source_id for j in jobs]
    assert all(ids), f"{source}: có tin thiếu source_id"
    assert len(set(ids)) == len(ids), f"{source}: source_id bị trùng"
    assert all(j.title for j in jobs), f"{source}: có tin thiếu tiêu đề"


@pytest.mark.parametrize("source", sorted(EXPECTED_COUNTS))
def test_urls_are_absolute(source):
    """DaiJob trả href tương đối; để nguyên thì người dùng bấm vào là 404."""
    jobs = SOURCES[source]["parse"](load(source))
    assert all(j.url.startswith("http") for j in jobs), f"{source}: có URL tương đối"


def test_gaijinpot_extracts_structured_fields():
    jobs = {j.source_id: j for j in SOURCES["gaijinpot"]["parse"](load("gaijinpot"))}
    job = jobs["159587"]
    assert job.title.startswith("Dispatch English teacher")
    assert job.company_name == "YARUKI Switch Career"
    assert job.location_text == "Tokyo, Japan"
    assert job.salary_text == "¥247,590 ~ ¥247,590 / Month"
    # Trường quý nhất trong cả bốn nguồn: yêu cầu tiếng Nhật nói thẳng.
    assert job.japanese_text == "None"


def test_daijob_reads_second_definition_list_with_description():
    """DaiJob tách làm hai thẻ <dl>; cái thứ hai chứa 仕事内容 (mô tả công việc).

    `select_one("dl")` chỉ lấy cái đầu và làm mất toàn bộ mô tả.
    """
    jobs = SOURCES["daijob"]["parse"](load("daijob"))
    assert all(len(j.description) > 50 for j in jobs), "có tin DaiJob không lấy được 仕事内容"


def test_nihongo_classifies_unlabelled_tags():
    """Thẻ của Nihongo gắn 3 nhãn không có tên: địa điểm, lương, hình thức."""
    jobs = SOURCES["nihongo"]["parse"](load("nihongo"))
    assert any(j.location_text == "Tokyo" for j in jobs)
    assert any(j.salary_text and "JPY" in j.salary_text for j in jobs)
    assert any(j.employment_text in {"At Office", "Full Remote", "Partial Remote"} for j in jobs)
    assert all(j.company_source_id for j in jobs), "mất liên kết tới hồ sơ công ty"


def test_linkedin_strips_tracking_query_string():
    """URL LinkedIn mang tham số theo dõi đổi mỗi lần tải.

    Giữ nguyên thì mỗi lần crawl lại sinh URL khác cho cùng một tin.
    """
    jobs = SOURCES["linkedin"]["parse"](load("linkedin"))
    assert all("?" not in j.url for j in jobs)


def test_nihongo_company_profile():
    company = nihongo.parse_company(load("nihongo_company"), "2")
    assert company is not None
    assert company.name == "JOBs Japan"
    assert company.website == "https://it-jobs-in-japan.co.jp/"
    assert company.location == "Shinjuku, Tokyo, Japan"
    assert company.job_count == 129
    assert len(company.description) > 200


def test_nihongo_company_list_page():
    """Trang chủ việc làm bị một công ty môi giới chiếm gần hết, nên phải đi từ
    trang danh sách công ty mới lấy được nhiều hồ sơ thật."""
    ids = nihongo.parse_company_ids(load("nihongo_companies"))
    assert len(ids) == 10
    assert all(i.isdigit() for i in ids)


@pytest.mark.parametrize("source", sorted(EXPECTED_COUNTS))
def test_parser_returns_empty_on_unrelated_html(source):
    """Trang nguồn đổi giao diện -> parser trả rỗng chứ không nổ.

    ETL dựa vào điều này để phân biệt "không có tin mới" với "selector đã mục
    rữa" (xem `run_source` trong pipeline.py).
    """
    assert SOURCES[source]["parse"]("<html><body><p>trang khac</p></body></html>") == []


@pytest.mark.parametrize("source", sorted(EXPECTED_COUNTS))
def test_normalize_job_produces_valid_document_fields(source):
    for raw in SOURCES[source]["parse"](load(source)):
        data = normalize_job(raw)
        assert data["source"] == source
        assert data["title"]
        assert isinstance(data["required_skills"], list)
        assert data["required_japanese"] in {
            None,
            "none",
            "basic",
            "conversational",
            "business",
            "fluent",
            "native",
        }
        if data["salary_min"] is not None:
            assert data["salary_min"] <= data["salary_max"]
            # Lương năm hợp lý ở Nhật: dưới 1 triệu yên/năm nghĩa là quên nhân 12.
            assert data["salary_min"] >= 1_000_000, f"{source}: lương có vẻ chưa quy đổi ra năm"
        assert data["search_text"].startswith(data["title"][:20])
