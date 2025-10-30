#!/bin/bash

################################################################################
# Rollback Script Template
################################################################################
#
# This script will be customized with actual backup file names during deployment
# Use this as a reference for manual rollback if needed
#
################################################################################

set -euo pipefail

# Configuration (WILL BE FILLED BY DEPLOYMENT SCRIPT)
readonly SERVER_IP="192.168.5.12"
readonly SERVER_USER="gzjbbk"
readonly SERVER_PASSWORD="Password@2021"
readonly SERVER_PROJECT_PATH="/home/gzjbbk/prototipe2"
readonly BACKUP_DIR="${SERVER_PROJECT_PATH}/backups"

# These will be filled with actual backup file names
DB_BACKUP_FILE="signage_db_backup_YYYYMMDD_HHMMSS.sql"
COMPOSE_BACKUP_FILE="docker-compose.yml.backup_YYYYMMDD_HHMMSS"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}         ROLLBACK DEPLOYMENT${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}⚠ WARNING: This will rollback to the previous state${NC}"
echo -e "${YELLOW}Server: ${SERVER_IP}${NC}"
echo ""

read -p "Are you sure you want to rollback? (type 'YES' to confirm): " confirm
if [[ "${confirm}" != "YES" ]]; then
    echo -e "${GREEN}Rollback cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}Step 1: Stopping all services...${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "cd ${SERVER_PROJECT_PATH} && docker-compose -f docker/docker-compose.yml down"
echo -e "${GREEN}✓ Services stopped${NC}"

echo ""
echo -e "${CYAN}Step 2: Restoring docker-compose.yml...${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "cp ${BACKUP_DIR}/${COMPOSE_BACKUP_FILE} ${SERVER_PROJECT_PATH}/docker/docker-compose.yml"
echo -e "${GREEN}✓ docker-compose.yml restored${NC}"

echo ""
echo -e "${CYAN}Step 3: Starting database...${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "cd ${SERVER_PROJECT_PATH} && docker-compose -f docker/docker-compose.yml up -d postgres"
sleep 10
echo -e "${GREEN}✓ Database started${NC}"

echo ""
echo -e "${CYAN}Step 4: Restoring database backup...${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "docker exec -i signage-postgres psql -U signage_user -d signage_db < ${BACKUP_DIR}/${DB_BACKUP_FILE}"
echo -e "${GREEN}✓ Database restored${NC}"

echo ""
echo -e "${CYAN}Step 5: Restarting all services...${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "cd ${SERVER_PROJECT_PATH} && docker-compose -f docker/docker-compose.yml up -d"
echo -e "${GREEN}✓ Services restarted${NC}"

echo ""
echo -e "${CYAN}Step 6: Waiting for services to be ready...${NC}"
sleep 20
echo -e "${GREEN}✓ Services should be ready${NC}"

echo ""
echo -e "${CYAN}Checking service status:${NC}"
sshpass -p "${SERVER_PASSWORD}" ssh "${SERVER_USER}@${SERVER_IP}" \
    "cd ${SERVER_PROJECT_PATH} && docker-compose -f docker/docker-compose.yml ps"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Rollback completed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Backend API:  http://${SERVER_IP}:8001/"
echo -e "API Docs:     http://${SERVER_IP}:8001/docs"
echo -e "Viewer:       http://${SERVER_IP}:8080/"
echo ""
