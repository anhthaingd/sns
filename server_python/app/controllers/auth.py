"""Đăng ký, đăng nhập, gia hạn và đăng xuất.

Tách khỏi `users.py` vì đây là nhóm nhạy cảm nhất về bảo mật (giới hạn tần
suất, thu hồi token, cookie refresh) — trộn chung với CRUD hồ sơ khiến file cũ
dài 634 dòng và rất khó rà lại phần này một cách độc lập.
"""

import logging

import bcrypt as _bcrypt
import jwt
from fastapi import Response
from pymongo.errors import DuplicateKeyError

from app.config.settings import (
    LOGIN_FAIL_LIMIT_PER_EMAIL,
    LOGIN_FAIL_LIMIT_PER_IP,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
)
from app.controllers.user_common import hash_password
from app.errors import ApiError
from app.middleware.auth import extract_bearer_token
from app.models.follower import Follower
from app.models.following import Following
from app.models.role import Role
from app.models.user import User
from app.services import rate_limit
from app.services.token_store import is_revoked, revoke
from app.utils.cookies import clear_refresh_cookie, set_refresh_cookie
from app.utils.ids import to_object_id
from app.utils.loaders import role_brief
from app.utils.responses import ok
from app.utils.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    seconds_until_expiry,
)

logger = logging.getLogger("fuurin.auth")

# Một thông báo duy nhất cho mọi kiểu đăng nhập hỏng. Bản cũ trả 404 "Tài khoản
# chưa được đăng ký!" khi email lạ và 403 "Sai mật khẩu!" khi sai mật khẩu —
# chỉ cần thử một lần là biết email nào có thật trong hệ thống.

# Hash "mồi" để lần đăng nhập với email không tồn tại vẫn tốn đúng chừng ấy
# thời gian như email có thật. Không có nó, kẻ tấn công đo thời gian phản hồi là
# biết email nào tồn tại — đúng cái lỗ mà thông báo lỗi chung đang bịt.
_DUMMY_PASSWORD_HASH = _bcrypt.hashpw(b"fuurin-dummy-password", _bcrypt.gensalt(10))


async def register_user(
    email: str = None, password: str = None, username: str = None, address: str = None, intro: str = None
):
    if not email or not password:
        raise ApiError(400, code="auth.credentialsRequired")

    duplicated = await User.find_one(User.email == email)
    if duplicated:
        raise ApiError(409, code="auth.emailExists")

    user_role = await Role.find_one(Role.value == 0)
    created_user = User(
        email=email,
        password=hash_password(password),
        username=username,
        address=address,
        intro=intro,
        role=user_role.id if user_role else None,
    )
    try:
        await created_user.insert()
    except DuplicateKeyError as err:
        # Hai request đăng ký cùng lúc: unique index là chốt chặn cuối.
        raise ApiError(409, code="auth.emailExists") from err

    await Follower(user=created_user.id).insert()
    await Following(user=created_user.id).insert()
    return ok(code="auth.registered")


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
        raise ApiError(401, code="auth.invalidCredentials")

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
        raise ApiError(401, code="auth.sessionExpired")

    try:
        decoded = decode_refresh_token(refresh_token)
    except jwt.PyJWTError as err:
        clear_refresh_cookie(response)
        raise ApiError(401, code="auth.sessionExpired") from err

    if await is_revoked(decoded.get("jti", "")):
        clear_refresh_cookie(response)
        raise ApiError(401, code="auth.sessionExpired")

    user = await User.get(to_object_id(decoded["_id"], "user_id"))
    if not user:
        clear_refresh_cookie(response)
        raise ApiError(401, code="auth.sessionExpired")

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
    return ok(code="auth.loggedOut")


# ---------------------------------------------------------------------------
# Hồ sơ người dùng
# ---------------------------------------------------------------------------
