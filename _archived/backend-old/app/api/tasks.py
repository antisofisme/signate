"""
============================================================================
Task Status API - Celery Background Jobs (Quick Wins Pattern)
============================================================================

Provides endpoints to monitor and manage Celery async tasks.

Features:
- Get status of individual tasks
- List all active tasks
- Cancel running tasks
- Get task queue statistics
- Purge pending tasks (admin only)

Quick Wins Standards:
✅ StructuredLogger for consistent logging
✅ success_response wrapper for all responses
✅ Comprehensive error handling
✅ Celery AsyncResult integration
✅ Request ID tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from typing import Optional
from datetime import datetime

from app.core.logging import StructuredLogger
from app.core.celery_app import celery_app
from app.core.deps import get_current_active_user
from app.schemas.common import success_response, paginated_response, APIResponse, PaginatedAPIResponse
from app.schemas.task import (
    TaskResponse,
    TaskMetadata,
    ActiveTasksResponse,
    ActiveTaskItem,
    TaskStatsResponse,
    TaskStatsSummary,
    WorkerStats,
    TaskCancelResponse,
    TaskPurgeResponse,
    TaskDeleteResponse
)
from app.models.user import User
from app.middleware.request_id import get_request_id

# ============================================================================
# Router Configuration
# ============================================================================

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task_status(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of a Celery background task.

    **Permissions:** Authenticated users only

    **Supported Task States:**
    - PENDING: Task waiting to be processed
    - STARTED: Task has started processing
    - PROGRESS: Task is in progress (with custom progress info)
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed with error
    - RETRY: Task is being retried
    - REVOKED: Task was cancelled

    **Returns:**
    - Task state and progress information
    - Current processing stage
    - ETA (if available)
    - Result data (if completed)
    - Error details (if failed)
    """
    request_id = get_request_id(request)

    logger.info(
        "Task status requested",
        task_id=task_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)

        # Basic task info
        task_data = {
            "task_id": task_id,
            "state": result.state,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "failed": result.failed() if result.ready() else None,
            "progress": 0,
            "stage": "unknown",
            "message": "Task status unknown"
        }

        # Handle different task states
        if result.state == 'PENDING':
            # Task not started yet or doesn't exist
            task_data.update({
                "progress": 0,
                "stage": "waiting",
                "message": "Task is waiting to be processed"
            })

        elif result.state == 'STARTED':
            # Task has started
            task_data.update({
                "progress": 0,
                "stage": "initializing",
                "message": "Task has started processing"
            })

        elif result.state == 'PROGRESS':
            # Task is in progress with custom state
            info = result.info or {}
            task_data.update({
                "progress": info.get('progress', 0),
                "stage": info.get('stage', 'processing'),
                "current": info.get('current', ''),
                "total": info.get('total'),
                "message": info.get('message', 'Processing...'),
                "metadata": TaskMetadata(**info.get('metadata', {})) if info.get('metadata') else None
            })

            # Calculate ETA if available
            if 'eta' in info:
                task_data['eta'] = info['eta']
            elif 'start_time' in info and 'progress' in info:
                # Estimate remaining time based on progress
                try:
                    start_time = datetime.fromisoformat(info['start_time'])
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    progress = info['progress']
                    if progress > 0:
                        total_time = elapsed / (progress / 100)
                        remaining = total_time - elapsed
                        task_data['eta_seconds'] = max(0, int(remaining))
                except Exception:
                    pass  # Ignore ETA calculation errors

        elif result.state == 'SUCCESS':
            # Task completed successfully
            task_data.update({
                "progress": 100,
                "stage": "completed",
                "message": "Task completed successfully",
                "result": result.result
            })

        elif result.state == 'FAILURE':
            # Task failed
            task_data.update({
                "progress": 0,
                "stage": "failed",
                "message": "Task failed with error",
                "error": str(result.info) if result.info else "Unknown error",
                "traceback": result.traceback
            })

        elif result.state == 'RETRY':
            # Task is being retried
            info = result.info or {}
            task_data.update({
                "progress": info.get('progress', 0),
                "stage": "retrying",
                "message": f"Task is being retried (attempt {info.get('retry_count', 1)})",
                "metadata": TaskMetadata(
                    retry_count=info.get('retry_count', 1),
                    max_retries=info.get('max_retries', 3)
                )
            })

        elif result.state == 'REVOKED':
            # Task was cancelled
            task_data.update({
                "progress": 0,
                "stage": "cancelled",
                "message": "Task was cancelled"
            })

        else:
            # Custom state
            info = result.info or {}
            task_data.update({
                "progress": info.get('progress', 0),
                "stage": result.state.lower(),
                "message": info.get('message', f"Task is in state: {result.state}")
            })

        logger.info(
            "Task status retrieved",
            task_id=task_id,
            state=result.state,
            progress=task_data.get('progress', 0),
            request_id=request_id
        )

        response_data = TaskResponse(**task_data)
        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to get task status",
            task_id=task_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/{task_id}/cancel", response_model=APIResponse[TaskCancelResponse])
async def cancel_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel a running Celery task.

    **Permissions:** Authenticated users only (can only cancel their own tasks, admins can cancel any)

    **Process:**
    1. Revoke task with SIGKILL signal
    2. Task state changes to REVOKED
    3. Task worker terminates the task immediately

    **Note:** Task cancellation is immediate but may not prevent side effects
    that have already occurred.
    """
    request_id = get_request_id(request)

    logger.info(
        "Task cancellation requested",
        task_id=task_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        # Revoke the task with terminate=True and SIGKILL
        celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')

        # Check if task was successfully cancelled
        result = celery_app.AsyncResult(task_id)

        logger.info(
            "Task cancelled successfully",
            task_id=task_id,
            final_state=result.state,
            request_id=request_id
        )

        response_data = TaskCancelResponse(
            task_id=task_id,
            message="Task cancellation requested",
            state=result.state
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to cancel task",
            task_id=task_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.delete("/{task_id}", response_model=APIResponse[TaskDeleteResponse])
async def delete_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a completed task from the result backend.

    **Permissions:** Authenticated users only

    **Note:** Only completed (SUCCESS or FAILURE) tasks can be deleted.
    Use /cancel endpoint to cancel running tasks.
    """
    request_id = get_request_id(request)

    logger.info(
        "Task deletion requested",
        task_id=task_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        # Get task result
        result = celery_app.AsyncResult(task_id)

        # Check if task is completed
        if not result.ready():
            logger.warning(
                "Cannot delete running task",
                task_id=task_id,
                state=result.state,
                request_id=request_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete running task. State: {result.state}. Use /cancel endpoint instead."
            )

        # Forget the task result (delete from backend)
        result.forget()

        logger.info(
            "Task deleted successfully",
            task_id=task_id,
            request_id=request_id
        )

        response_data = TaskDeleteResponse(
            task_id=task_id,
            message="Task deleted successfully"
        )

        return success_response(data=response_data, request_id=request_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete task",
            task_id=task_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.get("/active/list", response_model=APIResponse[ActiveTasksResponse])
async def get_active_tasks(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all active tasks across all workers.

    **Permissions:** Authenticated users only

    **Returns:**
    - List of active tasks with their details
    - Total number of active tasks
    - List of worker hostnames
    """
    request_id = get_request_id(request)

    logger.info(
        "Active tasks list requested",
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        # Get active tasks from all workers
        inspect = celery_app.control.inspect()
        active = inspect.active()

        if not active:
            logger.info(
                "No active tasks found",
                request_id=request_id
            )
            response_data = ActiveTasksResponse(
                active_tasks=[],
                total=0,
                workers=[]
            )
            return success_response(data=response_data, request_id=request_id)

        # Flatten tasks from all workers
        all_tasks = []
        for worker, tasks in active.items():
            for task in tasks:
                all_tasks.append(
                    ActiveTaskItem(
                        task_id=task['id'],
                        name=task['name'],
                        args=task.get('args', []),
                        kwargs=task.get('kwargs', {}),
                        worker=worker,
                        started=task.get('time_start')
                    )
                )

        logger.info(
            "Active tasks retrieved",
            total=len(all_tasks),
            workers=list(active.keys()),
            request_id=request_id
        )

        response_data = ActiveTasksResponse(
            active_tasks=all_tasks,
            total=len(all_tasks),
            workers=list(active.keys())
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to get active tasks",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        # Return empty list on error instead of failing
        response_data = ActiveTasksResponse(
            active_tasks=[],
            total=0,
            workers=[]
        )
        return success_response(data=response_data, request_id=request_id)


@router.get("/stats/summary", response_model=APIResponse[TaskStatsResponse])
async def get_task_stats(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get Celery task queue statistics.

    **Permissions:** Authenticated users only

    **Returns:**
    - Summary: Active, scheduled, reserved task counts and worker count
    - Per-worker statistics: Task totals, pool info, resource usage
    """
    request_id = get_request_id(request)

    logger.info(
        "Task statistics requested",
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        inspect = celery_app.control.inspect()

        # Get various stats
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()

        # Count tasks
        active_count = sum(len(tasks) for tasks in (active or {}).values())
        scheduled_count = sum(len(tasks) for tasks in (scheduled or {}).values())
        reserved_count = sum(len(tasks) for tasks in (reserved or {}).values())

        # Get worker stats
        worker_stats = {}
        if stats:
            for worker, stat in stats.items():
                worker_stats[worker] = WorkerStats(
                    total_tasks=stat.get('total', {}),
                    pool=stat.get('pool'),
                    rusage=stat.get('rusage'),
                    clock=stat.get('clock')
                )

        summary = TaskStatsSummary(
            active_tasks=active_count,
            scheduled_tasks=scheduled_count,
            reserved_tasks=reserved_count,
            total_workers=len(stats) if stats else 0
        )

        logger.info(
            "Task statistics retrieved",
            active=active_count,
            scheduled=scheduled_count,
            workers=len(stats) if stats else 0,
            request_id=request_id
        )

        response_data = TaskStatsResponse(
            summary=summary,
            workers=worker_stats
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to get task statistics",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        # Return empty stats on error
        response_data = TaskStatsResponse(
            summary=TaskStatsSummary(
                active_tasks=0,
                scheduled_tasks=0,
                reserved_tasks=0,
                total_workers=0
            ),
            workers={}
        )
        return success_response(data=response_data, request_id=request_id)


@router.post("/purge", response_model=APIResponse[TaskPurgeResponse])
async def purge_tasks(
    request: Request,
    queue: Optional[str] = Query(None, description="Queue name to purge (default: all)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Purge pending tasks from queue.

    **Permissions:** Admin users only

    **WARNING:** This operation is destructive and cannot be undone.
    All pending tasks in the specified queue will be permanently deleted.

    **Parameters:**
    - queue: Optional queue name (default: purge all queues)
    """
    request_id = get_request_id(request)

    # Admin only
    if not current_user.is_superuser:
        logger.warning(
            "Unauthorized purge attempt",
            user_id=current_user.id,
            request_id=request_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to purge tasks"
        )

    logger.warning(
        "Task purge requested",
        queue=queue or "all",
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        # Purge tasks
        if queue:
            count = celery_app.control.purge(queue=queue)
        else:
            count = celery_app.control.purge()

        logger.warning(
            "Tasks purged",
            count=count,
            queue=queue or "all",
            request_id=request_id
        )

        response_data = TaskPurgeResponse(
            purged_count=count or 0,
            queue=queue or "all",
            message=f"Purged {count or 0} pending tasks"
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to purge tasks",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purge tasks: {str(e)}"
        )


# ============================================================================
# Helper Functions for Task Progress Tracking
# ============================================================================

def update_task_progress(
    task_id: str,
    progress: int,
    stage: str,
    message: str = None,
    metadata: dict = None
):
    """
    Update task progress in Celery backend.

    This function should be called from within Celery tasks to update progress
    that can be queried via the API.

    Args:
        task_id: Celery task ID
        progress: Progress percentage (0-100)
        stage: Current processing stage
        message: Optional status message
        metadata: Optional metadata dict

    Usage in Celery task:
        @celery_app.task(bind=True)
        def my_task(self, ...):
            update_task_progress(
                self.request.id,
                progress=50,
                stage="processing",
                message="Processing data..."
            )
    """
    from celery import current_task

    if current_task and current_task.request.id == task_id:
        current_task.update_state(
            state='PROGRESS',
            meta={
                'progress': min(100, max(0, progress)),
                'stage': stage,
                'message': message or f"{stage}: {progress}%",
                'metadata': metadata or {},
                'updated_at': datetime.utcnow().isoformat()
            }
        )


# ============================================================================
# Example Celery Task with Progress Tracking
# ============================================================================

@celery_app.task(bind=True, name='transcode_video')
def transcode_video_task(self, content_id: int, file_path: str):
    """
    Example Celery task for video transcoding with progress tracking.

    This demonstrates how to update task progress that can be queried via API.

    Args:
        content_id: Content ID being transcoded
        file_path: Path to video file

    Returns:
        dict: Result with success status and output path
    """
    logger_task = StructuredLogger(__name__)

    try:
        # Stage 1: Initialization
        update_task_progress(
            self.request.id,
            progress=0,
            stage="initializing",
            message="Starting video transcoding",
            metadata={
                "content_id": content_id,
                "file_path": file_path
            }
        )

        logger_task.info(
            "Video transcoding started",
            task_id=self.request.id,
            content_id=content_id
        )

        # Stage 2: Analyzing video
        update_task_progress(
            self.request.id,
            progress=10,
            stage="analyzing",
            message="Analyzing video file"
        )

        # Simulate video analysis
        import time
        time.sleep(2)

        # Stage 3: Transcoding
        for i in range(10, 91, 10):
            update_task_progress(
                self.request.id,
                progress=i,
                stage="transcoding",
                message=f"Transcoding video: {i}%"
            )
            time.sleep(1)  # Simulate work

        # Stage 4: Finalizing
        update_task_progress(
            self.request.id,
            progress=95,
            stage="finalizing",
            message="Generating HLS playlist"
        )
        time.sleep(1)

        # Complete
        update_task_progress(
            self.request.id,
            progress=100,
            stage="completed",
            message="Transcoding completed successfully"
        )

        result = {
            "success": True,
            "content_id": content_id,
            "output_path": f"/data/hls/content_{content_id}/playlist.m3u8"
        }

        logger_task.info(
            "Video transcoding completed",
            task_id=self.request.id,
            content_id=content_id,
            output_path=result["output_path"]
        )

        return result

    except Exception as e:
        logger_task.error(
            "Video transcoding failed",
            task_id=self.request.id,
            content_id=content_id,
            error=str(e),
            exc_info=True
        )

        # Update task as failed
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'stage': 'failed',
                'progress': 0
            }
        )
        raise
