#!/usr/bin/env python3
"""
Firebird Database Inspector
Inspect schema and sample data from Firebird PMS database
"""

import fdb
import sys
from typing import List, Dict, Any


def connect_firebird(database_path: str) -> fdb.Connection:
    """Connect to Firebird database"""
    try:
        conn = fdb.connect(
            host='localhost',
            database=database_path,
            user='SYSDBA',
            password='masterkey',
            charset='UTF8'
        )
        print(f"✓ Connected to {database_path}")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)


def list_tables(conn: fdb.Connection) -> List[str]:
    """List all user tables"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT RDB$RELATION_NAME
        FROM RDB$RELATIONS
        WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_BLR IS NULL
        ORDER BY RDB$RELATION_NAME
    """)

    tables = [row[0].strip() for row in cursor.fetchall()]
    cursor.close()
    return tables


def describe_table(conn: fdb.Connection, table_name: str) -> List[Dict[str, Any]]:
    """Get column information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT
            r.RDB$FIELD_NAME AS field_name,
            f.RDB$FIELD_TYPE AS field_type,
            f.RDB$FIELD_LENGTH AS field_length
        FROM RDB$RELATION_FIELDS r
        LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
        WHERE r.RDB$RELATION_NAME = ?
        ORDER BY r.RDB$FIELD_POSITION
    """, (table_name,))

    # Map Firebird data types
    type_map = {
        7: 'SMALLINT',
        8: 'INTEGER',
        10: 'FLOAT',
        12: 'DATE',
        13: 'TIME',
        14: 'CHAR',
        16: 'BIGINT',
        27: 'DOUBLE',
        35: 'TIMESTAMP',
        37: 'VARCHAR',
        261: 'BLOB'
    }

    columns = []
    for row in cursor.fetchall():
        field_name = row[0].strip()
        field_type = type_map.get(row[1], f'TYPE_{row[1]}')
        field_length = row[2]

        if field_type in ['CHAR', 'VARCHAR'] and field_length:
            field_type = f'{field_type}({field_length})'

        columns.append({
            'name': field_name,
            'type': field_type
        })

    cursor.close()
    return columns


def sample_data(conn: fdb.Connection, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get sample data from table"""
    cursor = conn.cursor()

    try:
        cursor.execute(f'SELECT FIRST {limit} * FROM {table_name}')
        columns = [desc[0] for desc in cursor.description]

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        cursor.close()
        return results
    except Exception as e:
        cursor.close()
        return []


def inspect_database(database_path: str):
    """Main inspection function"""
    print(f"\n{'='*80}")
    print(f"Inspecting Firebird Database: {database_path}")
    print(f"{'='*80}\n")

    conn = connect_firebird(database_path)

    # List all tables
    tables = list_tables(conn)
    print(f"Found {len(tables)} tables:\n")

    # Look for guest/room related tables
    guest_tables = [t for t in tables if 'GUEST' in t or 'TAMU' in t or 'RESERVATION' in t or 'BOOKING' in t]
    room_tables = [t for t in tables if 'ROOM' in t or 'KAMAR' in t or 'CHAMBER' in t]

    print("Guest/Reservation Tables:")
    for table in guest_tables or ['(none found)']:
        print(f"  - {table}")

    print("\nRoom Tables:")
    for table in room_tables or ['(none found)']:
        print(f"  - {table}")

    print(f"\nAll Tables ({len(tables)}):")
    for i, table in enumerate(tables, 1):
        print(f"  {i:3d}. {table}")

    # Inspect specific tables if found
    for table in guest_tables[:2]:  # Inspect first 2 guest tables
        print(f"\n{'='*80}")
        print(f"Table: {table}")
        print(f"{'='*80}")

        columns = describe_table(conn, table)
        print("\nColumns:")
        for col in columns:
            print(f"  - {col['name']:<30} {col['type']}")

        print(f"\nSample Data (first 3 rows):")
        samples = sample_data(conn, table, limit=3)
        for i, sample in enumerate(samples, 1):
            print(f"\nRow {i}:")
            for key, value in sample.items():
                print(f"  {key:<30} = {value}")

    conn.close()
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_firebird.py <database_path>")
        print("\nExample:")
        print("  python inspect_firebird.py /mnt/g/khoirul/signate/powerbo.gdb")
        print("  python inspect_firebird.py /mnt/g/khoirul/signate/powerfo.gdb")
        sys.exit(1)

    database_path = sys.argv[1]
    inspect_database(database_path)
