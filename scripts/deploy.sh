#\!/bin/bash
# AdTicks — DigitalOcean Deployment Script
set -e

echo "========================================"
echo "  AdTicks — Production Deployment       "
echo "========================================"
echo ""

# --- Configuration ---
REGISTRY="registry.digitalocean.com/adticks"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
REMOTE_USER="${DEPLOY_USER:-root}"
REMOTE_HOST="${DEPLOY_HOST}"          # Set via environment: export DEPLOY_HOST=your.droplet.ip
REMOTE_DIR="/opt/adticks"

# Validate required env vars
if [ -z "$REMOTE_HOST" ]; then
    echo "ERROR: DEPLOY_HOST environment variable is not set."
    echo "Usage: DEPLOY_HOST=your.droplet.ip ./scripts/deploy.sh"
    exit 1
fi

if [ -z "$DO_ACCESS_TOKEN" ]; then
    echo "ERROR: DO_ACCESS_TOKEN is required to push to DigitalOcean Container Registry."
    exit 1
fi

echo "Deploying image tag: $IMAGE_TAG"
echo "Target host: $REMOTE_HOST"
echo ""

# --- Step 1: Authenticate with DO Container Registry ---
echo "Authenticating with DigitalOcean Container Registry..."
echo "$DO_ACCESS_TOKEN" | docker login registry.digitalocean.com --username token --password-stdin

# --- Step 2: Build images ---
echo ""
echo "Building backend image..."
docker build -t "$REGISTRY/backend:$IMAGE_TAG" -t "$REGISTRY/backend:latest" ./backend

echo "Building frontend image..."
docker build -t "$REGISTRY/frontend:$IMAGE_TAG" -t "$REGISTRY/frontend:latest" ./frontend

# --- Step 3: Push images ---
echo ""
echo "Pushing images to registry..."
docker push "$REGISTRY/backend:$IMAGE_TAG"
docker push "$REGISTRY/backend:latest"
docker push "$REGISTRY/frontend:$IMAGE_TAG"
docker push "$REGISTRY/frontend:latest"
echo "Images pushed successfully."

# --- Step 4: Deploy to Droplet via SSH ---
echo ""
echo "Deploying to $REMOTE_HOST..."

# Copy Nginx config to remote temporary location
scp -o StrictHostKeyChecking=no ./nginx/nginx.conf "$REMOTE_USER@$REMOTE_HOST:/tmp/adticks_nginx.conf"

ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" bash -s << REMOTE_SCRIPT
set -e

echo "Pulling latest images..."
cd $REMOTE_DIR

# Authenticate registry on remote
echo "$DO_ACCESS_TOKEN" | docker login registry.digitalocean.com --username token --password-stdin

# Pull new images
IMAGE_TAG="$IMAGE_TAG" docker-compose -f docker-compose.prod.yml pull backend frontend

# Run database migrations before switching traffic
echo "Running database migrations..."
IMAGE_TAG="$IMAGE_TAG" docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Restart services with zero-downtime rolling update
echo "Restarting services..."
IMAGE_TAG="$IMAGE_TAG" docker-compose -f docker-compose.prod.yml up -d --no-deps backend celery_worker celery_beat frontend

# Apply Nginx configuration to host
echo "Updating Host Nginx configuration..."
sudo mv /tmp/adticks_nginx.conf /etc/nginx/sites-available/adticks
sudo ln -sf /etc/nginx/sites-available/adticks /etc/nginx/sites-enabled/adticks

# Test and reload host Nginx
echo "Testing Nginx configuration..."
sudo nginx -t
echo "Reloading Host Nginx..."
sudo systemctl reload nginx

# Clean up old images
docker image prune -f

echo "Deployment complete on remote host."
REMOTE_SCRIPT

echo ""
echo "========================================"
echo "  Deployment successful\!"
echo "  Tag: $IMAGE_TAG"
echo "  Host: https://adticks.com"
echo "========================================"
