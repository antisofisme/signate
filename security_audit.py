#!/usr/bin/env python3
"""
Security Audit Script for Digital Signage System
Run this script to identify security vulnerabilities in your system
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import requests
from datetime import datetime

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class SecurityAuditor:
    """Automated security audit for the digital signage system"""

    def __init__(self, base_path: str = ".", api_url: str = "http://192.168.5.12:8001"):
        self.base_path = Path(base_path)
        self.api_url = api_url
        self.issues = []
        self.warnings = []
        self.passed = []

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

    def print_issue(self, issue: str, severity: str = "HIGH"):
        """Print security issue"""
        color = RED if severity == "HIGH" else YELLOW
        prefix = "❌" if severity == "HIGH" else "⚠️"
        print(f"{color}{prefix} {severity}: {issue}{RESET}")
        self.issues.append({"issue": issue, "severity": severity})

    def print_warning(self, warning: str):
        """Print warning"""
        print(f"{YELLOW}⚠️  WARNING: {warning}{RESET}")
        self.warnings.append(warning)

    def print_success(self, message: str):
        """Print success message"""
        print(f"{GREEN}✅ PASSED: {message}{RESET}")
        self.passed.append(message)

    def check_environment_files(self):
        """Check for exposed secrets in environment files"""
        self.print_header("1. Checking Environment Files")

        env_files = [
            ".env",
            "backend/.env",
            "web-admin/.env",
            ".env.example"
        ]

        for env_file in env_files:
            file_path = self.base_path / env_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()

                    # Check for default secrets
                    if "your_super_secret" in content or "change_this" in content:
                        self.print_issue(
                            f"Default secret found in {env_file}",
                            "HIGH"
                        )

                    # Check JWT secret strength
                    jwt_match = re.search(r'JWT_SECRET=(.+)', content)
                    if jwt_match:
                        secret = jwt_match.group(1).strip('"\'')
                        if len(secret) < 32:
                            self.print_issue(
                                f"Weak JWT secret in {env_file} (length: {len(secret)})",
                                "HIGH"
                            )
                        else:
                            self.print_success(f"JWT secret length adequate in {env_file}")

                    # Check for hardcoded passwords
                    if re.search(r'PASSWORD=.*(password|admin|123456)', content, re.IGNORECASE):
                        self.print_issue(
                            f"Weak password found in {env_file}",
                            "HIGH"
                        )

    def check_code_security(self):
        """Scan code for security vulnerabilities"""
        self.print_header("2. Checking Code Security")

        # Patterns to check
        security_patterns = {
            "SQL Injection Risk": [
                r'f".*SELECT.*{.*}',
                r'f".*INSERT.*{.*}',
                r'f".*UPDATE.*{.*}',
                r'f".*DELETE.*{.*}',
                r'\.format\(.*SELECT',
                r'%.*SELECT.*%',
            ],
            "Hardcoded Secrets": [
                r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                r'JWT_SECRET\s*=\s*["\'][^"\']+["\']',
            ],
            "Dangerous Functions": [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(.*shell=True',
            ],
            "Missing Input Validation": [
                r'request\.(args|form|json)\[',  # Direct access without validation
            ]
        }

        # Scan Python files
        python_files = list(self.base_path.glob("backend/**/*.py"))

        for pattern_name, patterns in security_patterns.items():
            found_issues = False
            for py_file in python_files:
                if "test" in str(py_file) or "venv" in str(py_file):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches and not self._is_false_positive(py_file, pattern):
                                self.print_warning(
                                    f"{pattern_name} in {py_file.relative_to(self.base_path)}"
                                )
                                found_issues = True
                                break
                except Exception as e:
                    pass

            if not found_issues:
                self.print_success(f"No {pattern_name} detected")

    def check_api_security(self):
        """Test API security endpoints"""
        self.print_header("3. Testing API Security")

        try:
            # Test if API is reachable
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                self.print_success("API is reachable")
            else:
                self.print_warning(f"API returned status {response.status_code}")

            # Test for rate limiting
            print("\nTesting rate limiting...")
            failed_attempts = 0
            for i in range(10):
                response = requests.post(
                    f"{self.api_url}/api/auth/login",
                    json={"username": "test", "password": "test"},
                    timeout=5
                )
                if response.status_code == 429:
                    self.print_success(f"Rate limiting is active (triggered after {i+1} attempts)")
                    break
                failed_attempts += 1

            if failed_attempts == 10:
                self.print_issue("No rate limiting detected on login endpoint", "HIGH")

            # Check security headers
            print("\nChecking security headers...")
            response = requests.get(f"{self.api_url}/", timeout=5)
            headers_to_check = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1",
            }

            for header, expected_value in headers_to_check.items():
                if header in response.headers:
                    actual = response.headers[header]
                    if isinstance(expected_value, list):
                        if any(v in actual for v in expected_value):
                            self.print_success(f"Security header {header} is set")
                        else:
                            self.print_warning(f"Security header {header} has unexpected value: {actual}")
                    else:
                        if expected_value in actual:
                            self.print_success(f"Security header {header} is set correctly")
                        else:
                            self.print_warning(f"Security header {header} has unexpected value: {actual}")
                else:
                    self.print_issue(f"Missing security header: {header}", "MEDIUM")

            # Test CORS configuration
            print("\nTesting CORS configuration...")
            response = requests.options(
                f"{self.api_url}/api/devices",
                headers={"Origin": "http://evil.com"},
                timeout=5
            )
            if "Access-Control-Allow-Origin" in response.headers:
                origin = response.headers["Access-Control-Allow-Origin"]
                if origin == "*":
                    self.print_issue("CORS allows all origins (*)", "HIGH")
                elif "evil.com" in origin:
                    self.print_issue("CORS allows unauthorized origin", "HIGH")
                else:
                    self.print_success("CORS properly configured")

        except requests.RequestException as e:
            self.print_warning(f"Could not connect to API: {e}")

    def check_dependencies(self):
        """Check for known vulnerabilities in dependencies"""
        self.print_header("4. Checking Dependencies")

        # Check Python dependencies
        requirements_files = [
            "backend/requirements.txt",
            "requirements.txt"
        ]

        for req_file in requirements_files:
            file_path = self.base_path / req_file
            if file_path.exists():
                print(f"Checking {req_file}...")

                # Check for outdated packages
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            package = line.strip().split("==")[0].split(">=")[0].split("~=")[0]

                            # Known vulnerable versions
                            vulnerable_packages = {
                                "flask": ["<2.2.5", "CVE-2023-30861"],
                                "werkzeug": ["<2.3.3", "CVE-2023-25577"],
                                "cryptography": ["<41.0.0", "CVE-2023-38325"],
                                "pillow": ["<10.0.1", "CVE-2023-44271"],
                                "urllib3": ["<2.0.7", "CVE-2023-45803"],
                            }

                            if package.lower() in vulnerable_packages:
                                self.print_warning(
                                    f"Check {package} version for known vulnerabilities"
                                )

        # Check npm dependencies
        package_json_files = [
            "web-admin/package.json",
            "viewer/package.json"
        ]

        for package_file in package_json_files:
            file_path = self.base_path / package_file
            if file_path.exists():
                print(f"\nChecking {package_file}...")
                try:
                    with open(file_path, 'r') as f:
                        package_data = json.load(f)

                    # Check for vulnerable packages
                    vulnerable_npm = {
                        "axios": ["<1.6.0", "CVE-2023-45857"],
                        "vite": ["<4.5.2", "CVE-2024-23331"],
                    }

                    deps = {**package_data.get("dependencies", {}),
                           **package_data.get("devDependencies", {})}

                    for dep, version in deps.items():
                        if dep in vulnerable_npm:
                            self.print_warning(
                                f"Check {dep} version for known vulnerabilities"
                            )

                except json.JSONDecodeError:
                    self.print_warning(f"Could not parse {package_file}")

    def check_database_security(self):
        """Check database security configuration"""
        self.print_header("5. Checking Database Security")

        # Check for default database passwords
        docker_compose = self.base_path / "docker-compose.yml"
        if docker_compose.exists():
            with open(docker_compose, 'r') as f:
                content = f.read()

                # Check for weak passwords
                if re.search(r'POSTGRES_PASSWORD:\s*(password|admin|123456)', content, re.IGNORECASE):
                    self.print_issue("Weak database password in docker-compose.yml", "HIGH")
                else:
                    self.print_success("No obvious weak passwords in docker-compose.yml")

                # Check if database is exposed
                if re.search(r'5432:5432|5433:5433', content):
                    self.print_warning("Database port is exposed externally")

    def check_file_permissions(self):
        """Check file permissions for sensitive files"""
        self.print_header("6. Checking File Permissions")

        sensitive_files = [
            ".env",
            "backend/.env",
            "docker-compose.yml",
            "backend/app/core/config.py"
        ]

        for file_path in sensitive_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                # Check if file is readable by others (Unix-like systems only)
                if sys.platform != "win32":
                    stat = os.stat(full_path)
                    mode = oct(stat.st_mode)[-3:]
                    if mode[-1] != '0':  # Others have read permission
                        self.print_warning(f"{file_path} is readable by others (mode: {mode})")
                    else:
                        self.print_success(f"{file_path} has appropriate permissions")

    def _is_false_positive(self, file_path: Path, pattern: str) -> bool:
        """Check if a security finding is a false positive"""
        # Skip test files and examples
        if any(x in str(file_path) for x in ['test', 'example', 'sample', 'mock']):
            return True

        # Skip migration files for some patterns
        if 'migration' in str(file_path) and 'SELECT' in pattern:
            return True

        return False

    def generate_report(self):
        """Generate final security report"""
        self.print_header("Security Audit Report")

        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_passed = len(self.passed)

        print(f"{BOLD}Summary:{RESET}")
        print(f"  {RED}High Severity Issues: {sum(1 for i in self.issues if i['severity'] == 'HIGH')}{RESET}")
        print(f"  {YELLOW}Medium Severity Issues: {sum(1 for i in self.issues if i['severity'] == 'MEDIUM')}{RESET}")
        print(f"  {YELLOW}Warnings: {total_warnings}{RESET}")
        print(f"  {GREEN}Passed Checks: {total_passed}{RESET}")

        if total_issues > 0:
            print(f"\n{RED}{BOLD}⚠️  SECURITY ISSUES FOUND{RESET}")
            print(f"{RED}Please address the identified security issues before deployment.{RESET}")

            # Save detailed report
            report_file = self.base_path / "security_audit_report.json"
            with open(report_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "issues": self.issues,
                    "warnings": self.warnings,
                    "passed": self.passed
                }, f, indent=2)

            print(f"\nDetailed report saved to: {report_file}")

            return 1  # Exit with error code
        else:
            print(f"\n{GREEN}{BOLD}✅ No critical security issues found!{RESET}")
            print(f"{GREEN}Your system passed the basic security audit.{RESET}")
            print(f"\n{YELLOW}Note: This is a basic audit. Consider professional penetration testing for production systems.{RESET}")

            return 0  # Exit successfully

    def run(self):
        """Run the complete security audit"""
        print(f"{BOLD}{BLUE}")
        print("=" * 60)
        print("   DIGITAL SIGNAGE SECURITY AUDIT")
        print("=" * 60)
        print(f"{RESET}")

        self.check_environment_files()
        self.check_code_security()
        self.check_api_security()
        self.check_dependencies()
        self.check_database_security()
        self.check_file_permissions()

        return self.generate_report()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Security audit for digital signage system")
    parser.add_argument(
        "--path",
        default=".",
        help="Base path of the project (default: current directory)"
    )
    parser.add_argument(
        "--api-url",
        default="http://192.168.5.12:8001",
        help="API URL to test (default: http://192.168.5.12:8001)"
    )

    args = parser.parse_args()

    auditor = SecurityAuditor(args.path, args.api_url)
    exit_code = auditor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()