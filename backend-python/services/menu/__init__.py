"""Digital Menu Service"""

from .routes import router as menu_router
from .public_routes import router as public_menu_router

__all__ = [
    "menu_router",
    "public_menu_router",
]
