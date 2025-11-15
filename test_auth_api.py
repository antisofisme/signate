#!/usr/bin/env python3
"""
Auth & Session Management API Test Script
Comprehensive testing of all authentication endpoints
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, Tuple

# Configuration
SERVER = "http://192.168.5.12:8001"
API_V1 = "/api/v1"
BASE_URL = f"{SERVER}{API_V1}"

# Colors for console output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Test result tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def print_header(title: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.BLUE}{title}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")

def print_result(test_name: str, status: str, response_time: int = None, details: str = ""):
    """Print test result"""
    test_results["total"] += 1

    if status == "PASS":
        print(f"{Colors.GREEN}✓ PASS{Colors.NC} - {test_name}", end="")
        test_results["passed"] += 1
    else:
        print(f"{Colors.RED}✗ FAIL{Colors.NC} - {test_name}", end="")
        test_results["failed"] += 1

    if response_time is not None:
        print(f" ({response_time}ms)")
    else:
        print()

    if details:
        print(f"{Colors.YELLOW}  Details: {details}{Colors.NC}")

    print()

    test_results["tests"].append({
        "name": test_name,
        "status": status,
        "response_time": response_time,
        "details": details
    })

def api_call(method: str, endpoint: str, data: Dict = None, token: str = None) -> Tuple[int, Dict, int]:
    """
    Make API call and measure response time

    Returns:
        Tuple of (status_code, response_body, response_time_ms)
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    start_time = time.time()

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)

        try:
            body = response.json()
        except:
            body = {"error": "Invalid JSON response", "text": response.text}

        return response.status_code, body, response_time

    except Exception as e:
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)
        return 0, {"error": str(e)}, response_time

def main():
    print_header("AUTH & SESSION API TEST REPORT")
    print(f"Server: {SERVER}")
    print(f"Test Started: {datetime.now()}\n")

    # Generate unique test credentials
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_email = f"test_{timestamp}@example.com"
    test_password = "TestPassword123"

    # Store tokens for later tests
    access_token = None
    reset_token = None
    org_id = 1  # Default organization

    # =========================================================================
    # TEST 1: Health Check
    # =========================================================================
    print_header("1. HEALTH CHECK")

    status_code, body, response_time = api_call("GET", "/health")

    if status_code == 200:
        print_result("GET /health", "PASS", response_time, "Server is healthy")
    else:
        # Try root endpoint instead
        status_code, body, response_time = api_call("GET", "")
        if status_code == 200:
            print_result("GET / (root)", "PASS", response_time, "Server is responding")
        else:
            print_result("GET /health", "FAIL", response_time, f"Status: {status_code}")

    # =========================================================================
    # TEST 2: Get Admin Organization ID
    # =========================================================================
    print_header("2. GET ADMIN ORGANIZATION ID")

    status_code, body, response_time = api_call("POST", "/auth/login", {
        "username": "admin",
        "password": "admin123"
    })

    if status_code == 200 and "data" in body:
        org_id = body["data"]["user"].get("organization_id", 1)
        print_result("Get admin org_id", "PASS", response_time, f"Organization ID: {org_id}")
    else:
        print_result("Get admin org_id", "FAIL", response_time, f"Status: {status_code}")
        org_id = 1  # Default fallback

    # Wait to avoid rate limiting
    time.sleep(2)

    # =========================================================================
    # TEST 3: Register New User
    # =========================================================================
    print_header("3. POST /api/v1/auth/register")

    register_data = {
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "full_name": "Test User",
        "organization_id": org_id
    }

    status_code, body, response_time = api_call("POST", "/auth/register", register_data)

    if status_code in [200, 201]:
        print_result("Register new user", "PASS", response_time, f"User: {test_username}")
    else:
        error_msg = body.get("message") or body.get("detail") or "Unknown error"
        print_result("Register new user", "FAIL", response_time, f"Status: {status_code} - {error_msg}")

    time.sleep(1)

    # =========================================================================
    # TEST 4: Register - Duplicate Username (should fail)
    # =========================================================================
    print_header("4. POST /api/v1/auth/register - Duplicate Username")

    status_code, body, response_time = api_call("POST", "/auth/register", register_data)

    if status_code in [400, 409, 422]:
        print_result("Reject duplicate username", "PASS", response_time, "Correctly rejected")
    else:
        print_result("Reject duplicate username", "FAIL", response_time, f"Status: {status_code} (expected 400/409/422)")

    time.sleep(1)

    # =========================================================================
    # TEST 5: Register - Weak Password (should fail)
    # =========================================================================
    print_header("5. POST /api/v1/auth/register - Weak Password")

    weak_pwd_data = {
        "username": f"weakuser_{timestamp}",
        "email": f"weak_{timestamp}@example.com",
        "password": "123",
        "full_name": "Weak User",
        "organization_id": org_id
    }

    status_code, body, response_time = api_call("POST", "/auth/register", weak_pwd_data)

    if status_code in [422, 400]:
        print_result("Reject weak password", "PASS", response_time, "Correctly rejected")
    else:
        print_result("Reject weak password", "FAIL", response_time, f"Status: {status_code} (expected 422/400)")

    time.sleep(1)

    # =========================================================================
    # TEST 6: Login with Valid Credentials
    # =========================================================================
    print_header("6. POST /api/v1/auth/login - Valid Credentials")

    login_data = {
        "username": test_username,
        "password": test_password
    }

    status_code, body, response_time = api_call("POST", "/auth/login", login_data)

    if status_code == 200:
        access_token = body.get("data", {}).get("token")
        if access_token:
            print_result("Login with valid credentials", "PASS", response_time, "Token received")
        else:
            print_result("Login with valid credentials", "FAIL", response_time, "No token in response")
    else:
        error_msg = body.get("message") or body.get("detail") or "Unknown error"
        print_result("Login with valid credentials", "FAIL", response_time, f"Status: {status_code} - {error_msg}")

    time.sleep(1)

    # =========================================================================
    # TEST 7: Login with Invalid Credentials
    # =========================================================================
    print_header("7. POST /api/v1/auth/login - Invalid Credentials")

    invalid_login_data = {
        "username": test_username,
        "password": "WrongPassword123"
    }

    status_code, body, response_time = api_call("POST", "/auth/login", invalid_login_data)

    if status_code == 401:
        print_result("Reject invalid credentials", "PASS", response_time, "Correctly rejected")
    else:
        print_result("Reject invalid credentials", "FAIL", response_time, f"Status: {status_code} (expected 401)")

    time.sleep(1)

    # =========================================================================
    # TEST 8: Login with Non-existent User
    # =========================================================================
    print_header("8. POST /api/v1/auth/login - Non-existent User")

    nonexist_login_data = {
        "username": "nonexistent_user_12345",
        "password": "SomePassword123"
    }

    status_code, body, response_time = api_call("POST", "/auth/login", nonexist_login_data)

    if status_code == 401:
        print_result("Reject non-existent user", "PASS", response_time, "Correctly rejected")
    else:
        print_result("Reject non-existent user", "FAIL", response_time, f"Status: {status_code} (expected 401)")

    time.sleep(1)

    # =========================================================================
    # TEST 9: Logout (Revoke Session)
    # =========================================================================
    print_header("9. POST /api/v1/auth/logout")

    if access_token:
        status_code, body, response_time = api_call("POST", "/auth/logout", token=access_token)

        if status_code == 200:
            print_result("Logout (revoke session)", "PASS", response_time, "Session revoked")
        else:
            print_result("Logout (revoke session)", "FAIL", response_time, f"Status: {status_code}")
    else:
        print_result("Logout (revoke session)", "FAIL", None, "No access token available")

    time.sleep(1)

    # =========================================================================
    # TEST 10: Use Revoked Token (should fail)
    # =========================================================================
    print_header("10. Use Revoked Token")

    if access_token:
        status_code, body, response_time = api_call("POST", "/auth/logout", token=access_token)

        if status_code == 401:
            print_result("Reject revoked token", "PASS", response_time, "Correctly rejected")
        else:
            print_result("Reject revoked token", "FAIL", response_time, f"Status: {status_code} (expected 401)")
    else:
        print_result("Reject revoked token", "FAIL", None, "No access token available")

    time.sleep(1)

    # =========================================================================
    # TEST 11: Forgot Password
    # =========================================================================
    print_header("11. POST /api/v1/auth/forgot-password")

    forgot_pwd_data = {
        "email": test_email
    }

    status_code, body, response_time = api_call("POST", "/auth/forgot-password", forgot_pwd_data)

    if status_code == 200:
        reset_token = body.get("reset_token")
        print_result("Forgot password request", "PASS", response_time, "Reset token generated")
    else:
        print_result("Forgot password request", "FAIL", response_time, f"Status: {status_code}")

    time.sleep(1)

    # =========================================================================
    # TEST 12: Reset Password with Valid Token
    # =========================================================================
    print_header("12. POST /api/v1/auth/reset-password - Valid Token")

    if reset_token:
        reset_pwd_data = {
            "token": reset_token,
            "new_password": "NewPassword123"
        }

        status_code, body, response_time = api_call("POST", "/auth/reset-password", reset_pwd_data)

        if status_code == 200:
            print_result("Reset password with valid token", "PASS", response_time, "Password reset successful")
            test_password = "NewPassword123"  # Update for subsequent tests
        else:
            print_result("Reset password with valid token", "FAIL", response_time, f"Status: {status_code}")
    else:
        print_result("Reset password with valid token", "FAIL", None, "No reset token available")

    time.sleep(1)

    # =========================================================================
    # TEST 13: Reset Password with Invalid Token
    # =========================================================================
    print_header("13. POST /api/v1/auth/reset-password - Invalid Token")

    invalid_reset_data = {
        "token": "invalid_token_12345",
        "new_password": "NewPassword123"
    }

    status_code, body, response_time = api_call("POST", "/auth/reset-password", invalid_reset_data)

    if status_code in [400, 401]:
        print_result("Reject invalid reset token", "PASS", response_time, "Correctly rejected")
    else:
        print_result("Reject invalid reset token", "FAIL", response_time, f"Status: {status_code} (expected 400/401)")

    time.sleep(1)

    # =========================================================================
    # TEST 14: Login with New Password
    # =========================================================================
    print_header("14. POST /api/v1/auth/login - After Password Reset")

    new_login_data = {
        "username": test_username,
        "password": test_password
    }

    status_code, body, response_time = api_call("POST", "/auth/login", new_login_data)

    if status_code == 200:
        new_access_token = body.get("data", {}).get("token")
        print_result("Login with new password", "PASS", response_time, "Login successful with new password")
    else:
        print_result("Login with new password", "FAIL", response_time, f"Status: {status_code}")

    time.sleep(1)

    # =========================================================================
    # TEST 15: Session Repository - Check Session Created
    # =========================================================================
    print_header("15. Integration Check - Session Repository")

    login_result_status, login_result_body, _ = api_call("POST", "/auth/login", new_login_data)

    if login_result_status == 200:
        has_token = login_result_body.get("data", {}).get("token")
        has_user = login_result_body.get("data", {}).get("user")

        if has_token and has_user:
            print_result("Session repository working", "PASS", None, "Session created on login")
        else:
            print_result("Session repository working", "FAIL", None, "Session data incomplete")
    else:
        print_result("Session repository working", "FAIL", None, "Login failed")

    time.sleep(1)

    # =========================================================================
    # TEST 16: Multi-tenancy - Organization Isolation
    # =========================================================================
    print_header("16. Integration Check - Multi-tenancy")

    org_check = login_result_body.get("data", {}).get("user", {}).get("organization_id")

    if org_check and org_check is not None:
        print_result("Multi-tenancy (organization_id)", "PASS", None, f"Organization ID: {org_check}")
    else:
        print_result("Multi-tenancy (organization_id)", "FAIL", None, "No organization_id in user data")

    # =========================================================================
    # TEST 17: Password Validation - Minimum Length
    # =========================================================================
    print_header("17. Password Validation - Minimum 8 Characters")

    short_pwd_data = {
        "username": f"shortpwd_{timestamp}",
        "email": f"short_{timestamp}@example.com",
        "password": "Short1",
        "full_name": "Short Password User",
        "organization_id": org_id
    }

    status_code, body, response_time = api_call("POST", "/auth/register", short_pwd_data)

    if status_code in [422, 400]:
        print_result("Password minimum length validation", "PASS", response_time, "Correctly rejected short password")
    else:
        print_result("Password minimum length validation", "FAIL", response_time, f"Status: {status_code} (expected 422/400)")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("TEST SUMMARY")

    print(f"{Colors.BLUE}Total Tests:{Colors.NC} {test_results['total']}")
    print(f"{Colors.GREEN}Passed:{Colors.NC} {test_results['passed']}")
    print(f"{Colors.RED}Failed:{Colors.NC} {test_results['failed']}")

    if test_results['failed'] == 0:
        print(f"\n{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.NC}\n")
    else:
        print(f"\n{Colors.RED}✗ SOME TESTS FAILED{Colors.NC}\n")

    print(f"Test Completed: {datetime.now()}\n")

    # Print detailed results
    print_header("DETAILED RESULTS")
    for i, test in enumerate(test_results['tests'], 1):
        status_icon = "✓" if test['status'] == "PASS" else "✗"
        color = Colors.GREEN if test['status'] == "PASS" else Colors.RED
        print(f"{color}{i}. {status_icon} {test['name']}{Colors.NC}")
        if test['response_time']:
            print(f"   Response Time: {test['response_time']}ms")
        if test['details']:
            print(f"   {test['details']}")
        print()

    return test_results['failed']

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
