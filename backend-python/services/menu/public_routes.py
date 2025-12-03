"""Menu Public API Routes - No authentication required"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import time
import hashlib

from shared.database import get_db
from shared.responses import success_response
from shared.config import settings
from shared.cache import cache as redis_cache

from .repositories import MenuRepository, MenuItemRepository, MenuViewRepository, MenuItemMediaRepository
from .use_cases import GetPublicMenuUseCase
from .dtos import PublicMenuItemListDTO
from services.auth.repositories.models import OrganizationModel
from loguru import logger

router = APIRouter(prefix="/api/v1/public/menu", tags=["public-menu"])


# ========== Analytics Consent ==========

# Cookie/header name for analytics consent
ANALYTICS_CONSENT_HEADER = "X-Analytics-Consent"
ANALYTICS_CONSENT_COOKIE = "analytics_consent"


def has_analytics_consent(request: Request) -> bool:
    """
    Check if user has given consent for analytics tracking.
    Consent can be provided via:
    1. X-Analytics-Consent header (value: "true" or "1")
    2. analytics_consent cookie (value: "true" or "1")

    If no consent signal, default to NO tracking (privacy by default).
    """
    # Check header first
    consent_header = request.headers.get(ANALYTICS_CONSENT_HEADER, "").lower()
    if consent_header in ("true", "1", "yes"):
        return True

    # Check cookie
    consent_cookie = request.cookies.get(ANALYTICS_CONSENT_COOKIE, "").lower()
    if consent_cookie in ("true", "1", "yes"):
        return True

    return False


# ========== Rate Limiting ==========

# Rate limit: 60 requests per minute per IP
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60  # seconds


async def check_rate_limit(request: Request) -> bool:
    """
    Check if request is within rate limits.
    Uses sliding window algorithm with Redis.
    Returns True if allowed, raises HTTPException if rate limited.
    """
    if not request.client:
        return True

    client_ip = request.client.host
    cache_key = f"rate_limit:public_menu:{client_ip}"

    try:
        # Try to get current count from Redis
        current_count = redis_cache.get(cache_key)

        if current_count is None:
            # First request in window
            redis_cache.set(cache_key, 1, ttl=RATE_LIMIT_WINDOW)
            return True

        current_count = int(current_count)

        if current_count >= RATE_LIMIT_REQUESTS:
            logger.warning(f"[RateLimit] IP {client_ip} exceeded rate limit ({current_count}/{RATE_LIMIT_REQUESTS})")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please wait before making more requests.",
                    "retry_after": RATE_LIMIT_WINDOW
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
            )

        # Increment counter
        redis_cache.set(cache_key, current_count + 1, ttl=RATE_LIMIT_WINDOW)
        return True

    except HTTPException:
        raise
    except Exception as e:
        # If Redis fails, allow request (fail open)
        logger.error(f"[RateLimit] Redis error: {e}")
        return True


# ========== Dependency Injection ==========

def get_menu_repository(db: Session = Depends(get_db)) -> MenuRepository:
    """Inject menu repository"""
    return MenuRepository(db)


def get_menu_item_repository(db: Session = Depends(get_db)) -> MenuItemRepository:
    """Inject menu item repository"""
    return MenuItemRepository(db)


def get_menu_view_repository(db: Session = Depends(get_db)) -> MenuViewRepository:
    """Inject menu view repository"""
    return MenuViewRepository(db)


def get_menu_item_media_repository(db: Session = Depends(get_db)) -> MenuItemMediaRepository:
    """Inject menu item media repository"""
    return MenuItemMediaRepository(db)


def extract_client_info(request: Request) -> dict:
    """Extract client IP, user agent, and device type from request"""
    # Get client IP
    client_ip = None
    if request.client:
        client_ip = request.client.host

    # Get user agent
    user_agent = request.headers.get("user-agent", None)

    # Simple device type detection
    device_type = None
    if user_agent:
        ua_lower = user_agent.lower()
        if any(x in ua_lower for x in ["mobile", "android", "iphone"]):
            device_type = "mobile"
        elif any(x in ua_lower for x in ["tablet", "ipad"]):
            device_type = "tablet"
        else:
            device_type = "desktop"

    return {
        "viewer_ip": client_ip,
        "user_agent": user_agent,
        "device_type": device_type
    }


# ========== Public Endpoints ==========

@router.get("/{public_url_code}")
async def get_public_menu(
    public_url_code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    request: Request = None,
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    menu_view_repo: MenuViewRepository = Depends(get_menu_view_repository),
    menu_item_media_repo: MenuItemMediaRepository = Depends(get_menu_item_media_repository)
):
    """
    Get menu and items by public URL code (no authentication)

    This endpoint is used by the public menu viewer.
    Analytics tracking only occurs if user has given consent (GDPR compliance).
    Rate limited: 60 requests/minute per IP.
    """
    # Rate limiting
    await check_rate_limit(request)

    # Only extract and pass analytics data if user consented (GDPR compliance)
    if request and has_analytics_consent(request):
        client_info = extract_client_info(request)
        viewer_ip = _anonymize_ip(client_info.get("viewer_ip"))  # Always anonymize
        user_agent = client_info.get("user_agent")
        device_type = client_info.get("device_type")
    else:
        viewer_ip = None
        user_agent = None
        device_type = None

    # Execute use case
    use_case = GetPublicMenuUseCase(menu_repo, menu_item_repo, menu_view_repo, menu_item_media_repo)

    try:
        result = await use_case.execute(
            public_url_code=public_url_code,
            skip=skip,
            limit=limit,
            category=category,
            viewer_ip=viewer_ip,
            user_agent=user_agent,
            device_type=device_type
        )

        return success_response(data=result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{public_url_code}/track-contact")
async def track_contact_click(
    public_url_code: str,
    contact_type: str = Query(..., pattern="^(whatsapp|phone)$"),
    request: Request = None,
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_view_repo: MenuViewRepository = Depends(get_menu_view_repository)
):
    """
    Track contact button click (WhatsApp or Phone)
    Rate limited: 60 requests/minute per IP.
    Only tracks if user has given analytics consent (GDPR compliance).

    This is called when user clicks on contact buttons in public viewer.
    """
    # Rate limiting
    await check_rate_limit(request)

    # Find menu
    menu = menu_repo.find_by_public_code(public_url_code)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Only track if user has given consent (GDPR compliance)
    if request and has_analytics_consent(request):
        # Extract client info with anonymization
        client_info = extract_client_info(request)

        # Track contact click
        menu_view_repo.track_view(
            menu_id=menu.id,
            organization_id=menu.organization_id,
            viewer_ip=_anonymize_ip(client_info.get("viewer_ip")),  # Anonymized
            user_agent=client_info.get("user_agent"),
            device_type=client_info.get("device_type"),
            contact_clicked=True,
            contact_type=contact_type
        )
        return success_response(data={"tracked": True})
    else:
        # No consent - don't track but still return success
        return success_response(data={"tracked": False, "reason": "no_consent"})


# ========== Analytics Consent Endpoint ==========

@router.post("/consent")
async def set_analytics_consent(
    consent: bool = Query(..., description="True to accept analytics, False to decline"),
    request: Request = None
):
    """
    Set analytics consent preference.
    Returns a response that sets the consent cookie.

    This endpoint allows users to:
    - Accept analytics tracking (consent=true)
    - Decline analytics tracking (consent=false)

    The consent is stored in a cookie that expires in 1 year.
    """
    from fastapi.responses import JSONResponse

    response = JSONResponse(content={
        "success": True,
        "data": {
            "consent": consent,
            "message": "Analytics consent preference saved"
        }
    })

    # Set consent cookie (1 year expiry)
    cookie_value = "true" if consent else "false"
    response.set_cookie(
        key=ANALYTICS_CONSENT_COOKIE,
        value=cookie_value,
        max_age=365 * 24 * 60 * 60,  # 1 year
        httponly=False,  # Allow JavaScript access for UI state
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )

    return response


# ========== Portal Endpoint (All Menus for Organization) ==========

@router.get("/portal/{portal_slug}")
async def get_portal_menus(
    portal_slug: str,
    request: Request = None,
    db: Session = Depends(get_db),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_view_repo: MenuViewRepository = Depends(get_menu_view_repository)
):
    """
    Get all active menus for an organization portal.

    This endpoint returns organization info and a list of all active menus
    for the unified menu portal view.
    Rate limited: 60 requests/minute per IP.
    Analytics tracking: Portal views are logged for business intelligence.

    URL format: /api/v1/public/menu/portal/{portal_slug}
    Example: /api/v1/public/menu/portal/hotel-signage-demo-22
    """
    # Rate limiting
    await check_rate_limit(request)

    # Find organization by portal_slug
    org = db.query(OrganizationModel).filter(
        OrganizationModel.portal_slug == portal_slug,
        OrganizationModel.is_active == True
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Portal not found")

    # Only track analytics if user has given consent (GDPR compliance)
    if request and has_analytics_consent(request):
        # Extract client info for analytics
        client_info = extract_client_info(request)

        # Track portal view using Redis counters (fast, no DB migration needed)
        try:
            # Track total portal views (daily counter)
            today = datetime.now().strftime("%Y-%m-%d")
            portal_view_key = f"portal_views:{org.id}:{portal_slug}:{today}"
            redis_cache.increment(portal_view_key, ttl=86400 * 30)  # Keep for 30 days

            # Track unique visitors (using anonymized IP hash)
            if client_info.get("viewer_ip"):
                anon_ip = _anonymize_ip(client_info.get("viewer_ip"))
                visitor_hash = hashlib.md5(f"{portal_slug}:{anon_ip}:{today}".encode()).hexdigest()[:8]
                unique_key = f"portal_unique:{org.id}:{portal_slug}:{today}"
                redis_cache.add_to_set(unique_key, visitor_hash, ttl=86400)

            # Track device distribution
            device = client_info.get("device_type") or "unknown"
            device_key = f"portal_devices:{org.id}:{portal_slug}:{today}:{device}"
            redis_cache.increment(device_key, ttl=86400 * 30)

            logger.debug(f"[PortalAnalytics] Tracked view for portal: {portal_slug} (consent given)")
        except Exception as e:
            # Don't fail request if analytics fails
            logger.warning(f"[PortalAnalytics] Failed to track portal view: {e}")
    else:
        logger.debug(f"[PortalAnalytics] Skipped tracking for portal: {portal_slug} (no consent)")

    # Get all active menus for this organization
    from .repositories.models import MenuModel

    menus = db.query(MenuModel).filter(
        MenuModel.organization_id == org.id,
        MenuModel.is_active == True,
        MenuModel.deleted_at.is_(None)
    ).order_by(
        MenuModel.name.asc()  # Order by name alphabetically
    ).all()

    # Build response with menu URLs
    player_url = settings.PLAYER_URL

    menu_list = []
    for menu in menus:
        menu_list.append({
            "id": menu.id,
            "name": menu.name,
            "menu_type": menu.menu_type,
            "tab_name": menu.tab_name,  # Custom tab label for portal
            "public_url_code": menu.public_url_code,
            "public_url": f"{player_url}/menu/{menu.public_url_code}",
            "description": menu.description,
            "display_mode": menu.display_mode,
            "primary_color": menu.primary_color,
            "secondary_color": menu.secondary_color,
            "theme_color": menu.theme_color,
            "outlet_extension": menu.outlet_extension  # Phone extension badge
        })

    return success_response(data={
        "organization": {
            "id": org.id,
            "name": org.name,
            "portal_slug": org.portal_slug,
            "logo_url": org.logo_url
        },
        "menus": menu_list,
        "total": len(menu_list)
    })


def _anonymize_ip(ip: Optional[str]) -> Optional[str]:
    """
    Anonymize IP address for GDPR compliance.
    IPv4: Remove last octet (e.g., 192.168.1.100 -> 192.168.1.0)
    IPv6: Remove last 80 bits
    """
    if not ip:
        return None

    try:
        if ":" in ip:  # IPv6
            parts = ip.split(":")
            if len(parts) >= 4:
                return ":".join(parts[:4]) + "::"
        else:  # IPv4
            parts = ip.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
    except Exception:
        pass

    return None  # Return None if we can't anonymize properly
