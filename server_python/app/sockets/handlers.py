"""Xử lý sự kiện thời gian thực: nhắn tin, gọi video, thông báo trạng thái.

Nguyên tắc
----------
1. **Kết nối phải mang access token.** Không có hoặc token sai -> từ chối
   ``connect`` luôn, chưa handler nào chạy.
2. **Danh tính lấy từ token, không bao giờ lấy từ payload.** ``sid`` -> ``user_id``
   được lưu ở phía máy chủ; ``sender._id`` client gửi lên chỉ còn giá trị tham
   khảo và bị ghi đè.
3. **Nội dung tin nhắn được mã hoá trước khi ghi DB** (``app/services/crypto.py``),
   và chỉ gửi bản rõ cho đúng hai người trong hội thoại.

Phase 3 — Room thay vì DB socketId
-----------------------------------
Trước đây mỗi ``joinChat`` / ``joinCall`` ghi ``socketId`` / ``socketCallId``
vào collection ``users`` trong MongoDB, rồi mỗi lần gửi tin lại query DB để
tìm socketId. Bây giờ:

* Mỗi user tự động join Room ``user:{user_id}`` ngay khi ``connect``.
* Emit tới room thay vì tới socketId cụ thể.
* Không ghi gì vào DB khi connect/disconnect.
* Multi-device tự động: một user mở nhiều tab -> nhiều socket cùng room.

Phase 4 — Typing indicator & Online presence
---------------------------------------------
* ``typing`` event cho phép hiện "đang nhập..." trong khung chat.
* ``online_users`` set theo dõi ai đang online; broadcast ``userOnline`` /
  ``userOffline`` khi thay đổi.

Phase 5 — System broadcast
---------------------------
* Admin có thể emit ``systemBroadcast`` -> server broadcast ``systemAlert``
  tới tất cả clients.
"""

import logging
from datetime import datetime

import jwt
from bson import ObjectId
from socketio.exceptions import ConnectionRefusedError

from app.models.chat import Chat
from app.models.newest_message import NewestMessage
from app.models.role import Role
from app.models.user import User
from app.services.crypto import encrypt_text
from app.services.token_store import is_revoked
from app.utils.token import decode_access_token

logger = logging.getLogger("fuurin.socket")

MAX_MESSAGE_LENGTH = 4000


def _extract_token(auth, environ) -> str | None:
    """Token có thể tới từ ``auth`` của socket.io hoặc header Authorization."""
    if isinstance(auth, dict):
        token = auth.get("token") or auth.get("accessToken")
        if token:
            return token.removeprefix("Bearer ").strip()
    header = (environ or {}).get("HTTP_AUTHORIZATION", "")
    if header:
        parts = header.split(" ")
        if len(parts) >= 2 and parts[1]:
            return parts[1]
    return None


async def _identify(auth, environ) -> str:
    """Trả về user_id từ access token, hoặc từ chối kết nối."""
    token = _extract_token(auth, environ)
    if not token:
        raise ConnectionRefusedError("Kết nối thời gian thực cần đăng nhập")
    try:
        decoded = decode_access_token(token)
    except jwt.PyJWTError as err:
        raise ConnectionRefusedError("Token không hợp lệ hoặc đã hết hạn") from err
    if await is_revoked(decoded.get("jti", "")):
        raise ConnectionRefusedError("Token đã bị thu hồi")
    user_id = decoded.get("_id")
    if not user_id:
        raise ConnectionRefusedError("Token thiếu danh tính người dùng")
    return str(user_id)


def register_handlers(sio):
    # ── Bảng tra in-memory ──────────────────────────────────────────────
    # Phase 3: Mọi thứ nằm trong RAM, KHÔNG ghi MongoDB.
    sessions: dict[str, str] = {}            # sid → user_id
    user_sockets: dict[str, set[str]] = {}   # user_id → {sid, ...}
    online_users: set[str] = set()           # Phase 4: tập user đang online

    def user_of(sid: str) -> str | None:
        return sessions.get(sid)

    # ── connect / disconnect ────────────────────────────────────────────

    @sio.event
    async def connect(sid, environ, auth=None):
        user_id = await _identify(auth, environ)
        sessions[sid] = user_id

        # Phase 3: Join Room thay vì ghi socketId vào DB.
        await sio.enter_room(sid, f"user:{user_id}")
        user_sockets.setdefault(user_id, set()).add(sid)

        # Phase 4: Online presence — broadcast nếu user vừa từ offline → online.
        was_offline = user_id not in online_users
        online_users.add(user_id)
        if was_offline:
            await sio.emit("userOnline", {"userId": user_id})

        logger.info("Socket %s đã xác thực cho user %s", sid, user_id)

    @sio.event
    async def disconnect(sid, _reason=None):
        user_id = sessions.pop(sid, None)
        if not user_id:
            logger.info("Client disconnected (unknown): %s", sid)
            return

        # Gỡ socket khỏi bảng tra; Room tự dọn khi socket ngắt.
        sockets = user_sockets.get(user_id, set())
        sockets.discard(sid)
        if not sockets:
            user_sockets.pop(user_id, None)
            # Phase 4: User không còn socket nào → offline.
            online_users.discard(user_id)
            await sio.emit("userOffline", {"userId": user_id})

        logger.info("Client disconnected: %s (user %s)", sid, user_id)

    # ── joinCall / joinChat — giờ là no-op ──────────────────────────────
    # Client vẫn emit hai event này (SocketProvider, ChatModal). Trước đây
    # chúng ghi socketId/socketCallId vào DB; giờ Room xử lý hết nên handler
    # chỉ cần tồn tại để không gây warning "unhandled event" trên console.

    @sio.on("joinCall")
    async def handle_join_call(sid, _payload=None):
        pass

    @sio.on("joinChat")
    async def handle_join_chat(sid, _payload=None):
        pass

    # ── Video call signaling ────────────────────────────────────────────
    # Phase 3: Emit tới Room thay vì query DB tìm socketCallId.

    @sio.on("callUser")
    async def handle_call_user(sid, data):
        if not user_of(sid):
            return
        receiver = (data or {}).get("receiver") or {}
        receiver_id = receiver.get("_id")
        if not receiver_id:
            return
        await sio.emit(
            "callUser",
            {"signal": (data or {}).get("signalData"), "from": (data or {}).get("seeder")},
            room=f"user:{receiver_id}",
        )

    @sio.on("answerCall")
    async def handle_answer_call(sid, data):
        if not user_of(sid):
            return
        to_user = (data or {}).get("to") or {}
        caller_id = to_user.get("_id")
        if not caller_id:
            return
        await sio.emit("callAccepted", (data or {}).get("signal"), room=f"user:{caller_id}")

    @sio.on("callEnd")
    async def handle_call_end(sid, data):
        sender_id = user_of(sid)
        if not sender_id:
            return
        receiver = (data or {}).get("receiver") or {}
        receiver_id = receiver.get("_id")
        if not receiver_id:
            return
        receiver_user = await User.get(ObjectId(receiver_id))
        await sio.emit(
            "callEnd",
            {
                "ended": True,
                "receiver": {
                    "_id": receiver_id,
                    "username": receiver_user.username if receiver_user else None,
                },
            },
            room=f"user:{receiver_id}",
        )

    # ── Chat ────────────────────────────────────────────────────────────

    @sio.on("sendMessage")
    async def handle_send_message(sid, data):
        sender_id_str = user_of(sid)
        if not sender_id_str:
            logger.warning("sendMessage từ socket chưa xác thực %s — bỏ qua", sid)
            return

        data = data or {}
        receiver = data.get("receiver") or {}
        if not receiver.get("_id"):
            return

        content = (data.get("content") or "").strip()[:MAX_MESSAGE_LENGTH]
        if not content:
            return

        sender_id = ObjectId(sender_id_str)
        try:
            receiver_id = ObjectId(receiver["_id"])
        except Exception:
            logger.warning("sendMessage có receiver._id không hợp lệ: %r", receiver.get("_id"))
            return
        if receiver_id == sender_id:
            return

        receiver_user = await User.get(receiver_id)
        if not receiver_user:
            return

        sealed = encrypt_text(content)
        await Chat(sender=sender_id, receiver=receiver_id, content=sealed).insert()

        existed_message = await NewestMessage.find_one(
            {
                "$or": [
                    {"sender.user": sender_id, "receiver.user": receiver_id},
                    {"sender.user": receiver_id, "receiver.user": sender_id},
                ]
            }
        )

        if not existed_message:
            await NewestMessage(
                sender={"user": sender_id, "isRead": True},
                receiver={"user": receiver_id, "isRead": False},
                content=sealed,
                lastSent=sender_id,
            ).insert()
        else:
            await NewestMessage.find_one(NewestMessage.id == existed_message.id).update(
                {
                    "$set": {
                        "sender.user": sender_id,
                        "sender.isRead": True,
                        "receiver.user": receiver_id,
                        "receiver.isRead": False,
                        "lastSent": sender_id,
                        "content": sealed,
                        "updated_at": datetime.utcnow(),
                    }
                }
            )

        sender_user = await User.get(sender_id)
        payload = {
            "sender": {"_id": str(sender_id), "username": sender_user.username if sender_user else None},
            "receiver": {"_id": str(receiver_id), "username": receiver_user.username},
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "refetch": True,
        }

        # Phase 3: Emit qua Room — tự động hỗ trợ multi-tab/multi-device.
        await sio.emit("receiveMessage", payload, room=f"user:{sender_id_str}")
        if str(receiver_id) != sender_id_str:
            await sio.emit("receiveMessage", payload, room=f"user:{str(receiver_id)}")

    # ── Phase 4: Typing indicator ──────────────────────────────────────

    @sio.on("typing")
    async def handle_typing(sid, data):
        user_id = user_of(sid)
        if not user_id:
            return
        data = data or {}
        receiver_id = data.get("receiverId")
        if not receiver_id:
            return
        await sio.emit(
            "typing",
            {"senderId": user_id, "isTyping": data.get("isTyping", False)},
            room=f"user:{receiver_id}",
        )

    # ── Phase 4: Online presence query ─────────────────────────────────

    @sio.on("getOnlineUsers")
    async def handle_get_online_users(sid, _data=None):
        """Client yêu cầu danh sách user đang online (dùng khi vừa kết nối)."""
        if not user_of(sid):
            return
        await sio.emit("onlineUsers", {"userIds": list(online_users)}, to=sid)

    # ── Phase 5: System broadcast (admin only) ─────────────────────────

    @sio.on("systemBroadcast")
    async def handle_system_broadcast(sid, data):
        user_id = user_of(sid)
        if not user_id:
            return
        user = await User.get(ObjectId(user_id))
        if not user or not user.role:
            logger.warning("systemBroadcast từ user không có role: %s", user_id)
            return
        role = await Role.get(user.role)
        if not role or role.value != 1:
            logger.warning("systemBroadcast từ user không phải admin: %s", user_id)
            return

        data = data or {}
        await sio.emit("systemAlert", {
            "type": data.get("type", "info"),
            "message": data.get("message", ""),
            "action": data.get("action"),
            "expiresAt": data.get("expiresAt"),
        })
        logger.info("Admin %s broadcast system alert: %s", user_id, data.get("type"))
