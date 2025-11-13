#!/usr/bin/env python3
"""
Auto-update Python code for migrations 042-043
- 042: Timestamp column renames (6 columns)
- 043: Boolean column renames (3 columns)
"""

import os
import re
from pathlib import Path

BASE_DIR = Path("/mnt/g/khoirul/signate/backend-python")

# Migration 042: Timestamp renames
TIMESTAMP_RENAMES = {
    'last_seen': 'last_seen_at',  # devices
    'last_activity': 'last_activity_at',  # user_sessions
    'last_updated': 'updated_at',  # contents, pms_guests (careful!)
    'last_sync': 'last_synced_at',  # pms_configurations
    'timestamp': 'recorded_at',  # device_logs
}

# Migration 043: Boolean renames
BOOLEAN_RENAMES = {
    'volume_enabled': 'is_volume_enabled',  # devices
    'supports_personalization': 'is_personalization_supported',  # devices
    'alert_triggered': 'is_alert_triggered',  # device_health_metrics
}

ALL_RENAMES = {**TIMESTAMP_RENAMES, **BOOLEAN_RENAMES}

changes_made = []

def update_file(file_path: Path):
    """Update a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        file_changes = []

        for old_name, new_name in ALL_RENAMES.items():
            # Pattern 1: SQLAlchemy Column definition
            # last_seen = Column(...)
            pattern1 = rf'\b{old_name}\s*=\s*Column\('
            if re.search(pattern1, content):
                content = re.sub(pattern1, f'{new_name} = Column(', content)
                file_changes.append(f"Column def: {old_name} → {new_name}")

            # Pattern 2: Object attribute access
            # device.last_seen, session.last_activity, etc.
            patterns = [
                (rf'\.{old_name}\s*=', f'.{new_name} ='),  # Assignment
                (rf'\.{old_name}\s*==', f'.{new_name} =='),  # Comparison
                (rf'\.{old_name}\s*!=', f'.{new_name} !='),
                (rf'\.{old_name}\s*>', f'.{new_name} >'),
                (rf'\.{old_name}\s*<', f'.{new_name} <'),
                (rf'\.{old_name}\s*,', f'.{new_name},'),  # In list/tuple
                (rf'\.{old_name}\s*\)', f'.{new_name})'),  # End of call
                (rf'\.{old_name}\s+or', f'.{new_name} or'),  # Boolean or
                (rf'\.{old_name}\s+and', f'.{new_name} and'),  # Boolean and
                (rf'{old_name}=', f'{new_name}='),  # Keyword argument
                (rf'"{old_name}"', f'"{new_name}"'),  # String literal
                (rf"'{old_name}'", f"'{new_name}'"),  # String literal
            ]

            for pattern, replacement in patterns:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    content = re.sub(pattern, replacement, content)
                    file_changes.append(f"Code ref ({matches}x): {old_name} → {new_name}")

        # Only write if changed
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
        print(f"❌ Error: {file_path}: {e}")
        return 0

def main():
    print("="*80)
    print("AUTO-UPDATING CODE FOR MIGRATIONS 042-043")
    print("="*80)
    print(f"\nTimestamp renames (042): {len(TIMESTAMP_RENAMES)}")
    print(f"Boolean renames (043): {len(BOOLEAN_RENAMES)}")
    print(f"Total column renames: {len(ALL_RENAMES)}\n")

    # Find all Python files
    python_files = list(BASE_DIR.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...\n")

    total_changes = 0
    for py_file in python_files:
        if '__pycache__' in str(py_file) or 'migrations/' in str(py_file):
            continue

        num_changes = update_file(py_file)
        if num_changes > 0:
            total_changes += num_changes
            print(f"✅ {py_file.relative_to(BASE_DIR)} ({num_changes} changes)")

    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(changes_made)} files updated, {total_changes} total changes")
    print(f"{'='*80}\n")

    if changes_made:
        print("Detailed changes:\n")
        for change_info in changes_made:
            print(f"📁 {change_info['file']}")
            for change in set(change_info['changes']):  # Dedupe
                print(f"   • {change}")
            print()

    # Save report
    report_path = BASE_DIR.parent / "CODE_UPDATE_042_043_REPORT.txt"
    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("CODE UPDATE REPORT - Migrations 042-043\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total files updated: {len(changes_made)}\n")
        f.write(f"Total changes: {total_changes}\n\n")
        f.write("Column Renames:\n")
        for old, new in ALL_RENAMES.items():
            f.write(f"  {old} → {new}\n")
        f.write("\n")

        for change_info in changes_made:
            f.write(f"\nFile: {change_info['file']}\n")
            for change in set(change_info['changes']):
                f.write(f"  - {change}\n")

    print(f"✅ Report saved: {report_path}\n")

    # Warnings
    print("="*80)
    print("⚠️  MANUAL REVIEW REQUIRED:")
    print("="*80)
    print("1. Check DTOs - Pydantic field names updated?")
    print("2. Check API docs - OpenAPI specs updated?")
    print("3. Check tests - Test assertions updated?")
    print("4. Check frontend - TypeScript types updated?")
    print("5. Verify no references to old names remain")
    print()

if __name__ == "__main__":
    main()
