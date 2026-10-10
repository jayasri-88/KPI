"""
Redis Caching Layer for Retail KPI Intelligence Platform
Provides deterministic key generation, TTL control, structured logging,
cache invalidation hooks, and graceful fallback to direct PostgreSQL queries
when Redis is unavailable or disconnected.
"""

import functools
import json
import logging
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
import uuid

import redis
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("retail_kpi.cache")

T = TypeVar("T")

# Standard TTL Definitions (in seconds)
TTL_DASHBOARD_KPIS = 300       # 5 minutes
TTL_STORE_PERFORMANCE = 600    # 10 minutes
TTL_PRODUCT_PERFORMANCE = 600  # 10 minutes
TTL_SALES_TRENDS = 900         # 15 minutes
TTL_DEMAND_ANALYTICS = 900     # 15 minutes
TTL_FORECAST = 3600            # 1 hour
TTL_AI_SESSION = 86400         # 24 hours
TTL_DEFAULT = 300              # 5 minutes


class CacheJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder supporting Pydantic, Decimals, UUIDs, Dates, and NumPy types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Handle numpy scalars if present
        try:
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
        except ImportError:
            pass

        return super().default(obj)


RECONNECT_COOLDOWN_SECONDS = 15.0


class RedisCacheManager:
    """
    Manages Redis connection, cache get/set/invalidate operations,
    and maintains hit/miss performance metrics with zero latency fallback.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._is_connected: bool = False
        self._last_connect_attempt: float = 0.0
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "errors": 0,
        }
        self._init_connection()

    def _init_connection(self) -> None:
        """Initializes Redis client with RESP2 protocol for wide compatibility."""
        self._last_connect_attempt = time.time()
        try:
            # Note: protocol=2 is explicitly passed to support Redis 3.x-7.x on Windows/Linux
            self._client = redis.from_url(
                self.redis_url,
                protocol=2,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            self._client.ping()
            self._is_connected = True
            logger.info("[REDIS CONNECTED] Successfully connected to Redis at %s", self.redis_url)
        except Exception as exc:
            self._is_connected = False
            self._client = None
            logger.warning(
                "[REDIS UNAVAILABLE] Could not connect to Redis at %s: %s. "
                "Operating in GRACEFUL FALLBACK mode (direct PostgreSQL queries).",
                self.redis_url,
                exc,
            )

    @property
    def is_available(self) -> bool:
        """Verifies live Redis connectivity with non-blocking cooldown."""
        if not self._is_connected or not self._client:
            # Only retry connection if cooldown has elapsed
            if time.time() - self._last_connect_attempt > RECONNECT_COOLDOWN_SECONDS:
                self._init_connection()
            return self._is_connected

        try:
            self._client.ping()
            return True
        except Exception as exc:
            self._is_connected = False
            self._last_connect_attempt = time.time()
            logger.warning("[REDIS DISCONNECTED] Ping failed: %s", exc)
            return False

    @property
    def stats(self) -> Dict[str, int]:
        """Returns runtime cache performance metrics (hits, misses, sets, invalidations)."""
        return dict(self._stats)


    @staticmethod
    def build_key(namespace: str, **kwargs: Any) -> str:
        """
        Builds a deterministic, sorted cache key including namespace and parameter filters.
        Example:
            build_key("kpi:dashboard", start_date="2025-01-01", end_date="2025-12-31")
            -> "retail:kpi:dashboard:end_date=2025-12-31:start_date=2025-01-01"
        """
        tokens = []
        for k in sorted(kwargs.keys()):
            val = kwargs[k]
            if val is None:
                continue
            if isinstance(val, (datetime, date)):
                val_str = val.isoformat()
            else:
                val_str = str(val).strip().lower()
            tokens.append(f"{k}={val_str}")

        param_str = ":".join(tokens)
        if param_str:
            return f"retail:{namespace}:{param_str}"
        return f"retail:{namespace}:default"

    def get(self, key: str, schema_cls: Optional[Type[T]] = None) -> Optional[Any]:
        """
        Retrieves an item from cache.
        Returns parsed JSON or validated Pydantic model if schema_cls is provided.
        Falls back gracefully if Redis is unavailable.
        """
        if not self.is_available:
            self._stats["misses"] += 1
            logger.debug("[CACHE MISS - REDIS OFFLINE] Key: %s -> Bypassing to DB", key)
            return None

        try:
            raw = self._client.get(key)
            if raw is None:
                self._stats["misses"] += 1
                logger.info("[CACHE MISS] Key: %s", key)
                return None

            self._stats["hits"] += 1
            logger.info("[CACHE HIT] Key: %s", key)
            data = json.loads(raw)

            if schema_cls and issubclass(schema_cls, BaseModel):
                if isinstance(data, list):
                    return [schema_cls.model_validate(item) for item in data]
                return schema_cls.model_validate(data)

            return data

        except Exception as exc:
            self._stats["errors"] += 1
            self._stats["misses"] += 1
            logger.warning("[REDIS ERROR] Failed to get key '%s': %s. Falling back to DB.", key, exc)
            return None

    def set(self, key: str, value: Any, ttl: int = TTL_DEFAULT) -> bool:
        """
        Saves a value in Redis with the specified TTL.
        Returns True if successful, False if Redis failed (graceful fallback).
        """
        if not self.is_available:
            return False

        try:
            serialized = json.dumps(value, cls=CacheJSONEncoder)
            self._client.setex(key, ttl, serialized)
            self._stats["sets"] += 1
            logger.info("[CACHE SET] Key: %s (TTL: %ds, Size: %d bytes)", key, ttl, len(serialized))
            return True
        except Exception as exc:
            self._stats["errors"] += 1
            logger.warning("[REDIS ERROR] Failed to set key '%s': %s", key, exc)
            return False

    def delete(self, key: str) -> bool:
        """Deletes a specific cache key."""
        if not self.is_available:
            return False
        try:
            res = self._client.delete(key)
            logger.info("[CACHE DELETE] Key: %s (Deleted: %s)", key, bool(res))
            return bool(res)
        except Exception as exc:
            self._stats["errors"] += 1
            logger.warning("[REDIS ERROR] Failed to delete key '%s': %s", key, exc)
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Invalidates all keys matching the glob pattern (e.g., 'retail:kpi:*').
        Logs the exact count of keys invalidated.
        """
        if not self.is_available:
            return 0

        try:
            # Ensure pattern is prefixed
            full_pattern = pattern if pattern.startswith("retail:") else f"retail:{pattern}"
            keys = self._client.keys(full_pattern)
            if keys:
                count = self._client.delete(*keys)
                self._stats["invalidations"] += count
                logger.info("[CACHE INVALIDATE] Pattern '%s' matched & deleted %d keys", full_pattern, count)
                return count
            else:
                logger.info("[CACHE INVALIDATE] Pattern '%s' matched 0 keys", full_pattern)
                return 0
        except Exception as exc:
            self._stats["errors"] += 1
            logger.warning("[REDIS ERROR] Failed to invalidate pattern '%s': %s", pattern, exc)
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache operational statistics and health."""
        available = self.is_available
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_ratio = (self._stats["hits"] / total_requests * 100.0) if total_requests > 0 else 0.0

        key_count = 0
        redis_info = {}
        if available and self._client:
            try:
                keys = self._client.keys("retail:*")
                key_count = len(keys)
                info = self._client.info()
                redis_info = {
                    "version": info.get("redis_version", "unknown"),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime_days": info.get("uptime_in_days", 0),
                }
            except Exception:
                pass

        return {
            "status": "connected" if available else "offline_fallback",
            "redis_url": self.redis_url.split("@")[-1],  # hide password if present
            "hit_ratio_pct": round(hit_ratio, 2),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "invalidations": self._stats["invalidations"],
            "errors": self._stats["errors"],
            "cached_keys_count": key_count,
            "redis_server": redis_info,
        }

    # -------------------------------------------------------------------------
    # Domain Invalidation Helpers
    # -------------------------------------------------------------------------
    def invalidate_dashboard_kpis(self) -> int:
        """Invalidates all cached dashboard overview and KPI keys."""
        return self.delete_pattern("kpi:dashboard:*")

    def invalidate_store_performance(self) -> int:
        """Invalidates store performance and geospatial caches."""
        return self.delete_pattern("analytics:store_perf:*")

    def invalidate_product_performance(self) -> int:
        """Invalidates product velocity and performance caches."""
        return self.delete_pattern("analytics:product_perf:*")

    def invalidate_sales_trends(self) -> int:
        """Invalidates sales time series trend caches."""
        return self.delete_pattern("analytics:sales_trend:*")

    def invalidate_all_analytics(self) -> int:
        """Invalidates all retail KPI and analytics caches."""
        count = self.delete_pattern("kpi:*")
        count += self.delete_pattern("analytics:*")
        count += self.delete_pattern("forecast:*")
        return count


# Global Cache Manager Singleton
cache_manager = RedisCacheManager(settings.redis_url)


def cached(
    namespace: str,
    ttl: int = TTL_DEFAULT,
    schema_cls: Optional[Type[BaseModel]] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching function results in Redis.
    Demonstrates:
      1. Cache Lookup -> Hit returns immediately
      2. Cache Miss -> Executes underlying DB function -> Saves in Redis -> Returns
      3. Graceful Fallback -> If Redis offline, executes DB function without interruption
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Strip db session from kwargs if passed
                clean_kwargs = {k: v for k, v in kwargs.items() if k != "db"}
                cache_key = cache_manager.build_key(namespace, **clean_kwargs)

            # 1. Attempt Cache Get
            cached_val = cache_manager.get(cache_key, schema_cls=schema_cls)
            if cached_val is not None:
                return cached_val

            # 2. Cache Miss -> Execute Database Query
            logger.info("[DB QUERY TRIGGERED] Function '%s' executing against PostgreSQL for key: %s", func.__name__, cache_key)
            result = func(*args, **kwargs)

            # 3. Cache Set
            cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator
