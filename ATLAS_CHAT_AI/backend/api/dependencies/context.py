"""
Context dependencies for FastAPI.
"""

from fastapi import Request, HTTPException

from ...core.entities import RequestContext, TenantConfig


async def get_context(request: Request) -> RequestContext:
    """
    Get RequestContext from request state.

    Usage:
        @router.get("/endpoint")
        async def endpoint(ctx: RequestContext = Depends(get_context)):
            ...
    """
    context = getattr(request.state, "context", None)
    if not context:
        raise HTTPException(
            status_code=500,
            detail="Request context not available"
        )
    return context


async def get_tenant_config(request: Request) -> TenantConfig:
    """
    Get TenantConfig from request state.

    Usage:
        @router.get("/endpoint")
        async def endpoint(tenant: TenantConfig = Depends(get_tenant_config)):
            ...
    """
    context = await get_context(request)
    if not context.tenant_config:
        raise HTTPException(
            status_code=400,
            detail="Tenant configuration not available"
        )
    return context.tenant_config


# Alias for backward compatibility
get_request_context = get_context
