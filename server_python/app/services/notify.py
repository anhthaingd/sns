"""Tạo thông báo trong DB VÀ đẩy qua WebSocket cùng lúc.

Trước đây các controller (posts, follows, channels) chỉ ghi ``Notification``
vào MongoDB. Client phải polling REST API ``GET /api/notifications`` mỗi 60
giây để biết — trễ tối đa một phút, tốn băng thông, và không giống real-time.

Module này bọc cả hai bước — ghi DB lẫn emit socket — vào một hàm duy nhất.
Nếu người nhận đang online, họ thấy thông báo NGAY qua sự kiện ``notification``
trên WebSocket, không cần đợi polling.

Phase 3: emit qua Room ``user:{user_id}`` thay vì query DB tìm ``socketId``.
Nếu room rỗng (user offline) thì emit là no-op — không tốn truy vấn nào.
"""

import logging

from bson import ObjectId

from app.messages import message_for
from app.models.notification import Notification
from app.models.user import User
from app.sockets import get_sio

logger = logging.getLogger("fuurin.notify")


async def create_and_push(
    *,
    user_id: ObjectId,
    seeder_id: ObjectId,
    code: str,
    params: dict | None = None,
    url: str | None = None,
) -> Notification:
    """Tạo notification trong DB và push qua WebSocket nếu user đang online.

    Parameters
    ----------
    user_id : ObjectId
        Người NHẬN thông báo.
    seeder_id : ObjectId
        Người GÂY RA hành động (like, comment, follow, ...).
    code : str
        Mã thông báo từ ``app/messages.py`` (ví dụ ``notification.postLiked``).
    params : dict, optional
        Tham số cho bản dịch (ví dụ ``{"username": "An"}``)
    url : str, optional
        Đường dẫn tương đối khi bấm vào thông báo.

    Returns
    -------
    Notification
        Document vừa ghi vào DB.
    """
    params = params or {}

    notif = await Notification(
        user=user_id,
        seeder=seeder_id,
        code=code,
        params=params,
        notification=message_for(code, params),
        url=url,
    ).insert()

    sio = get_sio()
    if sio is None:
        logger.warning("sio chưa khởi tạo — không push được notification %s", code)
        return notif

    seeder = await User.get(seeder_id)
    payload = {
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
        "created_at": notif.created_at.isoformat() if notif.created_at else None,
    }

    try:
        # Phase 3: Emit qua Room — nếu user offline thì room rỗng và emit là
        # no-op. Không cần query DB để kiểm tra socketId nữa.
        await sio.emit("notification", payload, room=f"user:{str(user_id)}")
        logger.info("Pushed notification %s tới user %s", code, user_id)
    except Exception:
        logger.exception("Không emit được notification %s tới user %s", code, user_id)

    return notif
