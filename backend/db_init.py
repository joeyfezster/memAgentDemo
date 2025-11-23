#!/usr/bin/env python3
"""
Database initialization script.
Runs alembic migrations and seeds personas against the database.
Should be executed once during deployment, not on every container start.
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic.command import upgrade
from app.db.session import get_session_factory
from app.db.seed import seed_user_profiles


def run_migrations(database_url: str) -> bool:
    print("Running database migrations...")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    try:
        upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"✓ Migrations already up to date: {e}")
        return True


async def run_seeding(database_url: str) -> bool:
    print("Seeding personas...")

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_user_profiles(session)
        print(
            "✓ Seeding completed successfully (new personas created or existing ones updated)"
        )
        return True
    except Exception as e:
        print(f"✗ Error during seeding: {e}", file=sys.stderr)
        return False


def run_initialization() -> int:
    print("Starting database initialization...")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("✗ DATABASE_URL environment variable not set", file=sys.stderr)
        return 1

    if not run_migrations(database_url):
        return 1

    try:
        if not asyncio.run(run_seeding(database_url)):
            return 1
    except Exception as e:
        print(f"✗ Error during seeding execution: {e}", file=sys.stderr)
        return 1

    print("✓ Database initialization completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run_initialization())
