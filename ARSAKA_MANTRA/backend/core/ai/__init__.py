"""
AI Module for ARSAKA_MANTRA

MANTRA delegates all AI functionality to ARSAKA_TUTUR service.
This module provides the integration client only.

Per MANTRA-LAW-001:
- AI is advisory only
- All decisions require human authority
- AI has ZERO approval power
"""

from .arsaka_tutur_client import (
    ArsakaTuturClient,
    AtlasChatConfig,
    ChatResponse,
    HintsResponse,
    get_arsaka_tutur_client,
    close_arsaka_tutur_client,
)

__all__ = [
    "ArsakaTuturClient",
    "AtlasChatConfig",
    "ChatResponse",
    "HintsResponse",
    "get_arsaka_tutur_client",
    "close_arsaka_tutur_client",
]
