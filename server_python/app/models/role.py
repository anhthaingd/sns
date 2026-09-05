from typing import Optional
from beanie import Document
from pydantic import Field


class Role(Document):
    name: Optional[str] = None
    value: int = 0

    class Settings:
        name = "roles"
