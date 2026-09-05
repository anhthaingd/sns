from beanie import Document


class Role(Document):
    name: str | None = None
    value: int = 0

    class Settings:
        name = "roles"
