import pytest

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


@pytest.fixture
async def joined(client, user, channel):
    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    return channel


async def _create_post(client, actor, channel_id, content="hello world"):
    r = await client.post(f"/api/posts/{channel_id}", headers=actor.headers, data={"content": content})
    assert r.status_code == 201, r.text
    r = await client.get(f"/api/posts/{channel_id}", headers=actor.headers)
    assert r.status_code == 200, r.text
    return next(p for p in r.json()["posts"] if p["content"] == content)


async def test_create_post_requires_content(client, user, joined):
    r = await client.post(f"/api/posts/{joined['_id']}", headers=user.headers, data={"content": ""})
    assert r.status_code == 400


async def test_create_and_list_post(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    assert post["user"]["_id"] == user.id
    assert post["channel"]["_id"] == joined["_id"]

    r = await client.get("/api/posts", headers=user.headers)
    assert r.status_code == 200, r.text
    assert post["_id"] in [p["_id"] for p in r.json()["posts"]]


async def test_create_post_with_image(client, user, joined):
    r = await client.post(
        f"/api/posts/{joined['_id']}",
        headers=user.headers,
        data={"content": "with image"},
        files={"images": ("pic.png", PNG, "image/png")},
    )
    assert r.status_code == 201, r.text
    r = await client.get(f"/api/posts/{joined['_id']}", headers=user.headers)
    post = next(p for p in r.json()["posts"] if p["content"] == "with image")
    assert post["images"]["url"].startswith("public/uploads/")

    served = await client.get("/" + post["images"]["url"])
    assert served.status_code == 200, "file upload không truy cập được qua /public"


async def test_post_details(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["post"]["_id"] == post["_id"]


async def test_get_by_users(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.get("/api/posts/get_by_users", headers=user.headers)
    assert r.status_code == 200, r.text
    assert post["_id"] in [p["_id"] for p in r.json()["posts"]]


async def test_update_post(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.put(f"/api/posts/{joined['_id']}/{post['_id']}", headers=user.headers, data={"content": "edited"})
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert r.json()["post"]["content"] == "edited"


async def test_cannot_update_other_users_post(client, user, other_user, joined):
    post = await _create_post(client, user, joined["_id"])
    await client.post(f"/api/channels/{joined['_id']}", headers=other_user.headers)
    r = await client.put(
        f"/api/posts/{joined['_id']}/{post['_id']}",
        headers=other_user.headers,
        data={"content": "hijacked"},
    )
    assert r.status_code == 403


async def test_like_and_unlike(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.post(f"/api/posts/{joined['_id']}/{post['_id']}/like_post", headers=user.headers)
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert user.id in [u["_id"] for u in r.json()["post"]["liked"]]

    await client.post(f"/api/posts/{joined['_id']}/{post['_id']}/like_post", headers=user.headers)
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert r.json()["post"]["liked"] == []


async def test_bookmark(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.post(f"/api/posts/{joined['_id']}/{post['_id']}/book_mark", headers=user.headers)
    assert r.status_code == 200, r.text
    r = await client.get("/api/posts/get_book_marked", headers=user.headers)
    assert post["_id"] in [p["_id"] for p in r.json()["posts"]]


async def test_comment_flow(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.post(
        f"/api/posts/{joined['_id']}/{post['_id']}/comments",
        headers=user.headers,
        json={"content": "nice post"},
    )
    assert r.status_code == 200, r.text

    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    comments = r.json()["post"]["comments"]
    assert len(comments) == 1 and comments[0]["content"] == "nice post"
    comment_id = comments[0]["_id"]

    r = await client.request(
        "DELETE",
        f"/api/posts/{joined['_id']}/{post['_id']}/comments",
        headers=user.headers,
        json={"commentId": comment_id},
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert r.json()["post"]["comments"] == []


async def test_empty_comment_rejected(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.post(
        f"/api/posts/{joined['_id']}/{post['_id']}/comments",
        headers=user.headers,
        json={"content": ""},
    )
    assert r.status_code == 400


async def test_notification_on_like(client, user, other_user, joined):
    post = await _create_post(client, user, joined["_id"])
    await client.post(f"/api/channels/{joined['_id']}", headers=other_user.headers)
    await client.post(f"/api/posts/{joined['_id']}/{post['_id']}/like_post", headers=other_user.headers)

    r = await client.get("/api/notifications", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["notRead"] >= 1
    notif = body["notifications"][0]
    assert notif["seeder"]["_id"] == other_user.id

    r = await client.post(f"/api/notifications/{notif['_id']}", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/notifications", headers=user.headers)
    assert r.json()["notRead"] == body["notRead"] - 1


async def test_delete_own_post(client, user, joined):
    post = await _create_post(client, user, joined["_id"])
    r = await client.delete(f"/api/posts/{joined['_id']}/{post['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/posts/get_post_details_in_channel/{post['_id']}", headers=user.headers)
    assert r.status_code == 404


async def test_cannot_delete_other_users_post(client, user, other_user, joined):
    """other_user có bài riêng nhưng không được xoá bài của user."""
    victim_post = await _create_post(client, user, joined["_id"], "victim post")
    await client.post(f"/api/channels/{joined['_id']}", headers=other_user.headers)
    await _create_post(client, other_user, joined["_id"], "attacker own post")

    r = await client.delete(f"/api/posts/{joined['_id']}/{victim_post['_id']}", headers=other_user.headers)
    assert r.status_code == 403, f"user khác xoá được bài! status={r.status_code}"

    r = await client.get(f"/api/posts/get_post_details_in_channel/{victim_post['_id']}", headers=user.headers)
    assert r.status_code == 200, "bài viết đã bị xoá bởi người không có quyền"


async def test_admin_post_endpoints(client, admin, user, joined):
    post = await _create_post(client, user, joined["_id"])

    r = await client.get("/api/posts/get_by_admin", headers=user.headers)
    assert r.status_code == 403

    r = await client.get("/api/posts/get_by_admin", headers=admin.headers)
    assert r.status_code == 200, r.text

    r = await client.delete(f"/api/delete_post_by_admin/{joined['_id']}/{post['_id']}", headers=user.headers)
    assert r.status_code == 403

    r = await client.delete(f"/api/delete_post_by_admin/{joined['_id']}/{post['_id']}", headers=admin.headers)
    assert r.status_code == 200, r.text


async def test_create_post_tolerates_client_sending_null_for_images(client, user, joined):
    """Client gửi `images` = chuỗi "null" khi không chọn ảnh (multer cũ bỏ qua).

    Backend phải chấp nhận, nếu không toàn bộ chức năng đăng bài / sửa hồ sơ hỏng.
    """
    r = await client.post(
        f"/api/posts/{joined['_id']}",
        headers=user.headers,
        data={"content": "no image attached", "images": "null"},
    )
    assert r.status_code == 201, r.text


async def test_update_profile_tolerates_null_file_fields(client, user):
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"username": "still works", "images": "null", "avatar": "null", "certificates": "null"},
    )
    assert r.status_code == 200, r.text
