"""
SessionState component (data holder, not logic).

See JARVIS-L3-ARCH-001: Component Decomposition
See JARVIS-L3-ARCH-002: Threading & Concurrency Model

Import this from jarvis.models for actual implementation.
This is a re-export for component package structure.
"""

from jarvis.models.session_models import SessionState

__all__ = ["SessionState"]
