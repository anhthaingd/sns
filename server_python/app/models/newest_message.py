from typing import Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field


class NewestMessage(Document):
    sender: Optional[dict] = None
    receiver: Optional[dict] = None
    content: Optional[str] = None
    lastSent: Optional[PydanticObjectId] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "newestmessages"
