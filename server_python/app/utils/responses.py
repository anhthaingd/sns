"""Khuôn response thành công dùng chung.

Mọi endpoint trả về `{"error": false, "success": true, ...}` cộng thêm các khoá
nghiệp vụ. Gom vào một hàm để 51 controller không phải lặp lại hai khoá này —
và để đổi hợp đồng (nếu có) chỉ phải sửa một chỗ.
"""

from typing import Any

from app.messages import message_for


def ok(code: str | None = None, **payload: Any) -> dict[str, Any]:
    """Response thành công.

    Truyền `code` thì câu tiếng Việt được lấy từ `app/messages.py` và mã đi
    kèm trong body để client tra bản dịch — cùng cơ chế với `ApiError`::

        return ok(code="post.created")
        # {"error": false, "success": true,
        #  "message": "Tạo bài viết thành công!", "code": "post.created"}

    Vẫn nhận `ok(message="...")` kiểu cũ cho những chỗ chưa gán mã; khi đó
    client hiện thẳng câu tiếng Việt.
    """
    if code is None:
        return {"error": False, "success": True, **payload}
    payload.setdefault("message", message_for(code))
    return {"error": False, "success": True, "code": code, **payload}
