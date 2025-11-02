"""
Background Tasks Module
=======================

Celery tasks untuk async processing:
- Content tasks: Transcoding, image optimization
- Device tasks: Heartbeat monitoring, device management
- System tasks: Cleanup, analytics, scheduled jobs
"""

from app.tasks.content_tasks import (
    process_video_upload,
    transcode_video,
    generate_video_thumbnail,
    optimize_image,
    cleanup_failed_transcoding
)

from app.tasks.device_tasks import (
    check_offline_devices,
    sync_device_heartbeats,
    cleanup_inactive_devices,
    send_device_command
)

from app.tasks.system_tasks import (
    cleanup_old_files,
    compute_analytics,
    generate_daily_report,
    check_storage_quotas,
    archive_old_activity_logs
)

__all__ = [
    # Content tasks
    "process_video_upload",
    "transcode_video",
    "generate_video_thumbnail",
    "optimize_image",
    "cleanup_failed_transcoding",
    
    # Device tasks
    "check_offline_devices",
    "sync_device_heartbeats",
    "cleanup_inactive_devices",
    "send_device_command",
    
    # System tasks
    "cleanup_old_files",
    "compute_analytics",
    "generate_daily_report",
    "check_storage_quotas",
    "archive_old_activity_logs",
]
