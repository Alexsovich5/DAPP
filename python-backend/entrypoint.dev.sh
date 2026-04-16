#!/bin/sh
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

echo "Starting FastAPI development server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
