"""
Admin API Routes

Endpoints for tenant, user, and system management.
Requires admin permissions.
"""

from typing import Optional, List
from datetime import datetime
from uuid import uuid4
import hashlib
import secrets

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from pydantic import BaseModel, Field, EmailStr

from ..dependencies.context import get_request_context
from ...core.entities import RequestContext
from ...container import get_container
from ...shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Permission Check
# =============================================================================

async def require_admin(ctx: RequestContext = Depends(get_request_context)):
    """Dependency that requires admin permission."""
    if "admin" not in ctx.permissions and ctx.user_id != "system":
        raise HTTPException(403, "Admin permission required")
    return ctx


# =============================================================================
# Tenant Management Schemas
# =============================================================================

class TenantCreate(BaseModel):
    """Create tenant request."""
    id: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    system_prompt: Optional[str] = Field(None, max_length=10000)
    max_sessions_per_user: int = Field(100, ge=1, le=10000)
    max_messages_per_session: int = Field(1000, ge=10, le=100000)
    llm_provider: str = Field("openai")
    llm_model: str = Field("gpt-4o-mini")
    llm_temperature: float = Field(0.7, ge=0, le=2)
    llm_max_tokens: int = Field(2000, ge=100, le=32000)
    rag_enabled: bool = Field(True)
    rag_top_k: int = Field(5, ge=1, le=20)
    rag_score_threshold: float = Field(0.5, ge=0, le=1)


class TenantUpdate(BaseModel):
    """Update tenant request."""
    name: Optional[str] = Field(None, max_length=200)
    system_prompt: Optional[str] = Field(None, max_length=10000)
    max_sessions_per_user: Optional[int] = Field(None, ge=1, le=10000)
    max_messages_per_session: Optional[int] = Field(None, ge=10, le=100000)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = Field(None, ge=0, le=2)
    llm_max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    rag_enabled: Optional[bool] = None
    rag_top_k: Optional[int] = Field(None, ge=1, le=20)
    rag_score_threshold: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class TenantResponse(BaseModel):
    """Tenant response."""
    id: str
    name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stats: Optional[dict] = None


# =============================================================================
# User Management Schemas
# =============================================================================

class UserCreate(BaseModel):
    """Create user request."""
    external_user_id: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    display_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field("user", pattern=r"^(admin|user|readonly)$")
    custom_permissions: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Update user request."""
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, pattern=r"^(admin|user|readonly)$")
    custom_permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response."""
    id: str
    tenant_id: str
    external_user_id: str
    email: Optional[str] = None
    display_name: str
    role: str
    is_active: bool
    last_seen_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


# =============================================================================
# API Key Management Schemas
# =============================================================================

class APIKeyCreate(BaseModel):
    """Create API key request."""
    name: str = Field(..., min_length=1, max_length=200)
    permissions: List[str] = Field(default_factory=lambda: ["chat.read", "chat.write"])
    rate_limit_per_minute: int = Field(100, ge=1, le=10000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response (without full key)."""
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    permissions: List[str]
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: Optional[datetime] = None


class APIKeyCreatedResponse(BaseModel):
    """API key creation response (includes full key - only shown once)."""
    id: str
    name: str
    key: str  # Full key - only returned on creation
    key_prefix: str
    permissions: List[str]
    expires_at: Optional[datetime] = None


# =============================================================================
# Tenant Endpoints
# =============================================================================

@router.get("/tenants")
async def list_tenants(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_inactive: bool = Query(False),
    ctx: RequestContext = Depends(require_admin),
):
    """List all tenants."""
    container = await get_container()

    tenants = await container.tenant_repository.list_all(
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )

    return {
        "success": True,
        "data": [
            TenantResponse(
                id=t.id,
                name=t.name,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ],
        "meta": {"limit": limit, "offset": offset},
    }


@router.post("/tenants")
async def create_tenant(
    request: TenantCreate,
    ctx: RequestContext = Depends(require_admin),
):
    """Create a new tenant."""
    container = await get_container()

    # Check if tenant ID already exists
    existing = await container.tenant_repository.get_by_id(request.id)
    if existing:
        raise HTTPException(409, f"Tenant '{request.id}' already exists")

    # Create tenant config
    from ...core.entities import TenantConfig, LLMConfig, RAGConfig

    tenant = TenantConfig(
        id=request.id,
        name=request.name,
        system_prompt=request.system_prompt or f"You are a helpful assistant for {request.name}.",
        max_sessions_per_user=request.max_sessions_per_user,
        max_messages_per_session=request.max_messages_per_session,
        llm_config=LLMConfig(
            provider=request.llm_provider,
            model=request.llm_model,
            temperature=request.llm_temperature,
            max_tokens=request.llm_max_tokens,
        ),
        rag_config=RAGConfig(
            enabled=request.rag_enabled,
            top_k=request.rag_top_k,
            score_threshold=request.rag_score_threshold,
        ),
    )

    await container.tenant_repository.create(tenant)

    logger.info(f"Created tenant: {request.id}")

    return {
        "success": True,
        "data": TenantResponse(
            id=tenant.id,
            name=tenant.name,
            is_active=tenant.is_active,
        ),
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str = Path(..., min_length=1),
    include_stats: bool = Query(False),
    ctx: RequestContext = Depends(require_admin),
):
    """Get tenant details."""
    container = await get_container()

    tenant = await container.tenant_repository.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")

    stats = None
    if include_stats:
        stats = await _get_tenant_stats(container, tenant_id)

    return {
        "success": True,
        "data": TenantResponse(
            id=tenant.id,
            name=tenant.name,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            stats=stats,
        ),
    }


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    request: TenantUpdate,
    tenant_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Update tenant configuration."""
    container = await get_container()

    tenant = await container.tenant_repository.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")

    # Update fields
    updates = request.model_dump(exclude_unset=True)
    if updates:
        await container.tenant_repository.update_fields(tenant_id, updates)

    logger.info(f"Updated tenant: {tenant_id}")

    return {"success": True, "data": {"updated": True}}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Soft-delete a tenant."""
    container = await get_container()

    tenant = await container.tenant_repository.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")

    await container.tenant_repository.soft_delete(tenant_id)

    logger.info(f"Deleted tenant: {tenant_id}")

    return {"success": True, "data": {"deleted": True}}


# =============================================================================
# User Endpoints
# =============================================================================

@router.get("/tenants/{tenant_id}/users")
async def list_users(
    tenant_id: str = Path(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role: Optional[str] = Query(None),
    ctx: RequestContext = Depends(require_admin),
):
    """List users for a tenant."""
    container = await get_container()

    users = await container.user_repository.list_by_tenant(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        role=role,
    )

    return {
        "success": True,
        "data": [
            UserResponse(
                id=str(u.id),
                tenant_id=u.tenant_id,
                external_user_id=u.external_user_id,
                email=u.email,
                display_name=u.display_name,
                role=u.role,
                is_active=u.is_active,
                last_seen_at=u.last_seen_at,
                created_at=u.created_at,
            )
            for u in users
        ],
        "meta": {"tenant_id": tenant_id, "limit": limit, "offset": offset},
    }


@router.post("/tenants/{tenant_id}/users")
async def create_user(
    request: UserCreate,
    tenant_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Create a user for a tenant."""
    container = await get_container()

    # Check tenant exists
    tenant = await container.tenant_repository.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")

    # Check user doesn't already exist
    existing = await container.user_repository.get_by_external_id(
        tenant_id=tenant_id,
        external_user_id=request.external_user_id,
    )
    if existing:
        raise HTTPException(409, f"User '{request.external_user_id}' already exists")

    # Create user
    from ...core.entities import User, UserProfile

    user = User(
        tenant_id=tenant_id,
        external_user_id=request.external_user_id,
        profile=UserProfile(
            display_name=request.display_name,
            email=request.email,
        ),
        role=request.role,
        custom_permissions=request.custom_permissions,
    )

    user_id = await container.user_repository.create(user)

    logger.info(f"Created user: {request.external_user_id} for tenant {tenant_id}")

    return {
        "success": True,
        "data": {"user_id": user_id},
    }


@router.get("/tenants/{tenant_id}/users/{user_id}")
async def get_user(
    tenant_id: str = Path(..., min_length=1),
    user_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Get user details."""
    container = await get_container()

    user = await container.user_repository.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(404, f"User not found")

    return {
        "success": True,
        "data": UserResponse(
            id=str(user.id),
            tenant_id=user.tenant_id,
            external_user_id=user.external_user_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            last_seen_at=user.last_seen_at,
            created_at=user.created_at,
        ),
    }


@router.patch("/tenants/{tenant_id}/users/{user_id}")
async def update_user(
    request: UserUpdate,
    tenant_id: str = Path(..., min_length=1),
    user_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Update user."""
    container = await get_container()

    user = await container.user_repository.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(404, f"User not found")

    updates = request.model_dump(exclude_unset=True)
    if updates:
        await container.user_repository.update_fields(user_id, tenant_id, updates)

    return {"success": True, "data": {"updated": True}}


@router.delete("/tenants/{tenant_id}/users/{user_id}")
async def delete_user(
    tenant_id: str = Path(..., min_length=1),
    user_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Soft-delete a user."""
    container = await get_container()

    user = await container.user_repository.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(404, f"User not found")

    await container.user_repository.soft_delete(user_id, tenant_id)

    return {"success": True, "data": {"deleted": True}}


# =============================================================================
# API Key Endpoints
# =============================================================================

@router.get("/tenants/{tenant_id}/api-keys")
async def list_api_keys(
    tenant_id: str = Path(..., min_length=1),
    include_inactive: bool = Query(False),
    ctx: RequestContext = Depends(require_admin),
):
    """List API keys for a tenant."""
    container = await get_container()

    pool = container.db_pool.pool
    async with pool.acquire() as conn:
        query = """
            SELECT id, tenant_id, name, key_prefix, permissions,
                   rate_limit_per_minute, expires_at, last_used_at,
                   is_active, created_at
            FROM api_keys
            WHERE tenant_id = $1
        """
        if not include_inactive:
            query += " AND is_active = TRUE"
        query += " ORDER BY created_at DESC"

        rows = await conn.fetch(query, tenant_id)

    import json

    return {
        "success": True,
        "data": [
            APIKeyResponse(
                id=str(row["id"]),
                tenant_id=row["tenant_id"],
                name=row["name"],
                key_prefix=row["key_prefix"],
                permissions=json.loads(row["permissions"]) if isinstance(row["permissions"], str) else row["permissions"],
                rate_limit_per_minute=row["rate_limit_per_minute"],
                expires_at=row["expires_at"],
                last_used_at=row["last_used_at"],
                is_active=row["is_active"],
                created_at=row["created_at"],
            )
            for row in rows
        ],
    }


@router.post("/tenants/{tenant_id}/api-keys")
async def create_api_key(
    request: APIKeyCreate,
    tenant_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """
    Create a new API key.

    Returns the full key only once - store it securely!
    """
    container = await get_container()

    # Check tenant exists
    tenant = await container.tenant_repository.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(404, f"Tenant '{tenant_id}' not found")

    # Generate key
    key = f"sk_{tenant_id}_{secrets.token_urlsafe(32)}"
    key_prefix = key[:12]
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    # Calculate expiry
    expires_at = None
    if request.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Insert into database
    import json

    pool = container.db_pool.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO api_keys (
                tenant_id, name, key_prefix, key_hash, permissions,
                rate_limit_per_minute, expires_at, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, created_at
            """,
            tenant_id,
            request.name,
            key_prefix,
            key_hash,
            json.dumps(request.permissions),
            request.rate_limit_per_minute,
            expires_at,
            ctx.user_id,
        )

    logger.info(f"Created API key '{request.name}' for tenant {tenant_id}")

    return {
        "success": True,
        "data": APIKeyCreatedResponse(
            id=str(row["id"]),
            name=request.name,
            key=key,  # Full key - only returned here!
            key_prefix=key_prefix,
            permissions=request.permissions,
            expires_at=expires_at,
        ),
    }


@router.delete("/tenants/{tenant_id}/api-keys/{key_id}")
async def revoke_api_key(
    tenant_id: str = Path(..., min_length=1),
    key_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Revoke an API key."""
    container = await get_container()

    pool = container.db_pool.pool
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE api_keys
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            key_id,
            tenant_id,
        )

    if result == "UPDATE 0":
        raise HTTPException(404, "API key not found")

    logger.info(f"Revoked API key {key_id} for tenant {tenant_id}")

    return {"success": True, "data": {"revoked": True}}


# =============================================================================
# System Stats Endpoints
# =============================================================================

@router.get("/stats")
async def get_system_stats(
    ctx: RequestContext = Depends(require_admin),
):
    """Get system-wide statistics."""
    container = await get_container()

    pool = container.db_pool.pool
    async with pool.acquire() as conn:
        # Get counts
        tenant_count = await conn.fetchval("SELECT COUNT(*) FROM tenants WHERE is_active = TRUE")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        session_count = await conn.fetchval("SELECT COUNT(*) FROM chat_sessions WHERE is_deleted = FALSE")
        message_count = await conn.fetchval("SELECT COUNT(*) FROM chat_messages WHERE is_deleted = FALSE")

        # Get recent activity
        active_sessions_24h = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_sessions WHERE updated_at > NOW() - INTERVAL '24 hours'"
        )
        messages_24h = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_messages WHERE created_at > NOW() - INTERVAL '24 hours'"
        )

    # Health check
    health = await container.health_check()

    return {
        "success": True,
        "data": {
            "totals": {
                "tenants": tenant_count,
                "users": user_count,
                "sessions": session_count,
                "messages": message_count,
            },
            "last_24h": {
                "active_sessions": active_sessions_24h,
                "messages": messages_24h,
            },
            "health": health,
        },
    }


@router.get("/stats/tenants/{tenant_id}")
async def get_tenant_stats(
    tenant_id: str = Path(..., min_length=1),
    ctx: RequestContext = Depends(require_admin),
):
    """Get statistics for a specific tenant."""
    container = await get_container()

    stats = await _get_tenant_stats(container, tenant_id)

    return {
        "success": True,
        "data": stats,
    }


# =============================================================================
# Helpers
# =============================================================================

async def _get_tenant_stats(container, tenant_id: str) -> dict:
    """Get statistics for a tenant."""
    pool = container.db_pool.pool

    async with pool.acquire() as conn:
        user_count = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE tenant_id = $1 AND is_active = TRUE",
            tenant_id,
        )
        session_count = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_sessions WHERE tenant_id = $1 AND is_deleted = FALSE",
            tenant_id,
        )
        message_count = await conn.fetchval(
            "SELECT COUNT(*) FROM chat_messages WHERE tenant_id = $1 AND is_deleted = FALSE",
            tenant_id,
        )
        fact_count = await conn.fetchval(
            "SELECT COUNT(*) FROM user_facts WHERE tenant_id = $1 AND is_active = TRUE",
            tenant_id,
        )

        # Recent activity
        active_users_7d = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT user_id) FROM chat_sessions
            WHERE tenant_id = $1 AND updated_at > NOW() - INTERVAL '7 days'
            """,
            tenant_id,
        )

    return {
        "tenant_id": tenant_id,
        "users": user_count,
        "sessions": session_count,
        "messages": message_count,
        "facts": fact_count,
        "active_users_7d": active_users_7d,
    }
