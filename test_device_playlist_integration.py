#!/usr/bin/env python3
"""
Integration Test: Device & Playlist Management
Agent: AGENT_DEVICE_PLAYLIST
Organization: TEST_ORG_DEVICE_PLAYLIST (org_11)
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://192.168.5.12:8001/api/v1"
COORDINATION_FILE = "/mnt/g/khoirul/signate/integration_test_coordinator.json"
SAMPLE_MEDIA_DIR = "/mnt/g/khoirul/signate/contoh_media"

# Test Organization
ORG_ID = 11
ORG_NAME = "TEST_ORG_DEVICE_PLAYLIST"

# Test Results
test_results = {
    "agent": "agent_device_playlist",
    "org_id": ORG_ID,
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "failures": [],
    "audit_logs_verified": False,
    "created_resources": {
        "device_ids": [],
        "playlist_ids": [],
        "content_ids": [],
        "tag_ids": []
    },
    "test_details": []
}

class TestSession:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.org_id = None

    def load_coordination_file(self):
        """Load coordination file and get token"""
        try:
            with open(COORDINATION_FILE, 'r') as f:
                coord = json.load(f)

            # Check if Phase 1 is completed
            phase1_status = coord['phases']['phase_1_setup']['status']
            if phase1_status != 'completed':
                print(f"❌ Phase 1 is not completed yet. Current status: {phase1_status}")
                print("Please wait for Phase 1 setup to complete before running this test.")
                return False

            # Get admin token
            self.token = coord['shared_resources'].get('admin_token')
            if not self.token:
                print("❌ Admin token not found in coordination file")
                return False

            self.session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            })

            print(f"✅ Loaded coordination file")
            print(f"✅ Using admin token: {self.token[:20]}...")
            return True

        except Exception as e:
            print(f"❌ Error loading coordination file: {e}")
            return False

    def create_test_org(self):
        """Create test organization"""
        try:
            # First try to find existing organization
            resp = self.session.get(f"{BASE_URL}/organizations")
            if resp.status_code == 200:
                orgs_data = resp.json()
                # Handle both direct list and wrapped response
                orgs = orgs_data if isinstance(orgs_data, list) else orgs_data.get('organizations', [])
                for org in orgs:
                    if org['name'] == ORG_NAME:
                        self.org_id = org['id']
                        print(f"✅ Using existing organization: {ORG_NAME} (ID: {self.org_id})")
                        return True

            # If not found, create new organization
            response = self.session.post(
                f"{BASE_URL}/organizations",
                json={
                    "name": ORG_NAME,
                    "code": f"TEST{ORG_ID}",
                    "status": "active"
                }
            )

            if response.status_code == 201:
                org_data = response.json()
                self.org_id = org_data.get('id') or org_data.get('data', {}).get('id')
                print(f"✅ Created organization: {ORG_NAME} (ID: {self.org_id})")
                return True
            elif response.status_code == 400 and ("sudah ada" in response.text.lower() or "already exists" in response.text.lower()):
                # Organization was just created, try to get it again
                resp = self.session.get(f"{BASE_URL}/organizations")
                if resp.status_code == 200:
                    orgs_data = resp.json()
                    orgs = orgs_data if isinstance(orgs_data, list) else orgs_data.get('organizations', [])
                    for org in orgs:
                        if org['name'] == ORG_NAME:
                            self.org_id = org['id']
                            print(f"✅ Using existing organization: {ORG_NAME} (ID: {self.org_id})")
                            return True
                print(f"❌ Organization exists but couldn't retrieve it")
                return False
            else:
                print(f"❌ Failed to create organization: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating organization: {e}")
            return False

def run_test_1_playlist_with_contents(session: TestSession):
    """Test 1: Create playlist with content items"""
    test_results['tests_run'] += 1
    test_name = "Test 1: Playlist with Content Items"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        # Step 1: Create playlist
        print("\n[1.1] Creating playlist 'Morning Show'...")
        playlist_response = session.session.post(
            f"{BASE_URL}/playlists",
            json={
                "name": "Morning Show",
                "description": "Morning content playlist",
                "organization_id": session.org_id,
                "is_active": True
            }
        )

        if playlist_response.status_code != 201:
            raise Exception(f"Failed to create playlist: {playlist_response.status_code} - {playlist_response.text}")

        playlist = playlist_response.json()
        playlist_id = playlist['id']
        test_results['created_resources']['playlist_ids'].append(playlist_id)
        print(f"✅ Created playlist: ID={playlist_id}, Name='{playlist['name']}'")

        # Step 2: Upload 3 contents
        print("\n[1.2] Uploading 3 content files...")
        media_files = [
            "WhatsApp Image 2024-11-05 at 18.20.08.jpeg",
            "DESIGN VfsfdfdOUCHER.jpg",
            "bfdbfdbfd.PNG"
        ]

        content_ids = []
        for idx, filename in enumerate(media_files, 1):
            file_path = Path(SAMPLE_MEDIA_DIR) / filename
            if not file_path.exists():
                print(f"⚠️  File not found: {file_path}, skipping...")
                continue

            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'image/jpeg')}
                data = {
                    'name': f'Morning Content {idx}',
                    'type': 'image',
                    'organization_id': str(session.org_id)
                }

                content_response = session.session.post(
                    f"{BASE_URL}/contents/upload",
                    data=data,
                    files=files,
                    headers={'Authorization': f'Bearer {session.token}'}
                )

                if content_response.status_code == 201:
                    content = content_response.json()
                    content_ids.append(content['id'])
                    test_results['created_resources']['content_ids'].append(content['id'])
                    print(f"  ✅ Uploaded: ID={content['id']}, Name='{content['name']}'")
                else:
                    print(f"  ❌ Failed to upload {filename}: {content_response.status_code}")

        if len(content_ids) < 3:
            raise Exception(f"Only uploaded {len(content_ids)} out of 3 contents")

        # Step 3: Add contents to playlist with order and duration
        print("\n[1.3] Adding contents to playlist...")
        for idx, content_id in enumerate(content_ids, 1):
            item_response = session.session.post(
                f"{BASE_URL}/playlists/{playlist_id}/items",
                json={
                    "content_id": content_id,
                    "order": idx,
                    "duration": 10 + idx  # 11, 12, 13 seconds
                }
            )

            if item_response.status_code != 201:
                raise Exception(f"Failed to add content {content_id} to playlist: {item_response.text}")

            item = item_response.json()
            print(f"  ✅ Added content {content_id} at position {idx}, duration={item['duration']}s")

        # Step 4: Verify playlist_contents table
        print("\n[1.4] Verifying playlist items...")
        items_response = session.session.get(f"{BASE_URL}/playlists/{playlist_id}/items")

        if items_response.status_code != 200:
            raise Exception(f"Failed to get playlist items: {items_response.text}")

        items = items_response.json()
        if len(items) != 3:
            raise Exception(f"Expected 3 items, got {len(items)}")

        # Verify order
        for idx, item in enumerate(items, 1):
            if item['order'] != idx:
                raise Exception(f"Item {idx} has wrong order: {item['order']}")

        print(f"✅ Verified: playlist has 3 items in correct order")

        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "playlist_id": playlist_id,
            "content_count": len(content_ids)
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def run_test_2_device_registration(session: TestSession):
    """Test 2: Device registration via activation code"""
    test_results['tests_run'] += 1
    test_name = "Test 2: Device Registration Flow"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        device_ids = []

        for device_name in ["TestDevice_A", "TestDevice_B"]:
            print(f"\n[2.{len(device_ids)+1}] Registering {device_name}...")

            # Step 1: Generate activation code
            print(f"  [2.{len(device_ids)+1}.1] Generating activation code...")
            code_response = session.session.post(
                f"{BASE_URL}/devices/activation-code",
                json={"organization_id": session.org_id}
            )

            if code_response.status_code != 200:
                raise Exception(f"Failed to generate activation code: {code_response.text}")

            activation_code = code_response.json()['code']
            print(f"    ✅ Generated activation code: {activation_code}")

            # Step 2: Activate device
            print(f"  [2.{len(device_ids)+1}.2] Activating device with name '{device_name}'...")
            activate_response = session.session.post(
                f"{BASE_URL}/devices/activate",
                json={
                    "activation_code": activation_code,
                    "device_name": device_name,
                    "device_info": {
                        "platform": "test",
                        "browser": "integration-test",
                        "screen_resolution": "1920x1080"
                    }
                }
            )

            if activate_response.status_code != 200:
                raise Exception(f"Failed to activate device: {activate_response.text}")

            device = activate_response.json()
            device_id = device['id']
            device_ids.append(device_id)
            test_results['created_resources']['device_ids'].append(device_id)
            print(f"    ✅ Activated device: ID={device_id}, Name='{device['name']}'")

            # Step 3: Verify device in database
            print(f"  [2.{len(device_ids)}.3] Verifying device status...")
            device_response = session.session.get(f"{BASE_URL}/devices/{device_id}")

            if device_response.status_code != 200:
                raise Exception(f"Failed to get device: {device_response.text}")

            device_data = device_response.json()
            if device_data['status'] != 'active':
                raise Exception(f"Device status is {device_data['status']}, expected 'active'")

            print(f"    ✅ Verified: Device status is 'active'")

        if len(device_ids) != 2:
            raise Exception(f"Expected 2 devices, registered {len(device_ids)}")

        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "device_ids": device_ids
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def run_test_3_playlist_assignment(session: TestSession):
    """Test 3: Assign playlist to device directly"""
    test_results['tests_run'] += 1
    test_name = "Test 3: Playlist Assignment to Device"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        # Get device A and a playlist
        device_ids = test_results['created_resources']['device_ids']
        playlist_ids = test_results['created_resources']['playlist_ids']

        if len(device_ids) < 1:
            raise Exception("No devices available from previous test")
        if len(playlist_ids) < 1:
            raise Exception("No playlists available from previous test")

        device_a_id = device_ids[0]
        playlist_id = playlist_ids[0]

        print(f"\n[3.1] Assigning playlist {playlist_id} to device {device_a_id}...")
        assign_response = session.session.post(
            f"{BASE_URL}/playlists/{playlist_id}/assign",
            json={
                "device_ids": [device_a_id]
            }
        )

        if assign_response.status_code != 200:
            raise Exception(f"Failed to assign playlist: {assign_response.text}")

        print(f"✅ Assigned playlist to device")

        # Verify assignment in database
        print(f"\n[3.2] Verifying playlist assignment...")
        assignments_response = session.session.get(
            f"{BASE_URL}/devices/{device_a_id}/playlist"
        )

        if assignments_response.status_code != 200:
            raise Exception(f"Failed to get device playlist: {assignments_response.text}")

        playlist_data = assignments_response.json()
        if playlist_data['id'] != playlist_id:
            raise Exception(f"Device has wrong playlist: {playlist_data['id']}, expected {playlist_id}")

        print(f"✅ Verified: Device has correct playlist assigned")

        # Verify device gets playlist with all contents
        print(f"\n[3.3] Verifying device receives complete playlist...")
        if 'items' not in playlist_data or len(playlist_data['items']) != 3:
            raise Exception(f"Playlist doesn't have 3 items: {playlist_data.get('items', [])}")

        # Verify order
        for idx, item in enumerate(playlist_data['items'], 1):
            if item['order'] != idx:
                raise Exception(f"Item has wrong order: {item['order']}, expected {idx}")

        print(f"✅ Verified: Device receives playlist with all 3 contents in correct order")

        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "device_id": device_a_id,
            "playlist_id": playlist_id
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def run_test_4_tag_based_assignment(session: TestSession):
    """Test 4: Tag-based playlist assignment"""
    test_results['tests_run'] += 1
    test_name = "Test 4: Tag-Based Playlist Assignment"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        # Get device B
        device_ids = test_results['created_resources']['device_ids']
        if len(device_ids) < 2:
            raise Exception("Device B not available from previous test")

        device_b_id = device_ids[1]

        # Step 1: Create tag "Lobby"
        print(f"\n[4.1] Creating tag 'Lobby'...")
        tag_response = session.session.post(
            f"{BASE_URL}/tags",
            json={
                "name": "Lobby",
                "category": "location",
                "organization_id": session.org_id
            }
        )

        if tag_response.status_code != 201:
            raise Exception(f"Failed to create tag: {tag_response.text}")

        tag = tag_response.json()
        tag_id = tag['id']
        test_results['created_resources']['tag_ids'].append(tag_id)
        print(f"✅ Created tag: ID={tag_id}, Name='{tag['name']}'")

        # Step 2: Assign device B to tag "Lobby"
        print(f"\n[4.2] Assigning device {device_b_id} to tag 'Lobby'...")
        device_tag_response = session.session.post(
            f"{BASE_URL}/devices/{device_b_id}/tags",
            json={
                "tag_ids": [tag_id]
            }
        )

        if device_tag_response.status_code != 200:
            raise Exception(f"Failed to assign tag to device: {device_tag_response.text}")

        print(f"✅ Assigned device to tag")

        # Step 3: Create a different playlist
        print(f"\n[4.3] Creating 'Lobby Playlist'...")
        playlist_response = session.session.post(
            f"{BASE_URL}/playlists",
            json={
                "name": "Lobby Playlist",
                "description": "Playlist for lobby devices",
                "organization_id": session.org_id,
                "is_active": True
            }
        )

        if playlist_response.status_code != 201:
            raise Exception(f"Failed to create playlist: {playlist_response.text}")

        lobby_playlist = playlist_response.json()
        lobby_playlist_id = lobby_playlist['id']
        test_results['created_resources']['playlist_ids'].append(lobby_playlist_id)
        print(f"✅ Created playlist: ID={lobby_playlist_id}")

        # Step 4: Assign playlist to tag
        print(f"\n[4.4] Assigning playlist to tag 'Lobby'...")
        tag_playlist_response = session.session.post(
            f"{BASE_URL}/playlists/{lobby_playlist_id}/assign",
            json={
                "tag_ids": [tag_id]
            }
        )

        if tag_playlist_response.status_code != 200:
            raise Exception(f"Failed to assign playlist to tag: {tag_playlist_response.text}")

        print(f"✅ Assigned playlist to tag")

        # Step 5: Verify device gets playlist via tag
        print(f"\n[4.5] Verifying device receives playlist via tag...")
        device_playlist_response = session.session.get(
            f"{BASE_URL}/devices/{device_b_id}/playlist"
        )

        if device_playlist_response.status_code != 200:
            raise Exception(f"Failed to get device playlist: {device_playlist_response.text}")

        playlist_data = device_playlist_response.json()
        if playlist_data['id'] != lobby_playlist_id:
            raise Exception(f"Device has wrong playlist: {playlist_data['id']}, expected {lobby_playlist_id}")

        print(f"✅ Verified: Device receives playlist via tag assignment")

        # Step 6: Verify device_tags table
        print(f"\n[4.6] Verifying device_tags table...")
        device_tags_response = session.session.get(
            f"{BASE_URL}/devices/{device_b_id}/tags"
        )

        if device_tags_response.status_code != 200:
            raise Exception(f"Failed to get device tags: {device_tags_response.text}")

        device_tags = device_tags_response.json()
        if not any(t['id'] == tag_id for t in device_tags):
            raise Exception(f"Tag {tag_id} not found in device tags")

        print(f"✅ Verified: device_tags table is correct")

        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "device_id": device_b_id,
            "tag_id": tag_id,
            "playlist_id": lobby_playlist_id
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def run_test_5_device_heartbeat(session: TestSession):
    """Test 5: Device heartbeat and status"""
    test_results['tests_run'] += 1
    test_name = "Test 5: Device Heartbeat & Status"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        # Get device A
        device_ids = test_results['created_resources']['device_ids']
        if len(device_ids) < 1:
            raise Exception("No devices available from previous test")

        device_a_id = device_ids[0]

        # Step 1: Get device token (from activation)
        print(f"\n[5.1] Getting device information...")
        device_response = session.session.get(f"{BASE_URL}/devices/{device_a_id}")

        if device_response.status_code != 200:
            raise Exception(f"Failed to get device: {device_response.text}")

        device = device_response.json()
        print(f"✅ Retrieved device: {device['name']}")

        # Step 2: Send heartbeat
        print(f"\n[5.2] Sending device heartbeat...")
        heartbeat_response = session.session.post(
            f"{BASE_URL}/devices/{device_a_id}/heartbeat",
            json={
                "status": "playing",
                "current_content_id": None
            }
        )

        if heartbeat_response.status_code != 200:
            raise Exception(f"Failed to send heartbeat: {heartbeat_response.text}")

        print(f"✅ Heartbeat sent successfully")

        # Step 3: Verify last_seen updated
        print(f"\n[5.3] Verifying last_seen timestamp...")
        time.sleep(1)  # Wait a moment

        device_response2 = session.session.get(f"{BASE_URL}/devices/{device_a_id}")
        if device_response2.status_code != 200:
            raise Exception(f"Failed to get device: {device_response2.text}")

        device2 = device_response2.json()
        last_seen = datetime.fromisoformat(device2['last_seen'].replace('Z', '+00:00'))
        now = datetime.now(last_seen.tzinfo)
        time_diff = (now - last_seen).total_seconds()

        if time_diff > 60:  # Should be less than 1 minute ago
            raise Exception(f"last_seen is {time_diff}s ago, expected < 60s")

        print(f"✅ Verified: last_seen updated ({time_diff:.1f}s ago)")

        # Step 4: Verify status is "online"
        print(f"\n[5.4] Verifying device status...")
        if device2['status'] != 'active':
            print(f"⚠️  Device status is '{device2['status']}' (expected 'active' or 'online')")

        # Check if device would be considered online (last_seen < 5 minutes)
        if time_diff < 300:
            print(f"✅ Verified: Device would show as 'online' in dashboard (last_seen < 5 min)")
        else:
            raise Exception(f"Device would show as offline (last_seen = {time_diff}s)")

        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "device_id": device_a_id,
            "last_seen_seconds_ago": round(time_diff, 1)
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def run_test_6_audit_logs(session: TestSession):
    """Test 6: Verify audit logs for device operations"""
    test_results['tests_run'] += 1
    test_name = "Test 6: Audit Logs for Device Operations"
    print(f"\n{'='*60}")
    print(f"{test_name}")
    print(f"{'='*60}")

    try:
        # Get device IDs
        device_ids = test_results['created_resources']['device_ids']
        if len(device_ids) < 1:
            raise Exception("No devices available from previous test")

        print(f"\n[6.1] Fetching audit logs for organization...")
        audit_response = session.session.get(
            f"{BASE_URL}/audit-logs",
            params={
                "organization_id": session.org_id,
                "limit": 100
            }
        )

        if audit_response.status_code != 200:
            raise Exception(f"Failed to get audit logs: {audit_response.text}")

        audit_logs = audit_response.json()
        print(f"✅ Retrieved {len(audit_logs)} audit log entries")

        # Verify device create/update logs
        print(f"\n[6.2] Verifying device operation logs...")
        device_logs = [log for log in audit_logs if log.get('entity_type') == 'device']

        if len(device_logs) < 2:  # At least 2 device creations
            raise Exception(f"Expected at least 2 device logs, found {len(device_logs)}")

        # Check for device creation actions
        device_create_logs = [log for log in device_logs if log.get('action') in ['create', 'activate']]
        if len(device_create_logs) < 2:
            raise Exception(f"Expected at least 2 device create/activate logs, found {len(device_create_logs)}")

        print(f"  ✅ Found {len(device_logs)} device-related logs")
        print(f"  ✅ Found {len(device_create_logs)} device create/activate logs")

        # Verify playlist assignment logs
        print(f"\n[6.3] Verifying playlist assignment logs...")
        playlist_logs = [log for log in audit_logs
                        if log.get('entity_type') in ['playlist', 'playlist_assignment']]

        if len(playlist_logs) < 2:  # At least 2 playlist assignments
            raise Exception(f"Expected at least 2 playlist logs, found {len(playlist_logs)}")

        print(f"  ✅ Found {len(playlist_logs)} playlist-related logs")

        # Verify log structure
        print(f"\n[6.4] Verifying audit log structure...")
        for log in device_logs[:3]:  # Check first 3 logs
            required_fields = ['id', 'action', 'entity_type', 'user_id', 'timestamp']
            missing_fields = [field for field in required_fields if field not in log]

            if missing_fields:
                raise Exception(f"Audit log missing fields: {missing_fields}")

        print(f"  ✅ Audit log structure is correct")

        test_results['audit_logs_verified'] = True
        test_results['tests_passed'] += 1
        test_results['test_details'].append({
            "test": test_name,
            "status": "PASSED",
            "total_logs": len(audit_logs),
            "device_logs": len(device_logs),
            "playlist_logs": len(playlist_logs)
        })
        print(f"\n✅ {test_name} - PASSED")

    except Exception as e:
        test_results['tests_failed'] += 1
        test_results['failures'].append(f"{test_name}: {str(e)}")
        test_results['test_details'].append({
            "test": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"\n❌ {test_name} - FAILED: {e}")

def update_coordination_file():
    """Update coordination file with test results"""
    try:
        with open(COORDINATION_FILE, 'r') as f:
            coord = json.load(f)

        # Update phase_2_crud results
        coord['test_results']['phase_2_crud']['agent_device_playlist'] = test_results

        # Update phase status if all agents completed
        # (This would be done by the coordinator, but we can mark our completion)

        with open(COORDINATION_FILE, 'w') as f:
            json.dump(coord, f, indent=2)

        print(f"\n✅ Updated coordination file with test results")
        return True

    except Exception as e:
        print(f"\n❌ Error updating coordination file: {e}")
        return False

def print_summary():
    """Print test summary"""
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY - AGENT_DEVICE_PLAYLIST")
    print(f"{'='*60}")
    print(f"Organization: {ORG_NAME} (ID: {ORG_ID})")
    print(f"Tests Run: {test_results['tests_run']}")
    print(f"Tests Passed: {test_results['tests_passed']}")
    print(f"Tests Failed: {test_results['tests_failed']}")
    print(f"Audit Logs Verified: {test_results['audit_logs_verified']}")

    print(f"\nCreated Resources:")
    print(f"  - Devices: {len(test_results['created_resources']['device_ids'])}")
    print(f"  - Playlists: {len(test_results['created_resources']['playlist_ids'])}")
    print(f"  - Contents: {len(test_results['created_resources']['content_ids'])}")
    print(f"  - Tags: {len(test_results['created_resources']['tag_ids'])}")

    if test_results['failures']:
        print(f"\nFailures:")
        for failure in test_results['failures']:
            print(f"  ❌ {failure}")

    print(f"\n{'='*60}")

    # Save detailed results to file
    results_file = "/mnt/g/khoirul/signage/test_device_playlist_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"Detailed results saved to: {results_file}")

def main():
    """Main test execution"""
    print(f"{'='*60}")
    print(f"INTEGRATION TEST: Device & Playlist Management")
    print(f"Agent: AGENT_DEVICE_PLAYLIST")
    print(f"Organization: {ORG_NAME}")
    print(f"{'='*60}")

    # Initialize session
    session = TestSession()

    # Load coordination file and check Phase 1
    if not session.load_coordination_file():
        print("\n❌ Cannot proceed without coordination file and Phase 1 completion")
        return

    # Create test organization
    if not session.create_test_org():
        print("\n❌ Cannot proceed without test organization")
        return

    # Run all tests
    run_test_1_playlist_with_contents(session)
    run_test_2_device_registration(session)
    run_test_3_playlist_assignment(session)
    run_test_4_tag_based_assignment(session)
    run_test_5_device_heartbeat(session)
    run_test_6_audit_logs(session)

    # Update coordination file
    update_coordination_file()

    # Print summary
    print_summary()

    # Exit with appropriate code
    if test_results['tests_failed'] > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()
