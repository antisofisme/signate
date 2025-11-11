#!/usr/bin/env python3
"""
Database Migration Runner
Runs SQL migration files in order
"""

import os
import sys
import psycopg2
from pathlib import Path
from typing import List, Tuple

# Database connection configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'signage_db'),
    'user': os.getenv('DB_USER', 'signage_user'),
    'password': os.getenv('DB_PASSWORD', 'signage_password')
}

MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def init_migrations_table(conn):
    """Create migrations tracking table"""
    with conn.cursor() as cursor:
        cursor.execute(MIGRATIONS_TABLE)
        conn.commit()

def get_applied_migrations(conn) -> List[str]:
    """Get list of already applied migrations"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return [row[0] for row in cursor.fetchall()]

def get_migration_files() -> List[Tuple[str, Path]]:
    """Get all migration files in order"""
    migrations_dir = Path(__file__).parent
    files = []
    
    for file in sorted(migrations_dir.glob("*.sql")):
        if file.name.startswith("001_complete_schema"):
            continue  # Skip complete schema file
        if file.name[0:3].isdigit() and file.name[3] == "_":
            files.append((file.stem, file))
    
    return files

def apply_migration(conn, version: str, filepath: Path):
    """Apply a single migration"""
    print(f"Applying migration: {version}")
    
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
        
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,)
            )
        conn.commit()
        print(f"  ✓ Applied {version}")
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error applying {version}: {e}")
        raise

def main():
    """Run migrations"""
    print("Database Migration Runner")
    print("=" * 50)
    
    # Connect to database
    conn = get_connection()
    
    try:
        # Initialize migrations table
        init_migrations_table(conn)
        
        # Get applied migrations
        applied = set(get_applied_migrations(conn))
        print(f"\nAlready applied: {len(applied)} migrations")
        
        # Get migration files
        migrations = get_migration_files()
        print(f"Found {len(migrations)} migration files")
        
        # Apply pending migrations
        pending = [(v, f) for v, f in migrations if v not in applied]
        if not pending:
            print("\n✓ All migrations are up to date!")
            return
        
        print(f"\nPending migrations: {len(pending)}")
        for version, _ in pending:
            print(f"  - {version}")
        
        # Confirm
        response = input("\nApply pending migrations? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        # Apply migrations
        print("\nApplying migrations...")
        for version, filepath in pending:
            apply_migration(conn, version, filepath)
        
        print(f"\n✓ Successfully applied {len(pending)} migrations!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()