from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

__all__ = ["DatabaseDialect", "DatabaseConfig", "create_engine"]


class DatabaseDialect(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    dialect: DatabaseDialect
    host: str
    port: int
    user: str
    password: str
    database: str
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False
    # Extra kwargs forwarded to create_async_engine
    engine_kwargs: dict[str, Any] = field(default_factory=dict)

    def build_url(self) -> str:
        if self.dialect == DatabaseDialect.MYSQL:
            driver = "aiomysql"
        else:
            driver = "asyncpg"
        return (
            f"{self.dialect.value}+{driver}://"
            f"{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )


def create_engine(config: DatabaseConfig) -> AsyncEngine:
    """Create an async SQLAlchemy engine from a DatabaseConfig."""
    url = config.build_url()
    return create_async_engine(
        url,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        echo=config.echo,
        **config.engine_kwargs,
    )
