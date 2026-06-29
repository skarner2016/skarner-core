"""Redis configuration dataclass."""
from dataclasses import dataclass

__all__ = ["RedisConfig"]


@dataclass
class RedisConfig:
    """Redis connection configuration.

    Mirrors the pattern established by ``DatabaseConfig``: a plain dataclass
    that carries all the knobs needed to build a Redis client, without any
    framework dependency.

    Args:
        host: Redis server hostname.
        port: Redis server port.
        db: Redis database index.
        password: Optional authentication password.
        socket_timeout: Timeout for socket read operations (seconds).
        socket_connect_timeout: Timeout for initial connection (seconds).
        decode_responses: Decode byte responses to str using UTF-8.
        max_connections: Maximum number of connections in the pool.
    """

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    decode_responses: bool = True
    max_connections: int = 10
