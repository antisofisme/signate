"""
MICS Universal Agent Format (UAF) Models

Pydantic models for the Universal Agent Format - platform-agnostic agent definitions.

Per MICS-TECHNICAL-DESIGN.md:
- Agent definition (YAML/JSON)
- Platform-agnostic
- Contains all context for AI assistants

Usage:
    from context.models import AgentDefinition
    from context.agent_loader import AgentLoader

    loader = AgentLoader()
    agent = loader.load("deployment-agent")
    print(agent.prompt.identity)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class AgentCategory(str, Enum):
    """Agent categories for classification."""
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    SECURITY = "security"
    TESTING = "testing"
    DEVOPS = "devops"
    GENERAL = "general"


class TriggerSeverity(str, Enum):
    """Severity level for rules."""
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class ConstraintType(str, Enum):
    """Types of constraints from decisions."""
    PROHIBITION = "PROHIBITION"
    REQUIREMENT = "REQUIREMENT"
    LIMITATION = "LIMITATION"
    INVARIANT = "INVARIANT"


class ValidationCheckType(str, Enum):
    """Types of validation checks."""
    EXIT_CODE = "exit_code"
    OUTPUT_CONTAINS = "output_contains"
    OUTPUT_EQUALS = "output_equals"
    FILE_EXISTS = "file_exists"
    HTTP_STATUS = "http_status"


# =============================================================================
# Trigger Models
# =============================================================================

class TriggerKeywords(BaseModel):
    """Keywords that trigger agent activation."""
    primary: List[str] = Field(
        default_factory=list,
        description="Primary keywords (high confidence match)"
    )
    secondary: List[str] = Field(
        default_factory=list,
        description="Secondary keywords (medium confidence match)"
    )


class TriggerCondition(BaseModel):
    """Context conditions for agent activation."""
    target_includes: Optional[List[str]] = Field(
        default=None,
        description="Target must include one of these"
    )
    environment_includes: Optional[List[str]] = Field(
        default=None,
        description="Environment must include one of these"
    )
    file_pattern: Optional[str] = Field(
        default=None,
        description="File pattern that triggers agent"
    )
    custom: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom conditions"
    )


class AgentTriggers(BaseModel):
    """Complete trigger configuration for an agent."""
    keywords: TriggerKeywords = Field(
        default_factory=TriggerKeywords,
        description="Keyword triggers"
    )
    intents: List[str] = Field(
        default_factory=list,
        description="Semantic intents (e.g., DEPLOYMENT, RELEASE)"
    )
    conditions: List[TriggerCondition] = Field(
        default_factory=list,
        description="Context conditions"
    )


# =============================================================================
# Decision Context Models
# =============================================================================

class GroupReference(BaseModel):
    """Reference to a MANTRA decision group."""
    id: str = Field(..., description="Group ID (INT, ARCH, CTL, EVO)")
    relevance: str = Field(default="medium", description="Relevance level")
    reason: Optional[str] = Field(default=None, description="Why this group is relevant")


class FeatureSet(BaseModel):
    """Feature IDs to consider."""
    required: List[str] = Field(
        default_factory=list,
        description="Required features (F01-F16)"
    )
    optional: List[str] = Field(
        default_factory=list,
        description="Optional features"
    )


class TagSet(BaseModel):
    """Tags to filter decisions."""
    required: List[str] = Field(
        default_factory=list,
        description="Required tags (must have all)"
    )
    optional: List[str] = Field(
        default_factory=list,
        description="Optional tags (nice to have)"
    )


class DecisionContext(BaseModel):
    """Configuration for which decisions to retrieve."""
    groups: List[GroupReference] = Field(
        default_factory=list,
        description="Groups to search"
    )
    features: FeatureSet = Field(
        default_factory=FeatureSet,
        description="Feature filters"
    )
    tags: TagSet = Field(
        default_factory=TagSet,
        description="Tag filters"
    )
    search_queries: List[str] = Field(
        default_factory=list,
        description="Semantic search queries"
    )


# =============================================================================
# Prompt Models
# =============================================================================

class CriticalRule(BaseModel):
    """A critical rule for the agent."""
    rule: str = Field(..., description="The rule text")
    severity: TriggerSeverity = Field(
        default=TriggerSeverity.WARNING,
        description="How severe is violating this rule"
    )


class AgentPrompt(BaseModel):
    """Agent prompt configuration."""
    identity: str = Field(
        default="",
        description="Core identity description"
    )
    critical_rules: List[CriticalRule] = Field(
        default_factory=list,
        description="Critical rules (always included)"
    )
    behavior: List[str] = Field(
        default_factory=list,
        description="Behavioral guidelines"
    )
    template: str = Field(
        default="",
        description="Prompt template with {{placeholders}}"
    )


# =============================================================================
# Checklist Models
# =============================================================================

class ValidationSpec(BaseModel):
    """Specification for validating a checklist step."""
    type: ValidationCheckType = Field(
        default=ValidationCheckType.EXIT_CODE,
        description="Type of validation"
    )
    expected: Any = Field(
        default=0,
        description="Expected value"
    )


class RetrySpec(BaseModel):
    """Retry configuration for a checklist step."""
    attempts: int = Field(default=3, description="Number of retry attempts")
    delay: str = Field(default="10s", description="Delay between retries")


class ChecklistItem(BaseModel):
    """A single item in the agent checklist."""
    id: str = Field(..., description="Unique identifier")
    step: str = Field(..., description="Step description")
    command: Optional[str] = Field(
        default=None,
        description="Command to execute"
    )
    blocking: bool = Field(
        default=False,
        description="If true, failure stops the process"
    )
    condition: Optional[str] = Field(
        default=None,
        description="Condition for this step"
    )
    validation: Optional[ValidationSpec] = Field(
        default=None,
        description="How to validate success"
    )
    retry: Optional[RetrySpec] = Field(
        default=None,
        description="Retry configuration"
    )


class AgentChecklist(BaseModel):
    """Complete checklist for an agent."""
    pre: List[ChecklistItem] = Field(
        default_factory=list,
        description="Pre-task checks",
        alias="pre_deploy"
    )
    main: List[ChecklistItem] = Field(
        default_factory=list,
        description="Main task steps",
        alias="deploy"
    )
    post: List[ChecklistItem] = Field(
        default_factory=list,
        description="Post-task checks",
        alias="post_deploy"
    )

    class Config:
        populate_by_name = True


# =============================================================================
# Validation Rules
# =============================================================================

class ValidationCondition(BaseModel):
    """A validation condition to check."""
    name: str = Field(..., description="Condition name")
    check: str = Field(..., description="Command or check to run")
    expected: Any = Field(..., description="Expected result")
    message: str = Field(default="", description="Error message if check fails")


class ValidationRules(BaseModel):
    """Validation rules for the agent."""
    pre_conditions: List[ValidationCondition] = Field(
        default_factory=list,
        description="Conditions to check before starting"
    )
    post_conditions: List[ValidationCondition] = Field(
        default_factory=list,
        description="Conditions to check after completion"
    )


# =============================================================================
# Platform Adapters
# =============================================================================

class ClaudeAdapter(BaseModel):
    """Claude Code-specific configuration."""
    mcp_tool_hints: List[str] = Field(
        default_factory=list,
        description="Hints for MCP tool usage"
    )
    skill_integration: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Skill/hook integration"
    )


class CursorAdapter(BaseModel):
    """Cursor-specific configuration."""
    rules_format: str = Field(
        default="",
        description="Format for .cursorrules"
    )


class OpenAIAdapter(BaseModel):
    """OpenAI-specific configuration."""
    function_hints: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Function calling hints"
    )


class GenericAdapter(BaseModel):
    """Generic/Markdown adapter."""
    markdown_format: str = Field(
        default="",
        description="Markdown export format"
    )


class PlatformAdapters(BaseModel):
    """Platform-specific adapter configurations."""
    claude: ClaudeAdapter = Field(
        default_factory=ClaudeAdapter,
        description="Claude Code adapter"
    )
    cursor: CursorAdapter = Field(
        default_factory=CursorAdapter,
        description="Cursor adapter"
    )
    openai: OpenAIAdapter = Field(
        default_factory=OpenAIAdapter,
        description="OpenAI adapter"
    )
    generic: GenericAdapter = Field(
        default_factory=GenericAdapter,
        description="Generic adapter"
    )


# =============================================================================
# Main Agent Definition
# =============================================================================

class AgentDefinition(BaseModel):
    """
    Complete Universal Agent Format definition.

    This is the main model that represents a MANTRA agent.
    Agents are loaded from YAML files and used to provide
    context-aware assistance to AI assistants.

    Example YAML:
        agent:
          id: "deployment-agent"
          name: "Deployment Agent"
          description: "Handles production deployments"
          version: "1.0.0"
          category: "deployment"
          triggers:
            keywords:
              primary: ["deploy", "release"]
          ...
    """

    # Core identity
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    category: AgentCategory = Field(
        default=AgentCategory.GENERAL,
        description="Agent category"
    )

    # Activation
    triggers: AgentTriggers = Field(
        default_factory=AgentTriggers,
        description="When to activate this agent"
    )

    # Decision context
    decision_context: DecisionContext = Field(
        default_factory=DecisionContext,
        description="Which decisions to retrieve"
    )

    # Prompt configuration
    prompt: AgentPrompt = Field(
        default_factory=AgentPrompt,
        description="Agent prompt configuration"
    )

    # Checklist
    checklist: AgentChecklist = Field(
        default_factory=AgentChecklist,
        description="Task checklist"
    )

    # Validation
    validation: ValidationRules = Field(
        default_factory=ValidationRules,
        description="Validation rules"
    )

    # Platform adapters
    platform_adapters: PlatformAdapters = Field(
        default_factory=PlatformAdapters,
        description="Platform-specific configurations"
    )

    # Metadata
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    def get_all_keywords(self) -> List[str]:
        """Get all keywords (primary + secondary)."""
        return (
            self.triggers.keywords.primary +
            self.triggers.keywords.secondary
        )

    def get_required_groups(self) -> List[str]:
        """Get group IDs to search."""
        return [g.id for g in self.decision_context.groups]

    def get_required_features(self) -> List[str]:
        """Get required feature IDs."""
        return self.decision_context.features.required

    def get_all_features(self) -> List[str]:
        """Get all feature IDs (required + optional)."""
        return (
            self.decision_context.features.required +
            self.decision_context.features.optional
        )

    def get_blocking_rules(self) -> List[str]:
        """Get blocking rules only."""
        return [
            r.rule for r in self.prompt.critical_rules
            if r.severity == TriggerSeverity.BLOCKING
        ]

    def get_warning_rules(self) -> List[str]:
        """Get warning rules only."""
        return [
            r.rule for r in self.prompt.critical_rules
            if r.severity == TriggerSeverity.WARNING
        ]

    def get_flat_checklist(self) -> List[ChecklistItem]:
        """Get all checklist items in order."""
        return self.checklist.pre + self.checklist.main + self.checklist.post


# =============================================================================
# Context Assembly Models
# =============================================================================

class RetrievedDecision(BaseModel):
    """A decision retrieved for context."""
    decision_id: str
    decision_code: str
    group_id: str
    feature_id: str
    statement: str
    rationale: Optional[str] = None
    constraints: List[Dict[str, str]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class ExtractedConstraints(BaseModel):
    """Constraints extracted from decisions."""
    prohibitions: List[str] = Field(
        default_factory=list,
        description="Things that MUST NOT be done"
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Things that MUST be done"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Advisory limitations"
    )
    invariants: List[str] = Field(
        default_factory=list,
        description="Things that are always true"
    )


class CodebaseContext(BaseModel):
    """Context from the codebase."""
    deploy_config: Optional[str] = None
    dockerfile: Optional[str] = None
    current_version: Optional[str] = None
    last_deploy: Optional[str] = None
    relevant_files: List[str] = Field(default_factory=list)
    environment_vars: List[str] = Field(default_factory=list)


class AssembledTaskContext(BaseModel):
    """
    Final assembled context for an AI task.

    This is the output of the Context Assembly Pipeline.
    """
    agent: Dict[str, Any] = Field(
        ...,
        description="Agent info (id, name, confidence)"
    )
    prompt: str = Field(
        ...,
        description="Rendered prompt string"
    )
    decisions: List[RetrievedDecision] = Field(
        default_factory=list,
        description="Retrieved decisions"
    )
    constraints: ExtractedConstraints = Field(
        default_factory=ExtractedConstraints,
        description="Extracted constraints"
    )
    checklist: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Checklist items"
    )
    codebase_context: CodebaseContext = Field(
        default_factory=CodebaseContext,
        description="Codebase context"
    )


class ContextAssemblyMeta(BaseModel):
    """Metadata about context assembly."""
    token_estimate: int = 0
    decisions_count: int = 0
    assembly_time_ms: int = 0
    agent_matched: str = ""
    confidence: float = 0.0
    platform: str = "generic"


class MICSResponse(BaseModel):
    """
    Complete MICS response.

    Returned by get_task_context MCP tool.
    """
    task_context: AssembledTaskContext
    meta: ContextAssemblyMeta
    hints: Dict[str, Any] = Field(default_factory=dict)
