.PHONY: up down logs migrate migration shell test lint format build

# --- Docker Compose Shortcuts ---

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

build:
	docker-compose build

# --- Database Migrations (Alembic) ---

migrate:
	docker-compose run --rm backend alembic upgrade head

## Usage: make migration msg="add users table"
migration:
	docker-compose run --rm backend alembic revision --autogenerate -m "$(msg)"

downgrade:
	docker-compose run --rm backend alembic downgrade -1

# --- Development Shell ---

shell:
	docker-compose run --rm backend python -c "import asyncio; asyncio.run(shell())"

# --- Testing ---

test:
	docker-compose run --rm backend pytest -v

test-cov:
	docker-compose run --rm backend pytest -v --cov=app --cov-report=html

# --- Code Quality ---

lint:
	docker-compose run --rm backend ruff check app/

format:
	docker-compose run --rm backend ruff format app/

# --- Service Management ---

restart-backend:
	docker-compose restart backend

restart-workers:
	docker-compose restart celery_worker celery_beat

status:
	docker-compose ps
