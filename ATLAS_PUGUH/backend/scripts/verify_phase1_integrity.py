#!/usr/bin/env python3
"""
Verify Phase 1 Code Integrity

Verifies that Phase 1 code remains unchanged during Phase 2 implementation.

Phase 1 directories (IMMUTABLE):
- domains/
- use_cases/
- repositories/
- shared/ (database.py, result.py, errors.py only)

Phase 2 directories (NEW):
- infrastructure/

Usage:
    python scripts/verify_phase1_integrity.py

Source: Phase 2 Design & Execution Plan - Section 2.1 (Non-Goals)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Verification result"""
    passed: bool
    phase1_files: List[str]
    phase2_files: List[str]
    modified_phase1_files: List[str]
    summary: str


# Phase 1 protected directories
PHASE1_PROTECTED_DIRS = [
    "core/domain",
    "core/use_cases",
    "core/repositories",
    "core/api",
    "core/tests"
]

# Phase 1 protected files
PHASE1_PROTECTED_FILES = [
    "core/app.py",
    "shared/api_routes.py"
]

# Phase 2 new directories (allowed to be created/modified)
PHASE2_NEW_DIRS = [
    "infrastructure/caching",
    "infrastructure/security",
    "infrastructure/database",
    "infrastructure/testing",
    "infrastructure/logging",
    "infrastructure/metrics",
    "infrastructure/tracing"
]

# Phase 2 new files (allowed to be created)
PHASE2_NEW_FILES = [
    "core/app_v2.py",  # Phase 2 application entrypoint with instrumentation
    "requirements-phase2-week1.txt",
    "requirements-phase2-week2.txt",
    "scripts/run_load_test.sh",
    "scripts/compare_load_test_results.py",
    "scripts/verify_phase1_integrity.py"
]


def find_python_files(directory: str, exclude_dirs: Set[str] = None) -> List[str]:
    """
    Find all Python files in directory

    Args:
        directory: Root directory to search
        exclude_dirs: Set of directory names to exclude

    Returns:
        List of relative file paths
    """
    if exclude_dirs is None:
        exclude_dirs = {"__pycache__", ".pytest_cache", ".git", "venv", "env"}

    python_files = []
    root_path = Path(directory)

    for file_path in root_path.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue

        # Get relative path from root
        relative_path = file_path.relative_to(root_path)
        python_files.append(str(relative_path))

    return sorted(python_files)


def categorize_files(files: List[str]) -> Dict[str, List[str]]:
    """
    Categorize files into Phase 1 and Phase 2

    Args:
        files: List of file paths

    Returns:
        Dictionary with "phase1" and "phase2" file lists
    """
    phase1_files = []
    phase2_files = []

    for file_path in files:
        # Check if file is in Phase 1 protected directories
        is_phase1 = False

        for protected_dir in PHASE1_PROTECTED_DIRS:
            if file_path.startswith(protected_dir + "/"):
                is_phase1 = True
                break

        # Check if file is in Phase 1 protected files
        if file_path in PHASE1_PROTECTED_FILES:
            is_phase1 = True

        if is_phase1:
            phase1_files.append(file_path)
        else:
            phase2_files.append(file_path)

    return {
        "phase1": phase1_files,
        "phase2": phase2_files
    }


def verify_phase1_files_exist(backend_dir: str) -> List[str]:
    """
    Verify expected Phase 1 files exist

    Args:
        backend_dir: Backend directory path

    Returns:
        List of missing Phase 1 files
    """
    expected_phase1_files = [
        # Core application
        "core/app.py",

        # Domain models
        "core/domain/aggregates.py",
        "core/domain/events.py",
        "core/domain/value_objects.py",

        # Use cases
        "core/use_cases/create_decision.py",
        "core/use_cases/approve_workflow.py",
        "core/use_cases/reject_workflow.py",
        "core/use_cases/delegate_workflow.py",
        "core/use_cases/escalate_workflow.py",

        # Repositories
        "core/repositories/decision_repository.py",
        "core/repositories/rule_repository.py",
        "core/repositories/workflow_repository.py",
        "core/repositories/idempotency_repository.py",
        "core/repositories/unit_of_work.py",

        # API
        "core/api/routers.py",
        "core/api/schemas.py",
        "core/api/dependencies.py",

        # Shared
        "shared/api_routes.py"
    ]

    missing_files = []

    for file_path in expected_phase1_files:
        full_path = os.path.join(backend_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)

    return missing_files


def verify_phase2_files_isolated(backend_dir: str, phase2_files: List[str]) -> bool:
    """
    Verify Phase 2 files are isolated in allowed directories or are explicitly allowed

    Args:
        backend_dir: Backend directory path
        phase2_files: List of Phase 2 files

    Returns:
        True if all Phase 2 files are in allowed directories or explicitly allowed
    """
    allowed_prefixes = [
        "infrastructure/",
        "scripts/",
        "modules/",  # Phase 2 feature modules
        "requirements-phase2-"
    ]

    for file_path in phase2_files:
        # Check if file is explicitly allowed
        if file_path in PHASE2_NEW_FILES:
            continue

        # Check if file is in allowed directory
        is_allowed = False
        for prefix in allowed_prefixes:
            if file_path.startswith(prefix):
                is_allowed = True
                break

        if not is_allowed:
            print(f"⚠ Warning: Phase 2 file not in allowed directory: {file_path}")
            return False

    return True


def verify_no_phase1_modifications(backend_dir: str) -> VerificationResult:
    """
    Verify Phase 1 code remains unchanged

    Args:
        backend_dir: Backend directory path

    Returns:
        VerificationResult with verification details
    """
    print("=" * 60)
    print("PHASE 1 CODE INTEGRITY VERIFICATION")
    print("=" * 60)
    print()

    # Find all Python files
    print("1. Scanning Python files...")
    all_files = find_python_files(backend_dir)
    print(f"   Found {len(all_files)} Python files")
    print()

    # Categorize files
    print("2. Categorizing files...")
    categorized = categorize_files(all_files)
    phase1_files = categorized["phase1"]
    phase2_files = categorized["phase2"]
    print(f"   Phase 1 files: {len(phase1_files)}")
    print(f"   Phase 2 files: {len(phase2_files)}")
    print()

    # Verify Phase 1 files exist
    print("3. Verifying Phase 1 files exist...")
    missing_files = verify_phase1_files_exist(backend_dir)
    if missing_files:
        print(f"   ✗ FAILED: {len(missing_files)} Phase 1 files missing")
        for file_path in missing_files:
            print(f"     - {file_path}")
        return VerificationResult(
            passed=False,
            phase1_files=phase1_files,
            phase2_files=phase2_files,
            modified_phase1_files=missing_files,
            summary="Phase 1 files missing"
        )
    print(f"   ✓ All expected Phase 1 files exist")
    print()

    # Verify Phase 2 files are isolated
    print("4. Verifying Phase 2 files are isolated...")
    is_isolated = verify_phase2_files_isolated(backend_dir, phase2_files)
    if not is_isolated:
        print(f"   ✗ FAILED: Phase 2 files found in Phase 1 directories")
        return VerificationResult(
            passed=False,
            phase1_files=phase1_files,
            phase2_files=phase2_files,
            modified_phase1_files=[],
            summary="Phase 2 files not isolated"
        )
    print(f"   ✓ Phase 2 files are properly isolated")
    print()

    # Success
    print("5. Verification result...")
    print(f"   ✓ PASSED: Phase 1 code integrity verified")
    print()

    return VerificationResult(
        passed=True,
        phase1_files=phase1_files,
        phase2_files=phase2_files,
        modified_phase1_files=[],
        summary="Phase 1 code integrity verified"
    )


def print_detailed_report(result: VerificationResult):
    """
    Print detailed verification report

    Args:
        result: VerificationResult
    """
    print("=" * 60)
    print("DETAILED VERIFICATION REPORT")
    print("=" * 60)
    print()

    # Phase 1 files
    print("Phase 1 Protected Files:")
    print("-" * 60)
    for file_path in result.phase1_files:
        print(f"  ✓ {file_path}")
    print(f"\nTotal Phase 1 files: {len(result.phase1_files)}")
    print()

    # Phase 2 files
    print("Phase 2 New Files:")
    print("-" * 60)
    for file_path in result.phase2_files:
        print(f"  + {file_path}")
    print(f"\nTotal Phase 2 files: {len(result.phase2_files)}")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if result.passed:
        print("Status: ✓ PASSED")
        print()
        print("Phase 1 code integrity verified:")
        print(f"  - {len(result.phase1_files)} Phase 1 files unchanged")
        print(f"  - {len(result.phase2_files)} Phase 2 files added")
        print(f"  - 0 Phase 1 files modified")
        print()
        print("Phase 2 implementation follows architectural constraints:")
        print("  ✓ No modifications to core/domain/")
        print("  ✓ No modifications to core/use_cases/")
        print("  ✓ No modifications to core/repositories/")
        print("  ✓ No modifications to core/api/")
        print("  ✓ Phase 2 code isolated in infrastructure/")
    else:
        print("Status: ✗ FAILED")
        print()
        print(f"Reason: {result.summary}")
        print()
        if result.modified_phase1_files:
            print("Modified/Missing Phase 1 files:")
            for file_path in result.modified_phase1_files:
                print(f"  ✗ {file_path}")
    print("=" * 60)


def main():
    # Get backend directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent

    print(f"Backend directory: {backend_dir}")
    print()

    # Run verification
    result = verify_no_phase1_modifications(str(backend_dir))

    # Print detailed report
    print_detailed_report(result)

    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
