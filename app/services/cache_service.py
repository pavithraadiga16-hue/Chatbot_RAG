"""
PhinsIQ Cache Service (Redis with In-Memory Fallback)
=====================================================

PURPOSE:
    Provides fast, async caching for user queries to eliminate repeated
    database lookups and redundant RAG vector processing.

SECURITY & ISOLATION:
    - Non-personal institutional RAG queries are cached using a normalized
      key such as: phinsiq:cache:rag:{institution_id}:{normalized_query}
      These can safely be reused across different students.
    - Personal student-specific queries (fee balance, attendance, marks, etc.)
      are cached under a strictly isolated student key:
      phinsiq:cache:student:{institution_id}:{user_id}:{normalized_query}
      This ensures student private records are NEVER leaked to other students.

RESILIENCY:
    - If a Redis server is active, all operations run against Redis.
    - If Redis is unavailable or offline, the service automatically falls back
      to an in-memory TTL cache without raising exceptions or breaking queries.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def normalize_cache_query(query: str) -> str:
    """Normalize query text for cache key matching."""
    text = query.strip().lower()
    # Collapse multiple whitespaces and strip standard punctuation
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


class CacheService:
    """Async Redis cache service with safe local in-memory fallback."""

    def __init__(self) -> None:
        self._redis_client = None
        self._redis_available: Optional[bool] = None
        self._local_cache: dict[str, tuple[float, str]] = {}  # key -> (expire_at, json_data)

    async def _get_client(self):
        if not settings.redis_enabled:
            return None

        if self._redis_available is False:
            return None

        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis
                url = settings.redis_url
                self._redis_client = aioredis.from_url(
                    url,
                    socket_connect_timeout=0.5,
                    socket_timeout=1.0,
                    decode_responses=True,
                )
                await self._redis_client.ping()
                self._redis_available = True
                logger.info("redis_connected", url=url.split("@")[-1])
            except Exception as exc:
                self._redis_available = False
                logger.warning("redis_unavailable_fallback_to_memory", error=str(exc))
                return None

        return self._redis_client

    def build_key(
        self,
        institution_id: str,
        query: str,
        user_id: Optional[str] = None,
        is_student_specific: bool = False,
    ) -> str:
        """
        Generate cache key with strict student data isolation.

        If is_student_specific is True, user_id MUST be included in the key.
        """
        norm_q = normalize_cache_query(query)
        inst = institution_id.lower().strip()
        if is_student_specific and user_id:
            return f"phinsiq:cache:student:{inst}:{user_id.lower().strip()}:{norm_q}"
        return f"phinsiq:cache:rag:{inst}:{norm_q}"

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        """Retrieve cached response data. Returns None on cache miss."""
        client = await self._get_client()

        if client is not None:
            try:
                cached_str = await client.get(key)
                if cached_str:
                    logger.info("[CACHE] HIT (Redis)", key=key)
                    print(f"[CACHE] HIT")
                    return json.loads(cached_str)
                else:
                    logger.info("[CACHE] MISS (Redis)", key=key)
                    print(f"[CACHE] MISS")
                    return None
            except Exception as exc:
                logger.warning("redis_get_failed_fallback_to_memory", error=str(exc))

        # In-memory fallback
        now = time.time()
        entry = self._local_cache.get(key)
        if entry:
            expire_at, cached_str = entry
            if expire_at > now:
                logger.info("[CACHE] HIT (in-memory)", key=key)
                print(f"[CACHE] HIT")
                return json.loads(cached_str)
            else:
                self._local_cache.pop(key, None)

        logger.info("[CACHE] MISS", key=key)
        print(f"[CACHE] MISS")
        return None

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store serialized response in cache with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else settings.redis_ttl_general
        serialized = json.dumps(value)

        client = await self._get_client()
        if client is not None:
            try:
                await client.set(key, serialized, ex=ttl)
                return
            except Exception as exc:
                logger.warning("redis_set_failed_fallback_to_memory", error=str(exc))

        # In-memory fallback
        self._local_cache[key] = (time.time() + ttl, serialized)
        # Limit memory cache size
        if len(self._local_cache) > 2000:
            now = time.time()
            expired = [k for k, (exp, _) in self._local_cache.items() if exp <= now]
            for k in expired:
                self._local_cache.pop(k, None)
            if len(self._local_cache) > 2000:
                # Remove oldest entries
                oldest_keys = sorted(self._local_cache.keys(), key=lambda k: self._local_cache[k][0])[:500]
                for k in oldest_keys:
                    self._local_cache.pop(k, None)

    async def clear(self) -> None:
        """Clear cache (primarily for tests)."""
        self._local_cache.clear()
        client = await self._get_client()
        if client is not None:
            try:
                # Flush only phinsiq cache keys
                keys = await client.keys("phinsiq:cache:*")
                if keys:
                    await client.delete(*keys)
            except Exception:
                pass


cache_service = CacheService()
