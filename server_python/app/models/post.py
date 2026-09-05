from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class Comment(dict):
    pass


class Post(Document):
    user: PydanticObjectId | None = None
    content: str | None = None
    images: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    liked: list[PydanticObjectId] = Field(default_factory=list)
    book_marked: list[PydanticObjectId] = Field(default_factory=list)
    comments: list[dict] = Field(default_factory=list)
    channel: PydanticObjectId | None = None

    class Settings:
        name = "posts"
        indexes = [
            IndexModel([("channel", ASCENDING), ("created_at", DESCENDING)], name="channel_created_idx"),
            IndexModel([("user", ASCENDING), ("created_at", DESCENDING)], name="user_created_idx"),
            IndexModel([("book_marked", ASCENDING)], name="book_marked_idx"),
        ]
