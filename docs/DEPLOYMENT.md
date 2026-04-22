# Deployment Guide — AdTicks

This guide covers deploying AdTicks to production on **DigitalOcean** using Docker Compose, a Container Registry, Nginx, and Let's Encrypt SSL.

---

## Table of Contents

- [Infrastructure Overview](#infrastructure-overview)
- [Prerequisites](#prerequisites)
- [First-Time Server Setup](#first-time-server-setup)
- [Environment Configuration](#environment-configuration)
- [Building & Pushing Images](#building--pushing-images)
- [Running the Production Stack](#running-the-production-stack)
- [Database Migrations in Production](#database-migrations-in-production)
- [SSL — Let's Encrypt](#ssl--lets-encrypt)
- [Automated Deployments (`deploy.sh`)](#automated-deployments-deploysh)
- [Rolling Back a Deployment](#rolling-back-a-deployment)
- [Monitoring & Logs](#monitoring--logs)
- [Scaling](#scaling)
- [Environment Variable Management](#environment-variable-management)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## Infrastructure Overview

```
DigitalOcean Droplet (Ubuntu 22.04, 4 vCPU / 8 GB RAM recommended)
├── Docker Engine
├── Docker Compose (production stack)
│   ├── nginx          (ports 80, 443)
│   ├── frontend       (Next.js, port 3000 internal)
│   ├── backend        (FastAPI, port 8000 internal)
│   ├── celery_worker  (4 concurrent processes)
│   ├── celery_beat    (scheduler)
│   ├── flower         (port 5555 internal)
│   ├── postgres       (port 5432 internal only)
│   └── redis          (port 6379 internal only)
│
DigitalOcean Container Registry
├── registry.digitalocean.com/adticks/backend:latest
└── registry.digitalocean.com/adticks/frontend:latest

DigitalOcean Spaces
└── adticks-data  (JSON result files)
```

Only ports **80** and **443** are exposed externally. All other service ports are internal to the Docker network. Postgres and Redis are never exposed to the public internet.

---

## Prerequisites

### DigitalOcean resources

1. **Droplet** — Ubuntu 22.04 LTS, at minimum 2 vCPU / 4 GB RAM (4 vCPU / 8 GB recommended for Celery workers)
2. **Container Registry** — Create at `cloud.digitalocean.com/registry`, name it `adticks`
3. **Spaces Bucket** — Create a Spaces bucket named `adticks-data` in your preferred region
4. **Domain** — Point your domain's A record to the Droplet's IP address
5. **Personal Access Token** — Read/write access to Container Registry (`doctl auth init`)

### Droplet setup (one-time)

```bash
# SSH into the droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash

# Install Docker Compose plugin
apt install docker-compose-plugin -y

# Install doctl (DigitalOcean CLI)
cd /tmp && wget https://github.com/digitalocean/doctl/releases/latest/download/doctl-*-linux-amd64.tar.gz
tar xf doctl-*.tar.gz && mv doctl /usr/local/bin/

# Authenticate doctl
doctl auth init   # paste your personal access token

# Authenticate Docker with Container Registry
doctl registry login

# Create app directory
mkdir -p /opt/adticks
```

---

## First-Time Server Setup

```bash
# From your local machine — copy production files to the droplet
scp .env                  root@YOUR_DROPLET_IP:/opt/adticks/.env
scp docker-compose.prod.yml root@YOUR_DROPLET_IP:/opt/adticks/docker-compose.prod.yml
scp -r nginx/             root@YOUR_DROPLET_IP:/opt/adticks/nginx/

# SSH into droplet
ssh root@YOUR_DROPLET_IP
cd /opt/adticks

# Pull images (first time — before deploy.sh is set up)
docker pull registry.digitalocean.com/adticks/backend:latest
docker pull registry.digitalocean.com/adticks/frontend:latest

# Run migrations
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Start the full production stack
docker compose -f docker-compose.prod.yml up -d
```

---

## Environment Configuration

Production `.env` differs from development in these critical ways:

```bash
# .env (production)

# Database — use strong password
DATABASE_URL=postgresql+asyncpg://adticks:STRONG_PASSWORD_HERE@postgres:5432/adticks
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE

# Security — generate with: openssl rand -hex 32
SECRET_KEY=64-character-random-string-here

# CORS
ENVIRONMENT=production
# ALLOWED_ORIGINS in code will restrict to your domain only

# AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Google OAuth
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/api/gsc/callback

# DigitalOcean Spaces
DO_SPACES_KEY=your_spaces_access_key
DO_SPACES_SECRET=your_spaces_secret_key
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=adticks-data
DO_SPACES_REGION=nyc3
```

```bash
# frontend/.env.local (production)
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=another-64-character-random-string
```

**Security checklist:**
- [ ] `SECRET_KEY` is 64+ random characters
- [ ] `POSTGRES_PASSWORD` is at least 20 random characters
- [ ] `.env` is in `.gitignore` — never commit it
- [ ] Spaces bucket is private (not public)
- [ ] `ENVIRONMENT=production` is set

---

## Building & Pushing Images

Images are tagged with the **git short SHA** so every deployment is traceable.

```bash
# On your local machine (or CI)
export SHA=$(git rev-parse --short HEAD)
export REGISTRY=registry.digitalocean.com/adticks

# Authenticate
doctl registry login

# Build backend
docker build -t $REGISTRY/backend:$SHA -t $REGISTRY/backend:latest ./backend

# Build frontend
docker build -t $REGISTRY/frontend:$SHA -t $REGISTRY/frontend:latest ./frontend

# Push both tags
docker push $REGISTRY/backend:$SHA
docker push $REGISTRY/backend:latest
docker push $REGISTRY/frontend:$SHA
docker push $REGISTRY/frontend:latest
```

The `:latest` tag is what `docker-compose.prod.yml` pulls by default.

---

## Running the Production Stack

**`docker-compose.prod.yml`** differs from development in:
- Images come from Container Registry (not local builds)
- No hot-reload volumes
- Restart policy: `unless-stopped`
- Flower port is NOT exposed externally (access via SSH tunnel)
- Postgres and Redis have no exposed ports

```bash
# On the droplet
cd /opt/adticks

# Start (or restart after image pull)
docker compose -f docker-compose.prod.yml up -d

# View running services
docker compose -f docker-compose.prod.yml ps

# Follow all logs
docker compose -f docker-compose.prod.yml logs -f

# Follow a specific service
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Database Migrations in Production

**Always run migrations before restarting the backend** after a schema change:

```bash
# On the droplet
cd /opt/adticks

docker compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Verify current state
docker compose -f docker-compose.prod.yml run --rm backend \
  alembic current
```

Never modify production database schema manually with SQL — always use Alembic migrations.

---

## SSL — Let's Encrypt

### Install Certbot

```bash
apt install -y certbot python3-certbot-nginx
```

### Obtain certificate

```bash
# Replace with your actual domain
certbot --nginx -d yourdomain.com -d www.yourdomain.com \
  --non-interactive --agree-tos --email admin@yourdomain.com
```

Certbot automatically edits `nginx.conf` to add HTTPS redirects and SSL configuration.

### Auto-renewal

Certbot installs a systemd timer that runs `certbot renew` twice daily. Verify:

```bash
systemctl status certbot.timer
certbot renew --dry-run   # Test renewal without actually renewing
```

### Nginx configuration after SSL

After Certbot, your `nginx.conf` should have:
- Port 80 → 301 redirect to HTTPS
- Port 443 with TLS
- `/api/*` → `http://backend:8000`
- `/*` → `http://frontend:3000`

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Security headers
    add_header X-Content-Type-Options "nosniff";
    add_header X-Frame-Options "DENY";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains";

    location /api/ {
        proxy_pass         http://backend:8000/api/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;   # Allow long-running requests (scan dispatch)
    }

    location / {
        proxy_pass         http://frontend:3000/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }
}
```

---

## Automated Deployments (`deploy.sh`)

`scripts/deploy.sh` performs a full zero-downtime rolling deployment:

```bash
#!/bin/bash
set -euo pipefail

SHA=$(git rev-parse --short HEAD)
REGISTRY=registry.digitalocean.com/adticks

# 1. Build images
docker build -t $REGISTRY/backend:$SHA  -t $REGISTRY/backend:latest  ./backend
docker build -t $REGISTRY/frontend:$SHA -t $REGISTRY/frontend:latest ./frontend

# 2. Push to registry
docker push $REGISTRY/backend:$SHA && docker push $REGISTRY/backend:latest
docker push $REGISTRY/frontend:$SHA && docker push $REGISTRY/frontend:latest

# 3. Deploy to droplet via SSH
ssh root@$DEPLOY_HOST "
  cd /opt/adticks
  doctl registry login

  # Pull new images
  docker pull $REGISTRY/backend:latest
  docker pull $REGISTRY/frontend:latest

  # Run migrations (safe to run even if no new migrations)
  docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

  # Rolling restart: backend first, then workers, then frontend
  docker compose -f docker-compose.prod.yml up -d --no-deps backend
  docker compose -f docker-compose.prod.yml up -d --no-deps celery_worker celery_beat
  docker compose -f docker-compose.prod.yml up -d --no-deps frontend

  # Reload Nginx (picks up any config changes)
  docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

  echo 'Deployment complete: $SHA'
"
```

**Run a deployment:**

```bash
export DEPLOY_HOST=your.droplet.ip
export DO_ACCESS_TOKEN=your_do_token

./scripts/deploy.sh
```

---

## Rolling Back a Deployment

Every deployment pushes a SHA-tagged image (`backend:abc1234`), so rollback is simple:

```bash
ssh root@YOUR_DROPLET_IP

# List recent image tags
doctl registry repository list-tags adticks/backend

# Roll back to a specific SHA
docker pull registry.digitalocean.com/adticks/backend:PREVIOUS_SHA
docker tag registry.digitalocean.com/adticks/backend:PREVIOUS_SHA \
           registry.digitalocean.com/adticks/backend:latest

cd /opt/adticks
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# If the previous version had a schema migration, roll back Alembic too
docker compose -f docker-compose.prod.yml run --rm backend alembic downgrade -1
```

---

## Monitoring & Logs

### Service logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend --tail=100

# Celery task logs
docker compose -f docker-compose.prod.yml logs -f celery_worker
```

### Celery Flower (task monitoring)

Flower is NOT exposed publicly. Access via SSH tunnel:

```bash
# On your local machine
ssh -L 5555:localhost:5555 root@YOUR_DROPLET_IP

# Then open in browser
open http://localhost:5555
```

### System metrics

```bash
# Container resource usage
docker stats

# Disk usage
df -h
docker system df    # Docker-specific disk usage

# Postgres database size
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U adticks -c "SELECT pg_size_pretty(pg_database_size('adticks'));"
```

### Health check

```bash
curl https://yourdomain.com/api/auth/health
# Expected: {"status":"ok","environment":"production"}
```

---

## Scaling

### Scaling Celery workers

```bash
# Scale to 8 celery worker containers
docker compose -f docker-compose.prod.yml up -d --scale celery_worker=8
```

Or increase the `--concurrency` in the Celery worker command in `docker-compose.prod.yml`:

```yaml
celery_worker:
  command: celery -A app.core.celery_app worker --loglevel=info --concurrency=8
```

### Scaling the backend

FastAPI + Uvicorn handles concurrency with async I/O. For more throughput:

```yaml
backend:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or add a second backend container and load-balance in Nginx.

### Database — upgrading Postgres

For high traffic, consider:
1. Upgrading to a **DigitalOcean Managed Database** (no self-managed backups needed)
2. Adding a **PgBouncer** connection pooler between FastAPI and Postgres

---

## Environment Variable Management

Never store secrets in the repository. Recommended approaches:

**Option 1: `.env` file on the server (current)**
- Simple but requires SSH access to rotate secrets
- Protected by file permissions (`chmod 600 /opt/adticks/.env`)

**Option 2: DigitalOcean Secrets / App Platform Env Vars**
- Managed secrets injection, no file on disk

**Option 3: HashiCorp Vault (enterprise)**
- Dynamic secrets, audit logs, automatic rotation

Rotate the `SECRET_KEY` by:
1. Generating a new 64-char key: `openssl rand -hex 32`
2. Updating `/opt/adticks/.env`
3. Restarting backend: `docker compose -f docker-compose.prod.yml restart backend`

Note: rotating `SECRET_KEY` invalidates all active JWT tokens — all users will be logged out.

---

## Backup & Recovery

### Automated Postgres backup

```bash
# Add to cron on the droplet (daily at 2 AM)
0 2 * * * docker compose -f /opt/adticks/docker-compose.prod.yml exec -T postgres \
  pg_dump -U adticks adticks | gzip > /opt/backups/adticks_$(date +%Y%m%d).sql.gz
```

### Restore from backup

```bash
# Restore to a running Postgres container
gunzip -c /opt/backups/adticks_20260421.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U adticks adticks
```

### DigitalOcean Spaces backup

Spaces files (JSON scan results) are durable by default (3× redundancy). For additional protection, enable Spaces versioning or cross-region replication in the DigitalOcean console.

---

## Troubleshooting

### Backend won't start

```bash
docker compose -f docker-compose.prod.yml logs backend | tail -50
```

Common causes:
- `DATABASE_URL` is wrong (check `postgres` hostname, not `localhost`)
- Missing required env var (Pydantic Settings will print what's missing)
- Postgres not ready yet (add `depends_on: postgres` with `healthcheck`)

### Migrations fail

```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head 2>&1
```

Check:
- Database is reachable from the backend container
- Migration file exists in `alembic/versions/`
- No conflicting schema changes

### Celery tasks not running

```bash
docker compose -f docker-compose.prod.yml logs celery_worker | grep ERROR
```

Check:
- Redis is running: `docker compose -f docker-compose.prod.yml exec redis redis-cli ping`
- `REDIS_URL` is correct
- Task is properly registered (visible in Flower)

### Nginx 502 Bad Gateway

Means Nginx can't reach the backend or frontend container:
```bash
docker compose -f docker-compose.prod.yml ps     # Check all containers are Up
docker compose -f docker-compose.prod.yml logs nginx
```

### Out of disk space

```bash
df -h                    # Check disk usage
docker system prune -af  # Remove unused images, containers, networks
```

Old images from previous deployments accumulate. Set a cleanup cron:
```bash
0 3 * * * docker image prune -af --filter "until=72h"
```
