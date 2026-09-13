"""Chụp bộ ảnh tư liệu cho toàn bộ giao diện Fuurin.

Đây KHÔNG phải test. File này dựng sẵn một tài khoản demo có dữ liệu thật —
CV đầy đủ, channel có ảnh bìa, bài viết, bình luận, lượt thích, người theo dõi,
tin nhắn — rồi đi hết mọi màn hình và chụp lại.

Vì sao phải tự dựng dữ liệu thay vì chụp DB đang có: DB dev đầy bản ghi do bộ
test sinh ra ("e2e user", "e2e-a3f9c1"). Ảnh tư liệu chụp những thứ đó thì
người đọc không hiểu màn hình đang làm gì.

Chạy:
    docker compose -f docker-compose.yml -f docker-compose.test.yml \
        run --rm -e E2E_LANG=vi e2e-tests python -m e2e.capture_docs

Ảnh ra ở docs/screenshots/ kèm manifest.json mô tả từng ảnh.
"""

import asyncio
import json
import math
import os
import pathlib
import struct
import uuid
import zlib

import httpx
import socketio
from playwright.async_api import async_playwright
from pymongo import AsyncMongoClient

from .conftest import (
    API_URL,
    APP_URL,
    MONGO_URL,
    PASSWORD,
    new_page_context,
    tr,
)

OUT = pathlib.Path(os.getenv("DOCS_DIR", "/work/docs/screenshots"))
DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}

SHOTS = []


# --- Ảnh bìa channel ---------------------------------------------------------
#
# Container e2e không có Pillow, và thêm một thư viện chỉ để vẽ một ảnh bìa là
# không đáng. PNG không nén phức tạp: header + IDAT là zlib của các hàng pixel.


def _png(width, height, pixel):
    rows = []
    for y in range(height):
        row = bytearray([0])  # filter type 0 (None) ở đầu mỗi hàng
        for x in range(width):
            row += bytes(pixel(x, y))
        rows.append(bytes(row))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
        + chunk(b"IEND", b"")
    )


def cover_png(width=960, height=320):
    """Chuyển sắc ai(藍) -> asagi(浅葱) phủ hoa văn seigaiha(青海波).

    Dùng đúng hai màu thương hiệu trong tailwind.config.js (ai-700, asagi-600)
    để ảnh bìa không chọi với giao diện.
    """
    a, b = (0x1E, 0x3A, 0x60), (0x0A, 0x70, 0x70)
    r = 72

    def pixel(x, y):
        t = x / width * 0.65 + y / height * 0.35
        base = [int(a[i] + (b[i] - a[i]) * t) for i in range(3)]
        cx, cy = round(x / r) * r, round(y / r) * r
        d = math.hypot(x - cx, y - cy)
        if d < r and (d % (r / 3)) / (r / 3) > 0.74:
            base = [min(255, c + 30) for c in base]
        return base

    return _png(width, height, pixel)


# Năm sắc thương hiệu trong tailwind.config.js, dùng làm màu ảnh đại diện.
TINTS = ["#274A78", "#0A7070", "#A22F14", "#33653F", "#A47522"]


def identicon_png(seed, size=256):
    """Ảnh đại diện hình học, đối xứng gương — mỗi tên một hình khác nhau.

    CHỈ tài khoản chính dùng cái này, để ảnh tư liệu có cả hai trạng thái mà
    người dùng thật gặp: người đã tải ảnh lên, và người chưa — người chưa thì
    `Avatar.jsx` dựng chữ cái đầu tên trên một trong sáu sắc chàm/asagi chọn
    theo tên, nên vẫn phân biệt được nhau.
    """
    h = 0
    for ch in seed:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    fg = TINTS[h % len(TINTS)]
    fg = (int(fg[1:3], 16), int(fg[3:5], 16), int(fg[5:7], 16))
    bg = (246, 245, 242)  # washi
    grid, cell = 5, size // 5
    filled = set()
    bits = h
    for col in range(3):
        for row in range(grid):
            bits = (bits * 1103515245 + 12345) & 0x7FFFFFFF
            if bits >> 16 & 1:
                filled.add((col, row))
                filled.add((grid - 1 - col, row))

    def pixel(x, y):
        return fg if (x // cell, y // cell) in filled else bg

    return _png(size, size, pixel)


# --- Dựng dữ liệu demo -------------------------------------------------------

POSTS = [
    "<p>Tuần này mình vừa hoàn thành vòng phỏng vấn kỹ thuật ở một công ty "
    "SIer tại Tokyo. Điều bất ngờ nhất: họ hỏi rất kỹ về cách mình <b>giải "
    "thích lỗi cho người không làm kỹ thuật</b>, chứ không phải thuật toán.</p>",
    "<p>Chia sẻ nhỏ cho bạn nào đang ôn JLPT N2: phần 聴解 chiếm nhiều điểm "
    "hơn mọi người tưởng. Mình đã dành 40% thời gian ôn cho riêng phần nghe "
    "và điểm tổng tăng rõ rệt.</p>",
    "<p>Câu hỏi cho mọi người: khi thương lượng lương ở Nhật, các bạn đưa ra "
    "con số trước hay chờ công ty đề xuất? Mình dùng trang "
    "<i>Bản đồ thị trường</i> để lấy trung vị theo vị trí rồi mới trả lời.</p>",
    "<p>Đã dùng thử tính năng <b>Nếu tôi học thêm</b> — chọn thử “N2” "
    "thì số công ty phù hợp tăng từ 12 lên 34. Nhìn con số cụ thể tự nhiên có "
    "động lực học hẳn.</p>",
]

COMMENTS = [
    "Cảm ơn bạn đã chia sẻ! Mình cũng đang chuẩn bị vòng phỏng vấn tương tự.",
    "Phần nghe đúng là khó nhất. Bạn ôn bằng tài liệu nào vậy?",
]

RESUME = {
    "name": "Nguyễn Anh Thái",
    "position": "Backend Engineer",
    "birthday": "1998-04-12",
    "email": "thai.nguyen@example.com",
    "address": "Cầu Giấy, Hà Nội",
    "phone": "090-1234-5678",
    "github": "https://github.com/anhthai",
    "objective": "Trở thành kỹ sư cầu nối giữa đội phát triển Việt Nam và "
    "khách hàng Nhật Bản, tập trung vào hệ thống backend chịu tải cao.",
    "educationName": "Đại học Bách khoa Hà Nội",
    "educationMajor": "Công nghệ thông tin",
    "educationCompletion": "2020",
    "educationGPA": "3.4",
    "japaneseLevel": "business",
    "englishLevel": "conversational",
    "yearsOfExperience": "5",
    "desiredSalaryMin": "5500000",
    "skills": ["Python", "FastAPI", "MongoDB", "Docker", "AWS", "React", "Redis"],
    "languages": ["Tiếng Nhật N2", "Tiếng Anh giao tiếp"],
    "desiredLocations": ["Tokyo", "Osaka"],
    "experiences": [
        {
            "name": "Sun Asterisk Việt Nam",
            "startTime": "2021-06",
            "endTime": "Hiện tại",
            "position": "Backend Engineer",
            "description": "Phát triển API cho hệ thống tuyển dụng phục vụ thị "
            "trường Nhật, tối ưu truy vấn Mongo giảm 60% thời gian phản hồi.",
        },
        {
            "name": "FPT Software",
            "startTime": "2020-08",
            "endTime": "2021-05",
            "position": "Junior Developer",
            "description": "Bảo trì hệ thống quản lý kho cho khách hàng Nhật Bản.",
        },
    ],
    "projects": [
        {
            "name": "Fuurin — nền tảng tuyển dụng kết hợp mạng xã hội",
            "tech": "FastAPI, MongoDB, React, Docker",
            "description": "So khớp CV với tin tuyển dụng bằng embedding kết hợp luật, "
            "kèm mô phỏng đối chứng “nếu tôi học thêm”.",
        },
    ],
}


async def api_register(api, email, username):
    r = await api.post(
        "/api/users/register",
        json={"email": email, "password": PASSWORD, "username": username},
    )
    assert r.status_code == 201, r.text


async def api_login(api, email):
    r = await api.post("/api/users/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["accessToken"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def seed(api, db):
    """Tạo toàn bộ dữ liệu demo, trả về các id cần cho phần chụp."""
    # Dọn dữ liệu demo của lần chạy trước. Không dọn thì mỗi lần chạy lại thêm
    # một bộ "Nguyễn Anh Thái" nữa, và trang tìm kiếm trong ảnh tư liệu hiện ba
    # người trùng tên — người đọc tưởng đó là lỗi của ứng dụng.
    old_users = await db.users.find({"email": {"$regex": "@fuurin\\.dev$"}}).to_list(200)
    if old_users:
        old_ids = [u["_id"] for u in old_users]
        old_channel = await db.channels.find_one({"name": "Kỹ sư cầu nối Việt–Nhật"})
        if old_channel:
            await db.posts.delete_many({"channel": old_channel["_id"]})
            await db.channels.delete_one({"_id": old_channel["_id"]})
        for coll in ("resumes", "followers", "followings", "notifications", "shortcuts"):
            await db[coll].delete_many({"user": {"$in": old_ids}})
        await db.chats.delete_many({"sender": {"$in": old_ids}})
        await db.newestmessages.delete_many({"sender": {"$in": old_ids}})
        await db.users.delete_many({"_id": {"$in": old_ids}})
        print(f"[seed] đã dọn {len(old_ids)} tài khoản demo của lần chạy trước")

    tag = uuid.uuid4().hex[:6]
    people = {
        "main": (f"demo-thai-{tag}@fuurin.dev", "Nguyễn Anh Thái"),
        "friend": (f"demo-khoa-{tag}@fuurin.dev", "Trần Minh Khoa"),
        "admin": (f"demo-admin-{tag}@fuurin.dev", "Quản trị viên Fuurin"),
        "extra1": (f"demo-ha-{tag}@fuurin.dev", "Lê Thu Hà"),
        "extra2": (f"demo-duy-{tag}@fuurin.dev", "Phạm Quốc Duy"),
    }
    tokens, ids = {}, {}
    for key, (email, username) in people.items():
        await api_register(api, email, username)
        tokens[key] = await api_login(api, email)
        doc = await db.users.find_one({"email": email})
        ids[key] = str(doc["_id"])

        # Chỉ tài khoản chính tải ảnh lên (kèm ảnh bìa cho trang cá nhân).
        # Bốn người còn lại để trống, để ảnh tư liệu cho thấy cả nhánh dựng chữ
        # cái đầu tên trong `Avatar.jsx`.
        if key == "main":
            r = await api.put(
                f"/api/users/{ids[key]}",
                headers=auth(tokens[key]),
                data={"update_images": "both"},
                files=[
                    ("images", ("avatar.png", identicon_png(username), "image/png")),
                    ("images", ("cover.png", cover_png(), "image/png")),
                ],
            )
            assert r.status_code == 200, r.text
    print("[seed] đã tạo 5 tài khoản demo")

    # DB dev bị bộ test API đổi tên website thành "Fuurin-<hex>" và thay logo.
    # Trả về đúng giá trị của `server_python/data/social_app.webs.json` để ảnh
    # chụp khớp với một lần cài đặt sạch.
    seed_web = json.loads(pathlib.Path("/work/server_python/data/social_app.webs.json").read_text(encoding="utf-8"))[0]
    await db.webs.update_one(
        {},
        {"$set": {k: v for k, v in seed_web.items() if k != "_id"}},
    )
    print("[seed] đặt lại cấu hình website")

    # Admin phải có quyền trước khi tạo channel.
    role = await db.roles.find_one({"value": 1})
    await db.users.update_one({"email": people["admin"][0]}, {"$set": {"role": role["_id"]}})
    tokens["admin"] = await api_login(api, people["admin"][0])

    # Tên cố định (không gắn hậu tố ngẫu nhiên) để ảnh tư liệu đọc được; chạy
    # lại lần sau thì dùng lại đúng channel đó thay vì tạo bản trùng tên.
    channel_name = "Kỹ sư cầu nối Việt–Nhật"
    channel = await db.channels.find_one({"name": channel_name})
    if channel is None:
        r = await api.post(
            "/api/channels",
            headers=auth(tokens["admin"]),
            data={
                "name": channel_name,
                "intro": "Nơi trao đổi kinh nghiệm phỏng vấn, JLPT và văn hoá làm việc "
                "cho kỹ sư Việt Nam đang tìm việc tại Nhật Bản.",
            },
            files={"images": ("cover.png", cover_png(), "image/png")},
        )
        assert r.status_code == 201, r.text
        channel = await db.channels.find_one({"name": channel_name})
    channel_id = str(channel["_id"])
    print(f"[seed] channel {channel_name}")

    for key in ("main", "friend", "extra1", "extra2"):
        await api.post(f"/api/channels/{channel_id}", headers=auth(tokens[key]))

    authors = ["main", "friend", "extra1", "main"]
    for content, who in zip(POSTS, authors, strict=True):
        r = await api.post(
            f"/api/posts/{channel_id}",
            headers=auth(tokens[who]),
            data={"content": content},
        )
        assert r.status_code == 201, r.text
        await asyncio.sleep(0.3)

    posts = await db.posts.find({"channel": channel["_id"]}).sort("created_at", -1).to_list(len(POSTS))
    featured = str(posts[-1]["_id"])  # bài cũ nhất trong loạt vừa đăng: bài có bình luận
    print(f"[seed] {len(posts)} bài viết")

    for who, text in zip(("friend", "extra1"), COMMENTS, strict=True):
        await api.post(
            f"/api/posts/{channel_id}/{featured}/comments",
            headers=auth(tokens[who]),
            json={"content": text},
        )
    for who in ("friend", "extra1", "extra2"):
        await api.post(f"/api/posts/{channel_id}/{featured}/like_post", headers=auth(tokens[who]))
        await api.post(f"/api/users/{ids['main']}/following", headers=auth(tokens[who]))
    await api.post(f"/api/users/{ids['friend']}/following", headers=auth(tokens["main"]))
    await api.post(f"/api/posts/{channel_id}/{featured}/book_mark", headers=auth(tokens["main"]))
    print("[seed] bình luận, lượt thích, theo dõi, đánh dấu")

    form = {k: v for k, v in RESUME.items() if isinstance(v, str)}
    for k in ("skills", "languages", "desiredLocations", "experiences", "projects"):
        form[k] = json.dumps(RESUME[k], ensure_ascii=False)
    r = await api.post("/api/resume", headers=auth(tokens["main"]), data=form)
    assert r.status_code == 200, r.text
    print("[seed] CV đầy đủ")

    # Tin nhắn đi qua Socket.io chứ không qua REST — đúng đường mà ứng dụng dùng.
    sio = socketio.AsyncClient()
    await sio.connect(API_URL, wait_timeout=10)
    try:
        await sio.emit("joinChat", {"_id": ids["friend"]})
        await sio.sleep(1)
        for text in (
            "Chào Thái! Công ty mình đang tuyển Backend, bạn quan tâm không?",
            "Yêu cầu N2 trở lên, làm ở Tokyo, có hỗ trợ visa nhé.",
        ):
            await sio.emit(
                "sendMessage",
                {
                    "sender": {"_id": ids["friend"]},
                    "receiver": {"_id": ids["main"]},
                    "content": text,
                    "lastSent": {"_id": ids["friend"]},
                },
            )
            await sio.sleep(1)
    finally:
        await sio.disconnect()
    print("[seed] tin nhắn")

    # Id công ty / việc làm để chụp hai trang phân tích thiếu sót.
    # Cả hai endpoint trả về `matches`, mỗi phần tử có `company` và `bestJob`
    # — đúng các trường mà MatchLayout.jsx dựng link.
    r = await api.get("/api/match/companies?page=1", headers=auth(tokens["main"]))
    matches = r.json().get("matches") or []
    company_id = matches[0]["company"].get("_id") if matches else None
    job_id = None
    for m in matches:
        if (m.get("bestJob") or {}).get("_id"):
            job_id = m["bestJob"]["_id"]
            break
    print(f"[seed] gợi ý: {len(matches)} công ty, company={company_id}, job={job_id}")

    return {
        "emails": {k: v[0] for k, v in people.items()},
        "ids": ids,
        "channel": channel_id,
        "post": featured,
        "company": company_id,
        "job": job_id,
        "search": "Nguyễn",
    }


# --- Chụp ảnh ----------------------------------------------------------------


async def shot(page, name, title, group, note, full_page=False, wait=1400):
    await page.wait_for_timeout(wait)
    await page.screenshot(path=str(OUT / name), full_page=full_page)
    SHOTS.append({"file": name, "title": title, "group": group, "note": note})
    print(f"[shot] {name}  ({title})")


async def wait_for_advice(page, timeout=30000):
    """Chờ thẻ gợi ý của LLM xong việc rồi mới chụp.

    Không có bước này thì ảnh tư liệu chụp đúng lúc khung chờ đang quay. Chờ
    khung chờ BIẾN MẤT (chứ không chờ thẻ hiện ra) là cách duy nhất đúng cho cả
    hai trường hợp: có cấu hình LLM thì thẻ hiện, không cấu hình thì thẻ không
    bao giờ hiện và chờ nó là treo vô ích.
    """
    try:
        await page.wait_for_selector("[data-testid='advice-skeleton']", state="detached", timeout=timeout)
    except Exception as err:  # noqa: BLE001 - ảnh vẫn chụp được, chỉ là có khung chờ
        print(f"[warn] thẻ gợi ý chưa xong sau {timeout}ms: {err}")


async def goto(page, path, wait=1600):
    await page.goto(f"{APP_URL}{path}", wait_until="domcontentloaded")
    await page.wait_for_timeout(wait)


async def login(page, email):
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    field = tr("auth", "field.emailPlaceholder")
    await page.get_by_placeholder(field).wait_for(timeout=30000)
    await page.get_by_placeholder(field).fill(email)
    await page.get_by_placeholder(tr("auth", "field.passwordPlaceholder")).fill(PASSWORD)
    await page.get_by_role("button", name=tr("auth", "login.submit"), exact=True).click()
    await page.wait_for_url(f"{APP_URL}/", timeout=25000)
    await page.wait_for_timeout(2500)


async def set_theme(page, theme):
    await page.evaluate("(t) => window.localStorage.setItem('social_app_theme', t)", theme)
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)


async def capture_auth(browser):
    ctx = await new_page_context(browser)
    page = await ctx.new_page()
    try:
        await goto(page, "/login")
        await shot(
            page,
            "01-dang-nhap.png",
            "Đăng nhập",
            "Xác thực",
            "Tên và mô tả website lấy từ API `GET /api/website`, không viết cứng ở frontend.",
        )
        await goto(page, "/register")
        await shot(
            page,
            "02-dang-ky.png",
            "Đăng ký",
            "Xác thực",
            "Cùng khung nền với trang đăng nhập; ba luận điểm giá trị nằm ở cột trái.",
        )
        await goto(page, "/khong-ton-tai")
        await shot(
            page,
            "03-khong-tim-thay.png",
            "Trang không tồn tại",
            "Xác thực",
            "Đường dẫn lạ rơi vào màn hình 404 có lối quay lại, không phải màn hình trắng.",
        )
    finally:
        await ctx.close()


async def capture_main(browser, w):
    ctx = await new_page_context(browser)
    page = await ctx.new_page()
    try:
        await login(page, w["emails"]["main"])

        await shot(
            page,
            "10-bang-tin.png",
            "Bảng tin",
            "Mạng xã hội",
            "Ba cột: điều hướng trái, dòng bài giữa, gợi ý phải. Cột phải ẩn dưới 1280px.",
        )

        await page.locator("[data-testid='composer-open']").first.click()
        await shot(
            page,
            "11-soan-bai.png",
            "Soạn bài viết",
            "Mạng xã hội",
            "Ô soạn bài mặc định thu gọn một dòng; bấm mới mở trình soạn thảo Quill và ô chọn channel.",
        )
        await page.keyboard.press("Escape")

        await goto(page, "/channels")
        await shot(
            page,
            "12-danh-sach-channel.png",
            "Danh sách channel",
            "Mạng xã hội",
            "Mỗi thẻ có ảnh bìa, số thành viên và nút tham gia; trạng thái đang xử lý bám theo từng thẻ.",
        )

        await goto(page, f"/channels/{w['channel']}")
        await shot(
            page,
            "13-chi-tiet-channel.png",
            "Chi tiết channel",
            "Mạng xã hội",
            "Ảnh bìa seigaiha, phần giới thiệu, danh sách thành viên và dòng bài của riêng channel.",
            full_page=True,
        )

        await goto(page, f"/channels/{w['channel']}/posts/{w['post']}")
        await shot(
            page,
            "14-chi-tiet-bai-viet.png",
            "Chi tiết bài viết & bình luận",
            "Mạng xã hội",
            "Bình luận hiển thị 2 dòng đầu rồi gập lại; ô nhập là `<input>` thật chứ không phải contentEditable.",
            full_page=True,
        )

        await goto(page, "/bookmarks")
        await shot(
            page,
            "15-da-luu.png",
            "Bài đã lưu",
            "Mạng xã hội",
            "Danh sách bài người dùng đã đánh dấu, dùng lại đúng component bài viết của bảng tin.",
        )

        await goto(page, f"/profile/{w['ids']['main']}")
        await shot(
            page,
            "16-trang-ca-nhan.png",
            "Trang cá nhân",
            "Mạng xã hội",
            "Ảnh bìa, thông tin, số người theo dõi và các bài đã đăng.",
            full_page=True,
        )

        await goto(page, f"/search?s={w['search']}&tab=users")
        await shot(
            page,
            "17-tim-nguoi-dung.png",
            "Tìm kiếm — người dùng",
            "Mạng xã hội",
            "Kết quả người dùng kèm nút theo dõi và nhắn tin ngay trên từng dòng.",
        )

        await goto(page, "/search?s=JLPT&tab=posts")
        await shot(
            page,
            "18-tim-bai-viet.png",
            "Tìm kiếm — bài viết",
            "Mạng xã hội",
            "Cùng ô tìm kiếm, đổi tab sang bài viết; từ khoá nằm ở tham số `s` trên URL nên chia sẻ được.",
        )

        await goto(page, "/users/settings")
        await shot(
            page,
            "19-cai-dat-tai-khoan.png",
            "Cài đặt tài khoản",
            "Mạng xã hội",
            "Ba tab: bài viết của tôi, người theo dõi, đang theo dõi.",
        )

        await goto(page, "/")
        await page.get_by_role("button", name=tr("nav", "notifications")).click()
        await shot(
            page,
            "20-thong-bao.png",
            "Thông báo",
            "Mạng xã hội",
            "Huy hiệu đếm số chưa đọc hiện ngay khi tải trang, không chờ tới lúc mở bảng.",
            wait=1200,
        )
        await page.keyboard.press("Escape")

        await page.get_by_role("button", name=tr("nav", "messages")).click()
        await page.wait_for_timeout(1200)
        await shot(
            page,
            "21-hop-thu.png",
            "Hộp thư",
            "Mạng xã hội",
            "Danh sách hội thoại lấy qua Socket.io; tin nhắn mới đẩy thẳng xuống client.",
            wait=600,
        )
        try:
            await page.get_by_text("Trần Minh Khoa").first.click()
            await shot(
                page,
                "22-tro-chuyen.png",
                "Trò chuyện",
                "Mạng xã hội",
                "Hộp thoại chat thời gian thực, có cả nút gọi video (simple-peer).",
                wait=1800,
            )
            await page.keyboard.press("Escape")
        except Exception as err:
            print(f"[warn] không mở được hộp thoại chat: {err}")

        # --- Tuyển dụng ---
        await goto(page, "/recruitment")
        await shot(
            page,
            "30-tin-tuyen-dung.png",
            "Tin tuyển dụng",
            "Tuyển dụng",
            "Dữ liệu đã qua ETL vào DB; cột lọc bên phải dính theo cuộn.",
            full_page=True,
        )

        await page.locator("[data-testid='filter-japanese']").select_option("business")
        await page.wait_for_timeout(1500)
        await page.locator("[data-testid='filter-prefecture']").select_option("Tokyo")
        await shot(
            page,
            "31-loc-tin-tuyen-dung.png",
            "Lọc tin tuyển dụng",
            "Tuyển dụng",
            "Mỗi bộ lọc đang bật thành một chip bỏ được; bộ lọc ghi vào URL nên F5 không mất.",
            wait=2000,
        )

        await goto(page, "/resume")
        await wait_for_advice(page)
        await shot(
            page,
            "32-ho-so-cv.png",
            "Hồ sơ CV",
            "Tuyển dụng",
            "Biểu mẫu CV chia khối: thông tin, kinh nghiệm, học vấn, kỹ năng, dự án.",
            full_page=True,
        )

        try:
            await page.get_by_role("button", name=tr("resume", "actions.downloadPreview")).first.click()
            await page.wait_for_timeout(2000)
            await shot(
                page,
                "33-xem-truoc-cv-mau-1.png",
                "Xem trước CV — mẫu 1",
                "Tuyển dụng",
                "Bản xem trước luôn giữ nền trắng chữ đen kể cả ở chế độ tối: đây là bản sẽ in ra giấy.",
            )
            await page.get_by_role("button", name=tr("resume", "template.pick2")).click()
            await shot(
                page,
                "34-xem-truoc-cv-mau-2.png",
                "Xem trước CV — mẫu 2",
                "Tuyển dụng",
                "Mẫu thứ hai cùng dữ liệu, đổi bố cục sang hai cột.",
                wait=1500,
            )
            await page.keyboard.press("Escape")
        except Exception as err:
            print(f"[warn] không mở được xem trước CV: {err}")

        # --- So khớp ---
        await goto(page, "/match")
        await wait_for_advice(page)
        await shot(
            page,
            "40-cong-ty-phu-hop.png",
            "Công ty phù hợp",
            "So khớp",
            "Điểm phù hợp tính từ CV: vòng cung 270° kèm số, không chỉ một thanh màu.",
            full_page=True,
        )

        if w["company"]:
            await goto(page, f"/match/companies/{w['company']}")
            await wait_for_advice(page)
            await shot(
                page,
                "41-thieu-sot-cong-ty.png",
                "Phân tích thiếu sót — công ty",
                "So khớp",
                "Điều kiện loại chỉ giữ mốc dễ nhất trong các vị trí đang tuyển; kỹ năng xếp "
                "theo số vị trí yêu cầu, nên dòng đầu là thứ đáng học nhất.",
                full_page=True,
            )
        if w["job"]:
            await goto(page, f"/match/jobs/{w['job']}")
            await wait_for_advice(page)
            await shot(
                page,
                "42-thieu-sot-viec-lam.png",
                "Phân tích thiếu sót — tin tuyển dụng",
                "So khớp",
                "Cùng cách trình bày, nhưng đối chiếu với một tin cụ thể.",
                full_page=True,
            )

        await goto(page, "/match/whatif")
        await wait_for_advice(page)
        await shot(
            page,
            "43-mo-phong.png",
            "Mô phỏng “Nếu tôi học thêm”",
            "So khớp",
            "Điểm gốc nằm trên cùng; mỗi phương án ghi rõ mức tăng nếu chọn.",
            full_page=True,
        )
        options = page.locator("[data-testid='whatif-option']")
        if await options.count() > 0:
            await options.first.click()
            await page.wait_for_timeout(1500)
            if await options.count() > 1:
                await options.nth(1).click()
            await shot(
                page,
                "44-mo-phong-ket-qua.png",
                "Mô phỏng — kết quả kết hợp",
                "So khớp",
                "Chọn nhiều phương án thì thẻ kết quả kết hợp dính ở mép dưới, không phải cuộn đi tìm.",
                full_page=True,
                wait=2200,
            )

        await goto(page, "/market")
        await wait_for_advice(page)
        await shot(
            page,
            "45-ban-do-thi-truong.png",
            "Bản đồ thị trường",
            "So khớp",
            "Biểu đồ thanh một sắc asagi, không chú giải thừa; mọi trung vị đều đi kèm cỡ mẫu n=.",
            full_page=True,
        )

        # --- Chế độ tối ---
        await set_theme(page, "dark")
        await goto(page, "/")
        await shot(
            page,
            "60-toi-bang-tin.png",
            "Chế độ tối — bảng tin",
            "Giao diện",
            "Nền sumi(墨) #0E1219; các token màu đổi giá trị chứ không phải lật ngược màu.",
        )
        await goto(page, "/recruitment")
        await shot(
            page,
            "61-toi-tin-tuyen-dung.png",
            "Chế độ tối — tin tuyển dụng",
            "Giao diện",
            "Sắc thương hiệu chuyển sang bậc nhạt hơn (ai-500) để giữ tương phản trên nền tối.",
        )
        await goto(page, "/market")
        await wait_for_advice(page)
        await shot(
            page,
            "62-toi-bieu-do.png",
            "Chế độ tối — biểu đồ",
            "Giao diện",
            "Bảng màu biểu đồ được chọn riêng cho nền tối, không dùng lại bảng của nền sáng.",
            full_page=True,
        )
        await set_theme(page, "light")
    finally:
        await ctx.close()


async def capture_admin(browser, w):
    ctx = await new_page_context(browser)
    page = await ctx.new_page()
    try:
        await login(page, w["emails"]["admin"])

        await goto(page, "/admin/management")
        await shot(
            page,
            "50-quan-tri-website.png",
            "Quản trị — cấu hình website",
            "Quản trị",
            "Tên, mô tả và logo của website sửa tại đây rồi áp dụng cho mọi trang.",
            full_page=True,
        )

        for key, label_key, name, title, note in (
            (
                "user",
                "management.tabs.users",
                "51-quan-tri-nguoi-dung.png",
                "Quản trị — người dùng",
                "Mã người dùng đứng cột cuối, cỡ chữ nhỏ: thứ chỉ dùng khi tra sự cố không nên chiếm chỗ dễ đọc nhất.",
            ),
            (
                "channel",
                "management.tabs.channels",
                "52-quan-tri-channel.png",
                "Quản trị — channel",
                "Danh sách channel kèm số thành viên và thao tác xoá.",
            ),
            (
                "user_posts",
                "management.tabs.userPosts",
                "53-quan-tri-bai-viet.png",
                "Quản trị — bài viết",
                "Bài viết của toàn hệ thống, tìm theo từ khoá và phân trang phía máy chủ.",
            ),
        ):
            try:
                await page.get_by_role("tab", name=tr("admin", label_key)).click()
                await shot(page, name, title, "Quản trị", note, full_page=True, wait=2200)
            except Exception as err:
                print(f"[warn] không mở được tab {key}: {err}")

        await goto(page, "/admin/settings")
        await shot(
            page,
            "54-quan-tri-ca-nhan.png",
            "Quản trị — trang cá nhân",
            "Quản trị",
            "Tab bài viết / người theo dõi / đang theo dõi của chính tài khoản quản trị.",
            full_page=True,
        )
    finally:
        await ctx.close()


async def capture_mobile(browser, w):
    ctx = await browser.new_context(viewport=MOBILE, device_scale_factor=2)
    await ctx.add_init_script(
        "if (!window.localStorage.getItem('social_app_lang')) window.localStorage.setItem('social_app_lang', 'vi');"
    )
    page = await ctx.new_page()
    try:
        await login(page, w["emails"]["main"])
        await shot(
            page,
            "70-dt-bang-tin.png",
            "Điện thoại — bảng tin",
            "Giao diện",
            "Dưới 1024px hai cột bên thu lại, thanh điều hướng chuyển xuống mép dưới.",
        )

        try:
            await page.get_by_role("button", name=tr("nav", "more"), exact=True).click()
            await shot(
                page,
                "71-dt-menu.png",
                "Điện thoại — menu",
                "Giao diện",
                "Thanh dưới chỉ chứa 4 mục hay dùng; phần còn lại nằm trong ngăn kéo “Thêm”.",
                wait=1000,
            )
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(600)
        except Exception as err:
            print(f"[warn] không mở được ngăn kéo trên điện thoại: {err}")

        await goto(page, "/recruitment")
        await shot(
            page,
            "72-dt-tin-tuyen-dung.png",
            "Điện thoại — tin tuyển dụng",
            "Giao diện",
            "Bộ lọc xếp dọc thành khối gập được thay vì cột dính bên phải.",
        )

        await goto(page, "/match")
        await wait_for_advice(page)
        await shot(
            page,
            "73-dt-cong-ty-phu-hop.png",
            "Điện thoại — công ty phù hợp",
            "Giao diện",
            "Thẻ điểm phù hợp giữ nguyên vòng cung, chỉ đổi cách xếp khối.",
        )
    finally:
        await ctx.close()


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mongo = AsyncMongoClient(MONGO_URL)
    db = mongo[MONGO_URL.rsplit("/", 1)[-1]]
    try:
        async with httpx.AsyncClient(base_url=API_URL, timeout=60) as api:
            world = await seed(api, db)
    finally:
        await mongo.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            await capture_auth(browser)
            await capture_main(browser, world)
            await capture_admin(browser, world)
            await capture_mobile(browser, world)
        finally:
            await browser.close()

    (OUT / "manifest.json").write_text(json.dumps(SHOTS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nXong: {len(SHOTS)} ảnh trong {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
