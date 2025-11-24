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


async def nuke_database() -> bool:
    """Delete ALL data from ALL tables to start from scratch."""
    print("Nuking database (deleting all data)...")

    try:
        from sqlalchemy import delete
        from app.models.conversation import Conversation
        from app.models.user import User

        session_factory = get_session_factory()
        async with session_factory() as session:
            # Delete everything
            await session.execute(delete(Conversation))
            await session.execute(delete(User))
            await session.commit()
            print("✓ Database nuked (all data deleted)")
        return True
    except Exception as e:
        # If tables don't exist yet, that's okay - migrations will create them
        if "does not exist" in str(e):
            print(
                "✓ Database is empty (tables don't exist yet, will be created by migrations)"
            )
            return True
        print(f"✗ Error during nuke: {e}", file=sys.stderr)
        return False


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


async def run_seeding() -> bool:
    """Seed personas and conversations."""
    print("Seeding personas and conversations...")

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_user_profiles(session)
        print("✓ Seeding completed successfully")
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

    async def nuke_and_seed_with_migrations():
        # Nuke
        if not await nuke_database():
            return False

        # Migrations (run synchronously in between)
        if not run_migrations(database_url):
            return False

        # Seed
        if not await run_seeding():
            return False

        return True

    try:
        if not asyncio.run(nuke_and_seed_with_migrations()):
            return 1
    except Exception as e:
        print(f"✗ Error during initialization: {e}", file=sys.stderr)
        return 1

    print("✓ Database initialization completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run_initialization())
