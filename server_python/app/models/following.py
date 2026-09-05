from typing import List
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Following(Document):
    user: PydanticObjectId
    following: List[PydanticObjectId] = Field(default_factory=list)

    class Settings:
        name = "followings"
        indexes = [IndexModel([("user", ASCENDING)], name="user_unique", unique=True)]
