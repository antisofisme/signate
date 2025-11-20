#!/usr/bin/env python3
"""
Integration Tests for Digital Signage CMS - v2
Comprehensive end-to-end workflow testing
"""

import requests
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys

# Configuration
BASE_URL = "http://192.168.5.12:8001"
API_PREFIX = "/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class IntegrationTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.test_data = {}
        self.api_issues = []
        self.vote_items = []
        self.performance_metrics = []

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.BLUE,
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "WARN": Colors.YELLOW,
            "DEBUG": Colors.CYAN
        }.get(level, Colors.RESET)
        print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")

    def api_call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API call and return response with performance metrics"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        start_time = time.time()

        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000

            # Record performance
            self.performance_metrics.append({
                "endpoint": endpoint,
                "method": method,
                "elapsed_ms": elapsed_ms,
                "status": response.status_code
            })

            # Try to parse JSON, handle empty responses
            try:
                data = response.json() if response.content else None
            except:
                data = {"raw": response.text}

            return {
                "status_code": response.status_code,
                "data": data,
                "headers": dict(response.headers),
                "elapsed_ms": elapsed_ms
            }
        except requests.exceptions.Timeout:
            return {
                "status_code": 0,
                "error": "Request timeout",
                "data": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "error": str(e),
                "data": None
            }

    def extract_response_data(self, response_data: Any) -> Any:
        """Extract actual data from nested response structure"""
        if isinstance(response_data, dict):
            # Handle {success, data, message} structure
            if "data" in response_data:
                return response_data["data"]
        return response_data

    def assert_status(self, response: Dict, expected: int, message: str) -> bool:
        if response["status_code"] == expected:
            perf = f" ({response.get('elapsed_ms', 0):.0f}ms)" if 'elapsed_ms' in response else ""
            self.log(f"✓ {message}{perf}", "PASS")
            return True
        else:
            self.log(f"✗ {message} - Expected {expected}, got {response['status_code']}", "FAIL")
            if response.get("data"):
                self.log(f"  Response: {json.dumps(response['data'], indent=2)[:500]}", "DEBUG")
            self.api_issues.append(f"{message}: HTTP {response['status_code']} (expected {expected})")
            return False

    def record_result(self, scenario: str, passed: bool, details: str = ""):
        self.results.append({
            "scenario": scenario,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def generate_6_digit_code(self) -> str:
        """Generate a 6-digit activation code"""
        return str(random.randint(100000, 999999))

    # ==================== SCENARIO 1: Device Onboarding ====================
    def test_scenario_1_device_onboarding(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 1: Complete Device Onboarding Flow", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Step 1: Login as default admin
        self.log("Step 1: Login as default admin", "INFO")
        login_resp = self.api_call("POST", "/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        passed &= self.assert_status(login_resp, 200, "Admin login")

        if login_resp["status_code"] != 200:
            self.record_result("Scenario 1", False, "Failed at login")
            return

        login_data = self.extract_response_data(login_resp["data"])
        token = login_data.get("token") or login_data.get("access_token")
        user = login_data.get("user")
        self.test_data["token"] = token
        self.test_data["headers"] = {"Authorization": f"Bearer {token}"}
        self.test_data["org_id"] = user["organization_id"]
        self.log(f"  Token: {token[:50]}..., Org: {user['organization_id']}", "DEBUG")

        # Step 2: Device requests activation code (simulating player)
        self.log("Step 2: Device requests activation code (player side)", "INFO")
        activation_code = self.generate_6_digit_code()
        device_request = {
            "code": activation_code,
            "device_name": f"Test Device {int(time.time())}",
            "device_type": "monitor",
            "platform": "browser"
        }
        resp = self.api_call("POST", "/devices/request-code", json=device_request)
        passed &= self.assert_status(resp, 201, "Activation code requested")

        if resp["status_code"] != 201:
            self.record_result("Scenario 1", False, "Failed to request activation code")
            return

        activation_data = self.extract_response_data(resp["data"])
        device_id = activation_data.get("device_id")
        self.test_data["device_id"] = device_id
        self.test_data["activation_code"] = activation_code
        self.log(f"  Device ID: {device_id}, Code: {activation_code}", "DEBUG")

        # Step 3: Admin activates device (web admin side)
        self.log("Step 3: Admin activates device via web admin", "INFO")
        activate_request = {
            "activation_code": activation_code,
            "device_name": f"Test Device {int(time.time())}",
            "location": "Test Location"
        }
        resp = self.api_call("POST", "/devices/activate",
                            json=activate_request, headers=self.test_data["headers"])
        passed &= self.assert_status(resp, 200, "Device activated by admin")

        if resp["status_code"] != 200:
            self.vote_items.append("Device activation: Should it be 200 OK or 201 Created?")

        # Step 4: Send device heartbeat
        self.log("Step 4: Device sends heartbeat", "INFO")
        heartbeat_data = {
            "cpu_usage": 45.5,
            "memory_usage": 60.2,
            "disk_usage": 70.0,
            "network_status": "connected"
        }
        resp = self.api_call("POST", f"/devices/{device_id}/heartbeat", json=heartbeat_data)
        passed &= self.assert_status(resp, 200, "Heartbeat accepted")

        # Step 5: Get device list and verify online
        self.log("Step 5: Admin checks device list (should show online)", "INFO")
        resp = self.api_call("GET", "/devices", headers=self.test_data["headers"])
        passed &= self.assert_status(resp, 200, "Device list retrieved")

        if resp["status_code"] == 200:
            devices = self.extract_response_data(resp["data"])
            if not isinstance(devices, list):
                devices = devices.get("devices", [])  # Handle nested

            device_found = False
            for d in devices:
                if d["id"] == device_id:
                    device_found = True
                    self.log(f"  Device found: {d.get('name', 'N/A')}, Status: {d.get('status', 'N/A')}", "DEBUG")
                    break

            if not device_found:
                self.log(f"  Device {device_id} not in list", "WARN")
                passed = False

        # Step 6: Create default playlist
        self.log("Step 6: Create default playlist", "INFO")
        playlist_data = {
            "name": f"Default Playlist {int(time.time())}",
            "description": "Test default playlist"
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=self.test_data["headers"])
        passed &= self.assert_status(resp, 201, "Playlist created")

        if resp["status_code"] == 201:
            playlist = self.extract_response_data(resp["data"])
            playlist_id = playlist.get("id")
            self.test_data["default_playlist_id"] = playlist_id
            self.log(f"  Playlist ID: {playlist_id}", "DEBUG")

        # Step 7: Assign playlist to device
        self.log("Step 7: Assign playlist to device", "INFO")
        # Check API docs for correct assignment endpoint
        resp = self.api_call("POST", f"/playlists/{playlist_id}/assign/devices",
                           json={"device_ids": [device_id]}, headers=self.test_data["headers"])

        if resp["status_code"] not in [200, 201]:
            # Try alternate approach via device endpoint
            resp = self.api_call("POST", f"/devices/{device_id}/playlists/{playlist_id}",
                               headers=self.test_data["headers"])

        if resp["status_code"] in [200, 201]:
            self.log(f"✓ Playlist assigned to device", "PASS")
        else:
            self.log(f"  Playlist assignment may have failed (HTTP {resp['status_code']})", "WARN")

        # Step 8: Device requests current content
        self.log("Step 8: Device requests current content", "INFO")
        resp = self.api_call("GET", f"/playlists/resolve/{device_id}")
        passed &= self.assert_status(resp, 200, "Content resolved for device")

        self.record_result("Scenario 1: Device Onboarding", passed,
                          "Full device lifecycle from registration to content delivery")

    # ==================== SCENARIO 2: Scheduled Content Delivery ====================
    def test_scenario_2_scheduled_content(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 2: Scheduled Content Delivery", "INFO")
        self.log("=" * 80, "INFO")

        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session", "WARN")
            self.record_result("Scenario 2", False, "Prerequisites not met")
            return

        passed = True
        headers = self.test_data["headers"]

        # Step 1: Create 3 contents (metadata only, no file upload)
        self.log("Step 1: Create 3 content entries", "INFO")
        content_ids = []

        for i in range(3):
            content_data = {
                "name": f"Test Content {i+1} - {int(time.time())}",
                "type": "IMAGE" if i % 2 == 0 else "VIDEO",
                "duration": 10,
                "file_url": f"https://example.com/test_{i+1}.jpg",
                "file_size": 1024000
            }
            resp = self.api_call("POST", "/contents", json=content_data, headers=headers)

            if resp["status_code"] == 201:
                content = self.extract_response_data(resp["data"])
                content_ids.append(content.get("id"))
                self.log(f"  Content {i+1} created: {content.get('id')}", "DEBUG")
            else:
                self.log(f"  Failed to create content {i+1} (HTTP {resp['status_code']})", "FAIL")
                passed = False

        if len(content_ids) < 3:
            self.record_result("Scenario 2", False, "Failed to create content")
            return

        # Step 2: Create scheduled playlist
        self.log("Step 2: Create scheduled playlist with contents", "INFO")
        playlist_data = {
            "name": f"Scheduled Playlist {int(time.time())}",
            "description": "Test scheduled playlist"
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)
        passed &= self.assert_status(resp, 201, "Scheduled playlist created")

        if resp["status_code"] != 201:
            self.record_result("Scenario 2", False, "Failed to create playlist")
            return

        playlist = self.extract_response_data(resp["data"])
        scheduled_playlist_id = playlist.get("id")
        self.log(f"  Scheduled Playlist ID: {scheduled_playlist_id}", "DEBUG")

        # Add contents to playlist
        for idx, content_id in enumerate(content_ids):
            item_data = {
                "content_id": content_id,
                "order": idx,
                "duration": 10
            }
            resp = self.api_call("POST", f"/playlists/{scheduled_playlist_id}/content",
                               json=item_data, headers=headers)

            if resp["status_code"] not in [200, 201]:
                self.log(f"  Failed to add content {idx+1} to playlist", "WARN")
                passed = False

        # Step 3: Create schedule
        self.log("Step 3: Create schedule (active now + 2 minutes)", "INFO")
        now = datetime.now()
        start_time = (now + timedelta(seconds=30)).strftime("%H:%M:%S")
        end_time = (now + timedelta(minutes=5)).strftime("%H:%M:%S")

        schedule_data = {
            "name": f"Test Schedule {int(time.time())}",
            "playlist_id": scheduled_playlist_id,
            "schedule_type": "DAILY",
            "start_time": start_time,
            "end_time": end_time,
            "days_of_week": [now.weekday()],
            "start_date": now.strftime("%Y-%m-%d"),
            "priority": 10,
            "is_active": True
        }

        resp = self.api_call("POST", "/schedules", json=schedule_data, headers=headers)
        passed &= self.assert_status(resp, 201, "Schedule created")

        if resp["status_code"] == 201:
            schedule = self.extract_response_data(resp["data"])
            self.test_data["schedule_id"] = schedule.get("id")
            self.log(f"  Schedule ID: {schedule.get('id')}, active {start_time}-{end_time}", "DEBUG")
        else:
            self.log(f"  Schedule creation failed", "FAIL")
            passed = False

        # Note: Full schedule activation test skipped (requires waiting)
        self.log("Step 4-7: Schedule activation/deactivation (skipped - time intensive)", "INFO")
        self.vote_items.append("Schedule activation: Immediate vs. waiting for start_time?")

        self.record_result("Scenario 2: Scheduled Content", passed,
                          "Schedule creation verified (activation not tested)")

    # ==================== SCENARIO 3: Multi-Tenant Isolation ====================
    def test_scenario_3_multi_tenant_isolation(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 3: Multi-Tenant Isolation", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Create Org A with User A
        self.log("Step 1: Create Organization A and User A", "INFO")

        # If admin token available, create org, otherwise register creates org
        org_a_data = {
            "name": f"Org A {int(time.time())}",
            "email": f"orga{int(time.time())}@example.com"
        }

        if "headers" in self.test_data:
            resp = self.api_call("POST", "/organizations", json=org_a_data, headers=self.test_data["headers"])
            if resp["status_code"] == 201:
                org_a = self.extract_response_data(resp["data"])
                org_a_id = org_a.get("id")
                self.log(f"  Org A ID: {org_a_id}", "DEBUG")
            else:
                # Fallback: use default org
                org_a_id = self.test_data.get("org_id")
        else:
            org_a_id = None

        # Register User A
        user_a_data = {
            "username": f"usera_{int(time.time())}",
            "email": f"usera{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "User A",
            "role": "ADMIN"
        }
        if org_a_id:
            user_a_data["organization_id"] = org_a_id

        resp = self.api_call("POST", "/auth/register", json=user_a_data)
        passed &= self.assert_status(resp, 201, "User A registered")

        if resp["status_code"] != 201:
            self.record_result("Scenario 3", False, "User A creation failed")
            return

        # Login User A
        login_resp = self.api_call("POST", "/auth/login", json={
            "username": user_a_data["username"],
            "password": user_a_data["password"]
        })
        passed &= self.assert_status(login_resp, 200, "User A login")

        if login_resp["status_code"] != 200:
            self.record_result("Scenario 3", False, "User A login failed")
            return

        login_a = self.extract_response_data(login_resp["data"])
        token_a = login_a.get("token") or login_a.get("access_token")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        org_a_id = login_a["user"]["organization_id"]

        # Create Org B with User B
        self.log("Step 2: Create Organization B and User B", "INFO")

        # Register User B (will create new org if needed)
        user_b_data = {
            "username": f"userb_{int(time.time())}",
            "email": f"userb{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "User B",
            "role": "ADMIN"
        }

        resp = self.api_call("POST", "/auth/register", json=user_b_data)
        passed &= self.assert_status(resp, 201, "User B registered")

        if resp["status_code"] != 201:
            self.record_result("Scenario 3", False, "User B creation failed")
            return

        # Login User B
        login_resp = self.api_call("POST", "/auth/login", json={
            "username": user_b_data["username"],
            "password": user_b_data["password"]
        })
        passed &= self.assert_status(login_resp, 200, "User B login")

        if login_resp["status_code"] != 200:
            self.record_result("Scenario 3", False, "User B login failed")
            return

        login_b = self.extract_response_data(login_resp["data"])
        token_b = login_b.get("token") or login_b.get("access_token")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        org_b_id = login_b["user"]["organization_id"]

        if org_a_id == org_b_id:
            self.log(f"  WARNING: Both users in same org ({org_a_id})", "WARN")
            self.api_issues.append("Multi-tenant: New registrations may assign to same org")

        # User A creates Device A
        self.log("Step 3: User A creates Device A", "INFO")
        activation_code_a = self.generate_6_digit_code()
        device_a_req = {
            "code": activation_code_a,
            "device_name": f"Device A {int(time.time())}",
            "device_type": "monitor"
        }
        resp = self.api_call("POST", "/devices/request-code", json=device_a_req)

        if resp["status_code"] == 201:
            device_a_data = self.extract_response_data(resp["data"])
            device_a_id = device_a_data.get("device_id")

            # Activate with User A
            resp = self.api_call("POST", "/devices/activate",
                               json={"activation_code": activation_code_a},
                               headers=headers_a)
            if resp["status_code"] in [200, 201]:
                self.log(f"  Device A ID: {device_a_id}", "DEBUG")
            else:
                device_a_id = None
        else:
            device_a_id = None

        # User B creates Device B
        self.log("Step 4: User B creates Device B", "INFO")
        activation_code_b = self.generate_6_digit_code()
        device_b_req = {
            "code": activation_code_b,
            "device_name": f"Device B {int(time.time())}",
            "device_type": "monitor"
        }
        resp = self.api_call("POST", "/devices/request-code", json=device_b_req)

        if resp["status_code"] == 201:
            device_b_data = self.extract_response_data(resp["data"])
            device_b_id = device_b_data.get("device_id")

            # Activate with User B
            resp = self.api_call("POST", "/devices/activate",
                               json={"activation_code": activation_code_b},
                               headers=headers_b)
            if resp["status_code"] in [200, 201]:
                self.log(f"  Device B ID: {device_b_id}", "DEBUG")
            else:
                device_b_id = None
        else:
            device_b_id = None

        if not device_a_id or not device_b_id:
            self.log("  Device creation incomplete, skipping isolation tests", "WARN")
            self.record_result("Scenario 3", False, "Device creation failed")
            return

        # Step 5-7: Test isolation
        self.log("Step 5: User A tries to access Device B (should fail)", "INFO")
        resp = self.api_call("GET", f"/devices/{device_b_id}", headers=headers_a)

        if resp["status_code"] in [403, 404]:
            self.log(f"  ✓ Access denied (HTTP {resp['status_code']})", "PASS")
        else:
            self.log(f"  ✗ SECURITY: User A can access Device B!", "FAIL")
            passed = False
            self.api_issues.append("Multi-tenant isolation broken: Cross-org device access")

        self.log("Step 6: User A tries to modify Device B (should fail)", "INFO")
        resp = self.api_call("PATCH", f"/devices/{device_b_id}",
                           json={"location": "Hacked"},
                           headers=headers_a)

        if resp["status_code"] in [403, 404]:
            self.log(f"  ✓ Modification denied (HTTP {resp['status_code']})", "PASS")
        else:
            self.log(f"  ✗ SECURITY: User A can modify Device B!", "FAIL")
            passed = False

        self.log("Step 7: Verify User A device list isolation", "INFO")
        resp = self.api_call("GET", "/devices", headers=headers_a)

        if resp["status_code"] == 200:
            devices = self.extract_response_data(resp["data"])
            if not isinstance(devices, list):
                devices = devices.get("devices", [])

            device_b_visible = any(d["id"] == device_b_id for d in devices)

            if not device_b_visible:
                self.log(f"  ✓ Device B not visible to User A", "PASS")
            else:
                self.log(f"  ✗ SECURITY: Device B visible to User A!", "FAIL")
                passed = False

        self.record_result("Scenario 3: Multi-Tenant Isolation", passed,
                          "Organization isolation between tenants")

    # ==================== SCENARIO 4: Cascade Delete ====================
    def test_scenario_4_cascade_delete(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 4: Cascade Delete (ON DELETE SET NULL)", "INFO")
        self.log("=" * 80, "INFO")

        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session", "WARN")
            self.record_result("Scenario 4", False, "Prerequisites not met")
            return

        passed = True
        headers = self.test_data["headers"]

        # Create test user
        self.log("Step 1: Create test user", "INFO")
        user_data = {
            "username": f"deletetest_{int(time.time())}",
            "email": f"deletetest{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Delete Test",
            "role": "USER",
            "organization_id": self.test_data.get("org_id")
        }
        resp = self.api_call("POST", "/auth/register", json=user_data)
        passed &= self.assert_status(resp, 201, "Test user created")

        if resp["status_code"] != 201:
            self.record_result("Scenario 4", False, "User creation failed")
            return

        test_user = self.extract_response_data(resp["data"])
        test_user_id = test_user.get("id")

        # Login as test user
        login_resp = self.api_call("POST", "/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })

        if login_resp["status_code"] == 200:
            login_data = self.extract_response_data(login_resp["data"])
            test_token = login_data.get("token") or login_data.get("access_token")
            test_headers = {"Authorization": f"Bearer {test_token}"}
        else:
            self.record_result("Scenario 4", False, "Test user login failed")
            return

        # User creates content
        self.log("Step 2: User creates content", "INFO")
        content_data = {
            "name": f"Delete Test Content {int(time.time())}",
            "type": "IMAGE",
            "duration": 10,
            "file_url": "https://example.com/test.jpg",
            "file_size": 1024000
        }
        resp = self.api_call("POST", "/contents", json=content_data, headers=test_headers)
        passed &= self.assert_status(resp, 201, "Content created")

        if resp["status_code"] == 201:
            content = self.extract_response_data(resp["data"])
            content_id = content.get("id")
            self.log(f"  Content ID: {content_id}", "DEBUG")
        else:
            self.log("  Skipping rest of cascade test", "WARN")
            self.record_result("Scenario 4", False, "Content creation failed")
            return

        # Delete user
        self.log("Step 3: Delete test user (admin action)", "INFO")
        resp = self.api_call("DELETE", f"/users/{test_user_id}", headers=headers)

        if resp["status_code"] in [200, 204]:
            self.log(f"  ✓ User deleted", "PASS")
        else:
            self.log(f"  User deletion failed (HTTP {resp['status_code']})", "FAIL")
            passed = False
            self.record_result("Scenario 4", False, "User deletion failed")
            return

        # Check content still exists
        self.log("Step 4: Verify content exists with NULL created_by", "INFO")
        resp = self.api_call("GET", f"/contents/{content_id}", headers=headers)

        if resp["status_code"] == 200:
            content = self.extract_response_data(resp["data"])
            created_by = content.get("created_by_id")

            if created_by is None:
                self.log(f"  ✓ Content exists with created_by_id = NULL", "PASS")
            else:
                self.log(f"  ✗ created_by_id not NULL: {created_by}", "FAIL")
                passed = False
                self.api_issues.append("Cascade delete: ON DELETE SET NULL not working")
        else:
            self.log(f"  ⚠ Content not accessible after user deletion", "WARN")
            self.vote_items.append("Content visibility: Should content be visible after owner deletion?")

        self.record_result("Scenario 4: Cascade Delete", passed,
                          "ON DELETE SET NULL behavior")

    # ==================== SCENARIO 5: Device Offline Detection ====================
    def test_scenario_5_device_offline_detection(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 5: Device Offline/Online Detection", "INFO")
        self.log("=" * 80, "INFO")

        if "device_id" not in self.test_data or "headers" not in self.test_data:
            self.log("Skipping - No device from previous tests", "WARN")
            self.record_result("Scenario 5", False, "Prerequisites not met")
            return

        passed = True
        device_id = self.test_data["device_id"]
        headers = self.test_data["headers"]

        # Send heartbeat
        self.log("Step 1: Device sends heartbeat", "INFO")
        heartbeat_data = {
            "cpu_usage": 50.0,
            "memory_usage": 65.0,
            "disk_usage": 75.0,
            "network_status": "connected"
        }
        resp = self.api_call("POST", f"/devices/{device_id}/heartbeat", json=heartbeat_data)
        passed &= self.assert_status(resp, 200, "Heartbeat sent")

        # Check immediately
        self.log("Step 2: Check device status (should be online)", "INFO")
        resp = self.api_call("GET", f"/devices/{device_id}", headers=headers)

        if resp["status_code"] == 200:
            device = self.extract_response_data(resp["data"])
            last_seen = device.get("last_seen_at")

            if last_seen:
                self.log(f"  ✓ Device last_seen updated: {last_seen}", "PASS")
            else:
                self.log(f"  ⚠ No last_seen_at field", "WARN")
                passed = False
        else:
            self.log(f"  Failed to get device", "FAIL")
            passed = False

        self.log("Step 3-5: Offline detection (skipped - requires 6+ min wait)", "INFO")
        self.vote_items.append("Device offline threshold: Confirmed at 5 minutes?")

        self.record_result("Scenario 5: Device Offline Detection", passed,
                          "Heartbeat mechanism (full offline test skipped)")

    # ==================== SCENARIO 6: Priority Schedules ====================
    def test_scenario_6_priority_schedules(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 6: Priority Schedule Resolution", "INFO")
        self.log("=" * 80, "INFO")

        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session", "WARN")
            self.record_result("Scenario 6", False, "Prerequisites not met")
            return

        passed = True
        headers = self.test_data["headers"]

        # Create two playlists
        self.log("Step 1: Create two playlists for priority test", "INFO")
        playlists = []

        for priority in [5, 10]:
            playlist_data = {
                "name": f"Priority {priority} Playlist {int(time.time())}",
                "description": f"Priority {priority} test"
            }
            resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)

            if resp["status_code"] == 201:
                playlist = self.extract_response_data(resp["data"])
                playlists.append({"id": playlist.get("id"), "priority": priority})
                self.log(f"  Playlist (priority {priority}): {playlist.get('id')}", "DEBUG")
            else:
                self.log(f"  Failed to create priority {priority} playlist", "FAIL")
                passed = False

        if len(playlists) < 2:
            self.record_result("Scenario 6", False, "Playlist creation failed")
            return

        # Create overlapping schedules
        self.log("Step 2: Create two overlapping schedules with different priorities", "INFO")
        now = datetime.now()

        for playlist_data in playlists:
            schedule_data = {
                "name": f"Schedule Priority {playlist_data['priority']} {int(time.time())}",
                "playlist_id": playlist_data["id"],
                "schedule_type": "DAILY",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "days_of_week": list(range(7)),
                "start_date": now.strftime("%Y-%m-%d"),
                "priority": playlist_data["priority"],
                "is_active": True
            }
            resp = self.api_call("POST", "/schedules", json=schedule_data, headers=headers)

            if resp["status_code"] == 201:
                schedule = self.extract_response_data(resp["data"])
                self.log(f"  Schedule (priority {playlist_data['priority']}): {schedule.get('id')}", "DEBUG")
            else:
                self.log(f"  Failed to create schedule (priority {playlist_data['priority']})", "FAIL")
                passed = False

        self.log("Step 3: Priority resolution (requires time-based test)", "INFO")
        self.vote_items.append("Priority ties: What happens when two schedules have same priority?")
        self.vote_items.append("Schedule overlap: Higher priority always wins?")

        self.record_result("Scenario 6: Priority Schedules", passed,
                          "Priority schedule creation (resolution not tested)")

    # ==================== SCENARIO 7: Content Deletion in Playlist ====================
    def test_scenario_7_content_deletion_in_playlist(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 7: Content Deletion in Playlist (Soft Delete)", "INFO")
        self.log("=" * 80, "INFO")

        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session", "WARN")
            self.record_result("Scenario 7", False, "Prerequisites not met")
            return

        passed = True
        headers = self.test_data["headers"]

        # Create 3 contents
        self.log("Step 1: Create 3 contents", "INFO")
        content_ids = []

        for i in range(3):
            content_data = {
                "name": f"Delete Test {i+1} - {int(time.time())}",
                "type": "IMAGE",
                "duration": 10,
                "file_url": f"https://example.com/test_{i+1}.jpg",
                "file_size": 1024000
            }
            resp = self.api_call("POST", "/contents", json=content_data, headers=headers)

            if resp["status_code"] == 201:
                content = self.extract_response_data(resp["data"])
                content_ids.append(content.get("id"))
            else:
                passed = False

        if len(content_ids) < 3:
            self.record_result("Scenario 7", False, "Content creation failed")
            return

        # Create playlist
        self.log("Step 2: Create playlist with 3 contents", "INFO")
        playlist_data = {
            "name": f"Deletion Test Playlist {int(time.time())}",
            "description": "Test content deletion"
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)
        passed &= self.assert_status(resp, 201, "Playlist created")

        if resp["status_code"] != 201:
            self.record_result("Scenario 7", False, "Playlist creation failed")
            return

        playlist = self.extract_response_data(resp["data"])
        playlist_id = playlist.get("id")

        # Add contents
        for idx, content_id in enumerate(content_ids):
            item_data = {"content_id": content_id, "order": idx, "duration": 10}
            resp = self.api_call("POST", f"/playlists/{playlist_id}/content",
                               json=item_data, headers=headers)

            if resp["status_code"] not in [200, 201]:
                passed = False

        # Delete middle content
        self.log("Step 3: Soft delete middle content", "INFO")
        middle_content_id = content_ids[1]
        resp = self.api_call("DELETE", f"/contents/{middle_content_id}", headers=headers)

        if resp["status_code"] in [200, 204]:
            self.log(f"  ✓ Content deleted", "PASS")
        else:
            self.log(f"  Content deletion failed (HTTP {resp['status_code']})", "FAIL")
            passed = False

        # Get playlist items
        self.log("Step 4: Get playlist items (should exclude deleted)", "INFO")
        resp = self.api_call("GET", f"/playlists/{playlist_id}/content", headers=headers)

        if resp["status_code"] == 200:
            items = self.extract_response_data(resp["data"])
            if not isinstance(items, list):
                items = items.get("items", [])

            has_deleted = any(
                item.get("content_id") == middle_content_id for item in items
            )

            if not has_deleted:
                self.log(f"  ✓ Deleted content excluded from playlist ({len(items)} items)", "PASS")
            else:
                self.log(f"  ✗ Deleted content still in playlist", "FAIL")
                passed = False
                self.api_issues.append("Soft delete: Deleted content still appears in playlists")
        else:
            passed = False

        self.vote_items.append("Content deletion: Should hard delete be possible or always soft?")

        self.record_result("Scenario 7: Content Deletion", passed,
                          "Soft delete and playlist filtering")

    # ==================== GENERATE REPORT ====================
    def generate_report(self):
        self.log("=" * 80, "INFO")
        self.log("INTEGRATION TEST REPORT", "INFO")
        self.log("=" * 80, "INFO")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        health_score = round((passed_tests / total_tests) * 10, 1) if total_tests > 0 else 0
        elapsed_time = time.time() - self.start_time

        print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}SUMMARY{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

        score_color = Colors.GREEN if health_score >= 7 else (Colors.YELLOW if health_score >= 5 else Colors.RED)
        print(f"Integration Health Score: {score_color}{health_score}/10{Colors.RESET}")
        print(f"Total Scenarios: {total_tests}")
        print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed_tests}{Colors.RESET}")
        print(f"Execution Time: {elapsed_time:.2f}s\n")

        # Test Results
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}TEST RESULTS{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

        for idx, result in enumerate(self.results, 1):
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result["passed"] else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"{idx}. [{status}] {result['scenario']}")
            if result["details"]:
                print(f"   {result['details']}")

        # API Issues
        if self.api_issues:
            print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
            print(f"{Colors.RED}API ISSUES FOUND{Colors.RESET}")
            print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")
            for issue in self.api_issues:
                print(f"  • {issue}")

        # Performance
        if self.performance_metrics:
            print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
            print(f"{Colors.CYAN}PERFORMANCE METRICS{Colors.RESET}")
            print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

            slow_endpoints = [m for m in self.performance_metrics if m['elapsed_ms'] > 1000]
            if slow_endpoints:
                print(f"Slow endpoints (>1s):")
                for m in slow_endpoints[:5]:
                    print(f"  • {m['method']} {m['endpoint']}: {m['elapsed_ms']:.0f}ms")
            else:
                print(f"{Colors.GREEN}✓ All endpoints responded in <1s{Colors.RESET}")

            avg_response = sum(m['elapsed_ms'] for m in self.performance_metrics) / len(self.performance_metrics)
            print(f"\nAverage response time: {avg_response:.0f}ms")

        # Vote Items
        if self.vote_items:
            print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
            print(f"{Colors.YELLOW}VOTE ITEMS (Ambiguous Behaviors){Colors.RESET}")
            print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")
            for idx, item in enumerate(set(self.vote_items), 1):
                print(f"{idx}. {item}")

        # Overall Assessment
        print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CYAN}OVERALL ASSESSMENT{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

        if health_score >= 8:
            print(f"{Colors.GREEN}✓ EXCELLENT: System integration working well{Colors.RESET}")
            print("  All critical workflows functional, ready for production")
        elif health_score >= 6:
            print(f"{Colors.YELLOW}⚠ GOOD: System mostly functional with minor issues{Colors.RESET}")
            print("  Core workflows work, some edge cases need attention")
        elif health_score >= 4:
            print(f"{Colors.YELLOW}⚠ FAIR: Significant issues found{Colors.RESET}")
            print("  Basic functionality works, but important features broken")
        else:
            print(f"{Colors.RED}✗ POOR: Critical issues require immediate attention{Colors.RESET}")
            print("  Major workflows broken, system not ready for use")

        return health_score

    # ==================== RUN ALL TESTS ====================
    def run_all(self):
        self.log("Integration Test Suite v2 - Digital Signage CMS", "INFO")
        self.log(f"Target: {BASE_URL}", "INFO")
        self.log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        print()

        try:
            self.test_scenario_1_device_onboarding()
            print()

            self.test_scenario_2_scheduled_content()
            print()

            self.test_scenario_3_multi_tenant_isolation()
            print()

            self.test_scenario_4_cascade_delete()
            print()

            self.test_scenario_5_device_offline_detection()
            print()

            self.test_scenario_6_priority_schedules()
            print()

            self.test_scenario_7_content_deletion_in_playlist()
            print()

            health_score = self.generate_report()
            return health_score

        except KeyboardInterrupt:
            self.log("\nTest suite interrupted by user", "WARN")
            self.generate_report()
            return 0
        except Exception as e:
            self.log(f"\nUnexpected error: {str(e)}", "FAIL")
            import traceback
            traceback.print_exc()
            return 0

if __name__ == "__main__":
    suite = IntegrationTestSuite()
    health_score = suite.run_all()
    sys.exit(0 if health_score >= 6 else 1)
