from typing import List
from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class Follower(Document):
    user: PydanticObjectId
    followers: List[PydanticObjectId] = Field(default_factory=list)

    class Settings:
        name = "followers"
        indexes = [IndexModel([("user", ASCENDING)], name="user_unique", unique=True)]
