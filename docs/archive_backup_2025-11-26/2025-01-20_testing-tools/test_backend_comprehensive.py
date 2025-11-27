#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING SCRIPT
Tests all backend services systematically with detailed reporting
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Configuration
BASE_URL = "http://192.168.5.12:8001/api/v1"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
TEST_RESULTS = []

class TestRunner:
    def __init__(self):
        self.token = None
        self.test_org_id = None
        self.test_user_id = None
        self.test_device_id = None
        self.test_content_id = None
        self.test_tag_id = None
        self.test_playlist_id = None

    def log_test(self, service: str, test_name: str, status: str, details: str, response: Optional[Dict] = None):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "test": test_name,
            "status": status,
            "details": details,
            "response_code": response.get("status_code") if response else None
        }
        TEST_RESULTS.append(result)

        # Print progress
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} [{service}] {test_name}: {details}")

    def test_auth_service(self):
        """Test AUTH service comprehensively"""
        print("\n" + "="*80)
        print("🔐 TESTING AUTH SERVICE")
        print("="*80)

        # Test 1: Login with correct credentials
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["token"]
                self.test_org_id = data["data"]["user"]["organization_id"]
                self.log_test("AUTH", "Login (valid credentials)", "PASS",
                            f"Token received, user_id={data['data']['user']['id']}")
            else:
                self.log_test("AUTH", "Login (valid credentials)", "FAIL",
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("AUTH", "Login (valid credentials)", "FAIL", str(e))

        # Test 2: Login with wrong password
        try:
            response = requests.post(f"{BASE_URL}/auth/login",
                                   json={"username": "admin", "password": "wrongpass"})
            if response.status_code == 401 or response.status_code == 400:
                self.log_test("AUTH", "Login (wrong password)", "PASS",
                            "Correctly rejected invalid credentials")
            else:
                self.log_test("AUTH", "Login (wrong password)", "FAIL",
                            f"Should reject but got {response.status_code}")
        except Exception as e:
            self.log_test("AUTH", "Login (wrong password)", "FAIL", str(e))

        # Test 3: Access protected endpoint without token
        try:
            response = requests.get(f"{BASE_URL}/users")
            if response.status_code == 401:
                self.log_test("AUTH", "Access without token", "PASS",
                            "Correctly blocked unauthorized access")
            else:
                self.log_test("AUTH", "Access without token", "FAIL",
                            f"Should block but got {response.status_code}")
        except Exception as e:
            self.log_test("AUTH", "Access without token", "FAIL", str(e))

        # Test 4: Access with valid token
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/users", headers=headers)
            if response.status_code == 200:
                self.log_test("AUTH", "Access with valid token", "PASS",
                            "Token authentication works")
            else:
                self.log_test("AUTH", "Access with valid token", "FAIL",
                            f"Token auth failed: {response.status_code}")
        except Exception as e:
            self.log_test("AUTH", "Access with valid token", "FAIL", str(e))

    def test_organization_service(self):
        """Test ORGANIZATION service"""
        print("\n" + "="*80)
        print("🏢 TESTING ORGANIZATION SERVICE")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test 1: List organizations
        try:
            response = requests.get(f"{BASE_URL}/organizations", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log_test("ORGANIZATION", "List organizations", "PASS",
                            f"Retrieved {count} organizations")
            else:
                self.log_test("ORGANIZATION", "List organizations", "FAIL",
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("ORGANIZATION", "List organizations", "FAIL", str(e))

        # Test 2: Create new organization
        test_org_data = {
            "name": f"TestOrg_{int(time.time())}",
            "organization_pin": str(int(time.time()))[-8:],
            "address": "Test Address",
            "phone": "1234567890"
        }
        try:
            response = requests.post(f"{BASE_URL}/organizations",
                                   json=test_org_data, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                new_org_id = data.get("id") or data.get("data", {}).get("id")
                self.log_test("ORGANIZATION", "Create organization", "PASS",
                            f"Created org_id={new_org_id}")
                self.test_org_id = new_org_id
            else:
                self.log_test("ORGANIZATION", "Create organization", "FAIL",
                            f"Status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("ORGANIZATION", "Create organization", "FAIL", str(e))

        # Test 3: Get single organization
        if self.test_org_id:
            try:
                response = requests.get(f"{BASE_URL}/organizations/{self.test_org_id}",
                                      headers=headers)
                if response.status_code == 200:
                    self.log_test("ORGANIZATION", "Get single organization", "PASS",
                                f"Retrieved org details")
                else:
                    self.log_test("ORGANIZATION", "Get single organization", "FAIL",
                                f"Status {response.status_code}")
            except Exception as e:
                self.log_test("ORGANIZATION", "Get single organization", "FAIL", str(e))

        # Test 4: Update organization
        if self.test_org_id:
            try:
                update_data = {"name": f"UpdatedOrg_{int(time.time())}"}
                response = requests.put(f"{BASE_URL}/organizations/{self.test_org_id}",
                                      json=update_data, headers=headers)
                if response.status_code == 200:
                    self.log_test("ORGANIZATION", "Update organization", "PASS",
                                "Organization updated successfully")
                else:
                    self.log_test("ORGANIZATION", "Update organization", "FAIL",
                                f"Status {response.status_code}")
            except Exception as e:
                self.log_test("ORGANIZATION", "Update organization", "FAIL", str(e))

    def test_user_service(self):
        """Test USER service"""
        print("\n" + "="*80)
        print("👤 TESTING USER SERVICE")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test 1: List users
        try:
            response = requests.get(f"{BASE_URL}/users", headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log_test("USER", "List users", "PASS",
                            f"Retrieved {count} users")
            else:
                self.log_test("USER", "List users", "FAIL",
                            f"Status {response.status_code}")
        except Exception as e:
            self.log_test("USER", "List users", "FAIL", str(e))

        # Test 2: Create new user
        test_user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test{int(time.time())}@example.com",
            "password": "Test123!@#",
            "full_name": "Test User",
            "role": "user",
            "organization_id": self.test_org_id or 4
        }
        try:
            response = requests.post(f"{BASE_URL}/users",
                                   json=test_user_data, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                new_user_id = data.get("id") or data.get("data", {}).get("id")
                self.log_test("USER", "Create user", "PASS",
                            f"Created user_id={new_user_id}")
                self.test_user_id = new_user_id
            else:
                self.log_test("USER", "Create user", "FAIL",
                            f"Status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("USER", "Create user", "FAIL", str(e))

        # Test 3: User login
        if self.test_user_id:
            try:
                response = requests.post(f"{BASE_URL}/auth/login",
                                       json={"username": test_user_data["username"],
                                            "password": test_user_data["password"]})
                if response.status_code == 200:
                    self.log_test("USER", "New user login", "PASS",
                                "New user can login successfully")
                else:
                    self.log_test("USER", "New user login", "FAIL",
                                f"Status {response.status_code}")
            except Exception as e:
                self.log_test("USER", "New user login", "FAIL", str(e))

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 TEST REPORT SUMMARY")
        print("="*80)

        # Count results by status
        total = len(TEST_RESULTS)
        passed = len([r for r in TEST_RESULTS if r["status"] == "PASS"])
        failed = len([r for r in TEST_RESULTS if r["status"] == "FAIL"])
        warnings = len([r for r in TEST_RESULTS if r["status"] == "WARN"])

        print(f"\n✅ PASSED: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"❌ FAILED: {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"⚠️  WARNINGS: {warnings}/{total}")

        # Group by service
        services = {}
        for result in TEST_RESULTS:
            service = result["service"]
            if service not in services:
                services[service] = {"pass": 0, "fail": 0, "warn": 0}
            services[service][result["status"].lower()] += 1

        print("\n" + "="*80)
        print("📋 RESULTS BY SERVICE")
        print("="*80)
        for service, counts in sorted(services.items()):
            total_tests = sum(counts.values())
            pass_rate = counts["pass"] / total_tests * 100
            icon = "✅" if pass_rate == 100 else "⚠️" if pass_rate >= 70 else "❌"
            print(f"{icon} {service:20s}: {counts['pass']}/{total_tests} passed ({pass_rate:.0f}%)")

        # Save detailed results to JSON
        with open("/mnt/g/khoirul/signate/test_results.json", "w") as f:
            json.dump(TEST_RESULTS, f, indent=2)
        print(f"\n📄 Detailed results saved to: test_results.json")

def main():
    """Run all tests"""
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "BACKEND COMPREHENSIVE TESTING" + " "*29 + "║")
    print("║" + " "*25 + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " "*25 + "║")
    print("╚" + "="*78 + "╝")

    runner = TestRunner()

    try:
        runner.test_auth_service()
        runner.test_organization_service()
        runner.test_user_service()
        # More services will be added...

    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
    finally:
        runner.generate_report()

if __name__ == "__main__":
    main()
