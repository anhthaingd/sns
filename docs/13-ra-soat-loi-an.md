# 13. Rà soát lỗi ẩn (14/09/2026)

> Tài liệu này ghi lại một đợt rà soát toàn bộ dự án, xuất phát từ một lỗi
> người dùng báo khi thử sửa trang cá nhân. Mỗi lỗi trong đây đều đã được
> **tái hiện thật** trên stack đang chạy (`docker compose up -d`), có lệnh kèm
> theo để bất kỳ ai cũng dựng lại được. Không có mục nào là suy đoán.

## 13.1. Lỗi được báo — và nó có thật

**Triệu chứng người dùng gặp:** đang đăng nhập bằng chính tài khoản của mình,
bấm *Sửa trang cá nhân* → *Lưu*, hệ thống báo
*"Bạn không thể sửa thông tin của người khác!"*.

**Tái hiện:**

```bash
TOKEN=... # access token của một tài khoản bất kỳ
curl -i -X PUT http://localhost:3000/api/users/undefined -H "Authorization: Bearer $TOKEN"
# HTTP/1.1 403 Forbidden
# {"error":true,"success":false,"message":"Bạn không thể sửa thông tin của người khác!",
#  "code":"user.cannotEditOthers"}
```

**Nguyên nhân.** Endpoint phía client khai báo là nhận một object hai trường:

```js
// client/src/services/redux/query/api/usersApi.js
updateUser: builder.mutation({
  query: ({ id, body }) => ({ url: `users/${id}`, method: 'PUT', body }),
})
```

Nhưng chỗ gọi lại truyền thẳng một `FormData`:

```js
// client/src/components/modal/UpdateProfileModal.jsx (bản cũ)
await updateUser(data);   // data là FormData
```

`FormData` không có thuộc tính `id` cũng không có `body`, nên phép bóc tách cho
ra `undefined` cả hai. Địa chỉ gửi đi thành `PUT /api/users/undefined`, và
backend so `"undefined"` với id trong token — dĩ nhiên là khác nhau, nên trả về
đúng câu *"không thể sửa thông tin của người khác"*.

Nói cách khác: **backend làm đúng, câu thông báo cũng đúng theo dữ liệu nó
nhận được.** Sai nằm ở chỗ client gửi sai địa chỉ. Đây là loại lỗi mà
JavaScript không cảnh báo được vì không có kiểu tĩnh — `undefined` cứ thế đi
vào chuỗi URL.

**Đã sửa:**

```js
await updateUser({ id: user?._id, body: data });
```

## 13.2. Lỗi thứ hai, nấp ngay sau lỗi thứ nhất: không đổi được mật khẩu

Sửa xong 13.1 thì lộ ra lỗi kế tiếp trên cùng màn hình. Form sửa hồ sơ chỉ có
**một** ô mật khẩu (mật khẩu mới), trong khi backend bắt buộc phải có mật khẩu
cũ đúng thì mới cho đổi:

```python
# server_python/app/controllers/users.py
if new_password and new_password != old_password:
    if not old_password or not bcrypt.checkpw(old_password..., current.password...):
        raise ApiError(403, code="user.wrongOldPassword")
```

Client luôn gửi `oldPassword=''`, nên mọi lần đổi mật khẩu đều bị từ chối:

```bash
curl -i -X PUT http://localhost:3000/api/users/$ID -H "Authorization: Bearer $TOKEN" \
  --form-string 'oldPassword=' --form-string 'newPassword=MatKhauMoi@123'
# HTTP/1.1 403 Forbidden — {"code":"user.wrongOldPassword"}
```

**Đã sửa:** thêm ô *Mật khẩu hiện tại* (ba ngôn ngữ) vào form, và chỉ đính kèm
cặp mật khẩu vào request khi người dùng thực sự điền mật khẩu mới.

Kiểm chứng lại bằng một tài khoản tạm:

```
PUT /api/users/<id>  (oldPassword đúng + newPassword) → 200
đăng nhập bằng mật khẩu mới → 200
đăng nhập bằng mật khẩu cũ  → 401
```

## 13.3. Lỗi thứ ba: lưu xong modal không đóng, toast thành công không hiện

Sau khi sửa 13.1, request đã trả về `200` nhưng **modal vẫn mở** và **không có
thông báo thành công nào**. Lỗi nằm ở bộ giảm trạng thái của modal:

```js
// client/src/context/ModalProvider.jsx (bản cũ)
if (typeof action.payload?.modal === 'object') return currentModal;  // THAY cả state
return { ...resetState, [currentModal]: !state[currentModal] };      // resetState = {}
```

Luồng "lưu thành công" trong `useMutationToast` chạy hai bước liên tiếp:

| Bước | Việc | Trạng thái sau đó |
|---|---|---|
| 1 | hiện toast: `setVisibleModal({ visibleToastModal })` | state bị **thay** thành `{ visibleToastModal }` — mọi cờ khác biến mất |
| 2 | `close()`: `setVisibleModal('visibleUpdateProfileModal')` | `!state['visibleUpdateProfileModal']` đọc phải `undefined` → đảo thành **`true`** |

Bước 2 vừa bật lại chính modal vừa định đóng, vừa xoá luôn toast của bước 1.
Lỗi này dính **mọi modal có nút lưu**: sửa hồ sơ, tạo channel, sửa channel,
sửa bài viết. Lý do trước giờ không ai để ý: đường **lỗi** chỉ có một lần
`setVisibleModal` nên toast lỗi vẫn hiện bình thường — đúng như người dùng đã
nhìn thấy ở 13.1.

**Đã sửa:** toast được tách khỏi cơ chế "mở modal này thì đóng modal kia".
Trộn trạng thái thay vì thay nguyên khối, và giữ toast qua mọi lần đóng/mở.

Kiểm chứng bằng trình duyệt thật (Playwright, `http://localhost:5173`):

```
bấm Sửa hồ sơ → đổi phần giới thiệu → Lưu
  PUT /api/users/6aa4c4286e41b58dc89d86e9 → 200
  toast  = "User updated successfully."
  dialog = đã đóng
  phần giới thiệu trên trang = nội dung mới
```

---

## 13.4. Những lỗi còn lại tìm được

> **Cập nhật 14/09/2026 — toàn bộ mục dưới đây ĐÃ ĐƯỢC SỬA.** Cách sửa, bộ test
> đi kèm và phần mã hoá tin nhắn nằm ở
> [tài liệu 14](14-va-loi-va-bo-test-phan-quyen.md). Phần mô tả bên dưới được
> giữ nguyên vì nó ghi lại *cách tái hiện* từng lỗi — vẫn là thứ cần đối chiếu
> khi muốn kiểm tra lại rằng chốt chặn còn nguyên.

Ba mục trên đã sửa vì nằm đúng trên màn hình được báo. Phần dưới là kết quả rà
soát rộng ra cả dự án, xếp theo mức độ nghiêm trọng.

Bối cảnh cần nhớ khi đọc: tại thời điểm rà soát,
`docker compose run --rm api-tests` cho **386 test đều xanh**, `npm run lint`
sạch, `check:i18n` khớp 583 khoá. Nghĩa là **không có test nào đang bảo vệ
những chỗ dưới đây** — đó chính là lý do chúng "ẩn". Sau đợt vá, con số là
**447 test API + 20 test E2E**, trong đó có ba file dành riêng cho phân quyền,
XSS và toàn vẹn dữ liệu.

### A. Nghiêm trọng — lộ dữ liệu / giả mạo

#### A1. Đọc được tin nhắn riêng của hai người bất kỳ

`GET /api/messages/{sender_id}/{receiver_id}` có kiểm tra đăng nhập, nhưng
**không kiểm tra người gọi có phải là một trong hai người trong cuộc trò chuyện
hay không**:

```python
# server_python/app/routes/chat.py
async def route_get_chat(sender_id, receiver_id, page, decoded=Depends(get_current_user)):
    return await get_chat(sender_id, receiver_id, page or 1)   # `decoded` không được dùng
```

Tái hiện — tài khoản demo đọc trọn hội thoại của hai người lạ:

```bash
curl "http://localhost:3000/api/messages/<idA>/<idB>?page=1" -H "Authorization: Bearer $TOKEN"
# 200 — trả về đầy đủ nội dung tin nhắn, kèm email của cả hai người
```

Chỉ cần id người dùng, mà id thì hiện công khai trong URL trang cá nhân.

**Hướng sửa:** truyền `decoded` vào `get_chat` và chặn nếu
`decoded["_id"]` không nằm trong `{sender_id, receiver_id}`.

#### A2. Socket không xác thực — mạo danh người khác gửi tin nhắn

`server_python/app/sockets/handlers.py` không có bước xác thực nào. Mọi handler
tin thẳng `_id` do client tự khai. Khách vãng lai không đăng nhập vẫn gửi được
tin nhắn **dưới danh nghĩa người khác**:

```bash
SID=$(curl -s "http://localhost:3000/socket.io/?EIO=4&transport=polling" | ...)
curl -X POST "http://localhost:3000/socket.io/?EIO=4&transport=polling&sid=$SID" -d '40'
curl -X POST "http://localhost:3000/socket.io/?EIO=4&transport=polling&sid=$SID" \
  -d '42["sendMessage",{"sender":{"_id":"<idA>"},"receiver":{"_id":"<idB>"},"content":"tin gia mao"}]'
```

Tin nhắn được ghi vào DB với `sender` là người bị mạo danh. Tương tự,
`joinChat` cho phép gán `socketId` của **tài khoản bất kỳ** về socket của kẻ
tấn công — tức là cướp luôn đường nhận tin nhắn của người đó.

**Hướng sửa:** bắt buộc access token ở sự kiện `connect` (socket.io hỗ trợ
`auth`), lưu `user_id` theo `sid` ở phía máy chủ, và mọi handler chỉ dùng id đó
— không bao giờ dùng id client gửi lên.

#### A3. XSS lưu trữ trong nội dung bài viết

Nội dung bài viết là HTML (soạn thảo bằng ReactQuill), được lưu **nguyên văn**
và render bằng `dangerouslySetInnerHTML`
(`client/src/components/ui/SinglePost.jsx:257`,
`client/src/layouts/home/UserSettings/components/Posts.jsx:62`). Không có bước
làm sạch HTML ở bất kỳ đâu — không có `DOMPurify` phía client, không có `bleach`
phía máy chủ.

Trình soạn thảo không tạo ra thẻ nguy hiểm, nhưng API thì nhận tuốt:

```bash
curl -X POST "http://localhost:3000/api/posts/<channelId>" -H "Authorization: Bearer $TOKEN" \
  --form-string 'content=<img src=x onerror="alert(1)">XSS-TEST'
# 201 — trong DB: content = '<img src=x onerror="alert(1)">XSS-TEST'
```

Mọi người xem bài đó sẽ chạy đoạn mã ấy trên phiên đăng nhập của chính họ.

**Hướng sửa:** làm sạch HTML **ở máy chủ** trước khi lưu (danh sách thẻ cho
phép đúng bằng những gì trình soạn thảo sinh ra), và làm sạch thêm một lần ở
client trước khi render.

#### A4. Hồ sơ người dùng đọc được khi chưa đăng nhập

`GET /api/users/{user_id}` không có `Depends(get_current_user)`:

```bash
curl http://localhost:3000/api/users/<id>     # không kèm token
# 200 — username, EMAIL, địa chỉ, giới thiệu, danh sách follower
```

Điều này đi ngược chính cam kết trong README mục 1.1 (*"Không lộ email nào đã
tồn tại"*): màn hình đăng nhập giấu email rất kỹ, còn endpoint này thì phát
email ra cho người chưa đăng nhập.

**Hướng sửa:** thêm `Depends(get_current_user)`, và cân nhắc bỏ `email` khỏi
payload trang cá nhân của người khác.

### B. Sai phân quyền

#### B1. Đăng bài vào channel chưa tham gia

`create_post` không kiểm tra người gửi có phải thành viên channel không:

```bash
curl -X POST "http://localhost:3000/api/posts/<channel-chua-tham-gia>" \
  -H "Authorization: Bearer $TOKEN" --form-string 'content=xin chao'
# 201 Created
```

`like`, `bookmark`, `comment` cũng vậy. Trong khi `get_channel_details` lại
chặn đúng (403 `channel.notJoined`) — tức là quy tắc "phải tham gia mới tương
tác được" có tồn tại, chỉ là không áp cho đường ghi.

### C. Mất dữ liệu / chức năng thiếu

#### C1. Lưu CV lần đầu thì mất ảnh và chứng chỉ

Trong `post_resume`, nhánh tạo mới **thoát sớm trước** đoạn xử lý file:

```python
if not existed_resume:
    resume = Resume(**resume_data)
    await resume.insert()
    await _refresh_match_profile(resume)
    return ok(code="resume.saved")     # <-- thoát ở đây

avatar_files = files.get("avatar", [])  # <-- chỉ chạy khi CV đã tồn tại
...
cert_files = files.get("certificates", [])
```

Người dùng mới điền CV kèm ảnh + chứng chỉ ngay lần đầu: file đã được ghi
xuống đĩa nhưng **không được gắn vào CV** — vừa mất dữ liệu vừa để lại file rác.
Phải bấm lưu lần thứ hai mới ăn.

#### C2. `$set` nguyên khối làm trắng dữ liệu (còn 3 chỗ)

Lỗi này **đã được sửa cho người dùng** (xem chú thích trong
`server_python/app/controllers/users.py`), nhưng ba chỗ khác vẫn giữ nguyên
kiểu cũ:

| File | Dòng | Ghi đè vô điều kiện |
|---|---|---|
| `server_python/app/controllers/channels.py` | `update_channel` | `{"name": name, "intro": intro}` |
| `server_python/app/controllers/web.py` | `update_web` | 4 trường tên/màu/quote |
| `server_python/app/controllers/posts.py` | `updated_post` | `{"content": content}` |

Hiện chưa bung ra vì client luôn gửi đủ trường. Đúng như ghi chú trong code
users.py: *"đó là may mắn, không phải thiết kế"*.

#### C3. Xoá channel nhưng lối tắt của người khác vẫn còn

```python
# server_python/app/controllers/channels.py — delete_channel
await Shortcut.find_one({"channel": channel_oid}).update({"$set": {"isJoin": False}})
```

`find_one` chỉ chạm **một** bản ghi. Channel có 30 người ghim thì 29 người vẫn
thấy lối tắt trỏ tới channel đã bị xoá. Phải là `Shortcut.find(...)`.
`delete_channel` cũng không xoá file ảnh của các bài viết trong channel.

#### C4. Follow không sinh thông báo

README mục 1.2 ghi: *"Có người thích, bình luận, **follow** → hiện trong chuông
thông báo"*. Nhưng `server_python/app/controllers/follows.py` không hề tạo
`Notification` nào, và bảng câu chữ (`app/messages.py`, `locales/*/error.json`)
chỉ có `postLiked`, `postSaved`, `postCommented`, `removedFromChannel` —
**không có** khoá nào cho follow. Hoặc bổ sung thông báo, hoặc sửa README.

#### C5. Follow hỏng âm thầm nếu thiếu bản ghi khởi tạo

```python
await Following.find_one(Following.user == user_oid).update({"$push": {"following": target_oid}})
```

Beanie **không upsert**. Tài khoản nào không có sẵn bản ghi `Following`/
`Follower` thì bấm Follow sẽ trả về *"Follow tài khoản thành công!"* nhưng
không có gì được ghi. Hiện tại chưa bung vì `register_user` tạo sẵn hai bản ghi
(đã kiểm tra trong DB: 8962 user / 8962 followings / 8962 followers). Nhưng bất
kỳ đường tạo user nào khác — script seed, nhập liệu tay — đều sinh ra tài khoản
hỏng chức năng follow mà không báo lỗi.

### D. Lỗi giao diện

#### D1. Tin nhắn của người A nhảy vào khung chat đang mở với người B

```js
// client/src/components/modal/ChatModal.jsx
socket.on('receiveMessage', (message) => {
  setMessages((prev) => [...prev, message]);   // không lọc theo hội thoại
});
```

Đang mở khung chat với B, C nhắn tới → tin của C hiện luôn trong khung của B.
Ngoài ra tin nhận qua socket **không có `_id`** (server phát lại nguyên gói mà
client gửi lên), nên `key={m._id}` là `undefined` → React cảnh báo trùng key khi
có nhiều tin mới.

#### D2. Xin quyền camera/micro ngay khi đăng nhập

```js
// client/src/context/SocketProvider.jsx
useEffect(() => {
  if (me) {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })...
```

`me` được gán ngay khi đăng nhập (`App.jsx`), nên **ai đăng nhập cũng bị trình
duyệt hỏi quyền camera + micro**, kể cả người không bao giờ gọi video. Nên dời
việc xin quyền vào lúc thực sự bắt đầu cuộc gọi.

#### D3. Người nhận không bao giờ biết cuộc gọi đã kết thúc

Client chờ một trường mà máy chủ không gửi:

```js
// client — SocketProvider.jsx
socket.on('callEnd', (data) => {
  if (data?.receiver?.socketCallId) setCallEnded(true);
});
```

```python
# server — sockets/handlers.py
await sio.emit("callEnd", {"receiver": {"_id": ..., "username": ...}}, to=...)
```

Không có `socketCallId` trong gói gửi đi → điều kiện luôn sai → `callEnded`
không bao giờ bật ở phía người nhận. Ngoài ra `leaveCall` kết thúc bằng
`window.location.reload()` — tải lại cả trang chỉ để dọn một cuộc gọi.

#### D4. Lối tắt sắp xếp ngược

`get_shortcuts` dùng `.sort("count")` (tăng dần), nên channel **ít vào nhất**
lại đứng đầu. Đây là bản chép đúng của code Node cũ
(`server/controllers/shortcut.controllers.js:10` — `.sort({ count: 1 })`), tức
là lỗi có từ trước khi chuyển sang Python, không phải lỗi khi chuyển đổi.

### E. Điểm cần lưu ý (cũng đã xử lý)

- `ACCESS_TOKEN_SECRET` có giá trị mặc định là `"secret"`
  (`app/config/settings.py:30`). `docker-compose.yml` có đặt đè bằng chuỗi dev,
  nhưng nếu chạy ngoài Docker mà quên đặt biến môi trường thì ai cũng ký được
  token hợp lệ. Nên chặn ngay lúc khởi động nếu biến chưa được đặt.
- File upload chỉ kiểm **phần mở rộng**, không kiểm nội dung thật. `.svg` không
  nằm trong danh sách cho phép nên rủi ro XSS qua file là thấp, nhưng vẫn nên
  kiểm magic bytes.
- `update_user` lưu file xuống đĩa **trước** khi kiểm quyền sở hữu, nên gửi
  `PUT /api/users/<id-người-khác>` kèm ảnh vẫn ghi được file rác vào đĩa dù
  request bị từ chối 403.

---

## 13.5. Vì sao 386 test xanh mà vẫn sót

Đáng để rút kinh nghiệm, vì cả ba lỗi đã sửa ở 13.1–13.3 đều **nằm hoàn toàn
phía client**, còn bộ test API thì kiểm rất kỹ phía máy chủ — kể cả đúng tình
huống của 13.1:

```python
# server_python/tests/test_users.py:138
r = await client.put(f"/api/users/{other_user.id}", headers=user.headers, data={"username": "hacked"})
```

Test này khẳng định backend **phải** chặn — và backend chặn đúng. Cái không ai
kiểm là: *client có gọi đúng địa chỉ không.*

Bộ E2E hiện có 15 test nhưng **không có test nào đi qua luồng sửa hồ sơ**
(`grep -i "profile" e2e/test_e2e.py` không ra kết quả nào). Thêm một test E2E
cho luồng "sửa hồ sơ → lưu → modal đóng → giá trị mới hiện trên trang" sẽ chặn
được cả ba lỗi 13.1, 13.2 và 13.3 cùng lúc.

## 13.6. Tóm tắt

| # | Lỗi | Mức | Trạng thái |
|---|---|---|---|
| 13.1 | Sửa hồ sơ báo "không thể sửa của người khác" | Chặn chức năng | ✅ đã sửa |
| 13.2 | Không đổi được mật khẩu | Chặn chức năng | ✅ đã sửa |
| 13.3 | Lưu xong modal không đóng, không có toast | Chặn chức năng | ✅ đã sửa |
| A1 | Đọc được tin nhắn riêng của người khác | Nghiêm trọng | ✅ đã sửa |
| A2 | Socket không xác thực, mạo danh được | Nghiêm trọng | ✅ đã sửa |
| A3 | XSS lưu trữ trong bài viết | Nghiêm trọng | ✅ đã sửa |
| A4 | Hồ sơ + email đọc được khi chưa đăng nhập | Nghiêm trọng | ✅ đã sửa |
| B1 | Đăng bài vào channel chưa tham gia | Vừa | ✅ đã sửa |
| C1 | Lưu CV lần đầu mất ảnh và chứng chỉ | Vừa | ✅ đã sửa |
| C2 | `$set` nguyên khối (channel, web, bài viết) | Vừa | ✅ đã sửa |
| C3 | Xoá channel, lối tắt người khác còn lại | Nhẹ | ✅ đã sửa |
| C4 | Follow không sinh thông báo (README nói có) | Nhẹ | ✅ đã sửa |
| C5 | Follow hỏng âm thầm nếu thiếu bản ghi | Nhẹ | ✅ đã sửa |
| D1 | Tin nhắn lạc vào khung chat đang mở | Vừa | ✅ đã sửa |
| D2 | Xin quyền camera/mic ngay khi đăng nhập | Nhẹ | ✅ đã sửa |
| D3 | Người nhận không biết cuộc gọi đã kết thúc | Nhẹ | ✅ đã sửa |
| D4 | Lối tắt sắp xếp ngược | Nhẹ | ✅ đã sửa |
