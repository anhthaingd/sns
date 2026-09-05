from typing import Optional, List
from beanie import Document, PydanticObjectId


class Resume(Document):
    user: Optional[PydanticObjectId] = None
    name: Optional[str] = None
    avatar: Optional[dict] = None
    position: Optional[str] = None
    birthday: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    github: Optional[str] = None
    objective: Optional[str] = None
    educationName: Optional[str] = None
    educationMajor: Optional[str] = None
    educationCompletion: Optional[str] = None
    educationGPA: Optional[str] = None
    experiences: List[dict] = []
    skills: List[str] = []
    languages: List[str] = []
    projects: List[dict] = []
    certificates: List[dict] = []

    class Settings:
        name = "resumes"
