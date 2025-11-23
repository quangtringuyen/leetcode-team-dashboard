# backend/utils/cache.py
"""Simple async LRU cache with TTL for in‑process use.
No external dependencies – pure Python.
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Tuple

def async_lru_cache(maxsize: int = 128, ttl: int = 300):
    """Wrap an async function with an LRU cache that expires after *ttl* seconds.
    The cache key is the tuple of positional args + frozenset of kwargs.
    """
    def decorator(fn: Callable):
        cache: dict[Tuple[Any, ...], Tuple[float, Any]] = {}
        lock = asyncio.Lock()

        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            async with lock:
                now = asyncio.get_event_loop().time()
                if key in cache:
                    ts, val = cache[key]
                    if now - ts < ttl:
                        return val
                    # expired
                    del cache[key]
                # compute fresh
                result = await fn(*args, **kwargs)
                cache[key] = (now, result)
                # enforce maxsize
                if len(cache) > maxsize:
                    oldest = min(cache.items(), key=lambda i: i[1][0])[0]
                    del cache[oldest]
                return result
        return wrapper
    return decorator
