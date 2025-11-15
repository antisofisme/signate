#!/usr/bin/env python3
"""
Organization Management API Test Suite
Tests all organization endpoints including CRUD, quota management, and atomic operations
"""

import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "http://192.168.5.12:8001"
API_V1 = f"{BASE_URL}/api/v1"

# Test credentials
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

# ANSI Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}")
    print(f"{title}")
    print(f"{'='*80}{Colors.RESET}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


class OrganizationAPITester:
    """Test suite for Organization Management API"""

    def __init__(self):
        self.base_url = BASE_URL
        self.api_v1 = API_V1
        self.token = None
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.test_org_id = None

    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        print_section("Authentication")

        try:
            response = requests.post(
                f"{self.api_v1}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success") and "data" in result:
                    data = result["data"]
                    self.token = data.get("token")
                    print_success(f"Authenticated as {ADMIN_CREDENTIALS['username']}")
                    print_info(f"Token: {self.token[:50]}...")
                    return True
                else:
                    print_error("Unexpected response format")
                    print_error(f"Response: {result}")
                    return False
            else:
                print_error(f"Authentication failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False

        except Exception as e:
            print_error(f"Authentication error: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def record_result(self, test_name: str, passed: bool, error: str = None):
        """Record test result"""
        self.results["total"] += 1
        if passed:
            self.results["passed"] += 1
            print_success(test_name)
        else:
            self.results["failed"] += 1
            print_error(f"{test_name}: {error}")
            self.results["errors"].append({"test": test_name, "error": error})

    # =========================================================================
    # CRUD TESTS
    # =========================================================================

    def test_list_organizations(self) -> bool:
        """Test GET /api/v1/organizations"""
        print_section("Test: List Organizations")

        try:
            response = requests.get(
                f"{self.api_v1}/organizations",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                orgs = data.get("organizations", [])
                total = data.get("total", 0)
                active = data.get("active", 0)

                print_info(f"Total organizations: {total}")
                print_info(f"Active organizations: {active}")

                for org in orgs[:3]:  # Show first 3
                    print_info(f"  - {org['name']} (ID: {org['id']}, Active: {org['is_active']})")

                self.record_result("List Organizations", True)
                return True
            else:
                self.record_result("List Organizations", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("List Organizations", False, str(e))
            return False

    def test_create_organization(self) -> bool:
        """Test POST /api/v1/organizations"""
        print_section("Test: Create Organization")

        org_data = {
            "name": f"Test Organization {int(time.time())}",
            "description": "Created by automated test",
            "address": "123 Test Street",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890"
        }

        try:
            response = requests.post(
                f"{self.api_v1}/organizations",
                headers=self.get_headers(),
                json=org_data,
                timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                self.test_org_id = data.get("id")

                print_info(f"Created organization ID: {self.test_org_id}")
                print_info(f"Name: {data.get('name')}")
                print_info(f"Organization PIN: {data.get('organization_pin', 'N/A')}")

                self.record_result("Create Organization", True)
                return True
            else:
                self.record_result("Create Organization", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Create Organization", False, str(e))
            return False

    def test_get_organization(self) -> bool:
        """Test GET /api/v1/organizations/{org_id}"""
        print_section("Test: Get Organization")

        if not self.test_org_id:
            print_warning("No test organization ID available, skipping")
            return False

        try:
            response = requests.get(
                f"{self.api_v1}/organizations/{self.test_org_id}",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                print_info(f"Organization: {data.get('name')}")
                print_info(f"Active: {data.get('is_active')}")
                print_info(f"User count: {data.get('user_count', 0)}")
                print_info(f"Device count: {data.get('device_count', 0)}")

                self.record_result("Get Organization", True)
                return True
            else:
                self.record_result("Get Organization", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Get Organization", False, str(e))
            return False

    def test_update_organization(self) -> bool:
        """Test PUT /api/v1/organizations/{org_id}"""
        print_section("Test: Update Organization")

        if not self.test_org_id:
            print_warning("No test organization ID available, skipping")
            return False

        update_data = {
            "name": f"Updated Test Organization {int(time.time())}",
            "description": "Updated by automated test",
            "address": "456 Updated Street",
            "contact_email": "updated@example.com",
            "contact_phone": "+9876543210",
            "is_active": True
        }

        try:
            response = requests.put(
                f"{self.api_v1}/organizations/{self.test_org_id}",
                headers=self.get_headers(),
                json=update_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                print_info(f"Updated organization: {data.get('name')}")
                print_info(f"New description: {data.get('description')}")

                self.record_result("Update Organization", True)
                return True
            else:
                self.record_result("Update Organization", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Update Organization", False, str(e))
            return False

    # =========================================================================
    # QUOTA TESTS
    # =========================================================================

    def test_get_quota(self) -> bool:
        """Test GET /api/v1/organizations/{org_id}/quota"""
        print_section("Test: Get Organization Quota")

        if not self.test_org_id:
            print_warning("No test organization ID available, using ID 1")
            org_id = 1
        else:
            org_id = self.test_org_id

        try:
            response = requests.get(
                f"{self.api_v1}/organizations/{org_id}/quota",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # Devices
                devices = data.get("devices", {})
                print_info(f"Devices: {devices.get('current')}/{devices.get('max')} ({devices.get('available')} available)")

                # Users
                users = data.get("users", {})
                print_info(f"Users: {users.get('current')}/{users.get('max')} ({users.get('available')} available)")

                # Content
                content = data.get("content", {})
                print_info(f"Content Items: {content.get('current_items')}/{content.get('max_items')}")
                print_info(f"Storage: {content.get('current_size_gb'):.2f}GB/{content.get('max_size_gb')}GB")

                # Playlists
                playlists = data.get("playlists", {})
                print_info(f"Playlists: {playlists.get('current')}/{playlists.get('max')}")

                # Warnings
                warnings = data.get("warnings", [])
                if warnings:
                    for warning in warnings:
                        print_warning(warning)

                self.record_result("Get Quota", True)
                return True
            else:
                self.record_result("Get Quota", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Get Quota", False, str(e))
            return False

    def test_check_device_quota(self) -> bool:
        """Test GET /api/v1/organizations/{org_id}/quota/check/device"""
        print_section("Test: Check Device Quota")

        org_id = self.test_org_id or 1

        try:
            response = requests.get(
                f"{self.api_v1}/organizations/{org_id}/quota/check/device",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                allowed = data.get("allowed", False)
                quota = data.get("quota", {})
                message = data.get("message")

                print_info(f"Can add device: {allowed}")
                print_info(f"Quota: {quota.get('current')}/{quota.get('max')}")

                if message:
                    print_warning(message)

                self.record_result("Check Device Quota", True)
                return True
            else:
                self.record_result("Check Device Quota", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Check Device Quota", False, str(e))
            return False

    def test_check_user_quota(self) -> bool:
        """Test GET /api/v1/organizations/{org_id}/quota/check/user"""
        print_section("Test: Check User Quota")

        org_id = self.test_org_id or 1

        try:
            response = requests.get(
                f"{self.api_v1}/organizations/{org_id}/quota/check/user",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                allowed = data.get("allowed", False)
                quota = data.get("quota", {})
                message = data.get("message")

                print_info(f"Can add user: {allowed}")
                print_info(f"Quota: {quota.get('current')}/{quota.get('max')}")

                if message:
                    print_warning(message)

                self.record_result("Check User Quota", True)
                return True
            else:
                self.record_result("Check User Quota", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Check User Quota", False, str(e))
            return False

    def test_check_content_quota(self) -> bool:
        """Test GET /api/v1/organizations/{org_id}/quota/check/content"""
        print_section("Test: Check Content Quota")

        org_id = self.test_org_id or 1
        file_size = 1024 * 1024 * 100  # 100MB

        try:
            response = requests.get(
                f"{self.api_v1}/organizations/{org_id}/quota/check/content",
                headers=self.get_headers(),
                params={"file_size_bytes": file_size},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                allowed = data.get("allowed", False)
                quota = data.get("quota", {})
                message = data.get("message")

                print_info(f"Can add content (100MB): {allowed}")
                print_info(f"Items: {quota.get('current_items')}/{quota.get('max_items')}")
                print_info(f"Storage: {quota.get('current_size_gb'):.2f}GB/{quota.get('max_size_gb')}GB")

                if message:
                    print_warning(message)

                self.record_result("Check Content Quota", True)
                return True
            else:
                self.record_result("Check Content Quota", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Check Content Quota", False, str(e))
            return False

    def test_update_quota(self) -> bool:
        """Test PUT /api/v1/organizations/{org_id}/quota"""
        print_section("Test: Update Quota")

        if not self.test_org_id:
            print_warning("No test organization ID available, skipping")
            return False

        quota_data = {
            "max_devices": 50,
            "max_users": 20,
            "max_content_size_gb": 500,
            "max_content_items": 5000,
            "max_playlists": 200
        }

        try:
            response = requests.put(
                f"{self.api_v1}/organizations/{self.test_org_id}/quota",
                headers=self.get_headers(),
                json=quota_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                devices = data.get("devices", {})
                users = data.get("users", {})
                content = data.get("content", {})
                playlists = data.get("playlists", {})

                print_info(f"Updated max devices: {devices.get('max')}")
                print_info(f"Updated max users: {users.get('max')}")
                print_info(f"Updated max content size: {content.get('max_size_gb')}GB")
                print_info(f"Updated max content items: {content.get('max_items')}")
                print_info(f"Updated max playlists: {playlists.get('max')}")

                self.record_result("Update Quota", True)
                return True
            else:
                self.record_result("Update Quota", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Update Quota", False, str(e))
            return False

    # =========================================================================
    # ATOMIC QUOTA ENFORCEMENT TEST
    # =========================================================================

    def test_concurrent_quota_enforcement(self) -> bool:
        """Test atomic quota enforcement with concurrent requests"""
        print_section("Test: Concurrent Quota Enforcement (Race Condition Test)")

        if not self.test_org_id:
            print_warning("No test organization ID available, skipping")
            return False

        print_info("Setting quota to 2 devices...")

        # Set low quota for testing
        try:
            response = requests.put(
                f"{self.api_v1}/organizations/{self.test_org_id}/quota",
                headers=self.get_headers(),
                json={"max_devices": 2},
                timeout=10
            )

            if response.status_code != 200:
                print_error(f"Failed to set quota: {response.text}")
                return False

        except Exception as e:
            print_error(f"Failed to set quota: {str(e)}")
            return False

        print_info("Attempting to create 5 devices concurrently...")

        # Attempt to create 5 devices concurrently
        results = []

        def create_device(index: int):
            """Create device in thread"""
            try:
                device_data = {
                    "name": f"Test Device {index}",
                    "type": "monitor",
                    "organization_id": self.test_org_id
                }

                response = requests.post(
                    f"{self.api_v1}/devices",
                    headers=self.get_headers(),
                    json=device_data,
                    timeout=10
                )

                results.append({
                    "index": index,
                    "status": response.status_code,
                    "success": response.status_code == 201,
                    "message": response.json().get("message", "") if response.status_code != 201 else "Created"
                })

            except Exception as e:
                results.append({
                    "index": index,
                    "status": 0,
                    "success": False,
                    "message": str(e)
                })

        # Create threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_device, args=(i,))
            threads.append(thread)

        # Start all threads simultaneously
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        elapsed = time.time() - start_time

        # Analyze results
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        print_info(f"Completed in {elapsed:.2f}s")
        print_info(f"Successful: {successful}/5")
        print_info(f"Failed: {failed}/5")

        for result in sorted(results, key=lambda x: x["index"]):
            status = "✓" if result["success"] else "✗"
            color = Colors.GREEN if result["success"] else Colors.RED
            print(f"{color}{status} Device {result['index']}: {result['message']}{Colors.RESET}")

        # Test passes if exactly 2 devices were created (quota limit)
        # and remaining 3 were rejected with quota error
        if successful == 2 and failed == 3:
            self.record_result("Concurrent Quota Enforcement", True)
            print_success("Atomic quota enforcement working correctly!")
            return True
        else:
            self.record_result(
                "Concurrent Quota Enforcement",
                False,
                f"Expected 2 successes and 3 failures, got {successful} successes and {failed} failures"
            )
            return False

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def test_delete_organization(self) -> bool:
        """Test DELETE /api/v1/organizations/{org_id}"""
        print_section("Test: Delete Organization")

        if not self.test_org_id:
            print_warning("No test organization ID available, skipping")
            return False

        try:
            response = requests.delete(
                f"{self.api_v1}/organizations/{self.test_org_id}",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 204:
                print_info(f"Deleted organization ID: {self.test_org_id}")
                self.record_result("Delete Organization", True)
                return True
            else:
                self.record_result("Delete Organization", False, f"Status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            self.record_result("Delete Organization", False, str(e))
            return False

    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================

    def run_all_tests(self):
        """Run all tests"""
        print_section("Organization Management API Test Suite")
        print_info(f"Base URL: {self.base_url}")
        print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Authenticate first
        if not self.authenticate():
            print_error("Authentication failed, cannot proceed with tests")
            return

        # CRUD Tests
        self.test_list_organizations()
        self.test_create_organization()
        self.test_get_organization()
        self.test_update_organization()

        # Quota Tests
        self.test_get_quota()
        self.test_check_device_quota()
        self.test_check_user_quota()
        self.test_check_content_quota()
        self.test_update_quota()

        # Atomic enforcement test
        self.test_concurrent_quota_enforcement()

        # Cleanup
        self.test_delete_organization()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_section("Test Summary")

        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        if self.results["errors"]:
            print(f"\n{Colors.RED}Errors:{Colors.RESET}")
            for error in self.results["errors"]:
                print(f"  - {error['test']}: {error['error']}")

        # Grade
        if pass_rate == 100:
            print(f"\n{Colors.GREEN}{Colors.BOLD}Grade: A+ (100/100) - All tests passed!{Colors.RESET}")
        elif pass_rate >= 90:
            print(f"\n{Colors.GREEN}Grade: A ({pass_rate:.0f}/100) - Excellent{Colors.RESET}")
        elif pass_rate >= 80:
            print(f"\n{Colors.YELLOW}Grade: B ({pass_rate:.0f}/100) - Good{Colors.RESET}")
        elif pass_rate >= 70:
            print(f"\n{Colors.YELLOW}Grade: C ({pass_rate:.0f}/100) - Needs improvement{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}Grade: F ({pass_rate:.0f}/100) - Failed{Colors.RESET}")


def main():
    """Main entry point"""
    tester = OrganizationAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
