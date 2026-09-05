from beanie import Document


class Web(Document):
    logo: dict | None = None
    website_name: str | None = None
    website_quotes_register: str | None = None
    website_quotes_login: str | None = None
    color_title: str | None = None

    class Settings:
        name = "webs"
