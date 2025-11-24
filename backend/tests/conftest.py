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
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_user_profiles  # noqa: E402
from app.db.session import get_engine, get_session_factory, init_engine  # noqa: E402

repo_root = project_root.parent
load_dotenv(repo_root / ".env")


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment() -> Generator[None, None, None]:
    # Use environment variable for database host, default to localhost for CI
    # In Docker/E2E tests, this can be set to "postgres"
    db_host = os.environ.get("TEST_DB_HOST", "localhost")
    db_url = f"postgresql+asyncpg://postgres:postgres@{db_host}:5432/memagent_test"
    os.environ["DATABASE_URL"] = db_url
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["PERSONA_SEED_PASSWORD"] = "changeme123"

    get_settings.cache_clear()

    async def create_test_db() -> None:
        admin_url = f"postgresql+asyncpg://postgres:postgres@{db_host}:5432/postgres"
        admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        async with admin_engine.begin() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS memagent_test"))
            await conn.execute(text("CREATE DATABASE memagent_test"))
        await admin_engine.dispose()

    asyncio.run(create_test_db())

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
