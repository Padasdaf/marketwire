# from asyncio import Semaphore
import asyncio
from functools import wraps

class RateLimiter:
    def __init__(self, max_concurrent=5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self):
        await self._semaphore.acquire()

    def release(self):
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()

def rate_limited(func):
    """Decorator to rate limit async functions"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with self.rate_limiter:
            return await func(self, *args, **kwargs)
    return wrapper