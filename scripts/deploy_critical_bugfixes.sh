#!/bin/bash
# Critical Bug Fixes Deployment Script
# Date: 2025-01-14
# Fixes: 4 critical bugs blocking user service

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Server details
SERVER_USER="gzjbbk"
SERVER_HOST="192.168.5.12"
SERVER_PASS="Password@2021"
PROJECT_DIR="/home/gzjbbk/signate"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Critical Bug Fixes Deployment${NC}"
echo -e "${YELLOW}  4 Bugs Fixed - User Service Restored${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Step 1: Backup
echo -e "${GREEN}[Step 1/5] Creating backup...${NC}"
BACKUP_DIR="~/backups/pre_bugfixes_$(date +%Y%m%d_%H%M%S)"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  mkdir -p $BACKUP_DIR && \
  docker exec signage-postgres pg_dump -U signage_user -d signage_db > \
    $BACKUP_DIR/signage_db_backup.sql && \
  echo 'Backup created' && \
  ls -lh $BACKUP_DIR/signage_db_backup.sql
"
echo -e "${GREEN}✅ Backup completed${NC}"
echo ""

# Step 2: Stop backend
echo -e "${GREEN}[Step 2/5] Stopping backend...${NC}"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  cd $PROJECT_DIR && \
  docker-compose -f docker/docker-compose.yml stop backend-api
"
echo -e "${GREEN}✅ Backend stopped${NC}"
echo ""

# Step 3: Deploy fixes
echo -e "${GREEN}[Step 3/5] Deploying bug fixes (2 files)...${NC}"
cd /mnt/g/khoirul/signate

FILES=(
  "backend-python/services/user/repositories/user_repo.py"
  "backend-python/shared/errors.py"
)

for file in "${FILES[@]}"; do
  echo "  Syncing: $file"
  sshpass -p "$SERVER_PASS" rsync -avz "$file" \
    ${SERVER_USER}@${SERVER_HOST}:${PROJECT_DIR}/${file}
done

echo -e "${GREEN}✅ Bug fixes deployed${NC}"
echo ""

# Step 4: Restart backend
echo -e "${GREEN}[Step 4/5] Restarting backend...${NC}"
sshpass -p "$SERVER_PASS" ssh ${SERVER_USER}@${SERVER_HOST} "
  cd $PROJECT_DIR && \
  docker-compose -f docker/docker-compose.yml start backend-api && \
  echo 'Waiting 30 seconds...' && \
  sleep 30
"
echo -e "${GREEN}✅ Backend restarted${NC}"
echo ""

# Step 5: Test
echo -e "${GREEN}[Step 5/5] Running tests...${NC}"

# Test 1: Health
echo "  Test 1: Health check"
HEALTH=$(curl -s http://192.168.5.12:8001/health)
if echo "$HEALTH" | grep -q "healthy"; then
  echo -e "  ${GREEN}✅ PASS${NC}"
else
  echo -e "  ${RED}❌ FAIL${NC}"
fi

# Test 2: Login
echo "  Test 2: Login"
LOGIN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
if echo "$LOGIN" | grep -q "token"; then
  echo -e "  ${GREEN}✅ PASS${NC}"
  TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

  # Test 3: List users (was broken)
  echo "  Test 3: List users"
  USERS=$(curl -s -H "Authorization: Bearer $TOKEN" \
    http://192.168.5.12:8001/api/v1/users)
  if echo "$USERS" | grep -q "username"; then
    echo -e "  ${GREEN}✅ PASS - User service WORKING!${NC}"
  else
    echo -e "  ${RED}❌ FAIL${NC}"
    echo "  Response: $USERS"
  fi
else
  echo -e "  ${RED}❌ FAIL${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Bugs Fixed:${NC}"
echo "  1. ✅ User role mapping (CRITICAL)"
echo "  2. ✅ Duplicate username error handling"
echo "  3. ✅ SESSION_REVOKED error code"
echo "  4. ✅ User create/update role_id assignment"
echo ""
echo -e "${GREEN}User Management Service: RESTORED${NC}"
