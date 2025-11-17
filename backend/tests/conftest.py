from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_personas  # noqa: E402
from app.db.session import get_engine, get_session_factory, init_engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment(tmp_path_factory: pytest.TempPathFactory) -> None:
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["PERSONA_SEED_PASSWORD"] = "test-password"
    os.environ["SKIP_LETTA_USE"] = "1"
    get_settings.cache_clear()
    init_engine()

    async def prepare_schema() -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Only seed personas for non-letta integration tests
        # to avoid interference with Letta tool registration tests
        if not os.environ.get("SKIP_PERSONA_SEED"):
            session_factory = get_session_factory()
            async with session_factory() as session:
                await seed_personas(session)

    asyncio.run(prepare_schema())
    yield
    get_settings.cache_clear()
    if db_path.exists():
        db_path.unlink()
    try:
        db_dir.rmdir()
    except OSError:
        pass
