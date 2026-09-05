import uuid

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


async def test_create_channel_requires_admin(client, user):
    r = await client.post(
        "/api/channels",
        headers=user.headers,
        data={"name": f"nope-{uuid.uuid4().hex[:6]}"},
        files={"images": ("bg.png", PNG, "image/png")},
    )
    assert r.status_code == 403


async def test_admin_creates_channel(client, channel):
    assert channel["name"]
    assert channel["background"]["url"].startswith("public/uploads/")


async def test_duplicate_channel_name(client, admin, channel):
    r = await client.post(
        "/api/channels",
        headers=admin.headers,
        data={"name": channel["name"]},
        files={"images": ("bg.png", PNG, "image/png")},
    )
    assert r.status_code == 409


async def test_channel_details_requires_membership(client, user, channel):
    r = await client.get(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 403

    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text

    r = await client.get(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert user.id in [m["_id"] for m in r.json()["channel"]["members"]]


async def test_leave_channel(client, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200
    r = await client.get(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 403


async def test_get_channels_by_user(client, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    r = await client.get("/api/channels/get_by_user", headers=user.headers)
    assert r.status_code == 200, r.text
    assert channel["_id"] in [c["_id"] for c in r.json()["channels"]]


async def test_update_channel_requires_admin(client, user, channel):
    r = await client.put(
        f"/api/channels/{channel['_id']}", headers=user.headers, data={"name": "hacked"}
    )
    assert r.status_code == 403


async def test_admin_updates_channel(client, admin, channel):
    new_name = f"renamed-{uuid.uuid4().hex[:6]}"
    r = await client.put(
        f"/api/channels/{channel['_id']}", headers=admin.headers, data={"name": new_name, "intro": "x"}
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/channels/{channel['_id']}", headers=admin.headers)
    assert r.json()["channel"]["name"] == new_name


async def test_admin_removes_member(client, admin, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    r = await client.request(
        "DELETE",
        f"/api/channels/{channel['_id']}/delete_user",
        headers=admin.headers,
        json={"userId": user.id},
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 403


async def test_admin_cannot_remove_self(client, admin, channel):
    r = await client.request(
        "DELETE",
        f"/api/channels/{channel['_id']}/delete_user",
        headers=admin.headers,
        json={"userId": admin.id},
    )
    assert r.status_code == 409


async def test_delete_channel_requires_admin(client, user, channel):
    r = await client.delete(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 403


async def test_admin_deletes_channel(client, admin, channel):
    r = await client.delete(f"/api/channels/{channel['_id']}", headers=admin.headers)
    assert r.status_code == 200, r.text
    r = await client.delete(f"/api/channels/{channel['_id']}", headers=admin.headers)
    assert r.status_code == 404


async def test_shortcuts(client, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    r = await client.put(f"/api/shortcuts/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text

    r = await client.get("/api/shortcuts", headers=user.headers)
    assert r.status_code == 200, r.text
    shortcuts = r.json()["shortcuts"]
    assert channel["_id"] in [s["channel"]["_id"] for s in shortcuts]
    assert all(isinstance(s["count"], int) for s in shortcuts)
