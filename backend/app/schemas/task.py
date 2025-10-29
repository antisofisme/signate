"""
Task Schemas for Quick Wins Pattern
Pydantic models for Celery task monitoring and management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Task Status Schemas
# ============================================================================

class TaskMetadata(BaseModel):
    """Task metadata (task-specific information)"""

    file_name: Optional[str] = Field(None, description="Filename being processed")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    resolution: Optional[str] = Field(None, description="Video resolution")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    retry_count: Optional[int] = Field(None, description="Number of retries")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts")

    class Config:
        extra = "allow"  # Allow additional fields


class TaskResponse(BaseModel):
    """Response model for task status"""

    task_id: str = Field(..., description="Celery task ID")
    state: str = Field(..., description="Task state (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY, REVOKED)")
    ready: bool = Field(..., description="Whether task has finished (success or failure)")
    successful: Optional[bool] = Field(None, description="Whether task completed successfully")
    failed: Optional[bool] = Field(None, description="Whether task failed")
    progress: int = Field(default=0, description="Progress percentage (0-100)", ge=0, le=100)
    stage: str = Field(..., description="Current processing stage")
    message: str = Field(..., description="Status message")
    current: Optional[str] = Field(None, description="Current operation description")
    total: Optional[int] = Field(None, description="Total items to process")
    eta: Optional[str] = Field(None, description="Estimated time of arrival (ISO format)")
    eta_seconds: Optional[int] = Field(None, description="Estimated seconds remaining")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result (when completed)")
    error: Optional[str] = Field(None, description="Error message (when failed)")
    traceback: Optional[str] = Field(None, description="Exception traceback (when failed)")
    metadata: Optional[TaskMetadata] = Field(None, description="Task-specific metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "state": "PROGRESS",
                "ready": False,
                "successful": None,
                "failed": None,
                "progress": 45,
                "stage": "transcoding",
                "message": "Transcoding video: 45%",
                "current": "Processing video segment 5/10",
                "total": 10,
                "eta": "2025-10-28T12:35:00Z",
                "eta_seconds": 120,
                "result": None,
                "error": None,
                "traceback": None,
                "metadata": {
                    "file_name": "video.mp4",
                    "file_size": 104857600,
                    "resolution": "1920x1080",
                    "duration": 300
                }
            }
        }


# ============================================================================
# Active Tasks Schemas
# ============================================================================

class ActiveTaskItem(BaseModel):
    """Individual active task information"""

    task_id: str = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    args: List[Any] = Field(default=[], description="Task arguments")
    kwargs: Dict[str, Any] = Field(default={}, description="Task keyword arguments")
    worker: str = Field(..., description="Worker hostname")
    started: Optional[float] = Field(None, description="Task start timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "xyz789abc012",
                "name": "transcode_video",
                "args": [123, "/data/videos/input.mp4"],
                "kwargs": {"quality": "high"},
                "worker": "celery@worker1",
                "started": 1698476400.0
            }
        }


class ActiveTasksResponse(BaseModel):
    """Response model for active tasks list"""

    active_tasks: List[ActiveTaskItem] = Field(..., description="List of active tasks")
    total: int = Field(..., description="Total number of active tasks")
    workers: List[str] = Field(..., description="List of worker hostnames")

    class Config:
        json_schema_extra = {
            "example": {
                "active_tasks": [
                    {
                        "task_id": "abc123",
                        "name": "transcode_video",
                        "args": [123, "/data/videos/input.mp4"],
                        "kwargs": {},
                        "worker": "celery@worker1",
                        "started": 1698476400.0
                    }
                ],
                "total": 1,
                "workers": ["celery@worker1", "celery@worker2"]
            }
        }


# ============================================================================
# Task Statistics Schemas
# ============================================================================

class WorkerPoolInfo(BaseModel):
    """Worker pool information"""

    max_concurrency: Optional[int] = Field(None, description="Maximum concurrent tasks")
    processes: Optional[List[int]] = Field(None, description="Worker process IDs")
    max_tasks_per_child: Optional[int] = Field(None, description="Max tasks per worker")
    timeouts: Optional[Dict[str, int]] = Field(None, description="Timeout settings")

    class Config:
        extra = "allow"


class WorkerStats(BaseModel):
    """Individual worker statistics"""

    total_tasks: Optional[Dict[str, Any]] = Field(None, description="Total tasks processed")
    pool: Optional[WorkerPoolInfo] = Field(None, description="Worker pool information")
    rusage: Optional[Dict[str, Any]] = Field(None, description="Resource usage")
    clock: Optional[str] = Field(None, description="Worker clock")

    class Config:
        extra = "allow"


class TaskStatsSummary(BaseModel):
    """Summary of task statistics"""

    active_tasks: int = Field(default=0, description="Number of active tasks", ge=0)
    scheduled_tasks: int = Field(default=0, description="Number of scheduled tasks", ge=0)
    reserved_tasks: int = Field(default=0, description="Number of reserved tasks", ge=0)
    total_workers: int = Field(default=0, description="Total number of workers", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "active_tasks": 3,
                "scheduled_tasks": 5,
                "reserved_tasks": 2,
                "total_workers": 2
            }
        }


class TaskStatsResponse(BaseModel):
    """Response model for task statistics"""

    summary: TaskStatsSummary = Field(..., description="Task statistics summary")
    workers: Dict[str, WorkerStats] = Field(default={}, description="Per-worker statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "active_tasks": 3,
                    "scheduled_tasks": 5,
                    "reserved_tasks": 2,
                    "total_workers": 2
                },
                "workers": {
                    "celery@worker1": {
                        "total_tasks": {"total": 150},
                        "pool": {
                            "max_concurrency": 4,
                            "processes": [1234, 1235]
                        }
                    }
                }
            }
        }


# ============================================================================
# Task Control Schemas
# ============================================================================

class TaskCancelResponse(BaseModel):
    """Response model for task cancellation"""

    task_id: str = Field(..., description="Cancelled task ID")
    message: str = Field(..., description="Status message")
    state: str = Field(..., description="Task state after cancellation")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "message": "Task cancellation requested",
                "state": "REVOKED"
            }
        }


class TaskPurgeResponse(BaseModel):
    """Response model for task purge operation"""

    purged_count: int = Field(..., description="Number of tasks purged", ge=0)
    queue: str = Field(..., description="Queue name (or 'all')")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "purged_count": 15,
                "queue": "all",
                "message": "Purged 15 pending tasks"
            }
        }


class TaskDeleteResponse(BaseModel):
    """Response model for task deletion"""

    task_id: str = Field(..., description="Deleted task ID")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "message": "Task deleted successfully"
            }
        }
