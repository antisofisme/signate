"""
Storage Module - Anthias Integration
=====================================

This module provides HTTP client wrapper for Anthias storage API.
Anthias runs as a separate Django service (port 8000) for file storage.

Components:
- StorageClient: HTTP client for Anthias API (client.py)
- StorageService: Business logic for file management (service.py)
- storage_client: Global storage client instance

Architecture:
    API Layer → StorageService → StorageClient → Anthias API (Django)
                       ↓
                ContentRepository → Database
"""

from app.storage.client import StorageClient, storage_client
from app.storage.service import StorageService

__all__ = ["StorageClient", "storage_client", "StorageService"]
