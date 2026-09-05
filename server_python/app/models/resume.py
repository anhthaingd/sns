from beanie import Document, PydanticObjectId


class Resume(Document):
    user: PydanticObjectId | None = None
    name: str | None = None
    avatar: dict | None = None
    position: str | None = None
    birthday: str | None = None
    email: str | None = None
    address: str | None = None
    phone: str | None = None
    github: str | None = None
    objective: str | None = None
    educationName: str | None = None
    educationMajor: str | None = None
    educationCompletion: str | None = None
    educationGPA: str | None = None
    experiences: list[dict] = []
    skills: list[str] = []
    languages: list[str] = []
    projects: list[dict] = []
    certificates: list[dict] = []

    class Settings:
        name = "resumes"
