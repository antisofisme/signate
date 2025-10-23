#!/bin/bash
# Browser Testing Helper Script

echo "========================================="
echo "WebOS App Browser Testing"
echo "========================================="
echo ""

# Check if webos-viewer server is running
if ! nc -z localhost 8081 2>/dev/null; then
    echo "⚠️  WebOS viewer server not running on port 8081"
    echo ""
    echo "Starting server..."
    cd ../webos-viewer
    python3 -m http.server 8081 &
    SERVER_PID=$!
    echo "✅ Server started (PID: $SERVER_PID)"
    echo ""
    sleep 2
else
    echo "✅ Server already running on port 8081"
    echo ""
fi

# Check if backend API is running
if ! nc -z 192.168.5.12 8001 2>/dev/null; then
    echo "⚠️  Backend API not reachable at 192.168.5.12:8001"
    echo ""
    echo "Please ensure backend is running:"
    echo "  ssh gzjbbk@192.168.5.12"
    echo "  docker ps | grep signage-backend"
    echo ""
else
    echo "✅ Backend API reachable"
    echo ""
fi

# Display testing instructions
echo "========================================="
echo "Browser Testing Instructions"
echo "========================================="
echo ""
echo "1. Open browser (Chrome recommended)"
echo "2. Navigate to: http://localhost:8080"
echo ""
echo "3. Open DevTools (F12)"
echo "4. Enable Device Toolbar (Ctrl+Shift+M)"
echo "5. Set resolution: 1920 x 1080"
echo ""
echo "6. Test checklist:"
echo "   ✓ Activation code appears"
echo "   ✓ Console shows cache initialization"
echo "   ✓ Register device in Web Admin"
echo "   ✓ Assign content"
echo "   ✓ Content downloads and plays"
echo ""
echo "7. Check cache in DevTools:"
echo "   → Application tab"
echo "   → IndexedDB"
echo "   → SignageMediaCache"
echo ""
echo "========================================="
echo ""

# Open browser (if possible)
if command -v xdg-open &> /dev/null; then
    echo "Opening browser..."
    xdg-open "http://localhost:8081" 2>/dev/null
elif command -v open &> /dev/null; then
    echo "Opening browser..."
    open "http://localhost:8081"
elif command -v start &> /dev/null; then
    echo "Opening browser..."
    start "http://localhost:8081"
else
    echo "Please open browser manually:"
    echo "  http://localhost:8081"
    echo ""
fi

echo "Press Ctrl+C to stop server when done testing"
echo ""

# If we started the server, wait for Ctrl+C
if [ ! -z "$SERVER_PID" ]; then
    trap "echo ''; echo 'Stopping server...'; kill $SERVER_PID 2>/dev/null; exit" INT
    wait $SERVER_PID
fi
