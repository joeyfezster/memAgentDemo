from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Generator
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
import testing.postgresql  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from collections.abc import AsyncGenerator  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.crud import user as user_crud  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_user_profiles  # noqa: E402
from app.db.session import get_engine, get_session_factory, init_engine  # noqa: E402
from app.models.user import User  # noqa: E402

repo_root = project_root.parent
load_dotenv(project_root / ".env")


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment() -> Generator[None, None, None]:
    postgresql = testing.postgresql.Postgresql()
    os.environ["DATABASE_URL"] = postgresql.url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["PERSONA_SEED_PASSWORD"] = "changeme123"

    get_settings.cache_clear()
    init_engine(poolclass=NullPool)

    async def setup_db() -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        init_engine(poolclass=NullPool)
        engine = get_engine()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_user_profiles(session)
        await engine.dispose()

    asyncio.run(setup_db())

    init_engine(poolclass=NullPool)

    yield

    try:
        engine = get_engine()
        if engine:
            engine.sync_engine.dispose(close=True)
    except Exception:
        pass
    get_settings.cache_clear()
    postgresql.stop()


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for tests."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_user_sarah(session: AsyncSession) -> User:
    """Provide Sarah test user for tests."""
    user = await user_crud.get_user_by_email(session, "sarah@chickfilb.com")
    if not user:
        raise RuntimeError("Test user not found - seed data may not have loaded")
    return user


@pytest.fixture(scope="function")
def settings():
    """Provide settings for tests."""
    return get_settings()
