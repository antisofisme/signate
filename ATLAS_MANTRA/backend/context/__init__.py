"""
MICS Context Assembly Module

Smart context injection for AI assistants.
Implements tiered delivery based on token budget:
- micro: ~100 tokens (content_summary only)
- standard: ~500 tokens (statement + rationale + constraints)
- detailed: ~2000+ tokens (full content including Layer B)
- sections: variable (specific sections only)

Philosophy:
- Token budget awareness: Respect AI context limits
- Relevance ranking: Most important decisions first
- Progressive disclosure: Start minimal, expand on demand

Universal Agent Format (UAF):
- Platform-agnostic agent definitions
- YAML-based configuration
- 7-stage Context Assembly Pipeline

Per MICS-TECHNICAL-DESIGN.md:
- Agents loaded from YAML files
- Intent recognition for agent matching
- Decision retrieval based on agent context
- Platform-specific adaptation
"""

from .pipeline import ContextPipeline, ContextAssembler
from .summarizer import ContentSummarizer, generate_content_summary
from .models import (
    AgentDefinition,
    AgentCategory,
    AgentTriggers,
    AgentPrompt,
    AgentChecklist,
    DecisionContext,
    ExtractedConstraints,
    AssembledTaskContext,
    MICSResponse,
)
from .agent_loader import (
    AgentLoader,
    AgentMatcher,
    get_builtin_agent,
    get_all_builtin_agents,
)
from .token_budget import (
    TokenTier,
    Position,
    TokenBudgetConfig,
    ContentBlock,
    AssembledContext,
    TokenBudgetManager,
    PriorityLevel,
    PrioritizedContent,
    PriorityResolver,
    assign_priority,
    assign_tier,
    estimate_tokens,
)

__all__ = [
    # Pipeline
    'ContextPipeline',
    'ContextAssembler',
    'ContentSummarizer',
    'generate_content_summary',
    # UAF Models
    'AgentDefinition',
    'AgentCategory',
    'AgentTriggers',
    'AgentPrompt',
    'AgentChecklist',
    'DecisionContext',
    'ExtractedConstraints',
    'AssembledTaskContext',
    'MICSResponse',
    # Agent Loader
    'AgentLoader',
    'AgentMatcher',
    'get_builtin_agent',
    'get_all_builtin_agents',
    # Token Budget Management
    'TokenTier',
    'Position',
    'TokenBudgetConfig',
    'ContentBlock',
    'AssembledContext',
    'TokenBudgetManager',
    'PriorityLevel',
    'PrioritizedContent',
    'PriorityResolver',
    'assign_priority',
    'assign_tier',
    'estimate_tokens',
]
