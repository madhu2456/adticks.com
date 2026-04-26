#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting AdTicks Backend entrypoint script..."

# Run migrations
echo "Running database migrations..."
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
