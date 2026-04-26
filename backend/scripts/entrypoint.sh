#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting AdTicks Backend entrypoint script..."

# 1. Run Force Schema Fix (handles cases where Alembic is out of sync)
echo "Running force schema fix (direct SQL)..."
python3 scripts/force_schema_fix.py

# 2. Run migrations
echo "Running database migrations via Alembic..."
alembic upgrade head
echo "Migrations completed successfully."

# Check if we should start uvicorn with reload (development) or not (production)
if [ "$DEBUG" = "true" ]; then
    echo "Starting Uvicorn with reload..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting Uvicorn..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000
fi
