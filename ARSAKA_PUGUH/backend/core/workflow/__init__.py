"""
Workflow Module - Approval Workflow Management

Source: PUGUH UI_API_MAPPING.md - Workflow Domain
"""

from .api.routes import router as workflow_router
from .api.dependencies import init_workflow_dependencies

__all__ = ["workflow_router", "init_workflow_dependencies"]
