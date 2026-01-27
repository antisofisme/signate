"""
MICS Agent Loader

Loads agent definitions from YAML files and matches intents to agents.

Per MICS-TECHNICAL-DESIGN.md:
- Load agent definition from YAML
- Keyword -> Agent mapping
- Semantic intent matching

Usage:
    loader = AgentLoader()
    agent = loader.load("deployment-agent")
    matched = loader.match_intent("deploy backend to production")
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import yaml

from .models import (
    AgentDefinition,
    AgentCategory,
    AgentTriggers,
    TriggerKeywords,
    TriggerCondition,
    DecisionContext,
    GroupReference,
    FeatureSet,
    TagSet,
    AgentPrompt,
    CriticalRule,
    TriggerSeverity,
    AgentChecklist,
    ChecklistItem,
    ValidationSpec,
    RetrySpec,
    ValidationRules,
    ValidationCondition,
    PlatformAdapters,
    ClaudeAdapter,
    CursorAdapter,
    OpenAIAdapter,
    GenericAdapter,
)

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Loads and manages MANTRA agent definitions.

    Agents are loaded from YAML files in the agents/ directory.
    Supports caching for performance.

    Usage:
        loader = AgentLoader()
        agent = loader.load("deployment-agent")

        # Or match by intent
        agent, confidence = loader.match_intent("deploy to production")
    """

    def __init__(self, agents_dir: Optional[str] = None):
        """
        Initialize agent loader.

        Args:
            agents_dir: Path to agents directory. If None, uses default.
        """
        if agents_dir:
            self.agents_dir = Path(agents_dir)
        else:
            # Default: backend/agents/
            self.agents_dir = Path(__file__).parent.parent / "agents"

        self._cache: Dict[str, AgentDefinition] = {}
        self._loaded_at: Optional[datetime] = None

    def load(self, agent_id: str) -> Optional[AgentDefinition]:
        """
        Load a single agent by ID.

        Args:
            agent_id: Agent identifier (e.g., "deployment-agent")

        Returns:
            AgentDefinition or None if not found
        """
        # Check cache
        if agent_id in self._cache:
            return self._cache[agent_id]

        # Try to load from file
        yaml_path = self.agents_dir / f"{agent_id}.yaml"
        if not yaml_path.exists():
            # Try without -agent suffix
            yaml_path = self.agents_dir / f"{agent_id}-agent.yaml"

        if not yaml_path.exists():
            logger.warning(f"Agent file not found: {agent_id}")
            return None

        try:
            agent = self._load_yaml(yaml_path)
            if agent:
                self._cache[agent_id] = agent
            return agent
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None

    def load_all(self, reload: bool = False) -> Dict[str, AgentDefinition]:
        """
        Load all agents from the agents directory.

        Args:
            reload: Force reload even if cached

        Returns:
            Dict mapping agent_id to AgentDefinition
        """
        if self._cache and not reload:
            return self._cache

        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return {}

        agents = {}
        for yaml_file in self.agents_dir.glob("*.yaml"):
            try:
                agent = self._load_yaml(yaml_file)
                if agent:
                    agents[agent.id] = agent
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")

        self._cache = agents
        self._loaded_at = datetime.utcnow()
        logger.info(f"Loaded {len(agents)} agents from {self.agents_dir}")

        return agents

    def _load_yaml(self, path: Path) -> Optional[AgentDefinition]:
        """Load and parse a YAML agent file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Handle nested 'agent' key
        agent_data = data.get('agent', data)

        return self._parse_agent(agent_data)

    def _parse_agent(self, data: Dict[str, Any]) -> AgentDefinition:
        """Parse raw YAML data into AgentDefinition."""

        # Parse triggers
        triggers_data = data.get('triggers', {})
        keywords_data = triggers_data.get('keywords', {})
        triggers = AgentTriggers(
            keywords=TriggerKeywords(
                primary=keywords_data.get('primary', []),
                secondary=keywords_data.get('secondary', [])
            ),
            intents=triggers_data.get('intents', []),
            conditions=[
                TriggerCondition(**c) for c in triggers_data.get('conditions', [])
            ]
        )

        # Parse decision context
        dc_data = data.get('decision_context', {})
        decision_context = DecisionContext(
            groups=[
                GroupReference(**g) for g in dc_data.get('groups', [])
            ],
            features=FeatureSet(
                required=dc_data.get('features', {}).get('required', []),
                optional=dc_data.get('features', {}).get('optional', [])
            ),
            tags=TagSet(
                required=dc_data.get('tags', {}).get('required', []),
                optional=dc_data.get('tags', {}).get('optional', [])
            ),
            search_queries=dc_data.get('search_queries', [])
        )

        # Parse prompt
        prompt_data = data.get('prompt', {})
        prompt = AgentPrompt(
            identity=prompt_data.get('identity', ''),
            critical_rules=[
                CriticalRule(
                    rule=r.get('rule', ''),
                    severity=TriggerSeverity(r.get('severity', 'warning'))
                )
                for r in prompt_data.get('critical_rules', [])
            ],
            behavior=prompt_data.get('behavior', []),
            template=prompt_data.get('template', '')
        )

        # Parse checklist
        checklist_data = data.get('checklist', {})
        checklist = AgentChecklist(
            pre=self._parse_checklist_items(checklist_data.get('pre_deploy', [])),
            main=self._parse_checklist_items(checklist_data.get('deploy', [])),
            post=self._parse_checklist_items(checklist_data.get('post_deploy', []))
        )

        # Parse validation
        validation_data = data.get('validation', {})
        validation = ValidationRules(
            pre_conditions=[
                ValidationCondition(**c)
                for c in validation_data.get('pre_conditions', [])
            ],
            post_conditions=[
                ValidationCondition(**c)
                for c in validation_data.get('post_conditions', [])
            ]
        )

        # Parse platform adapters
        adapters_data = data.get('platform_adapters', {})
        platform_adapters = PlatformAdapters(
            claude=ClaudeAdapter(**adapters_data.get('claude', {})),
            cursor=CursorAdapter(**adapters_data.get('cursor', {})),
            openai=OpenAIAdapter(**adapters_data.get('openai', {})),
            generic=GenericAdapter(**adapters_data.get('generic', {}))
        )

        # Parse category
        category_str = data.get('category', 'general')
        try:
            category = AgentCategory(category_str)
        except ValueError:
            category = AgentCategory.GENERAL

        return AgentDefinition(
            id=data.get('id', 'unknown'),
            name=data.get('name', 'Unknown Agent'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            category=category,
            triggers=triggers,
            decision_context=decision_context,
            prompt=prompt,
            checklist=checklist,
            validation=validation,
            platform_adapters=platform_adapters
        )

    def _parse_checklist_items(self, items: List[Dict]) -> List[ChecklistItem]:
        """Parse checklist items from YAML data."""
        result = []
        for item in items:
            validation = None
            if 'validation' in item:
                validation = ValidationSpec(**item['validation'])

            retry = None
            if 'retry' in item:
                retry = RetrySpec(**item['retry'])

            result.append(ChecklistItem(
                id=item.get('id', ''),
                step=item.get('step', ''),
                command=item.get('command'),
                blocking=item.get('blocking', False),
                condition=item.get('condition'),
                validation=validation,
                retry=retry
            ))
        return result

    def match_intent(
        self,
        intent: str,
        target: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Tuple[Optional[AgentDefinition], float]:
        """
        Match an intent to the best agent.

        Algorithm:
        1. Keyword matching (fast, first-pass)
        2. Condition checking (if keywords match)
        3. Return best match with confidence

        Args:
            intent: User intent string (e.g., "deploy backend to production")
            target: Optional target (e.g., "backend")
            environment: Optional environment (e.g., "production")

        Returns:
            Tuple of (AgentDefinition or None, confidence 0.0-1.0)
        """
        agents = self.load_all()
        if not agents:
            return None, 0.0

        intent_lower = intent.lower()
        target_lower = (target or "").lower()
        env_lower = (environment or "").lower()
        combined = f"{intent_lower} {target_lower} {env_lower}"

        best_agent = None
        best_score = 0.0

        for agent_id, agent in agents.items():
            score = self._calculate_match_score(
                agent, combined, target_lower, env_lower
            )
            if score > best_score:
                best_score = score
                best_agent = agent

        # Convert score to confidence (0.5 baseline + score contribution)
        confidence = min(0.95, 0.5 + (best_score * 0.45))

        return best_agent, confidence

    def _calculate_match_score(
        self,
        agent: AgentDefinition,
        combined_text: str,
        target: str,
        environment: str
    ) -> float:
        """Calculate match score for an agent against intent."""
        score = 0.0

        # Primary keyword matches (high weight)
        primary_matches = sum(
            1 for kw in agent.triggers.keywords.primary
            if kw.lower() in combined_text
        )
        if agent.triggers.keywords.primary:
            score += 0.5 * (primary_matches / len(agent.triggers.keywords.primary))

        # Secondary keyword matches (medium weight)
        secondary_matches = sum(
            1 for kw in agent.triggers.keywords.secondary
            if kw.lower() in combined_text
        )
        if agent.triggers.keywords.secondary:
            score += 0.3 * (secondary_matches / len(agent.triggers.keywords.secondary))

        # Condition matches (bonus)
        for condition in agent.triggers.conditions:
            if condition.target_includes:
                if any(t.lower() in target for t in condition.target_includes):
                    score += 0.1
            if condition.environment_includes:
                if any(e.lower() in environment for e in condition.environment_includes):
                    score += 0.1

        return min(1.0, score)

    def get_agent_for_category(self, category: AgentCategory) -> Optional[AgentDefinition]:
        """Get the first agent matching a category."""
        agents = self.load_all()
        for agent in agents.values():
            if agent.category == category:
                return agent
        return None


class AgentMatcher:
    """
    Enhanced agent matching with semantic similarity support.

    For complex cases where keyword matching is insufficient.
    """

    def __init__(self, loader: AgentLoader, embedding_service=None):
        """
        Initialize matcher.

        Args:
            loader: AgentLoader instance
            embedding_service: Optional embedding service for semantic matching
        """
        self.loader = loader
        self.embedding_service = embedding_service
        self._agent_embeddings: Dict[str, List[float]] = {}

    async def match_semantic(
        self,
        intent: str,
        fallback_to_keywords: bool = True
    ) -> Tuple[Optional[AgentDefinition], float]:
        """
        Match intent using semantic similarity.

        Falls back to keyword matching if embedding service unavailable.

        Args:
            intent: User intent string
            fallback_to_keywords: Use keyword matching as fallback

        Returns:
            Tuple of (AgentDefinition or None, confidence)
        """
        if not self.embedding_service:
            if fallback_to_keywords:
                return self.loader.match_intent(intent)
            return None, 0.0

        try:
            # Get intent embedding
            intent_embedding = await self.embedding_service.embed_text(intent)

            # Ensure agent embeddings are cached
            await self._cache_agent_embeddings()

            # Find best match
            best_agent = None
            best_similarity = 0.0

            for agent_id, agent_embedding in self._agent_embeddings.items():
                similarity = self._cosine_similarity(intent_embedding, agent_embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_agent = self.loader.load(agent_id)

            confidence = min(0.95, best_similarity)
            return best_agent, confidence

        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            if fallback_to_keywords:
                return self.loader.match_intent(intent)
            return None, 0.0

    async def _cache_agent_embeddings(self):
        """Cache embeddings for all agent descriptions."""
        if self._agent_embeddings:
            return

        agents = self.loader.load_all()
        for agent_id, agent in agents.items():
            try:
                # Combine agent info for embedding
                text = f"{agent.name} {agent.description} {' '.join(agent.get_all_keywords())}"
                embedding = await self.embedding_service.embed_text(text)
                self._agent_embeddings[agent_id] = embedding
            except Exception as e:
                logger.error(f"Failed to embed agent {agent_id}: {e}")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# =============================================================================
# Built-in Agents (Fallback when YAML not available)
# =============================================================================

BUILTIN_AGENTS = {
    "deployment": {
        "id": "deployment-agent",
        "name": "Deployment Agent",
        "description": "Handles production deployments with safety checks",
        "version": "1.0.0",
        "category": "deployment",
        "triggers": {
            "keywords": {
                "primary": ["deploy", "release", "ship"],
                "secondary": ["push to prod", "go live", "production"]
            },
            "intents": ["DEPLOYMENT", "RELEASE", "ROLLOUT"],
            "conditions": [
                {"target_includes": ["backend", "frontend", "api", "service"]},
                {"environment_includes": ["staging", "production", "prod"]}
            ]
        },
        "decision_context": {
            "groups": [
                {"id": "EVO", "relevance": "high", "reason": "Execution & Evolution"},
                {"id": "CTL", "relevance": "high", "reason": "Control & Policy"}
            ],
            "features": {"required": ["F15", "F13"], "optional": ["F14", "F11"]},
            "tags": {"required": ["INFRA", "CICD"], "optional": ["DEVOPS", "SECURITY"]}
        },
        "prompt": {
            "identity": "You are the Deployment Agent, responsible for safe and reliable production deployments.",
            "critical_rules": [
                {"rule": "NEVER deploy without passing tests", "severity": "blocking"},
                {"rule": "NEVER skip health checks", "severity": "blocking"},
                {"rule": "ALWAYS have rollback plan ready", "severity": "blocking"}
            ],
            "behavior": [
                "Ask for confirmation before destructive operations",
                "Log all deployment steps",
                "Verify success after each step"
            ]
        },
        "checklist": {
            "pre_deploy": [
                {"id": "tests", "step": "Run all tests", "command": "bun test", "blocking": True},
                {"id": "migrations", "step": "Check migrations", "command": "alembic check", "blocking": True}
            ],
            "deploy": [
                {"id": "build", "step": "Build Docker image", "command": "docker build", "blocking": True},
                {"id": "deploy", "step": "Deploy via Nomad", "command": "nomad job run", "blocking": True}
            ],
            "post_deploy": [
                {"id": "health", "step": "Verify health", "command": "curl /health", "blocking": True}
            ]
        }
    },
    "database": {
        "id": "database-agent",
        "name": "Database Agent",
        "description": "Handles database operations and migrations safely",
        "version": "1.0.0",
        "category": "database",
        "triggers": {
            "keywords": {
                "primary": ["database", "migration", "schema"],
                "secondary": ["sql", "postgresql", "table", "column"]
            },
            "intents": ["DATABASE", "MIGRATION", "SCHEMA_CHANGE"]
        },
        "decision_context": {
            "groups": [
                {"id": "ARCH", "relevance": "high", "reason": "Architecture - data ownership"},
                {"id": "CTL", "relevance": "high", "reason": "Control - security"}
            ],
            "features": {"required": ["F07", "F05"], "optional": ["F11"]},
            "tags": {"required": ["DB"], "optional": ["BE", "SECURITY"]}
        },
        "prompt": {
            "identity": "You are the Database Agent, responsible for safe database operations.",
            "critical_rules": [
                {"rule": "NEVER delete without backup", "severity": "blocking"},
                {"rule": "ALWAYS review migration before applying", "severity": "warning"}
            ]
        },
        "checklist": {
            "pre_deploy": [
                {"id": "backup", "step": "Backup existing data", "command": "pg_dump", "blocking": True}
            ],
            "deploy": [
                {"id": "migrate", "step": "Run migration", "command": "alembic upgrade head", "blocking": True}
            ],
            "post_deploy": [
                {"id": "verify", "step": "Verify schema", "command": "psql -c '\\dt'", "blocking": True}
            ]
        }
    },
    "backend": {
        "id": "backend-agent",
        "name": "Backend Development Agent",
        "description": "Handles backend API development with Clean Architecture",
        "version": "1.0.0",
        "category": "backend",
        "triggers": {
            "keywords": {
                "primary": ["backend", "api", "endpoint"],
                "secondary": ["service", "fastapi", "python", "route"]
            },
            "intents": ["BACKEND", "API_DEVELOPMENT"]
        },
        "decision_context": {
            "groups": [
                {"id": "ARCH", "relevance": "high"},
                {"id": "CTL", "relevance": "medium"},
                {"id": "STD", "relevance": "medium"}
            ],
            "features": {"required": ["F05", "F06", "F08"], "optional": ["F11"]},
            "tags": {"required": ["BE", "API"], "optional": ["SECURITY"]}
        },
        "prompt": {
            "identity": "You are the Backend Agent, ensuring Clean Architecture patterns.",
            "critical_rules": [
                {"rule": "Use repository pattern for data access", "severity": "warning"},
                {"rule": "Add authentication to new endpoints", "severity": "blocking"}
            ]
        },
        "checklist": {
            "pre_deploy": [
                {"id": "lint", "step": "Run linting", "command": "ruff check", "blocking": False},
                {"id": "tests", "step": "Run tests", "command": "pytest", "blocking": True}
            ]
        }
    },
    "frontend": {
        "id": "frontend-agent",
        "name": "Frontend Development Agent",
        "description": "Handles frontend development with React patterns",
        "version": "1.0.0",
        "category": "frontend",
        "triggers": {
            "keywords": {
                "primary": ["frontend", "react", "component"],
                "secondary": ["ui", "css", "page", "form"]
            },
            "intents": ["FRONTEND", "UI_DEVELOPMENT"]
        },
        "decision_context": {
            "groups": [
                {"id": "ARCH", "relevance": "high"},
                {"id": "STD", "relevance": "high"}
            ],
            "features": {"required": ["F06", "F08"], "optional": []},
            "tags": {"required": ["FE", "UI"], "optional": []}
        },
        "prompt": {
            "identity": "You are the Frontend Agent, ensuring consistent React patterns.",
            "critical_rules": [
                {"rule": "Follow component structure in /features", "severity": "warning"},
                {"rule": "Use shared components from /shared", "severity": "warning"}
            ]
        },
        "checklist": {
            "pre_deploy": [
                {"id": "typecheck", "step": "Run type check", "command": "bun tsc --noEmit", "blocking": True},
                {"id": "tests", "step": "Run tests", "command": "bun test", "blocking": True}
            ]
        }
    },
    "security": {
        "id": "security-agent",
        "name": "Security Review Agent",
        "description": "Reviews code for security vulnerabilities",
        "version": "1.0.0",
        "category": "security",
        "triggers": {
            "keywords": {
                "primary": ["security", "auth", "authentication"],
                "secondary": ["authorization", "permission", "vulnerability"]
            },
            "intents": ["SECURITY_REVIEW", "AUTH"]
        },
        "decision_context": {
            "groups": [
                {"id": "CTL", "relevance": "high"}
            ],
            "features": {"required": ["F11", "F12"], "optional": []},
            "tags": {"required": ["SECURITY"], "optional": []}
        },
        "prompt": {
            "identity": "You are the Security Agent, ensuring code is secure.",
            "critical_rules": [
                {"rule": "NEVER hardcode secrets", "severity": "blocking"},
                {"rule": "ALWAYS validate user input", "severity": "blocking"},
                {"rule": "Use parameterized queries", "severity": "blocking"}
            ]
        },
        "checklist": {
            "pre_deploy": [
                {"id": "secrets", "step": "Check for hardcoded secrets", "blocking": True},
                {"id": "auth", "step": "Review authentication", "blocking": True}
            ]
        }
    }
}


def get_builtin_agent(agent_id: str) -> Optional[AgentDefinition]:
    """Get a built-in agent definition."""
    # Handle various ID formats
    key = agent_id.replace("-agent", "").replace("_agent", "")

    if key not in BUILTIN_AGENTS:
        return None

    data = BUILTIN_AGENTS[key]
    loader = AgentLoader()
    return loader._parse_agent(data)


def get_all_builtin_agents() -> Dict[str, AgentDefinition]:
    """Get all built-in agents."""
    result = {}
    for key in BUILTIN_AGENTS:
        agent = get_builtin_agent(key)
        if agent:
            result[agent.id] = agent
    return result
