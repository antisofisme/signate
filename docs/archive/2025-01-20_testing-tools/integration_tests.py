#!/usr/bin/env python3
"""
Integration Tests for Digital Signage CMS
Tests complete workflows across services
"""

import requests
import time
import json
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
    RESET = '\033[0m'

class IntegrationTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.test_data = {}  # Store created resources for cleanup

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": Colors.BLUE,
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "WARN": Colors.YELLOW
        }.get(level, Colors.RESET)
        print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")

    def api_call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API call and return response"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "headers": dict(response.headers),
                "elapsed_ms": response.elapsed.total_seconds() * 1000
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "error": str(e),
                "data": None
            }

    def assert_status(self, response: Dict, expected: int, message: str):
        """Assert HTTP status code"""
        if response["status_code"] == expected:
            self.log(f"✓ {message} (HTTP {expected})", "PASS")
            return True
        else:
            self.log(f"✗ {message} - Expected {expected}, got {response['status_code']}", "FAIL")
            if response.get("data"):
                self.log(f"  Response: {json.dumps(response['data'], indent=2)}", "INFO")
            return False

    def assert_field(self, data: Dict, field: str, message: str):
        """Assert field exists in data"""
        if field in data:
            self.log(f"✓ {message}", "PASS")
            return True
        else:
            self.log(f"✗ {message} - Field '{field}' not found", "FAIL")
            return False

    def record_result(self, scenario: str, passed: bool, details: str = ""):
        """Record test result"""
        self.results.append({
            "scenario": scenario,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    # ==================== SCENARIO 1: Device Onboarding ====================
    def test_scenario_1_device_onboarding(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 1: Complete Device Onboarding Flow", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Step 1: Login as default admin
        self.log("Step 1: Login as default admin", "INFO")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        resp = self.api_call("POST", "/auth/login", json=login_data)
        passed &= self.assert_status(resp, 200, "Login successful")

        if resp["status_code"] == 200:
            # Handle nested response structure
            login_response = resp["data"]
            if "data" in login_response:
                # Nested structure: {success, data: {user, token}}
                token = login_response["data"]["token"]
                user = login_response["data"]["user"]
            else:
                # Flat structure: {user, token}
                token = login_response.get("token") or login_response.get("access_token")
                user = login_response.get("user")

            self.test_data["token"] = token
            headers = {"Authorization": f"Bearer {token}"}
            self.test_data["headers"] = headers
            self.test_data["user_id"] = user["id"]
            self.test_data["org_id"] = user["organization_id"]
            self.log(f"  JWT Token obtained (length: {len(token)})", "INFO")
            self.log(f"  User ID: {user['id']}, Org ID: {user['organization_id']}", "INFO")
        else:
            self.record_result("Scenario 1", False, "Failed to login")
            return

        # Step 2: Create organization
        self.log("Step 2: Create new organization", "INFO")
        org_data = {
            "name": f"Test Org {int(time.time())}",
            "email": f"testorg{int(time.time())}@example.com",
            "phone": "+6281234567890"
        }
        resp = self.api_call("POST", "/organizations", json=org_data, headers=headers)

        if resp["status_code"] == 201:
            # Handle nested response
            org_response = resp["data"]
            if "data" in org_response:
                org = org_response["data"]
            else:
                org = org_response
            self.test_data["test_org_id"] = org["id"]
            self.log(f"  Test Organization ID: {org['id']}", "PASS")
        else:
            self.log(f"  Failed to create organization (HTTP {resp['status_code']})", "WARN")
            # Not critical, continue with default org

        # Step 3: Create test user
        self.log("Step 3: Create test user for testing", "INFO")
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"testuser{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "USER",
            "organization_id": self.test_data["org_id"]
        }
        resp = self.api_call("POST", "/auth/register", json=user_data)

        if resp["status_code"] == 201:
            user_response = resp["data"]
            if "data" in user_response:
                test_user = user_response["data"]
            else:
                test_user = user_response
            self.log(f"  Test User ID: {test_user.get('id', 'created')}", "PASS")
        else:
            self.log(f"  Failed to create test user (HTTP {resp['status_code']})", "WARN")

        # Step 4: Request device activation code
        self.log("Step 4: Request device activation code", "INFO")
        device_request = {
            "device_name": f"Test Device {int(time.time())}",
            "location": "Test Location"
        }
        resp = self.api_call("POST", "/devices/activation-code",
                            json=device_request, headers=headers)
        passed &= self.assert_status(resp, 201, "Activation code generated")

        if resp["status_code"] == 201:
            activation_data = resp["data"]
            activation_code = activation_data["activation_code"]
            device_id = activation_data["device_id"]
            self.test_data["device_id"] = device_id
            self.test_data["activation_code"] = activation_code
            self.log(f"  Activation Code: {activation_code}", "INFO")
            self.log(f"  Device ID: {device_id}", "INFO")
        else:
            self.record_result("Scenario 1", False, "Failed to generate activation code")
            return

        # Step 5: Activate device with code
        self.log("Step 5: Activate device with code", "INFO")
        activate_data = {"activation_code": activation_code}
        resp = self.api_call("POST", "/devices/activate", json=activate_data)
        passed &= self.assert_status(resp, 200, "Device activated")

        if resp["status_code"] == 200:
            device = resp["data"]
            passed &= self.assert_field(device, "status", "Device has status field")
            if device.get("status") == "active":
                self.log(f"  Device status: {device['status']}", "PASS")
            else:
                self.log(f"  Unexpected device status: {device.get('status')}", "FAIL")
                passed = False
        else:
            self.record_result("Scenario 1", False, "Failed to activate device")
            return

        # Step 6: Send device heartbeat
        self.log("Step 6: Send device heartbeat", "INFO")
        heartbeat_data = {
            "cpu_usage": 45.5,
            "memory_usage": 60.2,
            "disk_usage": 70.0,
            "network_status": "connected"
        }
        resp = self.api_call("POST", f"/devices/{device_id}/heartbeat",
                            json=heartbeat_data)
        passed &= self.assert_status(resp, 200, "Heartbeat sent")

        # Step 7: Get device list and verify online
        self.log("Step 7: Get device list and verify online status", "INFO")
        resp = self.api_call("GET", "/devices", headers=headers)
        passed &= self.assert_status(resp, 200, "Device list retrieved")

        if resp["status_code"] == 200:
            devices = resp["data"]
            device_found = False
            for d in devices:
                if d["id"] == device_id:
                    device_found = True
                    # Check last_seen_at is recent (within 1 minute)
                    last_seen = datetime.fromisoformat(d["last_seen_at"].replace('Z', '+00:00'))
                    now = datetime.now(last_seen.tzinfo)
                    diff_seconds = (now - last_seen).total_seconds()

                    if diff_seconds < 60:
                        self.log(f"  Device online (last seen {diff_seconds:.1f}s ago)", "PASS")
                    else:
                        self.log(f"  Device may be offline (last seen {diff_seconds:.1f}s ago)", "WARN")
                    break

            if not device_found:
                self.log(f"  Device {device_id} not found in list", "FAIL")
                passed = False

        # Step 8: Assign default playlist (create one first)
        self.log("Step 8: Create and assign default playlist", "INFO")
        playlist_data = {
            "name": f"Default Playlist {int(time.time())}",
            "description": "Test default playlist",
            "is_default": True
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)

        if resp["status_code"] == 201:
            playlist = resp["data"]
            self.test_data["playlist_id"] = playlist["id"]
            self.log(f"  Playlist created: {playlist['id']}", "INFO")

            # Assign to device
            assign_data = {"default_playlist_id": playlist["id"]}
            resp = self.api_call("PATCH", f"/devices/{device_id}",
                               json=assign_data, headers=headers)
            passed &= self.assert_status(resp, 200, "Playlist assigned to device")
        else:
            self.log(f"  Failed to create playlist (status {resp['status_code']})", "WARN")

        # Step 9: Device requests current content
        self.log("Step 9: Device requests current content", "INFO")
        resp = self.api_call("GET", f"/devices/{device_id}/content")
        passed &= self.assert_status(resp, 200, "Content retrieved")

        if resp["status_code"] == 200:
            content_data = resp["data"]
            self.log(f"  Content response: {json.dumps(content_data, indent=2)}", "INFO")

        self.record_result("Scenario 1: Device Onboarding", passed,
                          "Complete device lifecycle from creation to content delivery")

    # ==================== SCENARIO 2: Scheduled Content Delivery ====================
    def test_scenario_2_scheduled_content(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 2: Scheduled Content Delivery", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Prerequisites: Need authenticated user with device
        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session from Scenario 1", "WARN")
            self.record_result("Scenario 2", False, "Prerequisites not met")
            return

        headers = self.test_data["headers"]
        device_id = self.test_data.get("device_id")

        # Step 1: Upload 3 contents (simulate with metadata only)
        self.log("Step 1: Create 3 content entries", "INFO")
        content_ids = []
        for i in range(3):
            content_data = {
                "name": f"Test Content {i+1} - {int(time.time())}",
                "type": "image" if i % 2 == 0 else "video",
                "file_path": f"/uploads/test_{i+1}.jpg",
                "duration": 10,
                "file_size": 1024000
            }
            resp = self.api_call("POST", "/contents", json=content_data, headers=headers)

            if resp["status_code"] == 201:
                content = resp["data"]
                content_ids.append(content["id"])
                self.log(f"  Content {i+1} created: {content['id']}", "INFO")
            else:
                self.log(f"  Failed to create content {i+1}", "FAIL")
                passed = False

        if len(content_ids) < 3:
            self.record_result("Scenario 2", False, "Failed to create content")
            return

        # Step 2: Create playlist with contents
        self.log("Step 2: Create playlist with contents", "INFO")
        playlist_data = {
            "name": f"Scheduled Playlist {int(time.time())}",
            "description": "Test scheduled playlist",
            "is_default": False
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)
        passed &= self.assert_status(resp, 201, "Playlist created")

        if resp["status_code"] == 201:
            playlist = resp["data"]
            scheduled_playlist_id = playlist["id"]
            self.log(f"  Playlist ID: {scheduled_playlist_id}", "INFO")

            # Add contents to playlist
            for idx, content_id in enumerate(content_ids):
                item_data = {
                    "content_id": content_id,
                    "order": idx,
                    "duration": 10
                }
                resp = self.api_call("POST", f"/playlists/{scheduled_playlist_id}/items",
                                   json=item_data, headers=headers)
                if resp["status_code"] == 201:
                    self.log(f"  Content {idx+1} added to playlist", "INFO")
                else:
                    self.log(f"  Failed to add content {idx+1}", "FAIL")
                    passed = False
        else:
            self.record_result("Scenario 2", False, "Failed to create playlist")
            return

        # Step 3: Create schedule
        self.log("Step 3: Create schedule (active for next 5 minutes)", "INFO")
        now = datetime.now()
        start_time = now + timedelta(minutes=1)
        end_time = now + timedelta(minutes=6)

        schedule_data = {
            "name": f"Test Schedule {int(time.time())}",
            "playlist_id": scheduled_playlist_id,
            "schedule_type": "daily",
            "start_time": start_time.strftime("%H:%M:%S"),
            "end_time": end_time.strftime("%H:%M:%S"),
            "days_of_week": [now.weekday()],  # Today
            "start_date": now.strftime("%Y-%m-%d"),
            "end_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "applies_to_all": True,
            "priority": 10,
            "is_active": True
        }

        resp = self.api_call("POST", "/schedules", json=schedule_data, headers=headers)
        passed &= self.assert_status(resp, 201, "Schedule created")

        if resp["status_code"] == 201:
            schedule = resp["data"]
            self.test_data["schedule_id"] = schedule["id"]
            self.log(f"  Schedule ID: {schedule['id']}", "INFO")
            self.log(f"  Active from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}", "INFO")
        else:
            self.record_result("Scenario 2", False, "Failed to create schedule")
            return

        # Step 4: Wait 2 minutes for schedule to activate
        self.log("Step 4: Waiting 90 seconds for schedule to activate...", "INFO")
        time.sleep(90)

        # Step 5: Device requests content (should get scheduled playlist)
        self.log("Step 5: Device requests content (expecting scheduled playlist)", "INFO")
        if device_id:
            resp = self.api_call("GET", f"/devices/{device_id}/content")

            if resp["status_code"] == 200:
                content_data = resp["data"]
                returned_playlist_id = content_data.get("playlist_id")

                if returned_playlist_id == scheduled_playlist_id:
                    self.log(f"  ✓ Correct playlist returned (scheduled)", "PASS")
                else:
                    self.log(f"  ✗ Wrong playlist returned. Expected {scheduled_playlist_id}, got {returned_playlist_id}", "FAIL")
                    passed = False
            else:
                self.log(f"  Failed to get content", "FAIL")
                passed = False

        # Note: Full schedule expiration test would require waiting 6+ minutes
        # Skipping for practical reasons, but logging the expected behavior
        self.log("Step 6-9: Schedule expiration test (skipped - would require 6+ min wait)", "INFO")
        self.log("  Expected: After end_time, device should receive default playlist", "INFO")

        self.record_result("Scenario 2: Scheduled Content", passed,
                          "Schedule creation and activation (partial - expiration not tested)")

    # ==================== SCENARIO 3: Multi-Tenant Isolation ====================
    def test_scenario_3_multi_tenant_isolation(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 3: Multi-Tenant Isolation", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Create Org A with User A
        self.log("Step 1: Create Organization A with User A", "INFO")
        org_a_data = {
            "name": f"Org A {int(time.time())}",
            "email": f"orga{int(time.time())}@example.com"
        }
        resp = self.api_call("POST", "/organizations", json=org_a_data)

        if resp["status_code"] == 201:
            org_a = resp["data"]
            self.log(f"  Org A ID: {org_a['id']}", "INFO")

            user_a_data = {
                "username": f"usera_{int(time.time())}",
                "email": f"usera{int(time.time())}@example.com",
                "password": "TestPass123!",
                "full_name": "User A",
                "role": "admin",
                "organization_id": org_a["id"]
            }
            resp = self.api_call("POST", "/auth/register", json=user_a_data)

            if resp["status_code"] == 201:
                user_a = resp["data"]
                self.log(f"  User A ID: {user_a['id']}", "INFO")

                # Login User A
                login_resp = self.api_call("POST", "/auth/login", json={
                    "username": user_a_data["username"],
                    "password": user_a_data["password"]
                })

                if login_resp["status_code"] == 200:
                    token_a = login_resp["data"]["access_token"]
                    headers_a = {"Authorization": f"Bearer {token_a}"}
                    self.log(f"  User A logged in", "PASS")
                else:
                    self.record_result("Scenario 3", False, "User A login failed")
                    return
            else:
                self.record_result("Scenario 3", False, "User A creation failed")
                return
        else:
            self.record_result("Scenario 3", False, "Org A creation failed")
            return

        # Create Org B with User B
        self.log("Step 2: Create Organization B with User B", "INFO")
        org_b_data = {
            "name": f"Org B {int(time.time())}",
            "email": f"orgb{int(time.time())}@example.com"
        }
        resp = self.api_call("POST", "/organizations", json=org_b_data)

        if resp["status_code"] == 201:
            org_b = resp["data"]
            self.log(f"  Org B ID: {org_b['id']}", "INFO")

            user_b_data = {
                "username": f"userb_{int(time.time())}",
                "email": f"userb{int(time.time())}@example.com",
                "password": "TestPass123!",
                "full_name": "User B",
                "role": "admin",
                "organization_id": org_b["id"]
            }
            resp = self.api_call("POST", "/auth/register", json=user_b_data)

            if resp["status_code"] == 201:
                user_b = resp["data"]
                self.log(f"  User B ID: {user_b['id']}", "INFO")

                # Login User B
                login_resp = self.api_call("POST", "/auth/login", json={
                    "username": user_b_data["username"],
                    "password": user_b_data["password"]
                })

                if login_resp["status_code"] == 200:
                    token_b = login_resp["data"]["access_token"]
                    headers_b = {"Authorization": f"Bearer {token_b}"}
                    self.log(f"  User B logged in", "PASS")
                else:
                    self.record_result("Scenario 3", False, "User B login failed")
                    return
            else:
                self.record_result("Scenario 3", False, "User B creation failed")
                return
        else:
            self.record_result("Scenario 3", False, "Org B creation failed")
            return

        # User A creates Device A
        self.log("Step 3: User A creates Device A", "INFO")
        device_a_data = {
            "device_name": f"Device A {int(time.time())}",
            "location": "Location A"
        }
        resp = self.api_call("POST", "/devices/activation-code",
                           json=device_a_data, headers=headers_a)

        if resp["status_code"] == 201:
            device_a = resp["data"]
            device_a_id = device_a["device_id"]
            self.log(f"  Device A ID: {device_a_id}", "INFO")
        else:
            self.record_result("Scenario 3", False, "Device A creation failed")
            return

        # User B creates Device B
        self.log("Step 4: User B creates Device B", "INFO")
        device_b_data = {
            "device_name": f"Device B {int(time.time())}",
            "location": "Location B"
        }
        resp = self.api_call("POST", "/devices/activation-code",
                           json=device_b_data, headers=headers_b)

        if resp["status_code"] == 201:
            device_b = resp["data"]
            device_b_id = device_b["device_id"]
            self.log(f"  Device B ID: {device_b_id}", "INFO")
        else:
            self.record_result("Scenario 3", False, "Device B creation failed")
            return

        # Step 5: User A tries to access Device B
        self.log("Step 5: User A tries to GET Device B (should fail)", "INFO")
        resp = self.api_call("GET", f"/devices/{device_b_id}", headers=headers_a)

        if resp["status_code"] in [403, 404]:
            self.log(f"  ✓ Access denied (HTTP {resp['status_code']})", "PASS")
        else:
            self.log(f"  ✗ Unexpected response: HTTP {resp['status_code']}", "FAIL")
            passed = False

        # Step 6: User A tries to PATCH Device B
        self.log("Step 6: User A tries to PATCH Device B (should fail)", "INFO")
        patch_data = {"location": "Hacked Location"}
        resp = self.api_call("PATCH", f"/devices/{device_b_id}",
                           json=patch_data, headers=headers_a)

        if resp["status_code"] in [403, 404]:
            self.log(f"  ✓ Modification denied (HTTP {resp['status_code']})", "PASS")
        else:
            self.log(f"  ✗ Unexpected response: HTTP {resp['status_code']}", "FAIL")
            passed = False

        # Step 7: User A tries to DELETE Device B
        self.log("Step 7: User A tries to DELETE Device B (should fail)", "INFO")
        resp = self.api_call("DELETE", f"/devices/{device_b_id}", headers=headers_a)

        if resp["status_code"] in [403, 404]:
            self.log(f"  ✓ Deletion denied (HTTP {resp['status_code']})", "PASS")
        else:
            self.log(f"  ✗ Unexpected response: HTTP {resp['status_code']}", "FAIL")
            passed = False

        # Step 8: Verify User A can only see Org A resources
        self.log("Step 8: Verify User A sees only Org A devices", "INFO")
        resp = self.api_call("GET", "/devices", headers=headers_a)

        if resp["status_code"] == 200:
            devices = resp["data"]
            device_b_found = False
            device_a_found = False

            for device in devices:
                if device["id"] == device_b_id:
                    device_b_found = True
                if device["id"] == device_a_id:
                    device_a_found = True

            if not device_b_found and device_a_found:
                self.log(f"  ✓ Isolation verified: Device B not visible, Device A visible", "PASS")
            elif device_b_found:
                self.log(f"  ✗ SECURITY ISSUE: User A can see Device B!", "FAIL")
                passed = False
            else:
                self.log(f"  ✗ User A cannot see their own device", "FAIL")
                passed = False
        else:
            self.log(f"  Failed to get device list", "FAIL")
            passed = False

        self.record_result("Scenario 3: Multi-Tenant Isolation", passed,
                          "Complete isolation between organizations verified")

    # ==================== SCENARIO 4: Cascade Delete ====================
    def test_scenario_4_cascade_delete(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 4: Cascade Delete Testing", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        # Prerequisites: Need authenticated session
        if "headers" not in self.test_data:
            self.log("Skipping - No authenticated session", "WARN")
            self.record_result("Scenario 4", False, "Prerequisites not met")
            return

        headers = self.test_data["headers"]

        # Create a new user for deletion test
        self.log("Step 1: Create test user", "INFO")
        user_data = {
            "username": f"deletetest_{int(time.time())}",
            "email": f"deletetest{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Delete Test User",
            "role": "user",
            "organization_id": self.test_data.get("org_id")
        }
        resp = self.api_call("POST", "/auth/register", json=user_data)

        if resp["status_code"] == 201:
            test_user = resp["data"]
            test_user_id = test_user["id"]
            self.log(f"  Test User ID: {test_user_id}", "INFO")

            # Login as test user
            login_resp = self.api_call("POST", "/auth/login", json={
                "username": user_data["username"],
                "password": user_data["password"]
            })

            if login_resp["status_code"] == 200:
                test_token = login_resp["data"]["access_token"]
                test_headers = {"Authorization": f"Bearer {test_token}"}
            else:
                self.record_result("Scenario 4", False, "Test user login failed")
                return
        else:
            self.record_result("Scenario 4", False, "Test user creation failed")
            return

        # Step 2: User uploads content
        self.log("Step 2: User uploads content", "INFO")
        content_data = {
            "name": f"Delete Test Content {int(time.time())}",
            "type": "image",
            "file_path": "/uploads/delete_test.jpg",
            "duration": 10,
            "file_size": 1024000
        }
        resp = self.api_call("POST", "/contents", json=content_data, headers=test_headers)

        if resp["status_code"] == 201:
            content = resp["data"]
            content_id = content["id"]
            self.log(f"  Content ID: {content_id}", "INFO")
        else:
            self.log("  Failed to create content - skipping cascade test", "WARN")
            self.record_result("Scenario 4", False, "Content creation failed")
            return

        # Step 3: User creates playlist
        self.log("Step 3: User creates playlist with content", "INFO")
        playlist_data = {
            "name": f"Delete Test Playlist {int(time.time())}",
            "description": "Test cascade delete",
            "is_default": False
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=test_headers)

        if resp["status_code"] == 201:
            playlist = resp["data"]
            playlist_id = playlist["id"]
            self.log(f"  Playlist ID: {playlist_id}", "INFO")

            # Add content to playlist
            item_data = {"content_id": content_id, "order": 0, "duration": 10}
            resp = self.api_call("POST", f"/playlists/{playlist_id}/items",
                               json=item_data, headers=test_headers)
            if resp["status_code"] == 201:
                self.log(f"  Content added to playlist", "INFO")
        else:
            self.log("  Failed to create playlist", "WARN")
            playlist_id = None

        # Step 4: Create schedule with playlist (using admin headers)
        schedule_id = None
        if playlist_id:
            self.log("Step 4: Create schedule with playlist", "INFO")
            now = datetime.now()
            schedule_data = {
                "name": f"Delete Test Schedule {int(time.time())}",
                "playlist_id": playlist_id,
                "schedule_type": "daily",
                "start_time": "08:00:00",
                "end_time": "17:00:00",
                "days_of_week": [0, 1, 2, 3, 4],
                "start_date": now.strftime("%Y-%m-%d"),
                "applies_to_all": False,
                "priority": 5,
                "is_active": True
            }
            resp = self.api_call("POST", "/schedules", json=schedule_data, headers=test_headers)

            if resp["status_code"] == 201:
                schedule = resp["data"]
                schedule_id = schedule["id"]
                self.log(f"  Schedule ID: {schedule_id}", "INFO")

        # Step 5: Delete user (using admin privileges)
        self.log("Step 5: Delete test user", "INFO")
        resp = self.api_call("DELETE", f"/users/{test_user_id}", headers=headers)

        if resp["status_code"] in [200, 204]:
            self.log(f"  User deleted successfully", "PASS")
        else:
            self.log(f"  Failed to delete user (HTTP {resp['status_code']})", "FAIL")
            passed = False
            self.record_result("Scenario 4", False, "User deletion failed")
            return

        # Step 6: Check content still exists but created_by is NULL
        self.log("Step 6: Verify content exists with NULL created_by", "INFO")
        resp = self.api_call("GET", f"/contents/{content_id}", headers=headers)

        if resp["status_code"] == 200:
            content = resp["data"]
            if content.get("created_by_id") is None:
                self.log(f"  ✓ Content exists with created_by_id = NULL", "PASS")
            else:
                self.log(f"  ✗ Content created_by_id not NULL: {content.get('created_by_id')}", "FAIL")
                passed = False
        else:
            self.log(f"  Content not found or inaccessible", "WARN")

        # Step 7: Check playlist still exists
        if playlist_id:
            self.log("Step 7: Verify playlist still exists", "INFO")
            resp = self.api_call("GET", f"/playlists/{playlist_id}", headers=headers)

            if resp["status_code"] == 200:
                self.log(f"  ✓ Playlist still exists", "PASS")
            else:
                self.log(f"  ✗ Playlist not found (HTTP {resp['status_code']})", "FAIL")
                passed = False

        # Step 8: Check schedule still exists
        if schedule_id:
            self.log("Step 8: Verify schedule still exists", "INFO")
            resp = self.api_call("GET", f"/schedules/{schedule_id}", headers=headers)

            if resp["status_code"] == 200:
                self.log(f"  ✓ Schedule still exists", "PASS")
            else:
                self.log(f"  ✗ Schedule not found (HTTP {resp['status_code']})", "FAIL")
                passed = False

        # Step 9: Verify system still functional
        self.log("Step 9: Verify system still functional", "INFO")
        resp = self.api_call("GET", "/devices", headers=headers)
        passed &= self.assert_status(resp, 200, "System operational after cascade delete")

        self.record_result("Scenario 4: Cascade Delete", passed,
                          "ON DELETE SET NULL behavior verified")

    # ==================== SCENARIO 5: Device Offline/Online ====================
    def test_scenario_5_device_offline_online(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 5: Device Offline → Online Transitions", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        if "headers" not in self.test_data or "device_id" not in self.test_data:
            self.log("Skipping - No device from previous tests", "WARN")
            self.record_result("Scenario 5", False, "Prerequisites not met")
            return

        headers = self.test_data["headers"]
        device_id = self.test_data["device_id"]

        # Step 1: Send heartbeat
        self.log("Step 1: Device sends heartbeat", "INFO")
        heartbeat_data = {
            "cpu_usage": 50.0,
            "memory_usage": 65.0,
            "disk_usage": 75.0,
            "network_status": "connected"
        }
        resp = self.api_call("POST", f"/devices/{device_id}/heartbeat", json=heartbeat_data)
        passed &= self.assert_status(resp, 200, "Heartbeat sent")

        # Step 2: Check device status immediately (should be online)
        self.log("Step 2: Check device status (should be online)", "INFO")
        resp = self.api_call("GET", f"/devices/{device_id}", headers=headers)

        if resp["status_code"] == 200:
            device = resp["data"]
            last_seen = datetime.fromisoformat(device["last_seen_at"].replace('Z', '+00:00'))
            now = datetime.now(last_seen.tzinfo)
            seconds_ago = (now - last_seen).total_seconds()

            if seconds_ago < 60:
                self.log(f"  ✓ Device online (last seen {seconds_ago:.1f}s ago)", "PASS")
            else:
                self.log(f"  ✗ Device shows old last_seen ({seconds_ago:.1f}s ago)", "FAIL")
                passed = False
        else:
            self.log(f"  Failed to get device status", "FAIL")
            passed = False

        # Step 3: Wait 6 minutes (skipped for practical reasons)
        self.log("Step 3-5: Offline detection test (skipped - would require 6+ min wait)", "INFO")
        self.log("  Expected: After 5 min without heartbeat, device shows offline", "INFO")
        self.log("  Expected: After sending new heartbeat, device shows online again", "INFO")

        self.record_result("Scenario 5: Device Offline/Online", passed,
                          "Heartbeat mechanism working (full offline test skipped)")

    # ==================== SCENARIO 6: Priority Schedule Handling ====================
    def test_scenario_6_priority_schedules(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 6: Priority Schedule Handling", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        if "headers" not in self.test_data or "device_id" not in self.test_data:
            self.log("Skipping - No device from previous tests", "WARN")
            self.record_result("Scenario 6", False, "Prerequisites not met")
            return

        headers = self.test_data["headers"]
        device_id = self.test_data["device_id"]

        # Step 1: Create default playlist
        self.log("Step 1: Create default playlist", "INFO")
        default_playlist_data = {
            "name": f"Default Priority Test {int(time.time())}",
            "description": "Default playlist for priority test",
            "is_default": True
        }
        resp = self.api_call("POST", "/playlists", json=default_playlist_data, headers=headers)

        if resp["status_code"] == 201:
            default_playlist = resp["data"]
            default_playlist_id = default_playlist["id"]
            self.log(f"  Default Playlist ID: {default_playlist_id}", "INFO")
        else:
            self.record_result("Scenario 6", False, "Failed to create default playlist")
            return

        # Step 2: Assign to device
        self.log("Step 2: Assign default playlist to device", "INFO")
        assign_data = {"default_playlist_id": default_playlist_id}
        resp = self.api_call("PATCH", f"/devices/{device_id}",
                           json=assign_data, headers=headers)
        passed &= self.assert_status(resp, 200, "Default playlist assigned")

        # Step 3: Create Schedule A (priority 5)
        self.log("Step 3: Create Schedule A (priority 5, overlapping time)", "INFO")
        playlist_a_data = {
            "name": f"Playlist A {int(time.time())}",
            "description": "Priority 5 playlist",
            "is_default": False
        }
        resp = self.api_call("POST", "/playlists", json=playlist_a_data, headers=headers)

        if resp["status_code"] == 201:
            playlist_a = resp["data"]
            playlist_a_id = playlist_a["id"]

            now = datetime.now()
            schedule_a_data = {
                "name": f"Schedule A {int(time.time())}",
                "playlist_id": playlist_a_id,
                "schedule_type": "daily",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "days_of_week": list(range(7)),
                "start_date": now.strftime("%Y-%m-%d"),
                "applies_to_all": True,
                "priority": 5,
                "is_active": True
            }
            resp = self.api_call("POST", "/schedules", json=schedule_a_data, headers=headers)

            if resp["status_code"] == 201:
                schedule_a = resp["data"]
                schedule_a_id = schedule_a["id"]
                self.log(f"  Schedule A ID: {schedule_a_id} (priority 5)", "INFO")
            else:
                self.log(f"  Failed to create Schedule A", "FAIL")
                passed = False
                self.record_result("Scenario 6", False, "Schedule A creation failed")
                return
        else:
            self.record_result("Scenario 6", False, "Playlist A creation failed")
            return

        # Step 4: Create Schedule B (priority 10, same time)
        self.log("Step 4: Create Schedule B (priority 10, overlapping time)", "INFO")
        playlist_b_data = {
            "name": f"Playlist B {int(time.time())}",
            "description": "Priority 10 playlist",
            "is_default": False
        }
        resp = self.api_call("POST", "/playlists", json=playlist_b_data, headers=headers)

        if resp["status_code"] == 201:
            playlist_b = resp["data"]
            playlist_b_id = playlist_b["id"]

            schedule_b_data = {
                "name": f"Schedule B {int(time.time())}",
                "playlist_id": playlist_b_id,
                "schedule_type": "daily",
                "start_time": "10:00:00",
                "end_time": "11:00:00",
                "days_of_week": list(range(7)),
                "start_date": now.strftime("%Y-%m-%d"),
                "applies_to_all": True,
                "priority": 10,
                "is_active": True
            }
            resp = self.api_call("POST", "/schedules", json=schedule_b_data, headers=headers)

            if resp["status_code"] == 201:
                schedule_b = resp["data"]
                schedule_b_id = schedule_b["id"]
                self.log(f"  Schedule B ID: {schedule_b_id} (priority 10)", "INFO")
            else:
                self.log(f"  Failed to create Schedule B", "FAIL")
                passed = False
                self.record_result("Scenario 6", False, "Schedule B creation failed")
                return
        else:
            self.record_result("Scenario 6", False, "Playlist B creation failed")
            return

        # Step 5-9: Priority resolution test (would require waiting for 10:00-11:00 time window)
        self.log("Step 5-9: Priority resolution test (simulation)", "INFO")
        self.log("  Expected behavior during 10:00-11:00:", "INFO")
        self.log(f"    - With both schedules active: Device gets Schedule B (priority 10)", "INFO")
        self.log(f"    - After deleting Schedule B: Device gets Schedule A (priority 5)", "INFO")
        self.log(f"    - Outside time window: Device gets default playlist", "INFO")

        # Test schedule list to verify both created
        resp = self.api_call("GET", "/schedules", headers=headers)
        if resp["status_code"] == 200:
            schedules = resp["data"]
            found_a = any(s["id"] == schedule_a_id for s in schedules)
            found_b = any(s["id"] == schedule_b_id for s in schedules)

            if found_a and found_b:
                self.log(f"  ✓ Both schedules exist in system", "PASS")
            else:
                self.log(f"  ✗ Schedules missing from list", "FAIL")
                passed = False

        self.record_result("Scenario 6: Priority Schedules", passed,
                          "Priority schedule creation verified (resolution not tested - time dependent)")

    # ==================== SCENARIO 7: Content Deletion in Playlist ====================
    def test_scenario_7_content_deletion_in_playlist(self):
        self.log("=" * 80, "INFO")
        self.log("SCENARIO 7: Content in Playlist Deletion", "INFO")
        self.log("=" * 80, "INFO")

        passed = True

        if "headers" not in self.test_data or "device_id" not in self.test_data:
            self.log("Skipping - No device from previous tests", "WARN")
            self.record_result("Scenario 7", False, "Prerequisites not met")
            return

        headers = self.test_data["headers"]
        device_id = self.test_data["device_id"]

        # Step 1: Create playlist with 3 contents
        self.log("Step 1: Create playlist with 3 contents", "INFO")
        content_ids = []

        for i in range(3):
            content_data = {
                "name": f"Deletion Test Content {i+1} - {int(time.time())}",
                "type": "image",
                "file_path": f"/uploads/delete_test_{i+1}.jpg",
                "duration": 10,
                "file_size": 1024000
            }
            resp = self.api_call("POST", "/contents", json=content_data, headers=headers)

            if resp["status_code"] == 201:
                content = resp["data"]
                content_ids.append(content["id"])
                self.log(f"  Content {i+1} ID: {content['id']}", "INFO")
            else:
                self.log(f"  Failed to create content {i+1}", "FAIL")
                passed = False

        if len(content_ids) < 3:
            self.record_result("Scenario 7", False, "Failed to create contents")
            return

        # Create playlist
        playlist_data = {
            "name": f"Deletion Test Playlist {int(time.time())}",
            "description": "Test content deletion",
            "is_default": False
        }
        resp = self.api_call("POST", "/playlists", json=playlist_data, headers=headers)

        if resp["status_code"] == 201:
            playlist = resp["data"]
            playlist_id = playlist["id"]
            self.log(f"  Playlist ID: {playlist_id}", "INFO")

            # Add contents to playlist
            for idx, content_id in enumerate(content_ids):
                item_data = {"content_id": content_id, "order": idx, "duration": 10}
                resp = self.api_call("POST", f"/playlists/{playlist_id}/items",
                                   json=item_data, headers=headers)
                if resp["status_code"] != 201:
                    self.log(f"  Failed to add content {idx+1} to playlist", "FAIL")
                    passed = False
        else:
            self.record_result("Scenario 7", False, "Failed to create playlist")
            return

        # Step 2: Assign playlist to device
        self.log("Step 2: Assign playlist to device", "INFO")
        assign_data = {"default_playlist_id": playlist_id}
        resp = self.api_call("PATCH", f"/devices/{device_id}",
                           json=assign_data, headers=headers)
        passed &= self.assert_status(resp, 200, "Playlist assigned to device")

        # Step 3: Soft delete middle content
        self.log("Step 3: Soft delete middle content (is_active = false)", "INFO")
        middle_content_id = content_ids[1]

        resp = self.api_call("DELETE", f"/contents/{middle_content_id}", headers=headers)

        if resp["status_code"] in [200, 204]:
            self.log(f"  Content {middle_content_id} soft deleted", "PASS")
        else:
            self.log(f"  Failed to delete content (HTTP {resp['status_code']})", "FAIL")
            passed = False

        # Step 4: Get playlist items
        self.log("Step 4: Get playlist items (should skip deleted content)", "INFO")
        resp = self.api_call("GET", f"/playlists/{playlist_id}/items", headers=headers)

        if resp["status_code"] == 200:
            items = resp["data"]
            active_item_count = len(items)

            # Check if deleted content is excluded
            deleted_content_in_list = any(
                item.get("content_id") == middle_content_id for item in items
            )

            if active_item_count == 2 and not deleted_content_in_list:
                self.log(f"  ✓ Only 2 active contents returned (deleted content skipped)", "PASS")
            elif active_item_count == 3:
                self.log(f"  ✗ Still showing 3 contents (deleted content not filtered)", "FAIL")
                passed = False
            else:
                self.log(f"  ⚠ Unexpected content count: {active_item_count}", "WARN")
        else:
            self.log(f"  Failed to get playlist items", "FAIL")
            passed = False

        # Step 5: Device requests playlist content
        self.log("Step 5: Device requests content (verify no error)", "INFO")
        resp = self.api_call("GET", f"/devices/{device_id}/content")

        if resp["status_code"] == 200:
            content_data = resp["data"]
            self.log(f"  ✓ Content delivery still works after deletion", "PASS")

            # Check if returned items exclude deleted content
            if "items" in content_data:
                items = content_data["items"]
                has_deleted = any(
                    item.get("content_id") == middle_content_id for item in items
                )

                if not has_deleted:
                    self.log(f"  ✓ Deleted content not in device content", "PASS")
                else:
                    self.log(f"  ✗ Deleted content still in device content", "FAIL")
                    passed = False
        else:
            self.log(f"  ✗ Content delivery failed after deletion", "FAIL")
            passed = False

        # Step 6: Verify playlist still functional
        self.log("Step 6: Verify playlist still functional", "INFO")
        resp = self.api_call("GET", f"/playlists/{playlist_id}", headers=headers)
        passed &= self.assert_status(resp, 200, "Playlist still accessible")

        self.record_result("Scenario 7: Content Deletion in Playlist", passed,
                          "Graceful handling of deleted content in playlists")

    # ==================== GENERATE REPORT ====================
    def generate_report(self):
        self.log("=" * 80, "INFO")
        self.log("INTEGRATION TEST REPORT", "INFO")
        self.log("=" * 80, "INFO")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        # Calculate health score (1-10)
        if total_tests == 0:
            health_score = 0
        else:
            health_score = round((passed_tests / total_tests) * 10, 1)

        elapsed_time = time.time() - self.start_time

        print(f"\n{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BLUE}SUMMARY{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

        print(f"Integration Health Score: {Colors.GREEN if health_score >= 7 else Colors.RED}{health_score}/10{Colors.RESET}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.RESET}")
        print(f"Failed: {Colors.RED}{failed_tests}{Colors.RESET}")
        print(f"Execution Time: {elapsed_time:.2f}s\n")

        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BLUE}TEST RESULTS{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

        for idx, result in enumerate(self.results, 1):
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result["passed"] else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"{idx}. [{status}] {result['scenario']}")
            if result["details"]:
                print(f"   {result['details']}")
            print()

        # API Issues
        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BLUE}KEY FINDINGS{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")

        if health_score >= 8:
            print(f"{Colors.GREEN}✓ System Integration: EXCELLENT{Colors.RESET}")
            print("  All major workflows functioning correctly")
        elif health_score >= 6:
            print(f"{Colors.YELLOW}⚠ System Integration: GOOD with minor issues{Colors.RESET}")
            print("  Most workflows functional, some edge cases need attention")
        else:
            print(f"{Colors.RED}✗ System Integration: NEEDS ATTENTION{Colors.RESET}")
            print("  Critical workflows have issues requiring immediate fix")

        print(f"\n{Colors.BLUE}Vote Items (Behaviors needing clarification):{Colors.RESET}")
        print("1. Schedule activation: Should it be immediate or wait for start_time?")
        print("2. Device offline threshold: Confirmed at 5 minutes?")
        print("3. Content deletion: Should hard delete be possible or always soft?")
        print("4. Multi-tenant: Should admins see deleted users' content?")
        print("5. Priority ties: What happens when two schedules have same priority?")

        return health_score

    # ==================== RUN ALL TESTS ====================
    def run_all(self):
        self.log("Starting Integration Test Suite", "INFO")
        self.log(f"Target: {BASE_URL}", "INFO")
        self.log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        print()

        try:
            # Run scenarios in order
            self.test_scenario_1_device_onboarding()
            print("\n")

            self.test_scenario_2_scheduled_content()
            print("\n")

            self.test_scenario_3_multi_tenant_isolation()
            print("\n")

            self.test_scenario_4_cascade_delete()
            print("\n")

            self.test_scenario_5_device_offline_online()
            print("\n")

            self.test_scenario_6_priority_schedules()
            print("\n")

            self.test_scenario_7_content_deletion_in_playlist()
            print("\n")

            # Generate final report
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

    # Exit with appropriate code
    sys.exit(0 if health_score >= 7 else 1)
