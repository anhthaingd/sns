"""Tạo và kiểm tra JWT.

Hai loại token, hai vai trò khác nhau:

- **access token** — sống 15 phút, client gửi kèm mọi request. Ngắn để thiệt
  hại khi lộ là hữu hạn.
- **refresh token** — sống 7 ngày, nằm trong cookie httpOnly (JavaScript không
  đọc được nên XSS không lấy được), chỉ dùng để xin access token mới.

Cả hai mang claim `jti` để thu hồi được từng token một qua
`app.services.token_store`. Trước đây chỉ có một token 7 ngày, không có `jti`,
và blacklist nằm trong RAM tiến trình -> không thu hồi được.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config.settings import (
    ACCESS_TOKEN_SECRET,
    ACCESS_TOKEN_TTL_SECONDS,
    REFRESH_TOKEN_SECRET,
    REFRESH_TOKEN_TTL_SECONDS,
)

ALGORITHM = "HS256"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Chỉ những claim thực sự cần cho phân quyền và hiển thị. Bản cũ nhét cả
# `socketId`, `socketCallId`, `address`, `intro`, `avatar`, `cover_bg` vào
# token rồi gửi kèm MỌI request — vừa nặng vừa lộ thông tin không cần thiết.
ACCESS_TOKEN_CLAIMS = ("_id", "email", "username", "role")


def _encode(payload: dict, secret: str, ttl_seconds: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    body = {
        **payload,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(body, secret, algorithm=ALGORITHM)


def create_access_token(user_data: dict) -> str:
    claims = {key: user_data.get(key) for key in ACCESS_TOKEN_CLAIMS if key in user_data}
    return _encode(claims, ACCESS_TOKEN_SECRET, ACCESS_TOKEN_TTL_SECONDS, ACCESS_TOKEN_TYPE)


def create_refresh_token(user_id: str) -> str:
    return _encode({"_id": str(user_id)}, REFRESH_TOKEN_SECRET, REFRESH_TOKEN_TTL_SECONDS, REFRESH_TOKEN_TYPE)


def _decode(token: str, secret: str, expected_type: str) -> dict:
    decoded = jwt.decode(token, secret, algorithms=[ALGORITHM])
    # Bắt buộc kiểm `type`: REFRESH_TOKEN_SECRET mặc định bằng
    # ACCESS_TOKEN_SECRET, thiếu bước này thì refresh token dùng thay access
    # token được — tức là có một token 7 ngày đi vòng qua mọi giới hạn.
    if decoded.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Sai loại token, cần '{expected_type}'")
    return decoded


def decode_access_token(token: str) -> dict:
    return _decode(token, ACCESS_TOKEN_SECRET, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> dict:
    return _decode(token, REFRESH_TOKEN_SECRET, REFRESH_TOKEN_TYPE)


def seconds_until_expiry(decoded: dict) -> int:
    """Còn bao lâu nữa token hết hạn — dùng làm TTL cho blacklist."""
    exp = decoded.get("exp")
    if not exp:
        return 0
    remaining = int(exp) - int(datetime.now(timezone.utc).timestamp())
    return max(remaining, 0)
