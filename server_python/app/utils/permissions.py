"""Kiểm tra quyền dựa trên claim `role` trong access token.

Đoạn `role_data = decoded_user.get("role"); role_value = ... if isinstance(...)`
trước đây bị chép lại y hệt ở 8 controller. Một bản duy nhất ở đây để nếu đổi
cách lưu role thì chỉ sửa một chỗ.
"""

from app.errors import ApiError

ADMIN_ROLE_VALUE = 1

ADMIN_ONLY_MESSAGE = "Chức năng này chỉ dành cho admin!"
NOT_ENOUGH_PERMISSION_MESSAGE = "Bạn không đủ quyền!"


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
        raise ApiError(403, message)
