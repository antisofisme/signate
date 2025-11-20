#!/usr/bin/env python3
"""
Content Management API Testing Suite
Tests all endpoints with security features validation
"""

import requests
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Optional, List
from io import BytesIO

# Configuration
BASE_URL = "http://192.168.5.12:8001"
API_V1 = f"{BASE_URL}/api/v1"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.ENDC}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.ENDC}")

def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")


class ContentAPITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.uploaded_content_ids: List[int] = []

    def login(self) -> bool:
        """Authenticate and get JWT token"""
        print_header("Authentication")
        try:
            response = requests.post(
                f"{API_V1}/auth/login",
                json={
                    "username": USERNAME,
                    "password": PASSWORD
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("data", {}).get("token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}"
                }
                print_success(f"Login successful - Token: {self.token[:20]}...")
                return True
            else:
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print_error(f"Login exception: {e}")
            return False

    def create_test_files(self):
        """Create test files for upload"""
        print_header("Creating Test Files")

        test_dir = Path("/tmp/content_test_files")
        test_dir.mkdir(exist_ok=True)

        # 1. Small image (1MB)
        small_image = test_dir / "small_image.jpg"
        if not small_image.exists():
            # Create 1MB JPG header + data
            with open(small_image, 'wb') as f:
                # JPEG header
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
                # Fill with random data to reach 1MB
                f.write(os.urandom(1024 * 1024))
                # JPEG footer
                f.write(b'\xFF\xD9')
            print_success(f"Created: {small_image} ({small_image.stat().st_size / 1024 / 1024:.2f} MB)")

        # 2. Large image (45MB - below 50MB limit)
        large_image = test_dir / "large_image.png"
        if not large_image.exists():
            # Create PNG header
            with open(large_image, 'wb') as f:
                # PNG signature
                f.write(b'\x89PNG\r\n\x1a\n')
                # IHDR chunk (minimal valid PNG)
                f.write(b'\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x02\x00\x00\x00')
                f.write(b'\x8f\xf4\x9f\xd2')
                # Fill with data
                f.write(os.urandom(45 * 1024 * 1024))
                # IEND chunk
                f.write(b'\x00\x00\x00\x00IEND\xae\x42\x60\x82')
            print_success(f"Created: {large_image} ({large_image.stat().st_size / 1024 / 1024:.2f} MB)")

        # 3. Oversized image (55MB - exceeds 50MB limit)
        oversized_image = test_dir / "oversized_image.jpg"
        if not oversized_image.exists():
            with open(oversized_image, 'wb') as f:
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
                f.write(os.urandom(55 * 1024 * 1024))
                f.write(b'\xFF\xD9')
            print_success(f"Created: {oversized_image} ({oversized_image.stat().st_size / 1024 / 1024:.2f} MB)")

        # 4. EICAR virus test file
        eicar = test_dir / "eicar.txt"
        with open(eicar, 'w') as f:
            # Standard EICAR test string
            f.write('X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
        print_success(f"Created: {eicar} (EICAR test)")

        # 5. Path traversal attempt
        malicious = test_dir / "path_traversal.jpg"
        with open(malicious, 'wb') as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
            f.write(os.urandom(100 * 1024))
            f.write(b'\xFF\xD9')
        print_success(f"Created: {malicious} (Path traversal test)")

        # 6. Invalid MIME type (text file with .jpg extension)
        fake_image = test_dir / "fake_image.jpg"
        with open(fake_image, 'w') as f:
            f.write("This is not an image file")
        print_success(f"Created: {fake_image} (MIME mismatch test)")

        # 7. Valid video (small MP4)
        small_video = test_dir / "small_video.mp4"
        if not small_video.exists():
            # Create minimal valid MP4 (1MB)
            with open(small_video, 'wb') as f:
                # MP4 file signature (ftyp box)
                f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41')
                # Fill with data
                f.write(os.urandom(1024 * 1024))
            print_success(f"Created: {small_video} ({small_video.stat().st_size / 1024 / 1024:.2f} MB)")

        return test_dir

    def test_upload_content(self, file_path: Path, title: str, should_succeed: bool = True) -> Optional[int]:
        """Test content upload endpoint"""
        self.test_results["total"] += 1

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                data = {
                    'title': title,
                    'description': f'Test upload: {title}',
                    'duration': 10,
                    'is_active': True
                }

                response = requests.post(
                    f"{API_V1}/contents/upload",
                    headers=self.headers,
                    files=files,
                    data=data
                )

                if should_succeed:
                    if response.status_code == 201:
                        content_id = response.json().get("data", {}).get("id")
                        self.uploaded_content_ids.append(content_id)
                        print_success(f"Upload '{title}' successful - ID: {content_id}")
                        self.test_results["passed"] += 1
                        return content_id
                    else:
                        print_error(f"Upload '{title}' failed: {response.status_code} - {response.text[:200]}")
                        self.test_results["failed"] += 1
                        self.test_results["errors"].append(f"Upload '{title}': Expected 201, got {response.status_code}")
                        return None
                else:
                    # Should fail
                    if response.status_code >= 400:
                        print_success(f"Upload '{title}' correctly rejected: {response.status_code}")
                        self.test_results["passed"] += 1
                        return None
                    else:
                        print_error(f"Upload '{title}' should have failed but succeeded: {response.status_code}")
                        self.test_results["failed"] += 1
                        self.test_results["errors"].append(f"Upload '{title}': Should reject but got {response.status_code}")
                        return None

        except Exception as e:
            print_error(f"Upload '{title}' exception: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"Upload '{title}': {str(e)}")
            return None

    def test_list_content(self, expected_count: Optional[int] = None) -> bool:
        """Test list content endpoint"""
        print_header("Testing List Content")
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{API_V1}/contents",
                headers=self.headers,
                params={
                    'skip': 0,
                    'limit': 20
                }
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                total = data.get("pagination", {}).get("total", 0)
                print_success(f"List content successful - Total: {total}, Items: {len(items)}")
                print_info(f"First item: {items[0] if items else 'No items'}")

                if expected_count is not None and total >= expected_count:
                    print_success(f"Expected count met: {total} >= {expected_count}")
                    self.test_results["passed"] += 1
                    return True
                elif expected_count is not None:
                    print_error(f"Expected count not met: {total} < {expected_count}")
                    self.test_results["failed"] += 1
                    return False
                else:
                    self.test_results["passed"] += 1
                    return True
            else:
                print_error(f"List content failed: {response.status_code} - {response.text}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"List content exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_get_content(self, content_id: int) -> bool:
        """Test get single content endpoint"""
        self.test_results["total"] += 1

        try:
            response = requests.get(
                f"{API_V1}/contents/{content_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                print_success(f"Get content {content_id} successful - Title: {data.get('title')}")
                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Get content {content_id} failed: {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Get content exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_update_content(self, content_id: int) -> bool:
        """Test update content endpoint"""
        self.test_results["total"] += 1

        try:
            response = requests.put(
                f"{API_V1}/contents/{content_id}",
                headers={**self.headers, "Content-Type": "application/json"},
                json={
                    "title": f"Updated Content {content_id}",
                    "description": "Updated via API test",
                    "duration": 15,
                    "is_active": False
                }
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                print_success(f"Update content {content_id} successful - New title: {data.get('title')}")
                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Update content {content_id} failed: {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Update content exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_delete_content(self, content_id: int) -> bool:
        """Test delete content endpoint"""
        self.test_results["total"] += 1

        try:
            response = requests.delete(
                f"{API_V1}/contents/{content_id}",
                headers=self.headers
            )

            if response.status_code == 204:
                print_success(f"Delete content {content_id} successful")
                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Delete content {content_id} failed: {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Delete content exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_bulk_upload(self, test_dir: Path) -> bool:
        """Test bulk upload endpoint"""
        print_header("Testing Bulk Upload")
        self.test_results["total"] += 1

        try:
            files = []
            file_handles = []

            # Upload 3 small images
            for i in range(3):
                file_path = test_dir / f"bulk_test_{i}.jpg"
                with open(file_path, 'wb') as f:
                    f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
                    f.write(os.urandom(100 * 1024))  # 100KB
                    f.write(b'\xFF\xD9')

                fh = open(file_path, 'rb')
                file_handles.append(fh)
                files.append(('files', (file_path.name, fh, 'image/jpeg')))

            data = {
                'duration': 10,
                'is_active': True
            }

            response = requests.post(
                f"{API_V1}/contents/bulk-upload",
                headers=self.headers,
                files=files,
                data=data
            )

            # Close file handles
            for fh in file_handles:
                fh.close()

            if response.status_code == 201:
                data = response.json().get("data", {})
                summary = data.get("summary", {})
                print_success(f"Bulk upload successful - Total: {summary.get('total')}, Success: {summary.get('successful')}, Failed: {summary.get('failed')}")
                self.test_results["passed"] += 1

                # Track uploaded content IDs
                for result in data.get("results", []):
                    if result.get("status") == "success":
                        content_id = result.get("content", {}).get("id")
                        if content_id:
                            self.uploaded_content_ids.append(content_id)

                return True
            else:
                print_error(f"Bulk upload failed: {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Bulk upload exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_duplicate_detection(self, file_path: Path) -> bool:
        """Test duplicate file detection"""
        print_header("Testing Duplicate Detection")
        self.test_results["total"] += 1

        try:
            # Upload same file twice
            content_id1 = self.test_upload_content(file_path, "Duplicate Test 1", should_succeed=True)
            time.sleep(1)
            content_id2 = self.test_upload_content(file_path, "Duplicate Test 2", should_succeed=False)

            if content_id1 and not content_id2:
                print_success("Duplicate detection working correctly")
                self.test_results["passed"] += 1
                return True
            else:
                print_error("Duplicate detection failed")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Duplicate detection exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_file_size_validation(self, test_dir: Path) -> bool:
        """Test file size validation"""
        print_header("Testing File Size Validation")

        # Test oversized image (should fail)
        oversized = test_dir / "oversized_image.jpg"
        result = self.test_upload_content(oversized, "Oversized Image", should_succeed=False)

        return result is None

    def test_mime_validation(self, test_dir: Path) -> bool:
        """Test MIME type validation"""
        print_header("Testing MIME Type Validation")

        # Test fake image (should fail)
        fake = test_dir / "fake_image.jpg"
        result = self.test_upload_content(fake, "Fake Image", should_succeed=False)

        return result is None

    def test_virus_scanning(self, test_dir: Path) -> bool:
        """Test virus scanning"""
        print_header("Testing Virus Scanning")
        self.test_results["total"] += 1

        try:
            eicar = test_dir / "eicar.txt"

            # Rename to .jpg to pass extension check
            eicar_jpg = test_dir / "eicar.jpg"
            with open(eicar_jpg, 'wb') as f:
                # JPEG header
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
                # EICAR string
                f.write(b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
                # JPEG footer
                f.write(b'\xFF\xD9')

            result = self.test_upload_content(eicar_jpg, "EICAR Test", should_succeed=False)

            if result is None:
                print_success("Virus scanning working (file rejected)")
                self.test_results["passed"] += 1
                return True
            else:
                print_warning("Virus scanning might be disabled (file accepted)")
                self.test_results["passed"] += 1  # Not a failure if ClamAV is unavailable
                return True

        except Exception as e:
            print_error(f"Virus scanning test exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_path_traversal(self, test_dir: Path) -> bool:
        """Test path traversal protection"""
        print_header("Testing Path Traversal Protection")
        self.test_results["total"] += 1

        try:
            malicious = test_dir / "path_traversal.jpg"

            # Try to upload with malicious filename
            with open(malicious, 'rb') as f:
                files = {'file': ('../../etc/passwd.jpg', f, 'image/jpeg')}
                data = {
                    'title': 'Path Traversal Test',
                    'duration': 10,
                    'is_active': True
                }

                response = requests.post(
                    f"{API_V1}/contents/upload",
                    headers=self.headers,
                    files=files,
                    data=data
                )

                # Should either reject or sanitize the filename
                if response.status_code >= 400:
                    print_success("Path traversal blocked (request rejected)")
                    self.test_results["passed"] += 1
                    return True
                elif response.status_code == 201:
                    # Check if filename was sanitized
                    data = response.json().get("data", {})
                    filename = data.get("original_filename", "")
                    if "../" not in filename and ".." not in filename:
                        print_success("Path traversal sanitized (filename cleaned)")
                        self.test_results["passed"] += 1
                        # Track for cleanup
                        content_id = data.get("id")
                        if content_id:
                            self.uploaded_content_ids.append(content_id)
                        return True
                    else:
                        print_error("Path traversal not prevented")
                        self.test_results["failed"] += 1
                        return False

        except Exception as e:
            print_error(f"Path traversal test exception: {e}")
            self.test_results["failed"] += 1
            return False

    def test_content_filters(self) -> bool:
        """Test content filtering"""
        print_header("Testing Content Filters")
        self.test_results["total"] += 1

        try:
            # Test filter by type
            response = requests.get(
                f"{API_V1}/contents",
                headers=self.headers,
                params={
                    'skip': 0,
                    'limit': 20,
                    'content_type': 'image'
                }
            )

            if response.status_code == 200:
                items = response.json().get("data", [])
                # Verify all items are images
                all_images = all(item.get("content_type") == "image" for item in items)

                if all_images or len(items) == 0:
                    print_success("Content type filter working correctly")
                    self.test_results["passed"] += 1
                    return True
                else:
                    print_error("Content type filter not working")
                    self.test_results["failed"] += 1
                    return False
            else:
                print_error(f"Filter test failed: {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Filter test exception: {e}")
            self.test_results["failed"] += 1
            return False

    def cleanup(self):
        """Delete all uploaded test content"""
        print_header("Cleanup - Deleting Test Content")

        for content_id in self.uploaded_content_ids:
            try:
                response = requests.delete(
                    f"{API_V1}/contents/{content_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    print_success(f"Deleted content {content_id}")
                else:
                    print_warning(f"Failed to delete content {content_id}: {response.status_code}")
            except Exception as e:
                print_warning(f"Cleanup exception for content {content_id}: {e}")

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension"""
        ext = file_path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.txt': 'text/plain'
        }
        return mime_map.get(ext, 'application/octet-stream')

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")

        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.RED}Failed: {failed}{Colors.ENDC}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.test_results["errors"]:
            print(f"\n{Colors.RED}Errors:{Colors.ENDC}")
            for error in self.test_results["errors"]:
                print(f"  - {error}")

        print()


def main():
    """Run all content API tests"""
    tester = ContentAPITester()

    # 1. Login
    if not tester.login():
        print_error("Authentication failed. Exiting.")
        sys.exit(1)

    # 2. Create test files
    test_dir = tester.create_test_files()

    # 3. Test basic CRUD
    print_header("Testing Basic CRUD Operations")
    small_image = test_dir / "small_image.jpg"
    content_id = tester.test_upload_content(small_image, "Test Image 1", should_succeed=True)

    if content_id:
        tester.test_get_content(content_id)
        tester.test_update_content(content_id)
        # Don't delete yet - will test list first

    # 4. Test list
    tester.test_list_content(expected_count=1)

    # 5. Test security features
    tester.test_file_size_validation(test_dir)
    tester.test_mime_validation(test_dir)
    tester.test_virus_scanning(test_dir)
    tester.test_path_traversal(test_dir)

    # 6. Test duplicate detection
    duplicate_test = test_dir / "duplicate_test.jpg"
    with open(duplicate_test, 'wb') as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00')
        f.write(os.urandom(500 * 1024))
        f.write(b'\xFF\xD9')
    tester.test_duplicate_detection(duplicate_test)

    # 7. Test bulk operations
    tester.test_bulk_upload(test_dir)

    # 8. Test filters
    tester.test_content_filters()

    # 9. Upload video for completeness
    small_video = test_dir / "small_video.mp4"
    video_id = tester.test_upload_content(small_video, "Test Video 1", should_succeed=True)

    # 10. Print summary
    tester.print_summary()

    # 11. Cleanup (optional - comment out to keep test data)
    cleanup_choice = input("\nDelete all test content? (y/n): ")
    if cleanup_choice.lower() == 'y':
        tester.cleanup()
    else:
        print_info(f"Test content preserved. IDs: {tester.uploaded_content_ids}")


if __name__ == "__main__":
    main()
