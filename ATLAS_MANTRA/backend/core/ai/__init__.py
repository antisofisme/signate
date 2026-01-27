"""
AI Module for ATLAS_MANTRA

Provides AI-powered assistance for decision drafting and review.
AI is advisory only - all decisions require human authority.
"""

from .providers import get_ai_provider, AIProvider
from .chat_service import ChatService
from .hints_service import HintsService

__all__ = [
    "get_ai_provider",
    "AIProvider",
    "ChatService",
    "HintsService",
]
