from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Notification(Document):
    user: PydanticObjectId | None = None
    seeder: PydanticObjectId | None = None
    # Câu chữ dựng sẵn. Với bản ghi mới đây chỉ là bản dự phòng: giao diện ưu
    # tiên dịch theo `code`. Giữ lại để những bản ghi tạo TRƯỚC khi có `code`
    # vẫn đọc được, nên không phải migrate dữ liệu cũ.
    notification: str | None = None
    # Mã ổn định + tham số thô, cùng cơ chế với `ApiError` và `ok`.
    code: str | None = None
    params: dict = Field(default_factory=dict)
    url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isRead: bool = False

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("user", ASCENDING), ("created_at", DESCENDING)], name="user_created_idx"),
        ]
