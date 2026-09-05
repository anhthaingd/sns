from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field


class NewestMessage(Document):
    sender: dict | None = None
    receiver: dict | None = None
    content: str | None = None
    lastSent: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "newestmessages"
