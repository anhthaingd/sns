"""Schema cho request body JSON.

Trước đây các route nhận `body: dict` nên mọi giá trị đều lọt xuống tầng truy
vấn mà không ai kiểm tra kiểu: `POST /api/users/login` với
`{"email": 123, "password": []}` vẫn đi thẳng vào Mongo. Khai báo tường minh ở
đây giúp FastAPI trả 422 ngay tại cửa và sinh tài liệu ở /docs.
"""

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
