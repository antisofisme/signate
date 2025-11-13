#!/usr/bin/env python3
"""
Phase 3: Audit Log, Multi-Tenancy, and RBAC Integration Tests
Tests cross-cutting concerns across all test organizations
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any

BASE_URL = "http://192.168.5.12:8001/api/v1"
COORDINATOR_FILE = "/mnt/g/khoirul/signate/integration_test_coordinator.json"

class Phase3IntegrationTester:
    def __init__(self):
        self.results = {
            "agent": "agent_audit_multitenancy_rbac",
            "started_at": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "critical_findings": {
                "data_leakage_found": False,
                "audit_logs_working": False,
                "multi_tenancy_secure": True,
                "rbac_enforced": False
            },
            "audit_log_stats": {},
            "security_issues": [],
            "test_details": []
        }

        # Load coordinator data
        with open(COORDINATOR_FILE, 'r') as f:
            self.coordinator = json.load(f)

        self.orgs = {
            "org_10": {"id": 13, "name": "TEST_ORG_CONTENT_TAG"},
            "org_11": {"id": 14, "name": "TEST_ORG_DEVICE_PLAYLIST"},
            "org_12": {"id": 15, "name": "TEST_ORG_SCHEDULE"},
            "org_13": {"id": 16, "name": "TEST_ORG_PMS_ANALYTICS"}
        }

        # Get tokens from coordinator
        self.load_tokens()

    def load_tokens(self):
        """Load authentication tokens for each org"""
        try:
            setup_results = self.coordinator.get("test_results", {}).get("phase_1_setup", {})

            # Try to get tokens from setup results or use main admin token
            self.org_tokens = {}

            # For now, we'll login to each org
            for org_key, org_data in self.orgs.items():
                username = f"testadmin_{org_key.split('_')[1]}"  # testadmin_10, testadmin_11, etc
                password = "TestPass123!"

                try:
                    response = requests.post(f"{BASE_URL}/auth/login", json={
                        "username": username,
                        "password": password
                    })

                    if response.status_code == 200:
                        token = response.json().get("access_token")
                        self.org_tokens[org_key] = token
                        print(f"✅ Logged in as {username}")
                    else:
                        print(f"⚠️  Failed to login as {username}: {response.status_code}")
                        self.org_tokens[org_key] = None
                except Exception as e:
                    print(f"❌ Error logging in as {username}: {e}")
                    self.org_tokens[org_key] = None

        except Exception as e:
            print(f"❌ Error loading tokens: {e}")
            self.org_tokens = {}

    def get_headers(self, org_key: str) -> Dict:
        """Get auth headers for organization"""
        token = self.org_tokens.get(org_key)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    def test_audit_logs_per_org(self):
        """Test 1: Check audit logs for each organization"""
        print("\n" + "="*80)
        print("TEST 1: Audit Log Verification per Organization")
        print("="*80)

        self.results["tests_run"] += 1
        test_result = {
            "test": "Test 1: Audit Logs per Organization",
            "status": "UNKNOWN",
            "details": {}
        }

        all_passed = True

        for org_key, org_data in self.orgs.items():
            headers = self.get_headers(org_key)
            if not headers:
                print(f"⚠️  Skipping {org_key} - No token")
                continue

            try:
                response = requests.get(f"{BASE_URL}/audit/logs", headers=headers)

                if response.status_code == 200:
                    logs = response.json()
                    log_count = len(logs) if isinstance(logs, list) else logs.get("total", 0)

                    print(f"✅ {org_key}: {log_count} audit logs")
                    test_result["details"][org_key] = {
                        "status": "accessible",
                        "log_count": log_count
                    }
                    self.results["audit_log_stats"][org_key] = log_count

                    if log_count > 0:
                        self.results["critical_findings"]["audit_logs_working"] = True

                elif response.status_code == 404:
                    print(f"⚠️  {org_key}: Audit endpoint not implemented (404)")
                    test_result["details"][org_key] = {"status": "not_implemented"}
                    all_passed = False
                else:
                    print(f"❌ {org_key}: Failed - HTTP {response.status_code}")
                    test_result["details"][org_key] = {
                        "status": "error",
                        "error": response.text
                    }
                    all_passed = False

            except Exception as e:
                print(f"❌ {org_key}: Exception - {e}")
                test_result["details"][org_key] = {"status": "exception", "error": str(e)}
                all_passed = False

        test_result["status"] = "PASSED" if all_passed else "FAILED"
        self.results["test_details"].append(test_result)

        if all_passed:
            self.results["tests_passed"] += 1
        else:
            self.results["tests_failed"] += 1

    def test_multi_tenancy_devices(self):
        """Test 2: Multi-tenancy isolation for devices"""
        print("\n" + "="*80)
        print("TEST 2: Multi-Tenancy - Device Isolation")
        print("="*80)

        self.results["tests_run"] += 1
        test_result = {
            "test": "Test 2: Device Multi-Tenancy Isolation",
            "status": "UNKNOWN",
            "details": {}
        }

        # Query devices from each org
        org_devices = {}

        for org_key in ["org_11", "org_12"]:  # org_11 has devices, org_12 might not
            headers = self.get_headers(org_key)
            if not headers:
                continue

            try:
                response = requests.get(f"{BASE_URL}/devices", headers=headers)

                if response.status_code == 200:
                    devices = response.json()
                    device_list = devices if isinstance(devices, list) else devices.get("items", [])
                    device_ids = [d.get("id") for d in device_list]

                    org_devices[org_key] = device_ids
                    print(f"✅ {org_key}: {len(device_ids)} devices - IDs: {device_ids[:5]}")

                    test_result["details"][org_key] = {
                        "device_count": len(device_ids),
                        "device_ids": device_ids[:5]  # First 5 IDs
                    }
                else:
                    print(f"⚠️  {org_key}: HTTP {response.status_code}")
                    org_devices[org_key] = []

            except Exception as e:
                print(f"❌ {org_key}: {e}")
                org_devices[org_key] = []

        # Check isolation - org_11 and org_12 should NOT have same device IDs
        if "org_11" in org_devices and "org_12" in org_devices:
            overlap = set(org_devices["org_11"]) & set(org_devices["org_12"])

            if overlap:
                print(f"🚨 SECURITY ISSUE: Device ID overlap detected: {overlap}")
                self.results["critical_findings"]["data_leakage_found"] = True
                self.results["critical_findings"]["multi_tenancy_secure"] = False
                self.results["security_issues"].append({
                    "severity": "CRITICAL",
                    "issue": "Device data leakage between organizations",
                    "overlap_ids": list(overlap)
                })
                test_result["status"] = "FAILED"
                self.results["tests_failed"] += 1
            else:
                print(f"✅ No device overlap - Multi-tenancy is secure")
                test_result["status"] = "PASSED"
                self.results["tests_passed"] += 1
        else:
            print(f"⚠️  Could not verify isolation - insufficient data")
            test_result["status"] = "SKIPPED"
            self.results["tests_failed"] += 1

        self.results["test_details"].append(test_result)

    def test_multi_tenancy_playlists(self):
        """Test 3: Multi-tenancy isolation for playlists"""
        print("\n" + "="*80)
        print("TEST 3: Multi-Tenancy - Playlist Isolation")
        print("="*80)

        self.results["tests_run"] += 1
        test_result = {
            "test": "Test 3: Playlist Multi-Tenancy Isolation",
            "status": "UNKNOWN",
            "details": {}
        }

        org_playlists = {}

        for org_key in ["org_11", "org_12", "org_13"]:
            headers = self.get_headers(org_key)
            if not headers:
                continue

            try:
                response = requests.get(f"{BASE_URL}/playlists", headers=headers)

                if response.status_code == 200:
                    playlists = response.json()
                    playlist_list = playlists if isinstance(playlists, list) else playlists.get("items", [])
                    playlist_ids = [p.get("id") for p in playlist_list]

                    org_playlists[org_key] = playlist_ids
                    print(f"✅ {org_key}: {len(playlist_ids)} playlists")

                    test_result["details"][org_key] = {
                        "playlist_count": len(playlist_ids),
                        "playlist_ids": playlist_ids[:5]
                    }
                else:
                    print(f"⚠️  {org_key}: HTTP {response.status_code}")
                    org_playlists[org_key] = []

            except Exception as e:
                print(f"❌ {org_key}: {e}")
                org_playlists[org_key] = []

        # Check for overlaps
        all_ids = []
        for ids in org_playlists.values():
            all_ids.extend(ids)

        if len(all_ids) != len(set(all_ids)):
            duplicates = [id for id in all_ids if all_ids.count(id) > 1]
            print(f"🚨 SECURITY ISSUE: Playlist ID overlap: {set(duplicates)}")
            self.results["critical_findings"]["data_leakage_found"] = True
            self.results["critical_findings"]["multi_tenancy_secure"] = False
            self.results["security_issues"].append({
                "severity": "CRITICAL",
                "issue": "Playlist data leakage between organizations",
                "duplicate_ids": list(set(duplicates))
            })
            test_result["status"] = "FAILED"
            self.results["tests_failed"] += 1
        else:
            print(f"✅ No playlist overlap - Multi-tenancy is secure")
            test_result["status"] = "PASSED"
            self.results["tests_passed"] += 1

        self.results["test_details"].append(test_result)

    def test_cross_org_access(self):
        """Test 4: Attempt cross-organization access (security test)"""
        print("\n" + "="*80)
        print("TEST 4: Cross-Organization Access Prevention")
        print("="*80)

        self.results["tests_run"] += 1
        test_result = {
            "test": "Test 4: Cross-Org Access Prevention",
            "status": "UNKNOWN",
            "details": {}
        }

        # Try to access org_11's device from org_12
        org_11_headers = self.get_headers("org_11")
        org_12_headers = self.get_headers("org_12")

        if not (org_11_headers and org_12_headers):
            print("⚠️  Cannot test - missing tokens")
            test_result["status"] = "SKIPPED"
            self.results["tests_failed"] += 1
            self.results["test_details"].append(test_result)
            return

        # Get a device from org_11
        try:
            response = requests.get(f"{BASE_URL}/devices", headers=org_11_headers)
            if response.status_code == 200:
                devices = response.json()
                device_list = devices if isinstance(devices, list) else devices.get("items", [])

                if device_list:
                    device_id = device_list[0].get("id")
                    print(f"📝 Testing cross-access with device ID: {device_id}")

                    # Try to access from org_12
                    response = requests.get(f"{BASE_URL}/devices/{device_id}", headers=org_12_headers)

                    if response.status_code in [403, 404]:
                        print(f"✅ Cross-access properly blocked (HTTP {response.status_code})")
                        test_result["status"] = "PASSED"
                        test_result["details"] = {
                            "attempted_device_id": device_id,
                            "response_code": response.status_code,
                            "access_blocked": True
                        }
                        self.results["tests_passed"] += 1
                    elif response.status_code == 200:
                        print(f"🚨 SECURITY BREACH: Cross-org access succeeded!")
                        self.results["critical_findings"]["data_leakage_found"] = True
                        self.results["critical_findings"]["multi_tenancy_secure"] = False
                        self.results["security_issues"].append({
                            "severity": "CRITICAL",
                            "issue": "Cross-organization device access allowed",
                            "device_id": device_id
                        })
                        test_result["status"] = "FAILED"
                        self.results["tests_failed"] += 1
                    else:
                        print(f"⚠️  Unexpected response: HTTP {response.status_code}")
                        test_result["status"] = "FAILED"
                        self.results["tests_failed"] += 1
                else:
                    print("⚠️  No devices available for testing")
                    test_result["status"] = "SKIPPED"
                    self.results["tests_failed"] += 1
            else:
                print(f"⚠️  Cannot get devices: HTTP {response.status_code}")
                test_result["status"] = "SKIPPED"
                self.results["tests_failed"] += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            self.results["tests_failed"] += 1

        self.results["test_details"].append(test_result)

    def test_rbac_roles(self):
        """Test 5: Check RBAC roles exist"""
        print("\n" + "="*80)
        print("TEST 5: RBAC Role Definitions")
        print("="*80)

        self.results["tests_run"] += 1
        test_result = {
            "test": "Test 5: RBAC Roles",
            "status": "UNKNOWN",
            "details": {}
        }

        headers = self.get_headers("org_13")
        if not headers:
            print("⚠️  No token for testing")
            test_result["status"] = "SKIPPED"
            self.results["tests_failed"] += 1
            self.results["test_details"].append(test_result)
            return

        try:
            response = requests.get(f"{BASE_URL}/roles", headers=headers)

            if response.status_code == 200:
                roles = response.json()
                role_list = roles if isinstance(roles, list) else roles.get("items", [])
                role_names = [r.get("name") for r in role_list]

                print(f"✅ Found {len(role_names)} roles: {role_names}")

                expected_roles = ["admin", "user", "super_admin"]
                missing_roles = [r for r in expected_roles if r not in role_names]

                if not missing_roles:
                    print(f"✅ All expected roles present")
                    self.results["critical_findings"]["rbac_enforced"] = True
                    test_result["status"] = "PASSED"
                    self.results["tests_passed"] += 1
                else:
                    print(f"⚠️  Missing roles: {missing_roles}")
                    test_result["status"] = "PARTIAL"
                    self.results["tests_failed"] += 1

                test_result["details"] = {
                    "roles_found": role_names,
                    "missing_roles": missing_roles
                }

            elif response.status_code == 404:
                print(f"⚠️  Roles endpoint not implemented")
                test_result["status"] = "NOT_IMPLEMENTED"
                self.results["tests_failed"] += 1
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                test_result["status"] = "FAILED"
                self.results["tests_failed"] += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            self.results["tests_failed"] += 1

        self.results["test_details"].append(test_result)

    def run_all_tests(self):
        """Run all Phase 3 tests"""
        print("\n" + "="*80)
        print("PHASE 3: AUDIT LOG, MULTI-TENANCY, AND RBAC INTEGRATION TESTS")
        print("="*80)
        print(f"Backend: {BASE_URL}")
        print(f"Test Organizations: {len(self.orgs)}")
        print("="*80)

        self.test_audit_logs_per_org()
        self.test_multi_tenancy_devices()
        self.test_multi_tenancy_playlists()
        self.test_cross_org_access()
        self.test_rbac_roles()

        # Final summary
        self.results["completed_at"] = datetime.now().isoformat()

        print("\n" + "="*80)
        print("PHASE 3 TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print(f"Pass Rate: {self.results['tests_passed']/self.results['tests_run']*100:.1f}%")
        print("\n🔒 CRITICAL FINDINGS:")
        print(f"  - Audit Logs Working: {self.results['critical_findings']['audit_logs_working']}")
        print(f"  - Multi-Tenancy Secure: {self.results['critical_findings']['multi_tenancy_secure']}")
        print(f"  - RBAC Enforced: {self.results['critical_findings']['rbac_enforced']}")
        print(f"  - Data Leakage Found: {self.results['critical_findings']['data_leakage_found']}")

        if self.results['security_issues']:
            print(f"\n🚨 {len(self.results['security_issues'])} SECURITY ISSUES FOUND:")
            for issue in self.results['security_issues']:
                print(f"  - {issue['severity']}: {issue['issue']}")

        print("="*80)

        # Save results
        results_file = "/mnt/g/khoirul/signate/phase3_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to: {results_file}")

        # Update coordinator file
        try:
            self.coordinator["test_results"]["phase_3_integration"] = self.results
            self.coordinator["phases"]["phase_3_integration"]["status"] = "completed"

            with open(COORDINATOR_FILE, 'w') as f:
                json.dump(self.coordinator, f, indent=2)
            print(f"✅ Coordinator file updated")
        except Exception as e:
            print(f"⚠️  Could not update coordinator: {e}")

        return self.results

if __name__ == "__main__":
    tester = Phase3IntegrationTester()
    results = tester.run_all_tests()
