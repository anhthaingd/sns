"""Kiểm tra quyền dựa trên claim `role` trong access token.

Đoạn `role_data = decoded_user.get("role"); role_value = ... if isinstance(...)`
trước đây bị chép lại y hệt ở 8 controller. Một bản duy nhất ở đây để nếu đổi
cách lưu role thì chỉ sửa một chỗ.
"""

from app.errors import ApiError
from app.messages import message_for

ADMIN_ROLE_VALUE = 1

ADMIN_ONLY_MESSAGE = message_for("auth.adminOnly")
NOT_ENOUGH_PERMISSION_MESSAGE = message_for("auth.notEnoughPermission")

# Bảng tra ngược câu -> mã, để `require_admin` giữ nguyên chữ ký nhận `message`
# (8 controller đang truyền câu tuỳ biến) mà vẫn gắn được mã cho client dịch.
_MESSAGE_CODES = {
    ADMIN_ONLY_MESSAGE: "auth.adminOnly",
    NOT_ENOUGH_PERMISSION_MESSAGE: "auth.notEnoughPermission",
}


def role_value(decoded_user: dict) -> int:
    role = decoded_user.get("role")
    if isinstance(role, dict):
        value = role.get("value", 0)
        return value if isinstance(value, int) else 0
    return 0


def is_admin(decoded_user: dict) -> bool:
    return role_value(decoded_user) == ADMIN_ROLE_VALUE


def require_admin(decoded_user: dict, message: str = ADMIN_ONLY_MESSAGE) -> None:
    if not is_admin(decoded_user):
        raise ApiError(403, message, code=_MESSAGE_CODES.get(message))
