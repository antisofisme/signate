"""
Celery Monitor Service
======================

Business logic for Celery task monitoring and management.
"""

from typing import Dict, Any, List, Optional
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.exceptions import NotFoundException, BadRequestException


class CeleryMonitorService:
    """
    Celery Monitor Service

    Handles Celery task monitoring:
    - Worker status and statistics
    - Active task listing
    - Task status by ID
    - Scheduled periodic tasks
    - Manual task triggering (debug only)
    """

    def __init__(self):
        """Initialize CeleryMonitorService"""
        self.celery_app = celery_app

    def get_worker_status(self) -> Dict[str, Any]:
        """
        Get Celery worker status and statistics.

        Returns:
            Dict with worker status, active tasks count, and scheduled tasks
        """
        try:
            # Check worker availability using inspect
            inspector = self.celery_app.control.inspect()

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
            beat_schedule = self.celery_app.conf.beat_schedule or {}
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
            return {
                "status": "error",
                "error": str(e),
                "workers": {
                    "available": [],
                    "count": 0,
                    "stats": {}
                },
                "tasks": {
                    "active": 0,
                    "scheduled_periodic": 0,
                    "scheduled_periodic_tasks": []
                }
            }

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of currently executing tasks.

        Returns:
            List of active tasks with details (id, name, worker, time_start, etc.)
        """
        try:
            inspector = self.celery_app.control.inspect()
            active_tasks = inspector.active()

            if not active_tasks:
                return []

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

            return all_tasks

        except Exception as e:
            raise BadRequestException(
                message=f"Failed to get active tasks: {str(e)}"
            )

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a specific task by ID.

        Args:
            task_id: Celery task ID

        Returns:
            Dict with task state, result, error info, and progress

        Raises:
            NotFoundException: If task not found
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)

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
            raise BadRequestException(
                message=f"Failed to get task status: {str(e)}"
            )

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of scheduled periodic tasks (Celery Beat).

        Returns:
            List of scheduled tasks with configuration
        """
        try:
            beat_schedule = self.celery_app.conf.beat_schedule or {}

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

            return scheduled_tasks

        except Exception as e:
            raise BadRequestException(
                message=f"Failed to get scheduled tasks: {str(e)}"
            )

    def trigger_task(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Manually trigger a task (debug/testing only).

        Args:
            task_name: Name of task to trigger
            args: Task arguments
            kwargs: Task keyword arguments

        Returns:
            Dict with task_id and execution details

        Raises:
            NotFoundException: If task not found
            BadRequestException: If task execution fails
        """
        try:
            # Get task by name
            task = self.celery_app.tasks.get(task_name)

            if not task:
                raise NotFoundException(
                    message=f"Task '{task_name}' not found"
                )

            # Send task to queue
            result = task.apply_async(args=args or [], kwargs=kwargs or {})

            return {
                "status": "success",
                "message": f"Task '{task_name}' has been queued",
                "task_id": result.id,
                "task_name": task_name,
                "args": args or [],
                "kwargs": kwargs or {}
            }

        except NotFoundException:
            raise
        except Exception as e:
            raise BadRequestException(
                message=f"Failed to trigger task: {str(e)}"
            )
