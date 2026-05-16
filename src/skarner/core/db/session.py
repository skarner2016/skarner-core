from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

__all__ = ["AsyncSessionManager"]


class AsyncSessionManager:
    """Manages async SQLAlchemy sessions for a given engine.

    Usage:
        manager = AsyncSessionManager(engine)

        async with manager.session() as session:
            result = await session.execute(...)
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a session that auto-commits on success and rolls back on error."""
        async with self._factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Dispose the underlying engine connection pool."""
        await self._engine.dispose()
