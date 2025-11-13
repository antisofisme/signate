#!/usr/bin/env python3
"""
Update SQLAlchemy models and code to reflect migration 039-041
Changes:
1. Rename created_by -> created_by_id
2. Rename updated_by -> updated_by_id
3. Rename assigned_by -> assigned_by_id
4. Rename uploaded_by -> uploaded_by_id
5. Rename added_by -> added_by_id
6. Remove users.role column
7. Rename organization_pin -> pin
"""

import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path("/mnt/g/khoirul/signate/backend-python")

# Mapping of old column names to new ones
COLUMN_RENAMES = {
    'created_by': 'created_by_id',
    'updated_by': 'updated_by_id',
    'assigned_by': 'assigned_by_id',
    'uploaded_by': 'uploaded_by_id',
    'added_by': 'added_by_id',
    'organization_pin': 'pin'
}

changes_made = []

def update_file(file_path: Path):
    """Update a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        file_changes = []

        # Pattern 1: SQLAlchemy Column definitions
        # created_by = Column(Integer, ...)
        for old_name, new_name in COLUMN_RENAMES.items():
            # Match: created_by = Column(
            pattern = rf'\b{old_name}\s*=\s*Column\('
            if re.search(pattern, content):
                content = re.sub(pattern, f'{new_name} = Column(', content)
                file_changes.append(f"Column definition: {old_name} -> {new_name}")

        # Pattern 2: Foreign key references in Column
        # ForeignKey("users.created_by")
        for old_name, new_name in COLUMN_RENAMES.items():
            pattern = rf'ForeignKey\("(\w+)\.{old_name}"\)'
            if re.search(pattern, content):
                content = re.sub(pattern, rf'ForeignKey("\1.{new_name}")', content)
                file_changes.append(f"ForeignKey reference: {old_name} -> {new_name}")

        # Pattern 3: Object attribute access in code
        # current_user.created_by, device.updated_by, etc.
        # BUT: Be careful not to change method names or comments!
        for old_name, new_name in COLUMN_RENAMES.items():
            # Only replace in assignment/comparison contexts
            # device.created_by = user_id
            # if device.updated_by:
            patterns = [
                (rf'\.{old_name}\s*=', f'.{new_name} ='),  # Assignment
                (rf'\.{old_name}\s*==', f'.{new_name} =='),  # Comparison
                (rf'\.{old_name}\s*!=', f'.{new_name} !='),  # Comparison
                (rf'\.{old_name}\s*,', f'.{new_name},'),  # In tuple/list
                (rf'\.{old_name}\s*\)', f'.{new_name})'),  # End of call
                (rf'{old_name}=', f'{new_name}='),  # Keyword argument
            ]

            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    file_changes.append(f"Code reference: {old_name} -> {new_name}")

        # Pattern 4: Remove users.role column references
        # But keep role_id!
        # This is tricky - need to be careful
        # Look for: user.role (but not user.role_id)
        user_role_pattern = r'(\.\s*role)(?!\w)'  # Match .role but not .role_id
        if 'user.role' in content.lower() and 'UserModel' in content:
            # This might need manual review
            file_changes.append("⚠️  MANUAL REVIEW: Found user.role references")

        # Pattern 5: Pydantic DTO fields
        # role: str (in UserResponse/CurrentUser)
        # This needs manual check too

        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            changes_made.append({
                'file': str(file_path.relative_to(BASE_DIR)),
                'changes': file_changes
            })

            return len(file_changes)

        return 0

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0

def main():
    print("="*80)
    print("UPDATING BACKEND CODE FOR MIGRATIONS 039-041")
    print("="*80)
    print()

    # Find all Python files
    python_files = list(BASE_DIR.rglob("*.py"))
    print(f"Found {len(python_files)} Python files to scan\n")

    total_changes = 0

    for py_file in python_files:
        # Skip __pycache__ and migrations
        if '__pycache__' in str(py_file) or 'migrations/' in str(py_file):
            continue

        num_changes = update_file(py_file)
        if num_changes > 0:
            total_changes += num_changes
            print(f"✅ Updated: {py_file.relative_to(BASE_DIR)} ({num_changes} changes)")

    print()
    print("="*80)
    print(f"SUMMARY: {len(changes_made)} files updated, {total_changes} changes made")
    print("="*80)
    print()

    if changes_made:
        print("Detailed changes:\n")
        for change_info in changes_made:
            print(f"📁 {change_info['file']}")
            for change in change_info['changes']:
                print(f"   • {change}")
            print()

    # Save report
    report_path = BASE_DIR.parent / "MODEL_UPDATE_REPORT.txt"
    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("MODEL UPDATE REPORT - Migrations 039-041\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total files updated: {len(changes_made)}\n")
        f.write(f"Total changes: {total_changes}\n\n")

        for change_info in changes_made:
            f.write(f"File: {change_info['file']}\n")
            for change in change_info['changes']:
                f.write(f"  - {change}\n")
            f.write("\n")

    print(f"✅ Report saved to: {report_path}")

    # Print warnings
    print("\n" + "="*80)
    print("⚠️  MANUAL REVIEW REQUIRED FOR:")
    print("="*80)
    print("1. CurrentUser Pydantic model - remove 'role: str' field if exists")
    print("2. UserResponse DTOs - remove 'role: str' field, keep only role_id")
    print("3. Any code that accesses user.role string - change to use role_id FK")
    print("4. OrganizationDTO - change organization_pin to pin")
    print("5. Test files - update test assertions for renamed columns")
    print()

if __name__ == "__main__":
    main()
