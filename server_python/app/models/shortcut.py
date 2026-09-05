from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Shortcut(Document):
    channel: Optional[PydanticObjectId] = None
    user: Optional[PydanticObjectId] = None
    shortcut_count: int = Field(default=0, alias="count")
    isJoin: bool = False

    class Settings:
        name = "shortcuts"
        use_state_management = True
        indexes = [
            IndexModel([("user", ASCENDING), ("channel", ASCENDING)], name="user_channel_unique", unique=True),
        ]

    model_config = {"populate_by_name": True}
