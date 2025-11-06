"""
Background Tasks Package
========================

Celery tasks untuk async operations:
- Device monitoring dan management
- Content processing dan cleanup
- System analytics dan maintenance
"""

# Import all tasks to make them discoverable by Celery
from app.tasks.device_tasks import (
    check_offline_devices,
    sync_device_heartbeats,
    cleanup_inactive_devices,
    send_device_command
)

from app.tasks.content_tasks import (
    cleanup_expired_content,
    generate_thumbnails,
    transcode_video,
    validate_content
)

from app.tasks.system_tasks import (
    generate_daily_analytics,
    check_storage_quota,
    cleanup_old_logs,
    database_backup
)

__all__ = [
    # Device tasks
    "check_offline_devices",
    "sync_device_heartbeats",
    "cleanup_inactive_devices",
    "send_device_command",

    # Content tasks
    "cleanup_expired_content",
    "generate_thumbnails",
    "transcode_video",
    "validate_content",

    # System tasks
    "generate_daily_analytics",
    "check_storage_quota",
    "cleanup_old_logs",
    "database_backup",
]