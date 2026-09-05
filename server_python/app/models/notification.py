from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Notification(Document):
    user: PydanticObjectId | None = None
    seeder: PydanticObjectId | None = None
    notification: str | None = None
    url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isRead: bool = False

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("user", ASCENDING), ("created_at", DESCENDING)], name="user_created_idx"),
        ]
