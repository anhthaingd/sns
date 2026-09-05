import json
import math

from app.errors import ApiError
from app.models.channel import Channel
from app.models.notification import Notification
from app.models.post import Post
from app.models.role import Role
from app.models.shortcut import Shortcut
from app.models.user import User
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id
from app.utils.loaders import load_roles_of, load_users, role_brief, user_brief
from app.utils.permissions import is_admin, require_admin
from app.utils.responses import ok
from app.utils.search import contains, normalize_search
from app.utils.serialization import serialize_doc

PAGE_SIZE = 10


async def _populate_channels(channels: list[Channel]) -> list[dict]:
    """Gắn thông tin thành viên cho CẢ TRANG channel bằng 2 truy vấn.

    Bản cũ gọi `User.get()` rồi `Role.get()` cho từng thành viên của từng
    channel: một channel 11 thành viên tốn 22 truy vấn, một trang 10 channel
    tốn hơn 200. Ở đây gom toàn bộ id thành viên của mọi channel lại, nạp user
    một lần rồi nạp role một lần.
    """
    if not channels:
        return []

    member_ids = [mid for ch in channels for mid in (ch.members or [])]
    user_map = await load_users(member_ids)
    role_map = await load_roles_of(user_map.values())

    result = []
    for ch in channels:
        data = serialize_doc(ch)
        members = []
        for mid in ch.members or []:
            user = user_map.get(str(mid))
            if user is None:
                continue
            member = user_brief(user)
            if user.role:
                member["role"] = role_brief(role_map.get(str(user.role)))
            members.append(member)
        data["members"] = members
        result.append(data)
    return result


async def get_all_channels(page: int = 1, search: str = None):
    query = {}
    keyword = normalize_search(search)
    if keyword:
        query["name"] = contains(keyword, unaccent=True)

    total_channels = await Channel.find(query).count()
    channels = await Channel.find(query).sort("-created_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()

    return ok(
        channels=await _populate_channels(channels),
        totalPage=math.ceil(total_channels / PAGE_SIZE) if total_channels > 0 else 1,
        curPage=page,
    )


async def get_channels_by_user(decoded_user: dict):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channels = await Channel.find({"members": user_id}).to_list()
    return ok(channels=await _populate_channels(channels))


async def get_channel_details(decoded_user: dict, channel_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channel = await Channel.find_one({"_id": to_object_id(channel_id, "channel_id"), "members": user_id})
    if not channel:
        raise ApiError(403, "Bạn chưa tham gia channel này!")
    populated = await _populate_channels([channel])
    return ok(channel=populated[0])


async def create_channel(decoded_user: dict, name: str, intro: str = None, files: dict = None):
    require_admin(decoded_user)

    existed = await Channel.find_one(Channel.name == name)
    images = files.get("images", []) if files else []
    if existed:
        # Ảnh đã được lưu xuống đĩa trước khi tới controller -> phải dọn, nếu
        # không mỗi lần trùng tên là một file rác nằm lại vĩnh viễn.
        if images:
            await delete_file(images[0].get("path", ""))
        raise ApiError(409, "Channel đã tồn tại!")

    channel_data = {
        "name": name,
        "intro": intro,
        "members": [to_object_id(decoded_user["_id"], "user_id")],
    }
    if images:
        channel_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Channel(**channel_data).insert()
    return ok(message="Tạo channel thành công!")


async def join_channel(decoded_user: dict, channel_id: str):
    if is_admin(decoded_user):
        raise ApiError(403, "Admin không thể tự ý rời khỏi nhóm!")

    user_id = to_object_id(decoded_user["_id"], "user_id")
    channel_oid = to_object_id(channel_id, "channel_id")
    channel = await Channel.get(channel_oid)
    if not channel:
        raise ApiError(404, "Channel không tồn tại!")

    shortcut = await Shortcut.find_one({"user": user_id, "channel": channel_oid})
    if not shortcut:
        await Shortcut(channel=channel_oid, user=user_id, isJoin=True).insert()

    if user_id in channel.members:
        await Channel.find_one(Channel.id == channel_oid).update({"$pull": {"members": user_id}})
        await Shortcut.find_one({"user": user_id, "channel": channel_oid}).delete()
        return ok(message="Bạn đã thoát nhóm channel!")

    await Channel.find_one(Channel.id == channel_oid).update({"$push": {"members": user_id}})
    await Shortcut.find_one({"user": user_id, "channel": channel_oid}).update({"$set": {"isJoin": True}})
    return ok(message="Gia nhập channel thành công!")


async def remove_user_from_channel(decoded_user: dict, channel_id: str, user_id_to_remove: str):
    require_admin(decoded_user)

    if user_id_to_remove == decoded_user["_id"]:
        raise ApiError(409, "Bạn không thể xóa chính mình ra khỏi channel!")

    target_oid = to_object_id(user_id_to_remove, "userId")
    channel_oid = to_object_id(channel_id, "channel_id")

    target_user = await User.get(target_oid)
    if target_user and target_user.role:
        target_role = await Role.get(target_user.role)
        if target_role and target_role.value == 1:
            raise ApiError(403, "Bạn không thể xóa admin khác ra khỏi nhóm!")

    channel = await Channel.find_one(Channel.id == channel_oid)
    await Channel.find_one(Channel.id == channel_oid).update({"$pull": {"members": target_oid}})
    await Shortcut.find_one({"user": target_oid, "channel": channel_oid}).update({"$set": {"isJoin": False}})

    if channel:
        await Notification(
            user=target_oid,
            seeder=to_object_id(decoded_user["_id"], "user_id"),
            notification=f"Admin đã xóa bạn ra khỏi channel {channel.name}!",
            url=None,
        ).insert()

    return ok(message=f"Đã xóa người dùng id:{user_id_to_remove} ra khỏi channel!")


async def update_channel(
    decoded_user: dict,
    channel_id: str,
    name: str = None,
    intro: str = None,
    old_background: str = None,
    files: dict = None,
):
    require_admin(decoded_user)

    try:
        parse_old_image = json.loads(old_background) if old_background else None
    except json.JSONDecodeError as err:
        raise ApiError(400, "Dữ liệu ảnh nền cũ không hợp lệ!") from err

    update_data = {"name": name, "intro": intro}

    images = files.get("images", []) if files else []
    if images:
        if parse_old_image:
            await delete_file(parse_old_image.get("url", ""))
        update_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Channel.find_one(Channel.id == to_object_id(channel_id, "channel_id")).update({"$set": update_data})
    return ok(message="Cập nhật channel thành công!")


async def delete_channel(decoded_user: dict, channel_id: str):
    require_admin(decoded_user)

    channel_oid = to_object_id(channel_id, "channel_id")
    channel = await Channel.get(channel_oid)
    if not channel:
        raise ApiError(404, "Channel không tồn tại!")

    await channel.delete()
    await Post.find(Post.channel == channel_oid).delete()
    await Shortcut.find_one({"channel": channel_oid}).update({"$set": {"isJoin": False}})
    if channel.background:
        await delete_file(channel.background.get("url", ""))
    return ok(message="Xóa channel thành công!")
