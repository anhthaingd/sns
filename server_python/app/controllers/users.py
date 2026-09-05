import json
import math

import bcrypt as _bcrypt
import jwt
from fastapi import Response
from pymongo.errors import DuplicateKeyError

from app.config.settings import (
    LOGIN_FAIL_LIMIT_PER_EMAIL,
    LOGIN_FAIL_LIMIT_PER_IP,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
)
from app.errors import ApiError
from app.middleware.auth import extract_bearer_token
from app.models.channel import Channel
from app.models.follower import Follower
from app.models.following import Following
from app.models.post import Post
from app.models.resume import Resume
from app.models.role import Role
from app.models.user import User
from app.services import rate_limit
from app.services.token_store import is_revoked, revoke
from app.utils.cookies import clear_refresh_cookie, set_refresh_cookie
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id
from app.utils.loaders import load_users, role_brief, user_brief
from app.utils.permissions import NOT_ENOUGH_PERMISSION_MESSAGE, require_admin
from app.utils.responses import ok
from app.utils.search import contains, normalize_search
from app.utils.serialization import serialize_doc
from app.utils.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    seconds_until_expiry,
)

PAGE_SIZE = 10
FOLLOW_PAGE_SIZE = 20
BCRYPT_ROUNDS = 10

# Một thông báo duy nhất cho mọi kiểu đăng nhập hỏng. Bản cũ trả 404 "Tài khoản
# chưa được đăng ký!" khi email lạ và 403 "Sai mật khẩu!" khi sai mật khẩu —
# chỉ cần thử một lần là biết email nào có thật trong hệ thống.
INVALID_CREDENTIALS_MESSAGE = "Email hoặc mật khẩu không đúng!"
USER_NOT_FOUND_MESSAGE = "Không tìm thấy người dùng!"


# Hash "mồi" để lần đăng nhập với email không tồn tại vẫn tốn đúng chừng ấy
# thời gian như email có thật. Không có nó, kẻ tấn công đo thời gian phản hồi là
# biết email nào tồn tại — đúng cái lỗ mà thông báo lỗi chung đang bịt.
_DUMMY_PASSWORD_HASH = _bcrypt.hashpw(b"fuurin-dummy-password", _bcrypt.gensalt(10))


def _hash_password(raw: str) -> str:
    return _bcrypt.hashpw(raw.encode("utf-8"), _bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def _parse_json(json_string):
    try:
        return json.loads(json_string) if json_string else None
    except (TypeError, ValueError):
        return None


def _total_page(total: int, page_size: int = PAGE_SIZE) -> int:
    return math.ceil(total / page_size) if total > 0 else 1


async def _populate_role(user_doc: User) -> dict:
    data = serialize_doc(user_doc)
    if user_doc.role:
        role = await Role.get(user_doc.role)
        if role:
            data["role"] = role_brief(role)
    return data


async def _brief_users_of(ids) -> list[dict]:
    """Danh sách user rút gọn từ một mảng id — một truy vấn duy nhất."""
    user_map = await load_users(ids)
    return [user_brief(user_map[key]) for key in (str(i) for i in ids or []) if key in user_map]


async def _populate_followers(user_id) -> list[dict]:
    doc = await Follower.find_one(Follower.user == to_object_id(user_id, "user_id"))
    return await _brief_users_of(doc.followers) if doc and doc.followers else []


async def _populate_following(user_id) -> list[dict]:
    doc = await Following.find_one(Following.user == to_object_id(user_id, "user_id"))
    return await _brief_users_of(doc.following) if doc and doc.following else []


# ---------------------------------------------------------------------------
# Xác thực
# ---------------------------------------------------------------------------


async def register_user(
    email: str = None, password: str = None, username: str = None, address: str = None, intro: str = None
):
    if not email or not password:
        raise ApiError(400, "Yêu cầu cần có email và password!")

    duplicated = await User.find_one(User.email == email)
    if duplicated:
        raise ApiError(409, "Địa chỉ email đã tồn tại!")

    user_role = await Role.find_one(Role.value == 0)
    created_user = User(
        email=email,
        password=_hash_password(password),
        username=username,
        address=address,
        intro=intro,
        role=user_role.id if user_role else None,
    )
    try:
        await created_user.insert()
    except DuplicateKeyError as err:
        # Hai request đăng ký cùng lúc: unique index là chốt chặn cuối.
        raise ApiError(409, "Địa chỉ email đã tồn tại!") from err

    await Follower(user=created_user.id).insert()
    await Following(user=created_user.id).insert()
    return ok(message="Tạo tài khoản thành công!")


LOGIN_EMAIL_BUCKET = "login_fail_email"
LOGIN_IP_BUCKET = "login_fail_ip"


async def login_user(email: str, password: str, response: Response, ip: str = "unknown"):
    identity = (email or "").strip().lower()

    # Chặn TRƯỚC khi tra DB/bcrypt: đã vượt ngưỡng thì không tốn tài nguyên nữa.
    await rate_limit.ensure_under_limit(LOGIN_EMAIL_BUCKET, identity, LOGIN_FAIL_LIMIT_PER_EMAIL)
    await rate_limit.ensure_under_limit(LOGIN_IP_BUCKET, ip, LOGIN_FAIL_LIMIT_PER_IP)

    user = await User.find_one(User.email == email)
    stored_hash = user.password.encode("utf-8") if user and user.password else _DUMMY_PASSWORD_HASH
    password_ok = _bcrypt.checkpw((password or "").encode("utf-8"), stored_hash)

    if not user or not user.password or not password_ok:
        await rate_limit.record_failure(LOGIN_EMAIL_BUCKET, identity, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        await rate_limit.record_failure(LOGIN_IP_BUCKET, ip, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        raise ApiError(401, INVALID_CREDENTIALS_MESSAGE)

    await rate_limit.reset(LOGIN_EMAIL_BUCKET, identity)
    await rate_limit.reset(LOGIN_IP_BUCKET, ip)

    role = await Role.get(user.role) if user.role else None
    claims = {
        "_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": role_brief(role),
    }

    # Access token vẫn nằm trong body để client không phải đổi cách lưu.
    # Refresh token đi bằng cookie httpOnly — JavaScript không chạm được.
    set_refresh_cookie(response, create_refresh_token(user.id))
    return ok(accessToken=create_access_token(claims))


async def refresh_access_token(refresh_token: str | None, response: Response):
    """Đổi refresh token lấy access token mới, có XOAY VÒNG.

    Xoay vòng = phát refresh token mới và thu hồi cái vừa dùng. Nhờ vậy một
    refresh token bị đánh cắp chỉ dùng được đúng một lần.
    """
    if not refresh_token:
        raise ApiError(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!")

    try:
        decoded = decode_refresh_token(refresh_token)
    except jwt.PyJWTError as err:
        clear_refresh_cookie(response)
        raise ApiError(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!") from err

    if await is_revoked(decoded.get("jti", "")):
        clear_refresh_cookie(response)
        raise ApiError(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!")

    user = await User.get(to_object_id(decoded["_id"], "user_id"))
    if not user:
        clear_refresh_cookie(response)
        raise ApiError(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!")

    await revoke(decoded.get("jti", ""), seconds_until_expiry(decoded))

    role = await Role.get(user.role) if user.role else None
    claims = {
        "_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": role_brief(role),
    }
    set_refresh_cookie(response, create_refresh_token(user.id))
    return ok(accessToken=create_access_token(claims))


async def logout_user(authorization: str | None, refresh_token: str | None, response: Response):
    """Thu hồi cả access token lẫn refresh token của phiên hiện tại.

    Ghi vào Redis với TTL đúng bằng hạn còn lại của token, nên đăng xuất có
    hiệu lực thật sự — sống sót qua restart, và Redis tự dọn khi token hết hạn.
    """
    access_token = extract_bearer_token(authorization)
    if access_token:
        try:
            decoded = decode_access_token(access_token)
            await revoke(decoded.get("jti", ""), seconds_until_expiry(decoded))
        except jwt.PyJWTError:
            # Token đã hết hạn/hỏng thì không cần thu hồi nữa.
            pass

    if refresh_token:
        try:
            decoded_refresh = decode_refresh_token(refresh_token)
            await revoke(decoded_refresh.get("jti", ""), seconds_until_expiry(decoded_refresh))
        except jwt.PyJWTError:
            pass

    clear_refresh_cookie(response)
    return ok(message="Đăng xuất tài khoản thành công!")


# ---------------------------------------------------------------------------
# Hồ sơ người dùng
# ---------------------------------------------------------------------------


async def get_user_by_token(decoded_user: dict):
    user = await User.find_one(User.email == decoded_user["email"])
    if not user:
        raise ApiError(404, USER_NOT_FOUND_MESSAGE)
    return ok(
        user=await _populate_role(user),
        followers=await _populate_followers(decoded_user["_id"]),
        following=await _populate_following(decoded_user["_id"]),
    )


async def get_user_details(user_id: str):
    oid = to_object_id(user_id, "user_id")
    user = await User.get(oid)
    if not user:
        raise ApiError(404, USER_NOT_FOUND_MESSAGE)

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
        followers=await _populate_followers(user_id),
        following=await _populate_following(user_id),
        posts=await Post.find(Post.user == oid).count(),
        channels=await Channel.find({"members": oid}).count(),
    )


async def update_user(
    user_id: str,
    decoded_user: dict,
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

    if str(decoded_user.get("_id")) != str(user_id):
        raise ApiError(403, "Bạn không thể sửa thông tin của người khác!")

    user_oid = to_object_id(user_id, "user_id")
    parse_old_avatar = _parse_json(old_avatar)
    parse_old_cover_bg = _parse_json(old_cover_bg)

    update_data = {
        "username": username,
        "address": address,
        "intro": intro,
        "updated_at": datetime.utcnow(),
    }

    if new_password and new_password != old_password:
        current = await User.get(user_oid)
        if (
            not current
            or not old_password
            or not _bcrypt.checkpw(old_password.encode("utf-8"), (current.password or "").encode("utf-8"))
        ):
            raise ApiError(403, "Mật khẩu cũ không chính xác!")
        update_data["password"] = _hash_password(new_password)

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
    return ok(message="Cập nhật người dùng thành công!")


# ---------------------------------------------------------------------------
# Follow
# ---------------------------------------------------------------------------


async def get_followers(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    doc = await Follower.find_one(Follower.user == user_id)
    if not doc:
        return ok(followers=[], totalPage=1)

    all_ids = doc.followers or []
    start = (page - 1) * FOLLOW_PAGE_SIZE
    page_ids = all_ids[start : start + FOLLOW_PAGE_SIZE]
    return ok(
        user=str(doc.user),
        followers=await _brief_users_of(page_ids),
        totalPage=_total_page(len(all_ids), FOLLOW_PAGE_SIZE),
    )


async def get_following(decoded_user: dict, page: int = 1):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    doc = await Following.find_one(Following.user == user_id)
    if not doc:
        return ok(following=[], totalPage=1)

    all_ids = doc.following or []
    start = (page - 1) * FOLLOW_PAGE_SIZE
    page_ids = all_ids[start : start + FOLLOW_PAGE_SIZE]
    return ok(
        user=str(doc.user),
        following=await _brief_users_of(page_ids),
        totalPage=_total_page(len(all_ids), FOLLOW_PAGE_SIZE),
    )


async def following_user(decoded_user: dict, target_id: str):
    user_id = decoded_user["_id"]
    if user_id == target_id:
        raise ApiError(409, "Bạn không thể tự follow bản thân!")

    user_oid = to_object_id(user_id, "user_id")
    target_oid = to_object_id(target_id, "target_id")
    following_doc = await Following.find_one(Following.user == user_oid)

    if following_doc and target_oid in following_doc.following:
        await Following.find_one(Following.user == user_oid).update({"$pull": {"following": target_oid}})
        await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": user_oid}})
        return ok(message="Hủy follow tài khoản thành công!")

    await Following.find_one(Following.user == user_oid).update({"$push": {"following": target_oid}})
    await Follower.find_one(Follower.user == target_oid).update({"$push": {"followers": user_oid}})
    return ok(message="Follow tài khoản thành công!")


async def remove_following(decoded_user: dict, target_id: str):
    user_oid = to_object_id(decoded_user["_id"], "user_id")
    target_oid = to_object_id(target_id, "target_id")
    await Following.find_one(Following.user == user_oid).update({"$pull": {"following": target_oid}})
    await Follower.find_one(Follower.user == target_oid).update({"$pull": {"followers": user_oid}})
    return ok(message="Hủy theo dõi người dùng thành công!")


async def remove_followers(decoded_user: dict, target_id: str):
    user_oid = to_object_id(decoded_user["_id"], "user_id")
    target_oid = to_object_id(target_id, "target_id")
    await Following.find_one(Following.user == target_oid).update({"$pull": {"following": user_oid}})
    await Follower.find_one(Follower.user == user_oid).update({"$pull": {"followers": target_oid}})
    return ok(message="Gỡ thành công người dùng ra khỏi danh sách theo dõi!")


# ---------------------------------------------------------------------------
# Tìm kiếm & quản trị
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
        totalPage=_total_page(total_users),
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
        totalPage=_total_page(total_users),
        totalUsers=total_users,
        curPage=page,
    )


# ---------------------------------------------------------------------------
# CV
# ---------------------------------------------------------------------------


def _filter_different_elements(arr1, arr2):
    different = [
        obj1
        for obj1 in arr1
        if not any(obj2.get("name") == obj1.get("name") and obj2.get("value") == obj1.get("value") for obj2 in arr2)
    ]
    different += [
        obj2
        for obj2 in arr2
        if not any(obj1.get("name") == obj2.get("name") and obj1.get("value") == obj2.get("value") for obj1 in arr1)
    ]
    return different


async def get_resume(decoded_user: dict):
    resume = await Resume.find_one(Resume.user == to_object_id(decoded_user["_id"], "user_id"))
    return ok(resume=serialize_doc(resume) if resume else None)


async def post_resume(
    decoded_user: dict,
    name: str = None,
    position: str = None,
    old_avatar: str = None,
    birthday: str = None,
    email: str = None,
    address: str = None,
    phone: str = None,
    github: str = None,
    objective: str = None,
    education_name: str = None,
    education_major: str = None,
    education_completion: str = None,
    education_gpa: str = None,
    certificates_name: str = None,
    old_certificates: str = None,
    edit_certificates: str = None,
    experiences: str = None,
    skills: str = None,
    languages: str = None,
    projects: str = None,
    files: dict = None,
):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    parse_old_avatar = _parse_json(old_avatar)
    parse_certificate_name = _parse_json(certificates_name) or []
    parse_old_certificates = _parse_json(old_certificates) or []
    parse_edit_certificates = _parse_json(edit_certificates) or []

    resume_data = {
        "user": user_id,
        "name": name,
        "position": position,
        "birthday": birthday,
        "email": email,
        "address": address,
        "phone": phone,
        "github": github,
        "objective": objective,
        "educationName": education_name,
        "educationMajor": education_major,
        "educationCompletion": education_completion,
        "educationGPA": education_gpa,
        "experiences": _parse_json(experiences) or [],
        "skills": _parse_json(skills) or [],
        "languages": _parse_json(languages) or [],
        "projects": _parse_json(projects) or [],
    }

    existed_resume = await Resume.find_one(Resume.user == user_id)
    if not existed_resume:
        await Resume(**resume_data).insert()
        return ok(message="Lưu CV thành công!")

    if parse_old_certificates:
        for removed in _filter_different_elements(parse_old_certificates, parse_edit_certificates):
            await delete_file(removed.get("url", ""))

    avatar_files = files.get("avatar", []) if files else []
    if avatar_files:
        if parse_old_avatar and parse_old_avatar.get("url"):
            await delete_file(parse_old_avatar["url"])
        resume_data["avatar"] = {"name": avatar_files[0]["filename"], "url": avatar_files[0]["path"]}

    cert_files = files.get("certificates", []) if files else []
    if cert_files and parse_certificate_name:
        new_certs = [
            {"name": parse_certificate_name[i] if i < len(parse_certificate_name) else "", "url": cf["path"]}
            for i, cf in enumerate(cert_files)
        ]
        resume_data["certificates"] = parse_edit_certificates + new_certs
    else:
        resume_data["certificates"] = parse_edit_certificates

    await Resume.find_one(Resume.user == user_id).update({"$set": resume_data})
    return ok(message="Lưu CV thành công!")
