from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Channel(Document):
    name: str | None = None
    intro: str | None = None
    background: dict | None = None
    members: list[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "channels"
        indexes = [
            IndexModel([("name", ASCENDING)], name="name_unique", unique=True),
            IndexModel([("members", ASCENDING)], name="members_idx"),
        ]
