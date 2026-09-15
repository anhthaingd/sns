# 14. Vá lỗi và bộ test phân quyền (14/09/2026)

> Tiếp nối [tài liệu 13](13-ra-soat-loi-an.md). Bài đó **tìm ra** lỗi; bài này
> ghi lại việc **sửa** chúng, và quan trọng hơn: bộ test được viết thêm để cùng
> một loại lỗi không quay lại lần nữa.

## 14.1. Kết quả đo được

| | Trước | Sau |
|---|---|---|
| Test API | 386 | **447** |
| Test E2E (giao diện thật) | 18 | **20** |
| File test riêng cho bảo mật / phân quyền | 0 | **3** |
| Lỗi còn lại từ tài liệu 13 | 14 | **0** |

Lệnh kiểm lại toàn bộ:

```bash
docker compose up -d
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm api-tests
#   -> 447 passed, 6 skipped

docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm e2e-tests
docker compose up -d client        # tra client ve cau hinh thuong
#   -> 20 passed

cd client && npm run lint          # 0 error, 587 khoa dich khop nhau
docker run --rm -v "$PWD":/w -w /w ghcr.io/astral-sh/ruff:0.15.1 \
  check server_python/app server_python/scripts server_python/tests embedder e2e \
  --config server_python/pyproject.toml
```

## 14.2. Tin nhắn: mã hoá khi lưu, và chỉ hai người xem được

Đây là phần được yêu cầu rõ, nên tách riêng và nói cho hết cả phần **không**
làm được.

### 14.2.1. Hai lớp khác nhau, giải quyết hai chuyện khác nhau

| Lớp | Chống được gì | Nằm ở đâu |
|---|---|---|
| **Phân quyền** | Người dùng khác gọi API để đọc trộm | `app/controllers/chat.py`, `app/sockets/handlers.py` |
| **Mã hoá khi lưu** | Lộ bản dump DB, lộ ổ đĩa, ai đó mở Compass lên xem | `app/services/crypto.py` |

Chỉ có lớp thứ nhất thì một bản backup rò rỉ là mất sạch. Chỉ có lớp thứ hai
thì người dùng A vẫn gọi API đọc được tin của B và C — vì chính máy chủ giải mã
hộ. Phải có cả hai.

### 14.2.2. Phân quyền — "chỉ hai người mới xem được"

Lỗi cũ nằm gọn trong một dòng:

```python
# app/routes/chat.py — BẢN CŨ
async def route_get_chat(sender_id, receiver_id, page, decoded=Depends(get_current_user)):
    return await get_chat(sender_id, receiver_id, page or 1)   # `decoded` khong duoc dung
```

Route có nhận danh tính người gọi, nhưng không truyền xuống, nên không ai kiểm.
Bất kỳ ai đã đăng nhập chỉ cần biết hai id là đọc trọn hội thoại — mà id thì
hiện công khai ngay trên URL trang cá nhân.

Bây giờ có một chốt chặn duy nhất, dùng chung:

```python
# app/controllers/chat.py
def ensure_participant(decoded_user, *participant_ids) -> str:
    me = str(decoded_user.get("_id") or "")
    if me not in {str(pid) for pid in participant_ids}:
        raise ApiError(403, code="chat.notYourConversation")
    return me
```

403 chứ không phải 404: người gọi **đã** đăng nhập hợp lệ, chỉ là không có
quyền. Trả 404 là nói dối rằng hội thoại không tồn tại.

### 14.2.3. Mã hoá — AES-256-GCM, trước khi ghi xuống Mongo

Dạng lưu trong DB:

```
enc:v1:<base64( nonce(12 byte) || ciphertext || tag(16 byte) )>
```

Kiểm chứng thật, gửi một tin qua giao diện rồi đọc thẳng MongoDB:

```
trong DB : enc:v1:QSXqj1sYzxIxxySF76SOVyZ4KcA3iGsTYtsM2Cn1e3gnNoscAAX4CiFF+euswrcctY+osMIXgqKEJ39/Dg==
qua API  : tin-nhan-kiem-chung-1789357803177
```

Ba chi tiết đáng nói:

- **GCM chứ không chỉ AES.** GCM vừa giấu nội dung vừa phát hiện nếu ai đó sửa
  bản mã trong DB. Mã hoá mà không xác thực thì sửa được bản mã một cách có
  chủ đích.
- **Mỗi tin một `nonce` riêng.** Dùng lại nonce với cùng một khoá là phá vỡ
  hoàn toàn GCM, nên đây không phải chi tiết làm cho đẹp.
- **Tiền tố `enc:v1:`.** Tin nhắn cũ (chữ thường, không có tiền tố) vẫn đọc
  được bình thường — không cần migration, và đổi thuật toán sau này thì thêm
  `enc:v2:` mà không phải đoán định dạng.

Khoá lấy từ `MESSAGE_ENCRYPTION_KEY`; để trống thì dẫn xuất từ
`ACCESS_TOKEN_SECRET` để dev chạy được ngay. **Đổi hoặc mất khoá = không đọc
lại được toàn bộ tin nhắn cũ** — đã ghi cảnh báo này ở `.env.example` và README.

### 14.2.4. Cái này KHÔNG phải end-to-end encryption

Nói thẳng để không ai hiểu nhầm: máy chủ giữ khoá, nên máy chủ vẫn đọc được nội
dung khi xử lý request. Bắt buộc phải thế, vì chính máy chủ là bên chuyển tiếp
tin qua socket và dựng dòng xem trước trong danh sách hội thoại.

- **Có** chống: lộ bản dump DB, lộ ổ đĩa, người đọc được DB nhưng không đọc
  được biến môi trường của tiến trình.
- **Không** chống: máy chủ bị chiếm quyền hoàn toàn (kẻ tấn công lấy luôn khoá).

Muốn chống cả trường hợp sau thì phải làm E2EE: khoá sinh và giữ trong trình
duyệt, máy chủ chỉ thấy bản mã. Đổi lại, máy chủ mất khả năng hiển thị dòng xem
trước và không tìm kiếm được trong tin nhắn. Đó là một quyết định sản phẩm,
không phải một dòng code, nên để nguyên ở đây và ghi rõ ranh giới.

### 14.2.5. Socket: danh tính lấy từ token, không lấy từ payload

Bản cũ không xác thực gì cả. Ba nguyên tắc bây giờ:

1. **Kết nối phải mang access token** — `connect` bị từ chối trước khi handler
   nào kịp chạy.
2. **`sid → user_id` giữ ở phía máy chủ.** `sender._id` client gửi lên bị ghi
   đè, `lastSent` bị bỏ qua.
3. **Nội dung mã hoá trước khi ghi**, bản rõ chỉ gửi cho đúng hai người.

Chạy lại đúng lệnh khai thác cũ:

```bash
SID=$(curl -s "http://localhost:3000/socket.io/?EIO=4&transport=polling" | ...)
curl -X POST ".../socket.io/?...&sid=$SID" -d '40'
# -> 44{"message":"Ket noi thoi gian thuc can dang nhap"}
curl -X POST ".../socket.io/?...&sid=$SID" -d '42["sendMessage",{...}]'
# so tin gia mao ghi duoc: 0
```

Phía client, `auth` là **hàm** chứ không phải object:

```js
export const socket = io(import.meta.env.VITE_BACKEND_URL, {
  autoConnect: false,
  auth: (cb) => cb({ token: getAccessToken() || '' }),
});
```

socket.io gọi lại hàm đó ở mỗi lần kết nối, nên access token gia hạn 15 phút
một lần vẫn đi kèm đúng token mới.

> **Một lỗi phát sinh trong chính lần sửa này, và cách nó bị bắt.** Bản sửa đầu
> tiên chỉ nối socket khi chưa có kết nối. Nhưng `auth` chỉ được đánh giá lúc
> bắt tay, nên đăng xuất rồi đăng nhập bằng tài khoản khác trong cùng một tab
> sẽ dùng lại socket đang mang danh tính người cũ — `joinChat` gán socket cho
> nhầm người. Bộ E2E đỏ ngay ở `test_client_connects_to_socketio_and_receives_new_message`.
> Cách sửa: đổi danh tính thì **bắt buộc ngắt rồi nối lại**.

## 14.3. Bộ test phân quyền

Ba file mới. Điểm chung: mỗi test nêu **đúng một câu** "X không được làm Y với
tài nguyên của Z", và khẳng định **cả mã HTTP lẫn tác dụng phụ trong DB** — từ
chối mà vẫn ghi được dữ liệu thì vẫn là hỏng.

### `tests/test_authorization.py` — 30 test, 7 nhóm

| Nhóm | Câu hỏi được trả lời |
|---|---|
| 1. Tin nhắn riêng | Người ngoài đọc được không? Đảo thứ tự id có lách được không? Cả hai người trong hội thoại đọc được chứ? |
| 2. Mã hoá | Đọc thẳng MongoDB có ra nội dung không? Tin nhắn cũ chưa mã hoá còn đọc được không? |
| 3. Socket | Kết nối không token có bị chặn? Khai `sender` là người khác thì sao? Cướp được `socketId` của người khác không? |
| 4. Hồ sơ | Chưa đăng nhập xem được không? Email người khác có lộ? Sửa hồ sơ người khác? Đổi mật khẩu sai mật khẩu cũ? |
| 5. Channel | Chưa tham gia thì đọc/đăng/thích/bình luận được không? **Rời channel rồi thì sao?** |
| 6. Quản trị | Người thường gọi được endpoint admin không? Xoá được bài người khác không? |
| 7. CV | CV của người khác có lọt ra không? |

Quy ước mã trạng thái được ghi ngay đầu file: **401** = chưa đăng nhập,
**403** = đã đăng nhập nhưng không có quyền, **404** = tài nguyên thật sự không
tồn tại (không dùng 404 để giấu chuyện thiếu quyền).

Một test đáng chú ý hơn cả — quyền phải được kiểm ở **thời điểm ghi**, không
phải một lần lúc tham gia:

```python
async def test_roi_channel_thi_mat_quyen_ghi(client, user, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)   # tham gia
    r = await client.post(f"/api/posts/{channel['_id']}", ...)                   # 201
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)   # roi
    r = await client.post(f"/api/posts/{channel['_id']}", ...)
    assert r.status_code == 403
```

Và một test cố tình khẳng định **điều không được xảy ra**: người ngoài tự ghép
mình vào một vế của hội thoại thì được 200 (hợp lệ), nhưng bí mật của hai người
kia tuyệt đối không lọt sang.

### `tests/test_xss_sanitize.py` — 16 test

Bảy payload (`<script>`, `onerror`, `<iframe>`, `javascript:`, `svg onload`,
`style=`, `data:text/html`) chạy qua **cả đường tạo lẫn đường sửa** bài viết.
Payload gửi **thẳng qua API**, không qua giao diện — đó chính là đường kẻ tấn
công đi, và cũng là đường mà trình soạn thảo không bảo vệ nổi.

Hai test đi kèm mà thiếu chúng thì bộ test này vô nghĩa:

- **Bài viết cũ trong DB cũng phải được dọn khi đọc.** Dữ liệu bẩn đã nằm sẵn
  trong DB từ trước; không làm sạch ở đường đọc thì phải chạy migration mới an
  toàn — và quên chạy là vẫn dính.
- **Làm sạch quá tay cũng là hỏng.** Một bài viết có in đậm, danh sách, trích
  dẫn, khối mã và liên kết phải giữ nguyên toàn bộ định dạng.

Có một hành vi được ghi lại rõ để lần sau không ai hiểu nhầm:
`<script>alert(1)</script>` còn lại đúng chuỗi chữ `alert(1)`. Bleach bỏ **thẻ**
nhưng giữ phần chữ bên trong. Nó là chữ thường, trình duyệt không chạy, và đó
là kết quả đúng.

### `tests/test_data_integrity.py` — 15 test

Nhóm lỗi "chạy vẫn ra 200, chỉ là dữ liệu biến mất": không exception, không log,
toast vẫn báo thành công. Nó chỉ lộ ra khi có người mở lại và thấy ô mình từng
điền giờ trống trơn — lúc đó thì không còn gì để khôi phục.

Điểm chung của cả nhóm: **client hiện tại luôn gửi đủ trường nên chưa ai gặp**.
Đó là may mắn, không phải thiết kế. Nên chỗ canh phải là test, không phải giao
diện.

### E2E: hai test cho luồng sửa hồ sơ

Bộ E2E cũ **không có test nào đi qua màn hình sửa hồ sơ** — đúng chỗ ba lỗi ở
tài liệu 13 nằm. Hai test mới canh cả ba cùng lúc: gọi đúng địa chỉ (không có
`undefined` trong URL), dữ liệu được lưu, modal đóng, giá trị mới hiện trên
trang, và đổi mật khẩu xong thì đăng nhập được bằng mật khẩu mới còn mật khẩu cũ
bị từ chối.

## 14.4. Toàn bộ thay đổi

### Bảo mật

| # | Lỗi | Cách sửa |
|---|---|---|
| A1 | Đọc được tin nhắn riêng của người lạ | `ensure_participant` ở `chat.py`; route truyền `decoded` xuống |
| A2 | Socket không xác thực, mạo danh được | Bắt buộc token ở `connect`; `sid → user_id` giữ ở máy chủ; bỏ qua mọi id client khai |
| A3 | XSS lưu trữ trong bài viết | `app/utils/sanitize.py` (bleach, danh sách thẻ hẹp đúng bằng nút của Quill), làm sạch ở **cả** đường ghi lẫn đường đọc |
| A4 | Hồ sơ + email lộ khi chưa đăng nhập | Thêm `Depends(get_current_user)`; email chỉ trả cho chính chủ |
| — | Tin nhắn nằm chữ thường trong DB | AES-256-GCM trước khi ghi (mục 14.2) |
| — | `ACCESS_TOKEN_SECRET` mặc định `"secret"` | Bỏ mặc định — thiếu biến môi trường thì backend **không khởi động**, kèm câu lệnh sinh secret |
| — | Upload chỉ kiểm phần mở rộng | Kiểm "magic bytes": `payload.html` đổi tên thành `.png` bị chặn |
| — | File ghi xuống đĩa trước khi kiểm quyền | Dependency `require_self` khai **trước** `save_uploaded_files` |

### Phân quyền

| # | Lỗi | Cách sửa |
|---|---|---|
| B1 | Đăng bài / thích / bình luận vào channel chưa tham gia | `_require_member` áp cho mọi đường ghi **và** đường đọc nội dung channel |

### Mất dữ liệu

| # | Lỗi | Cách sửa |
|---|---|---|
| C1 | Lưu CV lần đầu mất ảnh và chứng chỉ | Chuyển đoạn xử lý file lên **trước** nhánh `return` sớm |
| C2 | `$set` nguyên khối (channel, web, bài viết) | Dùng `submitted_fields` — chỉ ghi trường request thật sự gửi |
| C3 | Xoá channel còn sót lối tắt của người khác | `find` thay `find_one`; dọn thêm ảnh của mọi bài viết trong channel |
| C4 | Follow không sinh thông báo | Thêm `notification.userFollowed` (3 ngôn ngữ) |
| C5 | Follow hỏng âm thầm nếu thiếu bản ghi | `update_one(..., upsert=True)` |

### Giao diện

| # | Lỗi | Cách sửa |
|---|---|---|
| D1 | Tin nhắn của người khác lạc vào khung chat đang mở | Lọc theo đúng cặp người gửi/người nhận; `key` không còn `undefined` |
| D2 | Xin quyền camera/mic ngay khi đăng nhập | `ensureStream()` chỉ chạy khi khung gọi mở |
| D3 | Người nhận không biết cuộc gọi đã kết thúc | Máy chủ gửi `ended: true`; bỏ `window.location.reload()`, tắt track thật sự |
| D4 | Lối tắt sắp xếp ngược | `.sort("-count")` |

## 14.5. Bài học rút ra

**1. Route nhận `decoded` không có nghĩa là route có kiểm quyền.**
`route_get_chat` nhận đủ danh tính người gọi rồi… không dùng. Nhìn lướt qua chữ
ký hàm thì thấy "có xác thực" — nhưng xác thực (anh là ai) và phân quyền (anh
được làm gì) là hai chuyện khác nhau. Bộ test ở mục 14.3 kiểm chuyện thứ hai.

**2. Vá một nửa còn nguy hiểm hơn không vá.** `get_channel_details` chặn người
chưa tham gia rất đúng, nên nhìn vào đó ai cũng tin là quy tắc đã được áp. Thực
tế mọi đường **ghi** bỏ trống. Quy tắc phân quyền phải đi kèm một hàm dùng
chung (`_require_member`, `ensure_participant`) chứ không phải chép tay ở từng
chỗ — chép tay thì sẽ có chỗ quên.

**3. Tin vào trình soạn thảo là tin nhầm chỗ.** ReactQuill không bao giờ sinh ra
`onerror=`, nhưng API thì nhận tuốt. Chốt chặn phải nằm ở máy chủ, nơi duy nhất
mọi đường ghi đều đi qua.

**4. Test xanh không có nghĩa là không có lỗi — nó chỉ có nghĩa là không có lỗi
*ở chỗ đã viết test*.** 386 test xanh trong khi bốn lỗ hổng nghiêm trọng cùng
tồn tại. Bộ test cũ kiểm rất kỹ *chức năng chạy đúng không*, và gần như không
kiểm *chức năng có từ chối đúng người không*.
