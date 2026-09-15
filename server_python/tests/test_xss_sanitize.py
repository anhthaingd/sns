"""Nội dung bài viết là HTML — và HTML đi thẳng vào `dangerouslySetInnerHTML`.

Bài viết được soạn bằng ReactQuill nên `content` là HTML thật, và
`client/src/components/ui/SinglePost.jsx` render nó bằng
`dangerouslySetInnerHTML`. Trình soạn thảo không bao giờ sinh ra `<script>`,
nhưng **API thì nhận tuốt**: một lệnh `curl` là đủ để nhét mã chạy vào bài
viết, và mã đó sẽ chạy trên phiên đăng nhập của mọi người đọc bài (XSS lưu
trữ — đã tái hiện được trước khi vá).

Nên toàn bộ test ở đây gửi payload **thẳng qua API**, không qua giao diện: đó
chính là đường mà kẻ tấn công đi, và cũng là đường mà trình soạn thảo không
bảo vệ nổi.
"""

import uuid

import pytest
from bson import ObjectId

# Mỗi phần tử: (tên gọi dễ đọc, payload, chuỗi TUYỆT ĐỐI không được còn lại).
XSS_PAYLOADS = [
    ("the script", "<script>alert(1)</script>", "<script"),
    ("thuoc tinh onerror", '<img src=x onerror="alert(1)">', "onerror"),
    ("the iframe", '<iframe src="https://evil.example"></iframe>', "<iframe"),
    ("giao thuc javascript:", '<a href="javascript:alert(1)">bam</a>', "javascript:"),
    ("su kien onload tren svg", "<svg onload=alert(1)></svg>", "onload"),
    ("thuoc tinh style", '<p style="background:url(javascript:alert(1))">x</p>', "style="),
    ("data: chay HTML", '<a href="data:text/html,<script>alert(1)</script>">x</a>', "data:text/html"),
]


@pytest.fixture
async def joined_channel(client, user, channel):
    r = await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    return channel


@pytest.mark.parametrize("ten,payload,cam", XSS_PAYLOADS, ids=[p[0] for p in XSS_PAYLOADS])
async def test_ma_doc_khong_song_sot_khi_luu_bai_viet(client, db, user, joined_channel, ten, payload, cam):
    marker = f"marker-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        f"/api/posts/{joined_channel['_id']}",
        headers=user.headers,
        data={"content": f"{payload}{marker}"},
    )
    assert r.status_code == 201, r.text

    stored = await db.posts.find_one({"content": {"$regex": marker}})
    assert stored is not None, "bài viết không được lưu"
    assert cam.lower() not in stored["content"].lower(), f"{ten}: còn nguyên trong DB -> {stored['content']}"
    assert marker in stored["content"], "phần nội dung lành mạnh của người dùng bị mất"


@pytest.mark.parametrize("ten,payload,cam", XSS_PAYLOADS, ids=[p[0] for p in XSS_PAYLOADS])
async def test_ma_doc_khong_song_sot_khi_sua_bai_viet(client, db, user, joined_channel, ten, payload, cam):
    """Đường SỬA cũng phải làm sạch — vá mỗi đường tạo là để hở đúng một nửa."""
    marker = f"marker-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        f"/api/posts/{joined_channel['_id']}", headers=user.headers, data={"content": f"lanh manh {marker}"}
    )
    assert r.status_code == 201, r.text
    post = await db.posts.find_one({"content": {"$regex": marker}})

    r = await client.put(
        f"/api/posts/{joined_channel['_id']}/{post['_id']}",
        headers=user.headers,
        data={"content": f"{payload}{marker}"},
    )
    assert r.status_code == 200, r.text

    after = await db.posts.find_one({"_id": post["_id"]})
    assert cam.lower() not in after["content"].lower(), f"{ten}: còn nguyên sau khi sửa -> {after['content']}"


async def test_bai_viet_cu_luu_truoc_khi_co_buoc_lam_sach_van_duoc_don_khi_doc(client, db, user, joined_channel):
    """Dữ liệu bẩn có sẵn trong DB không được lọt ra API.

    Bài viết lưu trước khi có bước làm sạch vẫn đang nằm trong DB với HTML thô.
    Không làm sạch ở đường ĐỌC thì phải chạy migration mới an toàn được — và
    quên chạy là vẫn dính.
    """
    marker = f"cu-{uuid.uuid4().hex[:8]}"
    await db.posts.insert_one(
        {
            "user": ObjectId(user.id),
            "channel": ObjectId(joined_channel["_id"]),
            "content": f'<img src=x onerror="alert(1)">{marker}',
            "liked": [],
            "book_marked": [],
            "comments": [],
        }
    )

    r = await client.get(f"/api/posts/{joined_channel['_id']}", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.text
    assert marker in body, "bài viết cũ biến mất khỏi danh sách"
    assert "onerror" not in body.lower()


async def test_dinh_dang_hop_le_cua_trinh_soan_thao_duoc_giu_nguyen(client, db, user, joined_channel):
    """Làm sạch quá tay cũng là hỏng: bài viết bình thường phải giữ nguyên định dạng."""
    marker = f"dinh-dang-{uuid.uuid4().hex[:8]}"
    rich = (
        f'<p class="ql-align-center"><strong>đậm</strong> <em>nghiêng</em> '
        f"<u>gạch chân</u> {marker}</p>"
        f"<ul><li>một</li><li>hai</li></ul>"
        f'<blockquote>trích dẫn</blockquote><pre class="ql-syntax">mã</pre>'
        f'<p><a href="https://example.com">liên kết</a></p>'
    )
    r = await client.post(f"/api/posts/{joined_channel['_id']}", headers=user.headers, data={"content": rich})
    assert r.status_code == 201, r.text

    stored = (await db.posts.find_one({"content": {"$regex": marker}}))["content"]
    for phai_con in (
        "<strong>",
        "<em>",
        "<u>",
        "<ul>",
        "<li>",
        "<blockquote>",
        "<pre",
        "ql-align-center",
        "https://example.com",
    ):
        assert phai_con in stored, f"mất {phai_con!r} -> {stored}"


async def test_bai_viet_chi_gom_ma_doc_bi_tu_choi(client, user, joined_channel):
    """Làm sạch xong mà rỗng thì không còn là bài viết — không được lưu bài trống."""
    r = await client.post(
        f"/api/posts/{joined_channel['_id']}",
        headers=user.headers,
        data={"content": '<iframe src="https://evil.example"></iframe>'},
    )
    assert r.status_code == 400, r.text


async def test_the_script_bien_thanh_chu_thuong_chu_khong_bien_mat(client, db, user, joined_channel):
    """`<script>alert(1)</script>` còn lại đúng chuỗi chữ `alert(1)`.

    Bleach bỏ THẺ nhưng giữ phần chữ bên trong. Ghi rõ hành vi đó ở đây để lần
    sau không ai nhìn thấy `alert(1)` trong DB rồi tưởng bước làm sạch hỏng:
    nó là chữ thường, trình duyệt không chạy, và đó là kết quả đúng.
    """
    marker = f"script-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        f"/api/posts/{joined_channel['_id']}",
        headers=user.headers,
        data={"content": f"<script>alert(1)</script>{marker}"},
    )
    assert r.status_code == 201, r.text

    stored = (await db.posts.find_one({"content": {"$regex": marker}}))["content"]
    assert "<script" not in stored.lower()
    assert stored == f"alert(1){marker}", stored
