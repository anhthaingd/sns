import logging
from urllib.parse import urlsplit

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config.settings import DATABASE_URL
from app.models.channel import Channel
from app.models.chat import Chat
from app.models.company import Company
from app.models.follower import Follower
from app.models.following import Following
from app.models.job import Job
from app.models.newest_message import NewestMessage
from app.models.notification import Notification
from app.models.post import Post
from app.models.resume import Resume
from app.models.role import Role
from app.models.shortcut import Shortcut
from app.models.user import User
from app.models.web import Web

DOCUMENT_MODELS = [
    User,
    Post,
    Channel,
    Chat,
    NewestMessage,
    Notification,
    Follower,
    Following,
    Role,
    Shortcut,
    Web,
    Resume,
    Company,
    Job,
]

logger = logging.getLogger("fuurin.database")

DEFAULT_DB_NAME = "social_app"

_client: AsyncMongoClient | None = None


def _database_name(url: str) -> str:
    """Lấy tên database từ connection string, ví dụ mongodb://host:27017/fuurin -> fuurin."""
    db_name = urlsplit(url).path.lstrip("/")
    return db_name or DEFAULT_DB_NAME


async def connect_db():
    global _client
    _client = AsyncMongoClient(DATABASE_URL, minPoolSize=1, maxPoolSize=50)
    await init_beanie(
        database=_client[_database_name(DATABASE_URL)],
        document_models=DOCUMENT_MODELS,
    )
    logger.info("MongoDB connected!")


async def close_db():
    global _client
    if _client is not None:
        await _client.close()
        _client = None
