#!/bin/bash
# WebOS Viewer Server Start Script
# Serves viewer on port 8081 for WebOS TV production

PORT=8081
VIEWER_DIR="/home/gzjbbk/signage/webos-viewer"

echo "========================================="
echo "WebOS Viewer Server (Production)"
echo "========================================="
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port $PORT is already in use"
    echo ""
    echo "Processes using port $PORT:"
    lsof -i :$PORT
    echo ""
    read -p "Kill existing process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        echo "Killing process on port $PORT..."
        kill $(lsof -t -i:$PORT)
        sleep 2
    else
        echo "Aborted."
        exit 1
    fi
fi

# Start server
echo "🚀 Starting WebOS Viewer Server..."
echo "📁 Directory: $VIEWER_DIR"
echo "🌐 Port: $PORT"
echo ""
echo "Access URLs:"
echo "  Local:   http://localhost:$PORT"
echo "  Network: http://192.168.5.12:$PORT"
echo ""
echo "WebOS App loads from:"
echo "  http://192.168.5.12:$PORT/index.html"
echo ""
echo "========================================="
echo "Press Ctrl+C to stop server"
echo "========================================="
echo ""

# Change to directory and start server
cd "$VIEWER_DIR" || exit
python3 -m http.server $PORT
