from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Chat(Document):
    sender: PydanticObjectId
    receiver: PydanticObjectId
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    read_at: datetime | None = None

    class Settings:
        name = "chats"
        indexes = [
            IndexModel(
                [("sender", ASCENDING), ("receiver", ASCENDING), ("timestamp", DESCENDING)],
                name="conversation_idx",
            ),
        ]
