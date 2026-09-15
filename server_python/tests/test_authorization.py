"""Ma trận phân quyền: ai được làm gì với tài nguyên của ai.

Vì sao tách thành một file riêng
--------------------------------
Các file test khác kiểm *chức năng chạy đúng không*. File này kiểm *chức năng
có từ chối đúng người không* — một câu hỏi khác hẳn, và là câu hỏi mà 386 test
trước đây bỏ sót gần hết. Bốn lỗ hổng nghiêm trọng từng tồn tại cùng lúc trong
dự án đều thuộc loại "quên một dòng kiểm tra":

* đọc được tin nhắn riêng của hai người lạ,
* socket không xác thực -> mạo danh người khác gửi tin,
* trang cá nhân (kèm email) đọc được khi chưa đăng nhập,
* đăng bài / thích / bình luận vào channel chưa hề tham gia.

Cách viết ở đây cố ý **lặp lại theo khuôn**: mỗi test nêu đúng một câu
"X KHÔNG được làm Y với tài nguyên của Z", và khẳng định cả **mã HTTP** lẫn
**tác dụng phụ trong DB** (từ chối mà vẫn ghi được dữ liệu thì vẫn là hỏng).

Quy ước mã trạng thái
---------------------
* **401** — chưa đăng nhập (thiếu token / token hết hạn).
* **403** — đã đăng nhập nhưng không có quyền với tài nguyên này.
* **404** — chỉ dùng khi tài nguyên thật sự không tồn tại, không dùng để giấu
  chuyện thiếu quyền.
"""

import uuid

import pytest
from bson import ObjectId

# --------------------------------------------------------------------------
# Nhóm 1 — Tin nhắn riêng: CHỈ hai người trong hội thoại
# --------------------------------------------------------------------------


@pytest.fixture
async def third_user(client, db):
    """Người thứ ba, hoàn toàn ngoài cuộc hội thoại giữa `user` và `other_user`."""
    from tests.conftest import Actor, _register_and_login, unique_email

    email = unique_email("outsider")
    token = await _register_and_login(client, email)
    doc = await db.users.find_one({"email": email})
    return Actor(email, token, str(doc["_id"]))


@pytest.fixture
async def conversation(db, user, other_user):
    """Một hội thoại có sẵn giữa `user` và `other_user`."""
    secret = f"bi-mat-{uuid.uuid4().hex[:8]}"
    await db.chats.insert_one({"sender": ObjectId(user.id), "receiver": ObjectId(other_user.id), "content": secret})
    return secret


async def test_nguoi_ngoai_khong_doc_duoc_tin_nhan_cua_hai_nguoi_khac(
    client, third_user, user, other_user, conversation
):
    """Đây chính là lỗ hổng đã tái hiện được: chỉ cần biết hai id là đọc trọn hội thoại."""
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=third_user.headers)
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "chat.notYourConversation"
    assert conversation not in r.text


async def test_doi_thu_tu_id_cung_khong_lach_duoc(client, third_user, user, other_user, conversation):
    """Đảo hai id không phải là một hội thoại khác — vẫn phải bị chặn."""
    r = await client.get(f"/api/messages/{other_user.id}/{user.id}", headers=third_user.headers)
    assert r.status_code == 403, r.text


async def test_ghep_id_cua_minh_voi_id_nguoi_la_khong_doc_duoc_hoi_thoai_cua_ho(
    client, third_user, user, other_user, conversation
):
    """Người ngoài tự ghép mình vào một vế cũng chỉ thấy hội thoại của chính mình.

    `third_user` gọi với cặp (mình, other_user) là hợp lệ về mặt quyền, nhưng
    hội thoại đó rỗng — bí mật của hai người kia không được lọt sang.
    """
    r = await client.get(f"/api/messages/{third_user.id}/{other_user.id}", headers=third_user.headers)
    assert r.status_code == 200, r.text
    assert conversation not in r.text


@pytest.mark.parametrize("caller", ["nguoi_gui", "nguoi_nhan"])
async def test_ca_hai_nguoi_trong_hoi_thoai_deu_doc_duoc(client, user, other_user, conversation, caller):
    actor = user if caller == "nguoi_gui" else other_user
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=actor.headers)
    assert r.status_code == 200, r.text
    assert conversation in [m["content"] for m in r.json()["messages"]]


async def test_chua_dang_nhap_thi_khong_doc_duoc_tin_nhan(client, user, other_user):
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}")
    assert r.status_code == 401, r.text


async def test_khong_danh_dau_da_doc_hoi_thoai_cua_nguoi_khac(client, db, user, other_user, third_user):
    """Đánh dấu đã đọc cũng là một hành động trên hội thoại — người ngoài không được làm."""
    doc = await db.newestmessages.insert_one(
        {
            "sender": {"user": ObjectId(user.id), "isRead": True},
            "receiver": {"user": ObjectId(other_user.id), "isRead": False},
            "content": "rieng tu",
        }
    )
    r = await client.put(f"/api/newest_messages/{doc.inserted_id}", headers=third_user.headers)
    assert r.status_code == 404, r.text

    after = await db.newestmessages.find_one({"_id": doc.inserted_id})
    assert after["receiver"]["isRead"] is False, "bị từ chối nhưng vẫn sửa được dữ liệu"


# --------------------------------------------------------------------------
# Nhóm 2 — Mã hoá tin nhắn khi lưu trữ
# --------------------------------------------------------------------------


async def test_noi_dung_tin_nhan_khong_nam_duoi_dang_chu_thuong_trong_db(client, db, user, other_user, socket_of):
    """Đọc thẳng MongoDB không được ra nội dung tin nhắn.

    Bảo vệ trước tình huống mà quyền ở tầng API không đỡ nổi: lộ bản dump DB,
    lộ ổ đĩa, hoặc bất kỳ ai mở Compass lên xem.
    """
    secret = f"noi-dung-rat-rieng-tu-{uuid.uuid4().hex[:8]}"

    async with socket_of(user) as sender:
        await sender.emit("sendMessage", {"receiver": {"_id": other_user.id}, "content": secret})
        await sender.sleep(1.5)

    stored = await db.chats.find_one({"sender": ObjectId(user.id), "receiver": ObjectId(other_user.id)})
    assert stored is not None, "tin nhắn không được lưu"
    assert secret not in stored["content"], "nội dung nằm trong DB dưới dạng chữ thường"
    assert stored["content"].startswith("enc:v1:"), stored["content"][:40]

    newest = await db.newestmessages.find_one({"sender.user": ObjectId(user.id)})
    assert newest is not None and secret not in (newest.get("content") or "")

    # Nhưng đúng hai người trong hội thoại vẫn đọc ra bản rõ qua API.
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert secret in [m["content"] for m in r.json()["messages"]]


async def test_tin_nhan_cu_chua_ma_hoa_van_doc_duoc(client, db, user, other_user):
    """Tương thích ngược: lịch sử lưu trước khi có mã hoá không được biến mất."""
    legacy = f"tin-cu-{uuid.uuid4().hex[:8]}"
    await db.chats.insert_one({"sender": ObjectId(user.id), "receiver": ObjectId(other_user.id), "content": legacy})
    r = await client.get(f"/api/messages/{user.id}/{other_user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert legacy in [m["content"] for m in r.json()["messages"]]


# --------------------------------------------------------------------------
# Nhóm 3 — Socket: danh tính lấy từ token, không lấy từ payload
# --------------------------------------------------------------------------


async def test_socket_tu_choi_ket_noi_khong_co_token(socket_connect_raw):
    ok, error = await socket_connect_raw(None)
    assert ok is False, "socket vẫn cho kết nối ẩn danh"
    assert error


async def test_socket_tu_choi_token_bia(socket_connect_raw):
    ok, _ = await socket_connect_raw("day.khong.phai.token")
    assert ok is False


async def test_khong_mao_danh_duoc_nguoi_khac_de_gui_tin(db, user, other_user, third_user, socket_of):
    """`third_user` khai `sender` là `user`, máy chủ phải ghi đè bằng danh tính thật.

    Trước khi sửa, đây là đường mạo danh hoàn chỉnh — và còn không cần đăng
    nhập.
    """
    content = f"mao-danh-{uuid.uuid4().hex[:8]}"

    async with socket_of(third_user) as attacker:
        await attacker.emit(
            "sendMessage",
            {
                "sender": {"_id": user.id},  # nói dối
                "receiver": {"_id": other_user.id},
                "content": content,
                "lastSent": {"_id": user.id},
            },
        )
        await attacker.sleep(1.5)

    forged = await db.chats.find_one({"content": {"$regex": content}, "sender": ObjectId(user.id)})
    assert forged is None, "ghi được tin nhắn dưới tên người khác"

    real = await db.chats.find_one({"sender": ObjectId(third_user.id), "receiver": ObjectId(other_user.id)})
    assert real is not None, "tin vẫn phải được gửi, nhưng dưới danh tính THẬT của người gửi"


async def test_khong_cuop_duoc_duong_nhan_tin_cua_nguoi_khac(db, user, third_user, socket_of):
    """`joinChat` bỏ qua payload, nên không gán được `socketId` của người khác về mình."""
    before = await db.users.find_one({"_id": ObjectId(user.id)})

    async with socket_of(third_user) as attacker:
        await attacker.emit("joinChat", {"_id": user.id})  # nói dối
        await attacker.sleep(1.0)

        after = await db.users.find_one({"_id": ObjectId(user.id)})
        assert after.get("socketId") == before.get("socketId"), "socketId của nạn nhân bị trỏ sang kẻ tấn công"

        attacker_doc = await db.users.find_one({"_id": ObjectId(third_user.id)})
        assert attacker_doc.get("socketId") is not None, "joinChat phải gán socket cho CHÍNH người gọi"


# --------------------------------------------------------------------------
# Nhóm 4 — Hồ sơ người dùng
# --------------------------------------------------------------------------


async def test_trang_ca_nhan_khong_xem_duoc_khi_chua_dang_nhap(client, user):
    r = await client.get(f"/api/users/{user.id}")
    assert r.status_code == 401, r.text


async def test_email_nguoi_khac_khong_bi_lo_qua_trang_ca_nhan(client, user, other_user):
    r = await client.get(f"/api/users/{other_user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert "email" not in r.json()["user"], "email của người khác vẫn bị trả về"
    assert other_user.email not in r.text


async def test_xem_trang_cua_chinh_minh_thi_van_thay_email(client, user):
    r = await client.get(f"/api/users/{user.id}", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["user"]["email"] == user.email


async def test_khong_sua_duoc_ho_so_cua_nguoi_khac(client, db, user, other_user):
    r = await client.put(f"/api/users/{other_user.id}", headers=user.headers, data={"username": "bi-chiem"})
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "user.cannotEditOthers"

    victim = await db.users.find_one({"_id": ObjectId(other_user.id)})
    assert victim["username"] != "bi-chiem"


async def test_doi_mat_khau_phai_co_mat_khau_cu_dung(client, user):
    r = await client.put(
        f"/api/users/{user.id}",
        headers=user.headers,
        data={"oldPassword": "sai-hoan-toan", "newPassword": "MatKhauMoi@123"},
    )
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "user.wrongOldPassword"

    # Mật khẩu cũ vẫn phải dùng được: từ chối mà vẫn đổi thì còn tệ hơn.
    r = await client.post("/api/users/login", json={"email": user.email, "password": "Passw0rd!"})
    assert r.status_code == 200, r.text


# --------------------------------------------------------------------------
# Nhóm 5 — Channel: chưa tham gia thì không đọc, không ghi
# --------------------------------------------------------------------------


async def test_chua_tham_gia_thi_khong_dang_bai_duoc(client, db, user, channel):
    r = await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": "bai chui"})
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "channel.notJoined"

    assert await db.posts.count_documents({"channel": ObjectId(channel["_id"]), "content": "bai chui"}) == 0


async def test_chua_tham_gia_thi_khong_doc_duoc_bai_trong_channel(client, user, channel):
    r = await client.get(f"/api/posts/{channel['_id']}", headers=user.headers)
    assert r.status_code == 403, r.text


async def test_chua_tham_gia_thi_khong_thich_duoc_bai(client, db, user, other_user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=other_user.headers)
    r = await client.post(
        f"/api/posts/{channel['_id']}", headers=other_user.headers, data={"content": "cua thanh vien"}
    )
    assert r.status_code == 201, r.text
    post = await db.posts.find_one({"channel": ObjectId(channel["_id"]), "content": "cua thanh vien"})

    r = await client.post(f"/api/posts/{channel['_id']}/{post['_id']}/like_post", headers=user.headers)
    assert r.status_code == 403, r.text

    after = await db.posts.find_one({"_id": post["_id"]})
    assert ObjectId(user.id) not in (after.get("liked") or [])


async def test_chua_tham_gia_thi_khong_binh_luan_duoc(client, db, user, other_user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=other_user.headers)
    await client.post(f"/api/posts/{channel['_id']}", headers=other_user.headers, data={"content": "cho binh luan"})
    post = await db.posts.find_one({"channel": ObjectId(channel["_id"]), "content": "cho binh luan"})

    r = await client.post(
        f"/api/posts/{channel['_id']}/{post['_id']}/comments",
        headers=user.headers,
        json={"content": "chen ngang"},
    )
    assert r.status_code == 403, r.text

    after = await db.posts.find_one({"_id": post["_id"]})
    assert not (after.get("comments") or [])


async def test_roi_channel_thi_mat_quyen_ghi(client, user, channel):
    """Quyền phải được kiểm ở THỜI ĐIỂM ghi, không phải một lần lúc tham gia."""
    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    r = await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": "con la thanh vien"})
    assert r.status_code == 201, r.text

    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)  # rời
    assert r.status_code == 200, r.text

    r = await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": "da roi"})
    assert r.status_code == 403, r.text


# --------------------------------------------------------------------------
# Nhóm 6 — Quyền quản trị
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("post", "/api/channels", {"data": {"name": "chan-trom", "intro": "x"}}),
        ("get", "/api/posts/get_by_admin", {}),
        ("get", "/api/get_users_by_admin", {}),
    ],
)
async def test_nguoi_thuong_khong_dung_duoc_chuc_nang_quan_tri(client, user, method, path, payload):
    r = await getattr(client, method)(path, headers=user.headers, **payload)
    assert r.status_code == 403, f"{method.upper()} {path} -> {r.status_code}"


async def test_nguoi_thuong_khong_xoa_duoc_bai_bang_duong_cua_admin(client, db, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    await client.post(f"/api/posts/{channel['_id']}", headers=user.headers, data={"content": "bai cua toi"})
    post = await db.posts.find_one({"channel": ObjectId(channel["_id"]), "content": "bai cua toi"})

    r = await client.delete(f"/api/delete_post_by_admin/{channel['_id']}/{post['_id']}", headers=user.headers)
    assert r.status_code == 403, r.text
    assert await db.posts.find_one({"_id": post["_id"]}) is not None


async def test_khong_xoa_duoc_bai_viet_cua_nguoi_khac(client, db, user, other_user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    await client.post(f"/api/channels/{channel['_id']}", headers=other_user.headers)
    await client.post(
        f"/api/posts/{channel['_id']}", headers=other_user.headers, data={"content": "khong phai cua ban"}
    )
    post = await db.posts.find_one({"channel": ObjectId(channel["_id"]), "content": "khong phai cua ban"})

    r = await client.delete(f"/api/posts/{channel['_id']}/{post['_id']}", headers=user.headers)
    assert r.status_code == 403, r.text
    assert await db.posts.find_one({"_id": post["_id"]}) is not None


# --------------------------------------------------------------------------
# Nhóm 7 — CV: dữ liệu cá nhân nhất trong toàn hệ thống
# --------------------------------------------------------------------------


async def test_cv_chi_chu_nhan_doc_duoc(client, user_with_resume, other_user):
    """Không có endpoint nào đọc CV theo id — `/api/resume` luôn trả CV của CHÍNH người gọi."""
    r = await client.get("/api/resume", headers=other_user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["resume"] is None, "CV của người khác lọt ra"

    r = await client.get("/api/resume", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    assert r.json()["resume"]["name"] == "Nguyen Van A"


async def test_cv_khong_doc_duoc_khi_chua_dang_nhap(client):
    r = await client.get("/api/resume")
    assert r.status_code == 401, r.text
