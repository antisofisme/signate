#!/usr/bin/env python3
"""
Database Migration Script

Runs SQL migrations in order.

Usage:
    python scripts/migrate.py
    python scripts/migrate.py --dry-run
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


async def get_connection() -> asyncpg.Connection:
    """Get database connection."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://chat:chatpassword@localhost:5433/atlas_chat"
    )
    return await asyncpg.connect(database_url)


async def get_applied_migrations(conn: asyncpg.Connection) -> set:
    """Get list of applied migrations."""
    # Create migrations table if not exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    rows = await conn.fetch("SELECT name FROM _migrations")
    return {row["name"] for row in rows}


async def apply_migration(
    conn: asyncpg.Connection,
    name: str,
    sql: str,
    dry_run: bool = False
) -> bool:
    """Apply a single migration."""
    print(f"  Applying: {name}")

    if dry_run:
        print(f"    [DRY RUN] Would execute {len(sql)} characters of SQL")
        return True

    try:
        async with conn.transaction():
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO _migrations (name) VALUES ($1)",
                name
            )
        print(f"    ✓ Applied successfully")
        return True

    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return False


async def run_migrations(dry_run: bool = False):
    """Run all pending migrations."""
    migrations_dir = Path(__file__).parent.parent / "backend" / "infrastructure" / "database" / "migrations"

    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found")
        return

    print(f"Found {len(migration_files)} migration files")
    print()

    # Connect to database
    conn = await get_connection()
    print(f"Connected to database")

    try:
        # Get applied migrations
        applied = await get_applied_migrations(conn)
        print(f"Already applied: {len(applied)} migrations")
        print()

        # Apply pending migrations
        pending = []
        for f in migration_files:
            if f.name not in applied:
                pending.append(f)

        if not pending:
            print("No pending migrations")
            return

        print(f"Pending migrations: {len(pending)}")
        print()

        for f in pending:
            sql = f.read_text()
            success = await apply_migration(conn, f.name, sql, dry_run)
            if not success and not dry_run:
                print("\nMigration failed, stopping.")
                sys.exit(1)

        print()
        print("✓ All migrations completed")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without applying"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ATLAS_CHAT_AI Database Migration")
    print("=" * 60)
    print()

    asyncio.run(run_migrations(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
