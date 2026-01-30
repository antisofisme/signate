"""
Export Integration Module

Provides integrations for exporting MANTRA decisions and documents to external platforms:
- Confluence (Atlassian)
- Notion
- GitHub Wiki

Each exporter implements the ExporterProtocol for consistent interface.
"""

from .base import (
    ExporterProtocol,
    ExportResult,
    ExportConfig,
    ExportTarget,
)
from .confluence import ConfluenceExporter
from .notion import NotionExporter
from .github import GitHubWikiExporter

__all__ = [
    "ExporterProtocol",
    "ExportResult",
    "ExportConfig",
    "ExportTarget",
    "ConfluenceExporter",
    "NotionExporter",
    "GitHubWikiExporter",
]
