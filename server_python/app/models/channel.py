from typing import Optional, List
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Channel(Document):
    name: Optional[str] = None
    intro: Optional[str] = None
    background: Optional[dict] = None
    members: List[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "channels"
        indexes = [
            IndexModel([("name", ASCENDING)], name="name_unique", unique=True),
            IndexModel([("members", ASCENDING)], name="members_idx"),
        ]
