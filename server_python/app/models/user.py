from typing import Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel


class ImageField(dict):
    pass


class User(Document):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    intro: Optional[str] = None
    cover_bg: Optional[dict] = Field(default_factory=lambda: {"name": "", "url": ""})
    avatar: Optional[dict] = Field(default_factory=lambda: {"name": "avatar_trang.jpg", "url": "public/avatar-trang.jpg"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    role: Optional[PydanticObjectId] = None
    socketId: Optional[str] = None
    socketCallId: Optional[str] = None

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], name="email_unique", unique=True),
            IndexModel([("socketId", ASCENDING)], name="socketId_idx", sparse=True),
        ]
