import json
import math

from app.errors import ApiError
from app.messages import message_for
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
        raise ApiError(403, code="channel.notJoined")
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
        raise ApiError(409, code="channel.exists")

    channel_data = {
        "name": name,
        "intro": intro,
        "members": [to_object_id(decoded_user["_id"], "user_id")],
    }
    if images:
        channel_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    await Channel(**channel_data).insert()
    return ok(code="channel.created")


async def join_channel(decoded_user: dict, channel_id: str):
    if is_admin(decoded_user):
        raise ApiError(403, code="channel.adminCannotLeave")

    user_id = to_object_id(decoded_user["_id"], "user_id")
    channel_oid = to_object_id(channel_id, "channel_id")
    channel = await Channel.get(channel_oid)
    if not channel:
        raise ApiError(404, code="channel.notFound")

    shortcut = await Shortcut.find_one({"user": user_id, "channel": channel_oid})
    if not shortcut:
        await Shortcut(channel=channel_oid, user=user_id, isJoin=True).insert()

    if user_id in channel.members:
        await Channel.find_one(Channel.id == channel_oid).update({"$pull": {"members": user_id}})
        await Shortcut.find_one({"user": user_id, "channel": channel_oid}).delete()
        return ok(code="channel.left")

    await Channel.find_one(Channel.id == channel_oid).update({"$push": {"members": user_id}})
    await Shortcut.find_one({"user": user_id, "channel": channel_oid}).update({"$set": {"isJoin": True}})
    return ok(code="channel.joined")


async def remove_user_from_channel(decoded_user: dict, channel_id: str, user_id_to_remove: str):
    require_admin(decoded_user)

    if user_id_to_remove == decoded_user["_id"]:
        raise ApiError(409, code="channel.cannotRemoveSelf")

    target_oid = to_object_id(user_id_to_remove, "userId")
    channel_oid = to_object_id(channel_id, "channel_id")

    target_user = await User.get(target_oid)
    if target_user and target_user.role:
        target_role = await Role.get(target_user.role)
        if target_role and target_role.value == 1:
            raise ApiError(403, code="channel.cannotRemoveOtherAdmin")

    channel = await Channel.find_one(Channel.id == channel_oid)
    await Channel.find_one(Channel.id == channel_oid).update({"$pull": {"members": target_oid}})
    await Shortcut.find_one({"user": target_oid, "channel": channel_oid}).update({"$set": {"isJoin": False}})

    if channel:
        await Notification(
            user=target_oid,
            seeder=to_object_id(decoded_user["_id"], "user_id"),
            code="notification.removedFromChannel",
            params={"channel": channel.name},
            notification=message_for("notification.removedFromChannel", {"channel": channel.name}),
            url=None,
        ).insert()

    return ok(code="channel.userRemoved")


async def update_channel(
    decoded_user: dict,
    channel_id: str,
    name: str = None,
    intro: str = None,
    old_background: str = None,
    files: dict = None,
    submitted: set[str] | None = None,
):
    require_admin(decoded_user)

    submitted = submitted if submitted is not None else {"name", "intro"}

    try:
        parse_old_image = json.loads(old_background) if old_background else None
    except json.JSONDecodeError as err:
        raise ApiError(400, code="channel.invalidOldBackground") from err

    # Chỉ ghi trường request thật sự gửi lên — cùng lý do đã ghi ở
    # `users.update_user`: gán vô điều kiện thì một request chỉ đổi ảnh bìa sẽ
    # ghi `name=None` và xoá trắng tên channel.
    update_data = {}
    for field_name, value in (("name", name), ("intro", intro)):
        if field_name in submitted:
            update_data[field_name] = value if value is not None else ""

    images = files.get("images", []) if files else []
    if images:
        if parse_old_image:
            await delete_file(parse_old_image.get("url", ""))
        update_data["background"] = {"name": images[0]["filename"], "url": images[0]["path"]}

    # `$set` rỗng bị Mongo từ chối, nên request không gửi trường nào thì coi như
    # không có gì để làm.
    if update_data:
        await Channel.find_one(Channel.id == to_object_id(channel_id, "channel_id")).update({"$set": update_data})
    return ok(code="channel.updated")


async def delete_channel(decoded_user: dict, channel_id: str):
    require_admin(decoded_user)

    channel_oid = to_object_id(channel_id, "channel_id")
    channel = await Channel.get(channel_oid)
    if not channel:
        raise ApiError(404, code="channel.notFound")

    # Dọn ảnh của MỌI bài viết trong channel trước khi xoá bản ghi: xoá xong
    # thì không còn đường nào lần ra những file đó nữa.
    posts = await Post.find(Post.channel == channel_oid).to_list()
    for post in posts:
        if post.images:
            await delete_file(post.images.get("url", ""))

    await channel.delete()
    await Post.find(Post.channel == channel_oid).delete()
    # `find` chứ không phải `find_one`: bản cũ chỉ chạm MỘT lối tắt, nên channel
    # có 30 người ghim thì 29 người vẫn thấy lối tắt trỏ vào channel đã xoá.
    await Shortcut.find({"channel": channel_oid}).update({"$set": {"isJoin": False}})
    if channel.background:
        await delete_file(channel.background.get("url", ""))
    return ok(code="channel.deleted")
