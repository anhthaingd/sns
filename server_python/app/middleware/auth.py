"""Xác thực request bằng access token."""

import jwt
from fastapi import Header

from app.errors import ApiError
from app.services.token_store import is_revoked
from app.utils.token import decode_access_token


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ")
    if len(parts) < 2 or not parts[1]:
        return None
    return parts[1]


async def get_current_user(authorization: str = Header(default=None)) -> dict:
    token = extract_bearer_token(authorization)
    if not token:
        raise ApiError(401, code="auth.missingToken")

    try:
        decoded = decode_access_token(token)
    except jwt.ExpiredSignatureError as err:
        # 401 (không phải 403) để client biết cần gọi /api/users/refresh rồi
        # thử lại, thay vì đá người dùng ra màn hình đăng nhập.
        raise ApiError(401, code="auth.invalidOrExpiredToken") from err
    except jwt.PyJWTError as err:
        raise ApiError(403, code="auth.invalidToken") from err

    # Thu hồi tra theo `jti` trong Redis -> đăng xuất sống sót qua restart.
    if await is_revoked(decoded.get("jti", "")):
        raise ApiError(401, code="auth.invalidOrExpiredToken")

    return decoded
