import os
import uuid

import socketio


async def test_website_public(client):
    r = await client.get("/api/website")
    assert r.status_code == 200, r.text
    assert r.json()["website"]["website_name"]


async def test_update_website_requires_admin(client, user, db):
    web = await db.webs.find_one({})
    r = await client.put(f"/api/website/{web['_id']}", headers=user.headers, data={"website_name": "hacked"})
    assert r.status_code == 403


async def test_admin_updates_website(client, admin, db):
    """Quản trị viên đổi được cấu hình website — và test TRẢ LẠI nguyên trạng.

    Cấu hình website là bản ghi DÙNG CHUNG, chỉ có đúng một bản trong DB. Bản cũ
    của test này đặt tên thành `Fuurin-<hex>` rồi bỏ đó, nên sau mỗi lần chạy bộ
    test, môi trường phát triển mang một cái tên vô nghĩa và mọi ảnh chụp màn
    hình sau đó đều dính. Không phải lỗi của ứng dụng, nhưng người nhìn thấy
    tưởng là lỗi.
    """
    web = await db.webs.find_one({})
    before = {k: v for k, v in web.items() if k != "_id"}
    name = f"Fuurin-{uuid.uuid4().hex[:5]}"
    try:
        r = await client.put(
            f"/api/website/{web['_id']}",
            headers=admin.headers,
            data={"website_name": name, "color_title": "#123456"},
        )
        assert r.status_code == 200, r.text
        r = await client.get("/api/website")
        assert r.json()["website"]["website_name"] == name
    finally:
        await db.webs.update_one({"_id": web["_id"]}, {"$set": before})


async def test_newest_messages_empty(client, user):
    r = await client.get("/api/newest_messages", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["messages"] == [] and r.json()["unread"] == 0


async def test_get_chat_empty(client, user, other_user):
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["messages"] == []


async def test_chat_requires_auth(client, user, other_user):
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}")
    assert r.status_code == 401


async def test_socket_send_message_persists_and_delivers(client, user, other_user):
    """Gửi tin qua Socket.io -> lưu DB, trả về REST, và người nhận nhận được realtime."""
    base = os.getenv("BASE_URL", "http://localhost:3000")

    sender = socketio.AsyncClient()
    receiver = socketio.AsyncClient()
    received = []

    @receiver.on("receiveMessage")
    async def _on(data):
        received.append(data)

    # Không gửi header Origin: đây là client server-to-server, không phải trình duyệt.
    # Phần CORS cho origin thật được test ở e2e/ bằng browser thật.
    await sender.connect(base, wait_timeout=10)
    await receiver.connect(base, wait_timeout=10)

    try:
        await receiver.emit("joinChat", {"_id": other_user.id})
        await sender.emit("joinChat", {"_id": user.id})
        await sender.sleep(1)

        content = f"hello-{uuid.uuid4().hex[:6]}"
        await sender.emit(
            "sendMessage",
            {
                "sender": {"_id": user.id},
                "receiver": {"_id": other_user.id},
                "content": content,
                "lastSent": {"_id": user.id},
            },
        )
        await sender.sleep(2)

        assert any(m.get("content") == content for m in received), "người nhận không nhận được tin"
    finally:
        await sender.disconnect()
        await receiver.disconnect()

    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    messages = r.json()["messages"]
    assert content in [m["content"] for m in messages]
    assert messages[0]["sender"]["_id"] == user.id

    r = await client.get("/api/newest_messages", headers=other_user.headers)
    body = r.json()
    assert body["unread"] == 1, body
    msg_id = body["messages"][0]["_id"]

    r = await client.put(f"/api/newest_messages/{msg_id}", headers=other_user.headers)
    assert r.status_code == 200, r.text
    r = await client.get("/api/newest_messages", headers=other_user.headers)
    assert r.json()["unread"] == 0


async def test_read_message_of_other_conversation_is_rejected(client, user, other_user, db):
    """Không được đánh dấu đã đọc hội thoại mình không tham gia."""
    from bson import ObjectId

    fake = await db.newestmessages.insert_one(
        {
            "sender": {"user": ObjectId(), "isRead": False},
            "receiver": {"user": ObjectId(), "isRead": False},
            "content": "private",
        }
    )
    r = await client.put(f"/api/newest_messages/{fake.inserted_id}", headers=user.headers)
    assert r.status_code == 404


async def test_get_chat_is_paginated_and_ordered_oldest_first(client, user, other_user, db):
    """Phân trang + thứ tự hiển thị của lịch sử chat.

    Hai lỗi được sửa cùng lúc ở đây:
    1. `page` trước đây bị bỏ qua -> mở khung chat là tải TOÀN BỘ lịch sử.
    2. Backend sort mới-nhất-trước còn client render từ trên xuống -> lịch sử
       hiển thị ngược, trong khi tin mới qua socket lại nối xuống dưới.
    """
    from datetime import datetime, timedelta, timezone

    from bson import ObjectId

    base = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    await db.chats.insert_many(
        [
            {
                "sender": ObjectId(user.id),
                "receiver": ObjectId(other_user.id),
                "content": f"msg-{i:03d}",
                "timestamp": base + timedelta(seconds=i),
            }
            for i in range(45)
        ]
    )

    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", params={"page": 1}, headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()

    contents = [m["content"] for m in body["messages"]]
    assert len(contents) == 20, f"trang 1 phải có đúng 20 tin, nhận {len(contents)}"
    assert body["totalPage"] == 3, body["totalPage"]
    # Trang 1 = 20 tin GẦN NHẤT, sắp xếp cũ -> mới để client render thẳng từ trên xuống.
    assert contents == sorted(contents), f"sai thứ tự: {contents[:3]} ... {contents[-3:]}"
    assert contents[-1] == "msg-044", contents[-1]
    assert contents[0] == "msg-025", contents[0]

    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", params={"page": 2}, headers=user.headers)
    older = [m["content"] for m in r.json()["messages"]]
    assert older == sorted(older)
    assert older[-1] == "msg-024", older[-1]
    assert set(older).isdisjoint(contents), "trang 2 trùng dữ liệu với trang 1"
