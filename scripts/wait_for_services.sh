#!/bin/bash
set -e

# Wait for services to be ready (event-based, not time-based)
# Polls backend /health endpoint until ready
# Reads BACKEND_PORT from clone.env if present

BACKEND_PORT="8000"
if [ -f "backend/clone.env" ]; then
  BACKEND_PORT=$(grep '^BACKEND_PORT=' backend/clone.env | cut -d'=' -f2)
fi

BACKEND_URL="${BACKEND_URL:-http://localhost:${BACKEND_PORT}}"
MAX_WAIT_SECONDS="${MAX_WAIT_SECONDS:-120}"
POLL_INTERVAL_SECONDS=2

echo "⏳ Waiting for backend to be ready at $BACKEND_URL/healthz..."
echo "   Max wait time: ${MAX_WAIT_SECONDS}s"

elapsed=0
while [ $elapsed -lt $MAX_WAIT_SECONDS ]; do
  if curl -sf "$BACKEND_URL/healthz" > /dev/null 2>&1; then
    echo "✅ Backend is ready!"
    exit 0
  fi

  echo "   Still waiting... (${elapsed}s elapsed)"
  sleep $POLL_INTERVAL_SECONDS
  elapsed=$((elapsed + POLL_INTERVAL_SECONDS))
done

echo "❌ Backend did not become ready within ${MAX_WAIT_SECONDS}s"
echo "   Check logs: make logs"
exit 1
