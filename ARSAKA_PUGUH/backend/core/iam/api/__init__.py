"""
IAM API Module

FastAPI routes for Identity and Access Management.
"""

from .routes import router as iam_router
from .dependencies import init_iam_dependencies

__all__ = ["iam_router", "init_iam_dependencies"]
