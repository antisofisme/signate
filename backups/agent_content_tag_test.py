#!/usr/bin/env python3
"""
Integration Test Agent: Content + Tag
Scope: TEST_ORG_CONTENT_TAG (org_10)
"""

import requests
import json
import sys
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://192.168.5.12:8001"
COORDINATOR_FILE = "/mnt/g/khoirul/signage/integration_test_coordinator.json"
TEST_IMAGE = "/mnt/g/khoirul/signage/contoh_media/image1.jpg"

# Test organization details - using timestamp to make unique
import time
_timestamp = int(time.time())
ORG_NAME = f"TEST_ORG_CONTENT_TAG_{_timestamp}"
ORG_ADMIN_USERNAME = f"admin_content_tag_{_timestamp}"
ORG_ADMIN_PASSWORD = "TestPass123!"
ORG_ADMIN_EMAIL = f"admin_content_tag_{_timestamp}@test.com"

class ContentTagTestAgent:
    def __init__(self):
        self.session = requests.Session()
        self.org_id = None
        self.admin_token = None
        self.user_id = None
        self.results = {
            "agent": "agent_content_tag",
            "org_id": None,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "audit_logs_verified": False,
            "created_resources": {
                "content_ids": [],
                "tag_ids": []
            },
            "test_details": []
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def check_phase_1_status(self):
        """Check if Phase 1 setup is completed"""
        try:
            with open(COORDINATOR_FILE, 'r') as f:
                data = json.load(f)
                status = data['phases']['phase_1_setup']['status']
                self.log(f"Phase 1 status: {status}")
                return status == "completed"
        except Exception as e:
            self.log(f"Error checking Phase 1 status: {e}", "ERROR")
            return False

    def setup_organization(self):
        """Setup test organization and admin user"""
        self.log("Setting up test organization...")

        # Register organization
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/auth/register", json={
                "username": ORG_ADMIN_USERNAME,
                "email": ORG_ADMIN_EMAIL,
                "password": ORG_ADMIN_PASSWORD,
                
                "full_name": "Content Tag Test Admin"
            })

            if response.status_code == 201:
                data = response.json()
                # Extract user info from response
                if 'data' in data:
                    user_data = data['data']
                    self.user_id = user_data['id']
                    self.org_id = user_data['organization_id']
                    self.results['org_id'] = self.org_id
                    self.log(f"✓ User created: ID={self.user_id}, Org={self.org_id}")
                else:
                    self.log(f"✗ Unexpected response format: {data}", "ERROR")
                    return False

                # Now login to get access token
                login_response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
                    "username": ORG_ADMIN_USERNAME,
                    "password": ORG_ADMIN_PASSWORD
                })

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if 'data' in login_data and 'access_token' in login_data['data']:
                        self.admin_token = login_data['data']['access_token']
                        self.log(f"✓ Login successful, token obtained")
                        return True
                    else:
                        self.log(f"✗ Login response missing token: {login_data}", "ERROR")
                        return False
                else:
                    self.log(f"✗ Login failed: {login_response.status_code} - {login_response.text}", "ERROR")
                    return False
            else:
                self.log(f"✗ Failed to create organization: {response.status_code} - {response.text}", "ERROR")
                return False

        except Exception as e:
            self.log(f"✗ Exception during organization setup: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False

    def update_coordinator_file(self, phase_1_complete=False):
        """Update coordinator file with org info and token"""
        try:
            with open(COORDINATOR_FILE, 'r') as f:
                data = json.load(f)

            # Update org info
            data['test_organizations']['org_10']['org_id'] = self.org_id
            data['test_organizations']['org_10']['admin_token'] = self.admin_token
            data['test_organizations']['org_10']['user_id'] = self.user_id

            # If Phase 1 is complete, update status
            if phase_1_complete:
                data['phases']['phase_1_setup']['status'] = 'completed'
                data['phases']['phase_1_setup']['completed_at'] = datetime.now().isoformat()

            with open(COORDINATOR_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            self.log("✓ Coordinator file updated")
            return True

        except Exception as e:
            self.log(f"✗ Failed to update coordinator file: {e}", "ERROR")
            return False

    def create_tags(self):
        """Create test tags"""
        self.log("Creating test tags...")
        tag_names = ["Video Content", "Promotional", "Important"]
        tag_ids = []

        headers = {"Authorization": f"Bearer {self.admin_token}"}

        for name in tag_names:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/v1/tags/",
                    headers=headers,
                    json={"name": name, "color": "#FF5733"}
                )

                if response.status_code == 201:
                    tag_id = response.json()['id']
                    tag_ids.append(tag_id)
                    self.log(f"✓ Tag created: {name} (ID={tag_id})")
                else:
                    self.log(f"✗ Failed to create tag {name}: {response.status_code}", "ERROR")

            except Exception as e:
                self.log(f"✗ Exception creating tag {name}: {e}", "ERROR")

        self.results['created_resources']['tag_ids'] = tag_ids
        return tag_ids

    def test_1_content_creation_with_tags(self, tag_ids):
        """Test 1: Create contents with different tag combinations"""
        self.log("\n=== TEST 1: Content Creation with Tags ===")
        self.results['tests_run'] += 1

        test_passed = True
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Define content configurations
        contents = [
            {"name": "Content A", "tags": [tag_ids[0], tag_ids[1]]},
            {"name": "Content B", "tags": [tag_ids[1], tag_ids[2]]},
            {"name": "Content C", "tags": [tag_ids[0], tag_ids[2]]}
        ]

        content_ids = []

        for content_config in contents:
            try:
                # Check if test image exists
                if not Path(TEST_IMAGE).exists():
                    self.log(f"✗ Test image not found: {TEST_IMAGE}", "ERROR")
                    test_passed = False
                    continue

                # Upload content with tags
                with open(TEST_IMAGE, 'rb') as f:
                    files = {'file': ('test_image.jpg', f, 'image/jpeg')}
                    data = {
                        'name': content_config['name'],
                        'duration': '10',
                        'tag_ids': json.dumps(content_config['tags'])
                    }

                    response = self.session.post(
                        f"{BASE_URL}/api/v1/contents/upload",
                        headers=headers,
                        files=files,
                        data=data
                    )

                if response.status_code == 201:
                    content = response.json()
                    content_id = content['id']
                    content_ids.append(content_id)
                    self.log(f"✓ Created {content_config['name']}: ID={content_id}, tags={content_config['tags']}")

                    # Verify tags are associated
                    if 'tags' in content and len(content['tags']) == len(content_config['tags']):
                        self.log(f"  ✓ Tags correctly associated")
                    else:
                        self.log(f"  ✗ Tags mismatch!", "ERROR")
                        test_passed = False
                else:
                    self.log(f"✗ Failed to create {content_config['name']}: {response.status_code} - {response.text}", "ERROR")
                    test_passed = False

            except Exception as e:
                self.log(f"✗ Exception creating {content_config['name']}: {e}", "ERROR")
                test_passed = False

        self.results['created_resources']['content_ids'] = content_ids

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 1 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 1: Content creation with tags failed")
            self.log("✗ TEST 1 FAILED")

        self.results['test_details'].append({
            "test": "Content Creation with Tags",
            "passed": test_passed,
            "content_ids": content_ids
        })

        return content_ids

    def test_2_tag_based_content_query(self, tag_ids, content_ids):
        """Test 2: Query contents by tag"""
        self.log("\n=== TEST 2: Tag-Based Content Query ===")
        self.results['tests_run'] += 1

        test_passed = True
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Expected results based on our setup:
        # Content A: tags [0, 1] -> should appear in queries for tag 0 and tag 1
        # Content B: tags [1, 2] -> should appear in queries for tag 1 and tag 2
        # Content C: tags [0, 2] -> should appear in queries for tag 0 and tag 2

        test_cases = [
            {"tag_id": tag_ids[0], "expected_contents": [0, 2], "description": "Tag 0 (Video Content)"},
            {"tag_id": tag_ids[1], "expected_contents": [0, 1], "description": "Tag 1 (Promotional)"},
            {"tag_id": tag_ids[2], "expected_contents": [1, 2], "description": "Tag 2 (Important)"}
        ]

        for test_case in test_cases:
            try:
                response = self.session.get(
                    f"{BASE_URL}/api/v1/contents/",
                    headers=headers,
                    params={"tag_id": test_case['tag_id']}
                )

                if response.status_code == 200:
                    contents = response.json()
                    found_ids = [c['id'] for c in contents]
                    expected_ids = [content_ids[i] for i in test_case['expected_contents']]

                    # Check if expected contents are in results
                    all_found = all(eid in found_ids for eid in expected_ids)

                    if all_found:
                        self.log(f"✓ Query {test_case['description']}: Found {len(expected_ids)} expected contents")
                    else:
                        self.log(f"✗ Query {test_case['description']}: Missing expected contents", "ERROR")
                        self.log(f"  Expected: {expected_ids}", "ERROR")
                        self.log(f"  Found: {found_ids}", "ERROR")
                        test_passed = False
                else:
                    self.log(f"✗ Query failed for {test_case['description']}: {response.status_code}", "ERROR")
                    test_passed = False

            except Exception as e:
                self.log(f"✗ Exception querying {test_case['description']}: {e}", "ERROR")
                test_passed = False

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 2 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 2: Tag-based content query failed")
            self.log("✗ TEST 2 FAILED")

        self.results['test_details'].append({
            "test": "Tag-Based Content Query",
            "passed": test_passed
        })

    def test_3_audit_log_verification(self):
        """Test 3: Verify audit logs"""
        self.log("\n=== TEST 3: Audit Log Verification ===")
        self.results['tests_run'] += 1

        test_passed = True
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        try:
            response = self.session.get(
                f"{BASE_URL}/api/v1/audit-logs/",
                headers=headers,
                params={"limit": 50}
            )

            if response.status_code == 200:
                logs = response.json()

                # Check for CREATE actions on content
                create_logs = [log for log in logs if log['action'] == 'CREATE' and log['entity_type'] == 'content']

                if len(create_logs) >= 3:  # We created 3 contents
                    self.log(f"✓ Found {len(create_logs)} CREATE audit logs for content")

                    # Verify user_id matches
                    correct_user = all(log['user_id'] == self.user_id for log in create_logs)
                    if correct_user:
                        self.log("✓ All audit logs have correct user_id")
                    else:
                        self.log("✗ Some audit logs have incorrect user_id", "ERROR")
                        test_passed = False

                    self.results['audit_logs_verified'] = True
                else:
                    self.log(f"✗ Expected at least 3 CREATE logs, found {len(create_logs)}", "ERROR")
                    test_passed = False
            else:
                self.log(f"✗ Failed to fetch audit logs: {response.status_code}", "ERROR")
                test_passed = False

        except Exception as e:
            self.log(f"✗ Exception verifying audit logs: {e}", "ERROR")
            test_passed = False

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 3 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 3: Audit log verification failed")
            self.log("✗ TEST 3 FAILED")

        self.results['test_details'].append({
            "test": "Audit Log Verification",
            "passed": test_passed
        })

    def test_4_content_update_tags(self, content_ids, tag_ids):
        """Test 4: Update content tags"""
        self.log("\n=== TEST 4: Content Update Tags ===")
        self.results['tests_run'] += 1

        test_passed = True
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Update Content A: remove tag 0, add tag 2
        # Original: [tag_ids[0], tag_ids[1]]
        # New: [tag_ids[1], tag_ids[2]]

        try:
            content_id = content_ids[0]
            new_tags = [tag_ids[1], tag_ids[2]]

            response = self.session.put(
                f"{BASE_URL}/api/v1/contents/{content_id}",
                headers=headers,
                json={
                    "name": "Content A (Updated)",
                    "tag_ids": new_tags
                }
            )

            if response.status_code == 200:
                content = response.json()

                # Verify tags were updated
                content_tag_ids = sorted([t['id'] for t in content.get('tags', [])])
                expected_tag_ids = sorted(new_tags)

                if content_tag_ids == expected_tag_ids:
                    self.log(f"✓ Content tags updated correctly: {new_tags}")

                    # Verify queries return updated results
                    # Query tag 0 should NOT return Content A anymore
                    response = self.session.get(
                        f"{BASE_URL}/api/v1/contents/",
                        headers=headers,
                        params={"tag_id": tag_ids[0]}
                    )

                    if response.status_code == 200:
                        contents = response.json()
                        found_ids = [c['id'] for c in contents]

                        if content_id not in found_ids:
                            self.log("✓ Content A correctly removed from tag 0 queries")
                        else:
                            self.log("✗ Content A still appears in tag 0 queries", "ERROR")
                            test_passed = False

                    # Query tag 2 should NOW return Content A
                    response = self.session.get(
                        f"{BASE_URL}/api/v1/contents/",
                        headers=headers,
                        params={"tag_id": tag_ids[2]}
                    )

                    if response.status_code == 200:
                        contents = response.json()
                        found_ids = [c['id'] for c in contents]

                        if content_id in found_ids:
                            self.log("✓ Content A correctly added to tag 2 queries")
                        else:
                            self.log("✗ Content A not found in tag 2 queries", "ERROR")
                            test_passed = False
                else:
                    self.log(f"✗ Tag update failed. Expected {expected_tag_ids}, got {content_tag_ids}", "ERROR")
                    test_passed = False
            else:
                self.log(f"✗ Failed to update content: {response.status_code} - {response.text}", "ERROR")
                test_passed = False

        except Exception as e:
            self.log(f"✗ Exception updating content tags: {e}", "ERROR")
            test_passed = False

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 4 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 4: Content update tags failed")
            self.log("✗ TEST 4 FAILED")

        self.results['test_details'].append({
            "test": "Content Update Tags",
            "passed": test_passed
        })

    def test_5_content_delete_cascade(self, content_ids):
        """Test 5: Content delete with cascade"""
        self.log("\n=== TEST 5: Content Delete Cascade ===")
        self.results['tests_run'] += 1

        test_passed = True
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Delete Content B (content_ids[1])
        try:
            content_id = content_ids[1]

            response = self.session.delete(
                f"{BASE_URL}/api/v1/contents/{content_id}",
                headers=headers
            )

            if response.status_code == 204 or response.status_code == 200:
                self.log(f"✓ Content B deleted (ID={content_id})")

                # Verify content is really deleted
                response = self.session.get(
                    f"{BASE_URL}/api/v1/contents/{content_id}",
                    headers=headers
                )

                if response.status_code == 404:
                    self.log("✓ Content no longer accessible")

                    # Verify audit log has DELETE action
                    response = self.session.get(
                        f"{BASE_URL}/api/v1/audit-logs/",
                        headers=headers,
                        params={"limit": 10}
                    )

                    if response.status_code == 200:
                        logs = response.json()
                        delete_log = any(
                            log['action'] == 'DELETE' and
                            log['entity_type'] == 'content' and
                            log['entity_id'] == content_id
                            for log in logs
                        )

                        if delete_log:
                            self.log("✓ Audit log records DELETE action")
                        else:
                            self.log("✗ No DELETE audit log found", "ERROR")
                            test_passed = False
                else:
                    self.log(f"✗ Content still accessible after delete: {response.status_code}", "ERROR")
                    test_passed = False
            else:
                self.log(f"✗ Failed to delete content: {response.status_code} - {response.text}", "ERROR")
                test_passed = False

        except Exception as e:
            self.log(f"✗ Exception deleting content: {e}", "ERROR")
            test_passed = False

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 5 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 5: Content delete cascade failed")
            self.log("✗ TEST 5 FAILED")

        self.results['test_details'].append({
            "test": "Content Delete Cascade",
            "passed": test_passed
        })

    def test_6_multi_tenancy_check(self):
        """Test 6: Multi-tenancy isolation"""
        self.log("\n=== TEST 6: Multi-Tenancy Check ===")
        self.results['tests_run'] += 1

        test_passed = True

        # Create a different organization
        try:
            # Use timestamp to make username unique
            other_username = f"other_org_admin_{int(time.time())}"
            response = self.session.post(f"{BASE_URL}/api/v1/auth/register", json={
                "username": other_username,
                "email": f"{other_username}@test.com",
                "password": "OtherPass123!",
                
                "full_name": "Other Org Admin"
            })

            if response.status_code == 201:
                # Login to get token
                login_response = self.session.post(f"{BASE_URL}/api/v1/auth/login", json={
                    "username": other_username,
                    "password": "OtherPass123!"
                })

                if login_response.status_code != 200:
                    self.log(f"✗ Failed to login as other org: {login_response.status_code}", "ERROR")
                    test_passed = False
                else:
                    other_token = login_response.json()['data']['access_token']
                    self.log("✓ Created another organization for isolation test")

                    # Try to query contents from our organization using the other org's token
                    headers = {"Authorization": f"Bearer {other_token}"}
                    response = self.session.get(
                        f"{BASE_URL}/api/v1/contents/",
                        headers=headers
                    )

                    if response.status_code == 200:
                        contents = response.json()

                        # Should not see any of our contents
                        our_content_ids = self.results['created_resources']['content_ids']
                        found_our_content = any(c['id'] in our_content_ids for c in contents)

                        if not found_our_content:
                            self.log("✓ Multi-tenancy isolation working - other org cannot see our contents")
                        else:
                            self.log("✗ Multi-tenancy breach! Other org can see our contents", "ERROR")
                            test_passed = False
                    else:
                        self.log(f"✗ Failed to query from other org: {response.status_code}", "ERROR")
                        test_passed = False
            else:
                self.log(f"✗ Failed to create other organization: {response.status_code}", "ERROR")
                test_passed = False

        except Exception as e:
            self.log(f"✗ Exception in multi-tenancy test: {e}", "ERROR")
            test_passed = False

        if test_passed:
            self.results['tests_passed'] += 1
            self.log("✓ TEST 6 PASSED")
        else:
            self.results['tests_failed'] += 1
            self.results['failures'].append("Test 6: Multi-tenancy check failed")
            self.log("✗ TEST 6 FAILED")

        self.results['test_details'].append({
            "test": "Multi-Tenancy Check",
            "passed": test_passed
        })

    def save_results(self):
        """Save test results to coordinator file"""
        try:
            with open(COORDINATOR_FILE, 'r') as f:
                data = json.load(f)

            # Update phase 2 results
            data['test_results']['phase_2_crud']['agent_content_tag'] = self.results

            # Check if all Phase 2 agents are done
            phase_2_agents = data['phases']['phase_2_crud']['agents']
            phase_2_results = data['test_results']['phase_2_crud']

            if len(phase_2_results) == len(phase_2_agents):
                data['phases']['phase_2_crud']['status'] = 'completed'
                data['phases']['phase_2_crud']['completed_at'] = datetime.now().isoformat()
                self.log("✓ Phase 2 completed by all agents")

            with open(COORDINATOR_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            self.log("✓ Results saved to coordinator file")

            # Also save to separate file
            results_file = "/mnt/g/khoirul/signage/backups/agent_content_tag_results.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)

            self.log(f"✓ Detailed results saved to {results_file}")

        except Exception as e:
            self.log(f"✗ Failed to save results: {e}", "ERROR")

    def run_all_tests(self):
        """Run all integration tests"""
        self.log("=" * 60)
        self.log("CONTENT + TAG INTEGRATION TEST AGENT")
        self.log("=" * 60)

        # Setup organization
        if not self.setup_organization():
            self.log("Failed to setup organization. Aborting.", "ERROR")
            return False

        self.update_coordinator_file(phase_1_complete=True)

        # Create tags
        tag_ids = self.create_tags()
        if len(tag_ids) < 3:
            self.log("Failed to create all tags. Aborting.", "ERROR")
            return False

        # Run tests
        content_ids = self.test_1_content_creation_with_tags(tag_ids)

        if content_ids:
            self.test_2_tag_based_content_query(tag_ids, content_ids)
            self.test_3_audit_log_verification()
            self.test_4_content_update_tags(content_ids, tag_ids)
            self.test_5_content_delete_cascade(content_ids)
            self.test_6_multi_tenancy_check()

        # Save results
        self.save_results()

        # Print summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tests: {self.results['tests_run']}")
        self.log(f"Passed: {self.results['tests_passed']}")
        self.log(f"Failed: {self.results['tests_failed']}")
        self.log(f"Success Rate: {(self.results['tests_passed']/self.results['tests_run']*100):.1f}%")

        if self.results['failures']:
            self.log("\nFailures:")
            for failure in self.results['failures']:
                self.log(f"  - {failure}")

        return self.results['tests_failed'] == 0

def main():
    agent = ContentTagTestAgent()
    success = agent.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
