"""Hồ sơ người dùng: xem, sửa, tìm kiếm và danh sách cho quản trị."""

import logging

import bcrypt as _bcrypt

from app.controllers.user_common import (
    PAGE_SIZE,
    hash_password,
    parse_json,
    populate_followers,
    populate_following,
    populate_role,
    total_page,
)
from app.errors import ApiError
from app.models.channel import Channel
from app.models.post import Post
from app.models.role import Role
from app.models.user import User
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id
from app.utils.loaders import role_brief
from app.utils.permissions import NOT_ENOUGH_PERMISSION_MESSAGE, require_admin
from app.utils.responses import ok
from app.utils.search import contains, normalize_search

logger = logging.getLogger("fuurin.users")


async def get_user_by_token(decoded_user: dict):
    user = await User.find_one(User.email == decoded_user["email"])
    if not user:
        raise ApiError(404, code="user.notFound")
    return ok(
        user=await populate_role(user),
        followers=await populate_followers(decoded_user["_id"]),
        following=await populate_following(decoded_user["_id"]),
    )


async def get_user_details(user_id: str):
    oid = to_object_id(user_id, "user_id")
    user = await User.get(oid)
    if not user:
        raise ApiError(404, code="user.notFound")

    user_data = {
        "_id": str(user.id),
        "avatar": user.avatar,
        "cover_bg": user.cover_bg,
        "username": user.username,
        "email": user.email,
        "intro": user.intro,
        "address": user.address,
    }
    if user.role:
        user_data["role"] = role_brief(await Role.get(user.role))

    return ok(
        user=user_data,
        followers=await populate_followers(user_id),
        following=await populate_following(user_id),
        posts=await Post.find(Post.user == oid).count(),
        channels=await Channel.find({"members": oid}).count(),
    )


async def update_user(
    user_id: str,
    decoded_user: dict,
    # Tên các field có mặt trong form. Xem chỗ dựng `update_data` bên dưới để
    # biết vì sao không thể suy ra từ giá trị.
    submitted: set[str] | None = None,
    username: str = None,
    old_password: str = None,
    new_password: str = None,
    address: str = None,
    intro: str = None,
    old_avatar: str = None,
    old_cover_bg: str = None,
    update_images: str = None,
    files: dict = None,
):
    from datetime import datetime

    submitted = submitted if submitted is not None else set()

    if str(decoded_user.get("_id")) != str(user_id):
        raise ApiError(403, code="user.cannotEditOthers")

    user_oid = to_object_id(user_id, "user_id")
    parse_old_avatar = parse_json(old_avatar)
    parse_old_cover_bg = parse_json(old_cover_bg)

    # CHỈ ghi những trường request thực sự gửi lên.
    #
    # Bản cũ gán cả ba vô điều kiện rồi `$set` nguyên khối, nên một request chỉ
    # muốn đổi ảnh đại diện sẽ ghi `username=None` và xoá trắng tên tài khoản.
    # Chưa ai gặp vì `UpdateProfileModal.jsx` luôn gửi đủ ba trường — nhưng đó
    # là may mắn, không phải thiết kế: thêm một client khác, hoặc một lần sửa
    # giao diện quên đính một ô, là mất dữ liệu.
    #
    # Phân biệt "không gửi" với "gửi chuỗi rỗng" — hai chuyện khác hẳn nhau.
    # KHÔNG dùng được `value is not None` để phân biệt: FastAPI đưa một field
    # gửi rỗng (`intro=`) tới đây dưới dạng None y hệt field vắng mặt, nên dựa
    # vào đó thì người dùng mất luôn khả năng xoá sạch phần giới thiệu.
    # `submitted` là tên các field thật sự có trong form (xem app/utils/forms.py).
    update_data = {"updated_at": datetime.utcnow()}
    for field_name, value in (("username", username), ("address", address), ("intro", intro)):
        if field_name in submitted:
            update_data[field_name] = value if value is not None else ""

    if new_password and new_password != old_password:
        current = await User.get(user_oid)
        if (
            not current
            or not old_password
            or not _bcrypt.checkpw(old_password.encode("utf-8"), (current.password or "").encode("utf-8"))
        ):
            raise ApiError(403, code="user.wrongOldPassword")
        update_data["password"] = hash_password(new_password)

    images = files.get("images", []) if files else []
    if images:
        if update_images == "both":
            update_data["avatar"] = {"name": images[0]["filename"], "url": images[0]["path"]}
            if parse_old_avatar and parse_old_avatar.get("name") != "avatar_trang.jpg":
                await delete_file(parse_old_avatar.get("url"))
            if len(images) > 1:
                update_data["cover_bg"] = {"name": images[1]["filename"], "url": images[1]["path"]}
        elif update_images == "avatar":
            if parse_old_avatar and parse_old_avatar.get("name") != "avatar_trang.jpg":
                await delete_file(parse_old_avatar.get("url"))
            update_data["avatar"] = {"name": images[0]["filename"], "url": images[0]["path"]}
        elif update_images == "cover_bg":
            update_data["cover_bg"] = {"name": images[0]["filename"], "url": images[0]["path"]}
            if parse_old_cover_bg:
                await delete_file(parse_old_cover_bg.get("url", ""))

    await User.find_one(User.id == user_oid).update({"$set": update_data})
    return ok(code="user.updated")


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------


async def search_users(decoded_user: dict, search: str = None, page: int = 1):
    search = normalize_search(search)
    if not search or not page:
        # Giữ nguyên hình dạng cũ: 200 kèm danh sách rỗng, client dựa vào đó để
        # không hiện gì khi ô tìm kiếm trống.
        return {"error": True, "success": False, "users": [], "totalPage": 1, "totalUsers": 0}

    user_id = to_object_id(decoded_user["_id"], "user_id")
    regex = contains(search)
    query = {"_id": {"$ne": user_id}, "$or": [{"username": regex}, {"email": regex}]}

    total_users = await User.find(query).count()
    users = await User.find(query).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(
        users=[{"_id": str(u.id), "avatar": u.avatar, "username": u.username, "email": u.email} for u in users],
        totalPage=total_page(total_users),
        totalUsers=total_users,
    )


async def get_users_by_admin(decoded_user: dict, page: int = 1, search: str = None):
    require_admin(decoded_user, NOT_ENOUGH_PERMISSION_MESSAGE)

    role_data = decoded_user.get("role") or {}
    role_id = role_data.get("_id") if isinstance(role_data, dict) else None

    query = {}
    if role_id:
        # Ẩn các admin khác khỏi danh sách quản trị.
        query["role"] = {"$ne": to_object_id(role_id, "role")}
    keyword = normalize_search(search)
    if keyword:
        query["username"] = contains(keyword, unaccent=True)

    total_users = await User.find(query).count()
    users = await User.find(query).skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()
    return ok(
        users=[
            {
                "_id": str(u.id),
                "username": u.username,
                "email": u.email,
                "avatar": u.avatar,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                "address": u.address,
            }
            for u in users
        ],
        totalPage=total_page(total_users),
        totalUsers=total_users,
        curPage=page,
    )


# ---------------------------------------------------------------------------
# CV
# ---------------------------------------------------------------------------
