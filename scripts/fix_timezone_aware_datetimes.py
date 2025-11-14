#!/usr/bin/env python3
"""
Fix timezone-aware datetime usage across the codebase.

This script replaces all occurrences of:
- datetime.utcnow() → datetime.now(timezone.utc)
- datetime.now() → datetime.now(timezone.utc)

And ensures proper imports are present.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Root directory
ROOT_DIR = Path(__file__).parent.parent / "backend-python"

# Files to process
EXTENSIONS = [".py"]
EXCLUDE_DIRS = ["__pycache__", ".git", "venv", "env", ".pytest_cache"]

def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed"""
    if file_path.suffix not in EXTENSIONS:
        return False

    for exclude in EXCLUDE_DIRS:
        if exclude in file_path.parts:
            return False

    return True

def has_timezone_import(content: str) -> bool:
    """Check if file already imports timezone"""
    patterns = [
        r"from datetime import.*timezone",
        r"import datetime.*#.*timezone",
    ]

    for pattern in patterns:
        if re.search(pattern, content):
            return True

    return False

def add_timezone_import(content: str) -> str:
    """Add timezone import to file if not present"""
    if has_timezone_import(content):
        return content

    # Find existing datetime import
    datetime_import_pattern = r"from datetime import ([^\n]+)"
    match = re.search(datetime_import_pattern, content)

    if match:
        # Existing import found - add timezone to it
        current_imports = match.group(1)

        # Check if timezone already in imports
        if "timezone" in current_imports:
            return content

        # Add timezone to import
        new_imports = current_imports.rstrip() + ", timezone"
        new_import_line = f"from datetime import {new_imports}"

        content = content.replace(match.group(0), new_import_line)
    else:
        # No datetime import - add new one at top of imports
        # Find first import or first non-comment line
        lines = content.split("\n")
        insert_index = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith('"""'):
                if stripped.startswith("import") or stripped.startswith("from"):
                    insert_index = i + 1
                else:
                    insert_index = i
                    break

        lines.insert(insert_index, "from datetime import datetime, timezone, timedelta")
        content = "\n".join(lines)

    return content

def fix_datetime_usage(content: str) -> Tuple[str, int]:
    """
    Replace datetime.utcnow() with datetime.now(timezone.utc)
    Returns: (fixed_content, num_replacements)
    """
    replacements = 0

    # Pattern 1: datetime.utcnow()
    pattern1 = r'datetime\.utcnow\(\)'
    replacement1 = 'datetime.now(timezone.utc)'
    content, count1 = re.subn(pattern1, replacement1, content)
    replacements += count1

    # Pattern 2: datetime.now() without timezone (only if not already timezone.utc)
    # Be careful not to replace datetime.now(timezone.utc)
    pattern2 = r'datetime\.now\(\)(?!\(timezone\.utc\))'
    replacement2 = 'datetime.now(timezone.utc)'
    content, count2 = re.subn(pattern2, replacement2, content)
    replacements += count2

    return content, replacements

def process_file(file_path: Path) -> Tuple[bool, int]:
    """
    Process a single file.
    Returns: (was_modified, num_replacements)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Fix datetime usage
        fixed_content, num_replacements = fix_datetime_usage(original_content)

        if num_replacements == 0:
            return False, 0

        # Add timezone import if needed
        fixed_content = add_timezone_import(fixed_content)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        return True, num_replacements

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, 0

def main():
    """Main function"""
    print("🔧 Fixing timezone-aware datetime usage...")
    print(f"📁 Root directory: {ROOT_DIR}")
    print()

    total_files = 0
    modified_files = 0
    total_replacements = 0

    # Find all Python files
    for file_path in ROOT_DIR.rglob("*.py"):
        if not should_process_file(file_path):
            continue

        total_files += 1
        was_modified, num_replacements = process_file(file_path)

        if was_modified:
            modified_files += 1
            total_replacements += num_replacements

            relative_path = file_path.relative_to(ROOT_DIR)
            print(f"✅ {relative_path}: {num_replacements} replacement(s)")

    print()
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files modified: {modified_files}")
    print(f"   Total replacements: {total_replacements}")
    print("=" * 60)

    if modified_files > 0:
        print()
        print("✅ Timezone fixes applied successfully!")
        print("⚠️  Please review changes and run tests before committing.")
    else:
        print()
        print("ℹ️  No datetime.utcnow() occurrences found.")

if __name__ == "__main__":
    main()
