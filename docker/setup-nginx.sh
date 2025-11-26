#!/bin/bash

# Signage System - Nginx Setup Script
# This script sets up Nginx on the host system with domain support
# Run this AFTER deploy-production.sh and AFTER DNS propagation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Signage System - Nginx Setup"
echo "=========================================="
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo bash docker/setup-nginx.sh"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please run deploy-production.sh first"
    exit 1
fi

# Load environment variables
echo -e "${GREEN}✓${NC} Loading environment variables from .env"
set -a
source "$PROJECT_ROOT/.env"
set +a

# Validate domain variables
if [ -z "$API_DOMAIN" ] || [ -z "$ADMIN_DOMAIN" ] || [ -z "$PLAYER_DOMAIN" ]; then
    echo -e "${RED}Error: Domain variables not set in .env${NC}"
    exit 1
fi

echo ""
echo "Domain Configuration:"
echo "  - Admin: $ADMIN_DOMAIN"
echo "  - API: $API_DOMAIN"
echo "  - Player: $PLAYER_DOMAIN"
echo ""

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx not installed. Installing..."
    apt-get update
    apt-get install -y nginx
    echo -e "${GREEN}✓${NC} Nginx installed"
else
    echo -e "${GREEN}✓${NC} Nginx already installed"
fi

# Check if Nginx config was generated
NGINX_CONFIG="$SCRIPT_DIR/nginx/signage.conf"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo -e "${RED}Error: Nginx config not found at $NGINX_CONFIG${NC}"
    echo "Please run deploy-production.sh first to generate the config"
    exit 1
fi

# Backup existing Nginx config if exists
SITES_AVAILABLE="/etc/nginx/sites-available/signage"
SITES_ENABLED="/etc/nginx/sites-enabled/signage"

if [ -f "$SITES_AVAILABLE" ]; then
    echo "Backing up existing Nginx config..."
    cp "$SITES_AVAILABLE" "$SITES_AVAILABLE.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✓${NC} Backup created"
fi

# Copy generated config to Nginx
echo "Installing Nginx configuration..."
cp "$NGINX_CONFIG" "$SITES_AVAILABLE"
echo -e "${GREEN}✓${NC} Config copied to $SITES_AVAILABLE"

# Enable site (create symlink)
if [ -f "$SITES_ENABLED" ]; then
    rm "$SITES_ENABLED"
fi
ln -s "$SITES_AVAILABLE" "$SITES_ENABLED"
echo -e "${GREEN}✓${NC} Site enabled"

# Remove default Nginx site if exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "Removing default Nginx site..."
    rm /etc/nginx/sites-enabled/default
    echo -e "${GREEN}✓${NC} Default site removed"
fi

# Test Nginx configuration
echo ""
echo "Testing Nginx configuration..."
if nginx -t; then
    echo -e "${GREEN}✓${NC} Nginx configuration is valid"
else
    echo -e "${RED}Error: Nginx configuration test failed${NC}"
    echo "Restoring backup..."
    if [ -f "$SITES_AVAILABLE.backup."* ]; then
        cp "$SITES_AVAILABLE.backup."* "$SITES_AVAILABLE"
    fi
    exit 1
fi

# Reload Nginx
echo ""
echo "Reloading Nginx..."
systemctl reload nginx
echo -e "${GREEN}✓${NC} Nginx reloaded"

# Check Nginx status
echo ""
echo "Nginx Status:"
systemctl status nginx --no-pager | head -n 10

echo ""
echo "=========================================="
echo "Nginx Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration installed at:"
echo "  $SITES_AVAILABLE"
echo ""
echo "Next Steps:"
echo "1. Verify DNS propagation:"
echo "   host $ADMIN_DOMAIN"
echo "   host $API_DOMAIN"
echo "   host $PLAYER_DOMAIN"
echo ""
echo "2. Test HTTP access (from another machine):"
echo "   curl -I http://$ADMIN_DOMAIN"
echo "   curl -I http://$API_DOMAIN/health"
echo ""
echo "3. Install SSL certificates:"
echo "   sudo bash docker/setup-ssl.sh"
echo ""
echo "Nginx Logs:"
echo "  sudo tail -f /var/log/nginx/access.log"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""
