from typing import Optional, List
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Comment(dict):
    pass


class Post(Document):
    user: Optional[PydanticObjectId] = None
    content: Optional[str] = None
    images: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    liked: List[PydanticObjectId] = Field(default_factory=list)
    book_marked: List[PydanticObjectId] = Field(default_factory=list)
    comments: List[dict] = Field(default_factory=list)
    channel: Optional[PydanticObjectId] = None

    class Settings:
        name = "posts"
        indexes = [
            IndexModel([("channel", ASCENDING), ("created_at", DESCENDING)], name="channel_created_idx"),
            IndexModel([("user", ASCENDING), ("created_at", DESCENDING)], name="user_created_idx"),
            IndexModel([("book_marked", ASCENDING)], name="book_marked_idx"),
        ]
