#!/bin/bash

# Test script for Minimal Storage API
# Usage: ./test_minimal_api.sh [base_url]

BASE_URL="${1:-http://localhost:8000}"
API_URL="$BASE_URL/api/storage"

echo "=========================================="
echo "Testing Minimal Storage API"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo

# Test 1: Health Check
echo "Test 1: Health Check"
echo "GET $API_URL/health"
curl -s "$API_URL/health" | python3 -m json.tool
echo
echo

# Test 2: Upload File (create test file)
echo "Test 2: Upload File"
echo "Creating test file..."
echo "This is a test file" > /tmp/test_upload.txt

echo "POST $API_URL/upload"
UPLOAD_RESPONSE=$(curl -s -F "file=@/tmp/test_upload.txt" "$API_URL/upload")
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

# Extract asset_id from response
ASSET_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['asset_id'])" 2>/dev/null)
echo
echo "Uploaded asset_id: $ASSET_ID"
echo
echo

if [ -n "$ASSET_ID" ]; then
    # Test 3: Get Asset Info
    echo "Test 3: Get Asset Info"
    echo "GET $API_URL/$ASSET_ID"
    curl -s "$API_URL/$ASSET_ID" | python3 -m json.tool
    echo
    echo

    # Test 4: Serve File
    echo "Test 4: Serve File"
    echo "GET $API_URL/serve/$ASSET_ID"
    curl -s "$API_URL/serve/$ASSET_ID"
    echo
    echo

    # Test 5: Delete File
    echo "Test 5: Delete File"
    echo "DELETE $API_URL/delete/$ASSET_ID"
    curl -s -X DELETE "$API_URL/delete/$ASSET_ID" | python3 -m json.tool
    echo
else
    echo "Upload failed, skipping remaining tests"
fi

# Cleanup
rm -f /tmp/test_upload.txt

echo
echo "=========================================="
echo "Tests Complete"
echo "=========================================="
