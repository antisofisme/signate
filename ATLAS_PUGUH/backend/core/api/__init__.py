"""
API Layer - ATLAS_PUGUH Core Service

HTTP interface for Core Service use cases.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from .routers import router
from .read_endpoints import router as read_router
from .config_endpoints import router as config_router
from .schemas import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    ApproveWorkflowRequest,
    ApproveWorkflowResponse,
    RejectWorkflowRequest,
    RejectWorkflowResponse,
    DelegateWorkflowRequest,
    DelegateWorkflowResponse,
    EscalateWorkflowRequest,
    EscalateWorkflowResponse,
    ErrorResponse
)
from .exception_handlers import EXCEPTION_HANDLERS
from .dependencies import init_session_factory, get_session

__all__ = [
    # Routers
    "router",
    "read_router",
    "config_router",
    # Request/Response Schemas
    "CreateDecisionRequest",
    "CreateDecisionResponse",
    "ApproveWorkflowRequest",
    "ApproveWorkflowResponse",
    "RejectWorkflowRequest",
    "RejectWorkflowResponse",
    "DelegateWorkflowRequest",
    "DelegateWorkflowResponse",
    "EscalateWorkflowRequest",
    "EscalateWorkflowResponse",
    "ErrorResponse",
    # Exception Handlers
    "EXCEPTION_HANDLERS",
    # Dependencies
    "init_session_factory",
    "get_session",
]
