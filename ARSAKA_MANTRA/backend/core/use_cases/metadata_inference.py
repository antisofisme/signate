"""
Metadata Inference Module for MANTRA Validator

Automatically infers metadata from statement/rationale text:
- tags (FE, BE, DB, INFRA, SECURITY, etc.)
- tech_stack (PostgreSQL, React, Docker, etc.)
- blast_radius (from scope keywords)

This helps with the bootstrap problem: users can't score well without
metadata, but may not know what metadata to add. Auto-inference provides
suggestions based on text analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Any


# =============================================================================
# Keyword Databases for Inference
# =============================================================================

TAG_KEYWORDS: Dict[str, Set[str]] = {
    "FE": {
        "frontend", "ui", "react", "vue", "angular", "css", "component",
        "page", "user interface", "button", "form", "modal", "layout",
        "responsive", "mobile", "desktop", "browser", "dom", "html",
        "client-side", "spa", "single page", "tailwind", "vite"
    },
    "BE": {
        "backend", "api", "server", "endpoint", "service", "fastapi",
        "python", "flask", "django", "express", "node", "server-side",
        "microservice", "controller", "route", "handler", "pydantic"
    },
    "DB": {
        "database", "postgresql", "postgres", "mysql", "mongodb", "redis",
        "query", "table", "schema", "migration", "index", "sql", "nosql",
        "orm", "transaction", "acid", "persistence", "storage", "sqlalchemy"
    },
    "INFRA": {
        "docker", "kubernetes", "k8s", "deployment", "server", "cloud",
        "aws", "gcp", "azure", "infrastructure", "nomad", "consul",
        "terraform", "ansible", "container", "orchestration", "scaling",
        "load balancer", "nginx", "traefik", "minio", "s3"
    },
    "SECURITY": {
        "authentication", "authorization", "jwt", "oauth", "permission",
        "security", "encryption", "ssl", "tls", "https", "password",
        "token", "session", "rbac", "acl", "firewall", "vulnerability"
    },
    "API": {
        "rest", "graphql", "endpoint", "api", "http", "request", "response",
        "json", "openapi", "swagger", "grpc", "webhook", "rate limit",
        "mcp", "model context protocol"
    },
    "CICD": {
        "ci/cd", "pipeline", "github actions", "gitlab", "jenkins",
        "automation", "build", "deploy", "release", "continuous"
    },
    "DEVOPS": {
        "monitoring", "logging", "alerting", "observability", "metrics",
        "prometheus", "grafana", "elk", "tracing", "health check"
    },
    "TESTING": {
        "test", "testing", "unit test", "integration test", "e2e",
        "coverage", "pytest", "jest", "cypress", "mock", "fixture",
        "playwright", "vitest"
    },
    "PERF": {
        "performance", "optimization", "caching", "latency", "throughput",
        "benchmark", "profiling", "bottleneck", "scalability"
    },
    # NEW: Data & Analytics
    "DATA": {
        "data pipeline", "etl", "analytics", "data warehouse", "data lake",
        "pandas", "airflow", "dbt", "data engineering", "data flow",
        "batch processing", "stream processing", "data model"
    },
    # NEW: Architecture
    "ARCH": {
        "architecture", "design pattern", "clean architecture", "hexagonal",
        "domain driven", "ddd", "microservices", "monolith", "modular",
        "boundary", "layer", "coupling", "cohesion", "solid"
    },
}

TECH_KEYWORDS: Dict[str, Set[str]] = {
    # Languages
    "python": {"python", "py", "cpython"},
    "typescript": {"typescript", "ts"},
    "javascript": {"javascript", "js", "ecmascript"},

    # Databases
    "postgresql": {"postgresql", "postgres", "psql"},
    "mysql": {"mysql", "mariadb"},
    "mongodb": {"mongodb", "mongo"},
    "redis": {"redis"},
    "timescaledb": {"timescale", "timescaledb", "time-series"},
    "elasticsearch": {"elasticsearch", "elastic", "opensearch"},
    "qdrant": {"qdrant", "vector database", "vector db"},
    "sqlite": {"sqlite"},

    # Frameworks - Backend
    "fastapi": {"fastapi", "fast api", "starlette"},
    "django": {"django"},
    "flask": {"flask"},
    "express": {"express", "expressjs"},
    "nestjs": {"nestjs", "nest.js"},
    "pydantic": {"pydantic"},
    "sqlalchemy": {"sqlalchemy", "alembic"},

    # Frameworks - Frontend
    "react": {"react", "reactjs", "react.js"},
    "vue": {"vue", "vuejs", "vue.js"},
    "angular": {"angular"},
    "svelte": {"svelte"},
    "nextjs": {"nextjs", "next.js"},
    "vite": {"vite", "vitejs"},
    "tailwind": {"tailwind", "tailwindcss"},
    "zustand": {"zustand"},
    "tanstack": {"tanstack", "react-query", "tanstack query"},

    # Infrastructure
    "docker": {"docker", "dockerfile", "docker-compose"},
    "kubernetes": {"kubernetes", "k8s", "helm"},
    "nomad": {"nomad", "hashicorp nomad"},
    "consul": {"consul", "service mesh", "service discovery"},
    "terraform": {"terraform", "iac", "infrastructure as code"},
    "aws": {"aws", "amazon web services", "ec2", "lambda", "ecs"},
    "gcp": {"gcp", "google cloud"},
    "nginx": {"nginx"},
    "traefik": {"traefik"},

    # Storage
    "s3": {"s3", "minio", "object storage"},

    # Message Queues
    "rabbitmq": {"rabbitmq", "rabbit", "amqp"},
    "kafka": {"kafka"},
    "celery": {"celery", "task queue"},

    # API & Protocols
    "graphql": {"graphql", "apollo"},
    "grpc": {"grpc", "protobuf"},
    "websocket": {"websocket", "socket.io", "real-time"},
    "mcp": {"mcp", "model context protocol"},

    # Data & AI
    "pandas": {"pandas", "dataframe"},
    "airflow": {"airflow", "dag"},
    "langchain": {"langchain", "llm chain"},
    "openai": {"openai", "gpt", "chatgpt"},
    "anthropic": {"anthropic", "claude"},
}

BLAST_RADIUS_KEYWORDS: Dict[str, Set[str]] = {
    "CRITICAL": {
        "all services", "entire system", "organization-wide", "every",
        "platform-wide", "all users", "company-wide", "global"
    },
    "HIGH": {
        "multiple services", "core", "critical", "platform", "foundation",
        "shared", "common", "central", "main"
    },
    "MEDIUM": {
        "service", "module", "domain", "feature", "subsystem", "component"
    },
    "LOW": {
        "single", "local", "isolated", "specific", "minor", "small"
    },
}


# =============================================================================
# Inference Results
# =============================================================================

@dataclass
class InferredMetadata:
    """Result of metadata inference."""
    suggested_tags: List[str]
    suggested_tech_stack: List[str]
    suggested_blast_radius: str

    # Confidence scores (0-1)
    tag_confidence: float
    tech_confidence: float
    blast_radius_confidence: float

    # Details for transparency
    detected_keywords: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for API response."""
        return {
            'suggested_tags': self.suggested_tags,
            'suggested_tech_stack': self.suggested_tech_stack,
            'suggested_blast_radius': self.suggested_blast_radius,
            'confidence': {
                'tags': self.tag_confidence,
                'tech_stack': self.tech_confidence,
                'blast_radius': self.blast_radius_confidence,
            },
            'detected_keywords': self.detected_keywords,
        }


# =============================================================================
# Inference Functions
# =============================================================================

def infer_tags(text: str) -> Tuple[List[str], float, Dict[str, List[str]]]:
    """
    Infer tags from text.

    Returns:
        (tags, confidence, detected_keywords)
    """
    text_lower = text.lower()
    tags = []
    detected = {}

    for tag, keywords in TAG_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            tags.append(tag)
            detected[tag] = found[:3]  # Limit to 3 examples

    # Confidence based on number of tags and keywords found
    if not tags:
        confidence = 0.0
    elif len(tags) <= 2:
        confidence = 0.5 + (len(tags) * 0.1)
    else:
        confidence = min(0.9, 0.6 + (len(tags) * 0.05))

    return tags, confidence, detected


def infer_tech_stack(text: str) -> Tuple[List[str], float, Dict[str, List[str]]]:
    """
    Infer tech_stack from text.

    Returns:
        (tech_list, confidence, detected_keywords)
    """
    text_lower = text.lower()
    tech_list = []
    detected = {}

    for tech, keywords in TECH_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            tech_list.append(tech)
            detected[tech] = found[:2]  # Limit to 2 examples

    # Confidence based on number of technologies found
    if not tech_list:
        confidence = 0.0
    elif len(tech_list) == 1:
        confidence = 0.6
    elif len(tech_list) <= 3:
        confidence = 0.7
    else:
        confidence = 0.8

    return tech_list, confidence, detected


def infer_blast_radius(text: str) -> Tuple[str, float, List[str]]:
    """
    Infer blast_radius from text.

    Returns:
        (blast_radius, confidence, detected_keywords)
    """
    text_lower = text.lower()

    # Check each level from highest to lowest
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        keywords = BLAST_RADIUS_KEYWORDS[level]
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            confidence = 0.6 if level == "LOW" else 0.7
            return level, confidence, found[:3]

    # Default to LOW with low confidence
    return "LOW", 0.4, []


def infer_metadata(statement: str, rationale: str) -> InferredMetadata:
    """
    Analyze text to suggest metadata values.

    Args:
        statement: The decision statement
        rationale: The decision rationale

    Returns:
        InferredMetadata with suggestions and confidence scores
    """
    combined = f"{statement} {rationale}"

    # Infer each metadata type
    tags, tag_conf, tag_detected = infer_tags(combined)
    tech, tech_conf, tech_detected = infer_tech_stack(combined)
    radius, radius_conf, radius_detected = infer_blast_radius(combined)

    # Combine detected keywords
    all_detected = {}
    if tag_detected:
        all_detected['tags'] = tag_detected
    if tech_detected:
        all_detected['tech_stack'] = tech_detected
    if radius_detected:
        all_detected['blast_radius'] = radius_detected

    return InferredMetadata(
        suggested_tags=tags,
        suggested_tech_stack=tech,
        suggested_blast_radius=radius,
        tag_confidence=tag_conf,
        tech_confidence=tech_conf,
        blast_radius_confidence=radius_conf,
        detected_keywords=all_detected,
    )


def suggest_missing_metadata(
    record: Dict[str, Any],
    inferred: InferredMetadata
) -> List[str]:
    """
    Generate suggestions for missing metadata.

    Compares current record metadata with inferred values
    and suggests additions.

    Args:
        record: Current decision record
        inferred: Inferred metadata

    Returns:
        List of suggestion strings
    """
    suggestions = []

    # Check tags
    current_tags = set(record.get('tags', []))
    if not current_tags and inferred.suggested_tags:
        suggestions.append(
            f"Consider adding tags: {', '.join(inferred.suggested_tags[:3])}"
        )

    # Check tech_stack
    current_tech = set(record.get('tech_stack', []))
    if not current_tech and inferred.suggested_tech_stack:
        suggestions.append(
            f"Consider adding tech_stack: {', '.join(inferred.suggested_tech_stack[:3])}"
        )

    # Check blast_radius consistency
    current_radius = record.get('blast_radius', '')
    if current_radius and inferred.suggested_blast_radius:
        # Warn if mismatch
        radius_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        try:
            current_idx = radius_order.index(current_radius)
            inferred_idx = radius_order.index(inferred.suggested_blast_radius)
            if abs(current_idx - inferred_idx) >= 2:
                suggestions.append(
                    f"blast_radius '{current_radius}' may not match content. "
                    f"Text suggests '{inferred.suggested_blast_radius}'."
                )
        except ValueError:
            pass

    return suggestions
