"""Sáu endpoint lời khuyên — kiểm hợp đồng, không kiểm chất lượng văn.

Bộ test này phải xanh ở CẢ HAI môi trường:

* máy dev có API key   -> `reason` là `ok` / `cached`, có `advice`;
* CI không có key       -> `reason` là `disabled`, `advice` là `null`.

Nên nó khoá **hợp đồng và cách suy giảm**, không khoá nội dung câu chữ — nội
dung do mô hình sinh ra, không tất định, không thể assert được.
"""

import pytest

VALID_REASONS = {"ok", "cached", "disabled", "quota", "unavailable", "empty"}


def check_envelope(payload: dict):
    """Luôn 200 kèm `reason` đọc được; có `advice` thì phải đúng khuôn."""
    assert payload["reason"] in VALID_REASONS, payload["reason"]

    advice = payload.get("advice")
    if advice is None:
        return None

    assert isinstance(advice["summary"], str) and advice["summary"]
    assert 1 <= len(advice["roadmap"]) <= 3
    for step in advice["roadmap"]:
        assert step["title"] and step["detail"]
        assert 1 <= step["months"] <= 24
        # Không kiểm chứng được liên kết dẫn tới đâu thì không hiện liên kết nào.
        assert "http" not in step["detail"]
    assert "http" not in advice["summary"]
    return advice


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
async def test_market_advice_works_in_every_language(client, user, lang):
    """Bản đồ thị trường không cần CV — đây là endpoint rẻ nhất để kiểm ba ngôn ngữ."""
    r = await client.get("/api/jobs/market/advice", params={"lang": lang}, headers=user.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())


async def test_resume_advice(client, user_with_resume):
    r = await client.get("/api/resume/advice", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())


async def test_overview_advice(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/advice/overview", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())


async def test_whatif_advice(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/whatif/advice", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())


async def test_job_and_company_advice(client, user_with_resume, has_jobs):
    listed = await client.get("/api/match/companies", headers=user_with_resume.headers)
    assert listed.status_code == 200, listed.text
    matches = listed.json()["matches"]
    if not matches:
        pytest.skip("CV mẫu không khớp công ty nào trong kho hiện tại")

    job_id = matches[0]["bestJob"]["_id"]
    r = await client.get(f"/api/match/jobs/{job_id}/advice", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())

    company_id = matches[0]["company"]["_id"]
    if company_id:
        r = await client.get(f"/api/match/companies/{company_id}/advice", headers=user_with_resume.headers)
        assert r.status_code == 200, r.text
        check_envelope(r.json())


async def test_unknown_ids_still_return_404_not_a_blank_advice(client, user_with_resume):
    """Lời khuyên suy giảm êm, nhưng lỗi THẬT vẫn phải là lỗi."""
    r = await client.get("/api/match/jobs/000000000000000000000000/advice", headers=user_with_resume.headers)
    assert r.status_code == 404


async def test_advice_requires_login(client):
    r = await client.get("/api/jobs/market/advice")
    assert r.status_code == 401


async def test_unknown_language_falls_back_instead_of_failing(client, user):
    """`lang=xx` là dữ liệu client gửi lên — không được làm hỏng request."""
    r = await client.get("/api/jobs/market/advice", params={"lang": "xx"}, headers=user.headers)
    assert r.status_code == 200, r.text
    check_envelope(r.json())


async def test_asking_for_advice_never_changes_the_score(client, user_with_resume, has_jobs):
    """**Test quan trọng nhất của cả tính năng.**

    Điểm số là việc của `matching.py`: tất định, giải thích được. Lời khuyên chỉ
    đọc kết quả ấy rồi viết thành lời. Nếu một ngày nào đó LLM chen được vào
    phần chấm điểm, test này đỏ ngay.
    """
    listed = await client.get("/api/match/companies", headers=user_with_resume.headers)
    matches = listed.json()["matches"]
    if not matches:
        pytest.skip("CV mẫu không khớp công ty nào trong kho hiện tại")
    job_id = matches[0]["bestJob"]["_id"]

    before = await client.get(f"/api/match/jobs/{job_id}/gap", headers=user_with_resume.headers)
    await client.get(f"/api/match/jobs/{job_id}/advice", headers=user_with_resume.headers)
    after = await client.get(f"/api/match/jobs/{job_id}/gap", headers=user_with_resume.headers)

    assert before.json()["match"] == after.json()["match"]
    assert before.json()["qualified"] == after.json()["qualified"]
