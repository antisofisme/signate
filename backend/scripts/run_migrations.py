#!/usr/bin/env python3
"""
Auto-run database migrations on startup
Checks which migrations have been applied and runs pending ones
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_migration_files() -> List[Tuple[int, str, Path]]:
    """
    Get all migration files sorted by version number

    Returns:
        List of tuples (version, filename, filepath)
    """
    migrations_dir = Path(__file__).parent.parent / "migrations"

    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return []

    migrations = []
    for file in migrations_dir.glob("*.sql"):
        # Extract version number from filename (e.g., "001_create_tables.sql" -> 001)
        try:
            version = int(file.stem.split("_")[0])
            migrations.append((version, file.name, file))
        except (ValueError, IndexError):
            logger.warning(f"Skipping file with invalid naming: {file.name}")
            continue

    # Sort by version number
    migrations.sort(key=lambda x: x[0])
    return migrations


def create_migration_table(engine):
    """Create migration tracking table if it doesn't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        version INTEGER UNIQUE NOT NULL,
        filename VARCHAR(255) NOT NULL,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        success BOOLEAN DEFAULT TRUE
    );
    """

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    logger.info("✓ Migration tracking table ready")


def get_applied_migrations(engine) -> set:
    """Get set of already applied migration versions"""
    query = "SELECT version FROM schema_migrations WHERE success = TRUE"

    with engine.connect() as conn:
        result = conn.execute(text(query))
        return {row[0] for row in result}


def run_migration(engine, version: int, filename: str, filepath: Path) -> bool:
    """
    Run a single migration file

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"📝 Running migration {version:03d}: {filename}")

    try:
        # Read migration file
        with open(filepath, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        with engine.connect() as conn:
            # Split by statement if needed (some migrations use COMMIT)
            # For PostgreSQL, we can execute the whole file
            conn.execute(text(migration_sql))
            conn.commit()

            # Record successful migration
            insert_sql = """
            INSERT INTO schema_migrations (version, filename, success)
            VALUES (:version, :filename, TRUE)
            ON CONFLICT (version) DO UPDATE SET applied_at = NOW()
            """
            conn.execute(text(insert_sql), {"version": version, "filename": filename})
            conn.commit()

        logger.info(f"✅ Migration {version:03d} completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Migration {version:03d} failed: {e}")

        # Record failed migration
        try:
            with engine.connect() as conn:
                insert_sql = """
                INSERT INTO schema_migrations (version, filename, success)
                VALUES (:version, :filename, FALSE)
                ON CONFLICT (version) DO UPDATE SET success = FALSE, applied_at = NOW()
                """
                conn.execute(text(insert_sql), {"version": version, "filename": filename})
                conn.commit()
        except Exception as record_error:
            logger.error(f"Failed to record migration failure: {record_error}")

        return False


def run_migrations():
    """Main function to run all pending migrations"""
    logger.info("=" * 60)
    logger.info("🔄 Database Migration Runner Starting...")
    logger.info("=" * 60)

    # Create database engine
    try:
        engine = create_engine(settings.DATABASE_URL)
        logger.info(f"✓ Connected to database")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    # Create migration tracking table
    try:
        create_migration_table(engine)
    except Exception as e:
        logger.error(f"❌ Failed to create migration table: {e}")
        sys.exit(1)

    # Get all migration files
    migrations = get_migration_files()
    if not migrations:
        logger.warning("⚠️ No migration files found")
        return

    logger.info(f"📋 Found {len(migrations)} migration files")

    # Get already applied migrations
    applied = get_applied_migrations(engine)
    logger.info(f"✓ {len(applied)} migrations already applied")

    # Run pending migrations
    pending = [m for m in migrations if m[0] not in applied]

    if not pending:
        logger.info("✅ All migrations up to date - nothing to run")
        return

    logger.info(f"🚀 Running {len(pending)} pending migrations...")

    failed_count = 0
    for version, filename, filepath in pending:
        if not run_migration(engine, version, filename, filepath):
            failed_count += 1
            # Continue with next migration even if one fails
            # (some migrations might be independent)

    # Summary
    logger.info("=" * 60)
    if failed_count == 0:
        logger.info(f"✅ All {len(pending)} pending migrations completed successfully!")
    else:
        logger.warning(f"⚠️ {failed_count} migrations failed out of {len(pending)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_migrations()
