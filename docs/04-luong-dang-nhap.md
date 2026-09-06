# 4. Luồng đăng nhập

## 4.1. Vấn đề cần giải

Giao thức web vốn **không có trí nhớ**: mỗi lần trình duyệt hỏi máy chủ là một
cuộc gặp gỡ hoàn toàn mới. Máy chủ không tự biết "à, đây là anh Thái vừa đăng
nhập ban nãy".

Vậy làm sao web nhớ được bạn? Câu trả lời: sau khi đăng nhập, máy chủ phát cho
bạn một **tấm vé**, và bạn phải trình vé đó ở mọi lần gọi tiếp theo.

> 💡 **Token (tấm vé) là gì?** Là một chuỗi ký tự dài do máy chủ ký tên. Nó
> chứa sẵn "bạn là ai" và "vé hết hạn lúc nào". Ai sửa một ký tự trong đó thì
> chữ ký hỏng ngay, máy chủ phát hiện được. Vé **không** phải mật khẩu — nó
> chỉ dùng được trong thời gian ngắn.

## 4.2. Hai tấm vé, hai nhiệm vụ khác nhau

Dự án dùng **hai** loại vé, và lý do rất đáng đọc:

| | Vé ngắn hạn (access token) | Vé dài hạn (refresh token) |
|---|---|---|
| Sống được | **15 phút** | **7 ngày** |
| Cất ở đâu | localStorage của trình duyệt | Cookie mà JavaScript **không đọc được** |
| Gửi kèm khi nào | Mọi lần gọi API | Chỉ khi xin gia hạn |
| Dùng để | Chứng minh danh tính | Xin cấp vé ngắn hạn mới |

**Vì sao phải chia đôi như vậy?**

Nếu chỉ có một vé sống 7 ngày, kẻ trộm lấy được nó là dùng thoải mái suốt tuần.
Nếu chỉ có vé sống 15 phút, cứ 15 phút người dùng lại bị đá ra màn hình đăng
nhập — không ai chịu nổi.

Chia đôi giải quyết cả hai: vé hay bị đem đi khắp nơi thì sống ngắn; vé sống
dài thì cất kỹ trong cookie có cờ `httpOnly` — nghĩa là **mã JavaScript độc
hại chèn vào trang cũng không đọc nổi**.

> 💡 **Cookie là gì?** Là mẩu dữ liệu nhỏ trình duyệt tự động đính kèm mỗi khi
> gọi về đúng máy chủ đã phát nó. Cờ `httpOnly` bảo trình duyệt: "chỉ được gửi
> đi, cấm cho JavaScript đọc". Đây chính là lá chắn cho vé dài hạn.

Cấu hình thật nằm ở `server_python/app/config/settings.py`:

```python
ACCESS_TOKEN_TTL_SECONDS  = 15 * 60            # 15 phút
REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60   # 7 ngày
REFRESH_COOKIE_PATH = "/api/users"             # cookie chỉ gửi tới nhóm địa chỉ này
```

`REFRESH_COOKIE_PATH` là một lớp phòng thủ nữa: cookie dài hạn chỉ được đính
kèm khi gọi các địa chỉ bắt đầu bằng `/api/users`. Gọi `/api/jobs` thì nó nằm
im, không có cơ hội bị lộ.

## 4.3. Toàn cảnh luồng đăng nhập

```
NGƯỜI DÙNG                GIAO DIỆN                    MÁY CHỦ
────────────────────────────────────────────────────────────────────────
Gõ email + mật khẩu
Bấm "Login"
     │
     └──────────▶  LoginLayout.jsx
                   useLoginUserMutation()
                        │
                        └───▶  POST /api/users/login
                               { email, password }
                                     │
                                     ├─ ① Kiểm tra giới hạn số lần thử
                                     ├─ ② Tìm tài khoản theo email
                                     ├─ ③ So khớp mật khẩu (bcrypt)
                                     ├─ ④ Tạo 2 tấm vé
                                     └─ ⑤ Đặt vé dài hạn vào cookie
                                     │
                        ◀────────────┘
                        { accessToken: "eyJhbGci..." }
                        │
                        ├─ Lưu vé ngắn hạn vào localStorage
                        └─ Chuyển sang trang chủ
```

### Bước ① — Chống dò mật khẩu

File `server_python/app/controllers/auth.py`:

```python
await rate_limit.ensure_under_limit(LOGIN_EMAIL_BUCKET, email, LOGIN_FAIL_LIMIT_PER_EMAIL)
await rate_limit.ensure_under_limit(LOGIN_IP_BUCKET, ip, LOGIN_FAIL_LIMIT_PER_IP)
```

Hai tầng chặn, và **chỉ đếm lần THẤT BẠI**:

- **Theo email**: tối đa 10 lần sai trong 15 phút → chặn kẻ thử mật khẩu của
  một tài khoản cụ thể.
- **Theo địa chỉ IP**: tối đa 30 lần sai trong 15 phút → chặn kẻ rải một mật
  khẩu phổ biến qua hàng loạt tài khoản.

Vì chỉ đếm lần sai, người dùng bình thường không bao giờ chạm ngưỡng.

Bộ đếm cất ở **Redis** chứ không phải trong bộ nhớ máy chủ. Lý do: khởi động
lại máy chủ mà bộ đếm về 0 thì kẻ tấn công chỉ cần chờ một lần restart.

### Bước ③ — So khớp mật khẩu, và hai cái bẫy đã bịt

Mật khẩu **không bao giờ** được lưu nguyên văn. Thứ nằm trong kho là kết quả
băm bằng bcrypt — một chiều, không thể lần ngược lại mật khẩu gốc.

Hai chi tiết bảo mật rất dễ bị bỏ qua, dự án này đã xử lý:

**Cái bẫy 1 — thông báo lỗi tiết lộ thông tin.**

```python
# app/messages.py
"auth.invalidCredentials": "Email hoặc mật khẩu không đúng!",

# app/controllers/auth.py — cả email lạ lẫn sai mật khẩu đều ném đúng mã này
raise ApiError(401, code="auth.invalidCredentials")
```

Một thông báo **duy nhất** cho mọi trường hợp. Bản cũ trả *"Tài khoản chưa được
đăng ký!"* khi email lạ và *"Sai mật khẩu!"* khi sai mật khẩu — chỉ cần thử một
lần là biết email nào có thật trong hệ thống.

**Cái bẫy 2 — thời gian phản hồi cũng tiết lộ thông tin.**

```python
# Hash "mồi" để lần đăng nhập với email không tồn tại vẫn tốn đúng chừng ấy
# thời gian như email có thật.
_DUMMY_PASSWORD_HASH = _bcrypt.hashpw(b"fuurin-dummy-password", _bcrypt.gensalt(10))
```

Nếu email không tồn tại và máy chủ trả lời ngay lập tức, còn email có thật thì
mất 100 mili-giây để kiểm mật khẩu — kẻ tấn công bấm đồng hồ là đoán ra. Nên
khi không tìm thấy tài khoản, hệ thống vẫn cố tình đi kiểm với hash mồi cho
tốn đúng chừng ấy thời gian.

### Bước ④ — Trong tấm vé có gì

File `server_python/app/utils/token.py`:

```python
ACCESS_TOKEN_CLAIMS = ("_id", "email", "username", "role")
```

Chỉ đúng 4 thông tin cần cho phân quyền và hiển thị. Bản cũ nhét cả `socketId`,
`address`, `intro`, `avatar`, `cover_bg` vào vé rồi gửi kèm **mọi** request —
vừa nặng đường truyền vừa lộ thông tin không cần thiết.

Mỗi vé còn có `jti` — một mã ngẫu nhiên định danh riêng cho tấm vé đó. Mã này
là chìa khoá cho chức năng đăng xuất, xem mục 4.5.

## 4.4. Vé hết hạn thì sao — gia hạn tự động

Sau 15 phút, vé ngắn hạn hết hiệu lực. Người dùng **không hề biết** điều đó,
vì giao diện tự xử lý ở `client/src/services/redux/query/baseQuery.js`:

```
Gọi API  ──▶  Máy chủ trả 401 (vé hết hạn)
                    │
                    ▼
         Tự gọi POST /api/users/refresh
         (cookie vé dài hạn tự động đi kèm)
                    │
         ┌──────────┴───────────┐
         ▼                      ▼
   Được vé mới            Vé dài hạn cũng hỏng
   Gọi lại API cũ         → Đưa về trang đăng nhập
```

Có một chi tiết tinh tế trong file này:

```js
// Nhiều query có thể cùng nhận 401 một lúc (trang chủ gọi 4-5 endpoint song
// song). Dùng chung một promise để chỉ gọi refresh ĐÚNG MỘT LẦN.
let refreshPromise = null;
```

Trang chủ gọi 5 API cùng lúc. Nếu cả 5 cùng nhận 401 và cùng đi xin gia hạn,
sẽ có 5 lần xoay vòng vé nối đuôi nhau — và vé cấp trước bị chính lần sau thu
hồi, kết cục là người dùng bị đá ra ngoài. Dùng chung một lời hứa (`promise`)
để 5 request cùng chờ đúng một lần gia hạn.

**Xoay vòng vé (rotation).** Mỗi lần gia hạn, vé dài hạn cũ bị **thu hồi ngay**
và thay bằng vé mới. Nhờ vậy, nếu kẻ trộm lấy được vé dài hạn và đem dùng, chủ
tài khoản dùng vé sau sẽ làm vé của kẻ trộm hỏng — hoặc ngược lại, và sự bất
thường lộ ra.

## 4.5. Đăng xuất — và vì sao nó khó hơn vẻ ngoài

Vấn đề: tấm vé **tự chứng minh được tính hợp lệ** nhờ chữ ký. Máy chủ không cần
tra kho vẫn xác thực được — đó là ưu điểm về tốc độ, nhưng cũng có nghĩa là
**xoá vé ở trình duyệt không làm nó hết hiệu lực**. Ai đã kịp sao chép tấm vé
vẫn dùng tiếp được cho tới khi hết 15 phút.

Cách xử lý: một **sổ đen** trong Redis. Khi đăng xuất, mã `jti` của tấm vé bị
ghi vào sổ đen, và mọi request sau đó đều bị từ chối.

```
Đăng xuất  ──▶  Ghi jti vào Redis với hạn = thời gian còn lại của vé
                Xoá cookie vé dài hạn
                Giao diện xoá localStorage
```

Sổ đen đặt trong Redis chứ không phải bộ nhớ máy chủ, để **đăng xuất vẫn có
hiệu lực sau khi khởi động lại backend**. Mục hết hạn tự biến mất đúng lúc vé
hết hiệu lực, nên sổ đen không phình to mãi.

File liên quan: `server_python/app/services/token_store.py`.

## 4.6. Bản đồ file

| File | Vai trò |
|---|---|
| `client/src/layouts/login/LoginLayout.jsx` | Màn hình đăng nhập |
| `client/src/services/redux/query/baseQuery.js` | Đính vé vào request, tự gia hạn khi gặp 401 |
| `client/src/services/utils/token.js` | Đọc/ghi vé trong localStorage |
| `client/src/auth/ProtectedRoute.jsx` | Chặn trang cần đăng nhập |
| `client/src/context/FetchDataProvider.jsx` | Giữ thông tin người dùng cho toàn app |
| `server_python/app/routes/users.py` | Khai báo địa chỉ `/api/users/login`, `/refresh`, `/logout` |
| `server_python/app/controllers/auth.py` | Nghiệp vụ đăng ký, đăng nhập, gia hạn, đăng xuất |
| `server_python/app/utils/token.py` | Tạo và đọc vé |
| `server_python/app/utils/cookies.py` | Đặt/xoá cookie vé dài hạn |
| `server_python/app/services/token_store.py` | Sổ đen thu hồi vé |
| `server_python/app/middleware/auth.py` | Chốt kiểm vé trước mọi controller |
| `server_python/app/services/rate_limit.py` | Đếm số lần thử sai |

## 4.7. Giới hạn đã biết

**Cookie `SameSite=Lax` không đi qua hai tên miền khác nhau.** Nếu bạn mở giao
diện ở `http://localhost:5173` nhưng máy chủ lại ở một tên miền khác, trình
duyệt sẽ không gửi cookie vé dài hạn, và tính năng tự gia hạn ngừng hoạt động
— người dùng bị đá ra sau đúng 15 phút.

Đây là **lựa chọn có chủ đích**: `SameSite=Lax` chặn được một lớp tấn công
(CSRF). Muốn dùng chéo tên miền thì phải chuyển sang `SameSite=None; Secure`,
tức là **bắt buộc có HTTPS**. Hai biến `COOKIE_SAMESITE` và `COOKIE_SECURE`
trong `settings.py` để dành sẵn cho việc đó khi triển khai thật.

---

Tiếp theo: [5. Luồng bài viết và channel](05-luong-bai-viet.md)
