"""
Celery Task Monitoring API
===========================

API endpoints untuk monitoring dan managing Celery background tasks.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import require_auth, require_role

router = APIRouter()


@router.get("/celery/status")
async def celery_status(
    current_user: Dict = Depends(require_auth)
):
    """
    Get Celery worker status and active tasks.

    Returns information about:
    - Worker availability
    - Active tasks count
    - Scheduled tasks (Celery Beat)
    - Queue statistics
    """
    try:
        # Check worker availability using inspect
        inspector = celery_app.control.inspect()

        # Get active workers
        active_workers = inspector.active()
        stats = inspector.stats()
        scheduled_tasks = inspector.scheduled()

        # Count active tasks
        total_active = 0
        if active_workers:
            for worker, tasks in active_workers.items():
                total_active += len(tasks)

        # Get scheduled periodic tasks from Celery Beat config
        beat_schedule = celery_app.conf.beat_schedule or {}
        scheduled_task_names = list(beat_schedule.keys())

        return {
            "status": "healthy" if active_workers else "no_workers",
            "workers": {
                "available": list(active_workers.keys()) if active_workers else [],
                "count": len(active_workers) if active_workers else 0,
                "stats": stats if stats else {}
            },
            "tasks": {
                "active": total_active,
                "scheduled_periodic": len(scheduled_task_names),
                "scheduled_periodic_tasks": scheduled_task_names
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to get Celery status: {str(e)}"
            }
        )


@router.get("/celery/tasks/active")
async def get_active_tasks(
    current_user: Dict = Depends(require_auth)
):
    """
    Get list of currently executing tasks.

    Returns:
    - Task ID
    - Task name
    - Worker name
    - Time started
    """
    try:
        inspector = celery_app.control.inspect()
        active_tasks = inspector.active()

        if not active_tasks:
            return {
                "status": "success",
                "message": "No workers available or no active tasks",
                "tasks": []
            }

        # Flatten tasks from all workers
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "id": task.get("id"),
                    "name": task.get("name"),
                    "worker": worker,
                    "time_start": task.get("time_start"),
                    "args": task.get("args"),
                    "kwargs": task.get("kwargs")
                })

        return {
            "status": "success",
            "count": len(all_tasks),
            "tasks": all_tasks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active tasks: {str(e)}"
        )


@router.get("/celery/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Dict = Depends(require_auth)
):
    """
    Get status of a specific task by ID.

    Returns:
    - Task state (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
    - Result if completed
    - Error info if failed
    - Progress info if available
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "state": result.state,
            "current": None,
            "total": None,
            "status": None,
            "result": None,
            "error": None
        }

        if result.state == "PENDING":
            response["status"] = "Task is waiting to be executed"
        elif result.state == "STARTED":
            response["status"] = "Task has been started"
        elif result.state == "SUCCESS":
            response["status"] = "Task completed successfully"
            response["result"] = result.result
        elif result.state == "FAILURE":
            response["status"] = "Task failed"
            response["error"] = str(result.info)
        elif result.state == "RETRY":
            response["status"] = "Task is being retried"
            response["error"] = str(result.info)

        # Get progress info if available
        if hasattr(result, 'info') and isinstance(result.info, dict):
            response["current"] = result.info.get("current")
            response["total"] = result.info.get("total")

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/celery/scheduled")
async def get_scheduled_tasks(
    current_user: Dict = Depends(require_auth)
):
    """
    Get list of scheduled periodic tasks (Celery Beat).

    Returns all tasks configured in celery_app.conf.beat_schedule.
    """
    try:
        beat_schedule = celery_app.conf.beat_schedule or {}

        scheduled_tasks = []
        for task_name, task_config in beat_schedule.items():
            schedule_info = task_config.get("schedule")

            # Format schedule info
            if hasattr(schedule_info, "__str__"):
                schedule_str = str(schedule_info)
            else:
                schedule_str = "unknown"

            scheduled_tasks.append({
                "name": task_name,
                "task": task_config.get("task"),
                "schedule": schedule_str,
                "args": task_config.get("args", []),
                "kwargs": task_config.get("kwargs", {}),
                "options": task_config.get("options", {})
            })

        return {
            "status": "success",
            "count": len(scheduled_tasks),
            "tasks": scheduled_tasks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduled tasks: {str(e)}"
        )


# Debug-only endpoints for manual task triggering
if settings.DEBUG:
    @router.post("/celery/tasks/trigger/{task_name}")
    async def trigger_task(
        task_name: str,
        args: Optional[str] = Query(None, description="JSON string of task arguments"),
        kwargs: Optional[str] = Query(None, description="JSON string of task keyword arguments"),
        current_user: Dict = Depends(require_role("admin"))
    ):
        """
        Manually trigger a task (DEBUG mode only).

        Requires admin role.
        """
        try:
            import json

            # Parse arguments
            task_args = json.loads(args) if args else []
            task_kwargs = json.loads(kwargs) if kwargs else {}

            # Get task by name
            task = celery_app.tasks.get(task_name)

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task '{task_name}' not found"
                )

            # Send task to queue
            result = task.apply_async(args=task_args, kwargs=task_kwargs)

            return {
                "status": "success",
                "message": f"Task '{task_name}' has been queued",
                "task_id": result.id,
                "task_name": task_name,
                "args": task_args,
                "kwargs": task_kwargs
            }

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in args or kwargs: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger task: {str(e)}"
            )
