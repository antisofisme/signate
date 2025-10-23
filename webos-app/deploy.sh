#!/bin/bash
# WebOS App Deployment Script

echo "========================================="
echo "WebOS Digital Signage App Deployer"
echo "========================================="
echo ""

# Default device name
DEVICE=${1:-mytv}

# Check if ares-install is installed
if ! command -v ares-install &> /dev/null; then
    echo "❌ Error: ares-install not found!"
    echo ""
    echo "Please install WebOS CLI tools first:"
    echo "  npm install -g @webos-tools/cli"
    echo ""
    exit 1
fi

echo "✅ WebOS CLI tools found"
echo "📱 Target device: $DEVICE"
echo ""

# Check if device is configured
if ! ares-device-info -d $DEVICE &> /dev/null; then
    echo "❌ Error: Device '$DEVICE' not found!"
    echo ""
    echo "Please setup device first:"
    echo "  ares-setup-device"
    echo ""
    echo "Or specify device name:"
    echo "  ./deploy.sh your-device-name"
    echo ""
    exit 1
fi

echo "✅ Device found and connected"
echo ""

# Get latest IPK file
IPK_FILE=$(ls -t ../build/com.signage.viewer_*.ipk 2>/dev/null | head -1)

if [ -z "$IPK_FILE" ]; then
    echo "❌ Error: No IPK file found in ../build/"
    echo ""
    echo "Please package the app first:"
    echo "  ./package.sh"
    echo ""
    exit 1
fi

echo "📦 Installing: $IPK_FILE"
echo ""

# Install app to TV
ares-install --device $DEVICE "$IPK_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ App installed successfully!"
    echo ""
    
    # Ask to launch app
    read -p "Launch app now? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Launching app..."
        ares-launch --device $DEVICE com.signage.viewer
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ App launched successfully!"
            echo ""
            echo "📺 Check your TV screen for the activation code"
            echo "🌐 Go to Web Admin to activate: http://localhost:3000/devices"
            echo ""
        else
            echo ""
            echo "❌ Failed to launch app"
            echo ""
        fi
    fi
    
    echo ""
    echo "Useful commands:"
    echo "  List installed apps: ares-install --device $DEVICE --list"
    echo "  Launch app: ares-launch --device $DEVICE com.signage.viewer"
    echo "  Close app: ares-launch --device $DEVICE --close com.signage.viewer"
    echo "  Debug app: ares-inspect --device $DEVICE --app com.signage.viewer --open"
    echo ""
else
    echo ""
    echo "❌ Installation failed!"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Developer Mode enabled on TV"
    echo "  2. Check Key Server enabled on TV"
    echo "  3. Verify device connection: ares-device-info -d $DEVICE"
    echo "  4. Check TV and PC on same network"
    echo ""
    exit 1
fi
