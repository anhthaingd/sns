from bson import ObjectId

from app.models.channel import Channel
from app.models.shortcut import Shortcut


async def get_shortcuts(decoded_user: dict):
    try:
        user_id = ObjectId(decoded_user["_id"])
        shortcuts = await Shortcut.find({"user": user_id, "isJoin": True}).sort("count").to_list()

        shortcuts_list = []
        for s in shortcuts:
            d = {"_id": str(s.id), "user": str(s.user), "count": s.shortcut_count, "isJoin": s.isJoin}
            if s.channel:
                ch = await Channel.get(s.channel)
                if ch:
                    d["channel"] = {"_id": str(ch.id), "name": ch.name, "background": ch.background}
            shortcuts_list.append(d)

        return {"status": 200, "body": {"error": False, "success": True, "shortcuts": shortcuts_list}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def update_shortcut(decoded_user: dict, channel_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        channel_oid = ObjectId(channel_id)

        is_join = await Channel.find_one({"_id": channel_oid, "members": user_id})
        if is_join:
            existed = await Shortcut.find_one({"user": user_id, "channel": channel_oid})
            if existed:
                await Shortcut.find_one({"user": user_id, "channel": channel_oid}).update({"$inc": {"count": 1}})
                return {"status": 200, "body": {"error": False, "success": True}}

            await Shortcut(user=user_id, channel=channel_oid, count=1, isJoin=True).insert()
            return {"status": 200, "body": {"error": False, "success": True}}

        return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn chưa gia nhập channel này!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
