from typing import Optional
from beanie import Document


class Web(Document):
    logo: Optional[dict] = None
    website_name: Optional[str] = None
    website_quotes_register: Optional[str] = None
    website_quotes_login: Optional[str] = None
    color_title: Optional[str] = None

    class Settings:
        name = "webs"
