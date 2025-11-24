# Fix CI Failures

## Problem

The E2E CI pipeline is failing.

1. `db-init` service was failing due to:
   - `UndefinedTableError` (relation "conversation" does not exist) during `nuke_database`.
   - `RuntimeError` (asyncio.run() cannot be called from a running event loop) during `run_migrations`.
2. `frontend` service was failing healthcheck due to missing `curl`.

## Analysis

1. **db-init**:
   - The exception handling in `db_init.py` was not correctly unwrapping the SQLAlchemy/Asyncpg exception hierarchy to find `UndefinedTableError`.
   - `alembic/env.py` calls `asyncio.run()`, which conflicts with `db_init.py` wrapping the whole process in `asyncio.run()`.
2. **frontend**:
   - The `frontend` service in `docker-compose.yml` uses `curl` for healthcheck.
   - The `frontend/Dockerfile` uses `node:20-alpine`, which does not have `curl` installed by default.

## Solution

1. **db-init**:
   - Refactored `db_init.py` to handle exceptions by checking `e.orig.__cause__`.
   - Refactored `db_init.py` to run `nuke` and `seed` in separate `asyncio.run()` calls, and call `run_migrations` (synchronous wrapper) at the top level.
2. **frontend**:
   - Updated `frontend/Dockerfile` to install `curl` in the `base` stage.

## Verification

- Local `docker compose up db-init` passes.
- Local `docker compose build frontend` passes and `curl --version` works in the image.
- CI run should pass now.
