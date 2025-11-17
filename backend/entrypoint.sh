#!/bin/bash
set -e

echo "========================================"
echo "Backend Startup Script"
echo "========================================"

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH

# Wait for postgres
echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "  PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✓ PostgreSQL is ready"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head
echo "✓ Migrations complete"

# Wait for Letta and initialize OpenAI provider
echo "Initializing Letta..."
python /infra/init-letta.py
echo "✓ Letta initialization complete"

# Seed database if not already seeded
echo "Seeding database..."
python -c "
from app.db.session import get_session
from app.db.seed import seed_personas
import asyncio

async def run_seed():
    async for db in get_session():
        await seed_personas(db)
        break

asyncio.run(run_seed())
print('✓ Database seeded')
"

echo "========================================"
echo "Starting application server..."
echo "========================================"

# Start the application
exec "$@"
