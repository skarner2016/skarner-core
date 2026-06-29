from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from skarner.core.db.engine import DatabaseConfig, DatabaseDialect
from skarner.core.redis.config import RedisConfig

__all__ = [
    "Settings",
    "JWTSettings",
    "DatabaseSettings",
    "RedisSettings",
]


class JWTSettings(BaseModel):
    """JWT signing configuration. Bridges to skarner.core.auth.JWTManager."""

    secret: SecretStr
    algorithm: str = "HS256"
    expires_in: int = 3600


class DatabaseSettings(BaseModel):
    """Database configuration. Bridges to skarner.core.db.DatabaseConfig."""

    dialect: DatabaseDialect
    host: str = "localhost"
    port: int = 3306
    user: str
    password: str
    database: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    def to_database_config(self) -> DatabaseConfig:
        """Convert to the framework-agnostic DatabaseConfig consumed by create_engine()."""
        return DatabaseConfig(
            dialect=self.dialect,
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=self.echo,
        )


class RedisSettings(BaseModel):
    """Redis connection configuration (used by ratelimit / cache backends)."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: float = 5.0
    decode_responses: bool = True
    socket_connect_timeout: float = 5.0
    max_connections: int = 10

    def to_redis_config(self) -> RedisConfig:
        """Convert to the framework-agnostic RedisConfig consumed by create_redis_client()."""
        return RedisConfig(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            decode_responses=self.decode_responses,
            max_connections=self.max_connections,
        )


class Settings(BaseSettings):
    """Unified application settings.

    Do NOT instantiate directly for layered loading — use ``load_settings()``,
    which wires up the ``.env`` / ``.env.{profile}`` / env-var source chain.
    Direct instantiation is supported for tests and explicit construction.

    Nested fields are populated from environment variables using ``__`` as the
    delimiter, e.g. ``JWT__SECRET=xxx`` -> ``settings.jwt.secret``,
    ``DB__HOST=localhost`` -> ``settings.db.host``.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # --- application ---
    app_name: str = "skarner"
    env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    log_level: str = "INFO"

    # --- sub-configs ---
    jwt: JWTSettings
    db: DatabaseSettings | None = None
    redis: RedisSettings | None = None
