import time
from typing import Any, Optional

from config import settings


class TTLCache:
    def __init__(self, ttl: int = 60):
        self._store: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, ts = self._store[key]
            if time.time() - ts < self.ttl:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.time())

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


cache = TTLCache(ttl=settings.cache_ttl_seconds)
