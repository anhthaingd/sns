"""Chốt chặn hợp đồng response: khoá nào client đang đọc thì không được biến mất.

Viết TRƯỚC khi gắn `response_model` để chụp lại hiện trạng. `response_model`
của FastAPI **âm thầm loại bỏ** field không khai báo — thiếu một field là UI mất
dữ liệu mà không có lỗi nào. Test này là bằng chứng không có gì bị mất.

Danh sách khoá dưới đây đối chiếu với chỗ client thật sự đọc, ví dụ
`data?.posts`, `data?.totalPage`, `m?.sender?.avatar?.url`.
"""

import uuid

import pytest

ENVELOPE = {"error", "success"}


def assert_keys(body: dict, expected: set, where: str):
    missing = expected - set(body)
    assert not missing, f"{where}: THIẾU khoá {sorted(missing)} — client sẽ hỏng. Có: {sorted(body)}"


async def test_health_contract(client):
    r = await client.get("/health")
    assert r.json() == {"status": "ok"}


async def test_website_contract(client):
    r = await client.get("/api/website")
    assert_keys(r.json(), ENVELOPE | {"website"}, "GET /api/website")


async def test_auth_contracts(client, user):
    r = await client.get("/api/users/getByToken", headers=user.headers)
    body = r.json()
    assert_keys(body, ENVELOPE | {"user", "followers", "following"}, "GET /api/users/getByToken")
    assert_keys(body["user"], {"_id", "email", "username", "avatar", "cover_bg", "role"}, "user trong getByToken")
    assert "password" not in body["user"], "response lộ hash mật khẩu"

    r = await client.post("/api/users/login", json={"email": user.email, "password": "Passw0rd!"})
    assert_keys(r.json(), ENVELOPE | {"accessToken"}, "POST /api/users/login")

    r = await client.post("/api/users/refresh")
    assert_keys(r.json(), ENVELOPE | {"accessToken"}, "POST /api/users/refresh")


async def test_user_contracts(client, user, other_user):
    r = await client.get(f"/api/users/{other_user.id}", headers=user.headers)
    assert_keys(
        r.json(),
        ENVELOPE | {"user", "followers", "following", "posts", "channels"},
        "GET /api/users/{id}",
    )

    r = await client.get("/api/users", params={"search": "user", "page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"users", "totalPage", "totalUsers"}, "GET /api/users")

    r = await client.get("/api/get_followers", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"followers", "totalPage"}, "GET /api/get_followers")

    r = await client.get("/api/get_following", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"following", "totalPage"}, "GET /api/get_following")

    r = await client.get("/api/resume", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"resume"}, "GET /api/resume")


async def test_admin_contracts(client, admin):
    r = await client.get("/api/get_users_by_admin", params={"page": 1}, headers=admin.headers)
    assert_keys(
        r.json(),
        ENVELOPE | {"users", "totalPage", "totalUsers", "curPage"},
        "GET /api/get_users_by_admin",
    )

    r = await client.get("/api/posts/get_by_admin", params={"page": 1}, headers=admin.headers)
    assert_keys(r.json(), ENVELOPE | {"posts", "totalPage"}, "GET /api/posts/get_by_admin")


async def test_channel_contracts(client, admin, channel, user):
    r = await client.get("/api/channels", params={"page": 1})
    assert_keys(r.json(), ENVELOPE | {"channels", "totalPage", "curPage"}, "GET /api/channels")
    listed = next(c for c in r.json()["channels"] if c["_id"] == channel["_id"])
    assert_keys(listed, {"_id", "name", "intro", "background", "members", "created_at"}, "channel trong danh sách")

    r = await client.get("/api/channels/get_by_user", headers=admin.headers)
    assert_keys(r.json(), ENVELOPE | {"channels"}, "GET /api/channels/get_by_user")

    r = await client.get(f"/api/channels/{channel['_id']}", headers=admin.headers)
    assert_keys(r.json(), ENVELOPE | {"channel"}, "GET /api/channels/{id}")
    member = r.json()["channel"]["members"][0]
    assert_keys(member, {"_id", "username", "email", "avatar", "role"}, "member trong channel")

    r = await client.get("/api/shortcuts", headers=admin.headers)
    assert_keys(r.json(), ENVELOPE | {"shortcuts"}, "GET /api/shortcuts")


async def test_post_contracts(client, admin, channel, user):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    content = f"contract-{uuid.uuid4().hex[:8]}"
    r = await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": content})
    assert r.status_code == 201, r.text

    r = await client.get(f"/api/posts/{channel['_id']}", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"posts", "totalPage"}, "GET /api/posts/{channel_id}")
    post = next(p for p in r.json()["posts"] if p["content"] == content)
    assert_keys(
        post,
        {"_id", "user", "content", "images", "created_at", "updated_at", "liked", "book_marked", "comments", "channel"},
        "post",
    )
    assert_keys(post["user"], {"_id", "email", "username", "avatar"}, "tác giả bài viết")
    assert_keys(post["channel"], {"_id", "name"}, "channel của bài viết")

    await client.post(
        f"/api/posts/{channel['_id']}/{post['_id']}/comments",
        headers=user.headers,
        json={"content": "hello"},
    )
    await client.post(f"/api/posts/{channel['_id']}/{post['_id']}/like_post", headers=admin.headers)

    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"post"}, "GET /api/posts/get_post_details_in_channel/{id}")
    detail = r.json()["post"]
    assert_keys(detail["comments"][0], {"_id", "user", "content", "created_at"}, "bình luận")
    assert_keys(detail["liked"][0], {"_id", "email", "username", "avatar"}, "người đã like")

    r = await client.get("/api/posts", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"posts", "totalPage", "totalPosts"}, "GET /api/posts")

    r = await client.get("/api/posts/get_book_marked", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"posts", "totalPage"}, "GET /api/posts/get_book_marked")

    r = await client.get("/api/posts/get_by_users", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"posts", "totalPage"}, "GET /api/posts/get_by_users")


async def test_notification_and_chat_contracts(client, user, other_user):
    r = await client.get("/api/notifications", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"notifications", "notRead", "totalPage"}, "GET /api/notifications")

    r = await client.get("/api/newest_messages", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"messages", "unread"}, "GET /api/newest_messages")

    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"messages", "totalPage"}, "GET /api/messages/{a}/{b}")


async def test_error_contract_always_has_message(client):
    """24 chỗ trong client đọc `error.data.message` — mọi lỗi phải có khoá này."""
    cases = [
        ("GET", "/api/users/getByToken", {}),
        ("GET", "/api/users/khong-phai-objectid", {}),
        ("POST", "/api/users/login", {"json": {"email": "a", "password": "b"}}),
        ("POST", "/api/users/login", {"json": {"email": 1, "password": 2}}),
        ("GET", "/api/duong-dan-khong-ton-tai", {}),
    ]
    for method, path, kwargs in cases:
        r = await client.request(method, path, **kwargs)
        assert r.status_code >= 400, f"{path} phải là lỗi"
        body = r.json()
        assert_keys(body, {"error", "success", "message"}, f"{method} {path}")
        assert body["error"] is True and body["success"] is False, body
        assert isinstance(body["message"], str) and body["message"], body


# ---------------------------------------------------------------------------
# Việc làm, doanh nghiệp và gợi ý
# ---------------------------------------------------------------------------


async def test_job_contracts(client, user, has_jobs):

    r = await client.get("/api/jobs", params={"page": 1}, headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"jobs", "totalPage", "totalJobs", "curPage"}, "GET /api/jobs")

    job = r.json()["jobs"][0]
    assert_keys(
        job,
        {
            "_id",
            "source",
            "url",
            "title",
            "company_name",
            "location",
            "prefecture",
            "salary_min",
            "salary_max",
            "employment_type",
            "remote",
            "description",
            "required_skills",
            "required_japanese",
            "required_english",
            "min_years",
        },
        "job",
    )
    # Vector không bao giờ được ra API: 384 số thực mỗi bản ghi.
    assert "embedding" not in job and "search_text" not in job

    r = await client.get(f"/api/jobs/{job['_id']}", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"job"}, "GET /api/jobs/{id}")

    r = await client.get("/api/jobs/filters", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"prefectures", "japaneseLevels", "skills"}, "GET /api/jobs/filters")


async def test_company_contracts(client, user, has_jobs):

    r = await client.get("/api/companies", params={"page": 1}, headers=user.headers)
    assert_keys(
        r.json(),
        ENVELOPE | {"companies", "totalPage", "totalCompanies", "curPage"},
        "GET /api/companies",
    )
    company = r.json()["companies"][0]
    assert_keys(company, {"_id", "name", "logo_url", "description", "tech_stack", "job_count"}, "company")
    assert "embedding" not in company

    r = await client.get(f"/api/companies/{company['_id']}", headers=user.headers)
    assert_keys(r.json(), ENVELOPE | {"company", "jobs"}, "GET /api/companies/{id}")


async def test_match_contracts(client, user_with_resume, has_jobs):

    r = await client.get("/api/match/companies", params={"page": 1}, headers=user_with_resume.headers)
    body = r.json()
    assert_keys(
        body,
        ENVELOPE | {"matches", "totalPage", "totalCompanies", "curPage", "semanticAvailable"},
        "GET /api/match/companies",
    )
    match = body["matches"][0]
    assert_keys(match, {"company", "bestJob", "match"}, "một mục gợi ý")
    assert_keys(
        match["match"],
        {"score", "semantic", "requirementRatio", "semanticAvailable", "met", "gaps"},
        "kết quả chấm điểm",
    )

    job_id = match["bestJob"]["_id"]
    r = await client.get(f"/api/match/jobs/{job_id}/gap", headers=user_with_resume.headers)
    assert_keys(r.json(), ENVELOPE | {"job", "company", "match", "qualified"}, "GET .../gap")


async def test_gap_item_shape(client, user_with_resume, db, has_jobs):
    """Client dựng giao diện theo đúng các khoá này — thiếu là hỏng màn hình."""
    job = await db.jobs.find_one({"required_japanese": {"$in": ["fluent", "native"]}})
    if job is None:
        pytest.skip("không có tin nào đòi tiếng Nhật mức cao")

    r = await client.get(f"/api/match/jobs/{job['_id']}/gap", headers=user_with_resume.headers)
    for gap in r.json()["match"]["gaps"]:
        assert_keys(gap, {"kind", "message", "required", "current", "blocking"}, "một mục thiếu sót")
        assert isinstance(gap["blocking"], bool)


async def test_market_contract(client, user, has_jobs):
    r = await client.get("/api/jobs/market", headers=user.headers)
    assert_keys(
        r.json(),
        ENVELOPE | {"totalJobs", "minGroupSize", "skills", "japanese", "prefectures"},
        "GET /api/jobs/market",
    )
    body = r.json()
    assert_keys(body["skills"][0], {"skill", "jobs", "salaryMedian", "salarySample"}, "market.skills[]")
    assert_keys(body["japanese"][0], {"level", "jobs", "salaryMedian", "salarySample"}, "market.japanese[]")
    assert_keys(
        body["prefectures"][0],
        {"prefecture", "jobs", "salaryMedian", "salarySample"},
        "market.prefectures[]",
    )


async def test_whatif_contract(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/whatif", headers=user_with_resume.headers)
    body = r.json()
    assert_keys(body, ENVELOPE | {"totalJobs", "baseline", "suggestions"}, "GET /api/match/whatif")
    assert_keys(body["baseline"], {"qualifiedJobs", "qualifiedCompanies"}, "whatif.baseline")
    assert_keys(
        body["suggestions"][0],
        {
            "kind",
            "value",
            "qualifiedJobs",
            "qualifiedCompanies",
            "deltaJobs",
            "openedSalaryMedian",
            "openedSalarySample",
        },
        "whatif.suggestions[]",
    )

    r = await client.post(
        "/api/match/whatif",
        json={"actions": [{"kind": "japanese", "value": "business"}]},
        headers=user_with_resume.headers,
    )
    body = r.json()
    assert_keys(body, ENVELOPE | {"baseline", "combined", "sumOfIndividualDeltas"}, "POST /api/match/whatif")
    assert_keys(body["combined"], {"actions", "qualifiedJobs", "deltaJobs"}, "whatif.combined")


async def test_whatif_never_returns_vectors_or_personal_data(client, user_with_resume, has_jobs):
    """Response chỉ gồm con số và mã thô — không kéo theo CV hay vector.

    Mô phỏng đọc CV của người dùng và duyệt toàn bộ kho tin, nên đây đúng chỗ
    dễ vô tình trả cả hồ sơ ra ngoài.
    """
    raw = (await client.get("/api/match/whatif", headers=user_with_resume.headers)).text
    for forbidden in ("embedding", "search_text", "skills_normalized", "email"):
        assert forbidden not in raw, f"response chứa `{forbidden}`"
