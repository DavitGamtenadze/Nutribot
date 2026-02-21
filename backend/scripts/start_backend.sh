#!/usr/bin/env sh
set -e

until uv run alembic upgrade head; do
  echo "Waiting for database..."
  sleep 2
done

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
