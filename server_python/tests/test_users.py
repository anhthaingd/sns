import uuid

import pytest


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


async def test_partial_update_keeps_fields_that_were_not_sent(client, user):
    """Gửi thiếu một trường thì trường đó phải GIỮ NGUYÊN, không bị xoá trắng.

    Bản cũ dựng `update_data` với `username`/`address`/`intro` gán vô điều kiện
    rồi `$set` nguyên khối, nên một request chỉ muốn đổi ảnh đại diện sẽ ghi
    `username=None` và xoá mất tên tài khoản. Lỗi này không lộ ra qua giao diện
    vì `UpdateProfileModal.jsx` luôn gửi đủ ba trường — đúng loại lỗi phải để
    máy canh.
    """
    await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"username": "giu nguyen ten", "intro": "gioi thieu", "address": "Tokyo"},
    )

    # Chỉ gửi MỘT trường, giống hệt một client chỉ muốn đổi địa chỉ.
    r = await client.put(f"/api/users/{user.id}", headers=user.headers, data={"address": "Osaka"})
    assert r.status_code == 200, r.text

    saved = (await client.get(f"/api/users/{user.id}")).json()["user"]
    assert saved["username"] == "giu nguyen ten", "tên tài khoản bị xoá khi cập nhật một phần"
    assert saved["intro"] == "gioi thieu", "phần giới thiệu bị xoá khi cập nhật một phần"
    assert saved["address"] == "Osaka"


async def test_empty_string_still_clears_a_field(client, user):
    """Chuỗi rỗng KHÁC với không gửi: người dùng xoá sạch ô giới thiệu vẫn phải lưu được."""
    await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"username": "ten", "intro": "co noi dung"},
    )
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"username": "ten", "intro": ""},
    )
    assert r.status_code == 200, r.text
    assert (await client.get(f"/api/users/{user.id}")).json()["user"]["intro"] == ""


async def test_new_account_has_no_default_avatar(client, db):
    """Tài khoản mới KHÔNG được phát ảnh đại diện dùng chung.

    Trước đây model gán sẵn `avatar-trang.jpg` cho mọi người, nên nhánh dựng ảnh
    thay thế bằng chữ cái đầu tên trong `Avatar.jsx` không bao giờ chạy và mọi
    người trong mọi danh sách trông giống hệt nhau.
    """
    email = f"noavatar-{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post(
        "/api/users/register",
        json={"email": email, "password": "Passw0rd!", "username": "khong anh"},
    )
    assert r.status_code == 201, r.text
    doc = await db.users.find_one({"email": email})
    assert not doc.get("avatar"), f"tài khoản mới vẫn được phát ảnh mặc định: {doc.get('avatar')!r}"


async def test_update_other_user_profile_is_rejected(client, user, other_user):
    """Không được sửa hồ sơ của người khác."""
    r = await client.put(f"/api/users/{other_user.id}", headers=user.headers, data={"username": "hacked"})
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


@pytest.mark.parametrize("keyword", ["[", "(a+)+$", "*", "\\", "a{100000}", ".*"])
async def test_search_with_regex_metacharacters_does_not_crash(client, user, admin, keyword):
    """Ô tìm kiếm nhận văn bản thuần, không phải regex.

    Trước đây từ khoá đi thẳng vào `$regex`: gõ một dấu `[` là Mongo ném
    "Regular expression is invalid" -> API trả 500. Chuỗi kiểu `(a+)+$` còn có
    thể làm máy chủ quay regex rất lâu (ReDoS).
    """
    for path, headers in [
        ("/api/users", user.headers),
        ("/api/channels", None),
        ("/api/posts", user.headers),
        ("/api/get_users_by_admin", admin.headers),
    ]:
        r = await client.get(path, params={"search": keyword, "page": 1}, headers=headers)
        assert r.status_code == 200, f"{path} với từ khoá {keyword!r} trả {r.status_code}: {r.text}"


async def test_search_treats_keyword_as_literal_text(client, user, other_user):
    """`.*` phải tìm đúng chuỗi ".*", không phải khớp tất cả."""
    r = await client.get("/api/users", params={"search": ".*", "page": 1}, headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["users"] == [], "regex không được escape: '.*' đang khớp mọi user"
