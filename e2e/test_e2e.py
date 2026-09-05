import uuid

import httpx
import pytest
import socketio

from .conftest import (
    APP_URL,
    API_URL,
    login_via_ui,
    promote_to_admin,
    register_via_ui,
    unique_email,
)

PNG_B64_BYTES = "[137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82]"


async def _token(page):
    token = await page.evaluate("() => window.localStorage.getItem('social_app_token')")
    assert token, "không tìm thấy access token trong localStorage sau khi đăng nhập"
    return token


async def test_login_page_loads_website_config_from_api(page):
    """Trang login render tên website lấy từ GET /api/website -> backend + CORS hoạt động."""
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    await page.wait_for_selector("text=Login")
    assert "Fuurin" in await page.content(), "không lấy được cấu hình website từ backend"


async def test_unauthenticated_user_is_redirected_to_login(page):
    await page.goto(APP_URL, wait_until="domcontentloaded")
    await page.wait_for_url(f"{APP_URL}/login", timeout=15000)


async def test_register_then_login(page, db):
    email = unique_email("signup")
    await register_via_ui(page, email)
    assert await db.users.find_one({"email": email}), "user chưa được tạo trong DB"

    await login_via_ui(page, email)
    assert page.url.rstrip("/") == APP_URL.rstrip("/")
    await _token(page)


async def test_wrong_password_shows_backend_error_message(page):
    email = unique_email("badpw")
    await register_via_ui(page, email)
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    await page.get_by_placeholder("Enter your email...").fill(email)
    await page.get_by_placeholder("Enter your password...").fill("wrong-password")
    await page.get_by_role("button", name="Login").click()
    await page.wait_for_selector("text=Sai mật khẩu!", timeout=15000)


async def test_plain_user_has_no_admin_menu(page):
    email = unique_email("plain")
    await register_via_ui(page, email)
    await login_via_ui(page, email)
    await page.wait_for_timeout(3000)
    assert await page.get_by_role("link", name="Admin").count() == 0


async def test_admin_sees_admin_menu(page, db):
    email = unique_email("admin")
    await register_via_ui(page, email, username="admin e2e")
    await promote_to_admin(db, email)
    await login_via_ui(page, email)
    await page.wait_for_selector("text=Admin", timeout=20000)


async def test_channel_join_and_post_flow(page, browser, db):
    """Admin tạo channel -> user thường join qua UI -> đăng bài -> bài hiện trên feed."""
    admin_email = unique_email("admin")
    await register_via_ui(page, admin_email, username="admin e2e")
    await promote_to_admin(db, admin_email)
    await login_via_ui(page, admin_email)
    admin_token = await _token(page)

    name = f"e2e-{uuid.uuid4().hex[:6]}"
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
        "00000049454e44ae426082"
    )
    async with httpx.AsyncClient(base_url=API_URL, timeout=30) as api:
        r = await api.post(
            "/api/channels",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"name": name, "intro": "e2e channel"},
            files={"images": ("bg.png", png, "image/png")},
        )
    assert r.status_code == 201, r.text

    channel = await db.channels.find_one({"name": name})
    assert channel is not None

    ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
    user_page = await ctx.new_page()
    try:
        email = unique_email("member")
        await register_via_ui(user_page, email, username="member e2e")
        await login_via_ui(user_page, email)

        await user_page.goto(f"{APP_URL}/channels", wait_until="domcontentloaded")
        await user_page.get_by_placeholder("Search channels...").fill(name)
        await user_page.wait_for_timeout(2500)
        await user_page.get_by_role("button", name="Join").first.click()
        await user_page.wait_for_timeout(2500)

        member = await db.channels.find_one({"name": name})
        user_doc = await db.users.find_one({"email": email})
        assert user_doc["_id"] in member["members"], "join channel không ghi vào DB"

        await user_page.goto(f"{APP_URL}/channels/{channel['_id']}", wait_until="domcontentloaded")
        content = f"e2e post {uuid.uuid4().hex[:6]}"
        # CreatePost dùng ReactQuill -> ô nhập là contenteditable .ql-editor, không phải <input>.
        editor = user_page.locator(".ql-editor").first
        await editor.wait_for(timeout=30000)
        await editor.click()
        await editor.type(content)
        await user_page.get_by_role("button", name="Post", exact=True).first.click()
        await user_page.wait_for_timeout(3000)

        # Quill lưu nội dung dạng HTML (<p>...</p>).
        saved = await db.posts.find_one({"content": {"$regex": content}})
        assert saved, "bài viết không được lưu"
        await user_page.reload(wait_until="domcontentloaded")
        await user_page.wait_for_selector(f"text={content}", timeout=20000)
    finally:
        await ctx.close()


async def test_client_connects_to_socketio_and_receives_new_message(page, db):
    """Client React bắt tay Socket.io của backend Python, tin nhắn mới hiện badge chưa đọc."""
    receiver_email = unique_email("recv")
    sender_email = unique_email("send")

    await register_via_ui(page, receiver_email, username="bob e2e")
    await login_via_ui(page, receiver_email)
    await page.wait_for_timeout(4000)

    receiver = await db.users.find_one({"email": receiver_email})
    assert receiver.get("socketCallId"), (
        "backend không lưu socket id của client -> handler joinCall/Socket.io hỏng"
    )

    async with httpx.AsyncClient(base_url=API_URL, timeout=30) as api:
        r = await api.post(
            "/api/users/register",
            json={"email": sender_email, "password": "Passw0rd!", "username": "alice e2e"},
        )
        assert r.status_code == 201, r.text
    sender = await db.users.find_one({"email": sender_email})

    content = f"xin chao {uuid.uuid4().hex[:6]}"
    sio = socketio.AsyncClient()
    await sio.connect(API_URL, wait_timeout=10)
    try:
        await sio.emit("joinChat", {"_id": str(sender["_id"])})
        await sio.sleep(1)
        await sio.emit(
            "sendMessage",
            {
                "sender": {"_id": str(sender["_id"])},
                "receiver": {"_id": str(receiver["_id"])},
                "content": content,
                "lastSent": {"_id": str(sender["_id"])},
            },
        )
        await sio.sleep(2)
    finally:
        await sio.disconnect()

    assert await db.chats.find_one({"content": content}), "tin nhắn không được lưu vào DB"

    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    body = await page.inner_text("body")
    assert "alice e2e" in body, f"tin nhắn mới không hiện trên UI. body={body[:400]}"
