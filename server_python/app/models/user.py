from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class ImageField(dict):
    pass


class User(Document):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    address: str | None = None
    intro: str | None = None
    cover_bg: dict | None = Field(default_factory=lambda: {"name": "", "url": ""})
    # KHÔNG phát ảnh mặc định. Bản cũ gán sẵn `avatar-trang.jpg` — một file
    # hình bóng người xám dùng chung — cho mọi tài khoản mới. Hệ quả: nhánh dựng
    # ảnh thay thế bằng chữ cái đầu tên trong `client/src/components/ui/Avatar.jsx`
    # (mỗi người một trong sáu sắc chàm/asagi, chọn theo tên nên cố định) không
    # bao giờ chạy, và trong mọi danh sách mọi người trông giống hệt nhau.
    #
    # Để trống thì `mediaUrl()` trả về null và giao diện tự dựng ảnh thay thế.
    # Tài khoản cũ đã có sẵn trường này: chạy `scripts/clear_default_avatars.py`
    # để gỡ.
    avatar: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    role: PydanticObjectId | None = None
    socketId: str | None = None
    socketCallId: str | None = None

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], name="email_unique", unique=True),
            IndexModel([("socketId", ASCENDING)], name="socketId_idx", sparse=True),
        ]
