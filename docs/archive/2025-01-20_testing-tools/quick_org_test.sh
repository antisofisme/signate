#!/bin/bash
# Quick organization API test

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token: ${TOKEN:0:30}..."

# Test list organizations
echo -e "\n=== Testing GET /api/v1/organizations ==="
curl -s -X GET http://192.168.5.12:8001/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -50

# Test get quota
echo -e "\n=== Testing GET /api/v1/organizations/1/quota ==="
curl -s -X GET http://192.168.5.12:8001/api/v1/organizations/1/quota \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\nDone!"
