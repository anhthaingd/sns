"""Kết nối Redis dùng chung, quản lý theo vòng đời ứng dụng.

Redis giữ hai loại trạng thái bắt buộc phải chung cho mọi tiến trình:
danh sách token bị thu hồi và bộ đếm rate limit. Nếu không cấu hình
`REDIS_URL`, ứng dụng vẫn chạy được (fallback trong RAM) để `uvicorn` dev hay
script tiện ích không bắt buộc phải dựng Redis — nhưng log cảnh báo rõ rằng
trạng thái sẽ mất khi restart.
"""

import logging

from redis.asyncio import Redis

from app.config.settings import REDIS_URL

logger = logging.getLogger("fuurin.redis")

_redis: Redis | None = None


async def connect_redis() -> Redis | None:
    global _redis
    if not REDIS_URL:
        logger.warning("REDIS_URL trống — dùng bộ nhớ tiến trình, trạng thái sẽ mất khi restart")
        return None
    client = Redis.from_url(REDIS_URL, decode_responses=True)
    try:
        await client.ping()
    except Exception:
        logger.exception("Không kết nối được Redis (%s) — chuyển sang bộ nhớ tiến trình", REDIS_URL)
        await client.aclose()
        return None
    _redis = client
    logger.info("Redis connected!")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis | None:
    return _redis
