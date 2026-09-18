# 📡 Báo cáo Kiểm tra Kiến trúc WebSocket — Fuurin

> **Ngày kiểm tra:** 17/09/2026
> **Phạm vi:** Toàn bộ hệ thống real-time: tin nhắn (chat), thông báo (notifications), thông báo hệ thống (system alerts)

---

## 1. Tổng quan Kiến trúc Hiện tại

### 1.1 Các thành phần liên quan

| Thành phần | File | Vai trò |
|---|---|---|
| **Socket.IO Server** | `server_python/app/main.py` | Khởi tạo `AsyncServer` + Redis Manager |
| **Socket Handlers** | `server_python/app/sockets/handlers.py` | Xử lý sự kiện: `joinChat`, `sendMessage`, `joinCall`, v.v. |
| **Socket Client** | `client/src/context/SocketProvider.jsx` | Kết nối socket.io-client, quản lý video call |
| **Chat Modal** | `client/src/components/modal/ChatModal.jsx` | UI chat + lắng nghe `receiveMessage` |
| **Notification Route** | `server_python/app/routes/notifications.py` | REST API thông báo (GET, POST đánh đã đọc) |
| **Notification Dropdown** | `client/src/components/dropdown/NotificationDropdown.jsx` | UI chuông thông báo |
| **Messages Dropdown** | `client/src/components/dropdown/MessagesDropdown.jsx` | UI danh sách tin nhắn mới nhất |
| **FetchDataProvider** | `client/src/context/FetchDataProvider.jsx` | Fetch data qua REST API (polling) |
| **Notification Model** | `server_python/app/models/notification.py` | Document MongoDB: `notifications` |
| **User Model** | `server_python/app/models/user.py` | Lưu `socketId`, `socketCallId` trong DB |

### 1.2 Sơ đồ Kiến trúc Hiện tại

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TRÌNH DUYỆT (Client)                           │
│                                                                            │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐ │
│  │  SocketProvider  │    │ FetchDataProvider │    │  NotificationDropdown  │ │
│  │                  │    │                   │    │                        │ │
│  │ • socket.io conn │    │ • useGetNewest    │    │ • useGetNotifications  │ │
│  │ • joinChat       │    │   MessageQuery()  │    │   Query()              │ │
│  │ • joinCall       │    │                   │    │ • setInterval(60s)     │ │
│  │ • Video Call     │    │ (REST Polling)     │    │   refetch              │ │
│  └────────┬─────────┘    └─────────┬─────────┘    └───────────┬────────────┘ │
│           │                        │                          │              │
│  ┌────────▼─────────┐              │                          │              │
│  │    ChatModal      │              │                          │              │
│  │                   │              │                          │              │
│  │ • on('receive     │              │                          │              │
│  │   Message')       │              │                          │              │
│  │ • emit('send      │              │                          │              │
│  │   Message')       │              │                          │              │
│  └────────┬──────────┘              │                          │              │
│           │                         │                          │              │
└───────────┼─────────────────────────┼──────────────────────────┼──────────────┘
            │ WebSocket               │ HTTP REST                │ HTTP REST
            │ (socket.io)             │ (RTK Query)              │ (RTK Query)
            │                         │                          │
┌───────────▼─────────────────────────▼──────────────────────────▼──────────────┐
│                        MÁY CHỦ (Python FastAPI)                               │
│                                                                                │
│  ┌──────────────────────────────────┐    ┌──────────────────────────────────┐  │
│  │      Socket.IO AsyncServer       │    │         FastAPI Routes           │  │
│  │                                   │    │                                  │  │
│  │  Sự kiện được xử lý:             │    │  GET /api/notifications          │  │
│  │  • connect (xác thực JWT)        │    │  POST /api/notifications/:id     │  │
│  │  • joinChat → lưu socketId vào   │    │  GET /api/newest_messages        │  │
│  │    collection users trong DB     │    │  PUT /api/newest_messages/:id    │  │
│  │  • sendMessage → ghi DB          │    │  GET /api/messages/:s/:r         │  │
│  │    + emit receiveMessage         │    │                                  │  │
│  │  • joinCall / callUser /         │    │  ⚠️ KHÔNG có WebSocket event     │  │
│  │    answerCall / callEnd          │    │     cho notifications!           │  │
│  │  • disconnect → xoá socketId     │    │                                  │  │
│  └──────────────┬────────────────────┘    └──────────────────────────────────┘  │
│                 │                                                               │
│                 ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         MongoDB                                          │   │
│  │                                                                          │   │
│  │  users: { socketId, socketCallId, ... }  ← mapping socket ↔ user        │   │
│  │  chats: { sender, receiver, content, timestamp }                         │   │
│  │  newestmessages: { sender, receiver, content, lastSent }                 │   │
│  │  notifications: { user, seeder, notification, code, isRead }             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                      Redis (tuỳ chọn)                                    │   │
│  │  AsyncRedisManager → pub/sub giữa nhiều worker                           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phân tích Chi tiết Các Vấn đề

### 2.1 🔴 Thông báo (Notifications) — KHÔNG real-time

**Mức độ nghiêm trọng: Cao**

#### Hiện trạng

```
Hành động (like, comment, follow)
         │
         ▼
  Ghi Notification vào MongoDB  ←── posts.py, follows.py
         │
         ╳  KHÔNG có bước emit WebSocket
         │
         ▼
  Client POLLING mỗi 60 giây   ←── NotificationDropdown.jsx (setInterval)
         │
         ▼
  Người dùng thấy thông báo     ←── Trễ tối đa 60 giây!
```

**Vấn đề cốt lõi:** Khi một hành động tạo notification (like bài viết, bình luận, follow), server **CHỈ ghi vào MongoDB** mà **KHÔNG emit sự kiện WebSocket** nào. Client phải tự polling REST API `GET /api/notifications` mỗi 60 giây để kiểm tra.

**Code gốc của vấn đề — server tạo notification nhưng không emit:**

```python
# server_python/app/controllers/posts.py (dòng 300-308)
# Khi ai đó like bài viết:
await Notification(
    user=post.user,
    seeder=user_id,
    code="notification.postLiked",
    ...
).insert()
# ⚠️ KẾT THÚC — không có sio.emit() nào ở đây!
```

**Code gốc của vấn đề — client polling thay vì lắng nghe socket:**

```javascript
// client/src/components/dropdown/NotificationDropdown.jsx (dòng 77-84)
useEffect(() => {
    const refresh = setInterval(() => {
      setCurPage(1);
      setNotifications([]);
      setHasMore(true);
      refetchNotifications();
    }, REFRESH_MS);  // REFRESH_MS = 60_000 (60 giây)
    return () => clearInterval(refresh);
}, [refetchNotifications]);
```

**Hệ quả:**
- Người dùng phải chờ **tối đa 60 giây** để thấy thông báo mới
- Badge đếm chưa đọc trên chuông 🔔 luôn bị trễ
- Trải nghiệm không giống một ứng dụng real-time
- Tiêu tốn băng thông: mỗi client gửi HTTP request mỗi phút dù không có gì mới

---

### 2.2 🟡 Danh sách tin nhắn mới nhất (Messages Dropdown) — Bán real-time, vẫn có lỗ hổng

**Mức độ nghiêm trọng: Trung bình**

#### Hiện trạng

```
User A gửi tin nhắn cho User B
         │
         ▼
  Socket emit 'sendMessage'
         │
         ▼
  Server ghi Chat + NewestMessage vào DB
  Server emit 'receiveMessage' cho CẢ HAI bên
         │
         ▼
  ChatModal nhận 'receiveMessage'
  → Nếu message.refetch === true → gọi refetchMessages()
         │
         ▼
  refetchMessages() = REST API call GET /api/newest_messages
         │
         ▼
  Cập nhật danh sách tin nhắn & badge tin nhắn
```

**Vấn đề:**

| # | Vấn đề | Giải thích |
|---|--------|------------|
| 1 | **refetch qua REST thay vì push data** | Khi nhận `receiveMessage`, client gọi lại REST API `GET /api/newest_messages` để lấy toàn bộ danh sách. Thay vì server đẩy trực tiếp dữ liệu cập nhật, client phải đi vòng một request HTTP. |
| 2 | **Chỉ hoạt động khi ChatModal đang mở** | Listener `receiveMessage` chỉ được đăng ký trong `ChatModal.jsx` (dòng 115). Nếu user không mở khung chat → **không có listener** → badge tin nhắn trên Header KHÔNG cập nhật cho đến khi có thao tác khác trigger re-render. |
| 3 | **Race condition** | Giữa lúc ghi DB và emit, nếu `refetchMessages()` chạy quá nhanh, DB chưa commit xong → client nhận data cũ. |

**Code minh hoạ vấn đề "chỉ hoạt động khi ChatModal mở":**

```
ChatModal ĐÓNG                    ChatModal MỞ
─────────────────                  ─────────────────
User B nhắn tin tới ──►            User B nhắn tin tới ──►
                                   
socket.on('receiveMessage')        socket.on('receiveMessage')
KHÔNG ĐĂNG KÝ ❌                  CÓ listener ✅
                                   → refetchMessages()
Badge tin nhắn: CŨ                → Badge cập nhật
```

---

### 2.3 🟡 Tin nhắn Chat — Real-time nhưng có hạn chế

**Mức độ nghiêm trọng: Trung bình**

#### Luồng hoạt động

```
┌──────────┐                    ┌──────────────────┐                    ┌──────────┐
│  User A   │                    │      Server       │                    │  User B   │
│ (sender)  │                    │   Socket.IO +     │                    │(receiver) │
│           │                    │   MongoDB         │                    │           │
└─────┬─────┘                    └────────┬──────────┘                    └─────┬─────┘
      │                                   │                                     │
      │  emit('sendMessage', {            │                                     │
      │    receiver: {_id: B},            │                                     │
      │    content: "Xin chào"            │                                     │
      │  })                               │                                     │
      │──────────────────────────────────►│                                     │
      │                                   │                                     │
      │                                   │  1. Xác minh sender từ session      │
      │                                   │  2. Mã hoá nội dung                 │
      │                                   │  3. Ghi Chat document               │
      │                                   │  4. Cập nhật NewestMessage          │
      │                                   │  5. Tìm socketId của B              │
      │                                   │     từ DB (users collection)        │
      │                                   │                                     │
      │  emit('receiveMessage', {         │                                     │
      │    sender, receiver,              │                                     │
      │    content: BẢN RÕ,              │                                     │
      │    refetch: true                  │                                     │
      │  })                               │                                     │
      │◄──────────────────────────────────│                                     │
      │                                   │                                     │
      │                                   │  emit('receiveMessage', {           │
      │                                   │    sender, receiver,                │
      │                                   │    content: BẢN RÕ,                │
      │                                   │    refetch: true                    │
      │                                   │  })                                 │
      │                                   │────────────────────────────────────►│
      │                                   │                                     │
```

#### Các vấn đề phát hiện

| # | Vấn đề | Chi tiết |
|---|--------|----------|
| 1 | **Lookup socketId từ DB mỗi tin nhắn** | Mỗi lần gửi tin, server truy vấn `User.get(receiver_id)` để lấy `socketId` (dòng 180). Đây là I/O tốn kém, đặc biệt khi chat tần suất cao. |
| 2 | **socketId lưu trong MongoDB** | `socketId` được lưu trực tiếp vào collection `users`. MongoDB không phải nơi lý tưởng cho dữ liệu tạm thời thay đổi liên tục (connect/disconnect). Gây write amplification. |
| 3 | **Không dùng Room của Socket.IO** | Thay vì dùng cơ chế Room có sẵn của Socket.IO (hiệu quả, có sẵn adapter Redis), server tự mapping socketId ↔ userId qua DB. |
| 4 | **Mất tin khi đang offline** | Nếu receiver không online (socketId = null), tin nhắn chỉ được lưu DB. Khi receiver online lại, KHÔNG có cơ chế push tin đã bỏ lỡ — phải đợi mở ChatModal để load từ REST. |
| 5 | **Không có typing indicator** | Không có sự kiện "đang nhập..." |
| 6 | **Không có trạng thái online/offline** | Không emit/track trạng thái online của user |
| 7 | **Không có "đã đọc/đã nhận"** | Thiếu delivery receipt và read receipt qua socket |

---

### 2.4 🔴 Thông báo Hệ thống (System Alerts) — KHÔNG tồn tại

**Mức độ nghiêm trọng: Cao**

Hiện tại **không có kênh nào** để server đẩy thông báo hệ thống tới client qua WebSocket:

- Bị xoá khỏi channel → chỉ ghi `Notification` vào DB (dòng `channels.py`), không push
- Bảo trì hệ thống → không có cơ chế broadcast
- Cập nhật chính sách → không có cơ chế broadcast
- Lỗi quan trọng → không có cơ chế thông báo

---

## 3. Bảng Tổng hợp Vấn đề

```
┌───────────────────────┬───────────────────┬──────────────┬──────────────────────────┐
│      Tính năng         │   Phương thức      │  Độ trễ       │    Vấn đề chính           │
│                        │   hiện tại         │  trung bình   │                           │
├───────────────────────┼───────────────────┼──────────────┼──────────────────────────┤
│ 💬 Chat (tin nhắn)    │ WebSocket          │ ~200-500ms   │ Lookup DB mỗi tin,       │
│                        │ (socket.io)        │              │ không dùng Room          │
├───────────────────────┼───────────────────┼──────────────┼──────────────────────────┤
│ 📋 Danh sách tin mới  │ WebSocket trigger  │ ~500-2000ms  │ Socket chỉ trigger       │
│    nhất (dropdown)     │ + REST refetch     │              │ REST refetch, chỉ hoạt   │
│                        │                    │              │ động khi ChatModal mở    │
├───────────────────────┼───────────────────┼──────────────┼──────────────────────────┤
│ 🔔 Thông báo          │ REST Polling       │ 0-60 giây    │ KHÔNG dùng WebSocket,    │
│    (chuông)            │ (60s interval)     │              │ polling thuần tuý        │
├───────────────────────┼───────────────────┼──────────────┼──────────────────────────┤
│ 📢 Thông báo hệ thống │ KHÔNG CÓ           │ ∞            │ Chưa triển khai          │
│                        │                    │              │                           │
├───────────────────────┼───────────────────┼──────────────┼──────────────────────────┤
│ 📞 Video Call          │ WebSocket          │ ~100-300ms   │ Hoạt động tốt, đã có    │
│                        │ (socket.io +       │              │ xác thực đầy đủ          │
│                        │  WebRTC signaling) │              │                           │
└───────────────────────┴───────────────────┴──────────────┴──────────────────────────┘
```

---

## 4. Sơ đồ So sánh: Hiện tại vs. Đề xuất

### 4.1 Hiện tại — Mô hình lai (Hybrid) với nhiều lỗ hổng

```
                            ┌─────────────────┐
                            │     CLIENT       │
                            │                  │
                    ┌───────┤  ChatModal       │
     WebSocket      │       │  (receiveMessage)│
     (socket.io)    │       ├──────────────────┤
    ────────────────┤       │  Notifications   │─── HTTP Polling ──► GET /api/notifications
                    │       │  (60s interval)  │                     (mỗi 60 giây)
                    │       ├──────────────────┤
                    │       │  Messages List   │─── HTTP REST ─────► GET /api/newest_messages
                    │       │  (triggered by   │                     (khi nhận socket event)
                    └───────┤   receiveMessage)│
                            ├──────────────────┤
                            │  System Alerts   │
                            │  ❌ KHÔNG CÓ     │
                            └─────────────────┘

     ⚠️ Vấn đề:
     • 3 phương thức khác nhau cho dữ liệu real-time
     • Notification hoàn toàn không real-time  
     • Messages list phụ thuộc vào ChatModal
     • Không có system alerts
```

### 4.2 Đề xuất — Mô hình WebSocket-First Thống nhất

```
                            ┌──────────────────┐
                            │      CLIENT       │
                            │                   │
                            │  SocketProvider   │
                            │  (kênh duy nhất)  │
                    ┌───────┤                   │
     WebSocket      │       │  ┌──────────────┐ │
     (socket.io)    │       │  │ Chat         │ │ ◄── on('receiveMessage')
    ────────────────┤       │  │ Messages     │ │ ◄── on('newConversation')
                    │       │  │ Notifications│ │ ◄── on('notification')     ← MỚI
                    │       │  │ System       │ │ ◄── on('systemAlert')      ← MỚI
                    │       │  │ Presence     │ │ ◄── on('userOnline/Offline')← MỚI
                    │       │  │ Typing       │ │ ◄── on('typing')           ← MỚI
                    └───────┤  └──────────────┘ │
                            └──────────────────┘

     ✅ Ưu điểm:
     • Một kênh duy nhất cho mọi dữ liệu real-time
     • Mọi thông báo tức thì (< 200ms)
     • Tiết kiệm băng thông (không cần polling)
     • Có presence & typing indicators
```

---

## 5. Đề xuất Cải tiến Chi tiết

### 5.1 🔴 Ưu tiên 1: Thông báo Real-time qua WebSocket

**Thay đổi server — Emit sự kiện khi tạo notification:**

```python
# === Cách tiếp cận: Tạo hàm helper dùng chung ===

# server_python/app/services/notify.py (FILE MỚI)
from app.models.notification import Notification
from app.models.user import User

async def create_and_push_notification(sio, *, user_id, seeder_id, code, params, url):
    """Tạo notification trong DB VÀ push qua WebSocket cùng lúc."""
    from app.messages import message_for

    notif = await Notification(
        user=user_id,
        seeder=seeder_id,
        code=code,
        params=params,
        notification=message_for(code, params),
        url=url,
    ).insert()

    # Push qua WebSocket nếu user đang online
    target_user = await User.get(user_id)
    if target_user and target_user.socketId:
        seeder = await User.get(seeder_id)
        await sio.emit("notification", {
            "_id": str(notif.id),
            "code": code,
            "params": params,
            "url": url,
            "seeder": {
                "_id": str(seeder_id),
                "username": seeder.username if seeder else None,
                "avatar": seeder.avatar if seeder else None,
            },
            "isRead": False,
            "created_at": notif.created_at.isoformat(),
        }, to=target_user.socketId)
```

**Thay đổi client — Lắng nghe event `notification` ở SocketProvider (luôn active):**

```javascript
// Thêm vào SocketProvider.jsx - luôn lắng nghe, không phụ thuộc ChatModal
useEffect(() => {
  if (!myId) return;
  
  const onNotification = (data) => {
    // Cập nhật badge count ngay lập tức
    setNotificationCount(prev => prev + 1);
    // Hiển thị toast thông báo
    showToast(data);
  };
  
  socket.on('notification', onNotification);
  return () => socket.off('notification', onNotification);
}, [myId]);
```

---

### 5.2 🔴 Ưu tiên 2: Cập nhật Message Badge không phụ thuộc ChatModal

**Vấn đề:** Listener `receiveMessage` chỉ hoạt động khi `ChatModal` đang mở.

**Giải pháp:** Di chuyển listener `receiveMessage` lên `SocketProvider` hoặc `App.jsx`:

```javascript
// Thêm vào SocketProvider.jsx (luôn active khi đã đăng nhập)
useEffect(() => {
  if (!myId) return;

  const onReceiveMessage = (message) => {
    // Luôn cập nhật badge tin nhắn, dù ChatModal có mở hay không
    refetchMessages();
  };

  socket.on('receiveMessage', onReceiveMessage);
  return () => socket.off('receiveMessage', onReceiveMessage);
}, [myId]);
```

---

### 5.3 🟡 Ưu tiên 3: Dùng Room thay vì Lookup DB

**Hiện tại:** Mỗi tin nhắn → query DB để lấy `socketId` → emit tới socketId đó.

**Đề xuất:** Dùng Socket.IO Room, mỗi user join room = user_id:

```python
# Khi connect thành công:
@sio.event
async def connect(sid, environ, auth=None):
    user_id = await _identify(auth, environ)
    sessions[sid] = user_id
    await sio.enter_room(sid, f"user:{user_id}")  # ← Join room

# Khi gửi tin nhắn - không cần query DB nữa:
await sio.emit("receiveMessage", payload, room=f"user:{receiver_id}")
await sio.emit("receiveMessage", payload, room=f"user:{sender_id}")
```

**Lợi ích:**
- Bỏ 2 truy vấn DB mỗi tin nhắn (`User.get` để tìm socketId)
- Tự động hỗ trợ multi-device (1 user nhiều tab/thiết bị → nhiều socket trong cùng room)
- Redis adapter đã hỗ trợ sẵn cross-process room

---

### 5.4 🟡 Ưu tiên 4: Bỏ lưu socketId vào MongoDB

**Hiện tại:**

```python
# joinChat → ghi socketId vào users collection
await User.find_one(User.id == ObjectId(user_id)).update({"$set": {"socketId": sid}})

# disconnect → xoá socketId
await User.find_one(User.socketId == sid).update({"$set": {"socketId": None}})
```

**Vấn đề:**
- `socketId` là dữ liệu tạm thời (ephemeral), thay đổi mỗi lần connect/disconnect
- Ghi vào MongoDB tạo write amplification cho một collection quan trọng (`users`)
- Nếu server crash, `socketId` cũ vẫn nằm trong DB → tin nhắn gửi tới socket đã chết

**Đề xuất:** Dùng dict in-memory (đã có `sessions`) hoặc Redis hash:

```python
# Thay vì ghi vào MongoDB, dùng sessions dict đã có sẵn:
sessions: dict[str, str] = {}     # sid → user_id  (ĐÃ CÓ)
user_sockets: dict[str, str] = {} # user_id → sid   (THÊM MỚI, reverse lookup)

# Hoặc dùng Redis cho multi-worker:
await redis.hset("user_sockets", user_id, sid)
await redis.hdel("user_sockets", user_id)
```

---

### 5.5 🟢 Ưu tiên 5: Thêm Typing Indicator & Online Presence

```python
# Server - thêm sự kiện typing
@sio.on("typing")
async def handle_typing(sid, data):
    user_id = user_of(sid)
    if not user_id:
        return
    receiver_id = (data or {}).get("receiver_id")
    if receiver_id:
        await sio.emit("typing", {
            "sender_id": user_id,
            "isTyping": data.get("isTyping", False)
        }, room=f"user:{receiver_id}")

# Server - online presence
@sio.event
async def connect(sid, environ, auth=None):
    user_id = await _identify(auth, environ)
    sessions[sid] = user_id
    await sio.enter_room(sid, f"user:{user_id}")
    # Broadcast online status
    await sio.emit("userOnline", {"userId": user_id})

@sio.event
async def disconnect(sid):
    user_id = sessions.pop(sid, None)
    if user_id:
        # Chỉ broadcast offline nếu user không còn socket nào khác
        remaining = [s for s, u in sessions.items() if u == user_id]
        if not remaining:
            await sio.emit("userOffline", {"userId": user_id})
```

---

### 5.6 🟢 Ưu tiên 6: System Broadcast Channel

```python
# Server - broadcast hệ thống
@sio.on("adminBroadcast")
async def handle_admin_broadcast(sid, data):
    user_id = user_of(sid)
    # Kiểm tra quyền admin
    user = await User.get(ObjectId(user_id))
    if not user or not user.role:
        return
    await sio.emit("systemAlert", {
        "type": data.get("type", "info"),      # info, warning, maintenance
        "message": data.get("message"),
        "action": data.get("action"),           # redirect, reload, none
        "expiresAt": data.get("expiresAt"),
    })  # Broadcast tới TẤT CẢ clients
```

---

## 6. Sơ đồ Kiến trúc Đề xuất (Sau Cải tiến)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TRÌNH DUYỆT (Client)                                │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                     SocketProvider (TRUNG TÂM)                              ││
│  │                                                                             ││
│  │  socket.on('receiveMessage')  → ChatModal + badge tin nhắn                  ││
│  │  socket.on('notification')    → badge chuông + toast                 ← MỚI ││
│  │  socket.on('newConversation') → cập nhật danh sách tin nhắn          ← MỚI ││
│  │  socket.on('systemAlert')     → banner / toast hệ thống             ← MỚI ││
│  │  socket.on('typing')          → indicator "đang nhập..."            ← MỚI ││
│  │  socket.on('userOnline')      → chấm xanh trên avatar              ← MỚI ││
│  │  socket.on('userOffline')     → xoá chấm xanh                      ← MỚI ││
│  │  socket.on('callUser')        → popup cuộc gọi đến                         ││
│  │  socket.on('callEnd')         → kết thúc cuộc gọi                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                           │                                     │
│                                    WebSocket (socket.io)                        │
│                                    Kênh duy nhất                                │
└───────────────────────────────────────────┼─────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼─────────────────────────────────────┐
│                        MÁY CHỦ (Python FastAPI)                                  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐    │
│  │                    Socket.IO AsyncServer                                 │    │
│  │                                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │    │
│  │  │  Chat Events     │  │  Notify Service  │  │  Presence Manager       │ │    │
│  │  │                  │  │                  │  │                          │ │    │
│  │  │  sendMessage     │  │  create_and_push │  │  Room: user:{id}        │ │    │
│  │  │  typing          │  │  _notification() │  │  → auto multi-device    │ │    │
│  │  │  joinChat (Room) │  │  systemAlert     │  │  → no DB lookup         │ │    │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────────────┘ │    │
│  └──────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                    ┌─────────────────┼──────────────────┐                        │
│                    ▼                 ▼                   ▼                        │
│             ┌───────────┐    ┌─────────────┐    ┌──────────────┐                 │
│             │  MongoDB   │    │    Redis     │    │   In-Memory  │                 │
│             │            │    │              │    │              │                 │
│             │ chats      │    │ pub/sub      │    │ sessions{}   │                 │
│             │ notifs     │    │ (cross-proc) │    │ user_rooms{} │                 │
│             │ users      │    │ user:socket  │    │              │                 │
│             │ (NO socket │    │   mapping    │    │              │                 │
│             │  Id field) │    │              │    │              │                 │
│             └───────────┘    └─────────────┘    └──────────────┘                 │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Lộ trình Triển khai Đề xuất

| Giai đoạn | Công việc | Ước lượng | Tác động |
|-----------|-----------|-----------|----------|
| **Phase 1** | Thêm `notification` event qua WebSocket + listener global trên client | 1-2 ngày | 🔴 Giải quyết vấn đề lớn nhất: thông báo tức thì |
| **Phase 2** | Di chuyển listener `receiveMessage` lên SocketProvider (global) | 0.5 ngày | 🔴 Badge tin nhắn luôn cập nhật |
| **Phase 3** | Chuyển sang dùng Socket.IO Room, bỏ lưu `socketId` vào MongoDB | 1 ngày | 🟡 Giảm tải DB, hỗ trợ multi-device |
| **Phase 4** | Thêm typing indicator + online presence | 1-2 ngày | 🟢 UX nâng cao |
| **Phase 5** | Thêm system broadcast channel | 0.5 ngày | 🟢 Admin tools |
| **Phase 6** | Bỏ hoàn toàn polling 60s cho notifications | 0.5 ngày | 🟢 Tiết kiệm tài nguyên |

**Tổng ước lượng: 5-7 ngày**

---

## 8. Kết luận

Hệ thống hiện tại có **WebSocket đã hoạt động tốt cho chat và video call**, nhưng có hai vấn đề thiết kế cốt lõi:

1. **Thông báo (notifications) hoàn toàn không dùng WebSocket** — chỉ dựa vào polling REST API mỗi 60 giây, tạo trải nghiệm không real-time.

2. **Danh sách tin nhắn chỉ cập nhật khi ChatModal mở** — listener `receiveMessage` bị gắn vào component thay vì ở tầng global, nên badge trên Header không phản ánh kịp thời.

Ngoài ra, việc **lưu `socketId` vào MongoDB** thay vì dùng Room/in-memory mapping tạo overhead không cần thiết và không hỗ trợ multi-device.

Bằng cách triển khai theo lộ trình đề xuất (ưu tiên Phase 1 & 2), hệ thống sẽ đạt real-time thực sự cho mọi loại thông báo chỉ trong **2-3 ngày đầu tiên**.
