#!/usr/bin/env python3
"""
AGENT_SCHEDULE - Integration Testing for Schedule Management
Organization: TEST_ORG_SCHEDULE (org_12, ID: 15)
User: admin_sched (ID: 20)
"""

import requests
import json
from datetime import datetime, time
from typing import Dict, List, Any

BASE_URL = "http://192.168.5.12:8001"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMCIsInVzZXJuYW1lIjoiYWRtaW5fc2NoZWQiLCJyb2xlIjoiQURNSU4iLCJvcmdhbml6YXRpb25faWQiOjE1LCJleHAiOjE3NjMwMzkxOTUsImlhdCI6MTc2MzAzNzM5NSwidHlwZSI6ImFjY2VzcyJ9.EDbzWplfWbkBmWibTM_ZsSwfZ4D7Ys18Qs258JgJ_D0"
ORG_ID = 15
USER_ID = 20

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test results tracker
results = {
    "agent": "agent_schedule",
    "org_id": ORG_ID,
    "user_id": USER_ID,
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "failures": [],
    "audit_logs_verified": False,
    "features_tested": {
        "schedule_crud": "not_tested",
        "priority_logic": "not_tested",
        "device_targeting": "not_tested",
        "tag_targeting": "not_tested",
        "apply_to_all": "not_tested"
    },
    "created_resources": {
        "schedule_ids": [],
        "playlist_ids": [],
        "device_ids": [],
        "tag_ids": []
    },
    "test_details": []
}

def log_test(test_name: str, status: str, details: Dict = None):
    """Log test result"""
    results["tests_run"] += 1
    if status == "PASSED":
        results["tests_passed"] += 1
    else:
        results["tests_failed"] += 1
        if details and "error" in details:
            results["failures"].append(f"{test_name}: {details['error']}")

    test_detail = {"test": test_name, "status": status}
    if details:
        test_detail.update(details)
    results["test_details"].append(test_detail)

    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"STATUS: {status}")
    if details:
        print(f"DETAILS: {json.dumps(details, indent=2)}")
    print(f"{'='*60}")

def create_playlist(name: str, description: str) -> Dict:
    """Create a playlist"""
    response = requests.post(
        f"{BASE_URL}/api/v1/playlists",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "is_active": True,
            "priority": 0
        }
    )
    if response.status_code in [200, 201]:
        data = response.json()
        playlist = data.get("data") if "data" in data else data
        return playlist
    return None

def create_device(name: str) -> Dict:
    """Create a device via request-code and activate flow"""
    import random

    # Generate a 6-digit code
    activation_code = str(random.randint(100000, 999999))

    # Request activation code (player side)
    code_response = requests.post(
        f"{BASE_URL}/api/v1/devices/request-code",
        json={
            "code": activation_code,
            "device_name": name,
            "device_type": "monitor",
            "platform": "browser"
        }
    )

    print(f"Request code response: {code_response.status_code} - {code_response.text[:500]}")

    if code_response.status_code not in [200, 201]:
        return None

    # Activate device (admin side)
    activate_response = requests.post(
        f"{BASE_URL}/api/v1/devices/activate",
        headers=headers,
        json={
            "unique_code": activation_code,
            "device_name": name
        }
    )

    print(f"Activate device response: {activate_response.status_code} - {activate_response.text[:500]}")

    if activate_response.status_code in [200, 201]:
        activate_data = activate_response.json()
        # Check different response structures
        if "device" in activate_data:
            return activate_data["device"]
        elif "data" in activate_data:
            data = activate_data["data"]
            if isinstance(data, dict) and "device" in data:
                return data["device"]
            elif isinstance(data, dict) and "id" in data:
                return data
        return activate_data

    return None

def create_schedule(data: Dict) -> Dict:
    """Create a schedule"""
    # Ensure start_date is present (required field)
    if "start_date" not in data:
        data["start_date"] = "2025-01-13"

    response = requests.post(
        f"{BASE_URL}/api/v1/schedules",
        headers=headers,
        json=data
    )
    print(f"Create schedule response: {response.status_code} - {response.text[:500]}")
    if response.status_code in [200, 201]:
        resp_data = response.json()
        return resp_data.get("data") if "data" in resp_data else resp_data
    return None

def get_schedules() -> List[Dict]:
    """Get all schedules"""
    response = requests.get(
        f"{BASE_URL}/api/v1/schedules",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("schedules", [])
    return []

def get_active_schedule(device_id: int = None, time_str: str = None, date_str: str = None) -> Dict:
    """Get active schedule for device at specific time"""
    payload = {}
    if device_id:
        payload["device_id"] = device_id
    if time_str:
        payload["time"] = time_str
    if date_str:
        payload["date"] = date_str
    else:
        payload["date"] = "2025-01-13"  # Default test date

    # Use the /active/check endpoint (POST method)
    response = requests.post(
        f"{BASE_URL}/api/v1/schedules/active/check",
        headers=headers,
        json=payload
    )
    print(f"Get active schedule response: {response.status_code} - {response.text[:500]}")
    if response.status_code == 200:
        return response.json()
    return None

def create_tag(name: str, category: str = "location") -> Dict:
    """Create a tag"""
    response = requests.post(
        f"{BASE_URL}/api/v1/tags",
        headers=headers,
        json={
            "tag_name": name,
            "category": category,
            "organization_id": ORG_ID
        }
    )
    print(f"Create tag response: {response.status_code} - {response.text[:500]}")
    if response.status_code in [200, 201]:
        data = response.json()
        return data.get("data") if "data" in data else data
    return None

def assign_tag_to_device(device_id: int, tag_id: int) -> bool:
    """Assign tag to device"""
    response = requests.post(
        f"{BASE_URL}/api/v1/devices/{device_id}/tags",
        headers=headers,
        json={"tag_ids": [tag_id]}
    )
    print(f"Assign tag response: {response.status_code} - {response.text[:500]}")
    return response.status_code in [200, 201]

def get_audit_logs() -> List[Dict]:
    """Get audit logs"""
    response = requests.get(
        f"{BASE_URL}/api/v1/audit-logs",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("items", [])
    return []

# ============================================
# TEST 1: Basic Schedule Creation
# ============================================
def test_1_basic_schedule_creation():
    """Test creating 2 playlists and 2 schedules with different times"""
    try:
        # Create 2 playlists
        playlist_morning = create_playlist("Morning Playlist", "Content for morning")
        playlist_evening = create_playlist("Evening Playlist", "Content for evening")

        if not playlist_morning or not playlist_evening:
            log_test("Test 1: Basic Schedule Creation", "FAILED",
                    {"error": "Failed to create playlists"})
            return

        results["created_resources"]["playlist_ids"].append(playlist_morning["id"])
        results["created_resources"]["playlist_ids"].append(playlist_evening["id"])

        # Create Schedule A: Morning, 08:00-12:00, priority 10
        schedule_a = create_schedule({
            "name": "Morning Schedule",
            "playlist_id": playlist_morning["id"],
            "priority": 10,
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "is_active": True,
            "apply_to_all": False
        })

        # Create Schedule B: Evening, 08:00-12:00, priority 5 (overlapping)
        schedule_b = create_schedule({
            "name": "Evening Schedule (Overlapping)",
            "playlist_id": playlist_evening["id"],
            "priority": 5,
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "is_active": True,
            "apply_to_all": False
        })

        if not schedule_a or not schedule_b:
            log_test("Test 1: Basic Schedule Creation", "FAILED",
                    {"error": "Failed to create schedules - Backend bug: CurrentUser object has no attribute 'user_id' (should be 'id')"})
            results["features_tested"]["schedule_crud"] = "backend_bug"
            return

        results["created_resources"]["schedule_ids"].append(schedule_a["id"])
        results["created_resources"]["schedule_ids"].append(schedule_b["id"])

        # Verify schedules exist
        all_schedules = get_schedules()
        schedule_count = len([s for s in all_schedules if s["id"] in [schedule_a["id"], schedule_b["id"]]])

        if schedule_count == 2:
            log_test("Test 1: Basic Schedule Creation", "PASSED",
                    {"playlists_created": 2, "schedules_created": 2})
            results["features_tested"]["schedule_crud"] = "working"
        else:
            log_test("Test 1: Basic Schedule Creation", "FAILED",
                    {"error": f"Expected 2 schedules, found {schedule_count}"})
            results["features_tested"]["schedule_crud"] = "partial"

    except Exception as e:
        log_test("Test 1: Basic Schedule Creation", "FAILED", {"error": str(e)})
        results["features_tested"]["schedule_crud"] = "error"

# ============================================
# TEST 2: Schedule Priority Logic
# ============================================
def test_2_schedule_priority():
    """Test priority logic when schedules overlap"""
    try:
        # This test depends on Test 1 creating schedules successfully
        if results["features_tested"]["schedule_crud"] == "backend_bug":
            log_test("Test 2: Schedule Priority Logic", "SKIPPED",
                    {"error": "Cannot test - schedules not created due to backend bug in Test 1"})
            results["features_tested"]["priority_logic"] = "skipped_due_to_backend_bug"
            return

        # Query active schedule at 10:00 (both schedules overlap)
        active = get_active_schedule(time_str="10:00:00")

        if not active:
            log_test("Test 2: Schedule Priority Logic", "FAILED",
                    {"error": "No active schedule returned or endpoint not implemented"})
            results["features_tested"]["priority_logic"] = "not_implemented"
            return

        # Check if schedule is found
        if active.get("is_found") == False or active.get("schedule") is None:
            log_test("Test 2: Schedule Priority Logic", "SKIPPED",
                    {"error": "No schedules found - depends on Test 1 success"})
            results["features_tested"]["priority_logic"] = "skipped_no_data"
            return

        # Should return schedule with priority 10
        schedule = active.get("schedule")
        if schedule and schedule.get("priority") == 10:
            log_test("Test 2: Schedule Priority Logic", "PASSED",
                    {"returned_priority": 10, "expected_priority": 10})
            results["features_tested"]["priority_logic"] = "working"
        else:
            log_test("Test 2: Schedule Priority Logic", "FAILED",
                    {"error": f"Expected priority 10, got {schedule.get('priority') if schedule else 'None'}"})
            results["features_tested"]["priority_logic"] = "incorrect"

    except Exception as e:
        log_test("Test 2: Schedule Priority Logic", "FAILED", {"error": str(e)})
        results["features_tested"]["priority_logic"] = "error"

# ============================================
# TEST 3: Schedule by Device IDs
# ============================================
def test_3_schedule_by_device_ids():
    """Test schedule targeting specific device IDs"""
    try:
        # Create 2 devices
        device_x = create_device("DeviceX_Schedule")
        device_y = create_device("DeviceY_Schedule")

        print(f"Device X created: {device_x}")
        print(f"Device Y created: {device_y}")

        if not device_x or not device_y:
            log_test("Test 3: Schedule by Device IDs", "FAILED",
                    {"error": "Failed to create devices"})
            results["features_tested"]["device_targeting"] = "error"
            return

        # Check device structure and get ID
        device_x_id = device_x.get("id") if isinstance(device_x, dict) else None
        device_y_id = device_y.get("id") if isinstance(device_y, dict) else None

        if not device_x_id or not device_y_id:
            log_test("Test 3: Schedule by Device IDs", "FAILED",
                    {"error": f"Failed to get device IDs: device_x={device_x}, device_y={device_y}"})
            results["features_tested"]["device_targeting"] = "error"
            return

        results["created_resources"]["device_ids"].append(device_x_id)
        results["created_resources"]["device_ids"].append(device_y_id)

        # Create playlist for this test
        playlist = create_playlist("Device Specific Playlist", "For device targeting test")
        if not playlist:
            log_test("Test 3: Schedule by Device IDs", "FAILED",
                    {"error": "Failed to create playlist"})
            return

        results["created_resources"]["playlist_ids"].append(playlist["id"])

        # Create schedule targeting only DeviceX
        schedule = create_schedule({
            "name": "DeviceX Only Schedule",
            "playlist_id": playlist["id"],
            "priority": 15,
            "start_time": "14:00:00",
            "end_time": "16:00:00",
            "is_active": True,
            "apply_to_all": False,
            "device_ids": [device_x_id]
        })

        if not schedule:
            log_test("Test 3: Schedule by Device IDs", "FAILED",
                    {"error": "Failed to create device-specific schedule - likely backend bug with user_id vs id"})
            results["features_tested"]["device_targeting"] = "backend_bug"
            return

        results["created_resources"]["schedule_ids"].append(schedule["id"])

        # Test: Get active schedule for DeviceX at 15:00
        active_x = get_active_schedule(device_id=device_x_id, time_str="15:00:00")
        active_y = get_active_schedule(device_id=device_y_id, time_str="15:00:00")

        # DeviceX should get the schedule, DeviceY should not
        has_schedule_x = active_x and "data" in active_x
        has_schedule_y = active_y and "data" in active_y

        if has_schedule_x and not has_schedule_y:
            log_test("Test 3: Schedule by Device IDs", "PASSED",
                    {"device_x_got_schedule": True, "device_y_got_schedule": False})
            results["features_tested"]["device_targeting"] = "working"
        else:
            log_test("Test 3: Schedule by Device IDs", "FAILED",
                    {"error": f"DeviceX schedule: {has_schedule_x}, DeviceY schedule: {has_schedule_y}"})
            results["features_tested"]["device_targeting"] = "incorrect"

    except Exception as e:
        log_test("Test 3: Schedule by Device IDs", "FAILED", {"error": str(e)})
        results["features_tested"]["device_targeting"] = "error"

# ============================================
# TEST 4: Schedule by Tags
# ============================================
def test_4_schedule_by_tags():
    """Test schedule targeting devices via tags"""
    try:
        # Check if we have devices from previous test
        if len(results["created_resources"]["device_ids"]) < 2:
            log_test("Test 4: Schedule by Tags", "SKIPPED",
                    {"error": "No devices available from previous test"})
            results["features_tested"]["tag_targeting"] = "skipped"
            return

        device_y_id = results["created_resources"]["device_ids"][1]

        # Create tag
        tag = create_tag("Conference Room", "location")
        if not tag:
            log_test("Test 4: Schedule by Tags", "FAILED",
                    {"error": "Failed to create tag"})
            results["features_tested"]["tag_targeting"] = "not_implemented"
            return

        results["created_resources"]["tag_ids"].append(tag["id"])

        # Assign tag to DeviceY
        if not assign_tag_to_device(device_y_id, tag["id"]):
            log_test("Test 4: Schedule by Tags", "FAILED",
                    {"error": "Failed to assign tag to device"})
            results["features_tested"]["tag_targeting"] = "not_implemented"
            return

        # Create playlist
        playlist = create_playlist("Tag-Based Playlist", "For tag targeting test")
        if not playlist:
            log_test("Test 4: Schedule by Tags", "FAILED",
                    {"error": "Failed to create playlist"})
            return

        results["created_resources"]["playlist_ids"].append(playlist["id"])

        # Create schedule targeting tag
        schedule = create_schedule({
            "name": "Conference Room Schedule",
            "playlist_id": playlist["id"],
            "priority": 20,
            "start_time": "17:00:00",
            "end_time": "19:00:00",
            "is_active": True,
            "apply_to_all": False,
            "tag_ids": [tag["id"]]
        })

        if not schedule:
            log_test("Test 4: Schedule by Tags", "FAILED",
                    {"error": "Failed to create tag-based schedule"})
            results["features_tested"]["tag_targeting"] = "not_implemented"
            return

        results["created_resources"]["schedule_ids"].append(schedule["id"])

        # Test: Get active schedule for DeviceY at 18:00 (should get it via tag)
        active = get_active_schedule(device_id=device_y_id, time_str="18:00:00")

        if active and "data" in active:
            log_test("Test 4: Schedule by Tags", "PASSED",
                    {"device_got_schedule_via_tag": True, "tag_id": tag["id"]})
            results["features_tested"]["tag_targeting"] = "working"
        else:
            log_test("Test 4: Schedule by Tags", "FAILED",
                    {"error": "Device did not get schedule via tag"})
            results["features_tested"]["tag_targeting"] = "incorrect"

    except Exception as e:
        log_test("Test 4: Schedule by Tags", "FAILED", {"error": str(e)})
        results["features_tested"]["tag_targeting"] = "error"

# ============================================
# TEST 5: Schedule Apply to All
# ============================================
def test_5_apply_to_all():
    """Test schedule with apply_to_all flag"""
    try:
        # Check if we have devices
        if len(results["created_resources"]["device_ids"]) < 2:
            log_test("Test 5: Schedule Apply to All", "SKIPPED",
                    {"error": "No devices available"})
            results["features_tested"]["apply_to_all"] = "skipped"
            return

        device_x_id = results["created_resources"]["device_ids"][0]
        device_y_id = results["created_resources"]["device_ids"][1]

        # Create playlist
        playlist = create_playlist("Global Playlist", "For all devices")
        if not playlist:
            log_test("Test 5: Schedule Apply to All", "FAILED",
                    {"error": "Failed to create playlist"})
            return

        results["created_resources"]["playlist_ids"].append(playlist["id"])

        # Create schedule with apply_to_all=true
        schedule = create_schedule({
            "name": "Global Schedule",
            "playlist_id": playlist["id"],
            "priority": 25,
            "start_time": "20:00:00",
            "end_time": "22:00:00",
            "is_active": True,
            "apply_to_all": True
        })

        if not schedule:
            log_test("Test 5: Schedule Apply to All", "FAILED",
                    {"error": "Failed to create apply_to_all schedule"})
            results["features_tested"]["apply_to_all"] = "not_implemented"
            return

        results["created_resources"]["schedule_ids"].append(schedule["id"])

        # Test: Both devices should get the schedule at 21:00
        active_x = get_active_schedule(device_id=device_x_id, time_str="21:00:00")
        active_y = get_active_schedule(device_id=device_y_id, time_str="21:00:00")

        has_schedule_x = active_x and "data" in active_x
        has_schedule_y = active_y and "data" in active_y

        if has_schedule_x and has_schedule_y:
            log_test("Test 5: Schedule Apply to All", "PASSED",
                    {"both_devices_got_schedule": True})
            results["features_tested"]["apply_to_all"] = "working"
        else:
            log_test("Test 5: Schedule Apply to All", "FAILED",
                    {"error": f"DeviceX: {has_schedule_x}, DeviceY: {has_schedule_y}"})
            results["features_tested"]["apply_to_all"] = "incorrect"

    except Exception as e:
        log_test("Test 5: Schedule Apply to All", "FAILED", {"error": str(e)})
        results["features_tested"]["apply_to_all"] = "error"

# ============================================
# TEST 6: Audit Logs Verification
# ============================================
def test_6_audit_logs():
    """Verify audit logs for schedule operations"""
    try:
        audit_logs = get_audit_logs()

        # Filter logs for this organization and schedule-related actions
        schedule_logs = [
            log for log in audit_logs
            if log.get("organization_id") == ORG_ID
            and (log.get("entity_type") == "schedule" or "schedule" in log.get("action", "").lower())
        ]

        if len(schedule_logs) > 0:
            log_test("Test 6: Audit Logs for Schedules", "PASSED",
                    {"total_schedule_logs": len(schedule_logs)})
            results["audit_logs_verified"] = True
        else:
            log_test("Test 6: Audit Logs for Schedules", "FAILED",
                    {"error": "No schedule audit logs found"})
            results["audit_logs_verified"] = False

    except Exception as e:
        log_test("Test 6: Audit Logs for Schedules", "FAILED", {"error": str(e)})
        results["audit_logs_verified"] = False

# ============================================
# RUN ALL TESTS
# ============================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("AGENT_SCHEDULE - Integration Testing")
    print(f"Organization: TEST_ORG_SCHEDULE (ID: {ORG_ID})")
    print(f"User: admin_sched (ID: {USER_ID})")
    print("="*60 + "\n")

    test_1_basic_schedule_creation()
    test_2_schedule_priority()
    test_3_schedule_by_device_ids()
    test_4_schedule_by_tags()
    test_5_apply_to_all()
    test_6_audit_logs()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(json.dumps(results, indent=2))
    print("="*60 + "\n")

    # Save results to file
    with open("/mnt/g/khoirul/signate/backups/agent_schedule_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to: /mnt/g/khoirul/signate/backups/agent_schedule_results.json")
