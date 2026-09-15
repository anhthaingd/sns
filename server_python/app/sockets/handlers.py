"""Xử lý sự kiện thời gian thực: nhắn tin và gọi video.

Bản trước KHÔNG xác thực gì cả
------------------------------
Mọi handler đều tin thẳng `_id` do client tự khai trong payload. Hệ quả đã tái
hiện được bằng `curl` (không cần trình duyệt, không cần đăng nhập):

* `sendMessage` với `sender._id` là id người khác -> tin nhắn được ghi vào DB
  dưới tên người đó. Mạo danh hoàn toàn.
* `joinChat` với `_id` người khác -> `socketId` của họ bị trỏ về socket của kẻ
  tấn công, tức là cướp luôn đường nhận tin nhắn của họ.

Nguyên tắc bây giờ
------------------
1. **Kết nối phải mang access token.** Không có hoặc token sai -> từ chối
   `connect` luôn, chưa handler nào chạy.
2. **Danh tính lấy từ token, không bao giờ lấy từ payload.** `sid` -> `user_id`
   được lưu ở phía máy chủ; `sender._id` client gửi lên chỉ còn giá trị tham
   khảo và bị ghi đè.
3. **Nội dung tin nhắn được mã hoá trước khi ghi DB** (`app/services/crypto.py`),
   và chỉ gửi bản rõ cho đúng hai người trong hội thoại.
"""

import logging
from datetime import datetime

import jwt
from bson import ObjectId
from socketio.exceptions import ConnectionRefusedError

from app.models.chat import Chat
from app.models.newest_message import NewestMessage
from app.models.user import User
from app.services.crypto import encrypt_text
from app.services.token_store import is_revoked
from app.utils.token import decode_access_token

logger = logging.getLogger("fuurin.socket")

# Nội dung tin nhắn dài hơn mức này bị cắt. Không có giới hạn thì một client
# viết bậy có thể đẩy hàng MB vào mỗi document.
MAX_MESSAGE_LENGTH = 4000


def _extract_token(auth, environ) -> str | None:
    """Token có thể tới từ `auth` của socket.io hoặc header Authorization."""
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
    # sid -> user_id. Nguồn sự thật DUY NHẤT về "socket này là của ai".
    # Không bao giờ đọc danh tính từ payload client gửi lên.
    sessions: dict[str, str] = {}

    def user_of(sid: str) -> str | None:
        return sessions.get(sid)

    @sio.event
    async def connect(sid, environ, auth=None):
        user_id = await _identify(auth, environ)
        sessions[sid] = user_id
        logger.info("Socket %s đã xác thực cho user %s", sid, user_id)

    @sio.on("joinCall")
    async def handle_join_call(sid, _payload=None):
        # `_payload` client gửi lên bị bỏ qua hoàn toàn: danh tính lấy từ phiên.
        user_id = user_of(sid)
        if not user_id:
            return
        await User.find_one(User.id == ObjectId(user_id)).update({"$set": {"socketCallId": sid}})

    @sio.on("callUser")
    async def handle_call_user(sid, data):
        if not user_of(sid):
            return
        receiver = (data or {}).get("receiver") or {}
        if not receiver.get("_id"):
            return
        receiver_user = await User.get(ObjectId(receiver["_id"]))
        if receiver_user and receiver_user.socketCallId:
            await sio.emit(
                "callUser",
                {"signal": (data or {}).get("signalData"), "from": (data or {}).get("seeder")},
                to=receiver_user.socketCallId,
            )

    @sio.on("answerCall")
    async def handle_answer_call(sid, data):
        if not user_of(sid):
            return
        to_user = (data or {}).get("to") or {}
        if not to_user.get("_id"):
            return
        receiver_user = await User.get(ObjectId(to_user["_id"]))
        if receiver_user and receiver_user.socketCallId:
            await sio.emit("callAccepted", (data or {}).get("signal"), to=receiver_user.socketCallId)

    @sio.on("callEnd")
    async def handle_call_end(sid, data):
        if not user_of(sid):
            return
        receiver = (data or {}).get("receiver") or {}
        if not receiver.get("_id"):
            return
        receiver_user = await User.get(ObjectId(receiver["_id"]))
        if receiver_user and receiver_user.socketCallId:
            # `ended: True` là thứ client thật sự cần để biết cuộc gọi đã dừng.
            # Bản cũ gửi `{"receiver": {...}}` còn client lại kiểm
            # `data.receiver.socketCallId` — một trường chưa bao giờ được gửi —
            # nên phía người nhận không bao giờ biết cuộc gọi đã kết thúc.
            await sio.emit(
                "callEnd",
                {
                    "ended": True,
                    "receiver": {"_id": str(receiver_user.id), "username": receiver_user.username},
                },
                to=receiver_user.socketCallId,
            )

    @sio.on("joinChat")
    async def handle_join_chat(sid, _payload=None):
        user_id = user_of(sid)
        if not user_id:
            return
        await User.find_one(User.id == ObjectId(user_id)).update({"$set": {"socketId": sid}})

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

        # Người gửi LUÔN là chủ của socket này, kể cả khi payload khai người
        # khác. `lastSent` client gửi lên cũng bị bỏ qua vì lý do tương tự.
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

        # Bản mã đi vào DB; bản rõ chỉ đi tới đúng hai người trong hội thoại.
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
            # Dù bản ghi cũ để ai ở vế "sender", người vừa gửi luôn được đưa về
            # vế đã đọc, người kia về vế chưa đọc.
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

        await sio.emit("receiveMessage", payload, to=sid)
        if receiver_user.socketId and receiver_user.socketId != sid:
            await sio.emit("receiveMessage", payload, to=receiver_user.socketId)

    @sio.event
    async def disconnect(sid, _reason=None):
        sessions.pop(sid, None)
        # Dọn cả hai trường: bản cũ chỉ xoá `socketId`, nên `socketCallId` cứ
        # trỏ mãi vào một socket đã chết và cuộc gọi tới người đó rơi vào hư vô.
        await User.find_one(User.socketId == sid).update({"$set": {"socketId": None}})
        await User.find_one(User.socketCallId == sid).update({"$set": {"socketCallId": None}})
        logger.info("Client disconnected: %s", sid)
