from app.errors import ApiError
from app.models.channel import Channel
from app.models.shortcut import Shortcut
from app.utils.ids import to_object_id
from app.utils.loaders import load_channels
from app.utils.responses import ok


async def get_shortcuts(decoded_user: dict):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    # `-count`: channel vào NHIỀU nhất lên đầu. Bản cũ sort tăng dần (chép
    # nguyên `.sort({ count: 1 })` của code Node cũ) nên channel ít vào nhất
    # lại được ghim lên trên — ngược hẳn ý nghĩa của "lối tắt".
    # Tên trường ở đây là tên trong DB ("count"), không phải tên thuộc tính
    # Python (`shortcut_count`) — xem alias trong app/models/shortcut.py.
    shortcuts = await Shortcut.find({"user": user_id, "isJoin": True}).sort("-count").to_list()

    # Một truy vấn cho toàn bộ channel của mọi shortcut thay vì `Channel.get()`
    # trong vòng lặp.
    channel_map = await load_channels([s.channel for s in shortcuts])

    shortcuts_list = []
    for s in shortcuts:
        d = {"_id": str(s.id), "user": str(s.user), "count": s.shortcut_count, "isJoin": s.isJoin}
        channel = channel_map.get(str(s.channel)) if s.channel else None
        if channel:
            d["channel"] = {"_id": str(channel.id), "name": channel.name, "background": channel.background}
        shortcuts_list.append(d)

    return ok(shortcuts=shortcuts_list)


async def update_shortcut(decoded_user: dict, channel_id: str):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    channel_oid = to_object_id(channel_id, "channel_id")

    is_join = await Channel.find_one({"_id": channel_oid, "members": user_id})
    if not is_join:
        raise ApiError(403, code="channel.notJoinedShortcut")

    existed = await Shortcut.find_one({"user": user_id, "channel": channel_oid})
    if existed:
        await Shortcut.find_one({"user": user_id, "channel": channel_oid}).update({"$inc": {"count": 1}})
    else:
        await Shortcut(user=user_id, channel=channel_oid, count=1, isJoin=True).insert()
    return ok()
