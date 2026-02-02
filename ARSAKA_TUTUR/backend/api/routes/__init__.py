"""
API Routes.
"""

from fastapi import APIRouter

from .health import router as health_router
from .chat import router as chat_router
from .sessions import router as sessions_router
from .search import router as search_router
from .knowledge import router as knowledge_router
from .memory import router as memory_router
from .admin import router as admin_router

# Create main router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(memory_router, prefix="/memory", tags=["Memory"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

__all__ = ["api_router"]
