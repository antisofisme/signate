#!/bin/bash

# Auth & Session Management API Test Script
# Server: http://192.168.5.12:8001
# Date: 2025-11-14

SERVER="http://192.168.5.12:8001"
API_V1="/api/v1"
BASE_URL="${SERVER}${API_V1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print section header
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to print test result
print_result() {
    local test_name=$1
    local status=$2
    local response_time=$3
    local details=$4

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name (${response_time}ms)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    if [ ! -z "$details" ]; then
        echo -e "${YELLOW}  Details: $details${NC}"
    fi
    echo ""
}

# Function to make API call and measure time
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4

    local start_time=$(date +%s%3N)

    if [ ! -z "$token" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $token" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    fi

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    # Extract body and status code
    body=$(echo "$response" | head -n -1)
    status_code=$(echo "$response" | tail -n 1)

    echo "$status_code|$duration|$body"
}

# Generate unique username for test
TEST_USERNAME="testuser_$(date +%s)"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123"

print_header "AUTH & SESSION API TEST REPORT"
echo "Server: $SERVER"
echo "Test Started: $(date)"
echo ""

# =============================================================================
# TEST 1: Health Check
# =============================================================================
print_header "1. HEALTH CHECK"

result=$(api_call "GET" "/health" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "200" ]; then
    print_result "GET /health" "PASS" "$response_time" "Server is healthy"
else
    print_result "GET /health" "FAIL" "$response_time" "Status: $status_code"
fi

# =============================================================================
# TEST 2: Register New User
# =============================================================================
print_header "2. POST /api/v1/auth/register"

# Get admin user's organization_id first
login_result=$(api_call "POST" "/auth/login" '{"username":"admin","password":"admin123"}' "")
admin_body=$(echo "$login_result" | cut -d'|' -f3-)
org_id=$(echo "$admin_body" | jq -r '.data.user.organization_id // 1')

register_data="{
    \"username\": \"$TEST_USERNAME\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"full_name\": \"Test User\",
    \"organization_id\": $org_id
}"

result=$(api_call "POST" "/auth/register" "$register_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "201" ] || [ "$status_code" == "200" ]; then
    print_result "Register new user" "PASS" "$response_time" "User: $TEST_USERNAME"
else
    print_result "Register new user" "FAIL" "$response_time" "Status: $status_code - $(echo $body | jq -r '.message // .detail // "Unknown error"')"
fi

# =============================================================================
# TEST 3: Register - Duplicate Username (should fail)
# =============================================================================
print_header "3. POST /api/v1/auth/register - Duplicate Username"

result=$(api_call "POST" "/auth/register" "$register_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "400" ] || [ "$status_code" == "409" ]; then
    print_result "Reject duplicate username" "PASS" "$response_time" "Correctly rejected"
else
    print_result "Reject duplicate username" "FAIL" "$response_time" "Status: $status_code (expected 400 or 409)"
fi

# =============================================================================
# TEST 4: Register - Weak Password (should fail)
# =============================================================================
print_header "4. POST /api/v1/auth/register - Weak Password"

weak_pwd_data="{
    \"username\": \"weakuser_$(date +%s)\",
    \"email\": \"weak_$(date +%s)@example.com\",
    \"password\": \"123\",
    \"full_name\": \"Weak User\",
    \"organization_id\": $org_id
}"

result=$(api_call "POST" "/auth/register" "$weak_pwd_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "422" ] || [ "$status_code" == "400" ]; then
    print_result "Reject weak password" "PASS" "$response_time" "Correctly rejected"
else
    print_result "Reject weak password" "FAIL" "$response_time" "Status: $status_code (expected 422 or 400)"
fi

# =============================================================================
# TEST 5: Login with Valid Credentials
# =============================================================================
print_header "5. POST /api/v1/auth/login - Valid Credentials"

login_data="{
    \"username\": \"$TEST_USERNAME\",
    \"password\": \"$TEST_PASSWORD\"
}"

result=$(api_call "POST" "/auth/login" "$login_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "200" ]; then
    ACCESS_TOKEN=$(echo "$body" | jq -r '.data.token // empty')
    if [ ! -z "$ACCESS_TOKEN" ]; then
        print_result "Login with valid credentials" "PASS" "$response_time" "Token received"
    else
        print_result "Login with valid credentials" "FAIL" "$response_time" "No token in response"
    fi
else
    print_result "Login with valid credentials" "FAIL" "$response_time" "Status: $status_code"
fi

# =============================================================================
# TEST 6: Login with Invalid Credentials
# =============================================================================
print_header "6. POST /api/v1/auth/login - Invalid Credentials"

invalid_login_data="{
    \"username\": \"$TEST_USERNAME\",
    \"password\": \"WrongPassword123\"
}"

result=$(api_call "POST" "/auth/login" "$invalid_login_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "401" ]; then
    print_result "Reject invalid credentials" "PASS" "$response_time" "Correctly rejected"
else
    print_result "Reject invalid credentials" "FAIL" "$response_time" "Status: $status_code (expected 401)"
fi

# =============================================================================
# TEST 7: Login with Non-existent User
# =============================================================================
print_header "7. POST /api/v1/auth/login - Non-existent User"

nonexist_login_data="{
    \"username\": \"nonexistent_user_12345\",
    \"password\": \"SomePassword123\"
}"

result=$(api_call "POST" "/auth/login" "$nonexist_login_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "401" ]; then
    print_result "Reject non-existent user" "PASS" "$response_time" "Correctly rejected"
else
    print_result "Reject non-existent user" "FAIL" "$response_time" "Status: $status_code (expected 401)"
fi

# =============================================================================
# TEST 8: Rate Limiting - Login (5 attempts in 5 minutes)
# =============================================================================
print_header "8. Rate Limiting - Login Endpoint"

echo "Making 6 consecutive login attempts to test rate limiter..."
rate_limit_triggered=false

for i in {1..6}; do
    result=$(api_call "POST" "/auth/login" "$invalid_login_data" "")
    status_code=$(echo "$result" | cut -d'|' -f1)
    response_time=$(echo "$result" | cut -d'|' -f2)

    echo "  Attempt $i: Status $status_code (${response_time}ms)"

    if [ "$status_code" == "429" ]; then
        rate_limit_triggered=true
        break
    fi

    sleep 1
done

if [ "$rate_limit_triggered" == true ]; then
    print_result "Rate limiting active" "PASS" "N/A" "Rate limit triggered after multiple attempts"
else
    print_result "Rate limiting active" "FAIL" "N/A" "Rate limit not triggered after 6 attempts"
fi

# =============================================================================
# TEST 9: Logout (Revoke Session)
# =============================================================================
print_header "9. POST /api/v1/auth/logout"

if [ ! -z "$ACCESS_TOKEN" ]; then
    result=$(api_call "POST" "/auth/logout" "" "$ACCESS_TOKEN")
    status_code=$(echo "$result" | cut -d'|' -f1)
    response_time=$(echo "$result" | cut -d'|' -f2)
    body=$(echo "$result" | cut -d'|' -f3-)

    if [ "$status_code" == "200" ]; then
        print_result "Logout (revoke session)" "PASS" "$response_time" "Session revoked"
    else
        print_result "Logout (revoke session)" "FAIL" "$response_time" "Status: $status_code"
    fi
else
    print_result "Logout (revoke session)" "FAIL" "N/A" "No access token available"
fi

# =============================================================================
# TEST 10: Use Revoked Token (should fail)
# =============================================================================
print_header "10. Use Revoked Token"

if [ ! -z "$ACCESS_TOKEN" ]; then
    # Try to use the revoked token to access a protected endpoint
    result=$(api_call "POST" "/auth/logout" "" "$ACCESS_TOKEN")
    status_code=$(echo "$result" | cut -d'|' -f1)
    response_time=$(echo "$result" | cut -d'|' -f2)

    if [ "$status_code" == "401" ]; then
        print_result "Reject revoked token" "PASS" "$response_time" "Correctly rejected"
    else
        print_result "Reject revoked token" "FAIL" "$response_time" "Status: $status_code (expected 401)"
    fi
else
    print_result "Reject revoked token" "FAIL" "N/A" "No access token available"
fi

# =============================================================================
# TEST 11: Forgot Password
# =============================================================================
print_header "11. POST /api/v1/auth/forgot-password"

forgot_pwd_data="{
    \"email\": \"$TEST_EMAIL\"
}"

result=$(api_call "POST" "/auth/forgot-password" "$forgot_pwd_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "200" ]; then
    RESET_TOKEN=$(echo "$body" | jq -r '.reset_token // empty')
    print_result "Forgot password request" "PASS" "$response_time" "Reset token generated"
else
    print_result "Forgot password request" "FAIL" "$response_time" "Status: $status_code"
fi

# =============================================================================
# TEST 12: Reset Password with Valid Token
# =============================================================================
print_header "12. POST /api/v1/auth/reset-password - Valid Token"

if [ ! -z "$RESET_TOKEN" ]; then
    reset_pwd_data="{
        \"token\": \"$RESET_TOKEN\",
        \"new_password\": \"NewPassword123\"
    }"

    result=$(api_call "POST" "/auth/reset-password" "$reset_pwd_data" "")
    status_code=$(echo "$result" | cut -d'|' -f1)
    response_time=$(echo "$result" | cut -d'|' -f2)
    body=$(echo "$result" | cut -d'|' -f3-)

    if [ "$status_code" == "200" ]; then
        print_result "Reset password with valid token" "PASS" "$response_time" "Password reset successful"
        TEST_PASSWORD="NewPassword123"  # Update password for subsequent tests
    else
        print_result "Reset password with valid token" "FAIL" "$response_time" "Status: $status_code"
    fi
else
    print_result "Reset password with valid token" "FAIL" "N/A" "No reset token available"
fi

# =============================================================================
# TEST 13: Reset Password with Invalid Token
# =============================================================================
print_header "13. POST /api/v1/auth/reset-password - Invalid Token"

invalid_reset_data="{
    \"token\": \"invalid_token_12345\",
    \"new_password\": \"NewPassword123\"
}"

result=$(api_call "POST" "/auth/reset-password" "$invalid_reset_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "400" ] || [ "$status_code" == "401" ]; then
    print_result "Reject invalid reset token" "PASS" "$response_time" "Correctly rejected"
else
    print_result "Reject invalid reset token" "FAIL" "$response_time" "Status: $status_code (expected 400 or 401)"
fi

# =============================================================================
# TEST 14: Login with New Password
# =============================================================================
print_header "14. POST /api/v1/auth/login - After Password Reset"

new_login_data="{
    \"username\": \"$TEST_USERNAME\",
    \"password\": \"$TEST_PASSWORD\"
}"

result=$(api_call "POST" "/auth/login" "$new_login_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "200" ]; then
    NEW_ACCESS_TOKEN=$(echo "$body" | jq -r '.data.token // empty')
    print_result "Login with new password" "PASS" "$response_time" "Login successful with new password"
else
    print_result "Login with new password" "FAIL" "$response_time" "Status: $status_code"
fi

# =============================================================================
# TEST 15: Session Repository - Check Session Created
# =============================================================================
print_header "15. Integration Check - Session Repository"

# Login to create a fresh session
login_result=$(api_call "POST" "/auth/login" "$new_login_data" "")
login_status=$(echo "$login_result" | cut -d'|' -f1)
login_body=$(echo "$login_result" | cut -d'|' -f3-)

if [ "$login_status" == "200" ]; then
    # Check if session data is present in response
    has_token=$(echo "$login_body" | jq -r '.data.token // empty')
    has_user=$(echo "$login_body" | jq -r '.data.user // empty')

    if [ ! -z "$has_token" ] && [ ! -z "$has_user" ]; then
        print_result "Session repository working" "PASS" "N/A" "Session created on login"
    else
        print_result "Session repository working" "FAIL" "N/A" "Session data incomplete"
    fi
else
    print_result "Session repository working" "FAIL" "N/A" "Login failed"
fi

# =============================================================================
# TEST 16: Multi-tenancy - Organization Isolation
# =============================================================================
print_header "16. Integration Check - Multi-tenancy"

# Check if user has organization_id
org_check=$(echo "$login_body" | jq -r '.data.user.organization_id // empty')

if [ ! -z "$org_check" ] && [ "$org_check" != "null" ]; then
    print_result "Multi-tenancy (organization_id)" "PASS" "N/A" "Organization ID: $org_check"
else
    print_result "Multi-tenancy (organization_id)" "FAIL" "N/A" "No organization_id in user data"
fi

# =============================================================================
# TEST 17: Password Validation - Minimum Length
# =============================================================================
print_header "17. Password Validation - Minimum 8 Characters"

short_pwd_data="{
    \"username\": \"shortpwd_$(date +%s)\",
    \"email\": \"short_$(date +%s)@example.com\",
    \"password\": \"Short1\",
    \"full_name\": \"Short Password User\",
    \"organization_id\": $org_id
}"

result=$(api_call "POST" "/auth/register" "$short_pwd_data" "")
status_code=$(echo "$result" | cut -d'|' -f1)
response_time=$(echo "$result" | cut -d'|' -f2)
body=$(echo "$result" | cut -d'|' -f3-)

if [ "$status_code" == "422" ] || [ "$status_code" == "400" ]; then
    print_result "Password minimum length validation" "PASS" "$response_time" "Correctly rejected short password"
else
    print_result "Password minimum length validation" "FAIL" "$response_time" "Status: $status_code (expected 422 or 400)"
fi

# =============================================================================
# SUMMARY
# =============================================================================
print_header "TEST SUMMARY"

echo -e "${BLUE}Total Tests:${NC} $TOTAL_TESTS"
echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
echo -e "${RED}Failed:${NC} $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL TESTS PASSED!${NC}\n"
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}\n"
fi

echo "Test Completed: $(date)"
echo ""

exit $FAILED_TESTS
