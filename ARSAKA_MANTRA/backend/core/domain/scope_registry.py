"""
Scope Registry

Provides:
- Default scope tree for common project structure
- Functions to register custom scopes
- Functions to resolve scope paths with denormalization

Default Tree Structure:
                        project
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
      architecture        fe             be
      (umbrella)           │              │
            │         ┌────┴────┐    ┌────┴────┐
            │         ▼    ▼    ▼    ▼    ▼    ▼
            │       api  state  ui  api  db  service
            │         │         │    │    │
            │         ▼         ▼    ▼    ▼
            │       rest     component  sql  cache
            │         │                  │
            └─────────┴──────────────────┘
                 Shared: "api" under both fe and be

Usage:
    from core.domain.scope_registry import (
        get_default_tree,
        resolve_scope,
        register_custom_scope,
    )

    tree = get_default_tree()

    # Resolve a decision's scope
    scope_def = resolve_scope(tree, "fe.api", alternative_paths=["be.api"])
    print(scope_def.applies_to)  # ["fe.api", "be.api", "fe.api.rest", ...]
    print(scope_def.applies_to_description)  # Human-readable for AI
"""

from typing import Dict, List, Optional, Set, Tuple
from threading import Lock

from core.domain.scope_dag import (
    ScopeTree,
    ScopeNode,
    ScopeDefinition,
    InheritanceType,
    InheritanceInfo,
    create_scope_definition,
)


# =============================================================================
# DEFAULT SCOPE DEFINITIONS (COMPREHENSIVE)
# =============================================================================
#
# A comprehensive tree of predefined scopes. AI selects from these when
# creating decisions. If a scope doesn't exist, AI can create new ones.
#
# Structure:
#   project (root)
#   ├── architecture (umbrella - cross-cutting)
#   ├── fe (frontend)
#   │   ├── fe.api, fe.state, fe.ui, fe.routing, fe.forms
#   │   └── fe.ui.component, fe.ui.layout, fe.ui.styling
#   ├── be (backend)
#   │   ├── be.api, be.service, be.repository, be.auth, be.queue
#   │   └── be.repository.sql, be.repository.nosql
#   ├── data
#   │   └── data.model, data.schema, data.cache, data.search
#   ├── infra
#   │   └── infra.docker, infra.ci, infra.monitoring, infra.nomad
#   ├── shared (FE+BE shared)
#   │   └── shared.api, shared.types, shared.utils
#   └── mobile (optional)
#       └── mobile.ios, mobile.android

# Node definitions: (id, label, description, parents, aliases, tags)
DEFAULT_NODES: List[Tuple[str, str, str, List[str], List[str], List[str]]] = [
    # =========================================================================
    # ROOT
    # =========================================================================
    (
        "project",
        "Project",
        "Top-level scope - applies to entire codebase",
        [],
        ["proj", "root", "all", "*"],
        ["root"],
    ),

    # =========================================================================
    # LEVEL 1: Main Branches
    # =========================================================================
    (
        "architecture",
        "Architecture",
        "Cross-cutting architectural decisions (umbrella - applies to all code)",
        ["project"],
        ["arch", "design", "pattern", "principle"],
        ["umbrella", "cross-cutting"],
    ),
    (
        "fe",
        "Frontend",
        "Frontend/client-side code and decisions",
        ["project"],
        ["frontend", "client", "web", "ui-layer"],
        ["branch"],
    ),
    (
        "be",
        "Backend",
        "Backend/server-side code and decisions",
        ["project"],
        ["backend", "server", "api-layer"],
        ["branch"],
    ),
    (
        "data",
        "Data",
        "Data architecture, models, and storage",
        ["project"],
        ["database", "db", "storage", "persistence"],
        ["branch"],
    ),
    (
        "infra",
        "Infrastructure",
        "Infrastructure, deployment, and DevOps",
        ["project"],
        ["infrastructure", "devops", "deploy", "ops"],
        ["branch"],
    ),
    (
        "shared",
        "Shared",
        "Shared code between frontend and backend",
        ["project"],
        ["common", "lib", "util", "shared-lib"],
        ["branch"],
    ),
    (
        "mobile",
        "Mobile",
        "Mobile application code (iOS, Android)",
        ["project"],
        ["app", "native", "ios", "android"],
        ["branch"],
    ),
    (
        "testing",
        "Testing",
        "Testing strategies and conventions",
        ["project"],
        ["test", "qa", "quality"],
        ["branch"],
    ),
    (
        "security",
        "Security",
        "Security practices and policies",
        ["project"],
        ["sec", "auth", "authz"],
        ["branch", "cross-cutting"],
    ),

    # =========================================================================
    # LEVEL 2: Frontend Sub-domains
    # =========================================================================
    (
        "fe.api",
        "Frontend API",
        "Frontend API layer (HTTP clients, fetch, axios, tanstack-query)",
        ["fe"],
        ["fe-api", "frontend-api", "http-client", "fetch"],
        ["api"],
    ),
    (
        "fe.state",
        "Frontend State",
        "Frontend state management (Redux, Zustand, Context, Jotai)",
        ["fe"],
        ["state-management", "store", "redux", "zustand"],
        ["state"],
    ),
    (
        "fe.ui",
        "Frontend UI",
        "Frontend UI components and styling",
        ["fe"],
        ["ui", "components", "styling", "css"],
        ["ui"],
    ),
    (
        "fe.routing",
        "Frontend Routing",
        "Frontend routing and navigation",
        ["fe"],
        ["router", "navigation", "routes", "react-router"],
        ["routing"],
    ),
    (
        "fe.forms",
        "Frontend Forms",
        "Frontend form handling and validation",
        ["fe"],
        ["forms", "validation", "input", "react-hook-form"],
        ["forms"],
    ),
    (
        "fe.hooks",
        "Frontend Hooks",
        "Custom React hooks and composables",
        ["fe"],
        ["hooks", "composables", "custom-hooks"],
        ["hooks"],
    ),
    (
        "fe.utils",
        "Frontend Utils",
        "Frontend utility functions and helpers",
        ["fe"],
        ["utils", "helpers", "lib"],
        ["utils"],
    ),

    # =========================================================================
    # LEVEL 3: Frontend UI Sub-types
    # =========================================================================
    (
        "fe.ui.component",
        "UI Components",
        "Reusable UI component patterns (atoms, molecules, organisms)",
        ["fe.ui"],
        ["component", "widget", "atom", "molecule"],
        ["component"],
    ),
    (
        "fe.ui.layout",
        "UI Layouts",
        "Layout and structure patterns (grid, flex, containers)",
        ["fe.ui"],
        ["layout", "structure", "grid", "flex"],
        ["layout"],
    ),
    (
        "fe.ui.styling",
        "UI Styling",
        "Styling conventions (Tailwind, CSS modules, styled-components)",
        ["fe.ui"],
        ["styles", "css", "tailwind", "scss"],
        ["styling"],
    ),
    (
        "fe.ui.animation",
        "UI Animation",
        "Animation and transitions (Framer Motion, CSS animations)",
        ["fe.ui"],
        ["animation", "motion", "transition", "framer"],
        ["animation"],
    ),

    # =========================================================================
    # LEVEL 2: Backend Sub-domains
    # =========================================================================
    (
        "be.api",
        "Backend API",
        "Backend API layer (REST endpoints, GraphQL, OpenAPI)",
        ["be"],
        ["be-api", "backend-api", "rest", "endpoints", "openapi"],
        ["api"],
    ),
    (
        "be.service",
        "Backend Services",
        "Backend business logic and use cases",
        ["be"],
        ["services", "business-logic", "use-cases", "domain"],
        ["service"],
    ),
    (
        "be.repository",
        "Backend Repository",
        "Backend data access layer (repositories, DAL)",
        ["be"],
        ["repo", "data-access", "dal", "orm"],
        ["repository"],
    ),
    (
        "be.auth",
        "Backend Auth",
        "Backend authentication and authorization",
        ["be"],
        ["authentication", "authorization", "jwt", "oauth"],
        ["auth"],
    ),
    (
        "be.queue",
        "Backend Queue",
        "Backend message queues and async processing",
        ["be"],
        ["messaging", "rabbitmq", "celery", "async", "worker"],
        ["queue"],
    ),
    (
        "be.validation",
        "Backend Validation",
        "Backend input validation and sanitization",
        ["be"],
        ["validation", "sanitization", "pydantic", "schema"],
        ["validation"],
    ),
    (
        "be.middleware",
        "Backend Middleware",
        "Backend middleware and interceptors",
        ["be"],
        ["middleware", "interceptor", "decorator"],
        ["middleware"],
    ),
    (
        "be.utils",
        "Backend Utils",
        "Backend utility functions and helpers",
        ["be"],
        ["utils", "helpers", "lib"],
        ["utils"],
    ),

    # =========================================================================
    # LEVEL 3: Backend Repository Sub-types
    # =========================================================================
    (
        "be.repository.sql",
        "SQL Repository",
        "SQL/relational database patterns (PostgreSQL, MySQL)",
        ["be.repository"],
        ["sql", "postgres", "mysql", "relational"],
        ["sql"],
    ),
    (
        "be.repository.nosql",
        "NoSQL Repository",
        "NoSQL/document database patterns (MongoDB, Redis)",
        ["be.repository"],
        ["nosql", "mongodb", "redis", "document"],
        ["nosql"],
    ),

    # =========================================================================
    # LEVEL 2: Data Sub-domains
    # =========================================================================
    (
        "data.model",
        "Data Models",
        "Data models and entity definitions",
        ["data"],
        ["models", "entities", "domain", "pydantic"],
        ["model"],
    ),
    (
        "data.schema",
        "Data Schema",
        "Database schema and migrations",
        ["data"],
        ["schema", "migrations", "ddl", "alembic"],
        ["schema"],
    ),
    (
        "data.cache",
        "Data Cache",
        "Caching layer (Redis, in-memory, CDN)",
        ["data"],
        ["cache", "redis", "memory", "cdn"],
        ["cache"],
    ),
    (
        "data.search",
        "Data Search",
        "Search infrastructure (Meilisearch, Elasticsearch, Algolia)",
        ["data"],
        ["search", "indexing", "meilisearch", "elasticsearch"],
        ["search"],
    ),
    (
        "data.vector",
        "Vector Store",
        "Vector database for embeddings (Qdrant, Pinecone, pgvector)",
        ["data"],
        ["vector", "embedding", "qdrant", "pinecone"],
        ["vector"],
    ),

    # =========================================================================
    # LEVEL 2: Infrastructure Sub-domains
    # =========================================================================
    (
        "infra.docker",
        "Docker",
        "Docker containerization and compose",
        ["infra"],
        ["container", "dockerfile", "compose"],
        ["docker"],
    ),
    (
        "infra.nomad",
        "Nomad",
        "HashiCorp Nomad orchestration",
        ["infra"],
        ["orchestration", "nomad-jobs", "hashicorp"],
        ["nomad"],
    ),
    (
        "infra.k8s",
        "Kubernetes",
        "Kubernetes orchestration",
        ["infra"],
        ["kubernetes", "k8s", "helm", "kubectl"],
        ["k8s"],
    ),
    (
        "infra.ci",
        "CI/CD",
        "Continuous integration and deployment pipelines",
        ["infra"],
        ["cicd", "pipeline", "github-actions", "gitlab-ci"],
        ["ci"],
    ),
    (
        "infra.monitoring",
        "Monitoring",
        "Monitoring, logging, and observability",
        ["infra"],
        ["metrics", "logging", "observability", "prometheus", "grafana"],
        ["monitoring"],
    ),
    (
        "infra.networking",
        "Networking",
        "Network configuration, load balancing, DNS",
        ["infra"],
        ["network", "loadbalancer", "dns", "traefik", "nginx"],
        ["networking"],
    ),

    # =========================================================================
    # LEVEL 2: Shared Sub-domains
    # =========================================================================
    (
        "shared.api",
        "Shared API",
        "Shared API contracts and types between FE and BE",
        ["shared"],
        ["api-contract", "openapi", "types"],
        ["api"],
    ),
    (
        "shared.types",
        "Shared Types",
        "Shared type definitions (TypeScript, Python typing)",
        ["shared"],
        ["types", "interfaces", "typing"],
        ["types"],
    ),
    (
        "shared.utils",
        "Shared Utils",
        "Shared utility functions",
        ["shared"],
        ["utils", "helpers", "common"],
        ["utils"],
    ),
    (
        "shared.constants",
        "Shared Constants",
        "Shared constants and enums",
        ["shared"],
        ["constants", "enums", "config"],
        ["constants"],
    ),

    # =========================================================================
    # LEVEL 2: Mobile Sub-domains
    # =========================================================================
    (
        "mobile.ios",
        "iOS",
        "iOS-specific code and patterns",
        ["mobile"],
        ["ios", "swift", "swiftui", "uikit"],
        ["ios"],
    ),
    (
        "mobile.android",
        "Android",
        "Android-specific code and patterns",
        ["mobile"],
        ["android", "kotlin", "jetpack", "compose"],
        ["android"],
    ),
    (
        "mobile.shared",
        "Mobile Shared",
        "Cross-platform mobile code (React Native, Flutter)",
        ["mobile"],
        ["react-native", "flutter", "cross-platform"],
        ["shared"],
    ),

    # =========================================================================
    # LEVEL 2: Testing Sub-domains
    # =========================================================================
    (
        "testing.unit",
        "Unit Testing",
        "Unit testing patterns and conventions",
        ["testing"],
        ["unit", "jest", "pytest", "vitest"],
        ["unit"],
    ),
    (
        "testing.integration",
        "Integration Testing",
        "Integration testing patterns",
        ["testing"],
        ["integration", "api-test", "db-test"],
        ["integration"],
    ),
    (
        "testing.e2e",
        "E2E Testing",
        "End-to-end testing patterns (Playwright, Cypress)",
        ["testing"],
        ["e2e", "playwright", "cypress", "selenium"],
        ["e2e"],
    ),

    # =========================================================================
    # LEVEL 2: Security Sub-domains
    # =========================================================================
    (
        "security.auth",
        "Authentication",
        "Authentication mechanisms (JWT, OAuth, SSO)",
        ["security"],
        ["authentication", "jwt", "oauth", "sso", "login"],
        ["auth"],
    ),
    (
        "security.authz",
        "Authorization",
        "Authorization and access control (RBAC, ABAC)",
        ["security"],
        ["authorization", "rbac", "abac", "permissions"],
        ["authz"],
    ),
    (
        "security.crypto",
        "Cryptography",
        "Encryption and hashing",
        ["security"],
        ["encryption", "hashing", "crypto", "secrets"],
        ["crypto"],
    ),
    (
        "security.input",
        "Input Security",
        "Input validation, XSS prevention, SQL injection",
        ["security"],
        ["xss", "injection", "sanitization", "validation"],
        ["input"],
    ),

    # =========================================================================
    # ARCHITECTURE: Cross-cutting Patterns (Umbrella)
    # =========================================================================
    (
        "architecture.clean",
        "Clean Architecture",
        "Clean Architecture / Hexagonal / Ports & Adapters",
        ["architecture"],
        ["clean-arch", "hexagonal", "ports-adapters", "onion"],
        ["pattern"],
    ),
    (
        "architecture.modular",
        "Modular Design",
        "Module organization and boundaries",
        ["architecture"],
        ["modular", "modules", "packages", "boundaries"],
        ["pattern"],
    ),
    (
        "architecture.ddd",
        "Domain-Driven Design",
        "DDD patterns (aggregates, entities, value objects)",
        ["architecture"],
        ["ddd", "domain", "aggregate", "entity"],
        ["pattern"],
    ),
    (
        "architecture.cqrs",
        "CQRS/Event Sourcing",
        "Command Query Responsibility Segregation",
        ["architecture"],
        ["cqrs", "event-sourcing", "es"],
        ["pattern"],
    ),
    (
        "architecture.error",
        "Error Handling",
        "Error handling conventions and patterns",
        ["architecture"],
        ["error", "exception", "fault-tolerance"],
        ["pattern"],
    ),
    (
        "architecture.logging",
        "Logging",
        "Logging conventions and structured logging",
        ["architecture"],
        ["logging", "log", "structured-log"],
        ["pattern"],
    ),
    (
        "architecture.naming",
        "Naming Conventions",
        "Naming and coding style conventions",
        ["architecture"],
        ["naming", "convention", "style", "lint"],
        ["pattern"],
    ),
    (
        "architecture.api-design",
        "API Design",
        "API design principles (REST, GraphQL, versioning)",
        ["architecture"],
        ["api-design", "rest-design", "versioning"],
        ["pattern"],
    ),
]


# =============================================================================
# COMMON SCOPE PATTERNS (for suggestions/autocomplete)
# =============================================================================
# These are NOT nodes in the tree, just patterns for UI suggestions

COMMON_SCOPE_PATTERNS: List[str] = [
    # Frontend patterns
    "fe.api", "fe.state", "fe.ui", "fe.routing", "fe.forms",
    # Backend patterns
    "be.api", "be.service", "be.repository", "be.auth", "be.queue",
    # Data patterns
    "data.model", "data.schema", "data.cache", "data.search",
    # Infra patterns
    "infra.docker", "infra.ci", "infra.monitoring",
    # Architecture patterns
    "architecture.clean", "architecture.modular", "architecture.testing",
]


# Legacy compatibility - map old tags to new scope paths
TAG_TO_SCOPE_MAP: Dict[str, str] = {
    "FE": "fe",
    "BE": "be",
    "DB": "data",
    "INFRA": "infra",
    "API": "be.api",  # Default API to backend
    "UI": "fe.ui",
    "AUTH": "be.auth",
    "ARCH": "architecture",
}


def migrate_tags_to_scope(tags: List[str]) -> List[str]:
    """
    Migrate old tags to scope paths (for backward compatibility).

    Args:
        tags: Old-style tags ["FE", "API", "AUTH"]

    Returns:
        Scope paths ["fe", "be.api", "be.auth"]
    """
    scopes = []
    for tag in tags:
        tag_upper = tag.upper()
        if tag_upper in TAG_TO_SCOPE_MAP:
            scopes.append(TAG_TO_SCOPE_MAP[tag_upper])
        else:
            # Unknown tag - use as-is in lowercase
            scopes.append(tag.lower())
    return list(set(scopes))  # Deduplicate


# =============================================================================
# REGISTRY SINGLETON
# =============================================================================

_default_tree: Optional[ScopeTree] = None
_tree_lock = Lock()


def get_default_tree() -> ScopeTree:
    """
    Get the default scope tree (singleton).

    Returns:
        ScopeTree with default project structure
    """
    global _default_tree

    if _default_tree is None:
        with _tree_lock:
            if _default_tree is None:
                _default_tree = _build_default_tree()

    return _default_tree


def _build_default_tree() -> ScopeTree:
    """Build the default scope tree from definitions."""
    tree = ScopeTree()

    for node_id, label, description, parents, aliases, tags in DEFAULT_NODES:
        tree.add_node(
            node_id=node_id,
            label=label,
            description=description,
            parents=parents,
            aliases=aliases,
            tags=tags,
        )

    return tree


def reset_default_tree() -> None:
    """Reset the default tree (for testing)."""
    global _default_tree
    with _tree_lock:
        _default_tree = None


# =============================================================================
# DYNAMIC SCOPE CREATION
# =============================================================================

def ensure_scope_exists(
    scope_path: str,
    tree: Optional[ScopeTree] = None,
) -> ScopeNode:
    """
    Ensure a scope path exists in the tree, creating nodes as needed.

    This enables dynamic scope creation - users can use any scope path
    and the system will auto-create the necessary hierarchy.

    Args:
        scope_path: Dot-separated scope path (e.g., "fe.api.auth.oauth")
        tree: Tree to use (defaults to default tree)

    Returns:
        The leaf ScopeNode for the path

    Example:
        >>> ensure_scope_exists("fe.api.auth")
        # Creates: fe.api (if not exists), fe.api.auth (if not exists)
        # Returns: ScopeNode for fe.api.auth
    """
    target_tree = tree or get_default_tree()
    parts = scope_path.split(".")

    current_path = ""
    parent_ids = []

    for i, part in enumerate(parts):
        if current_path:
            current_path = f"{current_path}.{part}"
        else:
            current_path = part

        # Check if this node exists
        node = target_tree.get_node(current_path)

        if not node:
            # Determine parent
            if parent_ids:
                parents = [parent_ids[-1]]
            elif i == 0:
                # First level - check if it's a known branch
                if part in ["fe", "be", "data", "infra", "shared", "architecture"]:
                    parents = ["project"]
                else:
                    # Unknown top-level - put under project
                    parents = ["project"]
            else:
                parents = []

            # Create the node
            label = part.replace("_", " ").replace("-", " ").title()
            node = target_tree.add_node(
                node_id=current_path,
                label=label,
                description=f"Auto-created scope: {current_path}",
                parents=parents,
                aliases=[part],
                tags=["auto-created"],
            )

        parent_ids.append(current_path)

    return target_tree.get_node(scope_path)


def ensure_scopes_exist(
    scope_paths: List[str],
    tree: Optional[ScopeTree] = None,
) -> List[ScopeNode]:
    """
    Ensure multiple scope paths exist in the tree.

    Args:
        scope_paths: List of scope paths
        tree: Tree to use (defaults to default tree)

    Returns:
        List of ScopeNodes for all paths
    """
    return [ensure_scope_exists(path, tree) for path in scope_paths]


def auto_register_scope(
    scope_path: str,
    label: Optional[str] = None,
    description: Optional[str] = None,
    aliases: Optional[List[str]] = None,
    tree: Optional[ScopeTree] = None,
) -> ScopeNode:
    """
    Auto-register a scope with optional metadata.

    Like ensure_scope_exists but allows providing custom label/description.

    Args:
        scope_path: Scope path to register
        label: Optional human-readable label
        description: Optional description
        aliases: Optional list of aliases
        tree: Tree to use

    Returns:
        Created or existing ScopeNode
    """
    target_tree = tree or get_default_tree()

    # First ensure the path exists
    node = ensure_scope_exists(scope_path, target_tree)

    # Update with custom metadata if provided
    if label or description or aliases:
        if label:
            node.label = label
        if description:
            node.description = description
        if aliases:
            node.aliases = list(set(node.aliases + aliases))

    return node


# =============================================================================
# SCOPE RESOLUTION
# =============================================================================

def resolve_scope(
    tree: ScopeTree,
    primary_path: str,
    alternative_paths: Optional[List[str]] = None,
    auto_create: bool = True,
) -> ScopeDefinition:
    """
    Resolve a scope path to a full ScopeDefinition with denormalized fields.

    This is the main function for creating scope definitions for decisions.
    It pre-computes all the "applies_to" paths for efficient AI retrieval.

    If auto_create=True (default), missing scopes are automatically created.

    Args:
        tree: Scope tree to use
        primary_path: Primary scope path (e.g., "fe.api")
        alternative_paths: Alternative paths for shared scope (e.g., ["be.api"])
        auto_create: If True, auto-create missing scopes in tree

    Returns:
        ScopeDefinition with all fields populated

    Example:
        >>> tree = get_default_tree()
        >>> scope_def = resolve_scope(tree, "fe.api.auth")  # auto-creates fe.api.auth
        >>> print(scope_def.applies_to_description)
    """
    # Auto-create scopes if they don't exist
    if auto_create:
        all_paths = [primary_path] + (alternative_paths or [])
        ensure_scopes_exist(all_paths, tree)

    return create_scope_definition(tree, primary_path, alternative_paths)


def resolve_scope_simple(
    primary_path: str,
    alternative_paths: Optional[List[str]] = None,
) -> ScopeDefinition:
    """
    Resolve scope using the default tree.

    Convenience function that uses get_default_tree().

    Args:
        primary_path: Primary scope path
        alternative_paths: Alternative paths

    Returns:
        ScopeDefinition
    """
    return resolve_scope(get_default_tree(), primary_path, alternative_paths)


# =============================================================================
# CUSTOM SCOPE REGISTRATION
# =============================================================================

def register_custom_scope(
    node_id: str,
    label: str,
    description: str = "",
    parents: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    tree: Optional[ScopeTree] = None,
) -> ScopeNode:
    """
    Register a custom scope in the tree.

    Args:
        node_id: Unique scope identifier
        label: Human-readable label
        description: Scope description
        parents: Parent scope IDs
        aliases: Alternative names
        tags: Categorization tags
        tree: Tree to add to (defaults to default tree)

    Returns:
        Created ScopeNode

    Example:
        >>> register_custom_scope(
        ...     "fe.ui.charts",
        ...     "Chart Components",
        ...     "Data visualization components",
        ...     parents=["fe.ui"],
        ...     aliases=["charts", "visualization", "d3"],
        ... )
    """
    target_tree = tree or get_default_tree()
    return target_tree.add_node(
        node_id=node_id,
        label=label,
        description=description,
        parents=parents,
        aliases=aliases,
        tags=tags,
    )


def register_batch_scopes(
    scopes: List[Tuple[str, str, str, List[str], List[str], List[str]]],
    tree: Optional[ScopeTree] = None,
) -> List[ScopeNode]:
    """
    Register multiple custom scopes at once.

    Args:
        scopes: List of (node_id, label, description, parents, aliases, tags)
        tree: Tree to add to (defaults to default tree)

    Returns:
        List of created ScopeNodes
    """
    target_tree = tree or get_default_tree()
    nodes = []

    for node_id, label, description, parents, aliases, tags in scopes:
        node = target_tree.add_node(
            node_id=node_id,
            label=label,
            description=description,
            parents=parents,
            aliases=aliases,
            tags=tags,
        )
        nodes.append(node)

    return nodes


# =============================================================================
# SCOPE MATCHING & LOOKUP
# =============================================================================

def find_scope_by_alias(
    alias: str,
    tree: Optional[ScopeTree] = None,
) -> Optional[ScopeNode]:
    """
    Find a scope by its alias or ID.

    Args:
        alias: Alias or ID to search for
        tree: Tree to search (defaults to default tree)

    Returns:
        Matching ScopeNode or None
    """
    target_tree = tree or get_default_tree()

    # Try direct ID first
    node = target_tree.get_node(alias)
    if node:
        return node

    # Search aliases
    alias_lower = alias.lower()
    for node in target_tree.get_all_nodes():
        if alias_lower in [a.lower() for a in node.aliases]:
            return node

    return None


def get_scopes_by_tag(
    tag: str,
    tree: Optional[ScopeTree] = None,
) -> List[ScopeNode]:
    """
    Get all scopes with a specific tag.

    Args:
        tag: Tag to filter by
        tree: Tree to search (defaults to default tree)

    Returns:
        List of matching ScopeNodes
    """
    target_tree = tree or get_default_tree()

    return [
        node for node in target_tree.get_all_nodes()
        if tag in node.tags
    ]


def get_umbrella_scopes(tree: Optional[ScopeTree] = None) -> List[ScopeNode]:
    """
    Get all umbrella scopes (cross-cutting concerns).

    Umbrella scopes are those with the "cross-cutting" tag or
    under the "architecture" branch.

    Args:
        tree: Tree to search (defaults to default tree)

    Returns:
        List of umbrella ScopeNodes
    """
    target_tree = tree or get_default_tree()

    # Get architecture and its descendants
    arch_descendants = target_tree.get_descendants("architecture", include_self=True)

    # Get nodes with cross-cutting tag
    cross_cutting = get_scopes_by_tag("cross-cutting", target_tree)

    # Combine
    umbrella_ids = set(arch_descendants) | {n.id for n in cross_cutting}

    return [
        target_tree.get_node(nid)
        for nid in umbrella_ids
        if target_tree.get_node(nid)
    ]


def get_shared_scopes(tree: Optional[ScopeTree] = None) -> List[ScopeNode]:
    """
    Get all shared scopes (under multiple parents).

    Args:
        tree: Tree to search (defaults to default tree)

    Returns:
        List of shared ScopeNodes
    """
    target_tree = tree or get_default_tree()

    return [
        node for node in target_tree.get_all_nodes()
        if len(node.parents) > 1
    ]


# =============================================================================
# SCOPE SUGGESTIONS (for autocomplete)
# =============================================================================

def suggest_scopes(
    partial: str,
    tree: Optional[ScopeTree] = None,
    limit: int = 10,
) -> List[Dict]:
    """
    Suggest scopes based on partial input.

    For use in autocomplete/typeahead.

    Args:
        partial: Partial input to match
        tree: Tree to search (defaults to default tree)
        limit: Maximum suggestions to return

    Returns:
        List of suggestion dicts with id, label, description
    """
    target_tree = tree or get_default_tree()
    partial_lower = partial.lower()

    suggestions = []

    for node in target_tree.get_all_nodes():
        # Match against ID, label, and aliases
        if (
            partial_lower in node.id.lower()
            or partial_lower in node.label.lower()
            or any(partial_lower in alias.lower() for alias in node.aliases)
        ):
            suggestions.append({
                "id": node.id,
                "label": node.label,
                "description": node.description,
                "path": node.id,
            })

            if len(suggestions) >= limit:
                break

    return suggestions


def get_scope_hierarchy(
    tree: Optional[ScopeTree] = None,
) -> Dict[str, List[Dict]]:
    """
    Get scope hierarchy as nested structure.

    Useful for rendering tree views in UI.

    Args:
        tree: Tree to use (defaults to default tree)

    Returns:
        Dict with root nodes and their children
    """
    target_tree = tree or get_default_tree()

    def build_node_tree(node_id: str) -> Dict:
        node = target_tree.get_node(node_id)
        if not node:
            return {}

        return {
            "id": node.id,
            "label": node.label,
            "description": node.description,
            "tags": node.tags,
            "children": [
                build_node_tree(child_id)
                for child_id in node.children
            ],
        }

    # Get root nodes
    roots = [n for n in target_tree.get_all_nodes() if not n.parents]

    return {
        "roots": [build_node_tree(root.id) for root in roots],
    }


# =============================================================================
# AI RETRIEVAL HELPERS
# =============================================================================

def get_applies_to_for_retrieval(
    scope_paths: List[str],
    tree: Optional[ScopeTree] = None,
) -> Dict[str, any]:
    """
    Get denormalized scope information optimized for AI retrieval.

    This function produces the data that should be stored with each decision
    to enable intelligent scope-aware retrieval.

    Args:
        scope_paths: List of scope paths for a decision
        tree: Tree to use (defaults to default tree)

    Returns:
        Dict with:
        - primary_scope: Main scope path
        - all_scopes: All paths this applies to (denormalized)
        - description: Human-readable description
        - inheritance_type: How this scope inherits
        - ancestors: Scopes this is affected by
        - descendants: Scopes this affects
    """
    target_tree = tree or get_default_tree()

    if not scope_paths:
        return {
            "primary_scope": "*",
            "all_scopes": ["*"],
            "description": "Applies to entire project",
            "inheritance_type": "umbrella",
            "ancestors": [],
            "descendants": [],
        }

    primary = scope_paths[0]
    alternatives = scope_paths[1:] if len(scope_paths) > 1 else []

    scope_def = resolve_scope(target_tree, primary, alternatives)

    return {
        "primary_scope": scope_def.primary_path,
        "all_scopes": scope_def.applies_to,
        "description": scope_def.applies_to_description,
        "inheritance_type": scope_def.inheritance_type.value,
        "ancestors": scope_def.inheritance_info.affected_by if scope_def.inheritance_info else [],
        "descendants": scope_def.inheritance_info.affects if scope_def.inheritance_info else [],
    }


def scope_matches_query(
    decision_scope: Dict,
    query_scope: str,
    tree: Optional[ScopeTree] = None,
) -> bool:
    """
    Check if a decision's scope matches a query scope.

    Used by retrieval to filter decisions by scope.

    Args:
        decision_scope: Decision's scope info (from get_applies_to_for_retrieval)
        query_scope: Scope being queried
        tree: Tree to use (defaults to default tree)

    Returns:
        True if decision applies to the query scope
    """
    target_tree = tree or get_default_tree()

    # Direct match
    if query_scope in decision_scope.get("all_scopes", []):
        return True

    # Wildcard query
    if "*" in query_scope:
        expanded = target_tree.expand_wildcard(query_scope)
        for exp_scope in expanded:
            if exp_scope in decision_scope.get("all_scopes", []):
                return True

    # Check if query is ancestor of decision scope
    # (decisions in "fe" should match queries for "fe.api")
    query_parts = query_scope.split(".")
    for scope in decision_scope.get("all_scopes", []):
        scope_parts = scope.split(".")
        if len(scope_parts) >= len(query_parts):
            if scope_parts[:len(query_parts)] == query_parts:
                return True

    return False


__all__ = [
    # Tree access
    "get_default_tree",
    "reset_default_tree",
    # Dynamic scope creation (NEW)
    "ensure_scope_exists",
    "ensure_scopes_exist",
    "auto_register_scope",
    # Scope resolution
    "resolve_scope",
    "resolve_scope_simple",
    # Registration
    "register_custom_scope",
    "register_batch_scopes",
    # Lookup
    "find_scope_by_alias",
    "get_scopes_by_tag",
    "get_umbrella_scopes",
    "get_shared_scopes",
    # Suggestions
    "suggest_scopes",
    "get_scope_hierarchy",
    # AI Retrieval
    "get_applies_to_for_retrieval",
    "scope_matches_query",
    # Legacy migration
    "migrate_tags_to_scope",
    "TAG_TO_SCOPE_MAP",
    # Constants
    "DEFAULT_NODES",
    "COMMON_SCOPE_PATTERNS",
]
