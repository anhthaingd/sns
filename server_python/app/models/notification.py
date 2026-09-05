from typing import Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Notification(Document):
    user: Optional[PydanticObjectId] = None
    seeder: Optional[PydanticObjectId] = None
    notification: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isRead: bool = False

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("user", ASCENDING), ("created_at", DESCENDING)], name="user_created_idx"),
        ]
