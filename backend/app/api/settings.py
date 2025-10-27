"""
Settings API Endpoints
Provides system information, backup, and maintenance functions
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import os
import subprocess
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings as app_settings
from app.api.auth import get_current_user
from app.models import User

router = APIRouter()

# Application start time
APP_START_TIME = time.time()


@router.get("/settings/system/info")
async def get_system_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get system information

    Returns:
    - version: Application version
    - backend_uptime: Backend uptime since last restart (e.g. "2d 5h 30m")
    - backend_uptime_seconds: Backend uptime in seconds
    - backend_restart_count: Number of times backend has restarted
    - database_uptime: PostgreSQL uptime (e.g. "5d 12h 45m")
    - database_uptime_seconds: PostgreSQL uptime in seconds
    - database_restart_count: Number of times database has restarted
    - database_size: Database size in bytes
    - media_storage_used: Total file size of active content in bytes
    - python_version: Python version
    - environment: Current environment
    - database_type: Database type
    - cache_enabled: Whether caching is enabled
    """

    try:
        # Calculate backend uptime (since last restart)
        backend_uptime_seconds = time.time() - APP_START_TIME
        backend_uptime_days = int(backend_uptime_seconds // 86400)
        backend_uptime_hours = int((backend_uptime_seconds % 86400) // 3600)
        backend_uptime_minutes = int((backend_uptime_seconds % 3600) // 60)

        # Format backend uptime string
        if backend_uptime_days > 0:
            backend_uptime_display = f"{backend_uptime_days}d {backend_uptime_hours}h {backend_uptime_minutes}m"
        elif backend_uptime_hours > 0:
            backend_uptime_display = f"{backend_uptime_hours}h {backend_uptime_minutes}m"
        else:
            backend_uptime_display = f"{backend_uptime_minutes}m"

        # Get database (PostgreSQL) uptime
        database_uptime_seconds = 0
        database_uptime_display = "N/A"
        try:
            result = db.execute(text(
                "SELECT EXTRACT(EPOCH FROM (NOW() - pg_postmaster_start_time()))::INTEGER"
            ))
            database_uptime_seconds = result.scalar() or 0

            db_uptime_days = int(database_uptime_seconds // 86400)
            db_uptime_hours = int((database_uptime_seconds % 86400) // 3600)
            db_uptime_minutes = int((database_uptime_seconds % 3600) // 60)

            if db_uptime_days > 0:
                database_uptime_display = f"{db_uptime_days}d {db_uptime_hours}h {db_uptime_minutes}m"
            elif db_uptime_hours > 0:
                database_uptime_display = f"{db_uptime_hours}h {db_uptime_minutes}m"
            else:
                database_uptime_display = f"{db_uptime_minutes}m"
        except Exception as e:
            print(f"Error getting database uptime: {e}")
            db.rollback()

        # Get backend restart count from activity logs
        backend_restart_count = 0
        try:
            # Count "system_start" activity logs
            result = db.execute(text(
                """
                SELECT COUNT(*) FROM activity_logs
                WHERE action = 'system_start' AND entity_type = 'system'
                """
            ))
            backend_restart_count = result.scalar() or 0
        except Exception as e:
            print(f"Error getting backend restart count: {e}")
            db.rollback()  # Rollback failed transaction

        # Get database restart count from activity logs
        database_restart_count = 0
        try:
            # Count "database_start" activity logs
            result = db.execute(text(
                """
                SELECT COUNT(*) FROM activity_logs
                WHERE action = 'database_start' AND entity_type = 'system'
                """
            ))
            database_restart_count = result.scalar() or 0
        except Exception as e:
            print(f"Error getting database restart count: {e}")
            db.rollback()  # Rollback failed transaction

        # Get database size
        database_size = 0
        try:
            result = db.execute(text(
                "SELECT pg_database_size(current_database())"
            ))
            database_size = result.scalar()
        except Exception as e:
            print(f"Error getting database size: {e}")
            db.rollback()

        # Get media storage size from Content table (files stored in Anthias)
        media_storage_used = 0
        try:
            result = db.execute(text(
                "SELECT COALESCE(SUM(file_size), 0)::BIGINT FROM content WHERE is_active = true"
            ))
            media_storage_used = int(result.scalar() or 0)
        except Exception as e:
            print(f"Error calculating media storage: {e}")
            db.rollback()

        # Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        return {
            "version": "1.0.0",
            "backend_uptime": backend_uptime_display,
            "backend_uptime_seconds": int(backend_uptime_seconds),
            "backend_restart_count": backend_restart_count,
            "database_uptime": database_uptime_display,
            "database_uptime_seconds": database_uptime_seconds,
            "database_restart_count": database_restart_count,
            "database_size": database_size,
            "media_storage_used": media_storage_used,
            "python_version": python_version,
            "environment": app_settings.ENVIRONMENT,
            "database_type": "PostgreSQL",
            "cache_enabled": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")


@router.get("/settings/system/backup")
async def backup_database(
    current_user: User = Depends(get_current_user)
):
    """
    Create and download database backup

    Returns SQL dump file for download
    """

    try:
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"signage_backup_{timestamp}.sql"
        backup_path = f"/tmp/{backup_filename}"

        # Run pg_dump command
        # Note: Adjust credentials based on your PostgreSQL setup
        db_url = app_settings.DATABASE_URL

        # Extract database connection details from DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            raise HTTPException(status_code=500, detail="Invalid DATABASE_URL format")

        db_user = match.group(1)
        db_password = match.group(2)
        db_host = match.group(3)
        db_port = match.group(4)
        db_name = match.group(5)

        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        # Execute pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-f', backup_path,
            '--no-owner',
            '--no-acl',
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Backup failed: {result.stderr}"
            )

        # Read backup file
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=500, detail="Backup file not created")

        with open(backup_path, 'rb') as f:
            backup_content = f.read()

        # Clean up temporary file
        os.remove(backup_path)

        # Return file for download
        return Response(
            content=backup_content,
            media_type='application/sql',
            headers={
                'Content-Disposition': f'attachment; filename="{backup_filename}"'
            }
        )

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Backup command failed: {str(e)}")
    except Exception as e:
        # Clean up if file exists
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/settings/system/clear-cache")
async def clear_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Clear system cache

    This endpoint clears:
    - Query cache
    - Database connection pool
    - Application cache (if implemented)
    """

    try:
        # Clear database connection pool
        # This forces new connections to be created
        from app.core.database import engine
        engine.dispose()

        # Additional cache clearing can be added here
        # For example: Redis cache, file cache, etc.

        return {
            "status": "success",
            "message": "System cache cleared successfully",
            "cleared_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/settings/system/database-stats")
async def get_database_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed database statistics

    Returns table sizes, row counts, and index information
    """

    try:
        # Get table sizes
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)

        result = db.execute(query)
        tables = []
        for row in result:
            tables.append({
                "schema": row[0],
                "table": row[1],
                "size": row[2],
                "size_bytes": row[3]
            })

        # Get total database size
        total_size_query = text("SELECT pg_database_size(current_database())")
        total_size = db.execute(total_size_query).scalar()

        return {
            "total_size_bytes": total_size,
            "tables": tables,
            "table_count": len(tables)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")
