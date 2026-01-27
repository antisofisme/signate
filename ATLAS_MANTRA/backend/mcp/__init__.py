"""
MICS MCP Server Module

Model Context Protocol (MCP) server for MANTRA integration with AI assistants.
Provides resources and tools for:
- Decision context retrieval
- Validation with AI arbitration
- Smart context injection

Philosophy:
- Additive, not restrictive: Enhances AI capabilities without limiting them
- Capability negotiation: Platforms choose what to use
- Contract-based interface: Open for extension, closed for modification
"""

from .server import MantraMCPServer
from .resources import (
    DecisionResource,
    GroupResource,
    FeatureResource,
    ResourceProvider,
)
from .tools import (
    ValidateTool,
    QueryTool,
    ContextTool,
    ToolProvider,
)

__all__ = [
    'MantraMCPServer',
    'DecisionResource',
    'GroupResource',
    'FeatureResource',
    'ResourceProvider',
    'ValidateTool',
    'QueryTool',
    'ContextTool',
    'ToolProvider',
]
