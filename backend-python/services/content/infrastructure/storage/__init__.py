"""
Storage infrastructure
"""

from .interfaces import IStorageService
from .local_storage import LocalFilesystemStorage

__all__ = ['IStorageService', 'LocalFilesystemStorage']
