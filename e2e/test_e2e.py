import uuid

import httpx
import socketio

from .conftest import (
    API_URL,
    APP_URL,
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
    # Chờ ĐÚNG thứ đang kiểm. Bản cũ chờ chữ "Login" — vốn nằm sẵn trong JSX
    # tĩnh nên xuất hiện TRƯỚC khi GET /api/website trả về, khiến test chập chờn
    # mỗi khi lần tải đầu chậm hơn thường lệ.
    await page.wait_for_selector("text=Fuurin", timeout=20000)
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
    # Thông báo cố ý CHUNG cho cả email lạ lẫn sai mật khẩu (chống dò email).
    await page.wait_for_selector("text=Email hoặc mật khẩu không đúng!", timeout=15000)


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
    assert receiver.get("socketCallId"), "backend không lưu socket id của client -> handler joinCall/Socket.io hỏng"

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


async def test_refresh_token_is_never_exposed_to_javascript(page):
    """Refresh token không được nằm ở nơi JavaScript đọc được.

    XSS đọc `localStorage` và `document.cookie`; cookie `httpOnly` thì không.
    Đó là lý do access token (15 phút) ở localStorage còn refresh token (7 ngày)
    ở cookie httpOnly.

    Giới hạn của môi trường test này: trình duyệt mở `http://client:5173` còn
    API là `http://server:3000` — khác host nên là *cross-site*, và Chromium
    không lưu cookie `SameSite=Lax` đến từ phản hồi cross-site. Vì vậy phần
    "cookie thật sự hoạt động" được kiểm ở `server_python/tests/test_auth.py`
    (set-cookie có HttpOnly, xoay vòng, thu hồi). Chạy thật ở
    localhost:5173 -> localhost:3000 là CÙNG site nên cookie đi bình thường;
    deploy hai domain khác nhau cần COOKIE_SAMESITE=none + COOKIE_SECURE=true
    (bắt buộc HTTPS) — xem README mục 6.
    """
    email = unique_email("cookie")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    exposed = await page.evaluate(
        "() => JSON.stringify({"
        " local: Object.entries(window.localStorage),"
        " session: Object.entries(window.sessionStorage),"
        " cookie: document.cookie })"
    )
    assert "refresh_token" not in exposed, f"refresh token bị lộ cho JavaScript: {exposed}"

    # Nếu trình duyệt có lưu cookie (trường hợp cùng site) thì nó phải httpOnly.
    refresh = next((c for c in await page.context.cookies() if c["name"] == "refresh_token"), None)
    if refresh is not None:
        assert refresh["httpOnly"] is True, "refresh token phải httpOnly"


async def test_recruitment_page_shows_structured_jobs_with_filters(page):
    """Trang việc làm giờ đọc từ DB đã ETL, không còn nhúng HTML crawl trực tiếp."""
    email = unique_email("jobs")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    await page.goto(f"{APP_URL}/recruitment", wait_until="domcontentloaded")
    await page.get_by_placeholder("Tìm theo chức danh, công ty, mô tả...").wait_for(timeout=30000)

    body = await page.inner_text("body")
    assert "tin tổng hợp từ" in body, f"không thấy số liệu tổng hợp. body={body[:300]}"

    # Bộ lọc phải được nạp từ dữ liệu thật, không viết cứng.
    options = await page.locator("select[aria-label='Lọc theo địa điểm'] option").all_inner_texts()
    assert len(options) > 1, f"bộ lọc địa điểm trống: {options}"

    # Chọn hai bộ lọc liên tiếp rồi bỏ một cái: kiểm rằng bộ lọc còn lại KHÔNG
    # bị mất. Bản đầu dùng hook `useQueryString` nên mỗi thao tác phải gọi hai
    # lần (đặt bộ lọc + đưa về trang 1) mà cả hai lần đọc cùng một query cũ ->
    # lần sau ghi đè lần trước; còn `deleteQueryString()` thì xoá sạch mọi tham số.
    await page.locator("select[aria-label='Lọc theo tiếng Nhật']").select_option("business")
    await page.wait_for_timeout(1500)
    assert "japanese=business" in page.url, page.url

    await page.locator("select[aria-label='Lọc theo địa điểm']").select_option("Tokyo")
    await page.wait_for_timeout(1500)
    assert "japanese=business" in page.url and "prefecture=Tokyo" in page.url, page.url
    assert "page=1" in page.url, f"đổi bộ lọc phải quay về trang 1: {page.url}"

    await page.locator("select[aria-label='Lọc theo địa điểm']").select_option("")
    await page.wait_for_timeout(1500)
    assert "prefecture=" not in page.url, page.url
    assert "japanese=business" in page.url, f"bỏ một bộ lọc đã xoá mất bộ lọc khác: {page.url}"


async def test_match_page_requires_a_resume_then_shows_companies(page, db):
    """Chức năng 1 đi hết một vòng qua giao diện thật: chưa có CV -> tạo CV -> có gợi ý."""
    email = unique_email("match")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    # Chưa có CV: phải chỉ đường sang trang tạo CV chứ không hiện lỗi cụt lủn.
    await page.goto(f"{APP_URL}/match", wait_until="domcontentloaded")
    await page.get_by_role("link", name="Tạo CV ngay").wait_for(timeout=30000)

    # Tạo CV tối thiểu ngay qua API của ứng dụng (form CV rất dài, không phải
    # thứ đang kiểm ở test này).
    token = await page.evaluate("() => window.localStorage.getItem('social_app_token')")
    result = await page.evaluate(
        """async (args) => {
            const body = new FormData();
            body.append('position', 'Backend Engineer');
            body.append('skills', JSON.stringify(['Python', 'Docker', 'AWS']));
            body.append('languages', JSON.stringify(['Japanese N2', 'English business level']));
            body.append('japaneseLevel', 'business');
            body.append('yearsOfExperience', '5');
            const res = await fetch(args.api + '/api/resume', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + args.token },
                body,
            });
            return res.status;
        }""",
        {"api": API_URL, "token": token},
    )
    assert result == 200, f"không tạo được CV: {result}"

    await page.goto(f"{APP_URL}/match", wait_until="domcontentloaded")
    await page.get_by_text("Công ty phù hợp với bạn").wait_for(timeout=30000)
    await page.wait_for_timeout(2000)

    body = await page.inner_text("body")
    assert "Xếp hạng" in body
    gap_link = page.get_by_role("link", name="Tôi còn thiếu gì để vào công ty này →").first
    assert await gap_link.count() > 0, f"không có công ty nào được gợi ý. body={body[:400]}"

    # Chức năng 2: mở phân tích thiếu sót của công ty đầu bảng.
    await gap_link.click()
    await page.wait_for_timeout(2500)
    gap_body = await page.inner_text("body")
    assert "Bạn còn thiếu gì để vào" in gap_body, f"body={gap_body[:400]}"
    assert "Các vị trí đang tuyển" in gap_body
