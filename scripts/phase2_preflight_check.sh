#!/bin/bash
# Phase 2 Pre-Flight Check Script
# Verifies all dependencies before enabling storage services
# Usage: ./scripts/phase2_preflight_check.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

echo "=========================================="
echo "Phase 2 Storage Services Pre-Flight Check"
echo "=========================================="
echo ""

# Function to check file exists
check_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc: $file"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: $file NOT FOUND"
        ((FAIL++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    local dir=$1
    local desc=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $desc: $dir"
        ((PASS++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $desc: $dir NOT FOUND (will be created)"
        ((WARN++))
        return 1
    fi
}

# Function to check writable
check_writable() {
    local dir=$1
    local desc=$2
    if [ -w "$dir" ]; then
        echo -e "${GREEN}✓${NC} $desc: $dir (writable)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc: $dir (NOT writable)"
        ((FAIL++))
        return 1
    fi
}

echo "1. Checking Dockerfiles..."
echo "----------------------------"
check_file "anthias/docker/Dockerfile.server" "Storage Server Dockerfile"
check_file "anthias/docker/Dockerfile.celery" "Storage Celery Dockerfile"
check_file "anthias/docker/Dockerfile.websocket" "Storage WebSocket Dockerfile"
check_file "anthias/docker/Dockerfile.nginx" "Storage Nginx Dockerfile"
echo ""

echo "2. Checking Requirements Files..."
echo "----------------------------------"
check_file "anthias/requirements/requirements.txt" "Server Requirements"
check_file "anthias/requirements/requirements-websocket.txt" "WebSocket Requirements"
echo ""

echo "3. Checking Configuration Files..."
echo "-----------------------------------"
check_file "anthias/docker/nginx/nginx.development.conf" "Nginx Config"
check_file "anthias/bin/start_server.sh" "Server Startup Script"
check_file ".env" "Environment File"
check_file "docker/docker-compose.yml" "Docker Compose File"
echo ""

echo "4. Checking Directories..."
echo "---------------------------"
check_dir "anthias" "Anthias Source Directory"
check_dir "anthias-assets" "Assets Storage Directory"
check_dir "anthias/staticfiles" "Django Static Files"
echo ""

echo "5. Checking Write Permissions..."
echo "---------------------------------"
check_writable "anthias-assets" "Assets Directory"
echo ""

echo "6. Checking Environment Variables..."
echo "-------------------------------------"
if grep -q "ANTHIAS_API_URL=http://192.168.5.12:8000" .env; then
    echo -e "${GREEN}✓${NC} ANTHIAS_API_URL configured"
    ((PASS++))
else
    echo -e "${RED}✗${NC} ANTHIAS_API_URL not found or incorrect in .env"
    ((FAIL++))
fi

if grep -q "ANTHIAS_EXTERNAL_PORT=8000" .env; then
    echo -e "${GREEN}✓${NC} ANTHIAS_EXTERNAL_PORT configured"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} ANTHIAS_EXTERNAL_PORT not found in .env (will use default)"
    ((WARN++))
fi

if grep -q "CELERY_BROKER_URL=redis://redis:6379/0" .env; then
    echo -e "${GREEN}✓${NC} CELERY_BROKER_URL configured"
    ((PASS++))
else
    echo -e "${RED}✗${NC} CELERY_BROKER_URL not configured"
    ((FAIL++))
fi
echo ""

echo "7. Checking Docker Compose Status..."
echo "-------------------------------------"
# Count commented storage services
COMMENTED_SERVICES=$(grep -E "^  # (storage-server|storage-celery|storage-websocket|storage-nginx):" docker/docker-compose.yml | wc -l)

if [ "$COMMENTED_SERVICES" -eq 4 ]; then
    echo -e "${GREEN}✓${NC} All 4 storage services currently disabled (ready for Phase 2)"
    ((PASS++))
elif [ "$COMMENTED_SERVICES" -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC} Storage services already enabled"
    ((WARN++))
else
    echo -e "${YELLOW}⚠${NC} Partial storage services enabled ($COMMENTED_SERVICES/4 disabled)"
    ((WARN++))
fi
echo ""

echo "8. Checking Disk Space..."
echo "--------------------------"
AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -gt 10 ]; then
    echo -e "${GREEN}✓${NC} Disk space: ${AVAILABLE_GB}GB available (sufficient)"
    ((PASS++))
elif [ "$AVAILABLE_GB" -gt 5 ]; then
    echo -e "${YELLOW}⚠${NC} Disk space: ${AVAILABLE_GB}GB available (marginal)"
    ((WARN++))
else
    echo -e "${RED}✗${NC} Disk space: ${AVAILABLE_GB}GB available (insufficient - need 10GB+)"
    ((FAIL++))
fi
echo ""

# Summary
echo "=========================================="
echo "Pre-Flight Check Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC}  $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}❌ Pre-flight check FAILED${NC}"
    echo "Fix the above errors before proceeding with Phase 2"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}⚠ Pre-flight check PASSED with warnings${NC}"
    echo "Review warnings before proceeding"
    exit 0
else
    echo -e "${GREEN}✅ Pre-flight check PASSED${NC}"
    echo "All systems ready for Phase 2 storage services enablement"
    exit 0
fi
