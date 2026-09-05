import math

from app.errors import ApiError
from app.models.chat import Chat
from app.models.newest_message import NewestMessage
from app.utils.ids import to_object_id
from app.utils.loaders import load_users, user_brief_with_cover
from app.utils.responses import ok

PAGE_SIZE = 20


async def get_chat(sender_id: str, receiver_id: str, page: int = 1):
    """Lịch sử hội thoại, phân trang từ mới về cũ nhưng TRẢ VỀ theo thứ tự cũ -> mới.

    Hai điểm sửa so với bản đầu:
    1. `page` trước đây bị bỏ qua hoàn toàn -> mỗi lần mở khung chat là tải về
       toàn bộ lịch sử (hội thoại 500 tin = payload vài MB).
    2. Backend sort `-timestamp` còn client render thẳng từ trên xuống, nên
       lịch sử hiển thị NGƯỢC trong khi tin mới qua socket lại nối xuống dưới.
       Phải phân trang trên thứ tự mới-nhất-trước (để trang 1 là 20 tin gần
       nhất) rồi đảo lại trước khi trả về.
    """
    s_oid = to_object_id(sender_id, "sender_id")
    r_oid = to_object_id(receiver_id, "receiver_id")
    query = {
        "$or": [
            {"sender": s_oid, "receiver": r_oid},
            {"sender": r_oid, "receiver": s_oid},
        ]
    }
    total_messages = await Chat.find(query).count()
    messages = await Chat.find(query).sort("-timestamp").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    messages.reverse()

    # Hội thoại chỉ có 2 người -> đúng một truy vấn users cho cả trang.
    user_map = await load_users([s_oid, r_oid])

    messages_list = [
        {
            "_id": str(m.id),
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "read_at": m.read_at.isoformat() if m.read_at else None,
            "sender": user_brief_with_cover(user_map.get(str(m.sender))),
            "receiver": user_brief_with_cover(user_map.get(str(m.receiver))),
        }
        for m in messages
    ]

    return ok(
        messages=messages_list,
        totalPage=math.ceil(total_messages / PAGE_SIZE) if total_messages > 0 else 1,
        curPage=page,
    )


def _participant(side: dict | None, user_map) -> dict | None:
    if not side:
        return None
    return {
        "user": user_brief_with_cover(user_map.get(str(side.get("user")))) if side.get("user") else None,
        "isRead": side.get("isRead", False),
    }


async def get_newest_message(decoded_user: dict):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    total_unread = await NewestMessage.find(
        {
            "$or": [
                {"sender.user": user_id, "sender.isRead": False},
                {"receiver.user": user_id, "receiver.isRead": False},
            ]
        }
    ).count()

    messages = (
        await NewestMessage.find(
            {
                "$or": [
                    {"sender.user": user_id},
                    {"receiver.user": user_id},
                ]
            }
        )
        .sort("-updated_at")
        .to_list()
    )

    # Gom id của cả hai phía trong mọi hội thoại -> một truy vấn users duy nhất
    # (trước đây là 2 truy vấn cho mỗi hội thoại).
    participant_ids = []
    for m in messages:
        for side in (m.sender, m.receiver):
            if side and side.get("user"):
                participant_ids.append(side["user"])
    user_map = await load_users(participant_ids)

    messages_list = []
    for m in messages:
        d = {
            "_id": str(m.id),
            "content": m.content,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            "lastSent": str(m.lastSent) if m.lastSent else None,
        }
        if m.sender:
            d["sender"] = _participant(m.sender, user_map)
        if m.receiver:
            d["receiver"] = _participant(m.receiver, user_map)
        messages_list.append(d)

    return ok(messages=messages_list, unread=total_unread)


async def read_message(decoded_user: dict, message_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    message_oid = to_object_id(message_id, "message_id")
    msg = await NewestMessage.find_one(
        {
            "_id": message_oid,
            "$or": [
                {"sender.user": user_id},
                {"receiver.user": user_id},
            ],
        }
    )
    if not msg:
        raise ApiError(404, "Không tìm thấy hội thoại!")

    if msg.sender and msg.sender.get("user") == user_id:
        await NewestMessage.find_one(NewestMessage.id == message_oid).update({"$set": {"sender.isRead": True}})
    elif msg.receiver and msg.receiver.get("user") == user_id:
        await NewestMessage.find_one(NewestMessage.id == message_oid).update({"$set": {"receiver.isRead": True}})

    return ok()
