"""Khuôn response thành công dùng chung.

Mọi endpoint trả về `{"error": false, "success": true, ...}` cộng thêm các khoá
nghiệp vụ. Gom vào một hàm để 51 controller không phải lặp lại hai khoá này —
và để đổi hợp đồng (nếu có) chỉ phải sửa một chỗ.
"""

from typing import Any


def ok(**payload: Any) -> dict[str, Any]:
    return {"error": False, "success": True, **payload}
