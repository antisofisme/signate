#!/bin/bash
# =============================================================================
# CONFIGURATION VALIDATION SCRIPT
# =============================================================================
# Validates environment configuration for Smart TV Digital Signage System
# Usage: ./validate-config.sh [environment]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENV_TYPE="${1:-development}"

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}  Configuration Validation${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    exit 1
fi

# Source the environment file
set -a
source ../.env
set +a

echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "Server Host: ${GREEN}${SERVER_HOST}${NC}"
echo ""

# Required variables based on environment
declare -a REQUIRED_VARS=(
    "ENVIRONMENT"
    "DEBUG"
    "LOG_LEVEL"
    "SERVER_HOST"
    "PORT_BACKEND_API"
    "PORT_ANTHIAS"
    "PORT_WEB_ADMIN"
    "PORT_VIEWER"
    "PORT_POSTGRES"
    "PORT_REDIS"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "SECRET_KEY"
    "JWT_SECRET_KEY"
    "API_BASE_URL"
)

# Additional required vars for production
if [ "$ENVIRONMENT" == "production" ]; then
    REQUIRED_VARS+=(
        "BACKUP_ENABLED"
        "RATE_LIMIT_ENABLED"
        "METRICS_ENABLED"
    )
fi

echo -e "${BLUE}Checking required variables...${NC}"
echo "----------------------------------------"

# Check required variables
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=($var)
        echo -e "  ${RED}✗${NC} $var - MISSING"
    else
        # Mask sensitive values
        if [[ "$var" == *"PASSWORD"* ]] || [[ "$var" == *"SECRET"* ]] || [[ "$var" == *"KEY"* ]]; then
            echo -e "  ${GREEN}✓${NC} $var - ********"
        else
            echo -e "  ${GREEN}✓${NC} $var - ${!var}"
        fi
    fi
done

echo ""

# Report missing variables
if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    printf '  - %s\n' "${MISSING_VARS[@]}"
    exit 1
fi

# Validate environment value
echo -e "${BLUE}Validating configuration values...${NC}"
echo "----------------------------------------"

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}ERROR: Invalid ENVIRONMENT value: $ENVIRONMENT${NC}"
    echo "Must be one of: development, staging, production"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Environment is valid: $ENVIRONMENT"

# Check port conflicts
echo ""
echo -e "${BLUE}Checking for port conflicts...${NC}"
echo "----------------------------------------"

declare -a PORTS=(
    "$PORT_BACKEND_API"
    "$PORT_ANTHIAS"
    "$PORT_WEB_ADMIN"
    "$PORT_VIEWER"
    "$PORT_POSTGRES"
    "$PORT_REDIS"
)

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ${YELLOW}⚠${NC}  Port $port is already in use"
    else
        echo -e "  ${GREEN}✓${NC} Port $port is available"
    fi
done

# Security checks for production
if [ "$ENVIRONMENT" == "production" ]; then
    echo ""
    echo -e "${BLUE}Production security checks...${NC}"
    echo "----------------------------------------"

    # Check for default passwords
    if [[ "$POSTGRES_PASSWORD" == "your_password_here" ]] || [[ "$POSTGRES_PASSWORD" == "dev_password" ]]; then
        echo -e "  ${RED}✗${NC} Using default database password in production!"
        exit 1
    else
        echo -e "  ${GREEN}✓${NC} Database password is not default"
    fi

    if [[ "$SECRET_KEY" == "your-secret-key-change-in-production"* ]]; then
        echo -e "  ${RED}✗${NC} Using default SECRET_KEY in production!"
        exit 1
    else
        echo -e "  ${GREEN}✓${NC} SECRET_KEY is not default"
    fi

    if [[ "$JWT_SECRET_KEY" == "your-jwt-secret"* ]]; then
        echo -e "  ${RED}✗${NC} Using default JWT_SECRET_KEY in production!"
        exit 1
    else
        echo -e "  ${GREEN}✓${NC} JWT_SECRET_KEY is not default"
    fi

    # Check DEBUG is disabled
    if [ "$DEBUG" == "true" ]; then
        echo -e "  ${YELLOW}⚠${NC}  DEBUG is enabled in production!"
    else
        echo -e "  ${GREEN}✓${NC} DEBUG is disabled"
    fi

    # Check API docs are disabled
    if [ "$ENABLE_API_DOCS" == "true" ]; then
        echo -e "  ${YELLOW}⚠${NC}  API docs are enabled in production!"
    else
        echo -e "  ${GREEN}✓${NC} API docs are disabled"
    fi
fi

# Test database connection (if postgres is running)
if [ "$ENVIRONMENT" != "production" ]; then
    echo ""
    echo -e "${BLUE}Testing service connections...${NC}"
    echo "----------------------------------------"

    # Database connection
    if command -v psql &> /dev/null; then
        PGPASSWORD=$POSTGRES_PASSWORD psql -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1 && {
            echo -e "  ${GREEN}✓${NC} PostgreSQL connection successful"
        } || {
            echo -e "  ${YELLOW}⚠${NC}  Cannot connect to PostgreSQL (may not be running yet)"
        }
    else
        echo -e "  ${YELLOW}⚠${NC}  psql not installed, skipping database check"
    fi

    # Redis connection
    if command -v redis-cli &> /dev/null; then
        redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1 && {
            echo -e "  ${GREEN}✓${NC} Redis connection successful"
        } || {
            echo -e "  ${YELLOW}⚠${NC}  Cannot connect to Redis (may not be running yet)"
        }
    else
        echo -e "  ${YELLOW}⚠${NC}  redis-cli not installed, skipping Redis check"
    fi

    # API endpoint check
    if command -v curl &> /dev/null; then
        curl -f -s -o /dev/null -w "%{http_code}" ${API_BASE_URL}/health 2>/dev/null | grep -q "200" && {
            echo -e "  ${GREEN}✓${NC} Backend API is responding"
        } || {
            echo -e "  ${YELLOW}⚠${NC}  Backend API not responding (may not be running yet)"
        }
    fi
fi

# Check file permissions
echo ""
echo -e "${BLUE}Checking file permissions...${NC}"
echo "----------------------------------------"

if [ -f "../.env" ]; then
    PERM=$(stat -c %a ../.env 2>/dev/null || stat -f %A ../.env 2>/dev/null)
    if [ "$PERM" == "644" ] || [ "$PERM" == "600" ]; then
        echo -e "  ${GREEN}✓${NC} .env file permissions are secure"
    else
        echo -e "  ${YELLOW}⚠${NC}  .env file permissions ($PERM) may be too open"
        echo "     Recommended: chmod 600 ../.env"
    fi
fi

# Generate summary
echo ""
echo -e "${BLUE}====================================${NC}"
echo -e "${GREEN}  Configuration validation complete!${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Server: $SERVER_HOST"
echo "Backend API: ${API_BASE_URL}"
echo "Web Admin: http://${SERVER_HOST}:${PORT_WEB_ADMIN}"
echo "Viewer: http://${SERVER_HOST}:${PORT_VIEWER}"
echo ""

if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${YELLOW}⚠  Production mode detected${NC}"
    echo "Please ensure:"
    echo "  • All secrets are stored in a secure secret manager"
    echo "  • SSL/TLS is configured for all endpoints"
    echo "  • Firewall rules are properly configured"
    echo "  • Backup procedures are in place"
    echo "  • Monitoring and alerting are configured"
fi

echo ""
echo "To start services, run:"
echo "  docker-compose up -d"
echo ""

exit 0