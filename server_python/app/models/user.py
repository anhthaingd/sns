from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class ImageField(dict):
    pass


class User(Document):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    address: str | None = None
    intro: str | None = None
    cover_bg: dict | None = Field(default_factory=lambda: {"name": "", "url": ""})
    avatar: dict | None = Field(default_factory=lambda: {"name": "avatar_trang.jpg", "url": "public/avatar-trang.jpg"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    role: PydanticObjectId | None = None
    socketId: str | None = None
    socketCallId: str | None = None

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], name="email_unique", unique=True),
            IndexModel([("socketId", ASCENDING)], name="socketId_idx", sparse=True),
        ]
