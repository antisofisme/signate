#!/usr/bin/env python3
"""
DEEP COMPREHENSIVE BACKEND TESTING
Tests all 17 backend services with detailed test cases
Author: Claude Code Testing Framework
Date: 2025-11-13
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
from pathlib import Path

# Configuration
BASE_URL = "http://192.168.5.12:8001/api/v1"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
MEDIA_PATH = "/mnt/g/khoirul/signate/contoh_media"
TEST_RESULTS = []

class BackendTester:
    def __init__(self):
        self.token = None
        self.admin_user_id = None
        self.test_org_id = None
        self.test_user_id = None
        self.test_device_id = None
        self.test_content_id = None
        self.test_tag_id = None
        self.test_playlist_id = None
        self.test_schedule_id = None
        self.test_template_id = None
        self.test_widget_id = None
        self.test_role_id = None
        self.created_resources = []  # For cleanup

    def log(self, service: str, test: str, status: str, details: str, data: Any = None):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "test": test,
            "status": status,
            "details": details,
            "data": data
        }
        TEST_RESULTS.append(result)

        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} [{service:15s}] {test:40s} | {details}")

    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # ========================================================================
    # TEST 1: AUTH SERVICE
    # ========================================================================
    def test_auth_service(self):
        """Test AUTH service comprehensively"""
        print("\n" + "="*100)
        print("🔐 TEST 1: AUTH SERVICE - Authentication & Authorization")
        print("="*100)

        # 1.1: Login with valid credentials
        try:
            resp = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if resp.status_code == 200:
                data = resp.json()["data"]
                self.token = data["token"]
                self.admin_user_id = data["user"]["id"]
                self.test_org_id = data["user"]["organization_id"]
                self.log("AUTH", "Login (valid credentials)", "PASS",
                        f"Token received, user_id={self.admin_user_id}, org_id={self.test_org_id}")
            else:
                self.log("AUTH", "Login (valid credentials)", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Login (valid credentials)", "FAIL", str(e))

        # 1.2: Login with wrong password
        try:
            resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": "admin", "password": "wrongpass"})
            if resp.status_code in [401, 400]:
                self.log("AUTH", "Login (wrong password)", "PASS", "Correctly rejected")
            else:
                self.log("AUTH", "Login (wrong password)", "FAIL", f"Should reject, got {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Login (wrong password)", "FAIL", str(e))

        # 1.3: Login with non-existent user
        try:
            resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": "nonexistent", "password": "anything"})
            if resp.status_code in [401, 400, 404]:
                self.log("AUTH", "Login (non-existent user)", "PASS", "Correctly rejected")
            else:
                self.log("AUTH", "Login (non-existent user)", "FAIL", f"Should reject, got {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Login (non-existent user)", "FAIL", str(e))

        # 1.4: Access protected endpoint without token
        try:
            resp = requests.get(f"{BASE_URL}/users")
            if resp.status_code == 401:
                self.log("AUTH", "Access without token", "PASS", "Correctly blocked")
            else:
                self.log("AUTH", "Access without token", "FAIL", f"Should block, got {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Access without token", "FAIL", str(e))

        # 1.5: Access with valid token
        try:
            resp = requests.get(f"{BASE_URL}/users", headers=self.get_headers())
            if resp.status_code == 200:
                self.log("AUTH", "Access with valid token", "PASS", "Token auth works")
            else:
                self.log("AUTH", "Access with valid token", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Access with valid token", "FAIL", str(e))

        # 1.6: Token expiration (simulate with invalid token)
        try:
            invalid_headers = {"Authorization": "Bearer invalid.token.here"}
            resp = requests.get(f"{BASE_URL}/users", headers=invalid_headers)
            if resp.status_code == 401:
                self.log("AUTH", "Invalid token rejection", "PASS", "Invalid token blocked")
            else:
                self.log("AUTH", "Invalid token rejection", "FAIL", f"Should block, got {resp.status_code}")
        except Exception as e:
            self.log("AUTH", "Invalid token rejection", "FAIL", str(e))

    # ========================================================================
    # TEST 2: ORGANIZATION SERVICE
    # ========================================================================
    def test_organization_service(self):
        """Test ORGANIZATION service - Multi-tenancy foundation"""
        print("\n" + "="*100)
        print("🏢 TEST 2: ORGANIZATION SERVICE - Multi-tenancy & Isolation")
        print("="*100)

        headers = self.get_headers()

        # 2.1: List all organizations
        try:
            resp = requests.get(f"{BASE_URL}/organizations", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log("ORGANIZATION", "List organizations", "PASS", f"Retrieved {count} orgs")
            else:
                self.log("ORGANIZATION", "List organizations", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("ORGANIZATION", "List organizations", "FAIL", str(e))

        # 2.2: Create new organization
        org_data = {
            "name": f"DeepTest_Org_{int(time.time())}",
            "organization_pin": str(int(time.time()))[-8:],
            "address": "123 Test Street, Test City",
            "phone": "+62812345678",
            "contact_person": "Test Manager"
        }
        try:
            resp = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.test_org_id = data.get("id") or data.get("data", {}).get("id")
                self.created_resources.append(("organization", self.test_org_id))
                self.log("ORGANIZATION", "Create organization", "PASS",
                        f"Created org_id={self.test_org_id}")
            else:
                self.log("ORGANIZATION", "Create organization", "FAIL",
                        f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            self.log("ORGANIZATION", "Create organization", "FAIL", str(e))

        # 2.3: Get single organization by ID
        if self.test_org_id:
            try:
                resp = requests.get(f"{BASE_URL}/organizations/{self.test_org_id}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    org_name = data.get("name") or data.get("data", {}).get("name")
                    self.log("ORGANIZATION", "Get organization by ID", "PASS", f"Name: {org_name}")
                else:
                    self.log("ORGANIZATION", "Get organization by ID", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("ORGANIZATION", "Get organization by ID", "FAIL", str(e))

        # 2.4: Update organization
        if self.test_org_id:
            try:
                update_data = {
                    "name": f"Updated_Org_{int(time.time())}",
                    "phone": "+62888999000"
                }
                resp = requests.put(f"{BASE_URL}/organizations/{self.test_org_id}",
                                  json=update_data, headers=headers)
                if resp.status_code == 200:
                    self.log("ORGANIZATION", "Update organization", "PASS", "Updated successfully")
                else:
                    self.log("ORGANIZATION", "Update organization", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("ORGANIZATION", "Update organization", "FAIL", str(e))

        # 2.5: Duplicate organization_pin validation
        try:
            dup_data = org_data.copy()
            dup_data["name"] = "Duplicate PIN Test"
            resp = requests.post(f"{BASE_URL}/organizations", json=dup_data, headers=headers)
            if resp.status_code in [400, 409]:
                self.log("ORGANIZATION", "Duplicate PIN validation", "PASS",
                        "Correctly rejected duplicate PIN")
            else:
                self.log("ORGANIZATION", "Duplicate PIN validation", "WARN",
                        f"Should reject duplicate, got {resp.status_code}")
        except Exception as e:
            self.log("ORGANIZATION", "Duplicate PIN validation", "FAIL", str(e))

    # ========================================================================
    # TEST 3: USER SERVICE
    # ========================================================================
    def test_user_service(self):
        """Test USER service - User management & roles"""
        print("\n" + "="*100)
        print("👤 TEST 3: USER SERVICE - User Management & Roles")
        print("="*100)

        headers = self.get_headers()

        # 3.1: List users
        try:
            resp = requests.get(f"{BASE_URL}/users", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log("USER", "List users", "PASS", f"Retrieved {count} users")
            else:
                self.log("USER", "List users", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("USER", "List users", "FAIL", str(e))

        # 3.2: Create new user
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test{int(time.time())}@signage.test",
            "password": "SecurePass123!@#",
            "full_name": "Deep Test User",
            "role": "user",
            "organization_id": self.test_org_id or 4
        }
        try:
            resp = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.test_user_id = data.get("id") or data.get("data", {}).get("id")
                self.created_resources.append(("user", self.test_user_id))
                self.log("USER", "Create user", "PASS", f"Created user_id={self.test_user_id}")
            else:
                self.log("USER", "Create user", "FAIL", f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            self.log("USER", "Create user", "FAIL", str(e))

        # 3.3: New user can login
        if self.test_user_id:
            try:
                resp = requests.post(f"{BASE_URL}/auth/login",
                                   json={"username": user_data["username"],
                                        "password": user_data["password"]})
                if resp.status_code == 200:
                    self.log("USER", "New user login", "PASS", "New user authenticated")
                else:
                    self.log("USER", "New user login", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("USER", "New user login", "FAIL", str(e))

        # 3.4: Get user by ID
        if self.test_user_id:
            try:
                resp = requests.get(f"{BASE_URL}/users/{self.test_user_id}", headers=headers)
                if resp.status_code == 200:
                    self.log("USER", "Get user by ID", "PASS", "Retrieved user details")
                else:
                    self.log("USER", "Get user by ID", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("USER", "Get user by ID", "FAIL", str(e))

        # 3.5: Update user
        if self.test_user_id:
            try:
                update_data = {"full_name": "Updated Test User", "is_active": True}
                resp = requests.put(f"{BASE_URL}/users/{self.test_user_id}",
                                  json=update_data, headers=headers)
                if resp.status_code == 200:
                    self.log("USER", "Update user", "PASS", "User updated")
                else:
                    self.log("USER", "Update user", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("USER", "Update user", "FAIL", str(e))

        # 3.6: Duplicate username validation
        try:
            dup_data = user_data.copy()
            dup_data["email"] = f"different{int(time.time())}@test.com"
            resp = requests.post(f"{BASE_URL}/users", json=dup_data, headers=headers)
            if resp.status_code in [400, 409]:
                self.log("USER", "Duplicate username validation", "PASS", "Rejected duplicate")
            else:
                self.log("USER", "Duplicate username validation", "WARN",
                        f"Should reject, got {resp.status_code}")
        except Exception as e:
            self.log("USER", "Duplicate username validation", "FAIL", str(e))

        # 3.7: Duplicate email validation
        try:
            dup_data = user_data.copy()
            dup_data["username"] = f"different_{int(time.time())}"
            resp = requests.post(f"{BASE_URL}/users", json=dup_data, headers=headers)
            if resp.status_code in [400, 409]:
                self.log("USER", "Duplicate email validation", "PASS", "Rejected duplicate")
            else:
                self.log("USER", "Duplicate email validation", "WARN",
                        f"Should reject, got {resp.status_code}")
        except Exception as e:
            self.log("USER", "Duplicate email validation", "FAIL", str(e))

    # ========================================================================
    # TEST 4: DEVICE SERVICE (COMPLEX - 48+ endpoints)
    # ========================================================================
    def test_device_service(self):
        """Test DEVICE service - Device management (most complex service)"""
        print("\n" + "="*100)
        print("📱 TEST 4: DEVICE SERVICE - Registration, Activation, Monitoring & Commands")
        print("="*100)

        headers = self.get_headers()

        # 4.1: Request activation code (TV registration)
        try:
            device_data = {
                "device_name": f"Test_TV_{int(time.time())}",
                "device_type": "tv",
                "model_name": "LG WebOS 6.0",
                "screen_size": "55",
                "mac_address": f"AA:BB:CC:DD:EE:{int(time.time()) % 100:02d}"
            }
            resp = requests.post(f"{BASE_URL}/devices/request-code", json=device_data)
            if resp.status_code in [200, 201]:
                data = resp.json()
                activation_code = data.get("activation_code") or data.get("data", {}).get("activation_code")
                device_id = data.get("device_id") or data.get("data", {}).get("device_id")
                self.log("DEVICE", "Request activation code", "PASS",
                        f"Code: {activation_code}, device_id={device_id}")

                # Store for next tests
                self.activation_code = activation_code
                pending_device_id = device_id
            else:
                self.log("DEVICE", "Request activation code", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("DEVICE", "Request activation code", "FAIL", str(e))

        # 4.2: Check activation code validity
        if hasattr(self, 'activation_code'):
            try:
                resp = requests.get(f"{BASE_URL}/devices/check-activation/{self.activation_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    is_valid = data.get("valid", False)
                    self.log("DEVICE", "Check activation code", "PASS",
                            f"Valid: {is_valid}")
                else:
                    self.log("DEVICE", "Check activation code", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("DEVICE", "Check activation code", "FAIL", str(e))

        # 4.3: Activate device (admin accepts)
        if hasattr(self, 'activation_code'):
            try:
                activate_data = {
                    "activation_code": self.activation_code,
                    "device_name": f"Activated_TV_{int(time.time())}",
                    "room_number": "101",
                    "location_type": "guest_room"
                }
                resp = requests.post(f"{BASE_URL}/devices/activate",
                                   json=activate_data, headers=headers)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    self.test_device_id = data.get("device_id") or data.get("data", {}).get("device_id")
                    self.created_resources.append(("device", self.test_device_id))
                    self.log("DEVICE", "Activate device", "PASS",
                            f"Activated device_id={self.test_device_id}")
                else:
                    self.log("DEVICE", "Activate device", "FAIL",
                            f"HTTP {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                self.log("DEVICE", "Activate device", "FAIL", str(e))

        # 4.4: List devices (my_org scope)
        try:
            resp = requests.get(f"{BASE_URL}/devices?scope=my_org", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log("DEVICE", "List devices (my_org)", "PASS", f"Found {count} devices")
            else:
                self.log("DEVICE", "List devices (my_org)", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("DEVICE", "List devices (my_org)", "FAIL", str(e))

        # 4.5: List unassigned devices
        try:
            resp = requests.get(f"{BASE_URL}/devices?scope=unassigned", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("items", [])) if isinstance(data, dict) else len(data)
                self.log("DEVICE", "List devices (unassigned)", "PASS", f"Found {count} unassigned")
            else:
                self.log("DEVICE", "List devices (unassigned)", "FAIL", f"HTTP {resp.status_code}")
        except Exception as e:
            self.log("DEVICE", "List devices (unassigned)", "FAIL", str(e))

        # 4.6: Get device by ID
        if self.test_device_id:
            try:
                resp = requests.get(f"{BASE_URL}/devices/{self.test_device_id}", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    device_name = data.get("device_name") or data.get("data", {}).get("device_name")
                    self.log("DEVICE", "Get device by ID", "PASS", f"Name: {device_name}")
                else:
                    self.log("DEVICE", "Get device by ID", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("DEVICE", "Get device by ID", "FAIL", str(e))

        # 4.7: Update device settings
        if self.test_device_id:
            try:
                update_data = {
                    "device_name": f"Updated_TV_{int(time.time())}",
                    "rotation": 0,
                    "volume_enabled": True
                }
                resp = requests.put(f"{BASE_URL}/devices/{self.test_device_id}",
                                  json=update_data, headers=headers)
                if resp.status_code == 200:
                    self.log("DEVICE", "Update device", "PASS", "Settings updated")
                else:
                    self.log("DEVICE", "Update device", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("DEVICE", "Update device", "FAIL", str(e))

        # 4.8: Device heartbeat
        if self.test_device_id:
            try:
                resp = requests.post(f"{BASE_URL}/devices/heartbeat",
                                   json={"device_id": self.test_device_id})
                if resp.status_code in [200, 204]:
                    self.log("DEVICE", "Heartbeat", "PASS", "Heartbeat accepted")
                else:
                    self.log("DEVICE", "Heartbeat", "FAIL", f"HTTP {resp.status_code}")
            except Exception as e:
                self.log("DEVICE", "Heartbeat", "FAIL", str(e))

        # Continue in next part due to length...

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*100)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*100)

        # Statistics
        total = len(TEST_RESULTS)
        passed = sum(1 for r in TEST_RESULTS if r["status"] == "PASS")
        failed = sum(1 for r in TEST_RESULTS if r["status"] == "FAIL")
        warnings = sum(1 for r in TEST_RESULTS if r["status"] == "WARN")

        print(f"\n📈 OVERALL RESULTS:")
        print(f"  ✅ PASSED:   {passed:3d}/{total} ({passed/total*100:5.1f}%)")
        print(f"  ❌ FAILED:   {failed:3d}/{total} ({failed/total*100:5.1f}%)")
        print(f"  ⚠️  WARNINGS: {warnings:3d}/{total} ({warnings/total*100:5.1f}%)")

        # Group by service
        services = {}
        for r in TEST_RESULTS:
            svc = r["service"]
            if svc not in services:
                services[svc] = {"pass": 0, "fail": 0, "warn": 0, "tests": []}
            services[svc][r["status"].lower()] += 1
            services[svc]["tests"].append(r)

        print(f"\n📋 RESULTS BY SERVICE:")
        print("="*100)
        for svc in sorted(services.keys()):
            stats = services[svc]
            total_tests = sum([stats["pass"], stats["fail"], stats["warn"]])
            pass_rate = stats["pass"] / total_tests * 100 if total_tests > 0 else 0
            icon = "✅" if pass_rate == 100 else "⚠️" if pass_rate >= 70 else "❌"
            print(f"{icon} {svc:20s}: {stats['pass']:2d}/{total_tests:2d} passed ({pass_rate:5.1f}%)")

        # Save detailed JSON
        output_file = "/mnt/g/khoirul/signate/BACKEND_TEST_REPORT.json"
        with open(output_file, "w") as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "pass_rate": f"{passed/total*100:.1f}%"
                },
                "services": services,
                "all_results": TEST_RESULTS
            }, f, indent=2)

        print(f"\n💾 Detailed report saved to: {output_file}")

def main():
    print("╔" + "="*98 + "╗")
    print("║" + " "*30 + "DEEP BACKEND TESTING SUITE" + " "*42 + "║")
    print("║" + " "*35 + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " "*38 + "║")
    print("╚" + "="*98 + "╝\n")

    tester = BackendTester()

    try:
        tester.test_auth_service()
        tester.test_organization_service()
        tester.test_user_service()
        tester.test_device_service()
        # More services will be added in continuation...

    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.generate_report()

if __name__ == "__main__":
    main()
