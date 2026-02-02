"""
MANTRA MCP Tools

Provides action tools for AI assistants:
- validate: Validate decision records
- query: Semantic search for decisions
- get_context: Get relevant context for tasks
- suggest_decisions: Suggest new decisions from code
- check_compliance: Check code compliance

Tools perform actions and return results.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ValidateTool:
    """Validation tool result."""
    result: str  # READY | INVALID | BLOCKED
    quality_score: int
    can_store: bool
    warnings: List[str]
    suggestions: List[str]
    arbitration_required: bool
    arbitration_contexts: Optional[List[Dict]] = None


@dataclass
class QueryTool:
    """Query tool result."""
    decisions: List[Dict]
    total: int
    query: str
    filters_applied: Dict[str, Any]


@dataclass
class ContextTool:
    """Context tool result."""
    decisions: List[Dict]
    total_tokens: int
    task_relevance: Dict[str, float]
    context_summary: str


class ToolProvider:
    """
    Provides MCP tool handlers.

    MICS Integration:
    - Tools perform ACTIONS (validate, query, analyze)
    - Support delegated AI arbitration
    - Respect token budgets for context
    """

    def __init__(self, repository=None, context_pipeline=None):
        """
        Initialize tool provider.

        Args:
            repository: DecisionRepository instance
            context_pipeline: ContextPipeline instance
        """
        self.repository = repository
        self.context_pipeline = context_pipeline

    async def validate(
        self,
        record: Dict[str, Any],
        arbitration_verdicts: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Validate a decision record.

        This is the primary tool for decision validation.
        Supports DELEGATED AI arbitration - if arbitration_required=true,
        the calling AI should perform arbitration and call again with verdicts.

        Args:
            record: Decision record to validate
            arbitration_verdicts: Optional verdicts from AI arbitration

        Returns:
            Validation result with quality, duplicates, conflicts, impact
        """
        if not self.repository:
            # Run validation without repository (schema + quality only)
            from ..use_cases.validate_decision import DecisionValidator
            from ..use_cases.quality_scoring import assess_quality

            validator = DecisionValidator()
            schema_result = validator.validate(record)
            quality = assess_quality(record)

            return {
                "result": "READY" if quality.can_store else "BLOCKED",
                "proposal_id": record.get("decision_id", "pending"),
                "quality": {
                    "overall_score": quality.overall_score,
                    "grade": quality.grade.value,
                    "statement_score": quality.statement_score,
                    "rationale_score": quality.rationale_score,
                    "can_store": quality.can_store,
                    "suggestions": quality.improvement_suggestions,
                    "has_layer_b": quality.has_layer_b,
                },
                "schema_valid": schema_result.status.value != "INVALID",
                "violations": [
                    {"rule_id": v.rule_id, "message": v.message}
                    for v in schema_result.violations
                ],
                "warnings": [],
                "arbitration_required": False,
            }

        # Full validation with repository
        from ..use_cases.enhanced_validation import (
            validate_enhanced_async,
            serialize_enhanced_response
        )

        result = await validate_enhanced_async(
            record=record,
            repository=self.repository,
            client_verdicts=arbitration_verdicts,
            arbitration_mode="DELEGATED"
        )

        return serialize_enhanced_response(result)

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        detail_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Query decisions with semantic search.

        Args:
            query: Natural language query or keywords
            filters: Optional filter criteria
            limit: Max results
            detail_level: micro|standard|detailed|sections

        Returns:
            Matching decisions
        """
        if not self.repository:
            return {"decisions": [], "total": 0, "error": "Repository not configured"}

        try:
            # Fetch all decisions
            stored = await self.repository.find_all_async(limit=10000, offset=0)

            # Simple keyword matching (would use embeddings in production)
            query_lower = query.lower()
            query_words = set(query_lower.split())

            scored_decisions = []
            for sd in stored:
                d = sd.decision
                text = f"{d.statement} {d.rationale}".lower()

                # Calculate relevance score
                matches = sum(1 for w in query_words if w in text)
                if matches > 0:
                    score = matches / len(query_words)
                    scored_decisions.append((score, d))

            # Sort by score and limit
            scored_decisions.sort(key=lambda x: x[0], reverse=True)
            scored_decisions = scored_decisions[:limit]

            # Format results
            decisions = []
            for score, d in scored_decisions:
                record = {
                    "decision_id": d.decision_id,
                    "decision_code": d.decision_code,
                    "domain_id": d.domain_id.value if hasattr(d.domain_id, 'value') else d.domain_id,
                    "aspect_id": d.aspect_id.value if hasattr(d.aspect_id, 'value') else d.aspect_id,
                    "relevance_score": score,
                }

                if detail_level != "micro":
                    record["statement"] = d.statement
                    record["rationale"] = d.rationale[:200] + "..." if len(d.rationale) > 200 else d.rationale

                if detail_level == "detailed":
                    record["detailed_content"] = d.detailed_content
                    record["tags"] = d.tags or []

                decisions.append(record)

            return {
                "decisions": decisions,
                "total": len(decisions),
                "query": query,
                "filters_applied": filters or {},
                "detail_level": detail_level
            }

        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"decisions": [], "total": 0, "error": str(e)}

    async def get_context(
        self,
        task_description: str,
        code_context: Optional[str] = None,
        token_budget: int = 2000
    ) -> Dict[str, Any]:
        """
        Get relevant context for a task.

        MICS Smart Context Injection:
        1. Analyze task and code context
        2. Select relevant decisions
        3. Assemble within token budget
        4. Return tiered context

        Args:
            task_description: What the AI is trying to do
            code_context: Optional code snippet or file path
            token_budget: Max tokens for context

        Returns:
            Relevant decisions and context summary
        """
        if self.context_pipeline:
            # Use dedicated context pipeline
            return await self.context_pipeline.assemble(
                task=task_description,
                code=code_context,
                budget=token_budget
            )

        # Fallback: simple keyword-based selection
        if not self.repository:
            return {
                "decisions": [],
                "total_tokens": 0,
                "context_summary": "No repository configured"
            }

        try:
            # Extract keywords from task
            task_keywords = _extract_keywords(task_description)
            code_keywords = _extract_keywords(code_context) if code_context else set()
            all_keywords = task_keywords | code_keywords

            # Query relevant decisions
            query_result = await self.query(
                query=" ".join(all_keywords),
                limit=20,
                detail_level="standard"
            )

            # Estimate tokens and trim to budget
            decisions = []
            total_tokens = 0
            for d in query_result["decisions"]:
                est_tokens = _estimate_tokens(d)
                if total_tokens + est_tokens <= token_budget:
                    decisions.append(d)
                    total_tokens += est_tokens
                else:
                    # Try micro version
                    micro_d = {"decision_code": d["decision_code"], "statement": d.get("statement", "")[:100]}
                    micro_tokens = _estimate_tokens(micro_d)
                    if total_tokens + micro_tokens <= token_budget:
                        decisions.append(micro_d)
                        total_tokens += micro_tokens

            # Generate context summary
            summary = _generate_context_summary(decisions, task_description)

            return {
                "decisions": decisions,
                "total_tokens": total_tokens,
                "token_budget": token_budget,
                "keywords_matched": list(all_keywords)[:10],
                "context_summary": summary
            }

        except Exception as e:
            logger.error(f"Context error: {e}")
            return {"decisions": [], "total_tokens": 0, "error": str(e)}

    async def suggest_decisions(
        self,
        code_snippet: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest new decisions based on code analysis.

        Identifies patterns that should be documented as decisions:
        - Architectural patterns (DI, factory, repository)
        - Coding conventions (naming, structure)
        - Technology choices (frameworks, libraries)
        - Security practices

        Args:
            code_snippet: Code to analyze
            file_path: Optional file path for context

        Returns:
            Suggested decisions
        """
        suggestions = []

        # Pattern detection
        patterns = _detect_patterns(code_snippet)

        for pattern in patterns:
            suggestion = {
                "pattern_detected": pattern["name"],
                "confidence": pattern["confidence"],
                "suggested_decision": {
                    "domain_id": pattern["domain"],
                    "aspect_id": pattern["aspect"],
                    "statement": pattern["suggested_statement"],
                    "rationale": pattern["suggested_rationale"],
                },
                "evidence": pattern["evidence"],
            }
            suggestions.append(suggestion)

        return {
            "suggestions": suggestions,
            "file_path": file_path,
            "patterns_detected": len(suggestions)
        }

    async def check_compliance(
        self,
        code_snippet: str,
        file_path: Optional[str] = None,
        decision_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check code compliance with MANTRA decisions.

        Args:
            code_snippet: Code to check
            file_path: Optional file path
            decision_ids: Optional specific decisions to check

        Returns:
            Compliance report with violations
        """
        if not self.repository:
            return {"compliant": True, "violations": [], "error": "Repository not configured"}

        try:
            # Get relevant decisions
            if decision_ids:
                decisions = []
                for did in decision_ids:
                    stored = await self.repository.find_by_id_async(did)
                    if stored:
                        decisions.append(stored.decision)
            else:
                # Infer relevant decisions from code
                context = await self.get_context(
                    task_description=f"Check compliance for: {file_path or 'code'}",
                    code_context=code_snippet,
                    token_budget=5000
                )
                decision_codes = [d.get("decision_code") for d in context.get("decisions", [])]
                decisions = []
                for code in decision_codes:
                    stored = await self.repository.find_by_code_async(code)
                    if stored:
                        decisions.append(stored.decision)

            # Check compliance
            violations = []
            for d in decisions:
                for constraint in (d.constraints or []):
                    violation = _check_constraint(code_snippet, constraint)
                    if violation:
                        violations.append({
                            "decision_code": d.decision_code,
                            "constraint_type": constraint.type.value if hasattr(constraint.type, 'value') else constraint.type,
                            "constraint_statement": constraint.statement,
                            "violation": violation,
                        })

            return {
                "compliant": len(violations) == 0,
                "violations": violations,
                "decisions_checked": len(decisions),
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return {"compliant": True, "violations": [], "error": str(e)}


# =============================================================================
# Helper Functions
# =============================================================================

def _extract_keywords(text: Optional[str]) -> set:
    """Extract keywords from text."""
    if not text:
        return set()

    # Common technical keywords
    tech_keywords = {
        'database', 'api', 'authentication', 'authorization', 'security',
        'frontend', 'backend', 'service', 'component', 'module',
        'react', 'vue', 'angular', 'fastapi', 'django', 'express',
        'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'testing', 'deployment', 'ci', 'cd', 'infrastructure'
    }

    words = set(re.findall(r'\b\w{4,}\b', text.lower()))
    return words & tech_keywords | {w for w in words if len(w) > 6}


def _estimate_tokens(data: Dict[str, Any]) -> int:
    """Estimate token count for data."""
    import json
    text = json.dumps(data)
    # Rough estimate: 1 token ~= 4 characters
    return len(text) // 4


def _generate_context_summary(decisions: List[Dict], task: str) -> str:
    """Generate a summary of context decisions."""
    if not decisions:
        return "No relevant decisions found for this task."

    domains = {}
    for d in decisions:
        dom = d.get("domain_id", "UNKNOWN")
        if dom not in domains:
            domains[dom] = []
        domains[dom].append(d.get("decision_code", ""))

    lines = [f"Found {len(decisions)} relevant decisions for: {task[:50]}..."]
    for dom, codes in domains.items():
        lines.append(f"- {dom}: {', '.join(codes[:3])}" + ("..." if len(codes) > 3 else ""))

    return "\n".join(lines)


def _detect_patterns(code: str) -> List[Dict[str, Any]]:
    """Detect architectural/coding patterns in code."""
    patterns = []

    # Repository pattern
    if re.search(r'class\s+\w*Repository', code, re.IGNORECASE):
        patterns.append({
            "name": "Repository Pattern",
            "confidence": 0.9,
            "domain": "ARCH",
            "aspect": "DATABASE",
            "suggested_statement": "Use Repository pattern for data access abstraction",
            "suggested_rationale": "Repository pattern separates data access logic from business logic",
            "evidence": "Found Repository class definition"
        })

    # Dependency Injection
    if re.search(r'def\s+__init__\s*\([^)]*:\s*\w+', code):
        patterns.append({
            "name": "Dependency Injection",
            "confidence": 0.7,
            "domain": "ARCH",
            "aspect": "API",
            "suggested_statement": "Use constructor injection for dependencies",
            "suggested_rationale": "DI enables loose coupling and testability",
            "evidence": "Found typed constructor parameters"
        })

    # FastAPI endpoint
    if re.search(r'@(router|app)\.(get|post|put|delete|patch)', code):
        patterns.append({
            "name": "RESTful Endpoints",
            "confidence": 0.95,
            "domain": "STD",
            "aspect": "API",
            "suggested_statement": "Use RESTful conventions for API endpoints",
            "suggested_rationale": "RESTful APIs are predictable and self-documenting",
            "evidence": "Found FastAPI route decorators"
        })

    # Type hints
    if re.search(r'->\s*(List|Dict|Optional|str|int|bool)', code):
        patterns.append({
            "name": "Type Hints",
            "confidence": 0.85,
            "domain": "STD",
            "aspect": "API",
            "suggested_statement": "Use type hints for all function signatures",
            "suggested_rationale": "Type hints improve code quality and IDE support",
            "evidence": "Found return type annotations"
        })

    return patterns


def _check_constraint(code: str, constraint) -> Optional[str]:
    """Check if code violates a constraint."""
    stmt = constraint.statement.lower() if hasattr(constraint, 'statement') else str(constraint).lower()
    code_lower = code.lower()

    # Simple keyword-based violation detection
    # In production, this would use more sophisticated analysis

    if "must not" in stmt or "cannot" in stmt or "prohibited" in stmt:
        # Check for prohibited patterns
        if "hardcode" in stmt and re.search(r'["\'][a-zA-Z0-9]{20,}["\']', code):
            return "Potential hardcoded secret detected"
        if "print" in stmt and "print(" in code_lower:
            return "Print statement found (may violate logging requirement)"

    if "must" in stmt:
        # Check for required patterns
        if "logging" in stmt and "logger" not in code_lower:
            return "Logger not found (logging may be required)"
        if "type hint" in stmt and not re.search(r'->\s*\w+', code):
            return "Missing return type hints"

    return None


# =============================================================================
# WRITE OPERATIONS (Require Human Confirmation)
# =============================================================================

class WriteToolProvider:
    """
    Write operation tools for MCP.

    IMPORTANT: All write operations require human confirmation.
    AI CANNOT directly store decisions - human must approve.

    Flow:
    1. AI calls classify/propose → gets validated proposal
    2. AI presents proposal to human
    3. Human confirms → AI calls store with human_confirmed=true
    4. MANTRA stores the decision

    This follows MICS philosophy: MANTRA is ADDITIVE, not RESTRICTIVE.
    Human authority is 100% - AI only suggests.
    """

    def __init__(self, repository=None):
        self.repository = repository
        self._pending_proposals: Dict[str, Dict] = {}  # proposal_id -> proposal

    async def classify(
        self,
        statement: str,
        rationale: str,
        constraints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Auto-classify a decision into Domain and Aspect.

        Returns classification suggestion with confidence.
        Does NOT store anything.

        Args:
            statement: Decision statement
            rationale: Why this decision was made
            constraints: Optional constraints list

        Returns:
            Classification result with domain_id, aspect_id, confidence
        """
        try:
            from ..use_cases.ai_arbiter.decision_classifier import (
                get_classification_context,
                DecisionClassifier
            )

            # Get delegated context (AI performs classification)
            context = get_classification_context(statement, rationale, constraints)

            # Add helper info
            context["usage_hint"] = (
                "As AI assistant, analyze the statement and rationale to determine "
                "the best Domain (INT/ARCH/CTL/EVO) and Aspect (F01-F16). "
                "Return your classification with confidence score."
            )

            return {
                "action": "CLASSIFY",
                "requires_ai_decision": True,
                "classification_context": context,
                "statement_preview": statement[:100] + "..." if len(statement) > 100 else statement,
            }

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {"error": str(e)}

    async def propose(
        self,
        decision: Dict[str, Any],
        proposed_by: str = "ai_assistant"
    ) -> Dict[str, Any]:
        """
        Propose a new decision (validate without storing).

        Creates a proposal that can be reviewed and then stored.
        Does NOT store the decision - human must call store() to persist.

        Args:
            decision: Full decision record
            proposed_by: Who is proposing

        Returns:
            Validated proposal with proposal_id
        """
        import uuid
        from datetime import datetime

        try:
            # Validate the decision
            from ..use_cases.validate_decision import DecisionValidator
            from ..use_cases.quality_scoring import assess_quality

            validator = DecisionValidator()
            schema_result = validator.validate(decision)
            quality = assess_quality(decision)

            # Generate proposal ID
            proposal_id = str(uuid.uuid4())

            # Create proposal
            proposal = {
                "proposal_id": proposal_id,
                "decision": decision,
                "proposed_by": proposed_by,
                "proposed_at": datetime.utcnow().isoformat(),
                "validation": {
                    "schema_valid": schema_result.status.value != "INVALID",
                    "violations": [
                        {"rule_id": v.rule_id, "message": v.message}
                        for v in schema_result.violations
                    ],
                    "quality": {
                        "overall_score": quality.overall_score,
                        "grade": quality.grade.value,
                        "can_store": quality.can_store,
                        "suggestions": quality.improvement_suggestions,
                    }
                },
                "status": "PENDING_HUMAN_APPROVAL",
                "human_confirmed": False,
            }

            # Store in pending (in-memory for now, could use Redis)
            self._pending_proposals[proposal_id] = proposal

            # Check for supersedes suggestion if repository available
            supersedes_suggestion = None
            if self.repository and decision.get("domain_id") and decision.get("aspect_id"):
                from ..api.routes import _check_supersedes_suggestion
                supersedes_suggestion = await _check_supersedes_suggestion(
                    statement=decision.get("statement", ""),
                    rationale=decision.get("rationale", ""),
                    domain_id=decision.get("domain_id"),
                    aspect_id=decision.get("aspect_id"),
                    repository=self.repository
                )

            return {
                "action": "PROPOSAL_CREATED",
                "proposal_id": proposal_id,
                "status": "PENDING_HUMAN_APPROVAL",
                "validation": proposal["validation"],
                "supersedes_suggestion": supersedes_suggestion,
                "next_step": (
                    "Present this proposal to the human user. "
                    "If they approve, call mantra_store with human_confirmed=true"
                ),
                "human_action_required": True,
            }

        except Exception as e:
            logger.error(f"Propose error: {e}")
            return {"error": str(e)}

    async def store(
        self,
        proposal_id: Optional[str] = None,
        decision: Optional[Dict[str, Any]] = None,
        human_confirmed: bool = False,
        stored_by: str = "ai_assistant"
    ) -> Dict[str, Any]:
        """
        Store a decision (REQUIRES human_confirmed=true).

        IMPORTANT: This will FAIL if human_confirmed is not true.
        The AI assistant MUST get explicit human approval before calling this.

        Args:
            proposal_id: ID from previous propose() call
            decision: Or provide decision directly (will be validated)
            human_confirmed: MUST be true - indicates human approved
            stored_by: Who is storing

        Returns:
            Stored decision or rejection
        """
        # CRITICAL: Require human confirmation
        if not human_confirmed:
            return {
                "action": "REJECTED",
                "reason": "HUMAN_CONFIRMATION_REQUIRED",
                "message": (
                    "Cannot store decision without human confirmation. "
                    "Set human_confirmed=true ONLY after the human user "
                    "has explicitly approved this decision. "
                    "AI assistants must NEVER set this flag without human approval."
                ),
                "human_action_required": True,
            }

        if not self.repository:
            return {"error": "Repository not configured"}

        try:
            # Get decision from proposal or direct
            if proposal_id and proposal_id in self._pending_proposals:
                proposal = self._pending_proposals[proposal_id]
                decision = proposal["decision"]
                del self._pending_proposals[proposal_id]  # Clear pending
            elif not decision:
                return {"error": "Provide proposal_id or decision"}

            # Final validation
            from ..use_cases.validate_decision import DecisionValidator
            validator = DecisionValidator()
            schema_result = validator.validate(decision)

            if schema_result.status.value == "INVALID":
                return {
                    "action": "VALIDATION_FAILED",
                    "violations": [
                        {"rule_id": v.rule_id, "message": v.message}
                        for v in schema_result.violations
                    ]
                }

            # Store the decision
            from ..domain.schema import Decision, StoredDecision
            from datetime import datetime
            import uuid

            # Ensure decision has required fields
            if not decision.get("decision_id"):
                decision["decision_id"] = str(uuid.uuid4())
            if not decision.get("created_by"):
                decision["created_by"] = stored_by

            # Create Decision object
            decision_obj = Decision(**decision)
            stored = StoredDecision(
                decision=decision_obj,
                stored_at=datetime.utcnow(),
                stored_by=stored_by
            )

            # Store via repository
            await self.repository.store_async(stored)

            return {
                "action": "STORED",
                "decision_id": decision_obj.decision_id,
                "decision_code": decision_obj.decision_code,
                "stored_by": stored_by,
                "stored_at": stored.stored_at.isoformat(),
                "message": "Decision stored successfully in MANTRA constitutional law system.",
            }

        except Exception as e:
            logger.error(f"Store error: {e}")
            return {"error": str(e)}

    async def approve(
        self,
        proposal_id: str,
        approved_by: str = "human_user",
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Approve and store a pending proposal.

        This is a convenience method that combines human approval + storage.
        Should be called AFTER human explicitly approves the proposal.

        Args:
            proposal_id: ID of the pending proposal
            approved_by: Who approved (should be human user identifier)
            modifications: Optional modifications to apply before storing

        Returns:
            Stored decision
        """
        if proposal_id not in self._pending_proposals:
            return {
                "error": "PROPOSAL_NOT_FOUND",
                "message": f"No pending proposal with ID {proposal_id}",
            }

        proposal = self._pending_proposals[proposal_id]
        decision = proposal["decision"].copy()

        # Apply modifications if any
        if modifications:
            decision.update(modifications)

        # Store with human confirmation
        return await self.store(
            decision=decision,
            human_confirmed=True,
            stored_by=approved_by
        )

    async def challenge(
        self,
        existing_decision_id: str,
        new_decision: Dict[str, Any],
        challenge_reason: str,
        challenged_by: str = "ai_assistant",
        human_confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Challenge an existing decision with a superseding version.

        Creates a new decision that supersedes the existing one.
        Requires human confirmation before storage.

        Args:
            existing_decision_id: ID of decision being challenged
            new_decision: The superseding decision
            challenge_reason: Why this challenge is being made
            challenged_by: Who is challenging
            human_confirmed: MUST be true for storage

        Returns:
            Challenge result
        """
        if not self.repository:
            return {"error": "Repository not configured"}

        try:
            # Get existing decision
            existing = await self.repository.find_by_id_async(existing_decision_id)
            if not existing:
                return {
                    "error": "DECISION_NOT_FOUND",
                    "message": f"No decision found with ID {existing_decision_id}",
                }

            # Set supersedes relationship
            new_decision["supersedes"] = existing_decision_id
            new_decision["supersedes_reason"] = challenge_reason

            # If human not confirmed, return proposal
            if not human_confirmed:
                proposal_result = await self.propose(
                    decision=new_decision,
                    proposed_by=challenged_by
                )

                return {
                    "action": "CHALLENGE_PROPOSED",
                    "existing_decision": {
                        "decision_id": existing.decision.decision_id,
                        "decision_code": existing.decision.decision_code,
                        "statement": existing.decision.statement[:200],
                    },
                    "proposal": proposal_result,
                    "challenge_reason": challenge_reason,
                    "message": (
                        "Challenge proposal created. "
                        "Human must approve before this supersedes the existing decision."
                    ),
                    "human_action_required": True,
                }

            # Human confirmed - store the challenge
            return await self.store(
                decision=new_decision,
                human_confirmed=True,
                stored_by=challenged_by
            )

        except Exception as e:
            logger.error(f"Challenge error: {e}")
            return {"error": str(e)}

    async def get_pending_proposals(self) -> Dict[str, Any]:
        """List all pending proposals awaiting human approval."""
        proposals = []
        for pid, proposal in self._pending_proposals.items():
            proposals.append({
                "proposal_id": pid,
                "statement_preview": proposal["decision"].get("statement", "")[:100],
                "proposed_by": proposal["proposed_by"],
                "proposed_at": proposal["proposed_at"],
                "validation_grade": proposal["validation"]["quality"]["grade"],
            })

        return {
            "pending_count": len(proposals),
            "proposals": proposals,
        }


# =============================================================================
# MICS-SPECIFIC TOOLS (Intelligent Context System)
# =============================================================================

class MICSToolProvider:
    """
    MICS (MANTRA Intelligent Context System) tools.

    Provides enhanced context injection with:
    - Task-specific agent prompts (loaded from YAML)
    - Checklists and constraints
    - Decision lineage tracking
    - Decision comparison

    Per MICS-TECHNICAL-DESIGN.md:
    - Context Assembly Pipeline (7 stages)
    - Token Budget Management
    - Tiered Content Delivery
    - Universal Agent Format (UAF)

    Uses AgentLoader to load agent definitions from YAML files.
    Falls back to built-in agents if YAML files not available.
    """

    def __init__(self, repository=None, agents_dir=None):
        """
        Initialize MICS tool provider.

        Args:
            repository: DecisionRepository instance
            agents_dir: Path to agents directory (optional)
        """
        self.repository = repository

        # Initialize agent loader
        try:
            # Try multiple import strategies
            AgentLoader = None
            get_all_builtin_agents = None

            # Strategy 1: Relative import (package mode)
            try:
                from ..context.agent_loader import AgentLoader, get_all_builtin_agents
            except (ImportError, ValueError):
                pass

            # Strategy 2: Absolute import with full path
            if AgentLoader is None:
                try:
                    import sys
                    import os
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if backend_dir not in sys.path:
                        sys.path.insert(0, backend_dir)
                    from context.agent_loader import AgentLoader, get_all_builtin_agents
                except ImportError:
                    pass

            if AgentLoader is not None:
                self._agent_loader = AgentLoader(agents_dir)
                self._builtin_agents = get_all_builtin_agents() if get_all_builtin_agents else {}
            else:
                raise ImportError("Could not import AgentLoader from any path")
        except Exception as e:
            logger.warning(f"Failed to initialize AgentLoader: {e}")
            self._agent_loader = None
            self._builtin_agents = {}

    def _get_agent(self, agent_id: str):
        """Get agent by ID from loader or built-in."""
        if self._agent_loader:
            agent = self._agent_loader.load(agent_id)
            if agent:
                return agent

        # Fallback to built-in
        return self._builtin_agents.get(agent_id) or self._builtin_agents.get(f"{agent_id}-agent")

    def _match_intent(self, intent: str, target: str = None):
        """Match intent to agent."""
        if self._agent_loader:
            agent, confidence = self._agent_loader.match_intent(intent, target)
            if agent:
                return agent, confidence

        # Fallback: simple keyword matching on built-in agents
        intent_lower = intent.lower()
        target_lower = (target or "").lower()
        combined = f"{intent_lower} {target_lower}"

        best_agent = None
        best_score = 0

        for agent in self._builtin_agents.values():
            score = 0
            for kw in agent.get_all_keywords():
                if kw.lower() in combined:
                    score += 1
            if score > best_score:
                best_score = score
                best_agent = agent

        confidence = min(0.95, 0.5 + (best_score * 0.15))
        return best_agent, confidence

    async def get_task_context(
        self,
        intent: str,
        target: Optional[str] = None,
        environment: Optional[str] = None,
        code_context: Optional[str] = None,
        token_budget: int = 4000,
        platform: str = "claude-code"
    ) -> Dict[str, Any]:
        """
        Get intelligent task context with agent prompt and checklist.

        MICS Context Assembly Pipeline (7 stages):
        1. Intent Recognition - Identify task type from keywords
        2. Agent Loading - Load agent from YAML or built-in
        3. Decision Retrieval - Get relevant decisions from repository
        4. Constraint Extraction - Extract rules from decisions
        5. Codebase Context - Add relevant file info
        6. Template Rendering - Build agent prompt
        7. Platform Adaptation - Format for target platform

        Args:
            intent: What the user wants to do (e.g., "deploy backend to production")
            target: What is being worked on (backend, frontend, etc.)
            environment: Target environment (dev, staging, production)
            code_context: Optional code snippet or file path
            token_budget: Max tokens for context
            platform: Target platform (claude-code, cursor, openai, generic)

        Returns:
            Complete task context with agent, decisions, checklist, constraints
        """
        import time
        start_time = time.time()

        # Stage 1 & 2: Intent Recognition + Agent Loading
        agent, confidence = self._match_intent(intent, target)

        if not agent:
            # Fallback to backend agent
            agent = self._get_agent("backend-agent")
            confidence = 0.5

        agent_id = agent.id if agent else "backend-agent"
        agent_name = agent.name if agent else "Backend Agent"

        # Stage 3: Decision Retrieval
        decisions = await self._retrieve_decisions(agent)

        # Stage 4: Constraint Extraction
        constraints = self._extract_constraints(agent, decisions)

        # Stage 5: Codebase Context
        codebase_context = self._build_codebase_context(code_context)

        # Stage 6: Template Rendering
        prompt = self._render_prompt(
            agent=agent,
            intent=intent,
            target=target,
            environment=environment,
            decisions=decisions,
            constraints=constraints
        )

        # Stage 7: Platform Adaptation + Response Assembly
        checklist = self._get_checklist(agent)

        assembly_time_ms = int((time.time() - start_time) * 1000)

        return {
            "task_context": {
                "agent": {
                    "id": agent_id,
                    "name": agent_name,
                    "version": agent.version if agent else "1.0.0",
                    "confidence": confidence,
                    "category": agent.category.value if agent and hasattr(agent.category, 'value') else "general",
                },
                "prompt": prompt,
                "decisions": decisions[:10],  # Limit for token budget
                "constraints": constraints,
                "checklist": checklist,
                "codebase_context": codebase_context,
            },
            "meta": {
                "token_estimate": len(prompt) // 4,
                "decisions_count": len(decisions),
                "assembly_time_ms": assembly_time_ms,
                "agent_matched": agent_id,
                "confidence": confidence,
                "platform": platform,
            },
            "hints": self._get_platform_hints(agent, platform),
        }

    async def _retrieve_decisions(self, agent) -> List[Dict[str, Any]]:
        """Stage 3: Retrieve decisions based on agent context."""
        decisions = []

        if not self.repository or not agent:
            return decisions

        try:
            # Get domains and aspects from agent
            domains = agent.get_required_domains() if agent else []
            aspects = agent.get_all_aspects() if agent else []

            for domain_id in domains[:2]:  # Limit to top 2 domains
                from ..domain.schema import DomainId
                try:
                    domain_enum = DomainId(domain_id)
                    stored_list = await self.repository.find_by_domain_async(
                        domain_id=domain_enum,
                        limit=10
                    )
                    for stored in stored_list:
                        d = stored.decision
                        # Filter by aspects
                        aspect_val = d.aspect_id.value if hasattr(d.aspect_id, 'value') else d.aspect_id
                        if not aspects or aspect_val in aspects:
                            decisions.append({
                                "decision_id": d.decision_id,
                                "decision_code": d.decision_code,
                                "domain_id": domain_id,
                                "aspect_id": aspect_val,
                                "statement": d.statement,
                                "rationale": d.rationale[:200] if d.rationale else "",
                                "constraints": [
                                    {
                                        "type": c.type.value if hasattr(c.type, 'value') else c.type,
                                        "statement": c.statement
                                    }
                                    for c in (d.constraints or [])[:3]
                                ],
                                "tags": d.tags or [],
                            })
                except Exception as e:
                    logger.debug(f"Failed to fetch domain {domain_id}: {e}")

        except Exception as e:
            logger.error(f"Decision retrieval error: {e}")

        return decisions

    def _extract_constraints(self, agent, decisions: List[Dict]) -> Dict[str, List[str]]:
        """Stage 4: Extract constraints from agent rules and decisions."""
        prohibitions = []
        requirements = []
        limitations = []

        # From agent critical rules
        if agent:
            prohibitions.extend(agent.get_blocking_rules())
            requirements.extend(agent.get_warning_rules())

        # From decisions
        for d in decisions:
            for c in d.get("constraints", []):
                c_type = c.get("type", "")
                c_stmt = c.get("statement", "")
                if c_type == "PROHIBITION":
                    prohibitions.append(c_stmt)
                elif c_type == "REQUIREMENT":
                    requirements.append(c_stmt)
                elif c_type == "LIMITATION":
                    limitations.append(c_stmt)

        return {
            "prohibitions": list(set(prohibitions))[:10],
            "requirements": list(set(requirements))[:10],
            "limitations": list(set(limitations))[:5],
        }

    def _build_codebase_context(self, code_context: Optional[str]) -> Dict[str, Any]:
        """Stage 5: Build codebase context."""
        context = {}
        if code_context:
            context["provided_code"] = code_context[:500]
        return context

    def _render_prompt(
        self,
        agent,
        intent: str,
        target: Optional[str],
        environment: Optional[str],
        decisions: List[Dict],
        constraints: Dict[str, List[str]]
    ) -> str:
        """Stage 6: Render agent prompt template."""
        agent_name = agent.name if agent else "Task Agent"
        identity = agent.prompt.identity if agent else ""

        # Build prompt sections
        prompt_parts = [f"# {agent_name}"]

        if identity:
            prompt_parts.append(f"\n{identity.strip()}")

        prompt_parts.append(f"""
## Current Task
- Intent: {intent}
- Target: {target or 'not specified'}
- Environment: {environment or 'not specified'}
""")

        # Critical Rules (BLOCKING)
        if constraints.get("prohibitions"):
            rules = "\n".join(f"- ❌ {r}" for r in constraints["prohibitions"][:5])
            prompt_parts.append(f"## Critical Rules (BLOCKING)\n{rules}")

        # Requirements
        if constraints.get("requirements"):
            reqs = "\n".join(f"- ✓ {r}" for r in constraints["requirements"][:5])
            prompt_parts.append(f"\n## Requirements\n{reqs}")

        # Relevant Decisions
        if decisions:
            decision_text = "\n".join(
                f"### {d['decision_code']}: {d['statement'][:100]}..."
                for d in decisions[:5]
            )
            prompt_parts.append(f"\n## Relevant Decisions\n{decision_text}")

        # Checklist
        checklist = self._get_checklist(agent)
        if checklist:
            checklist_text = "\n".join(
                f"{i+1}. [ ] {step['step']}" + (f" (`{step.get('command')}`)" if step.get('command') else '')
                for i, step in enumerate(checklist)
            )
            prompt_parts.append(f"\n## Checklist\n{checklist_text}")

        return "\n".join(prompt_parts)

    def _get_checklist(self, agent) -> List[Dict[str, Any]]:
        """Get flat checklist from agent."""
        if not agent:
            return []

        checklist = []
        for item in agent.get_flat_checklist():
            checklist.append({
                "id": item.id,
                "step": item.step,
                "command": item.command,
                "blocking": item.blocking,
            })
        return checklist

    def _get_platform_hints(self, agent, platform: str) -> Dict[str, Any]:
        """Stage 7: Get platform-specific hints."""
        hints = {
            "tool_suggestions": [
                "Use mantra_validate before making changes",
                "Use mantra_check_compliance after changes",
                "Use mantra_propose when creating new decisions",
            ],
        }

        if agent and platform == "claude-code":
            if agent.platform_adapters and agent.platform_adapters.claude:
                hints["mcp_tool_hints"] = agent.platform_adapters.claude.mcp_tool_hints

        return hints

    async def get_lineage(
        self,
        decision_id: str,
        direction: str = "both"  # "ancestors" | "descendants" | "both"
    ) -> Dict[str, Any]:
        """
        Get decision lineage (version history via supersedes chain).

        Traces the evolution of a decision through its supersedes relationships.

        Args:
            decision_id: The decision to trace
            direction: Which direction to trace
                - "ancestors": Decisions this one supersedes
                - "descendants": Decisions that supersede this one
                - "both": Full lineage

        Returns:
            Lineage tree with all related decisions
        """
        if not self.repository:
            return {"error": "Repository not configured"}

        try:
            # Get the starting decision
            stored = await self.repository.find_by_id_async(decision_id)
            if not stored:
                return {"error": f"Decision not found: {decision_id}"}

            decision = stored.decision
            lineage = {
                "current": {
                    "decision_id": decision.decision_id,
                    "decision_code": decision.decision_code,
                    "statement": decision.statement[:150],
                    "supersedes": decision.supersedes,
                    "status": decision.status.value if hasattr(decision.status, 'value') else str(decision.status),
                },
                "ancestors": [],
                "descendants": [],
            }

            # Trace ancestors (what this decision supersedes)
            if direction in ("ancestors", "both") and decision.supersedes:
                current_id = decision.supersedes
                depth = 0
                while current_id and depth < 10:  # Limit depth
                    ancestor = await self.repository.find_by_id_async(current_id)
                    if ancestor:
                        a = ancestor.decision
                        lineage["ancestors"].append({
                            "decision_id": a.decision_id,
                            "decision_code": a.decision_code,
                            "statement": a.statement[:100],
                            "depth": depth + 1,
                        })
                        current_id = a.supersedes
                        depth += 1
                    else:
                        break

            # Trace descendants (what supersedes this decision)
            if direction in ("descendants", "both"):
                # Search all decisions for ones that supersede this
                all_decisions = await self.repository.find_all_async(limit=1000, offset=0)
                for sd in all_decisions:
                    d = sd.decision
                    if d.supersedes == decision_id:
                        lineage["descendants"].append({
                            "decision_id": d.decision_id,
                            "decision_code": d.decision_code,
                            "statement": d.statement[:100],
                        })

            return {
                "lineage": lineage,
                "total_ancestors": len(lineage["ancestors"]),
                "total_descendants": len(lineage["descendants"]),
                "is_superseded": len(lineage["descendants"]) > 0,
                "is_latest": len(lineage["descendants"]) == 0,
            }

        except Exception as e:
            logger.error(f"Lineage error: {e}")
            return {"error": str(e)}

    async def compare(
        self,
        decision_id_1: str,
        decision_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two decisions side by side.

        Useful for:
        - Comparing an old decision with its superseding version
        - Finding differences between similar decisions
        - Understanding decision evolution

        Args:
            decision_id_1: First decision ID
            decision_id_2: Second decision ID

        Returns:
            Side-by-side comparison with differences highlighted
        """
        if not self.repository:
            return {"error": "Repository not configured"}

        try:
            # Get both decisions
            stored1 = await self.repository.find_by_id_async(decision_id_1)
            stored2 = await self.repository.find_by_id_async(decision_id_2)

            if not stored1:
                return {"error": f"Decision not found: {decision_id_1}"}
            if not stored2:
                return {"error": f"Decision not found: {decision_id_2}"}

            d1 = stored1.decision
            d2 = stored2.decision

            # Compare key fields
            comparison = {
                "decision_1": {
                    "decision_id": d1.decision_id,
                    "decision_code": d1.decision_code,
                    "domain_id": d1.domain_id.value if hasattr(d1.domain_id, 'value') else str(d1.domain_id),
                    "aspect_id": d1.aspect_id.value if hasattr(d1.aspect_id, 'value') else str(d1.aspect_id),
                    "statement": d1.statement,
                    "rationale": d1.rationale,
                    "scope": d1.scope.value if hasattr(d1.scope, 'value') else str(d1.scope) if d1.scope else None,
                    "blast_radius": d1.blast_radius.value if hasattr(d1.blast_radius, 'value') else str(d1.blast_radius) if d1.blast_radius else None,
                    "constraints_count": len(d1.constraints or []),
                    "tags": d1.tags or [],
                    "created_at": d1.created_at.isoformat() if d1.created_at else None,
                },
                "decision_2": {
                    "decision_id": d2.decision_id,
                    "decision_code": d2.decision_code,
                    "domain_id": d2.domain_id.value if hasattr(d2.domain_id, 'value') else str(d2.domain_id),
                    "aspect_id": d2.aspect_id.value if hasattr(d2.aspect_id, 'value') else str(d2.aspect_id),
                    "statement": d2.statement,
                    "rationale": d2.rationale,
                    "scope": d2.scope.value if hasattr(d2.scope, 'value') else str(d2.scope) if d2.scope else None,
                    "blast_radius": d2.blast_radius.value if hasattr(d2.blast_radius, 'value') else str(d2.blast_radius) if d2.blast_radius else None,
                    "constraints_count": len(d2.constraints or []),
                    "tags": d2.tags or [],
                    "created_at": d2.created_at.isoformat() if d2.created_at else None,
                },
                "differences": [],
                "relationship": None,
            }

            # Find differences
            if d1.domain_id != d2.domain_id:
                comparison["differences"].append(f"domain_id: {comparison['decision_1']['domain_id']} vs {comparison['decision_2']['domain_id']}")
            if d1.aspect_id != d2.aspect_id:
                comparison["differences"].append(f"aspect_id: {comparison['decision_1']['aspect_id']} vs {comparison['decision_2']['aspect_id']}")
            if d1.scope != d2.scope:
                comparison["differences"].append(f"scope: {comparison['decision_1']['scope']} vs {comparison['decision_2']['scope']}")
            if d1.blast_radius != d2.blast_radius:
                comparison["differences"].append(f"blast_radius: {comparison['decision_1']['blast_radius']} vs {comparison['decision_2']['blast_radius']}")
            if d1.statement != d2.statement:
                comparison["differences"].append("statement: different content")
            if d1.rationale != d2.rationale:
                comparison["differences"].append("rationale: different content")

            # Check relationship
            if d1.supersedes == d2.decision_id:
                comparison["relationship"] = f"{d1.decision_code} supersedes {d2.decision_code}"
            elif d2.supersedes == d1.decision_id:
                comparison["relationship"] = f"{d2.decision_code} supersedes {d1.decision_code}"

            # Calculate similarity (simple word overlap)
            words1 = set(d1.statement.lower().split())
            words2 = set(d2.statement.lower().split())
            overlap = len(words1 & words2)
            union = len(words1 | words2)
            comparison["statement_similarity"] = round(overlap / union if union > 0 else 0, 2)

            return comparison

        except Exception as e:
            logger.error(f"Compare error: {e}")
            return {"error": str(e)}

    # =========================================================================
    # NEW MCP TOOLS (Per MICS-TECHNICAL-DESIGN.md)
    # =========================================================================

    async def list_agents(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all available task agents.

        Per MICS-TECHNICAL-DESIGN.md - mantra_list_agents tool.

        Args:
            category: Filter by category (infrastructure, development, quality, workflow, all)

        Returns:
            List of available agents with their metadata
        """
        agents = []

        # Get all agents from loader
        all_agent_ids = [
            "deployment-agent",
            "database-agent",
            "backend-agent",
            "frontend-agent",
            "security-agent",
        ]

        for agent_id in all_agent_ids:
            agent = self._get_agent(agent_id)
            if agent:
                agent_info = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "version": agent.version,
                    "category": agent.category.value if hasattr(agent.category, 'value') else str(agent.category),
                    "keywords": agent.get_all_keywords()[:10],
                    "domains": agent.get_required_domains(),
                    "aspects": agent.get_all_aspects()[:5],
                }

                # Filter by category if specified
                if category and category != "all":
                    category_mapping = {
                        "infrastructure": ["deployment", "infra", "devops"],
                        "development": ["backend", "frontend", "development"],
                        "quality": ["security", "testing", "review"],
                        "workflow": ["deployment", "release"],
                    }
                    agent_cat = agent_info["category"].lower()
                    matching_cats = category_mapping.get(category, [])
                    if not any(c in agent_cat for c in matching_cats):
                        continue

                agents.append(agent_info)

        # Also include built-in agents
        for aid, agent in self._builtin_agents.items():
            if aid not in all_agent_ids:
                agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "version": agent.version,
                    "category": agent.category.value if hasattr(agent.category, 'value') else str(agent.category),
                    "keywords": agent.get_all_keywords()[:10],
                })

        return {
            "agents": agents,
            "total": len(agents),
            "category_filter": category or "all",
        }

    async def get_checklist_for_task(
        self,
        task_type: str,
        target: Optional[str] = None,
        phase: str = "all"  # "pre_deploy" | "deploy" | "post_deploy" | "all"
    ) -> Dict[str, Any]:
        """
        Get the checklist for a specific task type.

        Per MICS-TECHNICAL-DESIGN.md - mantra_get_checklist tool.

        Args:
            task_type: Type of task (deployment, database-migration, backend, frontend, security)
            target: Optional target system (backend, frontend, etc.)
            phase: Which phase to get (pre_deploy, deploy, post_deploy, all)

        Returns:
            Step-by-step checklist with commands
        """
        # Map task_type to agent_id
        task_to_agent = {
            "deployment": "deployment-agent",
            "deploy": "deployment-agent",
            "release": "deployment-agent",
            "database": "database-agent",
            "migration": "database-agent",
            "database-migration": "database-agent",
            "backend": "backend-agent",
            "api": "backend-agent",
            "frontend": "frontend-agent",
            "ui": "frontend-agent",
            "security": "security-agent",
            "auth": "security-agent",
        }

        agent_id = task_to_agent.get(task_type.lower(), "backend-agent")
        agent = self._get_agent(agent_id)

        if not agent:
            return {
                "error": f"No agent found for task type: {task_type}",
                "available_types": list(task_to_agent.keys()),
            }

        # Get checklist from agent
        all_checklists = {
            "pre_deploy": [],
            "deploy": [],
            "post_deploy": [],
        }

        if hasattr(agent, 'checklist') and agent.checklist:
            # Note: AgentChecklist uses pre/main/post as field names with pre_deploy/deploy/post_deploy as aliases
            if agent.checklist.pre:
                all_checklists["pre_deploy"] = [
                    {
                        "id": item.id,
                        "step": item.step,
                        "command": item.command,
                        "blocking": item.blocking,
                    }
                    for item in agent.checklist.pre
                ]
            if agent.checklist.main:
                all_checklists["deploy"] = [
                    {
                        "id": item.id,
                        "step": item.step,
                        "command": item.command,
                        "blocking": item.blocking,
                    }
                    for item in agent.checklist.main
                ]
            if agent.checklist.post:
                all_checklists["post_deploy"] = [
                    {
                        "id": item.id,
                        "step": item.step,
                        "command": item.command,
                        "blocking": item.blocking,
                    }
                    for item in agent.checklist.post
                ]

        # Filter by phase
        if phase == "all":
            checklist = all_checklists
        elif phase in all_checklists:
            checklist = {phase: all_checklists[phase]}
        else:
            checklist = all_checklists

        # Add critical rules as blocking requirements
        critical_rules = []
        if agent:
            critical_rules = agent.get_blocking_rules()[:5]

        return {
            "task_type": task_type,
            "agent": {
                "id": agent.id,
                "name": agent.name,
            },
            "target": target,
            "phase": phase,
            "checklist": checklist,
            "critical_rules": critical_rules,
            "total_steps": sum(len(items) for items in all_checklists.values()),
        }

    async def validate_actions(
        self,
        task_type: str,
        proposed_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Validate proposed actions against MANTRA decisions.

        Per MICS-TECHNICAL-DESIGN.md - mantra_validate_actions tool.

        Args:
            task_type: Type of task (DEPLOYMENT, DEVELOPMENT, DATABASE, etc.)
            proposed_actions: List of actions the AI plans to take

        Returns:
            Validation result with any violations or warnings
        """
        # Get agent for task type
        task_to_agent = {
            "DEPLOYMENT": "deployment-agent",
            "DEVELOPMENT": "backend-agent",
            "DATABASE": "database-agent",
            "FRONTEND": "frontend-agent",
            "SECURITY": "security-agent",
        }

        agent_id = task_to_agent.get(task_type.upper(), "backend-agent")
        agent = self._get_agent(agent_id)

        violations = []
        warnings = []
        valid = True

        if agent:
            # Check against blocking rules (prohibitions)
            blocking_rules = agent.get_blocking_rules()
            warning_rules = agent.get_warning_rules()

            for action in proposed_actions:
                action_lower = action.lower()

                # Check blocking rules
                for rule in blocking_rules:
                    rule_lower = rule.lower()

                    # Simple keyword matching for violation detection
                    # "NEVER deploy without tests" -> if "deploy" in action and "test" not mentioned
                    if "never" in rule_lower:
                        # Extract the prohibited action pattern
                        prohibited_patterns = self._extract_prohibited_patterns(rule_lower)
                        for pattern in prohibited_patterns:
                            if pattern in action_lower:
                                violations.append({
                                    "action": action,
                                    "rule": rule,
                                    "severity": "BLOCKING",
                                    "message": f"Action may violate rule: {rule}",
                                })
                                valid = False

                # Check warning rules
                for rule in warning_rules:
                    rule_lower = rule.lower()
                    if "always" in rule_lower:
                        required_patterns = self._extract_required_patterns(rule_lower)
                        for pattern in required_patterns:
                            if pattern not in action_lower and not any(pattern in a.lower() for a in proposed_actions):
                                warnings.append({
                                    "action": action,
                                    "rule": rule,
                                    "severity": "WARNING",
                                    "message": f"Consider: {rule}",
                                })

        # Also check against decisions if repository available
        if self.repository:
            decisions = await self._retrieve_decisions(agent)
            for d in decisions[:5]:  # Check top 5 relevant decisions
                for c in d.get("constraints", []):
                    if c.get("type") == "PROHIBITION":
                        for action in proposed_actions:
                            if self._action_might_violate(action, c.get("statement", "")):
                                violations.append({
                                    "action": action,
                                    "decision": d.get("decision_code"),
                                    "constraint": c.get("statement"),
                                    "severity": "BLOCKING",
                                })
                                valid = False

        return {
            "valid": valid,
            "task_type": task_type,
            "actions_checked": len(proposed_actions),
            "violations": violations,
            "warnings": warnings,
            "suggestions": self._generate_suggestions(violations, warnings) if not valid else [],
        }

    def _extract_prohibited_patterns(self, rule: str) -> List[str]:
        """Extract prohibited action patterns from a rule."""
        patterns = []
        # "NEVER deploy without tests" -> ["deploy without test"]
        # "NEVER skip health checks" -> ["skip health", "no health"]

        keywords = ["deploy", "skip", "delete", "drop", "remove", "force", "direct"]
        for kw in keywords:
            if kw in rule:
                patterns.append(kw)

        return patterns

    def _extract_required_patterns(self, rule: str) -> List[str]:
        """Extract required action patterns from a rule."""
        patterns = []
        # "ALWAYS have rollback plan" -> ["rollback"]
        # "ALWAYS run tests" -> ["test"]

        keywords = ["rollback", "test", "backup", "verify", "check", "confirm"]
        for kw in keywords:
            if kw in rule:
                patterns.append(kw)

        return patterns

    def _action_might_violate(self, action: str, constraint: str) -> bool:
        """Check if an action might violate a constraint."""
        action_lower = action.lower()
        constraint_lower = constraint.lower()

        # Simple heuristic: look for contradicting patterns
        danger_words_in_constraint = ["never", "must not", "cannot", "prohibited"]
        action_words_in_constraint = ["deploy", "delete", "modify", "change", "update"]

        for danger in danger_words_in_constraint:
            if danger in constraint_lower:
                for action_word in action_words_in_constraint:
                    if action_word in constraint_lower and action_word in action_lower:
                        return True

        return False

    def _generate_suggestions(self, violations: List[Dict], warnings: List[Dict]) -> List[str]:
        """Generate suggestions to fix violations."""
        suggestions = []

        if violations:
            suggestions.append("Review and address all BLOCKING violations before proceeding")

        if any("test" in v.get("rule", "").lower() for v in violations):
            suggestions.append("Run tests before deployment: `pytest` or `bun test`")

        if any("rollback" in w.get("rule", "").lower() for w in warnings):
            suggestions.append("Create a rollback plan before making changes")

        if any("backup" in v.get("rule", "").lower() or v.get("constraint", "").lower() for v in violations):
            suggestions.append("Create a backup before destructive operations")

        return suggestions

    async def get_task_context_with_budget(
        self,
        intent: str,
        target: Optional[str] = None,
        environment: Optional[str] = None,
        code_context: Optional[str] = None,
        token_budget: int = 4000,
        platform: str = "claude-code"
    ) -> Dict[str, Any]:
        """
        Get intelligent task context with proper token budget management.

        This is an enhanced version of get_task_context that uses the
        TokenBudgetManager for proper tiered content allocation and
        position optimization to avoid "lost in the middle" problem.

        Token Budget Tiers:
        - TIER 1 (CRITICAL): Agent identity, Layer 0, PROHIBITIONS -> START
        - TIER 2 (IMPORTANT): Decisions, Requirements, Checklist -> NEAR_START
        - TIER 3 (SUPPLEMENTARY): Codebase context, Hints -> END
        - TIER 4 (REFERENCE): On-demand details

        Args:
            intent: What the user wants to do
            target: What is being worked on
            environment: Target environment
            code_context: Optional code snippet
            token_budget: Max tokens for context
            platform: Target platform

        Returns:
            Position-optimized context with token budget metadata
        """
        import time
        start_time = time.time()

        try:
            from ..context.token_budget import (
                TokenBudgetManager,
                TokenBudgetConfig,
                TokenTier,
                PriorityLevel,
                assign_priority,
            )

            # Initialize budget manager
            config = TokenBudgetConfig(total_budget=token_budget)
            budget_manager = TokenBudgetManager(config)

            # Stage 1 & 2: Intent Recognition + Agent Loading
            agent, confidence = self._match_intent(intent, target)
            if not agent:
                agent = self._get_agent("backend-agent")
                confidence = 0.5

            # TIER 1 (CRITICAL) - Position: START
            # Agent identity (P3)
            identity = agent.prompt.identity if agent and agent.prompt else "You are a task agent."
            budget_manager.add_critical(
                f"# {agent.name if agent else 'Task Agent'}\n\n{identity}",
                priority=PriorityLevel.P3_AGENT_PROMPTS.value,
                source="agent_identity"
            )

            # Blocking rules / Prohibitions (P1-P2)
            blocking_rules = agent.get_blocking_rules() if agent else []
            if blocking_rules:
                prohibitions_text = "## BLOCKING RULES (MUST FOLLOW)\n" + "\n".join(
                    f"- ❌ {rule}" for rule in blocking_rules[:7]
                )
                budget_manager.add_critical(
                    prohibitions_text,
                    priority=PriorityLevel.P1_LAYER_0.value,
                    source="blocking_rules"
                )

            # TIER 2 (IMPORTANT) - Position: NEAR_START
            # Stage 3: Decision Retrieval
            decisions = await self._retrieve_decisions(agent)

            if decisions:
                decisions_text = "## Relevant Decisions\n"
                for d in decisions[:5]:
                    decisions_text += f"\n### {d['decision_code']}\n{d['statement'][:150]}\n"
                budget_manager.add_important(
                    decisions_text,
                    priority=PriorityLevel.P2_LAYER_1.value,
                    source="decisions"
                )

            # Stage 4: Constraint Extraction
            constraints = self._extract_constraints(agent, decisions)
            if constraints.get("requirements"):
                req_text = "## Requirements\n" + "\n".join(
                    f"- ✓ {r}" for r in constraints["requirements"][:5]
                )
                budget_manager.add_important(
                    req_text,
                    priority=PriorityLevel.P2_LAYER_1.value,
                    source="requirements"
                )

            # Checklist (P3)
            checklist = self._get_checklist(agent)
            if checklist:
                checklist_text = "## Checklist\n" + "\n".join(
                    f"{i+1}. [ ] {item['step']}" + (f" (`{item.get('command')}`)" if item.get('command') else '')
                    for i, item in enumerate(checklist[:10])
                )
                budget_manager.add_important(
                    checklist_text,
                    priority=PriorityLevel.P3_AGENT_PROMPTS.value,
                    source="checklist"
                )

            # TIER 3 (SUPPLEMENTARY) - Position: END
            # Task context
            task_text = f"""## Current Task
- Intent: {intent}
- Target: {target or 'not specified'}
- Environment: {environment or 'not specified'}
"""
            budget_manager.add_supplementary(
                task_text,
                priority=PriorityLevel.P4_PLATFORM.value,
                source="task_context"
            )

            # Platform hints
            hints = self._get_platform_hints(agent, platform)
            if hints.get("tool_suggestions"):
                hints_text = "## Tool Suggestions\n" + "\n".join(
                    f"- {h}" for h in hints["tool_suggestions"][:3]
                )
                budget_manager.add_supplementary(
                    hints_text,
                    priority=PriorityLevel.P5_CODEBASE.value,
                    source="hints"
                )

            # Stage 5: Codebase Context
            if code_context:
                budget_manager.add_supplementary(
                    f"## Code Context\n```\n{code_context[:300]}\n```",
                    priority=PriorityLevel.P5_CODEBASE.value,
                    source="code_context"
                )

            # TIER 4 (REFERENCE) - On-demand
            # Add full decisions as reference items
            for d in decisions[5:10]:  # Additional decisions for on-demand
                budget_manager.add_reference(d)

            # Assemble with position optimization
            assembled = budget_manager.assemble()
            assembly_time_ms = int((time.time() - start_time) * 1000)

            return {
                "task_context": {
                    "agent": {
                        "id": agent.id if agent else "backend-agent",
                        "name": agent.name if agent else "Backend Agent",
                        "version": agent.version if agent else "1.0.0",
                        "confidence": confidence,
                        "category": agent.category.value if agent and hasattr(agent.category, 'value') else "general",
                    },
                    "prompt": assembled.get_full_context(),
                    "positioned_sections": {
                        "start": assembled.start_content,
                        "near_start": assembled.near_start_content,
                        "end": assembled.end_content,
                    },
                    "decisions": decisions[:10],
                    "constraints": constraints,
                    "checklist": checklist,
                },
                "meta": {
                    "total_tokens": assembled.total_tokens,
                    "token_budget": token_budget,
                    "tier_usage": assembled.tier_usage,
                    "decisions_count": len(decisions),
                    "assembly_time_ms": assembly_time_ms,
                    "position_optimized": True,
                    "reference_items_available": len(assembled.reference_items),
                },
                "budget_summary": budget_manager.get_usage_summary(),
                "hints": hints,
            }

        except ImportError as e:
            logger.warning(f"Token budget module not available: {e}")
            # Fallback to regular get_task_context
            return await self.get_task_context(
                intent=intent,
                target=target,
                environment=environment,
                code_context=code_context,
                token_budget=token_budget,
                platform=platform
            )
        except Exception as e:
            logger.error(f"get_task_context_with_budget error: {e}")
            return {"error": str(e)}
