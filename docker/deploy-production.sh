#!/bin/bash

# Signage System - Production Deployment Script
# This script deploys the signage system to production with domain support
# All configurations are loaded from .env file (no hardcoding)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Signage System - Production Deployment"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo ""
    echo "Please create .env file by copying from docker/.env.production:"
    echo "  cp docker/.env.production .env"
    echo "  nano .env  # Edit with your values"
    exit 1
fi

# Load environment variables
echo -e "${GREEN}✓${NC} Loading environment variables from .env"
set -a
source "$PROJECT_ROOT/.env"
set +a

# Validate required variables
REQUIRED_VARS=(
    "DOMAIN"
    "API_DOMAIN"
    "ADMIN_DOMAIN"
    "PLAYER_DOMAIN"
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "BACKEND_PORT"
    "CMS_PORT"
    "PLAYER_PORT"
)

echo ""
echo "Validating environment variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo -e "${GREEN}✓${NC} All required variables present"

# Display deployment configuration
echo ""
echo "=========================================="
echo "Deployment Configuration"
echo "=========================================="
echo "Mode: ${DEPLOYMENT_MODE:-production}"
echo "Domain: $DOMAIN"
echo "  - Admin: https://$ADMIN_DOMAIN"
echo "  - API: https://$API_DOMAIN"
echo "  - Player: https://$PLAYER_DOMAIN"
echo ""
echo "Services:"
echo "  - Backend API: localhost:$BACKEND_PORT"
echo "  - CMS Admin: localhost:$CMS_PORT"
echo "  - Player: localhost:$PLAYER_PORT"
echo "=========================================="
echo ""

# Confirm deployment
read -p "Continue with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 1: Check Docker
echo ""
echo "Step 1/8: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker OK"

# Step 2: Stop existing containers
echo ""
echo "Step 2/8: Stopping existing containers..."
cd "$PROJECT_ROOT"
docker-compose -f docker/docker-compose.yml down || true
echo -e "${GREEN}✓${NC} Containers stopped"

# Step 3: Generate Nginx configuration from template
echo ""
echo "Step 3/8: Generating Nginx configuration..."
NGINX_TEMPLATE="$SCRIPT_DIR/nginx/signage.conf.template"
NGINX_CONFIG="$SCRIPT_DIR/nginx/signage.conf"

if [ ! -f "$NGINX_TEMPLATE" ]; then
    echo -e "${YELLOW}Warning: Nginx template not found, skipping...${NC}"
else
    envsubst < "$NGINX_TEMPLATE" > "$NGINX_CONFIG" <<EOF
\$API_DOMAIN
\$ADMIN_DOMAIN
\$PLAYER_DOMAIN
\$BACKEND_PORT
\$CMS_PORT
\$PLAYER_PORT
\$NGINX_CLIENT_MAX_BODY_SIZE
EOF
    echo -e "${GREEN}✓${NC} Nginx configuration generated"
fi

# Step 4: Build Docker images
echo ""
echo "Step 4/8: Building Docker images..."
docker-compose -f docker/docker-compose.yml build
echo -e "${GREEN}✓${NC} Images built"

# Step 5: Start services
echo ""
echo "Step 5/8: Starting services..."
docker-compose -f docker/docker-compose.yml up -d
echo -e "${GREEN}✓${NC} Services started"

# Step 6: Wait for services to be healthy
echo ""
echo "Step 6/8: Waiting for services to be healthy..."
sleep 5

# Check backend health
echo -n "  - Backend API... "
for i in {1..30}; do
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}Timeout (may still be starting)${NC}"
    fi
    sleep 1
done

# Check player
echo -n "  - Player... "
for i in {1..30}; do
    if curl -s "http://localhost:$PLAYER_PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}Timeout (may still be starting)${NC}"
    fi
    sleep 1
done

# Step 7: Display service status
echo ""
echo "Step 7/8: Service status..."
docker-compose -f docker/docker-compose.yml ps

# Step 8: Display access URLs
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services are running. Access URLs:"
echo ""
echo "LOCAL ACCESS (from server):"
echo "  - Backend API: http://localhost:$BACKEND_PORT"
echo "  - API Docs: http://localhost:$BACKEND_PORT/docs"
echo "  - CMS Admin: http://localhost:$CMS_PORT"
echo "  - Player: http://localhost:$PLAYER_PORT"
echo ""
echo "PUBLIC ACCESS (after DNS + Nginx setup):"
echo "  - Admin Dashboard: https://$ADMIN_DOMAIN"
echo "  - Backend API: https://$API_DOMAIN"
echo "  - Player/Display: https://$PLAYER_DOMAIN"
echo ""
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Setup MikroTik port forwarding (port 80, 443)"
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "3. Run: sudo bash docker/setup-nginx.sh"
echo "4. Run: sudo bash docker/setup-ssl.sh"
echo ""
echo "Logs:"
echo "  docker-compose -f docker/docker-compose.yml logs -f"
echo ""
echo "Stop:"
echo "  docker-compose -f docker/docker-compose.yml down"
echo ""
