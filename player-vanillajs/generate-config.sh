#!/bin/bash

# =============================================================================
# Viewer Configuration Generator
# =============================================================================
# Generates viewer/js/config/env.js from template using environment variables
#
# Usage:
#   ./viewer/generate-config.sh
#
# Requirements:
#   - .env file in project root
#   - envsubst command (part of gettext package)
# =============================================================================

set -e

# Change to project root
cd "$(dirname "$0")/.."

echo "=========================================="
echo "  Viewer Config Generator"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found in project root"
    echo "   Please create .env file first"
    exit 1
fi

# Load environment variables from .env
echo "📄 Loading environment variables from .env..."
set -a  # automatically export all variables
source .env
set +a

# Set BUILD_TIME
export BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Set defaults for viewer-specific variables if not in .env
export VIEWER_API_URL="${VIEWER_API_URL:-http://192.168.5.12:8001}"
export VIEWER_WEBSOCKET_URL="${VIEWER_WEBSOCKET_URL:-ws://192.168.5.12:8001}"
export VIEWER_POLLING_INTERVAL="${VIEWER_POLLING_INTERVAL:-30000}"
export VIEWER_HEARTBEAT_INTERVAL="${VIEWER_HEARTBEAT_INTERVAL:-30000}"
export VIEWER_ACTIVATION_POLL_INTERVAL="${VIEWER_ACTIVATION_POLL_INTERVAL:-2000}"
export VIEWER_REGISTRATION_RETRY_INTERVAL="${VIEWER_REGISTRATION_RETRY_INTERVAL:-60000}"
export VIEWER_CONTENT_REFRESH_INTERVAL="${VIEWER_CONTENT_REFRESH_INTERVAL:-60000}"
export VIEWER_SPEEDTEST_INTERVAL="${VIEWER_SPEEDTEST_INTERVAL:-300000}"
export VIEWER_RESET_PASSWORD="${VIEWER_RESET_PASSWORD:-admin123}"
export ENVIRONMENT="${ENVIRONMENT:-production}"

# Generate env.js from template
echo "🔧 Generating viewer/js/config/env.js..."
envsubst < viewer/js/config/env.template.js > viewer/js/config/env.js

# Verify generated file
if [ -f "viewer/js/config/env.js" ]; then
    echo "✅ Configuration generated successfully!"
    echo ""
    echo "Generated config:"
    echo "  - API URL: $VIEWER_API_URL"
    echo "  - WebSocket URL: $VIEWER_WEBSOCKET_URL"
    echo "  - Environment: $ENVIRONMENT"
    echo "  - Build Time: $BUILD_TIME"
    echo ""
    echo "📄 Output file: viewer/js/config/env.js"
else
    echo "❌ ERROR: Failed to generate config file"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Done!"
echo "=========================================="
