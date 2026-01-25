"""
Tenant repository.
"""

from typing import Optional, List
import json

from .base_repository import BaseRepository
from ....core.entities import (
    TenantConfig, LLMConfig, EmbeddingConfig, RAGConfig, TenantFeatures
)
from ....shared.logging import get_logger

logger = get_logger(__name__)


class TenantRepository(BaseRepository[TenantConfig]):
    """Repository for tenant operations."""

    def __init__(self, pool):
        super().__init__(pool, "tenants")

    def _row_to_entity(self, row) -> TenantConfig:
        """Convert database row to TenantConfig."""
        llm_config = row["llm_config"] or {}
        embedding_config = row["embedding_config"] or {}
        rag_config = row["rag_config"] or {}
        features = row["features"] or {}

        return TenantConfig(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            llm_config=LLMConfig(
                provider=llm_config.get("provider", "openai"),
                model=llm_config.get("model", "gpt-4o-mini"),
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 1000),
            ),
            embedding_config=EmbeddingConfig(
                provider=embedding_config.get("provider", "openai"),
                model=embedding_config.get("model", "text-embedding-3-small"),
                dimensions=embedding_config.get("dimensions", 1536),
            ),
            rag_config=RAGConfig(
                strategy=rag_config.get("strategy", "hybrid"),
                reranker_enabled=rag_config.get("reranker_enabled", False),
                reranker_provider=rag_config.get("reranker_provider"),
                top_k=rag_config.get("top_k", 5),
                score_threshold=rag_config.get("score_threshold", 0.3),
            ),
            system_prompt=row["system_prompt"],
            persona_name=row["persona_name"],
            max_context_tokens=row["max_context_tokens"],
            max_response_tokens=row["max_response_tokens"],
            max_messages_per_session=row["max_messages_per_session"],
            max_sessions_per_user=row["max_sessions_per_user"],
            features=TenantFeatures(
                memory_extraction=features.get("memory_extraction", True),
                temporal_memory=features.get("temporal_memory", True),
                streaming=features.get("streaming", True),
                session_summarization=features.get("session_summarization", True),
            ),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, config: TenantConfig) -> str:
        """Create a new tenant."""
        query = """
            INSERT INTO tenants (
                id, name, description,
                llm_config, embedding_config, rag_config,
                system_prompt, persona_name,
                max_context_tokens, max_response_tokens,
                max_messages_per_session, max_sessions_per_user,
                features, is_active
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            )
            RETURNING id
        """

        llm_config = {
            "provider": config.llm_config.provider,
            "model": config.llm_config.model,
            "temperature": config.llm_config.temperature,
            "max_tokens": config.llm_config.max_tokens,
        }
        embedding_config = {
            "provider": config.embedding_config.provider,
            "model": config.embedding_config.model,
            "dimensions": config.embedding_config.dimensions,
        }
        rag_config = {
            "strategy": config.rag_config.strategy,
            "reranker_enabled": config.rag_config.reranker_enabled,
            "reranker_provider": config.rag_config.reranker_provider,
            "top_k": config.rag_config.top_k,
            "score_threshold": config.rag_config.score_threshold,
        }
        features = {
            "memory_extraction": config.features.memory_extraction,
            "temporal_memory": config.features.temporal_memory,
            "streaming": config.features.streaming,
            "session_summarization": config.features.session_summarization,
        }

        result = await self._fetchval(
            query,
            config.id, config.name, config.description,
            json.dumps(llm_config), json.dumps(embedding_config), json.dumps(rag_config),
            config.system_prompt, config.persona_name,
            config.max_context_tokens, config.max_response_tokens,
            config.max_messages_per_session, config.max_sessions_per_user,
            json.dumps(features), config.is_active
        )

        logger.info(f"Created tenant: {config.id}")
        return result

    async def get_by_id(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant by ID."""
        query = "SELECT * FROM tenants WHERE id = $1"
        row = await self._fetchrow(query, tenant_id)
        return self._row_to_entity(row) if row else None

    async def get_active(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get active tenant by ID."""
        query = "SELECT * FROM tenants WHERE id = $1 AND is_active = TRUE"
        row = await self._fetchrow(query, tenant_id)
        return self._row_to_entity(row) if row else None

    async def update(self, config: TenantConfig) -> bool:
        """Update tenant configuration."""
        query = """
            UPDATE tenants SET
                name = $2, description = $3,
                llm_config = $4, embedding_config = $5, rag_config = $6,
                system_prompt = $7, persona_name = $8,
                max_context_tokens = $9, max_response_tokens = $10,
                max_messages_per_session = $11, max_sessions_per_user = $12,
                features = $13, is_active = $14,
                updated_at = NOW()
            WHERE id = $1
        """

        llm_config = json.dumps({
            "provider": config.llm_config.provider,
            "model": config.llm_config.model,
            "temperature": config.llm_config.temperature,
            "max_tokens": config.llm_config.max_tokens,
        })
        embedding_config = json.dumps({
            "provider": config.embedding_config.provider,
            "model": config.embedding_config.model,
            "dimensions": config.embedding_config.dimensions,
        })
        rag_config = json.dumps({
            "strategy": config.rag_config.strategy,
            "reranker_enabled": config.rag_config.reranker_enabled,
            "reranker_provider": config.rag_config.reranker_provider,
            "top_k": config.rag_config.top_k,
            "score_threshold": config.rag_config.score_threshold,
        })
        features = json.dumps({
            "memory_extraction": config.features.memory_extraction,
            "temporal_memory": config.features.temporal_memory,
            "streaming": config.features.streaming,
            "session_summarization": config.features.session_summarization,
        })

        result = await self._execute(
            query,
            config.id, config.name, config.description,
            llm_config, embedding_config, rag_config,
            config.system_prompt, config.persona_name,
            config.max_context_tokens, config.max_response_tokens,
            config.max_messages_per_session, config.max_sessions_per_user,
            features, config.is_active
        )

        return "UPDATE 1" in result

    async def deactivate(self, tenant_id: str) -> bool:
        """Deactivate a tenant."""
        query = """
            UPDATE tenants SET is_active = FALSE, updated_at = NOW()
            WHERE id = $1 AND is_active = TRUE
        """
        result = await self._execute(query, tenant_id)
        return "UPDATE 1" in result

    async def soft_delete(self, tenant_id: str) -> bool:
        """Soft-delete a tenant (same as deactivate)."""
        return await self.deactivate(tenant_id)

    async def list_all(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
        include_inactive: bool = False,
    ) -> List[TenantConfig]:
        """List all tenants."""
        conditions = []
        if not include_inactive and active_only:
            conditions.append("is_active = TRUE")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT * FROM tenants
            {where_clause}
            ORDER BY name
            LIMIT $1 OFFSET $2
        """

        rows = await self._fetch(query, limit, offset)
        return [self._row_to_entity(row) for row in rows]

    async def update_fields(self, tenant_id: str, updates: dict) -> bool:
        """Update specific tenant fields."""
        if not updates:
            return True

        # Handle simple fields
        set_clauses = []
        params = [tenant_id]
        param_idx = 2

        simple_fields = ["name", "description", "system_prompt", "persona_name",
                        "max_context_tokens", "max_response_tokens",
                        "max_messages_per_session", "max_sessions_per_user", "is_active"]

        for key in simple_fields:
            if key in updates:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(updates[key])
                param_idx += 1

        # Handle nested config fields
        if any(k.startswith("llm_") for k in updates):
            # Would need to fetch current and merge
            pass

        if not set_clauses:
            return True

        set_clauses.append("updated_at = NOW()")

        query = f"""
            UPDATE tenants SET {', '.join(set_clauses)}
            WHERE id = $1
        """

        result = await self._execute(query, *params)
        return "UPDATE 1" in result

    async def exists(self, tenant_id: str) -> bool:
        """Check if tenant exists and is active."""
        query = "SELECT 1 FROM tenants WHERE id = $1 AND is_active = TRUE"
        result = await self._fetchval(query, tenant_id)
        return result is not None
