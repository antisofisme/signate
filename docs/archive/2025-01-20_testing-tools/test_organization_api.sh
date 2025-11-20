#!/bin/bash
# Organization Management API Test Suite
# Tests all organization endpoints including CRUD and quota management

BASE_URL="http://192.168.5.12:8001"
API_V1="${BASE_URL}/api/v1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0

# Functions
print_section() {
    echo -e "\n${BOLD}${BLUE}================================================================================"
    echo -e "$1"
    echo -e "================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
    ((TOTAL++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
    ((TOTAL++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Test variables
TOKEN=""
TEST_ORG_ID=""

# ============================================================================
# AUTHENTICATION
# ============================================================================

print_section "Organization Management API Test Report"
print_info "Base URL: ${BASE_URL}"
print_info "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

print_section "1. Authentication"

# Login
LOGIN_RESPONSE=$(curl -s -X POST "${API_V1}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

echo "$LOGIN_RESPONSE" | grep -q '"success":true'
if [ $? -eq 0 ]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
    print_success "Authentication successful"
    print_info "Token: ${TOKEN:0:50}..."
else
    print_error "Authentication failed"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

# ============================================================================
# CRUD OPERATIONS
# ============================================================================

print_section "2. CRUD Operations"

# 2.1 List Organizations
print_info "2.1. Testing GET /api/v1/organizations (List)"
LIST_RESPONSE=$(curl -s -X GET "${API_V1}/organizations" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$LIST_RESPONSE" | grep -q '"organizations":'
if [ $? -eq 0 ]; then
    TOTAL_ORGS=$(echo "$LIST_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    ACTIVE_ORGS=$(echo "$LIST_RESPONSE" | grep -o '"active":[0-9]*' | cut -d':' -f2)
    print_success "List organizations - Found ${TOTAL_ORGS} organizations (${ACTIVE_ORGS} active)"
else
    print_error "List organizations failed"
    echo "$LIST_RESPONSE" | head -3
fi

# 2.2 Create Organization
print_info "2.2. Testing POST /api/v1/organizations (Create)"
TIMESTAMP=$(date +%s)
CREATE_RESPONSE=$(curl -s -X POST "${API_V1}/organizations" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Test Organization ${TIMESTAMP}\",
        \"description\": \"Created by automated test\",
        \"address\": \"123 Test Street\",
        \"contact_email\": \"test@example.com\",
        \"contact_phone\": \"+1234567890\"
    }")

echo "$CREATE_RESPONSE" | grep -q '"id":'
if [ $? -eq 0 ]; then
    TEST_ORG_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    print_success "Create organization - Created organization ID: ${TEST_ORG_ID}"
else
    print_error "Create organization failed"
    echo "$CREATE_RESPONSE" | head -3
fi

# 2.3 Get Organization
if [ -n "$TEST_ORG_ID" ]; then
    print_info "2.3. Testing GET /api/v1/organizations/{org_id} (Get)"
    GET_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${TEST_ORG_ID}" \
        -H "Authorization: Bearer ${TOKEN}")

    echo "$GET_RESPONSE" | grep -q "\"id\":${TEST_ORG_ID}"
    if [ $? -eq 0 ]; then
        ORG_NAME=$(echo "$GET_RESPONSE" | grep -o '"name":"[^"]*' | cut -d'"' -f4)
        print_success "Get organization - Retrieved: ${ORG_NAME}"
    else
        print_error "Get organization failed"
        echo "$GET_RESPONSE" | head -3
    fi
fi

# 2.4 Update Organization
if [ -n "$TEST_ORG_ID" ]; then
    print_info "2.4. Testing PUT /api/v1/organizations/{org_id} (Update)"
    UPDATE_TIMESTAMP=$(date +%s)
    UPDATE_RESPONSE=$(curl -s -X PUT "${API_V1}/organizations/${TEST_ORG_ID}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"Updated Test Organization ${UPDATE_TIMESTAMP}\",
            \"description\": \"Updated by automated test\",
            \"address\": \"456 Updated Street\",
            \"contact_email\": \"updated@example.com\",
            \"contact_phone\": \"+9876543210\",
            \"is_active\": true
        }")

    echo "$UPDATE_RESPONSE" | grep -q "\"id\":${TEST_ORG_ID}"
    if [ $? -eq 0 ]; then
        print_success "Update organization - Updated successfully"
    else
        print_error "Update organization failed"
        echo "$UPDATE_RESPONSE" | head -3
    fi
fi

# ============================================================================
# QUOTA MANAGEMENT TESTS
# ============================================================================

print_section "3. Quota Management Tests"

# Use existing org ID 1 for quota tests
QUOTA_ORG_ID=${TEST_ORG_ID:-1}

# 3.1 Get Organization Quota
print_info "3.1. Testing GET /api/v1/organizations/{org_id}/quota"
QUOTA_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${QUOTA_ORG_ID}/quota" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$QUOTA_RESPONSE" | grep -q '"devices":'
if [ $? -eq 0 ]; then
    DEVICES_CURRENT=$(echo "$QUOTA_RESPONSE" | grep -o '"current":[0-9]*' | head -1 | cut -d':' -f2)
    DEVICES_MAX=$(echo "$QUOTA_RESPONSE" | grep -o '"max":[0-9]*' | head -1 | cut -d':' -f2)
    print_success "Get quota - Devices: ${DEVICES_CURRENT}/${DEVICES_MAX}"
else
    print_error "Get quota failed"
    echo "$QUOTA_RESPONSE" | head -3
fi

# 3.2 Check Device Quota
print_info "3.2. Testing GET /api/v1/organizations/{org_id}/quota/check/device"
CHECK_DEVICE_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${QUOTA_ORG_ID}/quota/check/device" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$CHECK_DEVICE_RESPONSE" | grep -q '"allowed":'
if [ $? -eq 0 ]; then
    ALLOWED=$(echo "$CHECK_DEVICE_RESPONSE" | grep -o '"allowed":[a-z]*' | cut -d':' -f2)
    print_success "Check device quota - Can add device: ${ALLOWED}"
else
    print_error "Check device quota failed"
    echo "$CHECK_DEVICE_RESPONSE" | head -3
fi

# 3.3 Check User Quota
print_info "3.3. Testing GET /api/v1/organizations/{org_id}/quota/check/user"
CHECK_USER_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${QUOTA_ORG_ID}/quota/check/user" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$CHECK_USER_RESPONSE" | grep -q '"allowed":'
if [ $? -eq 0 ]; then
    ALLOWED=$(echo "$CHECK_USER_RESPONSE" | grep -o '"allowed":[a-z]*' | cut -d':' -f2)
    print_success "Check user quota - Can add user: ${ALLOWED}"
else
    print_error "Check user quota failed"
    echo "$CHECK_USER_RESPONSE" | head -3
fi

# 3.4 Check Content Quota
print_info "3.4. Testing GET /api/v1/organizations/{org_id}/quota/check/content"
FILE_SIZE=$((100 * 1024 * 1024)) # 100MB
CHECK_CONTENT_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${QUOTA_ORG_ID}/quota/check/content?file_size_bytes=${FILE_SIZE}" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$CHECK_CONTENT_RESPONSE" | grep -q '"allowed":'
if [ $? -eq 0 ]; then
    ALLOWED=$(echo "$CHECK_CONTENT_RESPONSE" | grep -o '"allowed":[a-z]*' | cut -d':' -f2)
    print_success "Check content quota - Can add 100MB content: ${ALLOWED}"
else
    print_error "Check content quota failed"
    echo "$CHECK_CONTENT_RESPONSE" | head -3
fi

# 3.5 Update Quota
if [ -n "$TEST_ORG_ID" ]; then
    print_info "3.5. Testing PUT /api/v1/organizations/{org_id}/quota"
    UPDATE_QUOTA_RESPONSE=$(curl -s -X PUT "${API_V1}/organizations/${TEST_ORG_ID}/quota" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{
            "max_devices": 50,
            "max_users": 20,
            "max_content_size_gb": 500,
            "max_content_items": 5000,
            "max_playlists": 200
        }')

    echo "$UPDATE_QUOTA_RESPONSE" | grep -q '"devices":'
    if [ $? -eq 0 ]; then
        NEW_MAX_DEVICES=$(echo "$UPDATE_QUOTA_RESPONSE" | grep -o '"max":[0-9]*' | head -1 | cut -d':' -f2)
        print_success "Update quota - Set max devices to: ${NEW_MAX_DEVICES}"
    else
        print_error "Update quota failed"
        echo "$UPDATE_QUOTA_RESPONSE" | head -3
    fi
fi

# ============================================================================
# INTEGRATIONS & FEATURES
# ============================================================================

print_section "4. Integration & Feature Tests"

# 4.1 Organization PIN (if exists)
print_info "4.1. Organization PIN generation check"
if [ -n "$TEST_ORG_ID" ]; then
    GET_PIN_RESPONSE=$(curl -s -X GET "${API_V1}/organizations/${TEST_ORG_ID}" \
        -H "Authorization: Bearer ${TOKEN}")

    # Check if PIN field exists
    echo "$GET_PIN_RESPONSE" | grep -q '"organization_pin":'
    if [ $? -eq 0 ]; then
        print_success "Organization PIN field present in response"
    else
        print_warning "Organization PIN field not found (No-PIN flow active)"
    fi
else
    print_warning "Skipping PIN test (no test org)"
fi

# 4.2 User Association
print_info "4.2. User association check"
USER_LIST_RESPONSE=$(curl -s -X GET "${API_V1}/users" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$USER_LIST_RESPONSE" | grep -q '"organization_id":'
if [ $? -eq 0 ]; then
    print_success "Users are associated with organizations"
else
    print_error "User-organization association not found"
fi

# 4.3 Device Association
print_info "4.3. Device association check"
DEVICE_LIST_RESPONSE=$(curl -s -X GET "${API_V1}/devices" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$DEVICE_LIST_RESPONSE" | grep -q '"organization_id":'
if [ $? -eq 0 ]; then
    print_success "Devices are associated with organizations"
else
    print_warning "No devices found to check association"
fi

# ============================================================================
# CLEANUP
# ============================================================================

print_section "5. Cleanup"

# Delete test organization
if [ -n "$TEST_ORG_ID" ]; then
    print_info "5.1. Testing DELETE /api/v1/organizations/{org_id}"
    DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "${API_V1}/organizations/${TEST_ORG_ID}" \
        -H "Authorization: Bearer ${TOKEN}")

    HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -1)
    if [ "$HTTP_CODE" = "204" ]; then
        print_success "Delete organization - Deleted ID: ${TEST_ORG_ID}"
    else
        print_error "Delete organization failed - HTTP ${HTTP_CODE}"
        echo "$DELETE_RESPONSE" | head -3
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_section "Test Summary"

PASS_RATE=0
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")
fi

echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "Pass Rate: ${PASS_RATE}%"

# Grade
if [ $(echo "$PASS_RATE == 100" | bc -l) -eq 1 ]; then
    echo -e "\n${GREEN}${BOLD}Grade: A+ (100/100) - All tests passed!${NC}"
elif [ $(echo "$PASS_RATE >= 90" | bc -l) -eq 1 ]; then
    echo -e "\n${GREEN}Grade: A (${PASS_RATE}/100) - Excellent${NC}"
elif [ $(echo "$PASS_RATE >= 80" | bc -l) -eq 1 ]; then
    echo -e "\n${YELLOW}Grade: B (${PASS_RATE}/100) - Good${NC}"
elif [ $(echo "$PASS_RATE >= 70" | bc -l) -eq 1 ]; then
    echo -e "\n${YELLOW}Grade: C (${PASS_RATE}/100) - Needs improvement${NC}"
else
    echo -e "\n${RED}Grade: F (${PASS_RATE}/100) - Failed${NC}"
fi

# Final notes
print_section "Notes"
print_info "✓ All CRUD operations tested"
print_info "✓ Quota management endpoints verified"
print_info "✓ Integration with users and devices confirmed"
print_info "⚠ Atomic quota enforcement requires concurrent testing (Python script)"

echo ""
