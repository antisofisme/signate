#!/usr/bin/env python3
"""
WebSocket Test Script
Test WebSocket connections to the Digital Signage backend
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_status():
    """Test WebSocket status endpoint"""
    import urllib.request
    import json
    
    try:
        response = urllib.request.urlopen('http://192.168.5.12:8001/ws/status')
        data = json.loads(response.read().decode())
        print("📊 WebSocket Status:")
        print(f"  Status: {data['status']}")
        print(f"  Total Devices: {data['connections']['total_devices']}")
        print(f"  Total Admins: {data['connections']['total_admins']}")
        print(f"  Organizations: {data['connections']['organizations']}")
        print(f"  Features: {', '.join(data['features'])}")
        return True
    except Exception as e:
        print(f"❌ WebSocket status check failed: {e}")
        return False

async def test_websocket_connection():
    """Test WebSocket connection without auth (should fail gracefully)"""
    try:
        print("\n🔌 Testing WebSocket Connection...")
        
        # Try to connect to admin WebSocket without token
        uri = "ws://192.168.5.12:8001/ws/admin"
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Try to send a test message
            test_message = {"type": "ping", "timestamp": "2025-11-12T00:00:00Z"}
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent: {test_message}")
            
            # Try to receive response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Received: {response}")
            except asyncio.TimeoutError:
                print("⏱️ No response received (timeout)")
                
    except websockets.exceptions.ConnectionClosedError as e:
        if e.code == 1008:
            print("✅ WebSocket properly rejected unauthorized connection (code 1008)")
            return True
        else:
            print(f"❌ WebSocket connection closed unexpectedly: {e}")
            return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Digital Signage WebSocket Test")
    print("=" * 50)
    
    # Test 1: WebSocket status endpoint
    status_ok = await test_websocket_status()
    
    # Test 2: WebSocket connection
    connection_ok = await test_websocket_connection()
    
    print("\n📋 Test Results:")
    print(f"  WebSocket Status API: {'✅ PASS' if status_ok else '❌ FAIL'}")
    print(f"  WebSocket Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    
    overall_success = status_ok and connection_ok
    print(f"\n🎯 Overall WebSocket Test: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))