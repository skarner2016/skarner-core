"""Redis client wrapper and factory function."""
from __future__ import annotations

from typing import Union

import redis
import redis.asyncio

from .config import RedisConfig

__all__ = ["RedisClient", "create_redis_client"]

# Type alias for the underlying client (sync or async).
_RawClient = Union[redis.Redis, redis.asyncio.Redis]


class RedisClient:
    """Thin wrapper around a redis-py client for lifecycle management.

    Provides a uniform interface for both sync and async clients, with
    explicit ``close()`` for connection pool disposal and ``ping()`` for
    health checks.

    Usage:
        config = RedisConfig(host="localhost", port=6379)
        client = create_redis_client(config)          # async by default
        sync_client = create_redis_client(config, sync=True)

        async with client:
            await client.ping()
            value = await client.client.get("key")
    """

    def __init__(self, raw: _RawClient) -> None:
        self._raw = raw

    @property
    def client(self) -> _RawClient:
        """Access the underlying redis-py client instance."""
        return self._raw

    async def ping(self) -> bool:
        """Health check. Works for both sync and async clients.

        Returns:
            True if the Redis server is reachable.
        """
        if isinstance(self._raw, redis.asyncio.Redis):
            return await self._raw.ping()
        return self._raw.ping()

    async def close(self) -> None:
        """Close the connection pool and release all connections."""
        if isinstance(self._raw, redis.asyncio.Redis):
            await self._raw.aclose()
        else:
            self._raw.close()

    async def __aenter__(self) -> RedisClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()


def create_redis_client(config: RedisConfig, *, sync: bool = False) -> RedisClient:
    """Create a RedisClient from a RedisConfig.

    Args:
        config: Connection configuration.
        sync: If True, return a synchronous client; otherwise async (default).

    Returns:
        A RedisClient wrapping the raw redis-py client.
    """
    kwargs = {
        "host": config.host,
        "port": config.port,
        "db": config.db,
        "password": config.password,
        "socket_timeout": config.socket_timeout,
        "socket_connect_timeout": config.socket_connect_timeout,
        "decode_responses": config.decode_responses,
        "max_connections": config.max_connections,
    }

    if sync:
        raw: _RawClient = redis.Redis(**kwargs)
    else:
        raw = redis.asyncio.Redis(**kwargs)

    return RedisClient(raw)
