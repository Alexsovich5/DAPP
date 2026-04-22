#!/bin/sh
# Production entrypoint: wait for DB, run migrations, start uvicorn.
set -e

DB_HOST="${DB_HOST:-postgres}"
DB_USER="${DB_USER:-postgres}"

echo "Waiting for PostgreSQL at $DB_HOST:5432..."
until python -c "
import socket, sys
try:
    s = socket.create_connection(('$DB_HOST', 5432), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
# Single worker so prometheus_client metrics live in one process REGISTRY.
# Multi-worker would need PROMETHEUS_MULTIPROC_DIR + MultiProcessCollector;
# overkill for a demo with modest traffic.
#
# --proxy-headers + --forwarded-allow-ips="*" make uvicorn honor
# X-Forwarded-Proto/Host from the upstream nginx so FastAPI's redirects
# (e.g. /api/v1/health → /api/v1/health/) keep the original https:// scheme.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --proxy-headers \
  --forwarded-allow-ips="*"
