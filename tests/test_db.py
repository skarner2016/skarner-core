from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skarner.core.db.engine import DatabaseConfig, DatabaseDialect, create_engine
from skarner.core.db.session import AsyncSessionManager


# --- DatabaseConfig ---

def test_mysql_url():
    cfg = DatabaseConfig(
        dialect=DatabaseDialect.MYSQL,
        host="localhost",
        port=3306,
        user="root",
        password="secret",
        database="mydb",
    )
    assert cfg.build_url() == "mysql+aiomysql://root:secret@localhost:3306/mydb"


def test_postgresql_url():
    cfg = DatabaseConfig(
        dialect=DatabaseDialect.POSTGRESQL,
        host="localhost",
        port=5432,
        user="admin",
        password="pass",
        database="pgdb",
    )
    assert cfg.build_url() == "postgresql+asyncpg://admin:pass@localhost:5432/pgdb"


def test_create_engine_returns_async_engine():
    cfg = DatabaseConfig(
        dialect=DatabaseDialect.POSTGRESQL,
        host="localhost",
        port=5432,
        user="u",
        password="p",
        database="d",
    )
    with patch("skarner.core.db.engine.create_async_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine
        engine = create_engine(cfg)

    mock_create.assert_called_once_with(
        "postgresql+asyncpg://u:p@localhost:5432/d",
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        echo=False,
    )
    assert engine is mock_engine


def test_create_engine_forwards_extra_kwargs():
    cfg = DatabaseConfig(
        dialect=DatabaseDialect.MYSQL,
        host="db",
        port=3306,
        user="u",
        password="p",
        database="d",
        engine_kwargs={"connect_args": {"charset": "utf8mb4"}},
    )
    with patch("skarner.core.db.engine.create_async_engine") as mock_create:
        create_engine(cfg)

    _, kwargs = mock_create.call_args
    assert kwargs["connect_args"] == {"charset": "utf8mb4"}


# --- AsyncSessionManager ---

@pytest.mark.asyncio
async def test_session_commits_on_success():
    mock_engine = MagicMock()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("skarner.core.db.session.async_sessionmaker", return_value=mock_factory):
        manager = AsyncSessionManager(mock_engine)

    async with manager.session() as session:
        assert session is mock_session

    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_session_rolls_back_on_error():
    mock_engine = MagicMock()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("skarner.core.db.session.async_sessionmaker", return_value=mock_factory):
        manager = AsyncSessionManager(mock_engine)

    with pytest.raises(ValueError):
        async with manager.session():
            raise ValueError("boom")

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_disposes_engine():
    mock_engine = AsyncMock()
    with patch("skarner.core.db.session.async_sessionmaker"):
        manager = AsyncSessionManager(mock_engine)

    await manager.close()
    mock_engine.dispose.assert_awaited_once()
