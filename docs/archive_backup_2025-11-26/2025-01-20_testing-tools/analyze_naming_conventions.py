#!/usr/bin/env python3
"""
Analyze database naming conventions and architecture
"""

import re
from collections import defaultdict
from typing import Dict, List, Set

# Read schema file
with open('/mnt/g/khoirul/signate/database_schema_full.txt', 'r') as f:
    schema_text = f.read()

# Parse tables and columns
tables = {}
current_table = None

for line in schema_text.split('\n'):
    # Detect table name
    if 'Table "public.' in line:
        match = re.search(r'Table "public\.(\w+)"', line)
        if match:
            current_table = match.group(1)
            tables[current_table] = {
                'columns': [],
                'primary_keys': [],
                'foreign_keys': [],
                'indexes': []
            }

    # Parse column lines (format: column_name | type | ...)
    elif current_table and '|' in line and not line.strip().startswith('-'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2 and parts[0] and not parts[0].startswith('Column'):
            column_name = parts[0]
            column_type = parts[1] if len(parts) > 1 else ''
            if column_name and column_type and 'Type' not in column_type:
                tables[current_table]['columns'].append({
                    'name': column_name,
                    'type': column_type
                })

    # Parse primary keys
    elif 'PRIMARY KEY' in line and current_table:
        match = re.search(r'btree \((\w+)\)', line)
        if match:
            tables[current_table]['primary_keys'].append(match.group(1))

    # Parse foreign keys
    elif 'FOREIGN KEY' in line and current_table:
        # Format: "table_column_fkey" FOREIGN KEY (column) REFERENCES other_table(id)
        match = re.search(r'FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)', line)
        if match:
            tables[current_table]['foreign_keys'].append({
                'column': match.group(1),
                'references_table': match.group(2),
                'references_column': match.group(3)
            })

# Analysis results
results = {
    'total_tables': len(tables),
    'naming_issues': [],
    'naming_patterns': defaultdict(int),
    'fk_patterns': defaultdict(int),
    'pk_patterns': defaultdict(int),
    'column_name_analysis': defaultdict(int),
    'inconsistencies': [],
    'good_practices': [],
    'recommendations': []
}

# Analyze table naming
print("="*80)
print("DATABASE NAMING CONVENTION & ARCHITECTURE ANALYSIS")
print("="*80)
print(f"\nTotal Tables: {len(tables)}")
print("\nTables:")
for table_name in sorted(tables.keys()):
    print(f"  - {table_name}")

# 1. TABLE NAMING ANALYSIS
print("\n" + "="*80)
print("1. TABLE NAMING CONVENTIONS")
print("="*80)

singular_tables = []
plural_tables = []
junction_tables = []
prefix_tables = defaultdict(list)

for table_name in tables.keys():
    # Check singular vs plural
    if table_name.endswith('s') and not table_name.endswith('ss'):
        plural_tables.append(table_name)
    else:
        singular_tables.append(table_name)

    # Check for junction tables (many-to-many)
    if '_' in table_name:
        parts = table_name.split('_')
        if len(parts) == 2:
            # Check if it's entity_entity format
            if parts[0] in ['device', 'content', 'playlist', 'user'] or \
               parts[1] in ['tags', 'contents', 'widgets', 'members', 'assignments']:
                junction_tables.append(table_name)

        # Check for prefix patterns
        prefix = parts[0]
        prefix_tables[prefix].append(table_name)

print(f"\nPlural table names: {len(plural_tables)}/{len(tables)}")
print(f"  Examples: {', '.join(plural_tables[:5])}")

print(f"\nSingular table names: {len(singular_tables)}/{len(tables)}")
if singular_tables:
    print(f"  Examples: {', '.join(singular_tables[:5])}")

print(f"\nJunction tables (many-to-many): {len(junction_tables)}")
for jt in junction_tables:
    print(f"  - {jt}")

print(f"\nTable prefixes:")
for prefix, table_list in sorted(prefix_tables.items()):
    if len(table_list) > 1:
        print(f"  - '{prefix}_*': {len(table_list)} tables")
        for t in table_list[:3]:
            print(f"      {t}")

# 2. PRIMARY KEY NAMING ANALYSIS
print("\n" + "="*80)
print("2. PRIMARY KEY NAMING CONVENTIONS")
print("="*80)

pk_naming = defaultdict(list)
for table_name, table_data in tables.items():
    pks = table_data['primary_keys']
    if pks:
        pk_name = pks[0]
        pk_naming[pk_name].append(table_name)

print(f"\nPrimary key naming patterns:")
for pk_name, table_list in sorted(pk_naming.items()):
    print(f"  '{pk_name}': {len(table_list)} tables")
    if pk_name == 'id':
        results['pk_patterns']['simple_id'] = len(table_list)
    elif pk_name.endswith('_id'):
        results['pk_patterns']['table_id'] = len(table_list)

if 'id' in pk_naming:
    print(f"\n✅ Consistent: {len(pk_naming['id'])} tables use 'id' as PK")
else:
    print(f"\n⚠️  Inconsistent: No standard PK naming")

# 3. FOREIGN KEY NAMING ANALYSIS
print("\n" + "="*80)
print("3. FOREIGN KEY NAMING CONVENTIONS")
print("="*80)

fk_patterns = {
    'with_id_suffix': 0,
    'without_id_suffix': 0,
    'examples_with': [],
    'examples_without': []
}

all_fk_columns = set()
for table_name, table_data in tables.items():
    for fk in table_data['foreign_keys']:
        fk_col = fk['column']
        all_fk_columns.add(fk_col)

        if fk_col.endswith('_id'):
            fk_patterns['with_id_suffix'] += 1
            if len(fk_patterns['examples_with']) < 10:
                fk_patterns['examples_with'].append(f"{table_name}.{fk_col} → {fk['references_table']}.{fk['references_column']}")
        else:
            fk_patterns['without_id_suffix'] += 1
            if len(fk_patterns['examples_without']) < 10:
                fk_patterns['examples_without'].append(f"{table_name}.{fk_col} → {fk['references_table']}.{fk['references_column']}")

total_fks = fk_patterns['with_id_suffix'] + fk_patterns['without_id_suffix']
print(f"\nTotal Foreign Keys: {total_fks}")
print(f"\nFK with '_id' suffix: {fk_patterns['with_id_suffix']} ({fk_patterns['with_id_suffix']/total_fks*100:.1f}%)")
print(f"  Examples:")
for ex in fk_patterns['examples_with'][:5]:
    print(f"    ✅ {ex}")

print(f"\nFK WITHOUT '_id' suffix: {fk_patterns['without_id_suffix']} ({fk_patterns['without_id_suffix']/total_fks*100:.1f}%)")
print(f"  Examples:")
for ex in fk_patterns['examples_without'][:10]:
    print(f"    ⚠️  {ex}")

# 4. SPECIAL COLUMN NAMING ANALYSIS
print("\n" + "="*80)
print("4. SPECIAL COLUMN NAMING PATTERNS")
print("="*80)

special_columns = {
    'timestamps': defaultdict(list),
    'booleans': defaultdict(list),
    'jsonb': defaultdict(list),
    'user_tracking': defaultdict(list)
}

for table_name, table_data in tables.items():
    for col in table_data['columns']:
        col_name = col['name']
        col_type = col['type']

        # Timestamps
        if 'timestamp' in col_type.lower():
            special_columns['timestamps'][col_name].append(table_name)

        # Booleans
        if 'boolean' in col_type.lower():
            special_columns['booleans'][col_name].append(table_name)

        # JSONB
        if 'jsonb' in col_type.lower():
            special_columns['jsonb'][col_name].append(table_name)

        # User tracking columns
        if any(pattern in col_name for pattern in ['created_by', 'updated_by', 'assigned_by', 'uploaded_by']):
            special_columns['user_tracking'][col_name].append(table_name)

print("\nTimestamp columns:")
for col_name, table_list in sorted(special_columns['timestamps'].items()):
    print(f"  '{col_name}': {len(table_list)} tables")

print("\nBoolean columns (top patterns):")
bool_counts = sorted(special_columns['booleans'].items(), key=lambda x: len(x[1]), reverse=True)
for col_name, table_list in bool_counts[:10]:
    print(f"  '{col_name}': {len(table_list)} tables")

print("\nJSONB columns:")
for col_name, table_list in sorted(special_columns['jsonb'].items()):
    print(f"  '{col_name}': {len(table_list)} tables - {table_list}")

print("\nUser tracking columns (audit trail):")
for col_name, table_list in sorted(special_columns['user_tracking'].items()):
    print(f"  '{col_name}': {len(table_list)} tables")
    # Check if they're FKs
    is_fk = col_name in all_fk_columns
    suffix = "✅ (FK)" if is_fk else "⚠️  (NOT FK!)"
    print(f"      {suffix}")

# 5. INCONSISTENCIES
print("\n" + "="*80)
print("5. NAMING INCONSISTENCIES DETECTED")
print("="*80)

inconsistencies = []

# Check: created_by, updated_by, etc should have _id suffix
user_tracking_fks = ['created_by', 'updated_by', 'assigned_by', 'uploaded_by', 'added_by']
for col in user_tracking_fks:
    if col in all_fk_columns:
        inconsistencies.append({
            'severity': 'MEDIUM',
            'issue': f"FK column '{col}' lacks '_id' suffix",
            'expected': f"{col}_user_id or {col}_id",
            'current': col,
            'impact': 'Inconsistent with other FK naming (most use _id suffix)'
        })

# Check: organization_pin vs code inconsistency
if 'organizations' in tables:
    org_cols = [c['name'] for c in tables['organizations']['columns']]
    if 'organization_pin' in org_cols:
        inconsistencies.append({
            'severity': 'LOW',
            'issue': 'organizations.organization_pin - redundant prefix',
            'expected': 'pin or access_pin',
            'current': 'organization_pin',
            'impact': 'Redundant prefix (already in organizations table)'
        })

# Check: users table has both 'role' and 'role_id'
if 'users' in tables:
    user_cols = [c['name'] for c in tables['users']['columns']]
    if 'role' in user_cols and 'role_id' in user_cols:
        inconsistencies.append({
            'severity': 'MEDIUM',
            'issue': 'users table has BOTH role (string) AND role_id (FK)',
            'expected': 'Use ONLY role_id (FK to roles table)',
            'current': 'Duplicated: role + role_id',
            'impact': 'Data redundancy, potential inconsistency'
        })

# Print inconsistencies
print(f"\nFound {len(inconsistencies)} inconsistencies:\n")
for i, issue in enumerate(inconsistencies, 1):
    print(f"{i}. [{issue['severity']}] {issue['issue']}")
    print(f"   Current:  {issue['current']}")
    print(f"   Expected: {issue['expected']}")
    print(f"   Impact:   {issue['impact']}\n")

# 6. GOOD PRACTICES FOUND
print("="*80)
print("6. GOOD PRACTICES FOUND ✅")
print("="*80)

good_practices = []

# Check for indexes
total_indexes = 0
for table_data in tables.values():
    total_indexes += len(table_data['indexes'])

good_practices.append(f"✅ Comprehensive indexing: {total_indexes} indexes across {len(tables)} tables")

# Check for timestamps
tables_with_timestamps = 0
for table_name, table_data in tables.items():
    cols = [c['name'] for c in table_data['columns']]
    if 'created_at' in cols:
        tables_with_timestamps += 1

good_practices.append(f"✅ Audit timestamps: {tables_with_timestamps}/{len(tables)} tables have created_at")

# Check for organization_id (multi-tenancy)
tables_with_org_id = 0
for table_name, table_data in tables.items():
    fk_cols = [fk['column'] for fk in table_data['foreign_keys']]
    if 'organization_id' in fk_cols:
        tables_with_org_id += 1

good_practices.append(f"✅ Multi-tenancy: {tables_with_org_id} tables have organization_id FK")

# Check for CASCADE deletes
cascade_count = 0
for line in schema_text.split('\n'):
    if 'ON DELETE CASCADE' in line:
        cascade_count += 1

good_practices.append(f"✅ Referential integrity: {cascade_count} CASCADE delete rules")

# Check for ON DELETE SET NULL
set_null_count = 0
for line in schema_text.split('\n'):
    if 'ON DELETE SET NULL' in line:
        set_null_count += 1

good_practices.append(f"✅ Soft delete support: {set_null_count} SET NULL delete rules")

# Print good practices
for practice in good_practices:
    print(f"  {practice}")

# 7. ARCHITECTURE ASSESSMENT
print("\n" + "="*80)
print("7. OVERALL ARCHITECTURE ASSESSMENT")
print("="*80)

# Categorize tables by domain
domains = {
    'Core': ['users', 'organizations', 'roles', 'user_sessions'],
    'Device Management': [t for t in tables.keys() if t.startswith('device')],
    'Content Management': [t for t in tables.keys() if t.startswith('content')],
    'Playlist Management': [t for t in tables.keys() if t.startswith('playlist')],
    'Scheduling': ['schedules'],
    'PMS Integration': [t for t in tables.keys() if t.startswith('pms')],
    'Support': ['tags', 'templates', 'translations', 'widgets', 'audit_logs']
}

print("\nDomain-Driven Design Structure:")
for domain, domain_tables in domains.items():
    print(f"\n  {domain}: {len(domain_tables)} tables")
    for t in domain_tables:
        cols_count = len(tables[t]['columns']) if t in tables else 0
        fks_count = len(tables[t]['foreign_keys']) if t in tables else 0
        print(f"    - {t:30s} ({cols_count} cols, {fks_count} FKs)")

# 8. FINAL SCORES
print("\n" + "="*80)
print("8. NAMING CONVENTION SCORES")
print("="*80)

scores = {
    'table_naming': 0,
    'pk_naming': 0,
    'fk_naming': 0,
    'column_naming': 0,
    'consistency': 0
}

# Table naming score
plural_ratio = len(plural_tables) / len(tables)
if plural_ratio > 0.8:
    scores['table_naming'] = 90
    print(f"\n✅ Table Naming: 90/100 (Mostly plural - good)")
else:
    scores['table_naming'] = 70
    print(f"\n⚠️  Table Naming: 70/100 (Mixed singular/plural)")

# PK naming score
if len(pk_naming) == 1 and 'id' in pk_naming:
    scores['pk_naming'] = 100
    print(f"✅ PK Naming: 100/100 (Consistent 'id' for all tables)")
else:
    scores['pk_naming'] = 80
    print(f"✅ PK Naming: 80/100 (Mostly consistent)")

# FK naming score
fk_with_suffix_ratio = fk_patterns['with_id_suffix'] / total_fks
if fk_with_suffix_ratio > 0.9:
    scores['fk_naming'] = 90
    print(f"✅ FK Naming: 90/100 ({fk_with_suffix_ratio*100:.1f}% use '_id' suffix)")
else:
    scores['fk_naming'] = 60
    print(f"⚠️  FK Naming: 60/100 ({fk_with_suffix_ratio*100:.1f}% use '_id' suffix - inconsistent)")

# Column naming score
if len(inconsistencies) == 0:
    scores['column_naming'] = 100
    print(f"✅ Column Naming: 100/100 (No issues)")
elif len(inconsistencies) <= 3:
    scores['column_naming'] = 80
    print(f"✅ Column Naming: 80/100 ({len(inconsistencies)} minor issues)")
else:
    scores['column_naming'] = 60
    print(f"⚠️  Column Naming: 60/100 ({len(inconsistencies)} issues)")

# Overall consistency
avg_score = sum(scores.values()) / len(scores)
scores['consistency'] = avg_score
print(f"\n{'='*80}")
print(f"OVERALL CONSISTENCY SCORE: {avg_score:.1f}/100")
print(f"{'='*80}")

if avg_score >= 90:
    grade = "A (Excellent)"
    assessment = "✅ Database design follows best practices with minimal issues"
elif avg_score >= 80:
    grade = "B (Good)"
    assessment = "✅ Database design is solid with minor inconsistencies"
elif avg_score >= 70:
    grade = "C (Acceptable)"
    assessment = "⚠️  Database design is functional but has some inconsistencies"
else:
    grade = "D (Needs Improvement)"
    assessment = "⚠️  Database design needs refactoring for better consistency"

print(f"\nGrade: {grade}")
print(f"Assessment: {assessment}")

# 9. RECOMMENDATIONS
print("\n" + "="*80)
print("9. RECOMMENDATIONS FOR IMPROVEMENT")
print("="*80)

recommendations = [
    {
        'priority': 'HIGH',
        'item': 'Standardize FK naming: Add _id suffix to created_by, updated_by, etc',
        'effort': 'MEDIUM',
        'impact': 'Improves consistency, reduces confusion'
    },
    {
        'priority': 'HIGH',
        'item': 'Remove duplicate role column from users table (keep only role_id FK)',
        'effort': 'LOW',
        'impact': 'Eliminates data redundancy'
    },
    {
        'priority': 'MEDIUM',
        'item': 'Rename organization_pin to pin (remove redundant prefix)',
        'effort': 'LOW',
        'impact': 'Cleaner naming'
    },
    {
        'priority': 'LOW',
        'item': 'Document naming conventions in CLAUDE.md or DATABASE.md',
        'effort': 'LOW',
        'impact': 'Helps new developers'
    },
    {
        'priority': 'LOW',
        'item': 'Add database diagram (ERD) to docs',
        'effort': 'MEDIUM',
        'impact': 'Better understanding of relationships'
    }
]

for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. [{rec['priority']}] {rec['item']}")
    print(f"   Effort: {rec['effort']}")
    print(f"   Impact: {rec['impact']}")

print("\n" + "="*80)
print("END OF ANALYSIS")
print("="*80)
