"""Những lỗi "mất dữ liệu âm thầm" — chạy vẫn ra 200, chỉ là dữ liệu biến mất.

Loại lỗi này không bao giờ hiện lên thành sự cố: không có exception, không có
log, toast vẫn báo thành công. Nó chỉ lộ ra khi có người mở lại và thấy ô mình
từng điền giờ trống trơn — lúc đó thì không còn gì để khôi phục.

Điểm chung của cả nhóm: **client hiện tại luôn gửi đủ trường nên chưa ai gặp**.
Đó là may mắn, không phải thiết kế — thêm một client khác, hay một lần sửa giao
diện quên đính một ô, là bung ngay. Nên chỗ canh phải là test, không phải giao
diện.
"""

import uuid

import pytest
from bson import ObjectId

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


# --------------------------------------------------------------------------
# CV: lưu lần đầu kèm file
# --------------------------------------------------------------------------


async def test_luu_cv_lan_dau_kem_anh_va_chung_chi_khong_mat_file(client, db, user):
    """Người dùng mới điền CV kèm ảnh + chứng chỉ ngay lần đầu.

    Bản cũ đặt đoạn xử lý file SAU một `return` sớm của nhánh tạo mới: file đã
    ghi xuống đĩa nhưng không được gắn vào CV. Phải bấm lưu lần thứ hai mới ăn —
    và người dùng thì không có lý do gì để bấm lại.
    """
    r = await client.post(
        "/api/resume",
        headers=user.headers,
        data={
            "name": "Nguyen Van B",
            "position": "Backend Engineer",
            "certificatesName": '["JLPT N2"]',
        },
        files=[
            ("avatar", ("me.png", PNG, "image/png")),
            ("certificates", ("n2.pdf", PDF, "application/pdf")),
        ],
    )
    assert r.status_code == 200, r.text

    saved = await db.resumes.find_one({"user": ObjectId(user.id)})
    assert saved is not None, "CV không được lưu"
    assert saved.get("avatar", {}).get("url"), "ảnh đại diện CV bị mất ở lần lưu đầu tiên"
    certificates = saved.get("certificates") or []
    assert certificates, "chứng chỉ bị mất ở lần lưu đầu tiên"
    assert certificates[0]["name"] == "JLPT N2"


# --------------------------------------------------------------------------
# Cập nhật một phần: gửi thiếu trường thì KHÔNG được xoá trắng trường đó
# --------------------------------------------------------------------------


async def test_sua_channel_thieu_truong_khong_xoa_ten_channel(client, db, admin, channel):
    """Đổi mỗi phần giới thiệu thì tên channel phải còn nguyên."""
    r = await client.put(f"/api/channels/{channel['_id']}", headers=admin.headers, data={"intro": "gioi thieu moi"})
    assert r.status_code == 200, r.text

    saved = await db.channels.find_one({"_id": ObjectId(channel["_id"])})
    assert saved["name"] == channel["name"], "tên channel bị xoá khi cập nhật một phần"
    assert saved["intro"] == "gioi thieu moi"


async def test_sua_channel_gui_chuoi_rong_van_xoa_duoc_gioi_thieu(client, db, admin, channel):
    """Gửi rỗng KHÁC với không gửi — admin vẫn phải xoá sạch được phần giới thiệu."""
    r = await client.put(f"/api/channels/{channel['_id']}", headers=admin.headers, data={"intro": ""})
    assert r.status_code == 200, r.text
    saved = await db.channels.find_one({"_id": ObjectId(channel["_id"])})
    assert saved["intro"] == ""
    assert saved["name"] == channel["name"]


async def test_sua_bai_viet_thieu_content_khong_xoa_trang_bai(client, db, user, channel):
    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    marker = f"noi-dung-{uuid.uuid4().hex[:8]}"
    await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": marker})
    post = await db.posts.find_one({"content": {"$regex": marker}})

    # Request chỉ đính ảnh, không gửi `content` — giống một client chỉ muốn đổi ảnh.
    r = await client.put(
        f"/api/posts/{channel['_id']}/{post['_id']}",
        headers=user.headers,
        files={"images": ("new.png", PNG, "image/png")},
    )
    assert r.status_code == 200, r.text

    after = await db.posts.find_one({"_id": post["_id"]})
    assert after["content"] == marker, "nội dung bài viết bị xoá khi chỉ cập nhật ảnh"
    assert after.get("images", {}).get("url")


async def test_sua_website_thieu_truong_khong_xoa_ten_website(client, db, admin):
    web = await db.webs.find_one({})
    if not web:
        pytest.skip("DB chưa seed bảng website")
    goc = web.get("website_name")

    r = await client.put(f"/api/website/{web['_id']}", headers=admin.headers, data={"color_title": "#123456"})
    assert r.status_code == 200, r.text

    saved = await db.webs.find_one({"_id": web["_id"]})
    assert saved["website_name"] == goc, "tên website bị xoá khi chỉ đổi màu"
    assert saved["color_title"] == "#123456"

    await db.webs.update_one({"_id": web["_id"]}, {"$set": {"color_title": web.get("color_title")}})


# --------------------------------------------------------------------------
# Dọn dẹp theo dây chuyền
# --------------------------------------------------------------------------


async def test_xoa_channel_go_loi_tat_cua_MOI_nguoi(client, db, admin, user, other_user, channel):
    """`find_one` chỉ chạm một bản ghi: 30 người ghim thì 29 người còn lối tắt chết."""
    for actor in (user, other_user):
        assert (await client.post(f"/api/channels/{channel['_id']}", headers=actor.headers)).status_code == 200
        assert (await client.put(f"/api/shortcuts/{channel['_id']}", headers=actor.headers)).status_code == 200

    assert await db.shortcuts.count_documents({"channel": ObjectId(channel["_id"]), "isJoin": True}) >= 2

    r = await client.delete(f"/api/channels/{channel['_id']}", headers=admin.headers)
    assert r.status_code == 200, r.text

    con_lai = await db.shortcuts.count_documents({"channel": ObjectId(channel["_id"]), "isJoin": True})
    assert con_lai == 0, f"còn {con_lai} lối tắt trỏ vào channel đã xoá"


# --------------------------------------------------------------------------
# Follow
# --------------------------------------------------------------------------


async def test_follow_van_chay_khi_tai_khoan_chua_co_ban_ghi_khoi_tao(client, db, user, other_user):
    """Beanie không tự upsert: thiếu bản ghi `Following` thì follow hỏng ÂM THẦM.

    Mô phỏng tài khoản tạo bằng script seed / nhập tay — không đi qua
    `register_user` nên không có sẵn hai bản ghi đó.
    """
    await db.followings.delete_many({"user": ObjectId(user.id)})
    await db.followers.delete_many({"user": ObjectId(other_user.id)})

    r = await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["code"] == "follow.followed"

    doc = await db.followings.find_one({"user": ObjectId(user.id)})
    assert doc is not None and ObjectId(other_user.id) in doc["following"], "báo thành công nhưng không ghi gì"

    doc = await db.followers.find_one({"user": ObjectId(other_user.id)})
    assert doc is not None and ObjectId(user.id) in doc["followers"]


async def test_duoc_follow_thi_co_thong_bao(client, db, user, other_user):
    """README hứa "thích, bình luận, follow -> chuông thông báo"; follow từng bị bỏ quên."""
    r = await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    assert r.status_code == 200, r.text

    r = await client.get("/api/notifications", headers=other_user.headers)
    assert r.status_code == 200, r.text
    codes = [n["code"] for n in r.json()["notifications"]]
    assert "notification.userFollowed" in codes, codes


async def test_bo_follow_khong_sinh_them_thong_bao(client, user, other_user):
    """Follow rồi bỏ rồi follow lại không được làm ngập chuông của người kia."""
    await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)
    await client.post(f"/api/users/{other_user.id}/following", headers=user.headers)  # bỏ follow

    r = await client.get("/api/notifications", headers=other_user.headers)
    so_luong = [n["code"] for n in r.json()["notifications"]].count("notification.userFollowed")
    assert so_luong == 1, f"bỏ follow cũng sinh thông báo: {so_luong}"


# --------------------------------------------------------------------------
# Lối tắt
# --------------------------------------------------------------------------


async def test_loi_tat_sap_xep_channel_vao_nhieu_nhat_len_dau(client, db, user, admin):
    """Bản cũ sort tăng dần nên channel ÍT vào nhất được ghim lên trên."""
    ten_channels = []
    for _ in range(2):
        name = f"channel-{uuid.uuid4().hex[:8]}"
        r = await client.post("/api/channels", headers=admin.headers, data={"name": name, "intro": "x"})
        assert r.status_code == 201, r.text
        ten_channels.append(name)

    r = await client.get("/api/channels", params={"search": ten_channels[0][:8]})
    ids = {}
    for name in ten_channels:
        r = await client.get("/api/channels", params={"search": name})
        ids[name] = next(c for c in r.json()["channels"] if c["name"] == name)["_id"]

    it_vao, hay_vao = ten_channels
    for name in ten_channels:
        await client.post(f"/api/channels/{ids[name]}", headers=user.headers)

    await client.put(f"/api/shortcuts/{ids[it_vao]}", headers=user.headers)
    for _ in range(5):
        await client.put(f"/api/shortcuts/{ids[hay_vao]}", headers=user.headers)

    r = await client.get("/api/shortcuts", headers=user.headers)
    assert r.status_code == 200, r.text
    thu_tu = [s["channel"]["_id"] for s in r.json()["shortcuts"] if s.get("channel")]
    assert thu_tu.index(ids[hay_vao]) < thu_tu.index(ids[it_vao]), "channel hay vào không được xếp lên đầu"


# --------------------------------------------------------------------------
# Upload: nội dung thật, không chỉ phần mở rộng
# --------------------------------------------------------------------------


async def test_file_doi_duoi_thanh_png_bi_tu_choi(client, user):
    """`.png` là do người gửi đặt tên, không phải do nội dung quyết định."""
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"update_images": "avatar"},
        files={"images": ("payload.png", b"<html><script>alert(1)</script></html>", "image/png")},
    )
    assert r.status_code == 400, r.text
    assert r.json()["code"] == "upload.contentMismatch"


async def test_anh_that_van_upload_binh_thuong(client, db, user):
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"update_images": "avatar"},
        files={"images": ("that.png", PNG, "image/png")},
    )
    assert r.status_code == 200, r.text
    saved = await db.users.find_one({"_id": ObjectId(user.id)})
    assert saved["avatar"]["url"].endswith(".png")


async def test_sua_ho_so_nguoi_khac_bi_chan_ngay_ca_khi_kem_file(client, other_user, user):
    """Kèm file cũng không lách được chốt quyền sở hữu.

    Quyền được kiểm bằng dependency `require_self` khai TRƯỚC
    `save_uploaded_files`, nên request bị chặn trước khi có file nào kịp ghi
    xuống đĩa (bản cũ kiểm trong controller, tức là sau khi đã ghi xong).
    Test này khẳng định phần quan sát được từ ngoài — trạng thái đĩa của
    container `server` không nhìn thấy được từ container test.
    """
    r = await client.put(
        f"/api/users/{other_user.id}",
        headers=user.headers,
        data={"update_images": "avatar"},
        files={"images": ("kem-anh.png", PNG, "image/png")},
    )
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "user.cannotEditOthers"
