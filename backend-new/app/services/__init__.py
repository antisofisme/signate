"""
Service modules for business logic

FASE 2 COMPLETE:
- OrganizationService: CRITICAL multi-tenant service with PIN management
- PlaylistManager: Refactored to use repositories
- All 15+ services available for API layer
"""

# Authentication Services
from app.services.auth_service import AuthService

# Monitoring Services
from app.services.celery_monitor_service import CeleryMonitorService

# Core Services
from app.services.anthias_service import AnthiasService, anthias_service
from app.services.organization_service import OrganizationService

# Playlist & Content Services
from app.services.playlist_manager import PlaylistManager

# Device & System Services
from app.services.device_service import DeviceService
from app.services.command_service import CommandService

# Data & Analytics Services
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService

# External Integration Services
from app.services.firebird_service import FirebirdService

# Background Processing Services
from app.services.scheduler import Scheduler

# Media Processing Services
from app.services.transcoding_service import TranscodingService
from app.services.preview_service import PreviewService

# Communication Services
from app.services.websocket_service import WebSocketService, websocket_service

# Template & Translation Services
from app.services.template_service import TemplateService
from app.services.translation_service import TranslationService

# Storage Services (FASE 3)
from app.storage import StorageService, StorageClient, storage_client

__all__ = [
    # Authentication
    "AuthService",

    # Monitoring
    "CeleryMonitorService",

    # Core Services
    "AnthiasService",
    "anthias_service",
    "OrganizationService",

    # Playlist & Content
    "PlaylistManager",

    # Device & System
    "DeviceService",
    "CommandService",

    # Data & Analytics
    "AnalyticsService",
    "ReportService",

    # External Integration
    "FirebirdService",

    # Background Processing
    "Scheduler",

    # Media Processing
    "TranscodingService",
    "PreviewService",

    # Communication
    "WebSocketService",
    "websocket_service",

    # Template & Translation
    "TemplateService",
    "TranslationService",

    # Storage (FASE 3)
    "StorageService",
    "StorageClient",
    "storage_client",
]
