"""Danh sách token bị thu hồi (blacklist), chia sẻ giữa mọi tiến trình.

Trước đây là `blacklist: set = set()` trong RAM tiến trình. Đã kiểm chứng được
hậu quả: đăng xuất -> token bị chặn (401), nhưng sau `docker compose restart
server` thì CHÍNH token đó lại dùng được (200). Nói cách khác, đăng xuất chỉ có
hiệu lực tới lần restart kế tiếp, và token bị lộ thì không có cách nào thu hồi
trong suốt 7 ngày.

Lưu theo `jti` (định danh của token) chứ không lưu cả chuỗi token: khoá ngắn,
và đặt TTL đúng bằng thời điểm token hết hạn nên Redis tự dọn, không phình.
"""

import logging
import time

from app.config.redis_client import get_redis

logger = logging.getLogger("fuurin.token_store")

_KEY_PREFIX = "fuurin:revoked_jti:"

# Fallback khi không có Redis: {jti: thời điểm hết hạn}. Không dùng TTLCache vì
# ở đó mọi mục dùng chung một TTL, còn access token (15 phút) và refresh token
# (7 ngày) có hạn rất khác nhau — giữ access token 7 ngày là phí bộ nhớ vô ích.
_memory_store: dict[str, float] = {}
_MEMORY_STORE_MAX = 10_000


def _memory_revoke(jti: str, ttl_seconds: int) -> None:
    now = time.monotonic()
    if len(_memory_store) >= _MEMORY_STORE_MAX:
        for stale in [k for k, exp in _memory_store.items() if now >= exp]:
            _memory_store.pop(stale, None)
    _memory_store[jti] = now + ttl_seconds


def _memory_is_revoked(jti: str) -> bool:
    expires_at = _memory_store.get(jti)
    if expires_at is None:
        return False
    if time.monotonic() >= expires_at:
        _memory_store.pop(jti, None)
        return False
    return True


async def revoke(jti: str, ttl_seconds: int) -> None:
    if not jti:
        return
    ttl = max(int(ttl_seconds), 1)
    redis = get_redis()
    if redis is None:
        _memory_revoke(jti, ttl)
        return
    try:
        await redis.setex(f"{_KEY_PREFIX}{jti}", ttl, "1")
    except Exception:
        logger.exception("Không ghi được blacklist vào Redis, tạm ghi vào bộ nhớ")
        _memory_revoke(jti, ttl)


async def is_revoked(jti: str) -> bool:
    if not jti:
        return False
    if _memory_is_revoked(jti):
        return True
    redis = get_redis()
    if redis is None:
        return False
    try:
        return await redis.exists(f"{_KEY_PREFIX}{jti}") == 1
    except Exception:
        # Redis chết không được phép làm sập xác thực; log rồi cho qua.
        logger.exception("Không đọc được blacklist từ Redis")
        return False
