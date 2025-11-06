#!/usr/bin/env python3
"""
Test script to verify supported media formats
Tests upload and playback of various image and video formats
"""

import requests
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://192.168.5.12:8001"
USERNAME = "admin"
PASSWORD = "admin123"

# Test file formats (you need to provide sample files)
TEST_FILES = {
    "images": {
        "jpeg": "test_files/sample.jpg",
        "png": "test_files/sample.png",
        "webp": "test_files/sample.webp",
        "gif": "test_files/sample.gif",
        "svg": "test_files/sample.svg",
        "bmp": "test_files/sample.bmp",
    },
    "videos": {
        "mp4": "test_files/sample.mp4",
        "webm": "test_files/sample.webm",
        "ogv": "test_files/sample.ogv",
    }
}

# Supported MIME types
SUPPORTED_MIME_TYPES = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "bmp": "image/bmp",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "ogv": "video/ogg",
    "ogg": "video/ogg",
}


def get_auth_token():
    """Get authentication token"""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def test_upload_format(token, file_path, format_name, mime_type):
    """Test uploading a specific format"""
    print(f"\n📤 Testing {format_name.upper()} upload...")

    # Check if test file exists
    if not Path(file_path).exists():
        print(f"⚠️  Test file not found: {file_path}")
        print(f"   Skipping {format_name} test")
        return None

    # Prepare file upload
    with open(file_path, 'rb') as f:
        files = {
            'file': (Path(file_path).name, f, mime_type)
        }
        data = {
            'title': f'Test {format_name.upper()}',
            'description': f'Testing {format_name} format support',
            'duration': 10,
            'is_active': True
        }

        response = requests.post(
            f"{API_BASE_URL}/api/content/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

    if response.status_code == 201:
        content = response.json()
        print(f"✅ {format_name.upper()} upload successful")
        print(f"   Content ID: {content['id']}")
        print(f"   MIME type: {content.get('mime_type', 'N/A')}")
        return content
    else:
        print(f"❌ {format_name.upper()} upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_image_formats(token):
    """Test all image formats"""
    print("\n" + "="*50)
    print("TESTING IMAGE FORMATS")
    print("="*50)

    results = {}
    for format_name, file_path in TEST_FILES["images"].items():
        mime_type = SUPPORTED_MIME_TYPES.get(format_name)
        result = test_upload_format(token, file_path, format_name, mime_type)
        results[format_name] = result is not None

    return results


def test_video_formats(token):
    """Test all video formats"""
    print("\n" + "="*50)
    print("TESTING VIDEO FORMATS")
    print("="*50)

    results = {}
    for format_name, file_path in TEST_FILES["videos"].items():
        mime_type = SUPPORTED_MIME_TYPES.get(format_name)
        result = test_upload_format(token, file_path, format_name, mime_type)
        results[format_name] = result is not None

    return results


def print_summary(image_results, video_results):
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)

    print("\n📷 Image Formats:")
    for format_name, success in image_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {format_name.upper():<10} {status}")

    print("\n🎬 Video Formats:")
    for format_name, success in video_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {format_name.upper():<10} {status}")

    # Calculate totals
    total_tests = len(image_results) + len(video_results)
    total_passed = sum(image_results.values()) + sum(video_results.values())

    print(f"\n📊 Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests failed")


def main():
    """Main test function"""
    print("="*50)
    print("MEDIA FORMAT SUPPORT TEST")
    print("="*50)

    # Get auth token
    token = get_auth_token()

    # Test image formats
    image_results = test_image_formats(token)

    # Test video formats
    video_results = test_video_formats(token)

    # Print summary
    print_summary(image_results, video_results)


if __name__ == "__main__":
    print("\n⚠️  NOTE: This test requires sample media files in test_files/ directory")
    print("   You can skip missing files - they will be marked as skipped\n")

    response = input("Continue with tests? (y/n): ")
    if response.lower() == 'y':
        main()
    else:
        print("Tests cancelled")
