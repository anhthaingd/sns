"""E2E chạy Playwright trên frontend React thật, gọi backend FastAPI thật."""

import functools
import json
import os
import pathlib
import uuid

import pytest_asyncio
from playwright.async_api import async_playwright
from pymongo import AsyncMongoClient

APP_URL = os.getenv("APP_URL", "http://localhost:5173")
API_URL = os.getenv("API_URL", "http://localhost:3000")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/fuurin")
ARTIFACTS = os.getenv("ARTIFACTS_DIR", "/artifacts")

PASSWORD = "Passw0rd!"

# --- Ngôn ngữ của giao diện khi chạy test -----------------------------------
#
# Cố định ngôn ngữ thay vì để trình duyệt tự chọn: máy CI và máy lập trình viên
# có `Accept-Language` khác nhau, để mặc thì test xanh ở máy này đỏ ở máy kia.
# Mặc định là tiếng Nhật vì đó là ngôn ngữ mặc định của sản phẩm — chạy test
# đúng thứ người dùng thật nhìn thấy. Đổi bằng `E2E_LANG=vi` khi cần soi.
UI_LANG = os.getenv("E2E_LANG", "ja")
LANG_STORAGE_KEY = "social_app_lang"
LOCALES_DIR = pathlib.Path(__file__).resolve().parent.parent / "client" / "src" / "i18n" / "locales"


@functools.cache
def _catalog(namespace: str) -> dict:
    path = LOCALES_DIR / UI_LANG / f"{namespace}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def tr(namespace: str, dotted_key: str) -> str:
    """Chữ hiển thị thật của một khoá, đọc thẳng từ file dịch.

    Test KHÔNG được chép tay câu tiếng Nhật vào đây. Chép tay thì sửa một câu
    trong file dịch sẽ làm đỏ test mà không có lỗi thật nào, và tệ hơn: một
    component quên gọi `t()` vẫn qua được test nếu chuỗi cứng trùng câu đã chép.
    Đọc từ file dịch thì test kiểm đúng thứ cần kiểm — component có nối đúng
    khoá hay không.
    """
    node = _catalog(namespace)
    for part in dotted_key.split("."):
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(f"{namespace}.{dotted_key} không phải chuỗi: {node!r}")
    return node


async def new_page_context(browser):
    """Context trình duyệt đã ghim sẵn ngôn ngữ giao diện.

    `add_init_script` chạy TRƯỚC script của trang ở mọi lần điều hướng, nên
    i18next đọc được lựa chọn ngay từ lần render đầu — không có cảnh chữ nhảy
    từ ngôn ngữ này sang ngôn ngữ khác giữa chừng làm test chập chờn.
    """
    ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
    # Chỉ ĐẶT MẶC ĐỊNH, không ghi đè: script này chạy lại ở MỌI lần điều hướng,
    # nên nếu gán vô điều kiện thì một test đổi ngôn ngữ rồi F5 sẽ thấy ngôn ngữ
    # bị kéo ngược về mặc định — và test đó tưởng nhầm là tính năng ghi nhớ
    # lựa chọn bị hỏng.
    await ctx.add_init_script(
        f"if (!window.localStorage.getItem({LANG_STORAGE_KEY!r})) "
        f"window.localStorage.setItem({LANG_STORAGE_KEY!r}, {UI_LANG!r});"
    )
    return ctx


def unique_email(prefix="e2e"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


@pytest_asyncio.fixture
async def browser():
    async with async_playwright() as p:
        # /dev/shm của container mặc định chỉ 64MB; Chromium dùng hết là tab
        # chết với lỗi mù mờ "Target crashed" — không phải lỗi của ứng dụng.
        # Cách xử lý nằm ở `shm_size` của service `e2e-tests` trong
        # docker-compose.test.yml, KHÔNG dùng `--disable-dev-shm-usage`: cờ đó
        # đẩy Chromium sang ghi /tmp, tức là đổi một giới hạn bộ nhớ lấy một
        # giới hạn ổ đĩa (và ổ đĩa của máy build thường mới là thứ sắp hết).
        b = await p.chromium.launch(args=["--no-sandbox"])
        yield b
        await b.close()


@pytest_asyncio.fixture
async def db():
    mongo = AsyncMongoClient(MONGO_URL)
    yield mongo[MONGO_URL.rsplit("/", 1)[-1]]
    await mongo.close()


async def new_page_with_console(ctx):
    """Trang mới, có ghi lại lỗi console và sự kiện tab chết.

    Trước đây chỉ trang của fixture `page` mới bắt console; trang thứ hai mở
    trong cùng test (kịch bản hai người dùng) thì không. Khi trang thứ hai chết,
    thông báo duy nhất nhận được là "Target crashed" — không có manh mối nào.
    """
    pg = await ctx.new_page()
    console_errors = []
    pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))
    pg.on("crash", lambda _: console_errors.append("### TAB CHET (crash) ###"))
    pg.console_errors = console_errors
    return pg


@pytest_asyncio.fixture
async def page(browser, request):
    ctx = await new_page_context(browser)
    pg = await new_page_with_console(ctx)

    yield pg

    os.makedirs(ARTIFACTS, exist_ok=True)
    try:
        await pg.screenshot(path=f"{ARTIFACTS}/{request.node.name}.png", full_page=True)
    except Exception as err:  # noqa: BLE001 - ảnh chụp chỉ để gỡ lỗi
        # Trang quá dài (feed nhiều bài) thì `full_page=True` có thể vượt giới
        # hạn bộ nhớ của Chromium. Để lỗi đó nổi lên thành lỗi test là báo động
        # giả: phần kiểm tra thật đã chạy xong và đã xanh trước khi tới đây.
        print(f"[e2e] không chụp được màn hình cho {request.node.name}: {err}")
    await ctx.close()


async def register_via_ui(page, email, username="e2e user"):
    await page.goto(f"{APP_URL}/register", wait_until="domcontentloaded")
    name_field = tr("auth", "field.namePlaceholder")
    await page.get_by_placeholder(name_field).wait_for(timeout=30000)
    await page.get_by_placeholder(name_field).fill(username)
    await page.get_by_placeholder(tr("auth", "field.emailPlaceholder")).fill(email)
    await page.get_by_placeholder(tr("auth", "field.passwordPlaceholder")).fill(PASSWORD)
    await page.get_by_role("button", name=tr("auth", "register.submit"), exact=True).click()
    # Form đăng ký chỉ hiện toast thành công, không tự chuyển trang. Câu chữ của
    # toast do BACKEND quyết định (mã `auth.registered`) rồi client dịch lại —
    # nên chờ đúng bản dịch là kiểm luôn cả đường mã-lỗi-về-bản-dịch.
    await page.wait_for_selector(f"text={tr('error', 'server.auth.registered')}", timeout=20000)


async def login_via_ui(page, email):
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    email_field = tr("auth", "field.emailPlaceholder")
    await page.get_by_placeholder(email_field).wait_for(timeout=30000)
    await page.get_by_placeholder(email_field).fill(email)
    await page.get_by_placeholder(tr("auth", "field.passwordPlaceholder")).fill(PASSWORD)
    await page.get_by_role("button", name=tr("auth", "login.submit"), exact=True).click()
    await page.wait_for_url(f"{APP_URL}/", timeout=20000)


async def promote_to_admin(db, email):
    role = await db.roles.find_one({"value": 1})
    await db.users.update_one({"email": email}, {"$set": {"role": role["_id"]}})
