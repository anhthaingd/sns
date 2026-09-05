"""Cache đơn giản trong bộ nhớ tiến trình, có hạn dùng (TTL).

Cố ý KHÔNG dùng Redis: đây là cache đọc-lại-được, mỗi worker giữ bản riêng là
chấp nhận được, và giữ nó độc lập giúp chức năng crawl không chết theo Redis.
"""

import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: float, max_entries: int = 128):
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._store: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        # time.monotonic(): không bị nhảy khi hệ thống chỉnh lại đồng hồ.
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: Any, value: Any) -> None:
        if len(self._store) >= self._max_entries:
            self._evict_expired()
        if len(self._store) >= self._max_entries:
            # Vẫn đầy sau khi dọn -> bỏ mục cũ nhất.
            oldest = min(self._store, key=lambda k: self._store[k][0])
            self._store.pop(oldest, None)
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()

    def _evict_expired(self) -> None:
        now = time.monotonic()
        for key in [k for k, (exp, _) in self._store.items() if now >= exp]:
            self._store.pop(key, None)
