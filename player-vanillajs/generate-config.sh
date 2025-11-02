#!/bin/bash
# Generate env.js from env.template.js using environment variables
# Usage: ./generate-config.sh

set -e

echo "==================================="
echo "Player Viewer Config Generator"
echo "==================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please copy .env.example to .env and configure your values:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Load environment variables from .env
echo "📂 Loading environment variables from .env..."
export $(grep -v '^#' .env | xargs)

# Set build time
export BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "✅ Environment variables loaded"
echo ""
echo "Configuration:"
echo "  - API URL: $VIEWER_API_URL"
echo "  - WebSocket URL: $VIEWER_WEBSOCKET_URL"
echo "  - Environment: $ENVIRONMENT"
echo "  - Build Time: $BUILD_TIME"
echo ""

# Generate env.js from template
TEMPLATE_FILE="js/core/config/env.template.js"
OUTPUT_FILE="js/core/config/env.js"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

echo "🔧 Generating $OUTPUT_FILE from template..."

# Use envsubst to replace variables
envsubst < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "✅ Configuration file generated successfully!"
echo "📄 Output: $OUTPUT_FILE"
echo ""
echo "==================================="
echo "✅ Done! You can now deploy the viewer."
echo "==================================="
