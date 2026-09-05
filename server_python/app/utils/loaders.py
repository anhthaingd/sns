"""Batch loader — nạp nhiều document bằng MỘT truy vấn `$in`.

Vấn đề đã đo được trước khi có file này (bằng Mongo profiler, dữ liệu thật):

    GET /api/posts?page=1                 -> 53 truy vấn (users 40, channels 11)
    GET /api/channels?page=1 (1 channel,
        11 thành viên)                    -> 64 truy vấn (users 31, roles 31)

Nguyên nhân: mỗi quan hệ được "populate" bằng `await Model.get(id)` bên trong
vòng lặp — N+1 kinh điển. Cách chữa là gom toàn bộ id của **cả trang** rồi bắn
một truy vấn cho mỗi collection.

Cố ý không dùng `$lookup`: batch loader cho hiệu quả tương đương, giữ nguyên
code Python dễ đọc, và số truy vấn đo được bằng `tests/test_query_count.py`.
"""

from typing import Any

from beanie import Document
from bson import ObjectId

from app.models.channel import Channel
from app.models.role import Role
from app.models.user import User


async def load_by_ids(model: type[Document], ids) -> dict[str, Any]:
    """Nạp document theo danh sách id, trả về map `str(_id) -> document`.

    Tự loại trùng và bỏ giá trị rỗng, nên caller cứ ném cả danh sách id thô vào.
    """
    unique: dict[str, ObjectId] = {}
    for raw in ids or []:
        if not raw:
            continue
        key = str(raw)
        if key not in unique:
            unique[key] = raw if isinstance(raw, ObjectId) else ObjectId(key)

    if not unique:
        return {}

    docs = await model.find({"_id": {"$in": list(unique.values())}}).to_list()
    return {str(doc.id): doc for doc in docs}


async def load_users(ids) -> dict[str, User]:
    return await load_by_ids(User, ids)


async def load_channels(ids) -> dict[str, Channel]:
    return await load_by_ids(Channel, ids)


async def load_roles(ids) -> dict[str, Role]:
    return await load_by_ids(Role, ids)


async def load_roles_of(users) -> dict[str, Role]:
    """Nạp role cho một tập user đã có sẵn — một truy vấn cho tất cả."""
    return await load_roles([u.role for u in users if u is not None and u.role])


# ---------------------------------------------------------------------------
# Hình dạng rút gọn của user khi nhúng vào response khác.
# Giữ ĐÚNG các khoá mà bản Express cũ trả về để client không phải sửa gì.
# ---------------------------------------------------------------------------


def user_brief(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "avatar": user.avatar,
    }


def user_brief_with_cover(user: User | None) -> dict | None:
    """Bản dùng trong chat: client hiển thị cả ảnh bìa ở khung hội thoại."""
    brief = user_brief(user)
    if brief is None:
        return None
    brief["cover_bg"] = user.cover_bg
    return brief


def role_brief(role: Role | None) -> dict | None:
    if role is None:
        return None
    return {"_id": str(role.id), "name": role.name, "value": role.value}


def brief_list(ids, user_map: dict[str, User]) -> list[dict]:
    """Map danh sách id sang danh sách user rút gọn, bỏ qua id không còn tồn tại."""
    result = []
    for raw in ids or []:
        user = user_map.get(str(raw))
        if user is not None:
            result.append(user_brief(user))
    return result
