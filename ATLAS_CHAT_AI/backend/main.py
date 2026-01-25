"""
ATLAS_CHAT_AI - Main Entry Point

Multi-tenant AI Chat Service with RAG and Memory capabilities.

Usage:
    # Development
    python -m uvicorn backend.main:app --reload --port 8003

    # Production
    python -m backend.main

    # With environment file
    ENV_FILE=.env.prod python -m backend.main
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run the application."""
    import uvicorn
    from .config import get_settings

    settings = get_settings()

    uvicorn.run(
        "backend.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


# Export app for uvicorn
from .api.app import app


if __name__ == "__main__":
    main()
