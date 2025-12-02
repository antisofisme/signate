"""Menu Public API Routes - No authentication required"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List

from shared.database import get_db
from shared.responses import success_response
from shared.config import settings

from .repositories import MenuRepository, MenuItemRepository, MenuViewRepository, MenuItemMediaRepository
from .use_cases import GetPublicMenuUseCase
from .dtos import PublicMenuItemListDTO
from services.auth.repositories.models import OrganizationModel

router = APIRouter(prefix="/api/v1/public/menu", tags=["public-menu"])


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
    Analytics tracking is done asynchronously without blocking response.
    """
    # Extract client info for analytics
    client_info = extract_client_info(request)

    # Execute use case
    use_case = GetPublicMenuUseCase(menu_repo, menu_item_repo, menu_view_repo, menu_item_media_repo)

    try:
        result = await use_case.execute(
            public_url_code=public_url_code,
            skip=skip,
            limit=limit,
            category=category,
            viewer_ip=client_info["viewer_ip"],
            user_agent=client_info["user_agent"],
            device_type=client_info["device_type"]
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

    This is called when user clicks on contact buttons in public viewer.
    """
    # Find menu
    menu = menu_repo.find_by_public_code(public_url_code)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Extract client info
    client_info = extract_client_info(request)

    # Track contact click
    menu_view_repo.track_view(
        menu_id=menu.id,
        organization_id=menu.organization_id,
        viewer_ip=client_info["viewer_ip"],
        user_agent=client_info["user_agent"],
        device_type=client_info["device_type"],
        contact_clicked=True,
        contact_type=contact_type
    )

    return success_response(data={"tracked": True})


# ========== Portal Endpoint (All Menus for Organization) ==========

@router.get("/portal/{portal_slug}")
async def get_portal_menus(
    portal_slug: str,
    db: Session = Depends(get_db),
    menu_repo: MenuRepository = Depends(get_menu_repository)
):
    """
    Get all active menus for an organization portal.

    This endpoint returns organization info and a list of all active menus
    for the unified menu portal view.

    URL format: /api/v1/public/menu/portal/{portal_slug}
    Example: /api/v1/public/menu/portal/hotel-signage-demo-22
    """
    # Find organization by portal_slug
    org = db.query(OrganizationModel).filter(
        OrganizationModel.portal_slug == portal_slug,
        OrganizationModel.is_active == True
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Portal not found")

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
            "public_url_code": menu.public_url_code,
            "public_url": f"{player_url}/menu/{menu.public_url_code}",
            "description": menu.description,
            "display_mode": menu.display_mode,
            "primary_color": menu.primary_color,
            "secondary_color": menu.secondary_color,
            "theme_color": menu.theme_color
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
