"""
Token Budget Management for MICS

Implements tiered token allocation with position optimization
to avoid "lost in the middle" problem.

Per MICS-v2-FINAL-ARCHITECTURE.md:

TIER 1: CRITICAL (~500 tokens) - Position: START (first 20%)
  - Agent identity & role
  - Layer 0 principles (summarized)
  - PROHIBITIONS (blocking constraints)

TIER 2: IMPORTANT (~1500 tokens) - Position: NEAR START
  - Active decisions for current task
  - Requirements & limitations
  - Checklist steps

TIER 3: SUPPLEMENTARY (~1000 tokens) - Position: END (last 10%)
  - Codebase context
  - Tool hints & suggestions

TIER 4: REFERENCE (Load on-demand via MCP tools)
  - Full decision details
  - History, audit trails
  - Related decisions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class TokenTier(str, Enum):
    """Token budget tiers."""
    CRITICAL = "CRITICAL"        # START position
    IMPORTANT = "IMPORTANT"      # NEAR_START position
    SUPPLEMENTARY = "SUPPLEMENTARY"  # END position
    REFERENCE = "REFERENCE"      # On-demand


class Position(str, Enum):
    """Content position in context."""
    START = "START"           # First 20%
    NEAR_START = "NEAR_START" # 20-50%
    MIDDLE = "MIDDLE"         # 50-80% (avoid!)
    END = "END"               # Last 20%


@dataclass
class TokenBudgetConfig:
    """Configuration for token budget allocation."""
    total_budget: int = 4000

    # Tier allocations (percentages)
    tier_1_percent: float = 0.125   # ~500 tokens
    tier_2_percent: float = 0.375   # ~1500 tokens
    tier_3_percent: float = 0.25    # ~1000 tokens
    tier_4_percent: float = 0.25    # ~1000 tokens (on-demand reserve)

    @property
    def tier_1_budget(self) -> int:
        return int(self.total_budget * self.tier_1_percent)

    @property
    def tier_2_budget(self) -> int:
        return int(self.total_budget * self.tier_2_percent)

    @property
    def tier_3_budget(self) -> int:
        return int(self.total_budget * self.tier_3_percent)

    @property
    def tier_4_budget(self) -> int:
        return int(self.total_budget * self.tier_4_percent)


@dataclass
class ContentBlock:
    """A block of content with tier and priority."""
    content: str
    tier: TokenTier
    priority: int  # P0-P6
    token_count: int = 0
    content_type: str = "text"  # text, json, markdown
    source: str = ""  # Where this content came from

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = estimate_tokens(self.content)


@dataclass
class AssembledContext:
    """Final assembled context with position-optimized content."""
    # Positioned content
    start_content: str = ""       # CRITICAL tier
    near_start_content: str = ""  # IMPORTANT tier
    end_content: str = ""         # SUPPLEMENTARY tier

    # Metadata
    total_tokens: int = 0
    tier_usage: Dict[str, int] = field(default_factory=dict)
    truncated_items: List[str] = field(default_factory=list)
    reference_items: List[Dict] = field(default_factory=list)  # For on-demand loading

    def get_full_context(self) -> str:
        """Get full context with position optimization."""
        parts = []

        # START position (first 20%)
        if self.start_content:
            parts.append(self.start_content)

        # NEAR_START position
        if self.near_start_content:
            parts.append(self.near_start_content)

        # END position (recency effect)
        if self.end_content:
            parts.append(self.end_content)

        return "\n\n---\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "context": self.get_full_context(),
            "positioned_sections": {
                "start": self.start_content,
                "near_start": self.near_start_content,
                "end": self.end_content,
            },
            "meta": {
                "total_tokens": self.total_tokens,
                "tier_usage": self.tier_usage,
                "truncated_items": self.truncated_items,
                "reference_count": len(self.reference_items),
            }
        }


def estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    if not text:
        return 0
    # Rough estimate: 1 token ~= 4 characters (English)
    # For code/technical: 1 token ~= 3 characters
    return max(1, len(text) // 4)


def estimate_tokens_json(data: Any) -> int:
    """Estimate token count for JSON data."""
    return estimate_tokens(json.dumps(data, default=str))


class TokenBudgetManager:
    """
    Manages token allocation across tiers with position optimization.

    Usage:
        manager = TokenBudgetManager(total_budget=4000)
        manager.add_content("Agent identity...", TokenTier.CRITICAL, priority=1)
        manager.add_content("Decision 1...", TokenTier.IMPORTANT, priority=2)
        context = manager.assemble()
    """

    def __init__(self, config: Optional[TokenBudgetConfig] = None):
        self.config = config or TokenBudgetConfig()
        self.content_blocks: List[ContentBlock] = []
        self._tier_usage: Dict[TokenTier, int] = {
            TokenTier.CRITICAL: 0,
            TokenTier.IMPORTANT: 0,
            TokenTier.SUPPLEMENTARY: 0,
            TokenTier.REFERENCE: 0,
        }

    def add_content(
        self,
        content: str,
        tier: TokenTier,
        priority: int,
        content_type: str = "text",
        source: str = ""
    ) -> bool:
        """
        Add content block to the budget.

        Args:
            content: The content to add
            tier: Which tier this belongs to
            priority: P0-P6 priority (lower = higher priority)
            content_type: Type of content (text, json, markdown)
            source: Source identifier

        Returns:
            True if content was added, False if budget exceeded
        """
        block = ContentBlock(
            content=content,
            tier=tier,
            priority=priority,
            content_type=content_type,
            source=source
        )

        # Check if we have budget for this tier
        tier_budget = self._get_tier_budget(tier)
        current_usage = self._tier_usage[tier]

        if current_usage + block.token_count <= tier_budget:
            self.content_blocks.append(block)
            self._tier_usage[tier] += block.token_count
            return True

        return False

    def add_critical(self, content: str, priority: int = 0, source: str = "") -> bool:
        """Add critical content (START position)."""
        return self.add_content(content, TokenTier.CRITICAL, priority, source=source)

    def add_important(self, content: str, priority: int = 2, source: str = "") -> bool:
        """Add important content (NEAR_START position)."""
        return self.add_content(content, TokenTier.IMPORTANT, priority, source=source)

    def add_supplementary(self, content: str, priority: int = 4, source: str = "") -> bool:
        """Add supplementary content (END position)."""
        return self.add_content(content, TokenTier.SUPPLEMENTARY, priority, source=source)

    def add_reference(self, item: Dict[str, Any]) -> None:
        """Add reference item for on-demand loading."""
        # Reference items don't count against budget
        self.content_blocks.append(ContentBlock(
            content=json.dumps(item, default=str),
            tier=TokenTier.REFERENCE,
            priority=6,
            source="reference"
        ))

    def _get_tier_budget(self, tier: TokenTier) -> int:
        """Get budget for a specific tier."""
        budgets = {
            TokenTier.CRITICAL: self.config.tier_1_budget,
            TokenTier.IMPORTANT: self.config.tier_2_budget,
            TokenTier.SUPPLEMENTARY: self.config.tier_3_budget,
            TokenTier.REFERENCE: self.config.tier_4_budget,
        }
        return budgets.get(tier, 0)

    def assemble(self) -> AssembledContext:
        """
        Assemble all content into position-optimized context.

        Returns:
            AssembledContext with content positioned to avoid "lost in the middle"
        """
        # Sort blocks by tier and priority
        sorted_blocks = sorted(
            self.content_blocks,
            key=lambda b: (list(TokenTier).index(b.tier), b.priority)
        )

        # Separate by tier
        critical_blocks = [b for b in sorted_blocks if b.tier == TokenTier.CRITICAL]
        important_blocks = [b for b in sorted_blocks if b.tier == TokenTier.IMPORTANT]
        supplementary_blocks = [b for b in sorted_blocks if b.tier == TokenTier.SUPPLEMENTARY]
        reference_blocks = [b for b in sorted_blocks if b.tier == TokenTier.REFERENCE]

        # Build positioned content
        start_content = self._build_section(critical_blocks, "CRITICAL CONTEXT")
        near_start_content = self._build_section(important_blocks, "DECISIONS & REQUIREMENTS")
        end_content = self._build_section(supplementary_blocks, "ADDITIONAL CONTEXT")

        # Extract reference items
        reference_items = []
        for block in reference_blocks:
            try:
                reference_items.append(json.loads(block.content))
            except:
                reference_items.append({"content": block.content})

        # Calculate totals
        total_tokens = sum(b.token_count for b in sorted_blocks if b.tier != TokenTier.REFERENCE)

        return AssembledContext(
            start_content=start_content,
            near_start_content=near_start_content,
            end_content=end_content,
            total_tokens=total_tokens,
            tier_usage={
                "critical": self._tier_usage[TokenTier.CRITICAL],
                "important": self._tier_usage[TokenTier.IMPORTANT],
                "supplementary": self._tier_usage[TokenTier.SUPPLEMENTARY],
            },
            reference_items=reference_items,
        )

    def _build_section(self, blocks: List[ContentBlock], header: str) -> str:
        """Build a section from content blocks."""
        if not blocks:
            return ""

        parts = [f"## {header}\n"]
        for block in blocks:
            parts.append(block.content)

        return "\n\n".join(parts)

    def get_remaining_budget(self, tier: TokenTier) -> int:
        """Get remaining budget for a tier."""
        return self._get_tier_budget(tier) - self._tier_usage[tier]

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of budget usage."""
        return {
            "total_budget": self.config.total_budget,
            "tier_budgets": {
                "critical": self.config.tier_1_budget,
                "important": self.config.tier_2_budget,
                "supplementary": self.config.tier_3_budget,
                "reference": self.config.tier_4_budget,
            },
            "tier_usage": {
                "critical": self._tier_usage[TokenTier.CRITICAL],
                "important": self._tier_usage[TokenTier.IMPORTANT],
                "supplementary": self._tier_usage[TokenTier.SUPPLEMENTARY],
            },
            "remaining": {
                "critical": self.get_remaining_budget(TokenTier.CRITICAL),
                "important": self.get_remaining_budget(TokenTier.IMPORTANT),
                "supplementary": self.get_remaining_budget(TokenTier.SUPPLEMENTARY),
            },
        }


# =============================================================================
# Priority Hierarchy (P0-P6)
# =============================================================================

class PriorityLevel(int, Enum):
    """
    Priority hierarchy for conflict resolution.

    Per MICS-v2-FINAL-ARCHITECTURE.md:
    P0: Safety & Security (non-negotiable)
    P1: MANTRA Layer 0 (constitutional - immutable)
    P2: MANTRA Layer 1 (decisions - append-only)
    P3: Task Agent Prompts
    P4: Platform Instructions (claude.md, .cursorrules)
    P5: Codebase Patterns
    P6: Session Preferences
    """
    P0_SAFETY = 0
    P1_LAYER_0 = 1
    P2_LAYER_1 = 2
    P3_AGENT_PROMPTS = 3
    P4_PLATFORM = 4
    P5_CODEBASE = 5
    P6_SESSION = 6


@dataclass
class PrioritizedContent:
    """Content with priority level."""
    content: str
    priority: PriorityLevel
    source: str
    tier: TokenTier = TokenTier.IMPORTANT
    metadata: Dict[str, Any] = field(default_factory=dict)


class PriorityResolver:
    """
    Resolves conflicts between content with different priorities.

    Higher priority (lower P number) content always wins.
    """

    def __init__(self):
        self.content_items: List[PrioritizedContent] = []

    def add(
        self,
        content: str,
        priority: PriorityLevel,
        source: str,
        tier: TokenTier = TokenTier.IMPORTANT
    ) -> None:
        """Add content with priority."""
        self.content_items.append(PrioritizedContent(
            content=content,
            priority=priority,
            source=source,
            tier=tier
        ))

    def resolve(self) -> List[PrioritizedContent]:
        """
        Resolve priorities and return ordered content.

        Returns content sorted by priority (P0 first).
        """
        return sorted(self.content_items, key=lambda x: x.priority.value)

    def check_conflicts(self, new_content: str, new_priority: PriorityLevel) -> List[Dict]:
        """
        Check if new content would conflict with existing higher-priority content.

        Returns list of potential conflicts.
        """
        conflicts = []
        for item in self.content_items:
            if item.priority.value < new_priority.value:
                # Higher priority item exists
                # Simple check: look for contradicting keywords
                if self._might_conflict(new_content, item.content):
                    conflicts.append({
                        "existing_priority": item.priority.name,
                        "existing_source": item.source,
                        "existing_content_preview": item.content[:100],
                        "message": f"Higher priority ({item.priority.name}) content may conflict"
                    })

        return conflicts

    def _might_conflict(self, content1: str, content2: str) -> bool:
        """Simple conflict detection based on contradicting keywords."""
        # Look for negation patterns
        negation_pairs = [
            ("must", "must not"),
            ("always", "never"),
            ("require", "prohibit"),
            ("allow", "deny"),
            ("enable", "disable"),
        ]

        c1_lower = content1.lower()
        c2_lower = content2.lower()

        for pos, neg in negation_pairs:
            if (pos in c1_lower and neg in c2_lower) or (neg in c1_lower and pos in c2_lower):
                return True

        return False


def assign_priority(source_type: str) -> PriorityLevel:
    """Assign priority level based on content source."""
    mapping = {
        "safety": PriorityLevel.P0_SAFETY,
        "security": PriorityLevel.P0_SAFETY,
        "layer_0": PriorityLevel.P1_LAYER_0,
        "layer-0": PriorityLevel.P1_LAYER_0,
        "constitutional": PriorityLevel.P1_LAYER_0,
        "layer_1": PriorityLevel.P2_LAYER_1,
        "layer-1": PriorityLevel.P2_LAYER_1,
        "decision": PriorityLevel.P2_LAYER_1,
        "agent": PriorityLevel.P3_AGENT_PROMPTS,
        "agent_prompt": PriorityLevel.P3_AGENT_PROMPTS,
        "platform": PriorityLevel.P4_PLATFORM,
        "claude.md": PriorityLevel.P4_PLATFORM,
        "cursorrules": PriorityLevel.P4_PLATFORM,
        "codebase": PriorityLevel.P5_CODEBASE,
        "pattern": PriorityLevel.P5_CODEBASE,
        "session": PriorityLevel.P6_SESSION,
        "preference": PriorityLevel.P6_SESSION,
    }

    return mapping.get(source_type.lower(), PriorityLevel.P5_CODEBASE)


def assign_tier(priority: PriorityLevel) -> TokenTier:
    """Assign token tier based on priority level."""
    if priority in (PriorityLevel.P0_SAFETY, PriorityLevel.P1_LAYER_0):
        return TokenTier.CRITICAL
    elif priority in (PriorityLevel.P2_LAYER_1, PriorityLevel.P3_AGENT_PROMPTS):
        return TokenTier.IMPORTANT
    elif priority == PriorityLevel.P4_PLATFORM:
        return TokenTier.SUPPLEMENTARY
    else:
        return TokenTier.REFERENCE
