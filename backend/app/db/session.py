from __future__ import annotations

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: Optional[AsyncEngine] = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str | None = None) -> AsyncEngine:
    global _engine, AsyncSessionFactory
    settings = get_settings()
    url = database_url or settings.database_url
    if _engine is not None:
        # Dispose existing engine before creating a new one
        _engine.sync_engine.dispose(close=True)
    _engine = create_async_engine(url, future=True, echo=settings.debug)
    AsyncSessionFactory = async_sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        return init_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    factory = AsyncSessionFactory
    if factory is None:
        get_engine()
        factory = AsyncSessionFactory
    assert factory is not None
    return factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


# Initialize engine on import using default settings
init_engine()
