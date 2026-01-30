"""
MANTRA-INFERENCE-001: Auto-Inference Functions for Schema v3

This module provides functions to automatically populate v3 fields
from existing decision content. Enables seamless migration and
reduces manual data entry.

DESIGN PRINCIPLES:
1. All inference is optional - fields can still be manually set
2. Inference uses existing content (statement, rationale, tags, etc.)
3. Conservative inference - prefer under-inference to over-inference
4. Transparent - inference sources can be traced

INFERENCE CATEGORIES:
1. Knowledge Consumption - target_roles, audience_level, reading_time
2. Applicability Context - applies_when based on keywords
3. Search Metadata - semantic expansion, intent questions
4. RAG Optimization - context_summary, citation_format
5. Stability - based on version and change_type
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime, date
import re

from ..domain.schema_v3 import (
    # Enums
    DomainId, AspectId, Scope, BlastRadius, AudienceLevel, StabilityStatus,
    ImplementationStatusType, RiskLevel,
    # Models
    DecisionV3, KnowledgeConsumption, ApplicabilityContext, ContextTrigger,
    EnhancedSearchMetadata, SemanticExpansion, IntentBasedQuestions,
    EnhancedLLMOptimization, RAGOptimization, StabilityMetadata,
    ImplementationStatus, PersistedImpactAnalysis, UsageAnalytics,
)


# ============================================================================
# SECTION 1: Keyword Databases for Inference
# ============================================================================

# Role inference keywords
ROLE_KEYWORDS = {
    "frontend_dev": ["react", "vue", "angular", "frontend", "ui", "component", "jsx", "tsx", "css", "tailwind", "browser"],
    "backend_dev": ["api", "endpoint", "database", "server", "fastapi", "django", "express", "rest", "graphql", "microservice"],
    "devops": ["docker", "kubernetes", "k8s", "ci/cd", "cicd", "pipeline", "deployment", "terraform", "ansible", "infrastructure"],
    "architect": ["architecture", "system design", "scalability", "pattern", "bounded context", "domain", "integration"],
    "tech_lead": ["team", "process", "standard", "convention", "review", "governance", "organization"],
    "data_engineer": ["data", "etl", "pipeline", "warehouse", "analytics", "spark", "kafka"],
    "security_engineer": ["security", "authentication", "authorization", "encryption", "vulnerability", "audit"],
    "qa_engineer": ["test", "testing", "qa", "quality", "automation", "e2e", "unit test"],
}

# Semantic expansion database
CONCEPT_EXPANSIONS = {
    "microservices": {
        "parent": ["software architecture", "distributed systems"],
        "related": ["service mesh", "API gateway", "container orchestration"],
        "child": ["service discovery", "circuit breaker", "load balancing"],
    },
    "feature-based": {
        "parent": ["code organization", "frontend architecture"],
        "related": ["module boundary", "lazy loading", "code splitting"],
        "child": ["feature folder", "barrel exports", "index files"],
        "synonyms": ["feature-sliced", "feature-driven", "modular architecture"],
    },
    "authentication": {
        "parent": ["security", "identity management"],
        "related": ["authorization", "session management", "SSO"],
        "child": ["JWT", "OAuth", "SAML", "API keys"],
    },
    "database": {
        "parent": ["data management", "persistence"],
        "related": ["ORM", "migrations", "indexing"],
        "child": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
    },
    "api": {
        "parent": ["integration", "interfaces"],
        "related": ["REST", "GraphQL", "gRPC", "WebSocket"],
        "child": ["endpoint", "versioning", "rate limiting"],
    },
    "testing": {
        "parent": ["quality assurance", "software quality"],
        "related": ["CI/CD", "code coverage", "test automation"],
        "child": ["unit test", "integration test", "e2e test"],
    },
    "deployment": {
        "parent": ["software delivery", "DevOps"],
        "related": ["CI/CD", "infrastructure", "monitoring"],
        "child": ["container", "kubernetes", "docker", "helm"],
    },
}

# Tech stack to file pattern mapping
TECH_FILE_PATTERNS = {
    "react": ["*.tsx", "*.jsx", "src/components/**", "src/features/**"],
    "typescript": ["*.ts", "*.tsx", "tsconfig.json"],
    "python": ["*.py", "**/__init__.py", "requirements.txt"],
    "fastapi": ["**/api/**/*.py", "**/routes/**/*.py", "**/endpoints/**/*.py"],
    "postgresql": ["**/migrations/**", "**/*_repository.py", "**/models/**"],
    "docker": ["Dockerfile", "docker-compose*.yml", ".dockerignore"],
    "kubernetes": ["*.yaml", "*.yml", "**/k8s/**", "**/helm/**"],
}


# ============================================================================
# SECTION 2: Knowledge Consumption Inference
# ============================================================================

def infer_target_roles(
    tags: List[str],
    tech_stack: List[str],
    statement: str,
    rationale: str,
    blast_radius: BlastRadius,
) -> List[str]:
    """
    Infer target roles from tags, tech_stack, and content.

    Args:
        tags: Decision tags (FE, BE, etc.)
        tech_stack: Technologies used
        statement: Decision statement
        rationale: Decision rationale
        blast_radius: Impact level

    Returns:
        List of inferred role identifiers
    """
    roles: Set[str] = set()
    content = f"{statement} {rationale}".lower()

    # Infer from tags
    tag_role_map = {
        "FE": "frontend_dev",
        "BE": "backend_dev",
        "DB": "backend_dev",
        "INFRA": "devops",
        "CICD": "devops",
        "SECURITY": "security_engineer",
        "TESTING": "qa_engineer",
        "DATA": "data_engineer",
        "ARCH": "architect",
    }
    for tag in tags:
        if tag.upper() in tag_role_map:
            roles.add(tag_role_map[tag.upper()])

    # Infer from tech_stack
    tech_role_map = {
        "react": "frontend_dev",
        "vue": "frontend_dev",
        "angular": "frontend_dev",
        "typescript": "frontend_dev",
        "fastapi": "backend_dev",
        "django": "backend_dev",
        "express": "backend_dev",
        "postgresql": "backend_dev",
        "docker": "devops",
        "kubernetes": "devops",
        "terraform": "devops",
    }
    for tech in tech_stack:
        tech_lower = tech.lower()
        for key, role in tech_role_map.items():
            if key in tech_lower:
                roles.add(role)

    # Infer from content keywords
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in content for kw in keywords):
            roles.add(role)

    # High impact decisions should include architect/tech_lead
    if blast_radius in [BlastRadius.CRITICAL, BlastRadius.HIGH]:
        roles.add("architect")
        roles.add("tech_lead")

    return list(roles) if roles else ["developer"]


def infer_audience_level(
    statement: str,
    rationale: str,
    detailed_content: Optional[str] = None,
) -> AudienceLevel:
    """
    Infer audience level from content complexity.

    Uses simple heuristics:
    - Short, simple words = BEGINNER
    - Technical jargon = INTERMEDIATE/ADVANCED
    - Many acronyms = ADVANCED/EXPERT
    """
    content = f"{statement} {rationale} {detailed_content or ''}"

    # Count technical indicators
    acronym_pattern = r'\b[A-Z]{2,}\b'
    acronym_count = len(re.findall(acronym_pattern, content))

    # Count average word length (longer = more technical)
    words = content.split()
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)

    # Count technical keywords
    technical_keywords = [
        "architecture", "pattern", "implementation", "interface",
        "abstraction", "encapsulation", "polymorphism", "inheritance",
        "asynchronous", "concurrent", "distributed", "scalable",
        "idempotent", "immutable", "deterministic",
    ]
    tech_count = sum(1 for kw in technical_keywords if kw in content.lower())

    # Score calculation
    score = 0
    score += min(acronym_count, 10)  # Max 10 points for acronyms
    score += int(avg_word_length)     # Word length points
    score += tech_count * 2           # 2 points per technical keyword

    # Map score to level
    if score >= 25:
        return AudienceLevel.EXPERT
    elif score >= 15:
        return AudienceLevel.ADVANCED
    elif score >= 8:
        return AudienceLevel.INTERMEDIATE
    else:
        return AudienceLevel.BEGINNER


def infer_reading_time(
    statement: str,
    rationale: str,
    detailed_content: Optional[str] = None,
    sections_count: int = 0,
) -> int:
    """
    Estimate reading time in minutes.

    Assumes ~200 words per minute reading speed,
    with overhead for technical content.
    """
    content = f"{statement} {rationale} {detailed_content or ''}"
    word_count = len(content.split())

    # Base reading time
    base_time = word_count / 200

    # Add overhead for sections (assume 30 sec per section for context switching)
    section_overhead = sections_count * 0.5

    # Add overhead for technical content (20% slower)
    technical_overhead = base_time * 0.2

    total_minutes = base_time + section_overhead + technical_overhead

    return max(1, int(round(total_minutes)))


def infer_prerequisite_decisions(relations: List[dict]) -> List[str]:
    """
    Infer prerequisite decisions from DEPENDS_ON relations.
    """
    return [
        r.get("target_id")
        for r in relations
        if r.get("type") == "depends_on"
    ]


def infer_knowledge_consumption(decision: DecisionV3) -> KnowledgeConsumption:
    """
    Auto-infer complete KnowledgeConsumption from decision content.
    """
    target_roles = infer_target_roles(
        tags=decision.tags,
        tech_stack=decision.tech_stack,
        statement=decision.statement,
        rationale=decision.rationale,
        blast_radius=decision.blast_radius,
    )

    audience_level = infer_audience_level(
        statement=decision.statement,
        rationale=decision.rationale,
        detailed_content=decision.detailed_content,
    )

    reading_time = infer_reading_time(
        statement=decision.statement,
        rationale=decision.rationale,
        detailed_content=decision.detailed_content,
        sections_count=len(decision.sections),
    )

    prerequisite_decisions = infer_prerequisite_decisions(
        [r.model_dump() for r in decision.relations]
    )

    return KnowledgeConsumption(
        target_roles=target_roles,
        audience_level=audience_level,
        reading_time_minutes=reading_time,
        prerequisite_decisions=prerequisite_decisions,
        learning_objectives=[],  # Cannot auto-infer meaningfully
        prerequisites_knowledge=[],  # Cannot auto-infer meaningfully
    )


# ============================================================================
# SECTION 3: Applicability Context Inference
# ============================================================================

def infer_context_triggers(
    tags: List[str],
    tech_stack: List[str],
    statement: str,
) -> List[ContextTrigger]:
    """
    Infer context triggers from tags and tech_stack.
    """
    triggers = []
    idx = 1

    # Generate triggers from tech_stack
    for tech in tech_stack:
        tech_lower = tech.lower()
        if tech_lower in TECH_FILE_PATTERNS:
            patterns = TECH_FILE_PATTERNS[tech_lower]
            triggers.append(ContextTrigger(
                trigger_id=f"CTX-{idx:03d}",
                condition=f"Working with {tech} code",
                keywords=[tech_lower],
                file_patterns=patterns,
            ))
            idx += 1

    # Generate triggers from statement keywords
    statement_lower = statement.lower()
    trigger_conditions = [
        ("creating", "component", ["component", "create"], ["src/components/**"]),
        ("api", "endpoint", ["api", "endpoint", "route"], ["**/api/**", "**/routes/**"]),
        ("database", "migration", ["database", "migration", "schema"], ["**/migrations/**"]),
        ("test", "writing", ["test", "spec"], ["**/*.test.*", "**/*.spec.*"]),
    ]

    for keyword1, keyword2, keywords, patterns in trigger_conditions:
        if keyword1 in statement_lower or keyword2 in statement_lower:
            triggers.append(ContextTrigger(
                trigger_id=f"CTX-{idx:03d}",
                condition=f"When {keyword1} {keyword2}",
                keywords=keywords,
                file_patterns=patterns,
            ))
            idx += 1

    return triggers


def infer_exclusions(
    tags: List[str],
    statement: str,
) -> List[str]:
    """
    Infer exclusions (does_not_apply_when) from context.
    """
    exclusions = []

    # Common exclusions
    if "FE" in tags or "frontend" in statement.lower():
        exclusions.extend([
            "Backend-only services",
            "CLI tools without UI",
        ])

    if "BE" in tags or "backend" in statement.lower():
        exclusions.extend([
            "Static frontend-only projects",
            "Design assets",
        ])

    # Always exclude tests and generated code
    if not any(t in tags for t in ["TESTING", "TEST"]):
        exclusions.append("Test files and mocks")

    exclusions.append("Auto-generated code")
    exclusions.append("Third-party library code")

    return exclusions


def infer_applicability_context(decision: DecisionV3) -> ApplicabilityContext:
    """
    Auto-infer ApplicabilityContext from decision content.
    """
    triggers = infer_context_triggers(
        tags=decision.tags,
        tech_stack=decision.tech_stack,
        statement=decision.statement,
    )

    exclusions = infer_exclusions(
        tags=decision.tags,
        statement=decision.statement,
    )

    # Auto-detect if we have file patterns
    auto_detect = any(t.file_patterns for t in triggers)

    return ApplicabilityContext(
        applies_when=triggers,
        does_not_apply_when=exclusions,
        auto_detect=auto_detect,
    )


# ============================================================================
# SECTION 4: Search Metadata Inference
# ============================================================================

def infer_semantic_expansion(
    statement: str,
    rationale: str,
    tags: List[str],
    tech_stack: List[str],
) -> SemanticExpansion:
    """
    Infer semantic expansion from content and tech_stack.
    """
    content = f"{statement} {rationale}".lower()
    parent_concepts: Set[str] = set()
    related_concepts: Set[str] = set()
    child_concepts: Set[str] = set()
    synonyms: Set[str] = set()

    # Check for known concept expansions
    for concept, expansion in CONCEPT_EXPANSIONS.items():
        if concept in content or any(concept in t.lower() for t in tech_stack):
            parent_concepts.update(expansion.get("parent", []))
            related_concepts.update(expansion.get("related", []))
            child_concepts.update(expansion.get("child", []))
            synonyms.update(expansion.get("synonyms", []))

    # Add tech_stack as related concepts
    related_concepts.update(t.lower() for t in tech_stack)

    return SemanticExpansion(
        parent_concepts=list(parent_concepts),
        related_concepts=list(related_concepts),
        child_concepts=list(child_concepts),
        synonyms=list(synonyms),
    )


def infer_intent_questions(
    statement: str,
    rationale: str,
    decision_code: Optional[str] = None,
) -> IntentBasedQuestions:
    """
    Generate intent-based questions from statement and rationale.
    """
    # Extract key noun phrases (simplified)
    statement_nouns = re.findall(r'\b([A-Za-z]+(?:-[A-Za-z]+)*)\b', statement)
    key_terms = [n for n in statement_nouns if len(n) > 4][:5]

    how_questions = []
    why_questions = []
    what_questions = []
    when_questions = []

    for term in key_terms:
        how_questions.append(f"How do I implement {term}?")
        how_questions.append(f"How should I use {term}?")
        why_questions.append(f"Why do we use {term}?")
        what_questions.append(f"What is {term}?")
        when_questions.append(f"When should I apply {term}?")

    # Add statement-based questions
    if decision_code:
        what_questions.insert(0, f"What does {decision_code} say?")

    return IntentBasedQuestions(
        how_questions=how_questions[:5],
        why_questions=why_questions[:3],
        what_questions=what_questions[:3],
        when_questions=when_questions[:3],
        negative_questions=[],  # Cannot auto-infer meaningfully
    )


def infer_negative_keywords(
    tags: List[str],
    scope: Scope,
) -> List[str]:
    """
    Infer negative keywords (what this decision is NOT about).
    """
    negatives = []

    # Scope-based negatives
    if scope == Scope.APPLICATION:
        negatives.extend(["organization-wide", "company policy", "global standard"])
    elif scope == Scope.DOMAIN:
        negatives.extend(["specific application", "single project"])

    # Tag-based negatives
    if "FE" in tags:
        negatives.extend(["backend", "server-side", "database"])
    if "BE" in tags:
        negatives.extend(["frontend", "UI", "browser", "CSS"])
    if "DB" in tags:
        negatives.extend(["frontend", "UI component"])

    return negatives


def infer_enhanced_search_metadata(decision: DecisionV3) -> EnhancedSearchMetadata:
    """
    Auto-infer complete EnhancedSearchMetadata from decision content.
    """
    semantic_expansion = infer_semantic_expansion(
        statement=decision.statement,
        rationale=decision.rationale,
        tags=decision.tags,
        tech_stack=decision.tech_stack,
    )

    questions = infer_intent_questions(
        statement=decision.statement,
        rationale=decision.rationale,
        decision_code=decision.decision_code,
    )

    negative_keywords = infer_negative_keywords(
        tags=decision.tags,
        scope=decision.scope,
    )

    # Extract keywords from statement
    search_keywords = list(set(
        word.lower()
        for word in re.findall(r'\b[A-Za-z]{4,}\b', decision.statement)
        if word.lower() not in ["must", "should", "that", "this", "with", "from"]
    ))[:10]

    return EnhancedSearchMetadata(
        aliases=[],  # Cannot auto-infer
        search_keywords=search_keywords,
        questions=questions,
        semantic_expansion=semantic_expansion,
        negative_keywords=negative_keywords,
        retrieval_boost=1.0,  # Default
        question_variants=[],  # Deprecated
    )


# ============================================================================
# SECTION 5: LLM/RAG Optimization Inference
# ============================================================================

def infer_context_summary(
    statement: str,
    rationale: str,
    constraints: List[Any],
) -> str:
    """
    Generate context summary (~100-150 words) for RAG.
    """
    # Combine statement and rationale essence
    parts = [statement]

    # Add first sentence of rationale
    rationale_sentences = rationale.split('.')
    if rationale_sentences:
        parts.append(rationale_sentences[0].strip() + '.')

    # Add first constraint if exists
    if constraints and len(constraints) > 0:
        parts.append(f"Key constraint: {constraints[0].statement}")

    summary = " ".join(parts)

    # Truncate to ~150 words
    words = summary.split()
    if len(words) > 150:
        summary = " ".join(words[:150]) + "..."

    return summary


def infer_citation_format(
    decision_code: Optional[str],
    decision_id: str,
    statement: str,
) -> str:
    """
    Generate citation format for RAG output.
    """
    # Extract first noun phrase as title
    words = statement.split()[:5]
    title = " ".join(words)
    if not title.endswith("..."):
        title += "..."

    code = decision_code or decision_id[:8]
    return f"[{code}] {title}"


def infer_embedding_text(decision: DecisionV3) -> str:
    """
    Generate optimized embedding text with structure markers.
    """
    parts = [
        f"[DECISION] {decision.statement}",
        f"[RATIONALE] {decision.rationale}",
    ]

    if decision.invariants:
        parts.append(f"[INVARIANTS] {' '.join(decision.invariants)}")

    if decision.constraints:
        constraint_text = " ".join(c.statement for c in decision.constraints)
        parts.append(f"[CONSTRAINTS] {constraint_text}")

    if decision.tags:
        parts.append(f"[TAGS] {' '.join(decision.tags)}")

    if decision.tech_stack:
        parts.append(f"[TECH] {' '.join(decision.tech_stack)}")

    return " ".join(parts)


def infer_rag_optimization(decision: DecisionV3) -> RAGOptimization:
    """
    Auto-infer RAGOptimization from decision content.
    """
    context_summary = infer_context_summary(
        statement=decision.statement,
        rationale=decision.rationale,
        constraints=decision.constraints,
    )

    citation_format = infer_citation_format(
        decision_code=decision.decision_code,
        decision_id=decision.decision_id,
        statement=decision.statement,
    )

    return RAGOptimization(
        context_summary=context_summary,
        standalone_answer=decision.statement,  # Statement as standalone answer
        citation_format=citation_format,
        semantic_boundaries=[],  # Cannot auto-infer
        recommended_chunk_size=512,
        separate_embeddings=False,
    )


def estimate_token_count(text: str) -> int:
    """
    Estimate token count (rough approximation).

    Uses ~0.75 tokens per character heuristic for English text.
    """
    return int(len(text) * 0.75)


def infer_enhanced_llm_optimization(decision: DecisionV3) -> EnhancedLLMOptimization:
    """
    Auto-infer complete EnhancedLLMOptimization from decision content.
    """
    embedding_text = infer_embedding_text(decision)

    # Estimate total tokens
    total_content = decision.statement + decision.rationale
    if decision.detailed_content:
        total_content += decision.detailed_content
    total_token_count = estimate_token_count(total_content)

    # Generate micro summary (~20 words)
    micro_words = decision.statement.split()[:20]
    micro_summary = " ".join(micro_words)
    if len(decision.statement.split()) > 20:
        micro_summary += "..."

    # Extract RAG keywords
    keywords = list(set(
        word.lower()
        for word in re.findall(r'\b[A-Za-z]{3,}\b', decision.statement + " " + decision.rationale)
        if word.lower() not in ["the", "and", "for", "that", "this", "with", "from", "must", "should"]
    ))[:15]

    rag = infer_rag_optimization(decision)

    return EnhancedLLMOptimization(
        embedding_text=embedding_text,
        total_token_count=total_token_count,
        micro_summary=micro_summary,
        prompt_hints=[],  # Cannot auto-infer meaningfully
        keywords_for_rag=keywords,
        embedding_model=None,  # Set when embedding is generated
        embedding_generated_at=None,
        rag=rag,
    )


# ============================================================================
# SECTION 6: Stability Inference
# ============================================================================

def infer_stability_metadata(
    version: str,
    change_type: Optional[str],
    created_at: Optional[datetime],
    supersedes: Optional[str],
) -> StabilityMetadata:
    """
    Infer stability metadata from version and change_type.
    """
    # Parse version
    version_parts = version.split(".")
    major = int(version_parts[0]) if version_parts else 0
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0

    # Determine stability status
    if major == 0:
        if minor < 5:
            status = StabilityStatus.EXPERIMENTAL
        else:
            status = StabilityStatus.BETA
    elif change_type == "DEPRECATION":
        status = StabilityStatus.DEPRECATED
    else:
        status = StabilityStatus.STABLE

    # Calculate maturity score
    maturity = 50  # Base score
    if major >= 1:
        maturity += 20  # v1.0+ is more mature
    if supersedes:
        maturity += 10  # Has evolved from previous decision
    if created_at:
        age_days = (datetime.utcnow() - created_at).days
        if age_days > 90:
            maturity += 10  # Older than 90 days
        if age_days > 365:
            maturity += 10  # Older than a year

    maturity = min(100, maturity)  # Cap at 100

    return StabilityMetadata(
        stability_status=status,
        maturity_score=maturity,
        deprecation_date=None,
        deprecation_reason=None,
        successor_id=None,
        adoption_count=0,
        feedback_score=None,
    )


# ============================================================================
# SECTION 7: Master Inference Function
# ============================================================================

def auto_infer_v3_fields(decision: DecisionV3) -> DecisionV3:
    """
    Auto-infer all v3 fields for a decision.

    This is the master function that populates all inferrable fields
    from existing content. Only populates fields that are not already set.

    Args:
        decision: DecisionV3 instance with core fields populated

    Returns:
        DecisionV3 with v3 fields auto-populated
    """
    updates = {}

    # Infer knowledge_consumption if not set
    if not decision.knowledge_consumption:
        updates["knowledge_consumption"] = infer_knowledge_consumption(decision)

    # Infer applicability if not set
    if not decision.applicability:
        updates["applicability"] = infer_applicability_context(decision)

    # Infer search_metadata if not set
    if not decision.search_metadata:
        updates["search_metadata"] = infer_enhanced_search_metadata(decision)

    # Infer llm_optimization if not set
    if not decision.llm_optimization:
        updates["llm_optimization"] = infer_enhanced_llm_optimization(decision)

    # Infer stability if not set
    if not decision.stability:
        updates["stability"] = infer_stability_metadata(
            version=decision.version,
            change_type=decision.change_type.value if decision.change_type else None,
            created_at=decision.created_at,
            supersedes=decision.supersedes,
        )

    # Infer implementation_status if not set (default to NOT_STARTED)
    if not decision.implementation_status:
        updates["implementation_status"] = ImplementationStatus()

    # Initialize usage_analytics if not set
    if not decision.usage_analytics:
        updates["usage_analytics"] = UsageAnalytics()

    # Create updated decision
    if updates:
        decision_dict = decision.model_dump()
        for key, value in updates.items():
            if isinstance(value, BaseModel):
                decision_dict[key] = value.model_dump()
            else:
                decision_dict[key] = value
        return DecisionV3(**decision_dict)

    return decision


def enrich_decision_for_search(decision: DecisionV3) -> Dict[str, Any]:
    """
    Enrich decision with all search-relevant fields.

    Returns a dictionary optimized for indexing in search systems.
    """
    # Auto-infer if needed
    enriched = auto_infer_v3_fields(decision)

    return {
        "decision_id": enriched.decision_id,
        "decision_code": enriched.decision_code,
        "domain_id": enriched.domain_id.value,
        "aspect_id": enriched.aspect_id.value,

        # Core content for FTS
        "statement": enriched.statement,
        "rationale": enriched.rationale,

        # Classification
        "scope": enriched.scope.value,
        "blast_radius": enriched.blast_radius.value,
        "tags": enriched.tags,
        "tech_stack": enriched.tech_stack,

        # Search optimization
        "aliases": enriched.search_metadata.aliases if enriched.search_metadata else [],
        "search_keywords": enriched.search_metadata.search_keywords if enriched.search_metadata else [],
        "negative_keywords": enriched.search_metadata.negative_keywords if enriched.search_metadata else [],

        # Semantic expansion
        "related_concepts": (
            enriched.search_metadata.semantic_expansion.related_concepts
            if enriched.search_metadata and enriched.search_metadata.semantic_expansion
            else []
        ),
        "parent_concepts": (
            enriched.search_metadata.semantic_expansion.parent_concepts
            if enriched.search_metadata and enriched.search_metadata.semantic_expansion
            else []
        ),

        # Intent questions (flattened for search)
        "questions": (
            (enriched.search_metadata.questions.how_questions or []) +
            (enriched.search_metadata.questions.why_questions or []) +
            (enriched.search_metadata.questions.what_questions or []) +
            (enriched.search_metadata.questions.when_questions or [])
            if enriched.search_metadata and enriched.search_metadata.questions
            else []
        ),

        # LLM/RAG
        "embedding_text": (
            enriched.llm_optimization.embedding_text
            if enriched.llm_optimization
            else enriched.get_embedding_text()
        ),
        "micro_summary": (
            enriched.llm_optimization.micro_summary
            if enriched.llm_optimization
            else None
        ),
        "citation_format": (
            enriched.llm_optimization.rag.citation_format
            if enriched.llm_optimization and enriched.llm_optimization.rag
            else enriched.get_citation()
        ),

        # Knowledge consumption
        "target_roles": (
            enriched.knowledge_consumption.target_roles
            if enriched.knowledge_consumption
            else ["developer"]
        ),
        "audience_level": (
            enriched.knowledge_consumption.audience_level.value
            if enriched.knowledge_consumption and enriched.knowledge_consumption.audience_level
            else "INTERMEDIATE"
        ),

        # Stability
        "stability_status": (
            enriched.stability.stability_status.value
            if enriched.stability
            else "stable"
        ),
        "maturity_score": (
            enriched.stability.maturity_score
            if enriched.stability
            else 50
        ),

        # Boost factor
        "retrieval_boost": (
            enriched.search_metadata.retrieval_boost
            if enriched.search_metadata
            else 1.0
        ),
    }


# ============================================================================
# SECTION 8: Batch Processing
# ============================================================================

def batch_infer_v3_fields(decisions: List[DecisionV3]) -> List[DecisionV3]:
    """
    Batch process multiple decisions for v3 field inference.
    """
    return [auto_infer_v3_fields(d) for d in decisions]


def batch_enrich_for_search(decisions: List[DecisionV3]) -> List[Dict[str, Any]]:
    """
    Batch enrich multiple decisions for search indexing.
    """
    return [enrich_decision_for_search(d) for d in decisions]


# Import BaseModel for type checking
from pydantic import BaseModel
