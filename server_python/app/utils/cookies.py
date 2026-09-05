"""Đặt/xoá cookie refresh token.

Gom vào một chỗ để mọi route auth dùng cùng một bộ thuộc tính bảo mật — sai
lệch giữa lúc set và lúc delete sẽ khiến trình duyệt không xoá được cookie.
"""

from fastapi import Response

from app.config.settings import (
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    REFRESH_TOKEN_TTL_SECONDS,
)


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        # httponly: JavaScript không đọc được -> XSS không lấy được refresh token.
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
    )


def clear_refresh_cookie(response: Response) -> None:
    # Phải trùng path/samesite/secure với lúc set, nếu không trình duyệt coi
    # đây là một cookie khác và cookie cũ vẫn nằm lại.
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
