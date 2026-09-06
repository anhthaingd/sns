"""Tiện ích dùng chung của nhóm controller về người dùng.

Tách ra vì `auth`, `users`, `follows`, `resume` đều cần: hàm băm mật khẩu, hàm
đọc JSON từ form, cách tính số trang và cách rút gọn thông tin người dùng khi
trả về. Để chúng ở một trong bốn file kia thì ba file còn lại phải import chéo
lẫn nhau.
"""

import json
import math

import bcrypt as _bcrypt

from app.models.follower import Follower
from app.models.following import Following
from app.models.role import Role
from app.models.user import User
from app.utils.ids import to_object_id
from app.utils.loaders import load_users, role_brief, user_brief
from app.utils.serialization import serialize_doc

PAGE_SIZE = 10
FOLLOW_PAGE_SIZE = 20
BCRYPT_ROUNDS = 10


def hash_password(raw: str) -> str:
    return _bcrypt.hashpw(raw.encode("utf-8"), _bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def parse_json(json_string):
    try:
        return json.loads(json_string) if json_string else None
    except (TypeError, ValueError):
        return None


def total_page(total: int, page_size: int = PAGE_SIZE) -> int:
    return math.ceil(total / page_size) if total > 0 else 1


async def populate_role(user_doc: User) -> dict:
    data = serialize_doc(user_doc)
    if user_doc.role:
        role = await Role.get(user_doc.role)
        if role:
            data["role"] = role_brief(role)
    return data


async def brief_users_of(ids) -> list[dict]:
    """Danh sách user rút gọn từ một mảng id — một truy vấn duy nhất."""
    user_map = await load_users(ids)
    return [user_brief(user_map[key]) for key in (str(i) for i in ids or []) if key in user_map]


async def populate_followers(user_id) -> list[dict]:
    doc = await Follower.find_one(Follower.user == to_object_id(user_id, "user_id"))
    return await brief_users_of(doc.followers) if doc and doc.followers else []


async def populate_following(user_id) -> list[dict]:
    doc = await Following.find_one(Following.user == to_object_id(user_id, "user_id"))
    return await brief_users_of(doc.following) if doc and doc.following else []


# ---------------------------------------------------------------------------
# Xác thực
# ---------------------------------------------------------------------------
