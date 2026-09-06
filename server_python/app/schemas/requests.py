"""Schema cho request body JSON.

Trước đây các route nhận `body: dict` nên mọi giá trị đều lọt xuống tầng truy
vấn mà không ai kiểm tra kiểu: `POST /api/users/login` với
`{"email": 123, "password": []}` vẫn đi thẳng vào Mongo. Khai báo tường minh ở
đây giúp FastAPI trả 422 ngay tại cửa và sinh tài liệu ở /docs.
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    # Cố ý để Optional thay vì bắt buộc: controller vẫn trả 400 kèm thông báo
    # tiếng Việt "Yêu cầu cần có email và password!" như hợp đồng cũ, thay vì
    # 422 với thông báo máy móc. Kiểu dữ liệu vẫn được kiểm (int -> 422).
    email: EmailStr | None = None
    password: str | None = None
    username: str | None = None
    address: str | None = None
    intro: str | None = None


class CommentCreateRequest(BaseModel):
    content: str = Field(default="")


class CommentDeleteRequest(BaseModel):
    commentId: str = Field(default="")


class RemoveUserFromChannelRequest(BaseModel):
    userId: str = Field(default="")


class ClientLogRequest(BaseModel):
    """Một bản ghi lỗi do trình duyệt gửi lên.

    Mọi trường đều có `max_length`: đây là endpoint mở (không cần đăng nhập)
    nên phải giả định dữ liệu gửi lên là không đáng tin. Vượt giới hạn thì
    FastAPI trả 422 ngay tại cửa thay vì để một stack trace 10MB đi vào log.
    """

    level: Literal["error", "warn"] = "error"
    event: str = Field(default="unknown", max_length=100)
    message: str = Field(default="", max_length=500)
    url: str | None = Field(default=None, max_length=300)
    stack: str | None = Field(default=None, max_length=2000)
