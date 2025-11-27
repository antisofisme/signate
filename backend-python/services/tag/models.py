"""
Tag Models - Re-export from repositories
This file provides backward compatibility for imports
"""

# Re-export models from repositories
from .repositories.models import TagModel, ContentTag

__all__ = ["TagModel", "ContentTag"]
