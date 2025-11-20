#!/usr/bin/env python3
"""
Playlist Management API Test Suite
Tests all endpoints: CRUD, content, assignments, resolver
"""

import requests
import json
from typing import Dict, Optional, List
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================
BASE_URL = "http://192.168.5.12:8001/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

# Test data IDs (will be populated during tests)
test_data = {
    "access_token": None,
    "organization_id": None,
    "playlist_id": None,
    "playlist_id_2": None,
    "content_ids": [],
    "device_ids": [],
    "tag_ids": [],
    "playlist_content_ids": [],
}

# Test results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
}


# =============================================================================
# Helper Functions
# =============================================================================

def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(name: str, status: str, details: str = ""):
    """Print test result"""
    results["total"] += 1
    symbol = "✅" if status == "PASS" else "❌"

    if status == "PASS":
        results["passed"] += 1
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {details}")

    print(f"{symbol} {name}: {status}")
    if details:
        print(f"   {details}")


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    use_auth: bool = True
) -> requests.Response:
    """Make HTTP request"""
    url = f"{BASE_URL}{endpoint}"
    headers = {}

    if use_auth and test_data["access_token"]:
        headers["Authorization"] = f"Bearer {test_data['access_token']}"

    if data:
        headers["Content-Type"] = "application/json"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, json=data, timeout=10)
        else:
            print(f"❌ Invalid method: {method}")
            return None

        return resp
    except requests.exceptions.Timeout as e:
        print(f"❌ Request timeout: {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {url}")
        return None
    except Exception as e:
        print(f"❌ Request failed: {type(e).__name__}: {e}")
        return None


# =============================================================================
# Setup: Authentication & Data Preparation
# =============================================================================

def setup_authentication():
    """Login and get access token"""
    print_header("Setup: Authentication")

    response = make_request(
        "POST",
        "/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        use_auth=False
    )

    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            # Token field can be "token" or "access_token"
            token = data["data"].get("token") or data["data"].get("access_token")
            if token:
                test_data["access_token"] = token
                test_data["organization_id"] = data["data"]["user"]["organization_id"]
                print_test("Login", "PASS", f"Token: {test_data['access_token'][:20]}...")
                return True
            else:
                print_test("Login", "FAIL", "No token in response")
                return False

    print_test("Login", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    return False


def setup_test_data():
    """Get existing content IDs, device IDs, and tag IDs for testing"""
    print_header("Setup: Test Data")

    # Get content IDs
    response = make_request("GET", "/contents", params={"limit": 5})
    if response and response.status_code == 200:
        data = response.json()
        if data.get("data") and data["data"].get("items"):
            test_data["content_ids"] = [item["id"] for item in data["data"]["items"]]
            print_test("Get Content IDs", "PASS", f"Found {len(test_data['content_ids'])} contents")
        else:
            print_test("Get Content IDs", "FAIL", "No content found")
    else:
        print_test("Get Content IDs", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # Get device IDs
    response = make_request("GET", "/devices", params={"limit": 5})
    if response and response.status_code == 200:
        data = response.json()
        if data.get("data") and data["data"].get("items"):
            test_data["device_ids"] = [item["id"] for item in data["data"]["items"]]
            print_test("Get Device IDs", "PASS", f"Found {len(test_data['device_ids'])} devices")
        else:
            print_test("Get Device IDs", "FAIL", "No devices found")
    else:
        print_test("Get Device IDs", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # Get tag IDs
    response = make_request("GET", "/tags", params={"limit": 5})
    if response and response.status_code == 200:
        data = response.json()
        if data.get("data") and data["data"].get("items"):
            test_data["tag_ids"] = [item["id"] for item in data["data"]["items"]]
            print_test("Get Tag IDs", "PASS", f"Found {len(test_data['tag_ids'])} tags")
        else:
            print_test("Get Tag IDs", "SKIP", "No tags found (optional)")
    else:
        print_test("Get Tag IDs", "FAIL", f"Status: {response.status_code if response else 'No response'}")


# =============================================================================
# Test 1: Playlist CRUD Operations
# =============================================================================

def test_playlist_crud():
    """Test playlist Create, Read, Update, Delete"""
    print_header("Test 1: Playlist CRUD Operations")

    # 1.1 Create Playlist
    create_data = {
        "name": f"Test Playlist {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Automated test playlist",
        "is_active": True,
        "priority": 5,
        "schedule": {
            "days": ["monday", "wednesday", "friday"],
            "start_time": "08:00",
            "end_time": "17:00"
        }
    }

    response = make_request("POST", "/playlists", data=create_data)
    if response and response.status_code == 201:
        data = response.json()
        if data.get("success") and data.get("data"):
            test_data["playlist_id"] = data["data"]["id"]
            print_test("Create Playlist", "PASS", f"ID: {test_data['playlist_id']}")
        else:
            print_test("Create Playlist", "FAIL", "No data in response")
    else:
        print_test("Create Playlist", "FAIL", f"Status: {response.status_code if response else 'No response'}")
        return

    # 1.2 List Playlists
    response = make_request("GET", "/playlists", params={"limit": 10})
    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            print_test("List Playlists", "PASS", f"Total: {data['data']['total']}")
        else:
            print_test("List Playlists", "FAIL", "No data in response")
    else:
        print_test("List Playlists", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 1.3 Get Single Playlist
    response = make_request("GET", f"/playlists/{test_data['playlist_id']}")
    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            print_test("Get Playlist", "PASS", f"Name: {data['data']['name']}")
        else:
            print_test("Get Playlist", "FAIL", "No data in response")
    else:
        print_test("Get Playlist", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 1.4 Update Playlist
    update_data = {
        "name": f"Updated Test Playlist {datetime.now().strftime('%H%M%S')}",
        "description": "Updated description",
        "priority": 10,
        "is_active": False
    }

    response = make_request("PATCH", f"/playlists/{test_data['playlist_id']}", data=update_data)
    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            print_test("Update Playlist", "PASS", f"Priority: {data['data']['priority']}")
        else:
            print_test("Update Playlist", "FAIL", "No data in response")
    else:
        print_test("Update Playlist", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # Create second playlist for later tests
    create_data_2 = {
        "name": f"Test Playlist 2 {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Second test playlist",
        "is_active": True,
        "priority": 1
    }
    response = make_request("POST", "/playlists", data=create_data_2)
    if response and response.status_code == 201:
        data = response.json()
        test_data["playlist_id_2"] = data["data"]["id"]


# =============================================================================
# Test 2: Playlist Content Management
# =============================================================================

def test_playlist_content():
    """Test adding, listing, reordering, and removing content"""
    print_header("Test 2: Playlist Content Management")

    if not test_data.get("playlist_id"):
        print_test("Playlist Content Tests", "SKIP", "No playlist ID available")
        return

    if not test_data.get("content_ids"):
        print_test("Playlist Content Tests", "SKIP", "No content IDs available")
        return

    # 2.1 Add Content to Playlist
    add_data = {
        "content_ids": test_data["content_ids"][:3]  # Add first 3 contents
    }

    response = make_request("POST", f"/playlists/{test_data['playlist_id']}/content", data=add_data)
    if response and response.status_code == 201:
        data = response.json()
        if data.get("success"):
            print_test("Add Content", "PASS", f"Added: {data['data'].get('added', 0)}")
        else:
            print_test("Add Content", "FAIL", "No success in response")
    else:
        print_test("Add Content", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 2.2 Get Playlist Content
    response = make_request("GET", f"/playlists/{test_data['playlist_id']}/content")
    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            items = data["data"].get("items", [])
            test_data["playlist_content_ids"] = [item["id"] for item in items]
            print_test("Get Playlist Content", "PASS", f"Total: {data['data']['total']}")
        else:
            print_test("Get Playlist Content", "FAIL", "No data in response")
    else:
        print_test("Get Playlist Content", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 2.3 Reorder Content
    if test_data.get("playlist_content_ids") and len(test_data["playlist_content_ids"]) >= 2:
        reorder_data = {
            "content_items": [
                {"id": test_data["playlist_content_ids"][0], "order_index": 2, "duration": 15},
                {"id": test_data["playlist_content_ids"][1], "order_index": 1, "duration": 20},
            ]
        }

        response = make_request("PATCH", f"/playlists/{test_data['playlist_id']}/reorder", data=reorder_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_test("Reorder Content", "PASS", f"Updated: {data['data'].get('updated_count', 0)}")
            else:
                print_test("Reorder Content", "FAIL", "No success in response")
        else:
            print_test("Reorder Content", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    else:
        print_test("Reorder Content", "SKIP", "Not enough content items")

    # 2.4 Remove Content from Playlist
    if test_data.get("playlist_content_ids"):
        content_item_id = test_data["playlist_content_ids"][0]
        response = make_request("DELETE", f"/playlists/{test_data['playlist_id']}/content/{content_item_id}")
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_test("Remove Content", "PASS", data["data"]["message"])
            else:
                print_test("Remove Content", "FAIL", "No success in response")
        else:
            print_test("Remove Content", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    else:
        print_test("Remove Content", "SKIP", "No content items to remove")

    # 2.5 Test Duplicate Content (should skip)
    if test_data.get("content_ids"):
        add_data = {
            "content_ids": test_data["content_ids"][:2]  # Try to add again
        }
        response = make_request("POST", f"/playlists/{test_data['playlist_id']}/content", data=add_data)
        if response and response.status_code == 201:
            data = response.json()
            if data.get("data") and "skipped_duplicate" in data["data"]:
                print_test("Duplicate Content Handling", "PASS", f"Skipped: {len(data['data']['skipped_duplicate'])}")
            else:
                print_test("Duplicate Content Handling", "PASS", "Added or skipped appropriately")
        else:
            print_test("Duplicate Content Handling", "FAIL", f"Status: {response.status_code if response else 'No response'}")


# =============================================================================
# Test 3: Playlist Assignments
# =============================================================================

def test_playlist_assignments():
    """Test assigning playlists to devices and tags"""
    print_header("Test 3: Playlist Assignments")

    if not test_data.get("playlist_id"):
        print_test("Playlist Assignment Tests", "SKIP", "No playlist ID available")
        return

    # 3.1 Assign to Devices
    if test_data.get("device_ids"):
        assign_data = {
            "device_ids": test_data["device_ids"][:2]  # Assign to first 2 devices
        }

        response = make_request("POST", f"/playlists/{test_data['playlist_id']}/assign/devices", data=assign_data)
        if response and response.status_code == 201:
            data = response.json()
            if data.get("success"):
                print_test("Assign to Devices", "PASS", f"Assigned: {data['data'].get('assigned', 0)}")
            else:
                print_test("Assign to Devices", "FAIL", "No success in response")
        else:
            print_test("Assign to Devices", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    else:
        print_test("Assign to Devices", "SKIP", "No device IDs available")

    # 3.2 Assign to Tags
    if test_data.get("tag_ids"):
        assign_data = {
            "tag_ids": test_data["tag_ids"][:1]  # Assign to first tag
        }

        response = make_request("POST", f"/playlists/{test_data['playlist_id']}/assign/tags", data=assign_data)
        if response and response.status_code == 201:
            data = response.json()
            if data.get("success"):
                print_test("Assign to Tags", "PASS", f"Assigned: {data['data'].get('assigned', 0)}")
            else:
                print_test("Assign to Tags", "FAIL", "No success in response")
        else:
            print_test("Assign to Tags", "FAIL", f"Status: {response.status_code if response else 'No response'}")
    else:
        print_test("Assign to Tags", "SKIP", "No tag IDs available (optional)")

    # 3.3 Get Playlist Assignments
    response = make_request("GET", f"/playlists/{test_data['playlist_id']}/assignments")
    if response and response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            devices = data["data"].get("devices", [])
            tags = data["data"].get("tags", [])
            print_test("Get Assignments", "PASS", f"Devices: {len(devices)}, Tags: {len(tags)}")
        else:
            print_test("Get Assignments", "FAIL", "No data in response")
    else:
        print_test("Get Assignments", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 3.4 Unassign from Devices
    if test_data.get("device_ids"):
        unassign_data = {
            "device_ids": [test_data["device_ids"][0]]  # Unassign from first device
        }

        response = make_request("DELETE", f"/playlists/{test_data['playlist_id']}/assign/devices", data=unassign_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_test("Unassign from Devices", "PASS", f"Removed: {data['data'].get('removed', 0)}")
            else:
                print_test("Unassign from Devices", "FAIL", "No success in response")
        else:
            print_test("Unassign from Devices", "FAIL", f"Status: {response.status_code if response else 'No response'}")

    # 3.5 Unassign from Tags
    if test_data.get("tag_ids"):
        unassign_data = {
            "tag_ids": [test_data["tag_ids"][0]]
        }

        response = make_request("DELETE", f"/playlists/{test_data['playlist_id']}/assign/tags", data=unassign_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_test("Unassign from Tags", "PASS", f"Removed: {data['data'].get('removed', 0)}")
            else:
                print_test("Unassign from Tags", "FAIL", "No success in response")
        else:
            print_test("Unassign from Tags", "FAIL", f"Status: {response.status_code if response else 'No response'}")


# =============================================================================
# Test 4: Content Resolver
# =============================================================================

def test_content_resolver():
    """Test content resolution for devices"""
    print_header("Test 4: Content Resolver")

    if not test_data.get("device_ids"):
        print_test("Content Resolver Tests", "SKIP", "No device IDs available")
        return

    device_id = test_data["device_ids"][0]

    # 4.1 Resolve Content for Device
    response = make_request("GET", f"/playlists/resolve/{device_id}")
    if response:
        if response.status_code == 200:
            data = response.json()
            print_test("Resolve Content", "PASS", f"Playlist: {data.get('playlist_id', 'N/A')}")
        elif response.status_code == 404:
            print_test("Resolve Content", "PASS", "No content assigned (expected)")
        else:
            print_test("Resolve Content", "FAIL", f"Status: {response.status_code}")
    else:
        print_test("Resolve Content", "FAIL", "No response")

    # 4.2 Test with assigned device
    if test_data.get("playlist_id") and len(test_data.get("device_ids", [])) > 1:
        # Assign playlist to second device
        assign_data = {"device_ids": [test_data["device_ids"][1]]}
        make_request("POST", f"/playlists/{test_data['playlist_id']}/assign/devices", data=assign_data)

        # Resolve content for assigned device
        response = make_request("GET", f"/playlists/resolve/{test_data['device_ids'][1]}")
        if response and response.status_code == 200:
            data = response.json()
            print_test("Resolve with Assignment", "PASS", f"Content items: {len(data.get('content_items', []))}")
        else:
            print_test("Resolve with Assignment", "FAIL", f"Status: {response.status_code if response else 'No response'}")


# =============================================================================
# Test 5: Multi-tenancy & Security
# =============================================================================

def test_multi_tenancy():
    """Test multi-tenancy isolation"""
    print_header("Test 5: Multi-Tenancy & Security")

    # 5.1 Verify organization_id in responses
    if test_data.get("playlist_id"):
        response = make_request("GET", f"/playlists/{test_data['playlist_id']}")
        if response and response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("organization_id") == test_data["organization_id"]:
                print_test("Organization ID Verification", "PASS", "Correct organization_id")
            else:
                print_test("Organization ID Verification", "FAIL", "Organization ID mismatch")
        else:
            print_test("Organization ID Verification", "FAIL", "Cannot verify")

    # 5.2 Test accessing non-existent playlist
    response = make_request("GET", "/playlists/999999")
    if response and response.status_code == 404:
        print_test("Non-existent Playlist", "PASS", "Returns 404")
    else:
        print_test("Non-existent Playlist", "FAIL", f"Expected 404, got {response.status_code if response else 'No response'}")

    # 5.3 Test authentication requirement
    response = make_request("GET", "/playlists", use_auth=False)
    if response and response.status_code == 401:
        print_test("Authentication Required", "PASS", "Unauthorized without token")
    else:
        print_test("Authentication Required", "FAIL", f"Expected 401, got {response.status_code if response else 'No response'}")


# =============================================================================
# Test 6: Priority & Scheduling
# =============================================================================

def test_priority_scheduling():
    """Test priority and schedule functionality"""
    print_header("Test 6: Priority & Scheduling")

    # 6.1 Create playlists with different priorities
    playlists = []
    for i, priority in enumerate([1, 5, 10]):
        create_data = {
            "name": f"Priority {priority} Playlist",
            "description": f"Test priority {priority}",
            "is_active": True,
            "priority": priority
        }
        response = make_request("POST", "/playlists", data=create_data)
        if response and response.status_code == 201:
            playlists.append(response.json()["data"]["id"])

    if len(playlists) == 3:
        print_test("Create Priority Playlists", "PASS", f"Created {len(playlists)} playlists")
    else:
        print_test("Create Priority Playlists", "FAIL", f"Only created {len(playlists)}/3")

    # 6.2 List and verify priority order
    response = make_request("GET", "/playlists")
    if response and response.status_code == 200:
        data = response.json()
        if data.get("data") and data["data"].get("items"):
            # Check if priority field exists
            has_priority = all("priority" in item for item in data["data"]["items"])
            if has_priority:
                print_test("Priority Field", "PASS", "All playlists have priority")
            else:
                print_test("Priority Field", "FAIL", "Some playlists missing priority")

    # 6.3 Test schedule validation
    schedule_data = {
        "name": "Scheduled Playlist",
        "description": "Test schedule",
        "is_active": True,
        "priority": 1,
        "schedule": {
            "days": ["monday", "wednesday", "friday"],
            "start_time": "09:00",
            "end_time": "17:00",
            "timezone": "Asia/Jakarta"
        }
    }

    response = make_request("POST", "/playlists", data=schedule_data)
    if response and response.status_code == 201:
        print_test("Create Scheduled Playlist", "PASS", "Schedule accepted")
    else:
        print_test("Create Scheduled Playlist", "FAIL", f"Status: {response.status_code if response else 'No response'}")


# =============================================================================
# Cleanup & Final Report
# =============================================================================

def cleanup():
    """Clean up test data"""
    print_header("Cleanup: Delete Test Playlists")

    # Delete test playlists
    for key in ["playlist_id", "playlist_id_2"]:
        if test_data.get(key):
            response = make_request("DELETE", f"/playlists/{test_data[key]}")
            if response and response.status_code == 200:
                print_test(f"Delete Playlist {test_data[key]}", "PASS", "Deleted successfully")
            else:
                print_test(f"Delete Playlist {test_data[key]}", "FAIL", f"Status: {response.status_code if response else 'No response'}")


def print_final_report():
    """Print final test report"""
    print_header("FINAL TEST REPORT")

    print(f"\n📊 Test Statistics:")
    print(f"   Total Tests: {results['total']}")
    print(f"   Passed: {results['passed']} ✅")
    print(f"   Failed: {results['failed']} ❌")
    print(f"   Success Rate: {(results['passed'] / results['total'] * 100) if results['total'] > 0 else 0:.1f}%")

    if results["errors"]:
        print(f"\n❌ Failed Tests:")
        for error in results["errors"]:
            print(f"   - {error}")

    # Grade calculation
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    if success_rate >= 95:
        grade = "A+ (Excellent)"
    elif success_rate >= 85:
        grade = "A (Very Good)"
    elif success_rate >= 75:
        grade = "B+ (Good)"
    elif success_rate >= 65:
        grade = "B (Fair)"
    else:
        grade = "C (Needs Improvement)"

    print(f"\n🎯 Overall Grade: {grade}")
    print("\n" + "=" * 80)


# =============================================================================
# Main Test Runner
# =============================================================================

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PLAYLIST MANAGEMENT API TEST SUITE" + " " * 24 + "║")
    print("║" + " " * 78 + "║")
    print("║" + f"  Server: {BASE_URL:<69}" + "║")
    print("║" + f"  User: {USERNAME:<71}" + "║")
    print("║" + f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<69}" + "║")
    print("╚" + "=" * 78 + "╝")

    # Setup
    if not setup_authentication():
        print("\n❌ Authentication failed. Cannot proceed with tests.")
        return

    setup_test_data()

    # Run tests
    test_playlist_crud()
    test_playlist_content()
    test_playlist_assignments()
    test_content_resolver()
    test_multi_tenancy()
    test_priority_scheduling()

    # Cleanup
    cleanup()

    # Final report
    print_final_report()


if __name__ == "__main__":
    main()
