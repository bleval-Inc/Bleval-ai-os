"""Integration Cache — Multi-tier caching for integration data."""

import asyncio
import json
import os
import pickle
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from axiom.runtime.logging import RuntimeLogger

from .models import CacheConfig, CacheStrategy


class IntegrationCache:
    """Multi-tier cache for integration data.

    Supports:
    - Memory-only (L1)
    - Persistent-only (L2, file-based)
    - Tiered (L1 memory + L2 persistent)
    - Write-through / Write-back / Read-through patterns
    """

    def __init__(
        self,
        config: CacheConfig,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config = config
        self.logger = logger or RuntimeLogger()

        # L1: In-memory cache (LRU)
        self._memory_cache: OrderedDict[str, Any] = OrderedDict()
        self._memory_ttl: Dict[str, float] = {}

        # L2: Persistent cache
        self._persistent_path: Optional[Path] = None
        if config.persistent_path:
            self._persistent_path = Path(config.persistent_path)
            self._persistent_path.mkdir(parents=True, exist_ok=True)

        # Stats
        self._hits = 0
        self._misses = 0

        # Background cleanup
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check L1 memory cache
        if key in self._memory_cache:
            # Check TTL
            if key in self._memory_ttl:
                if time.time() > self._memory_ttl[key]:
                    # Expired
                    del self._memory_cache[key]
                    del self._memory_ttl[key]
                else:
                    # Hit - move to end (LRU)
                    self._memory_cache.move_to_end(key)
                    self._hits += 1
                    return self._memory_cache[key]

        # Check L2 persistent cache
        if self.config.strategy in (CacheStrategy.PERSISTENT_ONLY, CacheStrategy.TIERED):
            value = await self._get_persistent(key)
            if value is not None:
                # Promote to L1 if tiered
                if self.config.strategy == CacheStrategy.TIERED:
                    await self._set_memory(key, value)
                self._hits += 1
                return value

        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl_seconds or self.config.memory_ttl_seconds

        if self.config.strategy in (CacheStrategy.MEMORY_ONLY, CacheStrategy.TIERED):
            await self._set_memory(key, value, ttl)

        if self.config.strategy in (CacheStrategy.PERSISTENT_ONLY, CacheStrategy.TIERED, CacheStrategy.WRITE_THROUGH):
            await self._set_persistent(key, value, ttl)

    async def _set_memory(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in memory cache."""
        # Enforce max size (LRU eviction)
        while len(self._memory_cache) >= self.config.memory_max_size:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
            if oldest_key in self._memory_ttl:
                del self._memory_ttl[oldest_key]

        self._memory_cache[key] = value
        self._memory_ttl[key] = time.time() + ttl_seconds
        self._memory_cache.move_to_end(key)

    async def _set_persistent(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in persistent cache."""
        if not self._persistent_path:
            return

        try:
            # Use a safe filename
            safe_key = key.replace(":", "_").replace("/", "_").replace("\\", "_")
            file_path = self._persistent_path / f"{safe_key}.cache"

            cache_entry = {
                "value": value,
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }

            # Write atomically
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                pickle.dump(cache_entry, f)
            temp_path.replace(file_path)

            # Enforce persistent max size
            await self._enforce_persistent_size()

        except Exception as e:
            self.logger.warning(f"Failed to write persistent cache for {key}: {e}")

    async def _get_persistent(self, key: str) -> Optional[Any]:
        """Get value from persistent cache."""
        if not self._persistent_path:
            return None

        try:
            safe_key = key.replace(":", "_").replace("/", "_").replace("\\", "_")
            file_path = self._persistent_path / f"{safe_key}.cache"

            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                cache_entry = pickle.load(f)

            # Check expiry
            expires_at = datetime.fromisoformat(cache_entry["expires_at"])
            if datetime.utcnow() > expires_at:
                # Expired - delete
                file_path.unlink(missing_ok=True)
                return None

            return cache_entry["value"]

        except Exception as e:
            self.logger.warning(f"Failed to read persistent cache for {key}: {e}")
            return None

    async def _enforce_persistent_size(self) -> None:
        """Enforce persistent cache size limit."""
        if not self._persistent_path:
            return

        max_bytes = self.config.persistent_max_size_mb * 1024 * 1024

        # Get all cache files with sizes
        files = []
        for file_path in self._persistent_path.glob("*.cache"):
            try:
                stat = file_path.stat()
                files.append((file_path, stat.st_size, stat.st_mtime))
            except OSError:
                continue

        total_size = sum(f[1] for f in files)

        if total_size <= max_bytes:
            return

        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[2])

        # Remove oldest files until under limit
        for file_path, size, _ in files:
            if total_size <= max_bytes:
                break
            try:
                file_path.unlink()
                total_size -= size
            except OSError:
                continue

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        # L1
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._memory_ttl:
            del self._memory_ttl[key]

        # L2
        if self._persistent_path:
            safe_key = key.replace(":", "_").replace("/", "_").replace("\\", "_")
            file_path = self._persistent_path / f"{safe_key}.cache"
            file_path.unlink(missing_ok=True)

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        self._memory_ttl.clear()

        if self._persistent_path:
            for file_path in self._persistent_path.glob("*.cache"):
                file_path.unlink(missing_ok=True)

    async def size(self) -> int:
        """Get total cache size (memory + persistent)."""
        mem_size = len(self._memory_cache)

        if self._persistent_path:
            persistent_count = len(list(self._persistent_path.glob("*.cache")))
            return mem_size + persistent_count

        return mem_size

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "memory_size": len(self._memory_cache),
            "memory_max_size": self.config.memory_max_size,
        }

    async def _cleanup_loop(self) -> None:
        """Background cleanup of expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"Cache cleanup error: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from memory cache."""
        now = time.time()
        expired_keys = [
            key for key, expiry in self._memory_ttl.items()
            if now > expiry
        ]

        for key in expired_keys:
            if key in self._memory_cache:
                del self._memory_cache[key]
            del self._memory_ttl[key]

        # Also clean persistent (handled on read, but can do proactive)
        if self._persistent_path:
            for file_path in self._persistent_path.glob("*.cache"):
                try:
                    with open(file_path, "rb") as f:
                        cache_entry = pickle.load(f)
                    expires_at = datetime.fromisoformat(cache_entry["expires_at"])
                    if datetime.utcnow() > expires_at:
                        file_path.unlink()
                except Exception:
                    # Corrupted or unreadable - remove
                    file_path.unlink(missing_ok=True)