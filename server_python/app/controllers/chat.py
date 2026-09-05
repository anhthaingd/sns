import math
from bson import ObjectId

from app.models.chat import Chat
from app.models.newest_message import NewestMessage
from app.models.user import User


async def _populate_user_brief(user_id):
    u = await User.get(user_id)
    if u:
        return {"_id": str(u.id), "username": u.username, "email": u.email, "avatar": u.avatar, "cover_bg": u.cover_bg}
    return None


async def get_chat(sender_id: str, receiver_id: str, page: int = 1):
    try:
        s_oid = ObjectId(sender_id)
        r_oid = ObjectId(receiver_id)
        query = {
            "$or": [
                {"sender": s_oid, "receiver": r_oid},
                {"sender": r_oid, "receiver": s_oid},
            ]
        }
        total_messages = await Chat.find(query).count()
        messages = await Chat.find(query).sort("-timestamp").to_list()

        messages_list = []
        for m in messages:
            d = {
                "_id": str(m.id),
                "content": m.content,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "read_at": m.read_at.isoformat() if m.read_at else None,
            }
            d["sender"] = await _populate_user_brief(m.sender)
            d["receiver"] = await _populate_user_brief(m.receiver)
            messages_list.append(d)

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "messages": messages_list,
                "totalPage": math.ceil(total_messages / 20) if total_messages > 0 else 1,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_newest_message(decoded_user: dict):
    try:
        user_id = ObjectId(decoded_user["_id"])
        total_unread = await NewestMessage.find({
            "$or": [
                {"sender.user": user_id, "sender.isRead": False},
                {"receiver.user": user_id, "receiver.isRead": False},
            ]
        }).count()

        messages = await NewestMessage.find({
            "$or": [
                {"sender.user": user_id},
                {"receiver.user": user_id},
            ]
        }).sort("-updated_at").to_list()

        messages_list = []
        for m in messages:
            d = {
                "_id": str(m.id),
                "content": m.content,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                "lastSent": str(m.lastSent) if m.lastSent else None,
            }
            if m.sender:
                sender_user = await User.get(m.sender.get("user")) if m.sender.get("user") else None
                d["sender"] = {
                    "user": {"_id": str(sender_user.id), "username": sender_user.username, "email": sender_user.email, "avatar": sender_user.avatar, "cover_bg": sender_user.cover_bg} if sender_user else None,
                    "isRead": m.sender.get("isRead", False),
                }
            if m.receiver:
                receiver_user = await User.get(m.receiver.get("user")) if m.receiver.get("user") else None
                d["receiver"] = {
                    "user": {"_id": str(receiver_user.id), "username": receiver_user.username, "email": receiver_user.email, "avatar": receiver_user.avatar, "cover_bg": receiver_user.cover_bg} if receiver_user else None,
                    "isRead": m.receiver.get("isRead", False),
                }
            messages_list.append(d)

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "messages": messages_list,
                "unread": total_unread,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def read_message(decoded_user: dict, message_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        msg = await NewestMessage.find_one({
            "_id": ObjectId(message_id),
            "$or": [
                {"sender.user": user_id},
                {"receiver.user": user_id},
            ],
        })
        if not msg:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Message not found"}}

        if msg.sender and msg.sender.get("user") == user_id:
            await NewestMessage.find_one(NewestMessage.id == ObjectId(message_id)).update({"$set": {"sender.isRead": True}})
            return {"status": 200, "body": {"error": False, "success": True}}

        if msg.receiver and msg.receiver.get("user") == user_id:
            await NewestMessage.find_one(NewestMessage.id == ObjectId(message_id)).update({"$set": {"receiver.isRead": True}})
            return {"status": 200, "body": {"error": False, "success": True}}

        return {"status": 200, "body": {"error": False, "success": True}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
