#!/bin/bash

# ============================================
# Digital Signage Deployment Script
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Digital Signage Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found in project root${NC}"
    echo -e "${YELLOW}Creating from .env.example...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠ Please edit .env file with your configuration!${NC}"
        exit 1
    else
        echo -e "${RED}✗ .env.example not found!${NC}"
        exit 1
    fi
fi

# Change to project root
cd "$PROJECT_ROOT"
echo -e "${GREEN}✓ Working directory: $PROJECT_ROOT${NC}"

# Parse arguments
REBUILD=false
SERVICE=""
LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        backend|player|postgres|redis|celery-worker)
            SERVICE="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--rebuild] [--logs] [--service <name>] [backend|player|postgres|redis|celery-worker]"
            exit 1
            ;;
    esac
done

# Deployment function
deploy_service() {
    local service=$1
    local build_flag=""

    if [ "$REBUILD" = true ]; then
        build_flag="--build"
        echo -e "${YELLOW}Rebuilding $service...${NC}"
    else
        echo -e "${YELLOW}Deploying $service...${NC}"
    fi

    if [ -n "$service" ]; then
        docker-compose -f docker/docker-compose.yml up -d $build_flag $service
    else
        docker-compose -f docker/docker-compose.yml up -d $build_flag
    fi
}

# Main deployment
echo ""
echo -e "${BLUE}Starting deployment...${NC}"

if [ -n "$SERVICE" ]; then
    # Deploy specific service
    echo -e "${YELLOW}Target: $SERVICE${NC}"
    deploy_service "$SERVICE"
else
    # Deploy all services
    echo -e "${YELLOW}Target: All services${NC}"
    deploy_service ""
fi

# Wait a bit for services to start
echo ""
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check status
echo ""
echo -e "${BLUE}Service Status:${NC}"
docker-compose -f docker/docker-compose.yml ps

# Health checks
echo ""
echo -e "${BLUE}Health Checks:${NC}"

# Check backend API
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API: Healthy${NC}"
else
    echo -e "${RED}✗ Backend API: Not responding${NC}"
fi

# Check player
if curl -sf http://localhost:8080/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Player: Healthy${NC}"
else
    echo -e "${RED}✗ Player: Not responding${NC}"
fi

# Check postgres
if docker exec signage-postgres pg_isready -U signage_user -d signage_db > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL: Healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL: Not responding${NC}"
fi

# Check redis
if docker exec signage-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis: Healthy${NC}"
else
    echo -e "${RED}✗ Redis: Not responding${NC}"
fi

# Check CORS configuration
echo ""
echo -e "${BLUE}CORS Configuration:${NC}"
if docker logs signage-backend-python 2>&1 | grep -q "CORS enabled"; then
    CORS_ORIGINS=$(docker logs signage-backend-python 2>&1 | grep "CORS enabled" | tail -1)
    echo -e "${GREEN}✓ $CORS_ORIGINS${NC}"
else
    echo -e "${RED}✗ CORS not configured - check .env file!${NC}"
fi

# Show logs if requested
if [ "$LOGS" = true ]; then
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Streaming logs (Ctrl+C to exit)${NC}"
    echo -e "${BLUE}========================================${NC}"
    if [ -n "$SERVICE" ]; then
        docker logs -f signage-$SERVICE
    else
        docker-compose -f docker/docker-compose.yml logs -f
    fi
fi

# Deployment summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Backend API:  ${BLUE}http://localhost:8001${NC}"
echo -e "API Docs:     ${BLUE}http://localhost:8001/docs${NC}"
echo -e "Player:       ${BLUE}http://localhost:8080${NC}"
echo ""
echo -e "On Server (192.168.5.12):"
echo -e "Backend API:  ${BLUE}http://192.168.5.12:8001${NC}"
echo -e "API Docs:     ${BLUE}http://192.168.5.12:8001/docs${NC}"
echo -e "Player:       ${BLUE}http://192.168.5.12:8080${NC}"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  View logs:    ${BLUE}docker-compose -f docker/docker-compose.yml logs -f${NC}"
echo -e "  Stop all:     ${BLUE}docker-compose -f docker/docker-compose.yml down${NC}"
echo -e "  Restart:      ${BLUE}docker-compose -f docker/docker-compose.yml restart${NC}"
echo ""
