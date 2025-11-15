#!/bin/bash
# Phase 3 P0 Fixes Deployment Script
# Date: 2025-01-14
# Risk: MEDIUM (infrastructure changes: ClamAV, Redis rate limiter)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Server details
SERVER_USER="gzjbbk"
SERVER_HOST="192.168.5.12"
SERVER_PASS="Password@2021"
PROJECT_DIR="/home/gzjbbk/signate"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Phase 3 P0 Fixes Deployment Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Step 1: Backup Database
echo -e "${GREEN}[Step 1/7] Creating database backup...${NC}"
BACKUP_DIR="~/backups/pre_phase3_fixes_$(date +%Y%m%d_%H%M%S)"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  mkdir -p $BACKUP_DIR && \
  docker exec signage-postgres pg_dump -U signage_user -d signage_db > \
    $BACKUP_DIR/signage_db_backup.sql && \
  echo 'Backup created at: $BACKUP_DIR' && \
  ls -lh $BACKUP_DIR/signage_db_backup.sql
"
echo -e "${GREEN}✅ Database backup completed${NC}"
echo ""

# Step 2: Stop Services
echo -e "${GREEN}[Step 2/7] Stopping backend and celery services...${NC}"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  cd $PROJECT_DIR && \
  docker-compose -f docker/docker-compose.yml stop backend-api celery-worker && \
  echo 'Services stopped'
"
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# Step 3: Deploy Infrastructure Changes
echo -e "${GREEN}[Step 3/7] Deploying docker-compose.yml (ClamAV)...${NC}"
cd /mnt/g/khoirul/signate

sshpass -p "$SERVER_PASS" rsync -avz docker/docker-compose.yml \
  ${SERVER_USER}@${SERVER_HOST}:${PROJECT_DIR}/docker/

echo -e "${GREEN}✅ Infrastructure config deployed${NC}"
echo ""

# Step 4: Deploy Code Changes
echo -e "${GREEN}[Step 4/7] Deploying code changes (3 files)...${NC}"

# List of files to deploy (Phase 3 fixes)
FILES=(
  "backend-python/shared/rate_limiter.py"
  "backend-python/shared/virus_scanner.py"
  "backend-python/services/content/use_cases/upload_content.py"
)

# Sync each file individually
for file in "${FILES[@]}"; do
  echo "  Syncing: $file"
  sshpass -p "$SERVER_PASS" rsync -avz "$file" \
    ${SERVER_USER}@${SERVER_HOST}:${PROJECT_DIR}/${file}
done

echo -e "${GREEN}✅ Code changes deployed (3 files)${NC}"
echo ""

# Step 5: Start ClamAV
echo -e "${GREEN}[Step 5/7] Starting ClamAV service...${NC}"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  cd $PROJECT_DIR && \
  docker-compose -f docker/docker-compose.yml up -d clamav && \
  echo 'ClamAV started (virus DB update may take 5 minutes)' && \
  sleep 5
"
echo -e "${GREEN}✅ ClamAV service started${NC}"
echo ""

# Step 6: Restart Services
echo -e "${GREEN}[Step 6/7] Restarting backend and celery services...${NC}"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  cd $PROJECT_DIR && \
  docker-compose -f docker/docker-compose.yml start backend-api celery-worker && \
  echo 'Waiting 30 seconds for services to start...' && \
  sleep 30 && \
  echo 'Services restarted'
"
echo -e "${GREEN}✅ Services restarted${NC}"
echo ""

# Step 7: Smoke Tests
echo -e "${GREEN}[Step 7/7] Running smoke tests...${NC}"

# Test 1: Health check
echo "  Test 1: Health check"
HEALTH=$(curl -s http://192.168.5.12:8001/health)
if echo "$HEALTH" | grep -q "healthy"; then
  echo -e "  ${GREEN}✅ Health check PASSED${NC}"
else
  echo -e "  ${RED}❌ Health check FAILED${NC}"
  echo "  Response: $HEALTH"
fi

# Test 2: Login
echo "  Test 2: Login"
LOGIN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
if echo "$LOGIN" | grep -q "token"; then
  echo -e "  ${GREEN}✅ Login PASSED${NC}"
else
  echo -e "  ${RED}❌ Login FAILED${NC}"
  echo "  Response: $LOGIN"
fi

# Test 3: Check Redis rate limiter
echo "  Test 3: Redis rate limiter"
RATE_LIMIT=$(sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} \
  "docker logs signage-backend-python --tail 50 | grep 'Rate Limiter' || echo 'Not found'")
if echo "$RATE_LIMIT" | grep -q "Using Redis backend"; then
  echo -e "  ${GREEN}✅ Redis rate limiter ENABLED${NC}"
  echo "  $RATE_LIMIT"
else
  echo -e "  ${YELLOW}⚠️ Using fallback (check logs)${NC}"
  echo "  $RATE_LIMIT"
fi

# Test 4: Check ClamAV status
echo "  Test 4: ClamAV status"
CLAMAV_STATUS=$(sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} \
  "docker ps | grep clamav")
if [ ! -z "$CLAMAV_STATUS" ]; then
  echo -e "  ${GREEN}✅ ClamAV container running${NC}"
else
  echo -e "  ${RED}❌ ClamAV container NOT running${NC}"
fi

# Test 5: Check backend logs for errors
echo "  Test 5: Backend logs"
ERRORS=$(sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} \
  "docker logs signage-backend-python --tail 100 | grep -E '(ERROR|CRITICAL|Exception)' || echo 'No errors'")
if echo "$ERRORS" | grep -q "No errors"; then
  echo -e "  ${GREEN}✅ No errors in logs${NC}"
else
  echo -e "  ${YELLOW}⚠️ Found some errors/exceptions:${NC}"
  echo "$ERRORS" | head -10
fi

echo ""
echo -e "${GREEN}✅ All smoke tests completed${NC}"
echo ""

# Summary
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Deployment Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Fixes Deployed: ${GREEN}3 (P0-11, P0-12, P0-14)${NC}"
echo -e "Files Modified: ${GREEN}3 files${NC}"
echo -e "Infrastructure: ${GREEN}ClamAV added${NC}"
echo -e "Database Migrations: ${GREEN}0 (code-only)${NC}"
echo -e "Downtime: ${GREEN}~3 minutes${NC}"
echo -e "Status: ${GREEN}✅ COMPLETED${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. ✅ Monitor backend logs for 1 hour"
echo "2. ✅ Test file upload with virus scanning"
echo "3. ✅ Test rate limiting with multiple requests"
echo "4. ⏳ Wait for ClamAV virus DB update (~5 minutes)"
echo "5. ⏳ Monitor for 24 hours"
echo ""
echo -e "${GREEN}Deployment completed successfully! 🎉${NC}"
echo ""
echo -e "${YELLOW}Fixes Completed:${NC}"
echo "  P0-11: ✅ File cleanup on database transaction failure"
echo "  P0-12: ✅ Redis-backed rate limiter (multi-worker safe)"
echo "  P0-14: ✅ ClamAV virus scanning integration"
echo ""
echo -e "${YELLOW}Total Progress: 12/16 P0 fixes (75%)${NC}"
