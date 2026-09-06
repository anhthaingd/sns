import json
import uuid

import httpx
import socketio

from .conftest import (
    API_URL,
    APP_URL,
    LOCALES_DIR,
    login_via_ui,
    new_page_context,
    new_page_with_console,
    promote_to_admin,
    register_via_ui,
    tr,
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
    await page.get_by_placeholder(tr("auth", "field.emailPlaceholder")).fill(email)
    await page.get_by_placeholder(tr("auth", "field.passwordPlaceholder")).fill("wrong-password")
    await page.get_by_role("button", name=tr("auth", "login.submit"), exact=True).click()
    # Thông báo cố ý CHUNG cho cả email lạ lẫn sai mật khẩu (chống dò email).
    # Chờ theo bản dịch của mã `auth.invalidCredentials`: đi hết đường từ
    # `raise ApiError(401, code=...)` ở backend tới câu hiển thị trên màn hình.
    await page.wait_for_selector(f"text={tr('error', 'server.auth.invalidCredentials')}", timeout=15000)


async def test_plain_user_has_no_admin_menu(page):
    email = unique_email("plain")
    await register_via_ui(page, email)
    await login_via_ui(page, email)
    await page.wait_for_timeout(3000)
    # Kiểm đúng mục menu quản trị. Bản cũ tìm chữ "Admin" — vốn không có trong
    # giao diện, nên phép đếm luôn bằng 0 và test luôn xanh kể cả khi menu bị lộ.
    assert await page.get_by_role("button", name=tr("nav", "management")).count() == 0


async def test_admin_sees_admin_menu(page, db):
    email = unique_email("admin")
    await register_via_ui(page, email, username="admin e2e")
    await promote_to_admin(db, email)
    await login_via_ui(page, email)
    await page.get_by_role("button", name=tr("nav", "management")).wait_for(timeout=20000)


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

    ctx = await new_page_context(browser)
    user_page = await new_page_with_console(ctx)
    try:
        email = unique_email("member")
        await register_via_ui(user_page, email, username="member e2e")
        await login_via_ui(user_page, email)

        await user_page.goto(f"{APP_URL}/channels", wait_until="domcontentloaded")
        await user_page.get_by_placeholder(tr("channel", "searchPlaceholder")).fill(name)
        await user_page.wait_for_timeout(2500)
        await user_page.get_by_role("button", name=tr("channel", "detail.join"), exact=True).first.click()
        await user_page.wait_for_timeout(2500)

        member = await db.channels.find_one({"name": name})
        user_doc = await db.users.find_one({"email": email})
        assert user_doc["_id"] in member["members"], "join channel không ghi vào DB"

        await user_page.goto(f"{APP_URL}/channels/{channel['_id']}", wait_until="domcontentloaded")
        content = f"e2e post {uuid.uuid4().hex[:6]}"
        # CreatePost dùng ReactQuill -> ô nhập là contenteditable .ql-editor, không phải <input>.
        editor = user_page.locator(".ql-editor").first
        try:
            await editor.wait_for(timeout=30000)
        except Exception:
            print("[e2e] console cua user_page:", user_page.console_errors[-15:])
            raise
        await editor.click()
        await editor.type(content)
        await user_page.get_by_role("button", name=tr("post", "create.submit"), exact=True).first.click()
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
    await page.get_by_placeholder(tr("job", "searchPlaceholder")).wait_for(timeout=30000)

    body = await page.inner_text("body")
    # Câu tổng hợp có dạng "... {{count}} ..." nên chỉ so phần cố định đứng đầu.
    subtitle_head = tr("job", "subtitle_other").split("{{")[0].strip()
    assert subtitle_head in body, f"không thấy số liệu tổng hợp. body={body[:300]}"

    # Bộ lọc bám vào `data-testid` chứ không vào nhãn: nhãn đổi theo ngôn ngữ,
    # còn thứ đang kiểm ở đây là hành vi lọc, không phải câu chữ.
    options = await page.locator("[data-testid='filter-prefecture'] option").all_inner_texts()
    assert len(options) > 1, f"bộ lọc địa điểm trống: {options}"

    # Chọn hai bộ lọc liên tiếp rồi bỏ một cái: kiểm rằng bộ lọc còn lại KHÔNG
    # bị mất. Bản đầu dùng hook `useQueryString` nên mỗi thao tác phải gọi hai
    # lần (đặt bộ lọc + đưa về trang 1) mà cả hai lần đọc cùng một query cũ ->
    # lần sau ghi đè lần trước; còn `deleteQueryString()` thì xoá sạch mọi tham số.
    await page.locator("[data-testid='filter-japanese']").select_option("business")
    await page.wait_for_timeout(1500)
    assert "japanese=business" in page.url, page.url

    await page.locator("[data-testid='filter-prefecture']").select_option("Tokyo")
    await page.wait_for_timeout(1500)
    assert "japanese=business" in page.url and "prefecture=Tokyo" in page.url, page.url
    assert "page=1" in page.url, f"đổi bộ lọc phải quay về trang 1: {page.url}"

    await page.locator("[data-testid='filter-prefecture']").select_option("")
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
    await page.get_by_role("link", name=tr("match", "createResume")).wait_for(timeout=30000)

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
    await page.get_by_text(tr("match", "title")).wait_for(timeout=30000)
    await page.wait_for_timeout(2000)

    body = await page.inner_text("body")
    assert tr("match", "subtitle_other").split("{{")[0].strip() in body
    gap_link = page.get_by_role("link", name=tr("match", "companyGapLink")).first
    assert await gap_link.count() > 0, f"không có công ty nào được gợi ý. body={body[:400]}"

    # Chức năng 2: mở phân tích thiếu sót của công ty đầu bảng.
    await gap_link.click()
    await page.wait_for_timeout(2500)
    gap_body = await page.inner_text("body")
    title_head = tr("match", "companyGap.title").split("{{")[0].strip()
    assert title_head in gap_body, f"body={gap_body[:400]}"
    assert tr("match", "openPositions") in gap_body


async def _create_minimal_resume(page):
    """Tạo CV tối thiểu qua API của ứng dụng.

    Form CV rất dài và không phải thứ đang kiểm ở các test dưới; đi qua API là
    cách nhanh nhất để có được điều kiện tiên quyết.
    """
    token = await page.evaluate("() => window.localStorage.getItem('social_app_token')")
    status = await page.evaluate(
        """async (args) => {
            const body = new FormData();
            body.append('position', 'Backend Engineer');
            body.append('skills', JSON.stringify(['Python', 'Docker']));
            body.append('languages', JSON.stringify(['Japanese N3']));
            body.append('japaneseLevel', 'conversational');
            body.append('yearsOfExperience', '3');
            const res = await fetch(args.api + '/api/resume', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + args.token },
                body,
            });
            return res.status;
        }""",
        {"api": API_URL, "token": token},
    )
    assert status == 200, f"không tạo được CV: {status}"


async def test_whatif_recalculates_when_an_option_is_picked(page):
    """Tick một phương án -> con số kết hợp phải xuất hiện.

    Chọn phần tử theo `data-testid` chứ không theo câu chữ: test này phải sống
    được ở cả ba ngôn ngữ.
    """
    email = unique_email("whatif")
    await register_via_ui(page, email)
    await login_via_ui(page, email)
    await _create_minimal_resume(page)

    await page.goto(f"{APP_URL}/match/whatif", wait_until="domcontentloaded")
    await page.wait_for_selector("[data-testid='whatif-baseline']", timeout=30000)

    options = page.locator("[data-testid='whatif-option']")
    assert await options.count() > 0, "không có phương án nào để mô phỏng"

    await options.first.click()
    await page.wait_for_selector("[data-testid='whatif-combined']", timeout=20000)
    combined = (await page.locator("[data-testid='whatif-combined']").inner_text()).strip()
    assert combined, "tick rồi mà phần kết hợp vẫn trống"


async def test_whatif_needs_a_resume_first(page):
    """Chưa có CV thì phải nói rõ, không hiện màn hình trống."""
    email = unique_email("whatif-nocv")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    await page.goto(f"{APP_URL}/match/whatif", wait_until="domcontentloaded")
    await page.get_by_text(tr("whatif", "needResume")).wait_for(timeout=30000)


async def test_market_page_shows_the_sample_size_next_to_every_median(page):
    """Không được có trung vị nào đứng một mình — cỡ mẫu luôn đi kèm."""
    email = unique_email("market")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    await page.goto(f"{APP_URL}/market", wait_until="domcontentloaded")
    # Nhắm vào TIÊU ĐỀ trang, không phải văn bản bất kỳ: mục menu bên trái mang
    # đúng chữ đó nên `get_by_text` khớp hai phần tử và Playwright báo lỗi.
    await page.get_by_role("heading", name=tr("market", "title")).wait_for(timeout=30000)
    await page.wait_for_timeout(1500)

    body = await page.inner_text("body")
    assert "n=" in body, f"trang thống kê không hiện cỡ mẫu. body={body[:300]}"


async def test_switching_language_changes_the_whole_interface(page, db):
    """Đổi ngôn ngữ đổi cả giao diện tĩnh lẫn câu chữ do backend sinh ra.

    Hai thứ này đi hai đường khác nhau và hỏng độc lập với nhau:

      * menu bên trái là chuỗi trong `nav.json` -> chỉ cần `t()` là xong;
      * toast lỗi là mã `code` do backend trả về (`auth.invalidCredentials`),
        client mới tra sang `error.json`.

    Đường thứ hai là đường dễ gãy: thêm một endpoint quên đặt `code` thì toast
    vẫn hiện, vẫn đúng nghĩa, chỉ là sai ngôn ngữ — không ai phát hiện cho tới
    lúc demo. Nên test kiểm cả hai, và kiểm rằng lựa chọn sống sót qua F5.
    """
    email = unique_email("lang")
    await register_via_ui(page, email)
    await login_via_ui(page, email)

    # Mặc định (UI_LANG) hiển thị đúng.
    await page.get_by_role("button", name=tr("nav", "resume")).first.wait_for(timeout=30000)

    # Đổi sang tiếng Việt bằng chính nút trên thanh header.
    await page.get_by_role("button", name="VI", exact=True).click()
    await page.wait_for_timeout(1000)

    vi_nav = json.loads((LOCALES_DIR / "vi" / "nav.json").read_text(encoding="utf-8"))
    body = await page.inner_text("body")
    assert vi_nav["resume"] in body, f"menu chưa đổi sang tiếng Việt. body={body[:300]}"
    assert await page.evaluate("() => document.documentElement.lang") == "vi"

    # Lựa chọn phải sống sót qua tải lại trang, nếu không người dùng phải bấm
    # lại sau mỗi lần F5.
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    assert vi_nav["resume"] in await page.inner_text("body")

    # Thông báo lỗi do backend sinh ra cũng phải theo ngôn ngữ đang chọn.
    vi_error = json.loads((LOCALES_DIR / "vi" / "error.json").read_text(encoding="utf-8"))
    await page.evaluate("() => window.localStorage.removeItem('social_app_token')")
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    vi_auth = json.loads((LOCALES_DIR / "vi" / "auth.json").read_text(encoding="utf-8"))
    await page.get_by_placeholder(vi_auth["field"]["emailPlaceholder"]).fill(email)
    await page.get_by_placeholder(vi_auth["field"]["passwordPlaceholder"]).fill("sai-mat-khau")
    await page.get_by_role("button", name=vi_auth["login"]["submit"], exact=True).click()
    await page.wait_for_selector(f"text={vi_error['server']['auth']['invalidCredentials']}", timeout=15000)
