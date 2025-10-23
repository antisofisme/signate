#!/bin/bash
# WebOS App Packaging Script

echo "========================================="
echo "WebOS Digital Signage App Packager"
echo "========================================="
echo ""

# Check if ares-package is installed
if ! command -v ares-package &> /dev/null; then
    echo "❌ Error: ares-package not found!"
    echo ""
    echo "Please install WebOS CLI tools first:"
    echo "  npm install -g @webos-tools/cli"
    echo ""
    exit 1
fi

echo "✅ WebOS CLI tools found"
echo ""

# Create build directory if not exists
mkdir -p ../build

# Get version from appinfo.json
VERSION=$(grep '"version"' appinfo.json | sed 's/.*"version": "\(.*\)".*/\1/')
echo "📦 Packaging app version: $VERSION"
echo ""

# Package the app
echo "🔨 Building IPK package..."
ares-package . --outdir ../build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Package created successfully!"
    echo ""
    echo "📦 Output: ../build/com.signage.viewer_${VERSION}_all.ipk"
    echo ""
    echo "Next steps:"
    echo "  1. Install to TV: ares-install --device mytv ../build/com.signage.viewer_${VERSION}_all.ipk"
    echo "  2. Launch app: ares-launch --device mytv com.signage.viewer"
    echo ""
else
    echo ""
    echo "❌ Packaging failed!"
    echo ""
    exit 1
fi
