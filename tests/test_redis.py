"""Tests for Redis connectivity module."""
import pytest
import redis
import redis.asyncio

from skarner.core.redis import RedisConfig, RedisClient, create_redis_client


def test_redis_config_defaults():
    """RedisConfig should have sensible defaults."""
    config = RedisConfig()
    assert config.host == "localhost"
    assert config.port == 6379
    assert config.db == 0
    assert config.password is None
    assert config.socket_timeout == 5.0
    assert config.socket_connect_timeout == 5.0
    assert config.decode_responses is True
    assert config.max_connections == 10


def test_redis_config_custom_values():
    """RedisConfig should accept custom values."""
    config = RedisConfig(
        host="redis.example.com",
        port=6380,
        db=2,
        password="secret",
        max_connections=20,
    )
    assert config.host == "redis.example.com"
    assert config.port == 6380
    assert config.db == 2
    assert config.password == "secret"
    assert config.max_connections == 20


def test_create_async_client_returns_redis_client():
    """create_redis_client should return a RedisClient wrapping async Redis by default."""
    config = RedisConfig()
    client = create_redis_client(config)
    assert isinstance(client, RedisClient)
    assert isinstance(client.client, redis.asyncio.Redis)


def test_create_sync_client_returns_redis_client():
    """create_redis_client with sync=True should return a RedisClient wrapping sync Redis."""
    config = RedisConfig()
    client = create_redis_client(config, sync=True)
    assert isinstance(client, RedisClient)
    assert isinstance(client.client, redis.Redis)
    assert not isinstance(client.client, redis.asyncio.Redis)


def test_redis_client_exposes_underlying_client():
    """RedisClient.client should expose the raw redis-py instance."""
    config = RedisConfig(host="redis.test", port=6380, db=3)
    client = create_redis_client(config)
    # The underlying connection pool should reflect our config
    pool = client.client.connection_pool
    assert pool.connection_kwargs["host"] == "redis.test"
    assert pool.connection_kwargs["port"] == 6380
    assert pool.connection_kwargs["db"] == 3


def test_redis_client_password_forwarded():
    """Password should be forwarded to the underlying client."""
    config = RedisConfig(password="s3cret")
    client = create_redis_client(config)
    pool = client.client.connection_pool
    assert pool.connection_kwargs["password"] == "s3cret"


def test_redis_client_max_connections():
    """max_connections should be forwarded to the connection pool."""
    config = RedisConfig(max_connections=50)
    client = create_redis_client(config)
    pool = client.client.connection_pool
    assert pool.max_connections == 50


async def test_redis_client_close_async():
    """close() should dispose the async connection pool."""
    config = RedisConfig()
    client = create_redis_client(config)
    await client.close()


async def test_redis_client_close_sync():
    """close() on a sync client should not raise."""
    config = RedisConfig()
    client = create_redis_client(config, sync=True)
    await client.close()


async def test_redis_client_async_context_manager():
    """RedisClient should work as an async context manager."""
    config = RedisConfig()
    async with create_redis_client(config) as client:
        assert isinstance(client, RedisClient)
        assert isinstance(client.client, redis.asyncio.Redis)
    # After exiting, the pool should be closed — no error on double-close
    await client.close()


def test_redis_settings_bridge():
    """RedisSettings.to_redis_config() should produce a valid RedisConfig."""
    from skarner.core.config import RedisSettings

    settings = RedisSettings(
        host="redis.prod",
        port=6380,
        db=5,
        password="pw",
        max_connections=100,
    )
    config = settings.to_redis_config()
    assert isinstance(config, RedisConfig)
    assert config.host == "redis.prod"
    assert config.port == 6380
    assert config.db == 5
    assert config.password == "pw"
    assert config.max_connections == 100
