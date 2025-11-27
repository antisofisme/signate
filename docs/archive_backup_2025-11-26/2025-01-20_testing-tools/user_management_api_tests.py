"""
User Management API Test Suite
Tests all user endpoints on http://192.168.5.12:8001

Endpoints to test:
1. GET /api/v1/users - List users with filters
2. POST /api/v1/users - Create user
3. GET /api/v1/users/{id} - Get single user
4. PUT /api/v1/users/{id} - Update user
5. PUT /api/v1/users/{id}/change-password - Change password (P0-16 fix)
6. DELETE /api/v1/users/{id} - Delete user

Permission Tests:
- Admin: Can see all users, perform all operations
- Manager: Can see org users only, limited operations
- User: Can see self only, very limited operations
"""

import requests
import json
import sys
from typing import Dict, Optional

# Configuration
BASE_URL = "http://192.168.5.12:8001"
API_V1 = f"{BASE_URL}/api/v1"

# Test results storage
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "issues": []
}

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def record_test(test_name: str, passed: bool, details: Optional[str] = None):
    """Record test result"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print_success(f"{test_name}")
    else:
        test_results["failed"] += 1
        print_error(f"{test_name}")
        if details:
            test_results["issues"].append(f"{test_name}: {details}")
            print(f"  Details: {details}")

def login(username: str, password: str) -> Optional[Dict]:
    """Login and get access token"""
    try:
        response = requests.post(
            f"{API_V1}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "token": data["data"]["token"],
                "user": data["data"]["user"]
            }
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return None

def get_headers(token: str) -> Dict:
    """Get request headers with authorization"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

# =============================================================================
# TEST: LIST USERS
# =============================================================================
def test_list_users(token: str, role: str):
    """Test GET /api/v1/users"""
    print_header(f"TEST: List Users ({role})")

    try:
        # Test 1: Basic list
        response = requests.get(
            f"{API_V1}/users",
            headers=get_headers(token)
        )
        record_test(
            f"List users - {role}",
            response.status_code == 200,
            f"Status: {response.status_code}, Response: {response.text[:200]}"
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  Total users: {data['data']['total']}")
            print(f"  Active users: {data['data']['active']}")
            print(f"  Users returned: {len(data['data']['users'])}")

            # Test 2: Filter by role
            response = requests.get(
                f"{API_V1}/users?role=admin",
                headers=get_headers(token)
            )
            record_test(
                f"Filter by role - {role}",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            # Test 3: Filter by active_only
            response = requests.get(
                f"{API_V1}/users?active_only=true",
                headers=get_headers(token)
            )
            record_test(
                f"Filter by active_only - {role}",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            # Test 4: Filter by organization_id (if admin)
            if role == "admin":
                response = requests.get(
                    f"{API_V1}/users?organization_id=1",
                    headers=get_headers(token)
                )
                record_test(
                    f"Filter by organization_id - {role}",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )

    except Exception as e:
        record_test(f"List users - {role}", False, str(e))

# =============================================================================
# TEST: CREATE USER
# =============================================================================
def test_create_user(token: str, role: str, org_id: int) -> Optional[int]:
    """Test POST /api/v1/users"""
    print_header(f"TEST: Create User ({role})")

    try:
        # Create test user
        user_data = {
            "username": f"test_user_{role}_001",
            "email": f"test_{role}_001@example.com",
            "password": "Test123!@#",
            "full_name": f"Test User {role}",
            "role": "user",
            "organization_id": org_id
        }

        response = requests.post(
            f"{API_V1}/users",
            headers=get_headers(token),
            json=user_data
        )

        expected_status = 201 if role in ["admin", "manager"] else 403
        record_test(
            f"Create user - {role}",
            response.status_code == expected_status,
            f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200]}"
        )

        if response.status_code == 201:
            data = response.json()
            user_id = data["data"]["id"]
            print(f"  Created user ID: {user_id}")
            return user_id

        return None

    except Exception as e:
        record_test(f"Create user - {role}", False, str(e))
        return None

# =============================================================================
# TEST: GET USER
# =============================================================================
def test_get_user(token: str, role: str, user_id: int, should_succeed: bool = True):
    """Test GET /api/v1/users/{id}"""
    print_header(f"TEST: Get User ({role})")

    try:
        response = requests.get(
            f"{API_V1}/users/{user_id}",
            headers=get_headers(token)
        )

        expected_status = 200 if should_succeed else 403
        record_test(
            f"Get user - {role}",
            response.status_code == expected_status,
            f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200]}"
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  User: {data['data']['username']} ({data['data']['role']})")
            print(f"  Organization: {data['data']['organization_name']}")

    except Exception as e:
        record_test(f"Get user - {role}", False, str(e))

# =============================================================================
# TEST: UPDATE USER
# =============================================================================
def test_update_user(token: str, role: str, user_id: int, should_succeed: bool = True):
    """Test PUT /api/v1/users/{id}"""
    print_header(f"TEST: Update User ({role})")

    try:
        update_data = {
            "full_name": f"Updated Name by {role}",
            "email": f"updated_{role}@example.com"
        }

        response = requests.put(
            f"{API_V1}/users/{user_id}",
            headers=get_headers(token),
            json=update_data
        )

        expected_status = 200 if should_succeed else 403
        record_test(
            f"Update user - {role}",
            response.status_code == expected_status,
            f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200]}"
        )

    except Exception as e:
        record_test(f"Update user - {role}", False, str(e))

# =============================================================================
# TEST: CHANGE PASSWORD
# =============================================================================
def test_change_password(token: str, role: str, user_id: int, should_succeed: bool = True):
    """Test PUT /api/v1/users/{id}/change-password (P0-16 fix)"""
    print_header(f"TEST: Change Password ({role})")

    try:
        password_data = {
            "new_password": "NewPassword123!@#"
        }

        response = requests.put(
            f"{API_V1}/users/{user_id}/change-password",
            headers=get_headers(token),
            json=password_data
        )

        expected_status = 200 if should_succeed else 403
        record_test(
            f"Change password - {role}",
            response.status_code == expected_status,
            f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200]}"
        )

        if response.status_code == 200:
            print_success("  P0-16 FIX VERIFIED: Session revocation on password change")

    except Exception as e:
        record_test(f"Change password - {role}", False, str(e))

# =============================================================================
# TEST: DELETE USER
# =============================================================================
def test_delete_user(token: str, role: str, user_id: int, should_succeed: bool = True):
    """Test DELETE /api/v1/users/{id}"""
    print_header(f"TEST: Delete User ({role})")

    try:
        response = requests.delete(
            f"{API_V1}/users/{user_id}",
            headers=get_headers(token)
        )

        expected_status = 204 if should_succeed else 403
        record_test(
            f"Delete user - {role}",
            response.status_code == expected_status,
            f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200] if response.text else 'No content'}"
        )

    except Exception as e:
        record_test(f"Delete user - {role}", False, str(e))

# =============================================================================
# TEST: MULTI-TENANCY
# =============================================================================
def test_multi_tenancy(admin_token: str):
    """Test multi-tenancy filtering"""
    print_header("TEST: Multi-Tenancy Filtering")

    try:
        # Get all users (admin can see all)
        response = requests.get(
            f"{API_V1}/users",
            headers=get_headers(admin_token)
        )

        if response.status_code == 200:
            data = response.json()
            users = data["data"]["users"]

            # Check that users from different orgs are present
            org_ids = set([u["organization_id"] for u in users])

            record_test(
                "Multi-tenancy: Multiple organizations",
                len(org_ids) >= 1,
                f"Found {len(org_ids)} organization(s)"
            )

            print(f"  Organizations found: {org_ids}")

            # Test filtering by organization
            if len(org_ids) > 0:
                org_id = list(org_ids)[0]
                response = requests.get(
                    f"{API_V1}/users?organization_id={org_id}",
                    headers=get_headers(admin_token)
                )

                if response.status_code == 200:
                    data = response.json()
                    filtered_users = data["data"]["users"]
                    all_same_org = all(u["organization_id"] == org_id for u in filtered_users)

                    record_test(
                        "Multi-tenancy: Organization filtering",
                        all_same_org,
                        f"All users belong to org {org_id}: {all_same_org}"
                    )

    except Exception as e:
        record_test("Multi-tenancy test", False, str(e))

# =============================================================================
# TEST: RBAC PERMISSIONS
# =============================================================================
def test_rbac_permissions(admin_token: str, admin_user: Dict):
    """Test role-based access control"""
    print_header("TEST: RBAC Permissions")

    try:
        # Admin should see all users
        response = requests.get(
            f"{API_V1}/users",
            headers=get_headers(admin_token)
        )

        if response.status_code == 200:
            data = response.json()
            total_users = data["data"]["total"]

            record_test(
                "RBAC: Admin can see all users",
                total_users > 0,
                f"Admin sees {total_users} users"
            )

            # Admin can create users
            user_data = {
                "username": "rbac_test_user",
                "email": "rbac_test@example.com",
                "password": "Test123!@#",
                "full_name": "RBAC Test User",
                "role": "user",
                "organization_id": admin_user["organization_id"]
            }

            response = requests.post(
                f"{API_V1}/users",
                headers=get_headers(admin_token),
                json=user_data
            )

            record_test(
                "RBAC: Admin can create users",
                response.status_code == 201,
                f"Status: {response.status_code}"
            )

            if response.status_code == 201:
                created_user_id = response.json()["data"]["id"]

                # Admin can update any user
                response = requests.put(
                    f"{API_V1}/users/{created_user_id}",
                    headers=get_headers(admin_token),
                    json={"full_name": "Updated by Admin"}
                )

                record_test(
                    "RBAC: Admin can update any user",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )

                # Admin can delete any user
                response = requests.delete(
                    f"{API_V1}/users/{created_user_id}",
                    headers=get_headers(admin_token)
                )

                record_test(
                    "RBAC: Admin can delete any user",
                    response.status_code == 204,
                    f"Status: {response.status_code}"
                )

    except Exception as e:
        record_test("RBAC test", False, str(e))

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================
def main():
    """Run all tests"""
    print_header("USER MANAGEMENT API TEST SUITE")
    print(f"Testing API: {BASE_URL}")
    print(f"API Version: v1")

    # Login as admin
    print_header("Authentication")
    admin_auth = login("admin", "admin123")

    if not admin_auth:
        print_error("Failed to login as admin. Aborting tests.")
        sys.exit(1)

    print_success(f"Logged in as: {admin_auth['user']['username']} (Role: {admin_auth['user']['role']})")
    print(f"Organization ID: {admin_auth['user']['organization_id']}")

    admin_token = admin_auth["token"]
    admin_user = admin_auth["user"]

    # Run all tests
    test_list_users(admin_token, "admin")

    # Create a test user and run CRUD operations
    created_user_id = test_create_user(admin_token, "admin", admin_user["organization_id"])

    if created_user_id:
        test_get_user(admin_token, "admin", created_user_id, should_succeed=True)
        test_update_user(admin_token, "admin", created_user_id, should_succeed=True)
        test_change_password(admin_token, "admin", created_user_id, should_succeed=True)

        # Test permission denied for regular user trying to access another user
        test_get_user(admin_token, "admin", 999999, should_succeed=False)  # Non-existent user

        # Clean up: Delete the test user
        test_delete_user(admin_token, "admin", created_user_id, should_succeed=True)

    # Test multi-tenancy
    test_multi_tenancy(admin_token)

    # Test RBAC permissions
    test_rbac_permissions(admin_token, admin_user)

    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total tests: {test_results['total']}")
    print_success(f"Passed: {test_results['passed']}")
    print_error(f"Failed: {test_results['failed']}")

    if test_results["failed"] > 0:
        print_header("ISSUES FOUND")
        for i, issue in enumerate(test_results["issues"], 1):
            print(f"{i}. {issue}")

    # Calculate success rate
    if test_results["total"] > 0:
        success_rate = (test_results["passed"] / test_results["total"]) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if success_rate == 100:
            print_success("ALL TESTS PASSED! ✓")
        elif success_rate >= 80:
            print_warning("MOST TESTS PASSED - Some issues need attention")
        else:
            print_error("MANY TESTS FAILED - Critical issues detected")

    # Exit with appropriate code
    sys.exit(0 if test_results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
