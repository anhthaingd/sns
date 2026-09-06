# 5. Luồng bài viết và channel

## 5.1. Mô hình dữ liệu

**Channel** là một nhóm (giống nhóm Facebook). **Post** là bài viết, luôn thuộc
về một channel. Người dùng phải **tham gia** channel thì mới thấy bài trong đó.

```
   User  ──── tham gia ────▶  Channel  ◀──── thuộc về ────  Post
                                                             │
                                              ┌──────────────┼──────────────┐
                                              │              │              │
                                          liked[]      book_marked[]    comments[]
                                        (ai đã thích)  (ai đã lưu)    (bình luận)
```

File `server_python/app/models/post.py`:

```python
class Post(Document):
    user: PydanticObjectId | None       # ai viết
    channel: PydanticObjectId | None    # thuộc channel nào
    content: str | None                 # nội dung (có định dạng)
    images: dict | None                 # ảnh đính kèm: {"name": ..., "url": ...} hoặc để trống
    liked: list[PydanticObjectId]       # danh sách id người đã thích
    book_marked: list[PydanticObjectId] # danh sách id người đã lưu
    comments: list[dict]                # bình luận nằm luôn trong bài
```

Hai quyết định thiết kế đáng chú ý:

**`images` là một object, KHÔNG phải mảng.** Mỗi bài chỉ một ảnh. Đây từng là
nguồn của một lỗi nghiêm trọng: trang tìm kiếm viết `p?.images[0]` như thể nó
là mảng, mà 358/374 bài trong kho không có ảnh, nên `null[0]` làm **sập cả
trang**. Bài học: khi hai chỗ trong code hiểu khác nhau về hình dạng một
trường, sớm muộn cũng có chỗ nổ.

**Bình luận nằm luôn trong bài viết** thay vì tách ra bảng riêng. Với vài chục
bình luận mỗi bài thì cách này nhanh hơn (một lần đọc là có đủ). Nếu sau này
một bài có hàng nghìn bình luận thì phải tách ra — nhưng chưa cần bây giờ.

**Chỉ mục** (mục lục để tra nhanh):

```python
IndexModel([("channel", ASCENDING), ("created_at", DESCENDING)])  # bài trong channel, mới nhất trước
IndexModel([("user", ASCENDING), ("created_at", DESCENDING)])     # bài của một người
IndexModel([("book_marked", ASCENDING)])                          # bài đã lưu
```

Ba chỉ mục ứng với đúng ba cách người dùng xem bài viết.

## 5.2. Luồng đăng một bài viết

```
NGƯỜI DÙNG                     GIAO DIỆN                      MÁY CHỦ
──────────────────────────────────────────────────────────────────────────────
Gõ nội dung, chọn ảnh
Bấm "Post"
   │
   └───▶ CreatePost.jsx
         useCreatePostMutation()
              │
              └───▶ POST /api/posts/{channelId}
                    (dạng multipart vì có file ảnh)
                          │
                          ├─ ① Kiểm vé đăng nhập
                          ├─ ② Nhận file: kiểm định dạng và dung lượng
                          ├─ ③ Lưu ảnh vào public/uploads/
                          ├─ ④ Ghi bài vào MongoDB
                          └─ ⑤ Tạo thông báo cho thành viên channel
                          │
              ◀───────────┘
              { message: "Đăng bài thành công!" }
              │
              ├─ useMutationToast hiện thông báo xanh
              ├─ Xoá trắng ô soạn bài (onSuccess)
              └─ Tự tải lại danh sách bài (nhờ tag cache)
```

### Bước ② — Kiểm file trước khi đọc

File `server_python/app/middleware/upload.py`:

```python
# Kiểm tra kích thước TRƯỚC khi đọc: `await file.read()` nạp toàn bộ file vào
# RAM, nên kiểm tra sau khi đọc thì file 2GB đã kịp làm sập tiến trình.
if file.size is not None and file.size > MAX_FILE_SIZE:
    raise ApiError(413, f"File vượt quá {MAX_FILE_SIZE // (1024 * 1024)}MB.")
```

Thứ tự ở đây quyết định sống chết của máy chủ. Kiểm tra **sau** khi đọc file
thì kẻ xấu chỉ cần gửi một file khổng lồ là làm sập dịch vụ.

### Bước ⑤ — Thông báo

Đăng bài xong, mọi thành viên khác trong channel nhận được một thông báo. Bản
ghi thông báo lưu ở collection `notifications`, và chuông ở góc trên bên phải
(`NotificationDropdown.jsx`) đọc từ đó.

## 5.3. Thích một bài — và bài học về bộ nhớ đệm

Bấm nút thích trông đơn giản, nhưng phía sau có một quyết định kỹ thuật đáng
kể.

**Vấn đề.** Trình duyệt nhớ sẵn kết quả các API đã gọi để trang chạy nhanh.
Nhưng khi bạn thích một bài, số lượt thích đổi — bản nhớ cũ thành sai. Phải có
cách nói cho hệ thống biết "chỗ này cũ rồi, tải lại đi".

**Cách cũ (đã sửa).** Mọi danh sách bài viết dùng chung một nhãn `'posts'`, và
mọi thao tác đều xoá sạch nhãn đó:

```js
invalidatesTags: ['posts']   // ← thích một bài = tải lại TẤT CẢ danh sách
```

Hậu quả: bấm thích một bài ở trang chủ làm tải lại **toàn bộ** — feed, trang cá
nhân, danh sách của admin, bài trong channel, mục đã lưu — kể cả những danh
sách không hề chứa bài đó.

**Cách hiện tại.** File `client/src/services/redux/query/api/postsApi.js`:

```js
// Mỗi danh sách khai báo hai loại nhãn: một nhãn cho "tập hợp này",
// và một nhãn riêng cho từng bài trong đó.
const listTags = (result) => [
  { type: 'posts', id: 'LIST' },
  ...(result?.posts || []).map((post) => ({ type: 'posts', id: post._id })),
];

// Thích một bài -> chỉ vô hiệu hoá nhãn của đúng bài ấy.
likePost: builder.mutation({
  invalidatesTags: (result, error, arg) => [{ type: 'posts', id: arg?.postId }],
}),
```

Giờ chỉ những danh sách **thật sự chứa bài đó** mới tải lại.

> Nói cho đúng: đây là **thu hẹp**, không phải loại bỏ. Danh sách nào có chứa
> bài đó vẫn phải tải lại, vì nội dung bài nằm ngay trong danh sách. Cái tiết
> kiệm được là các danh sách không liên quan.

Thêm/xoá bài thì khác — số lượng phần tử đổi nên phải đụng tới nhãn `LIST`:

```js
deletePost: builder.mutation({
  invalidatesTags: (result, error, arg) => [
    { type: 'posts', id: 'LIST' },
    { type: 'posts', id: arg?.postId },
  ],
}),
```

## 5.4. Vấn đề N+1 — và cách dự án tránh

Danh sách 10 bài viết cần hiển thị tên và ảnh đại diện của người viết. Cách
ngây thơ:

```
Lấy 10 bài                        → 1 lần hỏi kho
Với mỗi bài, lấy thông tin tác giả → 10 lần hỏi kho
Với mỗi bài, lấy thông tin channel → 10 lần hỏi kho
                                   ─────────────────
                                     21 lần hỏi kho
```

Đây gọi là **vấn đề N+1**: một truy vấn ban đầu kéo theo N truy vấn con.

Cách dự án làm — file `server_python/app/utils/loaders.py`:

```
Lấy 10 bài                              → 1 lần
Gom hết id tác giả, hỏi MỘT lần cho cả 10 → 1 lần
Gom hết id channel, hỏi MỘT lần            → 1 lần
                                         ──────────
                                            3 lần
```

Kết quả đo được trong dự án: danh sách bài viết từ **53 xuống 5** truy vấn,
danh sách channel từ **64 xuống 4**.

Có test canh chuyện này khỏi tái diễn — `server_python/tests/test_query_count.py`
đếm số lệnh thật sự gửi xuống MongoDB và báo đỏ nếu vượt ngưỡng.

## 5.5. Nhắn tin thời gian thực

Bài viết dùng cách "hỏi thì trả lời" (request–response). Nhắn tin thì không thể
như vậy — không lẽ cứ 2 giây lại hỏi máy chủ "có tin mới chưa?".

Giải pháp: **Socket.IO** — một đường dây mở sẵn hai chiều giữa trình duyệt và
máy chủ, để máy chủ **chủ động đẩy** tin xuống.

```
Người A gõ tin nhắn
     │
     └──▶ socket.emit('sendMessage', {...})
                │
                ▼
          Máy chủ (app/sockets/handlers.py)
                ├─ Lưu tin vào MongoDB
                └─ socket.emit tới đúng người B
                          │
                          ▼
                   Trình duyệt người B hiện tin ngay
```

File liên quan:

| File | Vai trò |
|---|---|
| `server_python/app/sockets/handlers.py` | Xử lý sự kiện phía máy chủ |
| `client/src/context/SocketProvider.jsx` | Giữ kết nối phía trình duyệt |
| `client/src/components/modal/ChatModal.jsx` | Cửa sổ chat |
| `client/src/components/modal/VideoModal.jsx` | Gọi video (WebRTC) |

**Một chi tiết về khả năng mở rộng.** Socket.IO được cấu hình dùng Redis làm
trung gian. Nếu chỉ chạy một máy chủ thì không cần, nhưng khi chạy nhiều máy
chủ song song, người A nối vào máy 1 còn người B nối vào máy 2 — không có Redis
làm cầu, tin nhắn của A sẽ không bao giờ tới B.

## 5.6. Bản đồ file

**Phía giao diện:**

| File | Vai trò |
|---|---|
| `layouts/home/Home/HomeLayout.jsx` | Trang chủ, feed tổng hợp |
| `layouts/home/Home/components/CreatePost.jsx` | Ô soạn bài ở trang chủ |
| `layouts/home/Home/components/ListsPost.jsx` | Danh sách bài, cuộn tới đâu tải tới đó |
| `components/ui/SinglePost.jsx` | Một bài viết: thích, bình luận, lưu, sửa, xoá |
| `layouts/home/Channels/ChannelsList/ChannelListLayout.jsx` | Danh sách channel |
| `layouts/home/Channels/ChanelDetails/ChannelDetailsLayout.jsx` | Bên trong một channel |
| `layouts/home/Channels/ChanelDetails/PostDetails/PostDetailsLayout.jsx` | Chi tiết một bài |
| `layouts/home/BookMark/BookMarkLayout.jsx` | Bài đã lưu |
| `services/redux/query/api/postsApi.js` | Khai báo 15 API về bài viết |

**Phía máy chủ:**

| File | Vai trò |
|---|---|
| `app/routes/posts.py` | 12 địa chỉ URL về bài viết |
| `app/controllers/posts.py` | Nghiệp vụ bài viết |
| `app/routes/channels.py` + `app/controllers/channels.py` | Channel |
| `app/models/post.py`, `app/models/channel.py` | Hình dạng dữ liệu |
| `app/utils/loaders.py` | Nạp theo lô, tránh N+1 |
| `app/middleware/upload.py` | Nhận file ảnh |

---

Tiếp theo: [6. Luồng CV và việc làm](06-luong-cv-va-viec-lam.md)
