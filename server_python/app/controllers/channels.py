import json
import math
from bson import ObjectId
from unidecode import unidecode

from app.models.channel import Channel
from app.models.post import Post
from app.models.shortcut import Shortcut
from app.models.notification import Notification
from app.models.user import User
from app.models.role import Role
from app.utils.file_utils import delete_file
from app.utils.serialization import serialize_doc



async def _populate_members(channel):
    d = serialize_doc(channel)
    members = []
    for mid in channel.members:
        u = await User.get(mid)
        if u:
            m = {"_id": str(u.id), "username": u.username, "email": u.email, "avatar": u.avatar}
            if u.role:
                role = await Role.get(u.role)
                m["role"] = serialize_doc(role) if role else None
            members.append(m)
    d["members"] = members
    return d


async def get_all_channels(page: int = 1, search: str = None):
    try:
        query = {}
        if search and search != "null" and search.strip():
            unaccented = unidecode(search)
            query["name"] = {"$regex": unaccented, "$options": "i"}

        total_channels = await Channel.find(query).count()
        channels = await Channel.find(query).sort("-created_at").skip((page - 1) * 10).limit(10).to_list()
        channels_list = []
        for ch in channels:
            channels_list.append(await _populate_members(ch))

        return {
            "status": 200,
            "body": {
                "error": False,
                "success": True,
                "channels": channels_list,
                "totalPage": math.ceil(total_channels / 10) if total_channels > 0 else 1,
                "curPage": page,
            },
        }
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_channels_by_user(decoded_user: dict):
    try:
        user_id = ObjectId(decoded_user["_id"])
        channels = await Channel.find({"members": user_id}).to_list()
        channels_list = []
        for ch in channels:
            channels_list.append(await _populate_members(ch))
        return {"status": 200, "body": {"error": False, "success": True, "channels": channels_list}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def get_channel_details(decoded_user: dict, channel_id: str):
    try:
        user_id = ObjectId(decoded_user["_id"])
        channel = await Channel.find_one({"_id": ObjectId(channel_id), "members": user_id})
        if channel:
            channel_data = await _populate_members(channel)
            return {"status": 200, "body": {"error": False, "success": True, "channel": channel_data}}
        return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn chưa tham gia channel này!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def create_channel(decoded_user: dict, name: str, intro: str = None, files: dict = None):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Chức năng này chỉ dành cho admin!"}}

        existed = await Channel.find_one(Channel.name == name)
        images = files.get("images", []) if files else []
        if existed:
            if images:
                await delete_file(images[0].get("path", ""))
            return {"status": 409, "body": {"error": True, "success": False, "message": "Channel đã tồn tại!"}}

        channel_data = {"name": name, "intro": intro, "members": [ObjectId(decoded_user["_id"])]}
        if images:
            channel_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

        channel = Channel(**channel_data)
        await channel.insert()
        return {"status": 201, "body": {"error": False, "success": True, "message": "Tạo channel thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def join_channel(decoded_user: dict, channel_id: str):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value == 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Admin không thể tự ý rời khỏi nhóm!"}}

        user_id = ObjectId(decoded_user["_id"])
        channel = await Channel.get(ObjectId(channel_id))
        if not channel:
            return {"status": 404, "body": {"error": True, "success": False, "message": "Channel không tồn tại!"}}

        shortcut = await Shortcut.find_one({"user": user_id, "channel": ObjectId(channel_id)})
        if not shortcut:
            await Shortcut(channel=ObjectId(channel_id), user=user_id, isJoin=True).insert()

        if user_id in channel.members:
            await Channel.find_one(Channel.id == ObjectId(channel_id)).update({"$pull": {"members": user_id}})
            await Shortcut.find_one({"user": user_id, "channel": ObjectId(channel_id)}).delete()
            return {"status": 200, "body": {"error": False, "success": True, "message": "Bạn đã thoát nhóm channel!"}}

        await Channel.find_one(Channel.id == ObjectId(channel_id)).update({"$push": {"members": user_id}})
        await Shortcut.find_one({"user": user_id, "channel": ObjectId(channel_id)}).update({"$set": {"isJoin": True}})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Gia nhập channel thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def remove_user_from_channel(decoded_user: dict, channel_id: str, user_id_to_remove: str):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Chức năng này chỉ dành cho admin!"}}

        if user_id_to_remove == decoded_user["_id"]:
            return {"status": 409, "body": {"error": True, "success": False, "message": "Bạn không thể xóa chính mình ra khỏi channel!"}}

        target_user = await User.get(ObjectId(user_id_to_remove))
        if target_user and target_user.role:
            target_role = await Role.get(target_user.role)
            if target_role and target_role.value == 1:
                return {"status": 403, "body": {"error": True, "success": False, "message": "Bạn không thể xóa admin khác ra khỏi nhóm!"}}

        target_oid = ObjectId(user_id_to_remove)
        channel = await Channel.find_one(Channel.id == ObjectId(channel_id))
        await Channel.find_one(Channel.id == ObjectId(channel_id)).update({"$pull": {"members": target_oid}})
        await Shortcut.find_one({"user": target_oid, "channel": ObjectId(channel_id)}).update({"$set": {"isJoin": False}})

        if channel:
            await Notification(
                user=target_oid,
                seeder=ObjectId(decoded_user["_id"]),
                notification=f"Admin đã xóa bạn ra khỏi channel {channel.name}!",
                url=None,
            ).insert()

        return {"status": 200, "body": {"error": False, "success": True, "message": f"Đã xóa người dùng id:{user_id_to_remove} ra khỏi channel!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def update_channel(decoded_user: dict, channel_id: str, name: str = None, intro: str = None, old_background: str = None, files: dict = None):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Chức năng này chỉ dành cho admin!"}}

        parse_old_image = json.loads(old_background) if old_background else None
        update_data = {"name": name, "intro": intro}

        images = files.get("images", []) if files else []
        if images:
            if parse_old_image:
                await delete_file(parse_old_image.get("url", ""))
            update_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

        await Channel.find_one(Channel.id == ObjectId(channel_id)).update({"$set": update_data})
        return {"status": 200, "body": {"error": False, "success": True, "message": "Cập nhật channel thành công!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}


async def delete_channel(decoded_user: dict, channel_id: str):
    try:
        role_data = decoded_user.get("role")
        role_value = role_data.get("value", 0) if isinstance(role_data, dict) else 0
        if role_value != 1:
            return {"status": 403, "body": {"error": True, "success": False, "message": "Chức năng này chỉ dành cho admin!"}}

        channel = await Channel.get(ObjectId(channel_id))
        if channel:
            await channel.delete()
            await Post.find(Post.channel == ObjectId(channel_id)).delete()
            await Shortcut.find_one({"channel": ObjectId(channel_id)}).update({"$set": {"isJoin": False}})
            if channel.background:
                await delete_file(channel.background.get("url", ""))
            return {"status": 200, "body": {"error": False, "success": True, "message": "Xóa channel thành công!"}}

        return {"status": 404, "body": {"error": True, "success": False, "message": "Channel không tồn tại!"}}
    except Exception as e:
        return {"status": 500, "body": {"error": True, "success": False, "message": str(e)}}
