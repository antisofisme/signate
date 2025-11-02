"""
Celery Task Monitoring API Endpoints
=====================================

API endpoints for monitoring and managing Celery background tasks.

Clean Architecture: API → Service (CeleryMonitorService)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query, Request
import json

from app.core.deps import get_current_active_user
from app.core.config import settings
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id
from app.services.celery_monitor_service import CeleryMonitorService
from app.models.user import User

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get(
    "/status",
    summary="Celery Worker Status",
    description="Get Celery worker status and active tasks count"
)
async def get_celery_status(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get Celery worker status and statistics.

    **Returns**:
    - Worker availability and count
    - Active tasks count
    - Scheduled periodic tasks list
    - Worker statistics

    **Requires**: Authentication
    """
    request_id = get_request_id(request)

    logger.info(
        "Celery status check requested",
        request_id=request_id,
        user_id=current_user.id
    )

    service = CeleryMonitorService()
    result = service.get_worker_status()

    logger.info(
        "Celery status retrieved",
        request_id=request_id,
        worker_count=result["workers"]["count"],
        active_tasks=result["tasks"]["active"]
    )

    return result


@router.get(
    "/tasks/active",
    summary="Active Tasks",
    description="Get list of currently executing tasks"
)
async def get_active_tasks(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get list of currently executing tasks.

    **Returns**:
    - Task ID
    - Task name
    - Worker name
    - Time started
    - Arguments

    **Requires**: Authentication
    """
    request_id = get_request_id(request)

    logger.info(
        "Active tasks list requested",
        request_id=request_id,
        user_id=current_user.id
    )

    service = CeleryMonitorService()
    tasks = service.get_active_tasks()

    logger.info(
        "Active tasks retrieved",
        request_id=request_id,
        count=len(tasks)
    )

    return {
        "status": "success",
        "count": len(tasks),
        "tasks": tasks
    }


@router.get(
    "/tasks/{task_id}",
    summary="Task Status",
    description="Get status of a specific task by ID"
)
async def get_task_status(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get status of a specific task by ID.

    **Returns**:
    - Task state (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
    - Result if completed
    - Error info if failed
    - Progress info if available

    **Requires**: Authentication
    """
    request_id = get_request_id(request)

    logger.info(
        "Task status requested",
        request_id=request_id,
        task_id=task_id,
        user_id=current_user.id
    )

    service = CeleryMonitorService()
    result = service.get_task_status(task_id)

    logger.info(
        "Task status retrieved",
        request_id=request_id,
        task_id=task_id,
        state=result["state"]
    )

    return result


@router.get(
    "/scheduled",
    summary="Scheduled Tasks",
    description="Get list of scheduled periodic tasks (Celery Beat)"
)
async def get_scheduled_tasks(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get list of scheduled periodic tasks (Celery Beat).

    **Returns**: All tasks configured in celery beat schedule

    **Requires**: Authentication
    """
    request_id = get_request_id(request)

    logger.info(
        "Scheduled tasks list requested",
        request_id=request_id,
        user_id=current_user.id
    )

    service = CeleryMonitorService()
    tasks = service.get_scheduled_tasks()

    logger.info(
        "Scheduled tasks retrieved",
        request_id=request_id,
        count=len(tasks)
    )

    return {
        "status": "success",
        "count": len(tasks),
        "tasks": tasks
    }


# Debug-only endpoint for manual task triggering
if settings.DEBUG:
    @router.post(
        "/tasks/trigger/{task_name}",
        summary="Trigger Task Manually",
        description="Manually trigger a task (DEBUG mode only)"
    )
    async def trigger_task(
        task_name: str,
        request: Request,
        args: Optional[str] = Query(None, description="JSON string of task arguments"),
        kwargs: Optional[str] = Query(None, description="JSON string of task keyword arguments"),
        current_user: User = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """
        Manually trigger a task (DEBUG mode only).

        **Requires**: Authentication + DEBUG mode enabled

        **Args**:
        - task_name: Name of task to trigger
        - args: JSON string of task arguments (e.g., '[1, 2, 3]')
        - kwargs: JSON string of task keyword arguments (e.g., '{"key": "value"}')
        """
        request_id = get_request_id(request)

        logger.info(
            "Manual task trigger requested",
            request_id=request_id,
            task_name=task_name,
            user_id=current_user.id
        )

        try:
            # Parse arguments
            task_args = json.loads(args) if args else []
            task_kwargs = json.loads(kwargs) if kwargs else {}

            service = CeleryMonitorService()
            result = service.trigger_task(
                task_name=task_name,
                args=task_args,
                kwargs=task_kwargs
            )

            logger.info(
                "Task triggered successfully",
                request_id=request_id,
                task_name=task_name,
                task_id=result["task_id"]
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in task arguments",
                request_id=request_id,
                task_name=task_name,
                error=str(e)
            )
            from app.core.exceptions import BadRequestException
            raise BadRequestException(
                message=f"Invalid JSON in args or kwargs: {str(e)}"
            )
