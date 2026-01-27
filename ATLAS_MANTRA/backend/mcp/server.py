"""
MANTRA MCP Server Implementation

Implements Model Context Protocol for AI assistant integration.

Supported Capabilities:
- Resources: decisions://, groups://, features://
- Tools: validate, query, get_context, suggest_decisions
- Prompts: decision_template, validation_help

Integration Pattern:
1. AI assistant connects via stdio or HTTP
2. Lists available resources/tools
3. Calls resources for context, tools for actions
4. Results enhance AI's knowledge for the session
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class MCPCapability(str, Enum):
    """MCP protocol capabilities."""
    RESOURCES = "resources"
    TOOLS = "tools"
    PROMPTS = "prompts"
    SAMPLING = "sampling"  # Not used - AI does its own sampling


@dataclass
class MCPServerInfo:
    """Server information for MCP protocol."""
    name: str = "mantra-mcp"
    version: str = "1.0.0"
    protocol_version: str = "2024-11-05"
    capabilities: List[MCPCapability] = field(default_factory=lambda: [
        MCPCapability.RESOURCES,
        MCPCapability.TOOLS,
        MCPCapability.PROMPTS,
    ])


@dataclass
class MCPResource:
    """MCP resource definition."""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPPrompt:
    """MCP prompt template."""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)


class MantraMCPServer:
    """
    MANTRA MCP Server

    Provides MCP protocol interface for AI assistant integration.
    Designed for MICS (MANTRA Intelligent Context System).

    Usage:
        server = MantraMCPServer(repository)
        await server.start_stdio()  # or start_http(port)

    Philosophy:
        - Additive: Resources/tools ADD to AI knowledge
        - Not restrictive: AI decides what to use
        - Capability negotiation: AI queries what's available
    """

    def __init__(self, repository=None, context_pipeline=None):
        """
        Initialize MCP server.

        Args:
            repository: DecisionRepository instance (optional, can set later)
            context_pipeline: ContextPipeline instance (optional)
        """
        self.repository = repository
        self.context_pipeline = context_pipeline
        self.server_info = MCPServerInfo()

        # Registered handlers
        self._resource_handlers: Dict[str, Callable] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._prompt_handlers: Dict[str, Callable] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default resource/tool/prompt handlers."""
        from .resources import ResourceProvider
        from .tools import ToolProvider, WriteToolProvider

        # Resources
        resource_provider = ResourceProvider(self.repository)
        self._resource_handlers['decisions'] = resource_provider.get_decisions
        self._resource_handlers['decision'] = resource_provider.get_decision
        self._resource_handlers['groups'] = resource_provider.get_groups
        self._resource_handlers['features'] = resource_provider.get_features
        self._resource_handlers['matrix'] = resource_provider.get_decision_matrix

        # Tools - Read Operations
        tool_provider = ToolProvider(self.repository, self.context_pipeline)
        self._tool_handlers['validate'] = tool_provider.validate
        self._tool_handlers['query'] = tool_provider.query
        self._tool_handlers['get_context'] = tool_provider.get_context
        self._tool_handlers['suggest_decisions'] = tool_provider.suggest_decisions
        self._tool_handlers['check_compliance'] = tool_provider.check_compliance

        # Tools - Write Operations (require human confirmation)
        write_provider = WriteToolProvider(self.repository)
        self._tool_handlers['classify'] = write_provider.classify
        self._tool_handlers['propose'] = write_provider.propose
        self._tool_handlers['store'] = write_provider.store
        self._tool_handlers['approve'] = write_provider.approve
        self._tool_handlers['challenge'] = write_provider.challenge
        self._tool_handlers['get_pending_proposals'] = write_provider.get_pending_proposals

        # Tools - MICS (Intelligent Context System)
        from .tools import MICSToolProvider
        mics_provider = MICSToolProvider(self.repository)
        self._tool_handlers['get_task_context'] = mics_provider.get_task_context
        self._tool_handlers['get_lineage'] = mics_provider.get_lineage
        self._tool_handlers['compare'] = mics_provider.compare

    # =========================================================================
    # MCP Protocol Methods
    # =========================================================================

    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP initialize request.

        Returns server capabilities and info.
        """
        return {
            "protocolVersion": self.server_info.protocol_version,
            "capabilities": {
                "resources": {"subscribe": False, "listChanged": False},
                "tools": {},
                "prompts": {},
            },
            "serverInfo": {
                "name": self.server_info.name,
                "version": self.server_info.version,
            }
        }

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available MCP resources.

        Returns resource URIs that AI can read.
        """
        return [
            {
                "uri": "mantra://decisions",
                "name": "All Decisions",
                "description": "List all constitutional decisions with filtering",
                "mimeType": "application/json"
            },
            {
                "uri": "mantra://decision/{id}",
                "name": "Single Decision",
                "description": "Get a specific decision by ID or code",
                "mimeType": "application/json"
            },
            {
                "uri": "mantra://groups",
                "name": "Decision Groups",
                "description": "List all decision groups (ARCH, STD, PROC, etc.)",
                "mimeType": "application/json"
            },
            {
                "uri": "mantra://features",
                "name": "Feature Areas",
                "description": "List all feature areas per group",
                "mimeType": "application/json"
            },
            {
                "uri": "mantra://matrix",
                "name": "Decision Matrix",
                "description": "Group x Feature matrix of decision counts",
                "mimeType": "application/json"
            },
            {
                "uri": "mantra://context/{task}",
                "name": "Task Context",
                "description": "Get relevant decisions for a specific task",
                "mimeType": "application/json"
            }
        ]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a specific MCP resource.

        Args:
            uri: Resource URI (e.g., "mantra://decisions")

        Returns:
            Resource contents as JSON
        """
        # Parse URI
        if not uri.startswith("mantra://"):
            raise ValueError(f"Invalid URI scheme: {uri}")

        path = uri[9:]  # Remove "mantra://"
        parts = path.split("/")
        resource_type = parts[0]
        resource_id = parts[1] if len(parts) > 1 else None

        # Route to handler
        if resource_type in self._resource_handlers:
            handler = self._resource_handlers[resource_type]
            if resource_id:
                return await handler(resource_id)
            return await handler()

        raise ValueError(f"Unknown resource type: {resource_type}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.

        Returns tool definitions with input schemas.
        """
        return [
            {
                "name": "mantra_validate",
                "description": (
                    "Validate a decision record against MANTRA constitutional rules. "
                    "Returns quality score, duplicate/conflict detection, impact analysis. "
                    "If arbitration_required=true, YOU should perform the arbitration."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "record": {
                            "type": "object",
                            "description": "Decision record to validate",
                            "properties": {
                                "statement": {"type": "string", "description": "Decision statement"},
                                "rationale": {"type": "string", "description": "Why this decision was made"},
                                "group_id": {"type": "string", "description": "Group: ARCH, STD, PROC, etc."},
                                "feature_id": {"type": "string", "description": "Feature area"},
                                "scope": {"type": "string", "enum": ["ORGANIZATION", "DOMAIN", "APPLICATION"]},
                                "detailed_content": {"type": "string", "description": "Full specification (Layer B)"},
                                "sections": {"type": "array", "description": "Structured sections for Layer B"},
                            },
                            "required": ["statement", "rationale"]
                        },
                        "arbitration_verdicts": {
                            "type": "array",
                            "description": "Your verdicts for any pending arbitrations",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "arbitration_type": {"type": "string"},
                                    "verdict": {"type": "string"},
                                    "confidence": {"type": "number"},
                                    "reason": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["record"]
                }
            },
            {
                "name": "mantra_query",
                "description": (
                    "Query MANTRA decisions with semantic search. "
                    "Find decisions by keywords, tags, tech stack, or natural language."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query or keywords"
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "group_id": {"type": "string"},
                                "feature_id": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "tech_stack": {"type": "array", "items": {"type": "string"}},
                                "scope": {"type": "string"},
                                "status": {"type": "string"}
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Max results to return"
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["micro", "standard", "detailed", "sections"],
                            "default": "standard",
                            "description": "How much detail to include"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "mantra_get_context",
                "description": (
                    "Get relevant MANTRA decisions for your current task. "
                    "Automatically selects decisions based on task description and code context."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "What you're trying to accomplish"
                        },
                        "code_context": {
                            "type": "string",
                            "description": "Current code or file path for context"
                        },
                        "token_budget": {
                            "type": "integer",
                            "default": 2000,
                            "description": "Max tokens for context injection"
                        }
                    },
                    "required": ["task_description"]
                }
            },
            {
                "name": "mantra_suggest_decisions",
                "description": (
                    "Get suggestions for new decisions based on code analysis. "
                    "Identifies patterns that should be documented as decisions."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {
                            "type": "string",
                            "description": "Code to analyze for potential decisions"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file being analyzed"
                        }
                    },
                    "required": ["code_snippet"]
                }
            },
            {
                "name": "mantra_check_compliance",
                "description": (
                    "Check if code complies with relevant MANTRA decisions. "
                    "Returns violations and recommendations."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {
                            "type": "string",
                            "description": "Code to check for compliance"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file being checked"
                        },
                        "decision_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific decisions to check against (optional)"
                        }
                    },
                    "required": ["code_snippet"]
                }
            },

            # =================================================================
            # WRITE OPERATIONS (Require Human Confirmation)
            # =================================================================

            {
                "name": "mantra_classify",
                "description": (
                    "Auto-classify a decision into Group (INT/ARCH/CTL/EVO) and Feature (F01-F16). "
                    "Returns classification context for AI to determine the best category. "
                    "Does NOT store anything - just provides classification guidance."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "statement": {
                            "type": "string",
                            "description": "The decision statement to classify"
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Why this decision was made"
                        },
                        "constraints": {
                            "type": "array",
                            "description": "Optional list of constraints"
                        }
                    },
                    "required": ["statement", "rationale"]
                }
            },
            {
                "name": "mantra_propose",
                "description": (
                    "Propose a new decision (validate without storing). "
                    "Creates a proposal that human can review and approve. "
                    "Does NOT store - human must call mantra_store to persist."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "object",
                            "description": "Full decision record to propose",
                            "properties": {
                                "statement": {"type": "string"},
                                "rationale": {"type": "string"},
                                "group_id": {"type": "string"},
                                "feature_id": {"type": "string"},
                                "scope": {"type": "string"},
                                "blast_radius": {"type": "string"},
                                "constraints": {"type": "array"},
                                "tags": {"type": "array"},
                                "tech_stack": {"type": "array"}
                            },
                            "required": ["statement", "rationale"]
                        },
                        "proposed_by": {
                            "type": "string",
                            "description": "Who is proposing this decision"
                        }
                    },
                    "required": ["decision"]
                }
            },
            {
                "name": "mantra_store",
                "description": (
                    "Store a decision in MANTRA. "
                    "CRITICAL: REQUIRES human_confirmed=true. "
                    "AI must get explicit human approval BEFORE calling this. "
                    "Will REJECT if human_confirmed is false."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {
                            "type": "string",
                            "description": "ID from previous propose() call"
                        },
                        "decision": {
                            "type": "object",
                            "description": "Or provide decision directly (will be validated)"
                        },
                        "human_confirmed": {
                            "type": "boolean",
                            "description": "MUST be true - indicates human approved. NEVER set without explicit human approval."
                        },
                        "stored_by": {
                            "type": "string",
                            "description": "Who is storing this decision"
                        }
                    },
                    "required": ["human_confirmed"]
                }
            },
            {
                "name": "mantra_approve",
                "description": (
                    "Approve and store a pending proposal. "
                    "Call this AFTER human explicitly approves the proposal. "
                    "Convenience method that combines approval + storage."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {
                            "type": "string",
                            "description": "ID of the pending proposal"
                        },
                        "approved_by": {
                            "type": "string",
                            "description": "Who approved (human user identifier)"
                        },
                        "modifications": {
                            "type": "object",
                            "description": "Optional modifications to apply before storing"
                        }
                    },
                    "required": ["proposal_id"]
                }
            },
            {
                "name": "mantra_challenge",
                "description": (
                    "Challenge an existing decision with a superseding version. "
                    "Creates new decision that supersedes the old one. "
                    "Requires human_confirmed=true for storage."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "existing_decision_id": {
                            "type": "string",
                            "description": "ID of decision being challenged"
                        },
                        "new_decision": {
                            "type": "object",
                            "description": "The superseding decision"
                        },
                        "challenge_reason": {
                            "type": "string",
                            "description": "Why this challenge is being made"
                        },
                        "challenged_by": {
                            "type": "string",
                            "description": "Who is challenging"
                        },
                        "human_confirmed": {
                            "type": "boolean",
                            "description": "Must be true to actually store the challenge"
                        }
                    },
                    "required": ["existing_decision_id", "new_decision", "challenge_reason"]
                }
            },
            {
                "name": "mantra_get_pending_proposals",
                "description": (
                    "List all pending proposals awaiting human approval. "
                    "Use to show human what proposals need their review."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },

            # =================================================================
            # MICS TOOLS (Intelligent Context System)
            # =================================================================

            {
                "name": "mantra_get_task_context",
                "description": (
                    "Get intelligent task context with agent prompt and checklist. "
                    "Use at the START of any significant task. "
                    "Returns task-specific agent, relevant decisions, checklist, and constraints. "
                    "This is the MICS Context Assembly Pipeline."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "description": "What the user wants to do (e.g., 'deploy backend to production')"
                        },
                        "target": {
                            "type": "string",
                            "description": "What is being worked on (backend, frontend, database, etc.)"
                        },
                        "environment": {
                            "type": "string",
                            "description": "Target environment if relevant (dev, staging, production)"
                        },
                        "code_context": {
                            "type": "string",
                            "description": "Optional code snippet or file path for additional context"
                        },
                        "token_budget": {
                            "type": "integer",
                            "default": 4000,
                            "description": "Max tokens for context assembly"
                        }
                    },
                    "required": ["intent"]
                }
            },
            {
                "name": "mantra_get_lineage",
                "description": (
                    "Get decision lineage (version history via supersedes chain). "
                    "Traces the evolution of a decision through its history. "
                    "Useful for understanding how a decision evolved over time."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision_id": {
                            "type": "string",
                            "description": "The decision ID to trace"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["ancestors", "descendants", "both"],
                            "default": "both",
                            "description": "Which direction to trace the lineage"
                        }
                    },
                    "required": ["decision_id"]
                }
            },
            {
                "name": "mantra_compare",
                "description": (
                    "Compare two decisions side by side. "
                    "Shows differences in statements, constraints, scope, etc. "
                    "Useful for comparing old vs new versions or similar decisions."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision_id_1": {
                            "type": "string",
                            "description": "First decision ID"
                        },
                        "decision_id_2": {
                            "type": "string",
                            "description": "Second decision ID"
                        }
                    },
                    "required": ["decision_id_1", "decision_id_2"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP tool.

        Args:
            name: Tool name (e.g., "mantra_validate")
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        # Remove "mantra_" prefix if present
        tool_name = name.replace("mantra_", "")

        if tool_name not in self._tool_handlers:
            raise ValueError(f"Unknown tool: {name}")

        handler = self._tool_handlers[tool_name]
        return await handler(**arguments)

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List available MCP prompts.

        Returns prompt templates for common operations.
        """
        return [
            {
                "name": "decision_template",
                "description": "Template for creating a new decision record",
                "arguments": [
                    {"name": "topic", "description": "What the decision is about", "required": True}
                ]
            },
            {
                "name": "validation_help",
                "description": "Help understanding validation results",
                "arguments": [
                    {"name": "validation_result", "description": "The validation response", "required": True}
                ]
            },
            {
                "name": "arbitration_prompt",
                "description": "Prompt for performing AI arbitration on ambiguous cases",
                "arguments": [
                    {"name": "arbitration_context", "description": "Context from validation", "required": True}
                ]
            }
        ]

    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a specific prompt with arguments filled in.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Prompt with filled arguments
        """
        if name == "decision_template":
            topic = arguments.get("topic", "")
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"""Create a MANTRA decision record for: {topic}

Use this structure:
{{
  "statement": "Clear, imperative statement of the decision",
  "rationale": "Explanation of WHY this decision was made",
  "group_id": "ARCH|STD|PROC|IMPL|SPEC",
  "feature_id": "Feature area this applies to",
  "scope": "ORGANIZATION|DOMAIN|APPLICATION",
  "blast_radius": "LOW|MEDIUM|HIGH|CRITICAL",
  "tags": ["relevant", "tags"],
  "tech_stack": ["technologies", "involved"],
  "constraints": [
    {{"type": "REQUIREMENT", "statement": "MUST do X"}},
    {{"type": "PROHIBITION", "statement": "MUST NOT do Y"}}
  ]
}}

For detailed decisions, add:
  "detailed_content": "Full markdown specification...",
  "sections": [
    {{"section_id": "overview", "title": "Overview", "section_type": "OVERVIEW", "content": "..."}}
  ]
"""
                        }
                    }
                ]
            }

        elif name == "arbitration_prompt":
            ctx = arguments.get("arbitration_context", {})
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": ctx.get("prompt_template", "Perform arbitration based on context.")
                        }
                    }
                ]
            }

        raise ValueError(f"Unknown prompt: {name}")

    # =========================================================================
    # Server Startup Methods
    # =========================================================================

    async def start_stdio(self):
        """Start MCP server in stdio mode (for CLI integration)."""
        import sys
        import asyncio

        logger.info("Starting MANTRA MCP server in stdio mode")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                request = json.loads(line.decode())
                response = await self._handle_request(request)
                print(json.dumps(response), flush=True)

            except Exception as e:
                logger.error(f"Error handling request: {e}")
                print(json.dumps({"error": str(e)}), flush=True)

    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        try:
            if method == "initialize":
                result = await self.initialize(params)
            elif method == "resources/list":
                result = {"resources": await self.list_resources()}
            elif method == "resources/read":
                result = {"contents": [await self.read_resource(params.get("uri"))]}
            elif method == "tools/list":
                result = {"tools": await self.list_tools()}
            elif method == "tools/call":
                result = await self.call_tool(params.get("name"), params.get("arguments", {}))
            elif method == "prompts/list":
                result = {"prompts": await self.list_prompts()}
            elif method == "prompts/get":
                result = await self.get_prompt(params.get("name"), params.get("arguments", {}))
            else:
                raise ValueError(f"Unknown method: {method}")

            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
