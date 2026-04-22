#\!/bin/bash
# AdTicks Developer Setup Script
set -e

echo "========================================"
echo "  AdTicks — Visibility Intelligence     "
echo "  Developer Setup                       "
echo "========================================"
echo ""

# Check required tools
check_dependency() {
    if \! command -v "$1" &> /dev/null; then
        echo "ERROR: '$1' is not installed. Please install it and re-run this script."
        exit 1
    fi
}

echo "Checking dependencies..."
check_dependency docker
check_dependency docker-compose
echo "All dependencies found."
echo ""

# Copy env files if they don't exist
if [ \! -f ".env" ]; then
    echo "Copying .env.example -> .env"
    cp .env.example .env
    echo "  Please review and update .env with your actual credentials before continuing."
else
    echo ".env already exists, skipping."
fi

if [ \! -f "frontend/.env.local" ]; then
    echo "Copying frontend/.env.local.example -> frontend/.env.local"
    cp frontend/.env.local.example frontend/.env.local
else
    echo "frontend/.env.local already exists, skipping."
fi

echo ""
echo "Starting postgres and redis..."
docker-compose up -d postgres redis

echo "Waiting for postgres to be ready..."
sleep 5

# Wait for postgres health check to pass
RETRIES=10
until docker-compose exec -T postgres pg_isready -U adticks -d adticks > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "  Waiting for postgres... ($RETRIES retries left)"
    RETRIES=$((RETRIES - 1))
    sleep 3
done

if [ $RETRIES -eq 0 ]; then
    echo "ERROR: Postgres did not become ready in time."
    exit 1
fi

echo "Postgres is ready."
echo ""

echo "Running database migrations..."
docker-compose run --rm backend alembic upgrade head

echo ""
echo "Starting all services..."
docker-compose up -d

echo ""
echo "========================================"
echo "  AdTicks is running\!"
echo ""
echo "  Frontend    : http://localhost:3002"
echo "  API         : http://localhost:8002"
echo "  API Docs    : http://localhost:8002/docs"
echo "  Celery UI   : http://localhost:5555"
echo "========================================"
