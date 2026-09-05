async def test_user_details(client, user, other_user):
    r = await client.get(f"/api/users/{other_user.id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == other_user.email
    assert body["posts"] == 0
    assert "password" not in body["user"]


async def test_user_details_not_found(client, user):
    r = await client.get("/api/users/000000000000000000000000")
    assert r.status_code == 404


async def test_search_users(client, user, other_user):
    r = await client.get("/api/users", params={"search": other_user.email}, headers=user.headers)
    assert r.status_code == 200, r.text
    emails = [u["email"] for u in r.json()["users"]]
    assert other_user.email in emails
    assert user.email not in emails, "search không được trả về chính mình"


async def test_follow_and_unfollow(client, user, other_user):
    r = await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    assert r.status_code == 200, r.text

    r = await client.get("/api/get_following", headers=user.headers)
    assert r.status_code == 200, r.text
    assert other_user.id in [u["_id"] for u in r.json()["following"]]

    r = await client.get("/api/get_followers", headers=other_user.headers)
    assert r.status_code == 200, r.text
    assert user.id in [u["_id"] for u in r.json()["followers"]]

    r = await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/get_following", headers=user.headers)
    assert other_user.id not in [u["_id"] for u in r.json()["following"]]


async def test_cannot_follow_self(client, user):
    r = await client.post(f"/api/users/{user.id}/following", headers=user.headers)
    assert r.status_code == 409


async def test_remove_following(client, user, other_user):
    await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    r = await client.delete(f"/api/remove_following/{other_user.id}", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/get_following", headers=user.headers)
    assert other_user.id not in [u["_id"] for u in r.json()["following"]]


async def test_remove_followers(client, user, other_user):
    await client.post(f"/api/users/{user.id}/following", headers=other_user.headers)
    r = await client.delete(f"/api/remove_followers/{other_user.id}", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/get_followers", headers=user.headers)
    assert other_user.id not in [u["_id"] for u in r.json()["followers"]]


async def test_update_profile(client, user):
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"username": "renamed", "intro": "hello", "address": "Tokyo"},
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/users/{user.id}")
    assert r.json()["user"]["username"] == "renamed"


async def test_update_other_user_profile_is_rejected(client, user, other_user):
    """Không được sửa hồ sơ của người khác."""
    r = await client.put(
        f"/api/users/{other_user.id}", headers=user.headers, data={"username": "hacked"}
    )
    assert r.status_code in (403, 404), f"cho phép sửa user khác! status={r.status_code}"
    r = await client.get(f"/api/users/{other_user.id}")
    assert r.json()["user"]["username"] != "hacked"


async def test_admin_list_users_requires_admin(client, user):
    r = await client.get("/api/get_users_by_admin", headers=user.headers)
    assert r.status_code == 403


async def test_admin_list_users(client, admin, user):
    r = await client.get("/api/get_users_by_admin", headers=admin.headers)
    assert r.status_code == 200, r.text
    assert r.json()["totalUsers"] >= 1


async def test_resume_roundtrip(client, user):
    r = await client.get("/api/resume", headers=user.headers)
    assert r.status_code == 200 and r.json()["resume"] is None

    r = await client.post(
        "/api/resume",
        headers=user.headers,
        data={
            "name": "Nguyen Van A",
            "position": "Backend Engineer",
            "email": user.email,
            "skills": '["Python","MongoDB"]',
            "languages": '["JP","EN"]',
            "experiences": "[]",
            "projects": "[]",
        },
    )
    assert r.status_code == 200, r.text

    r = await client.get("/api/resume", headers=user.headers)
    resume = r.json()["resume"]
    assert resume["name"] == "Nguyen Van A"
    assert resume["skills"] == ["Python", "MongoDB"]
