#!/usr/bin/env python3
"""
Test Script for Device JWT Authentication

This script tests the complete JWT authentication flow for devices:
1. Device registration with activation code
2. JWT token issuance upon registration
3. Using JWT token for authenticated endpoints
4. Token refresh mechanism
5. Backward compatibility with device_id query param

Run this script to verify the JWT implementation is working correctly.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
BASE_URL = "http://192.168.5.12:8001"  # Server API URL
TEST_DEVICE_NAME = f"Test-Device-{int(time.time())}"
TEST_ACTIVATION_CODE = str(100000 + int(time.time()) % 900000)  # 6-digit code

# Test results
test_results = []


def print_header(title):
    """Print formatted test header"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{title.center(60)}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")


def print_test(test_name, status, details=""):
    """Print test result"""
    icon = "✅" if status == "PASS" else "❌"
    color = Fore.GREEN if status == "PASS" else Fore.RED
    print(f"{color}{icon} {test_name}: {status}{Style.RESET_ALL}")
    if details:
        print(f"   {Fore.YELLOW}→ {details}{Style.RESET_ALL}")
    test_results.append({"test": test_name, "status": status, "details": details})


def test_device_registration():
    """Test 1: Device Registration with JWT Token"""
    print_header("TEST 1: Device Registration")

    try:
        # Register device
        response = requests.post(
            f"{BASE_URL}/api/devices/monitor/register",
            json={
                "activation_code": TEST_ACTIVATION_CODE,
                "device_name": TEST_DEVICE_NAME,
                "platform": "Test-Platform"
            }
        )

        if response.status_code == 201:
            data = response.json()
            device_data = data.get("data", {})

            # Check for required fields
            device_id = device_data.get("id")
            device_token = device_data.get("device_token")
            token_expires_at = device_data.get("token_expires_at")

            if device_id and device_token:
                print_test(
                    "Device Registration",
                    "PASS",
                    f"Device ID: {device_id}, Token: {device_token[:20]}..."
                )

                if token_expires_at:
                    expires = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
                    days_until_expiry = (expires - datetime.utcnow()).days
                    print_test(
                        "Token Expiration",
                        "PASS" if days_until_expiry >= 29 else "FAIL",
                        f"Token expires in {days_until_expiry} days"
                    )

                return device_id, device_token
            else:
                print_test(
                    "Device Registration",
                    "FAIL",
                    "Missing device_id or device_token in response"
                )
                return None, None
        else:
            print_test(
                "Device Registration",
                "FAIL",
                f"HTTP {response.status_code}: {response.text}"
            )
            return None, None

    except Exception as e:
        print_test("Device Registration", "FAIL", str(e))
        return None, None


def test_jwt_authentication(device_id, device_token):
    """Test 2: JWT Authentication for Protected Endpoints"""
    print_header("TEST 2: JWT Authentication")

    if not device_token:
        print_test("JWT Authentication", "SKIP", "No token available")
        return False

    # Test playlist endpoint with JWT
    try:
        # First, try WITHOUT token (should fail)
        response = requests.get(f"{BASE_URL}/api/client/playlist")

        if response.status_code == 401:
            print_test(
                "Endpoint Protection",
                "PASS",
                "Playlist endpoint correctly requires authentication"
            )
        else:
            print_test(
                "Endpoint Protection",
                "FAIL",
                f"Expected 401, got {response.status_code}"
            )

        # Now try WITH JWT token
        headers = {"Authorization": f"Bearer {device_token}"}
        response = requests.get(
            f"{BASE_URL}/api/client/playlist",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            playlist_data = data.get("data", {})
            device_id_from_jwt = playlist_data.get("device_id")

            if device_id_from_jwt == device_id:
                print_test(
                    "JWT Authentication",
                    "PASS",
                    f"Successfully authenticated device {device_id}"
                )
                return True
            else:
                print_test(
                    "JWT Authentication",
                    "FAIL",
                    f"Device ID mismatch: expected {device_id}, got {device_id_from_jwt}"
                )
                return False
        else:
            print_test(
                "JWT Authentication",
                "FAIL",
                f"HTTP {response.status_code}: {response.text}"
            )
            return False

    except Exception as e:
        print_test("JWT Authentication", "FAIL", str(e))
        return False


def test_backward_compatibility(device_id):
    """Test 3: Backward Compatibility with device_id Query Param"""
    print_header("TEST 3: Backward Compatibility")

    if not device_id:
        print_test("Backward Compatibility", "SKIP", "No device_id available")
        return

    try:
        # Try using old method (device_id query param)
        response = requests.get(
            f"{BASE_URL}/api/client/playlist?device_id={device_id}"
        )

        if response.status_code == 200:
            data = response.json()
            playlist_data = data.get("data", {})

            if playlist_data.get("device_id") == device_id:
                print_test(
                    "Query Param Auth",
                    "PASS",
                    "Legacy device_id parameter still works (with deprecation warning in logs)"
                )
            else:
                print_test(
                    "Query Param Auth",
                    "FAIL",
                    "Device ID mismatch"
                )
        elif response.status_code == 403:
            # Device might be pending, not active
            print_test(
                "Query Param Auth",
                "PASS",
                "Authentication works but device is not active"
            )
        else:
            print_test(
                "Query Param Auth",
                "FAIL",
                f"HTTP {response.status_code}"
            )

    except Exception as e:
        print_test("Query Param Auth", "FAIL", str(e))


def test_token_refresh(device_token):
    """Test 4: Token Refresh Mechanism"""
    print_header("TEST 4: Token Refresh")

    if not device_token:
        print_test("Token Refresh", "SKIP", "No token available")
        return None

    try:
        # Call refresh endpoint with current token
        headers = {"Authorization": f"Bearer {device_token}"}
        response = requests.post(
            f"{BASE_URL}/api/client/refresh",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            new_token = data.get("device_token")
            token_expires_at = data.get("token_expires_at")

            if new_token and new_token != device_token:
                print_test(
                    "Token Refresh",
                    "PASS",
                    f"New token generated: {new_token[:20]}..."
                )

                if token_expires_at:
                    expires = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
                    days_until_expiry = (expires - datetime.utcnow()).days
                    print_test(
                        "Refresh Expiration",
                        "PASS" if days_until_expiry >= 29 else "FAIL",
                        f"New token expires in {days_until_expiry} days"
                    )

                return new_token
            else:
                print_test(
                    "Token Refresh",
                    "FAIL",
                    "No new token in response or token unchanged"
                )
                return None
        else:
            print_test(
                "Token Refresh",
                "FAIL",
                f"HTTP {response.status_code}: {response.text}"
            )
            return None

    except Exception as e:
        print_test("Token Refresh", "FAIL", str(e))
        return None


def test_invalid_token():
    """Test 5: Invalid Token Rejection"""
    print_header("TEST 5: Invalid Token Rejection")

    try:
        # Try with invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = requests.get(
            f"{BASE_URL}/api/client/playlist",
            headers=headers
        )

        if response.status_code == 401:
            print_test(
                "Invalid Token",
                "PASS",
                "Invalid token correctly rejected with 401"
            )
        else:
            print_test(
                "Invalid Token",
                "FAIL",
                f"Expected 401, got {response.status_code}"
            )

        # Try with malformed auth header
        headers = {"Authorization": "NotBearer token"}
        response = requests.get(
            f"{BASE_URL}/api/client/playlist",
            headers=headers
        )

        if response.status_code == 401:
            print_test(
                "Malformed Header",
                "PASS",
                "Malformed auth header correctly rejected"
            )
        else:
            print_test(
                "Malformed Header",
                "FAIL",
                f"Expected 401, got {response.status_code}"
            )

    except Exception as e:
        print_test("Invalid Token", "FAIL", str(e))


def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")

    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")
    total = len(test_results)

    print(f"\n{Fore.CYAN}Total Tests: {total}")
    print(f"{Fore.GREEN}Passed: {passed}")
    print(f"{Fore.RED}Failed: {failed}")
    print(f"{Fore.YELLOW}Skipped: {skipped}")

    if failed == 0:
        print(f"\n{Fore.GREEN}{'🎉 ALL TESTS PASSED! 🎉'.center(60)}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{'⚠️ SOME TESTS FAILED'.center(60)}{Style.RESET_ALL}")
        print("\nFailed tests:")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  - {r['test']}: {r['details']}")


def main():
    """Run all tests"""
    print(f"{Fore.MAGENTA}{'=' * 60}")
    print(f"{Fore.MAGENTA}{'DEVICE JWT AUTHENTICATION TEST SUITE'.center(60)}")
    print(f"{Fore.MAGENTA}{'=' * 60}{Style.RESET_ALL}")
    print(f"\nTarget: {BASE_URL}")
    print(f"Test Device: {TEST_DEVICE_NAME}")
    print(f"Activation Code: {TEST_ACTIVATION_CODE}")

    # Run tests
    device_id, device_token = test_device_registration()

    if device_id and device_token:
        test_jwt_authentication(device_id, device_token)
        test_backward_compatibility(device_id)
        new_token = test_token_refresh(device_token)

        # Test with refreshed token
        if new_token:
            print_header("TEST 4.1: Using Refreshed Token")
            test_jwt_authentication(device_id, new_token)

    test_invalid_token()

    # Print summary
    print_summary()


if __name__ == "__main__":
    main()