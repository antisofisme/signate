"""
Settings API Endpoints
Provides system information, backup, and maintenance functions
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request
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
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
from app.core.exceptions import InternalServerException
from app.schemas.common import success_response

logger = StructuredLogger(__name__)
router = APIRouter()

# Application start time
APP_START_TIME = time.time()


@router.get("/settings/system/info")
async def get_system_info(
    request: Request,
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
    request_id = get_request_id(request)

    logger.info(
        "Getting system information",
        request_id=request_id,
        operation_type="system_info"
    )

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
            logger.warning(
                "Failed to get database uptime",
                request_id=request_id,
                error=str(e)
            )
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
            logger.warning(
                "Failed to get backend restart count",
                request_id=request_id,
                error=str(e)
            )
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
            logger.warning(
                "Failed to get database restart count",
                request_id=request_id,
                error=str(e)
            )
            db.rollback()  # Rollback failed transaction

        # Get database size
        database_size = 0
        try:
            result = db.execute(text(
                "SELECT pg_database_size(current_database())"
            ))
            database_size = result.scalar()
        except Exception as e:
            logger.warning(
                "Failed to get database size",
                request_id=request_id,
                error=str(e)
            )
            db.rollback()

        # Get media storage size from Content table (files stored in Anthias)
        media_storage_used = 0
        try:
            result = db.execute(text(
                "SELECT COALESCE(SUM(file_size), 0)::BIGINT FROM contents WHERE is_active = true"
            ))
            media_storage_used = int(result.scalar() or 0)
        except Exception as e:
            logger.warning(
                "Failed to calculate media storage",
                request_id=request_id,
                error=str(e)
            )
            db.rollback()

        # Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        info_dict = {
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

        logger.info(
            "System information retrieved successfully",
            request_id=request_id,
            backend_uptime_seconds=int(backend_uptime_seconds),
            database_size=database_size,
            media_storage_used=media_storage_used
        )

        return success_response(
            data=info_dict,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to get system information",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to get system information",
            details={"error": str(e)}
        )


@router.get("/settings/system/backup")
async def backup_database(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Create and download database backup

    Returns SQL dump file for download
    """
    request_id = get_request_id(request)
    backup_path = None

    logger.info(
        "Starting database backup",
        request_id=request_id,
        operation_type="backup"
    )

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
            logger.error(
                "Invalid DATABASE_URL format",
                request_id=request_id
            )
            raise InternalServerException(
                message="Invalid database configuration",
                details={"error": "DATABASE_URL format is invalid"}
            )

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

        logger.info(
            "Executing pg_dump command",
            request_id=request_id,
            database=db_name,
            host=db_host
        )

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(
                "pg_dump command failed",
                request_id=request_id,
                returncode=result.returncode,
                stderr=result.stderr
            )
            raise InternalServerException(
                message="Database backup failed",
                details={"error": result.stderr}
            )

        # Read backup file
        if not os.path.exists(backup_path):
            logger.error(
                "Backup file not created",
                request_id=request_id,
                expected_path=backup_path
            )
            raise InternalServerException(
                message="Backup file was not created",
                details={"expected_path": backup_path}
            )

        with open(backup_path, 'rb') as f:
            backup_content = f.read()

        # Clean up temporary file
        os.remove(backup_path)
        backup_path = None  # Mark as cleaned up

        logger.info(
            "Database backup completed successfully",
            request_id=request_id,
            backup_size=len(backup_content),
            filename=backup_filename
        )

        # Return file for download
        response = Response(
            content=backup_content,
            media_type='application/sql',
            headers={
                'Content-Disposition': f'attachment; filename="{backup_filename}"',
                'X-Request-ID': request_id
            }
        )
        return response

    except subprocess.CalledProcessError as e:
        logger.error(
            "Backup subprocess error",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Database backup command failed",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error(
            "Database backup failed",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        # Clean up if file exists
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
        raise InternalServerException(
            message="Database backup failed",
            details={"error": str(e)}
        )


@router.post("/settings/system/clear-cache")
async def clear_cache(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear system cache

    This endpoint clears:
    - Query cache
    - Database connection pool
    - Application cache (if implemented)
    """
    request_id = get_request_id(request)

    logger.info(
        "Clearing system cache",
        request_id=request_id,
        operation_type="clear_cache"
    )

    try:
        # Clear database connection pool
        # This forces new connections to be created
        from app.core.database import engine
        engine.dispose()

        logger.info(
            "Database connection pool disposed",
            request_id=request_id
        )

        # Additional cache clearing can be added here
        # For example: Redis cache, file cache, etc.

        cleared_at = datetime.now().isoformat()

        logger.info(
            "System cache cleared successfully",
            request_id=request_id,
            cleared_at=cleared_at
        )

        return success_response(
            data={
                "message": "System cache cleared successfully",
                "cleared_at": cleared_at
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to clear system cache",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to clear cache",
            details={"error": str(e)}
        )


@router.get("/settings/system/database-stats")
async def get_database_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed database statistics

    Returns table sizes, row counts, and index information
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting database statistics",
        request_id=request_id,
        operation_type="database_stats"
    )

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

        stats_dict = {
            "total_size_bytes": total_size,
            "tables": tables,
            "table_count": len(tables)
        }

        logger.info(
            "Database statistics retrieved successfully",
            request_id=request_id,
            table_count=len(tables),
            total_size_bytes=total_size
        )

        return success_response(
            data=stats_dict,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to get database statistics",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message="Failed to get database statistics",
            details={"error": str(e)}
        )
