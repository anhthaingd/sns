"""Giới hạn tần suất theo cửa sổ cố định (Redis INCR + EXPIRE).

Hai tầng bảo vệ cho đăng nhập, cố ý chỉ đếm LẦN THẤT BẠI:

1. **Theo email** (chặt, mặc định 10 lần/15 phút) — chặn dò mật khẩu của một
   tài khoản cụ thể. Đây là tầng có ý nghĩa nhất.
2. **Theo IP** (rộng hơn, mặc định 30 lần/15 phút) — chặn kiểu rải một mật khẩu
   phổ biến qua nhiều tài khoản.

Chỉ đếm lần thất bại nên người dùng bình thường (và bộ test, vốn đăng nhập rất
nhiều lần thành công) không bao giờ chạm ngưỡng.
"""

import logging
import time

from fastapi import Request

from app.config.redis_client import get_redis
from app.config.settings import RATE_LIMIT_ENABLED, TRUST_PROXY_HEADERS
from app.errors import ApiError

logger = logging.getLogger("fuurin.rate_limit")

_KEY_PREFIX = "fuurin:ratelimit:"
TOO_MANY_REQUESTS_MESSAGE = "Bạn thao tác quá nhiều lần, vui lòng thử lại sau ít phút!"

# Fallback khi không có Redis: {key: (count, expires_at_monotonic)}
_memory_counters: dict[str, tuple[int, float]] = {}
_MEMORY_COUNTERS_MAX = 10_000


def client_ip(request: Request) -> str:
    """IP của client.

    `X-Forwarded-For` do client tự gửi được, nên chỉ đọc khi đã khai báo tường
    minh là có reverse proxy đứng trước (`TRUST_PROXY_HEADERS=true`). Tin nó vô
    điều kiện đồng nghĩa với việc vô hiệu hoá giới hạn theo IP.
    """
    if TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _key(bucket: str, identity: str) -> str:
    return f"{_KEY_PREFIX}{bucket}:{identity}"


def _memory_count(key: str) -> int:
    count, expires_at = _memory_counters.get(key, (0, 0.0))
    return count if time.monotonic() < expires_at else 0


def _memory_incr(key: str, window: int) -> int:
    now = time.monotonic()
    count, expires_at = _memory_counters.get(key, (0, 0.0))
    if now >= expires_at:
        count, expires_at = 0, now + window
    count += 1
    _memory_counters[key] = (count, expires_at)
    if len(_memory_counters) > _MEMORY_COUNTERS_MAX:
        for stale in [k for k, (_, exp) in _memory_counters.items() if now >= exp]:
            _memory_counters.pop(stale, None)
    return count


async def current_count(bucket: str, identity: str) -> int:
    key = _key(bucket, identity)
    redis = get_redis()
    if redis is None:
        return _memory_count(key)
    try:
        raw = await redis.get(key)
        return int(raw) if raw else 0
    except Exception:
        logger.exception("Không đọc được bộ đếm rate limit từ Redis")
        return _memory_count(key)


async def ensure_under_limit(bucket: str, identity: str, limit: int) -> None:
    """Chặn TRƯỚC khi xử lý nếu đã vượt ngưỡng. Không tăng bộ đếm."""
    if not RATE_LIMIT_ENABLED or not identity:
        return
    if await current_count(bucket, identity) >= limit:
        raise ApiError(429, TOO_MANY_REQUESTS_MESSAGE)


async def record_failure(bucket: str, identity: str, window_seconds: int) -> None:
    """Ghi nhận một lần thất bại."""
    if not RATE_LIMIT_ENABLED or not identity:
        return
    key = _key(bucket, identity)
    redis = get_redis()
    if redis is None:
        _memory_incr(key, window_seconds)
        return
    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        # nx=True: chỉ đặt hạn ở lần đầu -> cửa sổ cố định, không bị "gia hạn"
        # mỗi lần thử khiến người dùng bị khoá vĩnh viễn.
        pipe.expire(key, window_seconds, nx=True)
        await pipe.execute()
    except Exception:
        logger.exception("Rate limit không dùng được Redis, tạm đếm trong bộ nhớ")
        _memory_incr(key, window_seconds)


async def reset(bucket: str, identity: str) -> None:
    """Xoá bộ đếm — gọi khi đăng nhập thành công."""
    if not identity:
        return
    key = _key(bucket, identity)
    _memory_counters.pop(key, None)
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.delete(key)
    except Exception:
        logger.exception("Không xoá được bộ đếm rate limit")


async def hit(bucket: str, identity: str, limit: int, window_seconds: int) -> None:
    """Đếm mọi lần gọi (không chỉ thất bại) rồi chặn khi vượt ngưỡng."""
    if not RATE_LIMIT_ENABLED:
        return
    await record_failure(bucket, identity, window_seconds)
    if await current_count(bucket, identity) > limit:
        raise ApiError(429, TOO_MANY_REQUESTS_MESSAGE)


def rate_limit(bucket: str, limit: int, window_seconds: int):
    """Dependency cho FastAPI, đếm theo IP: `dependencies=[Depends(rate_limit(...))]`."""

    async def dependency(request: Request) -> None:
        await hit(bucket, client_ip(request), limit, window_seconds)

    return dependency
