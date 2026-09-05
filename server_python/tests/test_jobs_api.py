"""Test API việc làm, doanh nghiệp và gợi ý — chạy trên server thật với dữ liệu ETL."""

import pytest

# ---------------------------------------------------------------------------
# Tra cứu việc làm
# ---------------------------------------------------------------------------


async def test_jobs_require_authentication(client):
    assert (await client.get("/api/jobs")).status_code == 401


async def test_list_jobs(client, user, has_jobs):
    r = await client.get("/api/jobs", params={"page": 1}, headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["jobs"] and body["totalJobs"] > 0
    job = body["jobs"][0]
    assert job["title"] and job["url"].startswith("http")


async def test_job_response_never_contains_vectors(client, user, has_jobs):
    """Mỗi vector là 384 số thực; trả ra API là phình payload vô ích."""
    r = await client.get("/api/jobs", params={"page": 1}, headers=user.headers)
    for job in r.json()["jobs"]:
        assert "embedding" not in job, "response chứa vector — payload phình vô ích"
        assert "search_text" not in job


async def test_filter_jobs_by_japanese_level(client, user, has_jobs):
    r = await client.get("/api/jobs", params={"japanese": "business"}, headers=user.headers)
    assert r.status_code == 200, r.text
    assert all(j["required_japanese"] == "business" for j in r.json()["jobs"])


async def test_filter_jobs_by_prefecture(client, user, has_jobs):
    r = await client.get("/api/jobs", params={"prefecture": "Tokyo"}, headers=user.headers)
    assert r.status_code == 200, r.text
    assert all(j["prefecture"] == "Tokyo" for j in r.json()["jobs"])


async def test_search_with_regex_metacharacters_is_safe(client, user, has_jobs):
    """Ô tìm kiếm nhận văn bản thuần — `[` từng làm Mongo ném lỗi và API trả 500."""
    for keyword in ["[", "(a+)+$", "*"]:
        r = await client.get("/api/jobs", params={"search": keyword}, headers=user.headers)
        assert r.status_code == 200, f"{keyword!r}: {r.text}"


async def test_job_filters_come_from_real_data(client, user, has_jobs):
    r = await client.get("/api/jobs/filters", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["prefectures"] and body["skills"]
    assert all(s["count"] > 0 for s in body["skills"])


async def test_job_details_and_bad_id(client, user, db, has_jobs):
    job = await db.jobs.find_one({"is_active": True})
    r = await client.get(f"/api/jobs/{job['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["job"]["_id"] == str(job["_id"])

    r = await client.get("/api/jobs/khong-phai-id", headers=user.headers)
    assert r.status_code == 400
    assert "ObjectId" not in r.json()["message"]


async def test_companies_list_and_details(client, user, db, has_jobs):
    r = await client.get("/api/companies", params={"page": 1}, headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["companies"]

    company = await db.companies.find_one({})
    r = await client.get(f"/api/companies/{company['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert "jobs" in r.json()


# ---------------------------------------------------------------------------
# Chức năng 1: công ty phù hợp
# ---------------------------------------------------------------------------


async def test_match_requires_a_resume(client, user):
    r = await client.get("/api/match/companies", headers=user.headers)
    assert r.status_code == 404
    assert "CV" in r.json()["message"]


async def test_match_companies_returns_ranked_list(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/companies", params={"page": 1}, headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["matches"], "không gợi ý được công ty nào"

    scores = [m["match"]["score"] for m in body["matches"]]
    assert scores == sorted(scores, reverse=True), "kết quả chưa sắp xếp theo điểm"
    for m in body["matches"]:
        assert m["company"]["name"] and m["bestJob"]["title"]
        assert 0 <= m["match"]["score"] <= 100


async def test_each_company_appears_at_most_once(client, user_with_resume, has_jobs):
    """Người dùng cần "công ty nào hợp với tôi", không phải 20 vị trí cùng công ty."""
    r = await client.get("/api/match/companies", params={"page": 1}, headers=user_with_resume.headers)
    names = [m["company"]["name"] for m in r.json()["matches"]]
    assert len(names) == len(set(names))


async def test_match_jobs_lists_individual_positions(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/jobs", params={"page": 1}, headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    assert r.json()["matches"][0]["job"]["title"]


# ---------------------------------------------------------------------------
# Chức năng 2: còn thiếu gì
# ---------------------------------------------------------------------------


async def test_job_gap_explains_what_is_missing(client, user_with_resume, db, has_jobs):
    """Tin đòi tiếng Nhật cao hơn CV -> phải nói rõ thiếu ở đâu, chứ không chỉ trả điểm."""
    job = await db.jobs.find_one({"required_japanese": {"$in": ["fluent", "native"]}})
    if job is None:
        pytest.skip("dữ liệu hiện tại không có tin nào đòi tiếng Nhật mức cao")

    r = await client.get(f"/api/match/jobs/{job['_id']}/gap", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()

    # CV mẫu ở mức N2 (business) nên tin đòi fluent/native phải sinh gap chặn.
    japanese_gaps = [g for g in body["match"]["gaps"] if g["kind"] == "japanese_level"]
    assert japanese_gaps, body["match"]["gaps"]
    assert japanese_gaps[0]["blocking"] is True
    assert body["qualified"] is False


async def test_company_gap_aggregates_across_positions(client, user_with_resume, db, has_jobs):
    company = await db.companies.find_one({"job_count": {"$gte": 1}})
    job = await db.jobs.find_one({"company": company["_id"]})
    if job is None:
        pytest.skip("công ty này chưa gắn được vị trí nào")

    r = await client.get(f"/api/match/companies/{company['_id']}/gap", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["company"]["name"] and body["bestJob"]["title"]
    assert isinstance(body["combinedGaps"], list)
    # Thiếu sót phải loại trùng: nhiều vị trí cùng đòi một thứ chỉ hiện một lần.
    messages = [g["message"] for g in body["combinedGaps"]]
    assert len(messages) == len(set(messages))


async def test_gap_on_unknown_job_returns_404(client, user_with_resume):
    from bson import ObjectId

    r = await client.get(f"/api/match/jobs/{ObjectId()}/gap", headers=user_with_resume.headers)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Quản trị
# ---------------------------------------------------------------------------


async def test_etl_status_is_admin_only(client, user, admin):
    assert (await client.get("/api/admin/etl/status", headers=user.headers)).status_code == 403

    r = await client.get("/api/admin/etl/status", headers=admin.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "jobs" in body["stats"] and "companies" in body["stats"]
    assert set(body["sources"]) == {"gaijinpot", "daijob", "nihongo", "linkedin"}


async def test_etl_run_rejects_bad_parameters(client, admin):
    r = await client.post("/api/admin/etl/run", headers=admin.headers, json={"sources": ["khong-ton-tai"]})
    assert r.status_code == 400
    assert "khong-ton-tai" in r.json()["message"]

    r = await client.post("/api/admin/etl/run", headers=admin.headers, json={"pages": 999})
    assert r.status_code == 400


async def test_etl_run_is_admin_only(client, user):
    assert (await client.post("/api/admin/etl/run", headers=user.headers, json={})).status_code == 403


# ---------------------------------------------------------------------------
# Suy giảm êm: không có vector thì vẫn phải chấm được
# ---------------------------------------------------------------------------


async def test_match_still_works_without_any_vector(client, user_with_resume, db, has_jobs):
    """Service embedder tắt / CV chưa kịp tính vector -> vẫn phải ra kết quả.

    Xếp hạng theo ngữ nghĩa là phần làm kết quả đẹp hơn, không phải phần bắt
    buộc: tầng lọc theo luật (JLPT, số năm, lương, địa điểm) tự nó đã đủ để trả
    lời "công ty nào phù hợp". Nếu chỗ này 500 thì cả chức năng phụ thuộc vào
    một container.
    """
    await db.resumes.update_one(
        {"user": __import__("bson").ObjectId(user_with_resume.id)},
        {"$set": {"embedding": None}},
    )

    r = await client.get("/api/match/companies", params={"page": 1}, headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["matches"], "không có vector thì vẫn phải gợi ý được"
    assert body["semanticAvailable"] is False, "phải nói rõ là đang chấm thuần luật"
    assert all(m["match"]["semanticAvailable"] is False for m in body["matches"])


async def test_gap_still_works_without_any_vector(client, user_with_resume, db, has_jobs):
    await db.resumes.update_one(
        {"user": __import__("bson").ObjectId(user_with_resume.id)},
        {"$set": {"embedding": None}},
    )
    job = await db.jobs.find_one({"required_japanese": {"$ne": None}})
    r = await client.get(f"/api/match/jobs/{job['_id']}/gap", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    assert "gaps" in r.json()["match"]
