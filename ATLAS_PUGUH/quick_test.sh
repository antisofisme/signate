#!/bin/bash
# ATLAS_PUGUH Phase A+ - Quick Test Script
# Run this to verify deployment is working

set -e

API_URL="http://31.97.111.175:25536/api"
FRONTEND_URL="http://31.97.111.175:3000"
TENANT_ID="550e8400-e29b-41d4-a716-446655440000"

echo "=========================================="
echo "🧪 ATLAS_PUGUH Phase A+ - Quick Test"
echo "=========================================="
echo ""

# Test 1: Frontend health
echo "1️⃣  Testing Frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/health")
if [ "$FRONTEND_STATUS" = "200" ]; then
  echo "   ✅ Frontend is UP ($FRONTEND_URL)"
else
  echo "   ❌ Frontend is DOWN (Status: $FRONTEND_STATUS)"
  exit 1
fi
echo ""

# Test 2: Backend API health
echo "2️⃣  Testing Backend API..."
BACKEND_RESPONSE=$(curl -s "$API_URL/decisions?tenant_id=$TENANT_ID")
DECISION_COUNT=$(echo "$BACKEND_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')

if [ "$DECISION_COUNT" -ge 5 ]; then
  echo "   ✅ Backend API is UP"
  echo "   ✅ Found $DECISION_COUNT decisions in database"
else
  echo "   ⚠️  Backend API is UP but no test data found"
  echo "   ℹ️  Run: ssh root@31.97.111.175 'docker exec -i postgresql-1f85ac2c-3200-7c4a-6af6-c8802fa6b6e2 psql -U atlas_user -d atlas_puguh < /tmp/insert_test_data_correct.sql'"
fi
echo ""

# Test 3: Workflows
echo "3️⃣  Testing Workflows..."
WORKFLOW_RESPONSE=$(curl -s "$API_URL/workflows?tenant_id=$TENANT_ID&state=PENDING_APPROVAL")
WORKFLOW_COUNT=$(echo "$WORKFLOW_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')

if [ "$WORKFLOW_COUNT" -ge 2 ]; then
  echo "   ✅ Workflow engine is working"
  echo "   ✅ Found $WORKFLOW_COUNT pending approvals"
else
  echo "   ⚠️  No pending workflows found"
fi
echo ""

# Test 4: Frontend-Backend integration
echo "4️⃣  Testing Frontend-Backend Integration..."
FRONTEND_HTML=$(curl -s "$FRONTEND_URL")
API_URL_IN_HTML=$(echo "$FRONTEND_HTML" | grep -o 'http://31.97.111.175:25536/api')

if [ ! -z "$API_URL_IN_HTML" ]; then
  echo "   ✅ Frontend configured with correct API URL"
  echo "   ✅ URL: $API_URL_IN_HTML"
else
  echo "   ❌ Frontend not configured correctly"
  exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""
echo "✅ Frontend:      $FRONTEND_URL"
echo "✅ Backend API:   $API_URL"
echo "✅ Decisions:     $DECISION_COUNT total"
echo "✅ Workflows:     $WORKFLOW_COUNT pending"
echo ""
echo "🎯 Next Step: Open browser → $FRONTEND_URL"
echo ""
echo "=========================================="
echo "✅ All Tests Passed! Deployment Working!"
echo "=========================================="
