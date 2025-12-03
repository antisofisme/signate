"""Menu API Routes - Admin endpoints (authenticated)"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO

from shared.database import get_db
from shared.responses import success_response
from shared.logging import AuditLogger
from shared.auth import get_current_user, CurrentUser
from shared.config import settings
from shared.rbac import require_permission

from .repositories import (
    MenuRepository,
    MenuItemRepository,
    MenuImportHistoryRepository,
    MenuViewRepository,
    MenuCategoryRepository,
    MenuItemMediaRepository
)
from .infrastructure import QRCodeGenerator, ExcelImporter, ExcelExporter
from .use_cases import CreateMenuUseCase, BulkImportItemsUseCase
from .dtos import (
    MenuCreateDTO,
    MenuUpdateDTO,
    MenuResponseDTO,
    MenuListResponseDTO,
    MenuItemCreateDTO,
    MenuItemUpdateDTO,
    MenuItemResponseDTO,
    MenuItemListResponseDTO,
    MenuItemReorderDTO,
    MenuImportResultDTO,
    MenuImportHistoryListDTO,
    MenuItemMediaSimpleDTO,
    # Category DTOs
    MenuCategoryCreateDTO,
    MenuCategoryUpdateDTO,
    MenuCategoryResponseDTO,
    MenuCategoryListDTO,
    MenuCategoryReorderDTO,
    # Menu Item Media DTOs
    MenuItemMediaAddDTO,
    MenuItemMediaResponseDTO,
    MenuItemMediaListDTO,
    MenuItemMediaBulkSetDTO,
    MenuItemMediaReorderDTO,
    MenuMediaResponseDTO,
    # PIN verification
    PINVerifyDTO,
    PINVerifyResponseDTO
)

router = APIRouter(prefix="/api/v1/menus", tags=["menus"])


# ========== Dependency Injection ==========

def get_menu_repository(db: Session = Depends(get_db)) -> MenuRepository:
    """Inject menu repository"""
    return MenuRepository(db)


def get_menu_item_repository(db: Session = Depends(get_db)) -> MenuItemRepository:
    """Inject menu item repository"""
    return MenuItemRepository(db)


def get_import_history_repository(db: Session = Depends(get_db)) -> MenuImportHistoryRepository:
    """Inject import history repository"""
    return MenuImportHistoryRepository(db)


def get_menu_view_repository(db: Session = Depends(get_db)) -> MenuViewRepository:
    """Inject menu view repository"""
    return MenuViewRepository(db)


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()


def get_qr_generator() -> QRCodeGenerator:
    """Get QR code generator"""
    return QRCodeGenerator()


def get_excel_importer() -> ExcelImporter:
    """Get Excel importer"""
    return ExcelImporter()


def get_excel_exporter() -> ExcelExporter:
    """Get Excel exporter"""
    return ExcelExporter()


def get_category_repository(db: Session = Depends(get_db)) -> MenuCategoryRepository:
    """Inject menu category repository"""
    return MenuCategoryRepository(db)


def get_item_media_repository(db: Session = Depends(get_db)) -> MenuItemMediaRepository:
    """Inject menu item media repository"""
    return MenuItemMediaRepository(db)


# ========== Menu CRUD Endpoints ==========

@router.post("", status_code=201)
async def create_menu(
    payload: MenuCreateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "create")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Create new digital menu (requires menus:create permission)"""
    use_case = CreateMenuUseCase(menu_repo, qr_generator, audit_logger)

    menu_data = await use_case.execute(
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
        name=payload.name,
        menu_type=payload.menu_type,
        description=payload.description,
        is_active=payload.is_active,
        show_prices=payload.show_prices,
        display_mode=payload.display_mode,
        # Color scheme (60-30-10 principle)
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        theme_color=payload.theme_color,
        whatsapp_number=payload.whatsapp_number,
        phone_number=payload.phone_number,
        contact_label=payload.contact_label,
        outlet_extension=payload.outlet_extension,
        footer_description=payload.footer_description,
        available_days=payload.available_days,
        available_hours=payload.available_hours,
        translations=payload.translations
    )

    # Get full menu for response
    menu = menu_repo.find_by_id(menu_data["id"], current_user.organization_id)
    items_count = menu_repo.get_items_count(menu.id)

    # Build response
    player_url = settings.PLAYER_URL  # Must be configured via environment variable
    public_url = f"{player_url}/menu/{menu.public_url_code}"
    qr_url = qr_generator.get_qr_url(menu.qr_code_path) if menu.qr_code_path else None

    response = MenuResponseDTO.model_validate(menu)
    response.public_url = public_url
    response.qr_code_url = qr_url
    response.items_count = items_count

    return success_response(data=response)


@router.get("")
def list_menus(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    menu_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator)
):
    """List all menus for current organization (requires menus:view permission)"""
    menus, total = menu_repo.find_all(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        menu_type=menu_type,
        is_active=is_active
    )

    # Build responses with computed URLs
    player_url = settings.PLAYER_URL  # Must be configured via environment variable
    menu_responses = []

    for menu in menus:
        items_count = menu_repo.get_items_count(menu.id)
        public_url = f"{player_url}/menu/{menu.public_url_code}"
        qr_url = qr_generator.get_qr_url(menu.qr_code_path) if menu.qr_code_path else None

        response = MenuResponseDTO.model_validate(menu)
        response.public_url = public_url
        response.qr_code_url = qr_url
        response.items_count = items_count

        menu_responses.append(response)

    return success_response(data={
        "items": menu_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    })


# ========== Excel Template (MUST be before /{menu_id} routes) ==========

@router.get("/excel-template")
def download_excel_template(
    excel_exporter: ExcelExporter = Depends(get_excel_exporter)
):
    """Download Excel template for menu import"""
    template_bytes = excel_exporter.generate_template()

    return StreamingResponse(
        BytesIO(template_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=menu_template.xlsx"}
    )


@router.get("/{menu_id}")
def get_menu(
    menu_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator)
):
    """Get single menu by ID (requires menus:view permission)"""
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    items_count = menu_repo.get_items_count(menu.id)

    # Build response
    player_url = settings.PLAYER_URL  # Must be configured via environment variable
    public_url = f"{player_url}/menu/{menu.public_url_code}"
    qr_url = qr_generator.get_qr_url(menu.qr_code_path) if menu.qr_code_path else None

    response = MenuResponseDTO.model_validate(menu)
    response.public_url = public_url
    response.qr_code_url = qr_url
    response.items_count = items_count

    return success_response(data=response)


@router.patch("/{menu_id}")
def update_menu(
    menu_id: int,
    payload: MenuUpdateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Update menu (requires menus:edit permission)"""
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)

    # Debug logging for color updates
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[MENU_UPDATE] Menu {menu_id} - Received update_data: {update_data}")
    if 'primary_color' in update_data or 'secondary_color' in update_data or 'theme_color' in update_data:
        logger.info(f"[MENU_UPDATE] Color update - primary: {update_data.get('primary_color')}, secondary: {update_data.get('secondary_color')}, theme: {update_data.get('theme_color')}")
    menu = menu_repo.update(menu, updated_by_id=current_user.id, **update_data)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.update",
        resource_type="menu",
        resource_id=menu.id,
        details=update_data,
        organization_id=current_user.organization_id
    )

    items_count = menu_repo.get_items_count(menu.id)

    # Build response
    player_url = settings.PLAYER_URL  # Must be configured via environment variable
    public_url = f"{player_url}/menu/{menu.public_url_code}"
    qr_url = qr_generator.get_qr_url(menu.qr_code_path) if menu.qr_code_path else None

    response = MenuResponseDTO.model_validate(menu)
    response.public_url = public_url
    response.qr_code_url = qr_url
    response.items_count = items_count

    return success_response(data=response)


@router.delete("/{menu_id}", status_code=204)
def delete_menu(
    menu_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "delete")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Soft delete menu (requires menus:delete permission)"""
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    menu_repo.soft_delete(menu)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.delete",
        resource_type="menu",
        resource_id=menu.id,
        details={"name": menu.name},
        organization_id=current_user.organization_id
    )

    return None


# ========== Menu Item Endpoints ==========

@router.get("/{menu_id}/items")
def list_menu_items(
    menu_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository)
):
    """List items for menu (requires menus:view permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    items, total = menu_item_repo.find_by_menu(
        menu_id=menu_id,
        skip=skip,
        limit=limit,
        category=category
    )

    # Convert items to response DTOs with media
    item_responses = []
    for item in items:
        item_dict = {
            "id": item.id,
            "menu_id": item.menu_id,
            "organization_id": item.organization_id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "currency": item.currency,
            "image_url": item.image_url,
            "video_url": item.video_url,
            "content_id": item.content_id,
            "category": item.category,
            "subcategory": item.subcategory,
            "variant": item.variant,
            "tags": item.tags,
            "display_order": item.display_order,
            "is_active": item.is_active,
            "is_featured": item.is_featured,
            "is_available": item.is_available,
            "translations": item.translations,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "media": []
        }

        # Convert media_items relationship to simple media array
        if hasattr(item, 'media_items') and item.media_items:
            for mim in item.media_items:
                if mim.menu_media:
                    media_url = None
                    if mim.menu_media.file_path:
                        media_url = f"{settings.PUBLIC_BASE_URL}/uploads/menu-media/{mim.menu_media.filename}"
                    item_dict["media"].append({
                        "id": mim.menu_media_id,
                        "url": media_url,
                        "mime_type": mim.menu_media.mime_type,
                        "is_primary": mim.is_primary,
                        "display_order": mim.display_order
                    })

        item_responses.append(MenuItemResponseDTO.model_validate(item_dict))

    return success_response(data={
        "items": item_responses,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": (skip + limit) < total
    })


@router.post("/{menu_id}/items", status_code=201)
def add_menu_item(
    menu_id: int,
    payload: MenuItemCreateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Add item to menu (requires menus:edit permission)"""
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    item = menu_item_repo.create(
        menu_id=menu_id,
        organization_id=current_user.organization_id,
        **payload.model_dump()
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.add_item",
        resource_type="menu",
        resource_id=menu.id,
        details={"item_id": item.id, "item_name": item.name},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuItemResponseDTO.model_validate(item))


@router.patch("/{menu_id}/items/{item_id}")
def update_menu_item(
    menu_id: int,
    item_id: int,
    payload: MenuItemUpdateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Update menu item (requires menus:edit permission)"""
    # Verify menu exists and belongs to organization
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find item
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    item = menu_item_repo.update(item, **update_data)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.update_item",
        resource_type="menu",
        resource_id=menu.id,
        details={"item_id": item.id, "item_name": item.name, "changes": update_data},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuItemResponseDTO.model_validate(item))


@router.delete("/{menu_id}/items/{item_id}", status_code=204)
def delete_menu_item(
    menu_id: int,
    item_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "delete")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Delete menu item (requires menus:delete permission)"""
    # Verify menu exists and belongs to organization
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find item
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Soft delete item
    menu_item_repo.soft_delete(item)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.delete_item",
        resource_type="menu",
        resource_id=menu.id,
        details={"item_id": item_id, "item_name": item.name},
        organization_id=current_user.organization_id
    )

    return None


# ========== Excel Import/Export Endpoints ==========

@router.post("/{menu_id}/import")
async def import_items_from_excel(
    menu_id: int,
    file: UploadFile = File(...),
    replace_existing: bool = Query(False),
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    import_history_repo: MenuImportHistoryRepository = Depends(get_import_history_repository),
    excel_importer: ExcelImporter = Depends(get_excel_importer),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Import menu items from Excel file (requires menus:edit permission)"""
    use_case = BulkImportItemsUseCase(
        menu_repo,
        menu_item_repo,
        import_history_repo,
        excel_importer,
        audit_logger
    )

    result = await use_case.execute(
        menu_id=menu_id,
        organization_id=current_user.organization_id,
        imported_by_id=current_user.id,
        file=file,
        replace_existing=replace_existing
    )

    return success_response(data=result)


@router.get("/{menu_id}/export")
def export_menu_to_excel(
    menu_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    excel_exporter: ExcelExporter = Depends(get_excel_exporter)
):
    """Export menu items to Excel file (requires menus:view permission)"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO

    # Get menu
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Get all items for this menu
    items = menu_item_repo.find_all_for_export(menu_id, current_user.organization_id)

    # Convert to dict list with all columns
    items_data = [
        {
            "name": item.name,
            "price": item.price,
            "currency": item.currency,
            "description": item.description,
            "category": item.category,
            "subcategory": item.subcategory,
            "tags": item.tags,
            "is_active": item.is_active,
            "is_featured": item.is_featured,
            "is_available": item.is_available,
        }
        for item in items
    ]

    # Generate Excel file
    excel_bytes = excel_exporter.export_menu(menu.name, items_data)

    # Return as streaming response
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{menu.name}_menu.xlsx"'
        }
    )


# ========== PIN Verification Endpoint ==========

@router.post("/verify-pin")
def verify_organization_pin(
    payload: PINVerifyDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "delete")),
    db: Session = Depends(get_db)
):
    """Verify organization PIN for sensitive operations (requires menus:delete permission)"""
    from services.auth.repositories.models import OrganizationModel

    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == current_user.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if PIN matches
    if org.pin == payload.pin:
        return success_response(data=PINVerifyResponseDTO(
            verified=True,
            message="PIN verified successfully"
        ))
    else:
        return success_response(data=PINVerifyResponseDTO(
            verified=False,
            message="Invalid PIN"
        ))


@router.delete("/{menu_id}/with-pin", status_code=204)
def delete_menu_with_pin(
    menu_id: int,
    payload: PINVerifyDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "delete")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    db: Session = Depends(get_db)
):
    """Delete menu with PIN verification (requires menus:delete permission)"""
    from services.auth.repositories.models import OrganizationModel

    # Verify PIN first
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == current_user.organization_id
    ).first()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.pin != payload.pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")

    # Find and delete menu
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    menu_repo.soft_delete(menu)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.delete_with_pin",
        resource_type="menu",
        resource_id=menu.id,
        details={"name": menu.name, "pin_verified": True},
        organization_id=current_user.organization_id
    )

    return None


# ========== Menu Category Endpoints (Per-Menu) ==========

@router.get("/{menu_id}/categories")
def list_menu_categories(
    menu_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    category_repo: MenuCategoryRepository = Depends(get_category_repository)
):
    """List categories for a specific menu (requires menus:view permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    categories = category_repo.find_by_menu(menu_id, current_user.organization_id)
    category_responses = [MenuCategoryResponseDTO.model_validate(cat) for cat in categories]

    return success_response(data=MenuCategoryListDTO(
        items=category_responses,
        total=len(category_responses)
    ))


@router.post("/{menu_id}/categories", status_code=201)
def create_menu_category(
    menu_id: int,
    payload: MenuCategoryCreateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    category_repo: MenuCategoryRepository = Depends(get_category_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Create a category for a specific menu (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Check if category with same name exists
    existing = category_repo.find_by_name(menu_id, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    # Create category
    category = category_repo.create(
        organization_id=current_user.organization_id,
        menu_type=menu.menu_type,
        name=payload.name,
        display_order=payload.display_order,
        icon=payload.icon,
        translations=payload.translations,
        subcategories=payload.subcategories,
        menu_id=menu_id
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.create_category",
        resource_type="menu",
        resource_id=menu.id,
        details={"category_id": category.id, "category_name": category.name},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuCategoryResponseDTO.model_validate(category))


@router.patch("/{menu_id}/categories/{category_id}")
def update_menu_category(
    menu_id: int,
    category_id: int,
    payload: MenuCategoryUpdateDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    category_repo: MenuCategoryRepository = Depends(get_category_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Update a menu category (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find category
    category = category_repo.find_by_id(category_id, current_user.organization_id)
    if not category or category.menu_id != menu_id:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check for duplicate name if changing name
    if payload.name and payload.name != category.name:
        existing = category_repo.find_by_name(menu_id, payload.name)
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")

    # Update
    update_data = payload.model_dump(exclude_unset=True)
    category = category_repo.update(category, **update_data)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.update_category",
        resource_type="menu",
        resource_id=menu.id,
        details={"category_id": category.id, "changes": update_data},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuCategoryResponseDTO.model_validate(category))


@router.delete("/{menu_id}/categories/{category_id}", status_code=204)
def delete_menu_category(
    menu_id: int,
    category_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "delete")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    category_repo: MenuCategoryRepository = Depends(get_category_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Delete a menu category (requires menus:delete permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Find category
    category = category_repo.find_by_id(category_id, current_user.organization_id)
    if not category or category.menu_id != menu_id:
        raise HTTPException(status_code=404, detail="Category not found")

    category_name = category.name
    category_repo.delete(category)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.delete_category",
        resource_type="menu",
        resource_id=menu.id,
        details={"category_id": category_id, "category_name": category_name},
        organization_id=current_user.organization_id
    )

    return None


@router.post("/{menu_id}/categories/reorder")
def reorder_menu_categories(
    menu_id: int,
    payload: MenuCategoryReorderDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    category_repo: MenuCategoryRepository = Depends(get_category_repository)
):
    """Reorder categories for a menu (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    category_repo.reorder(menu_id, payload.category_orders)

    # Return updated list
    categories = category_repo.find_by_menu(menu_id, current_user.organization_id)
    category_responses = [MenuCategoryResponseDTO.model_validate(cat) for cat in categories]

    return success_response(data=MenuCategoryListDTO(
        items=category_responses,
        total=len(category_responses)
    ))


# ========== Menu Item Media Endpoints (Multiple Media per Item) ==========

@router.get("/{menu_id}/items/{item_id}/media")
def list_item_media(
    menu_id: int,
    item_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "view")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository)
):
    """List all media for a menu item (requires menus:view permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Get media with details
    media_list = item_media_repo.get_media_for_item_with_details(item_id)

    # Build response
    responses = []
    for m in media_list:
        media_response = MenuMediaResponseDTO.model_validate(m["media"]) if m["media"] else None
        response = MenuItemMediaResponseDTO(
            id=m["id"],
            menu_item_id=m["menu_item_id"],
            menu_media_id=m["menu_media_id"],
            display_order=m["display_order"],
            is_primary=m["is_primary"],
            created_at=m["created_at"],
            media=media_response
        )
        responses.append(response)

    return success_response(data=MenuItemMediaListDTO(
        items=responses,
        total=len(responses)
    ))


@router.post("/{menu_id}/items/{item_id}/media", status_code=201)
def add_media_to_item(
    menu_id: int,
    item_id: int,
    payload: MenuItemMediaAddDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Add media to a menu item (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    try:
        item_media = item_media_repo.add_media_to_item(
            menu_item_id=item_id,
            menu_media_id=payload.menu_media_id,
            display_order=payload.display_order,
            is_primary=payload.is_primary
        )
    except Exception as e:
        if "unique_menu_item_media" in str(e) or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="Media already added to this item")
        raise

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.add_item_media",
        resource_type="menu_item",
        resource_id=item.id,
        details={"media_id": payload.menu_media_id, "is_primary": payload.is_primary},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuItemMediaResponseDTO.model_validate(item_media))


@router.delete("/{menu_id}/items/{item_id}/media/{media_id}", status_code=204)
def remove_media_from_item(
    menu_id: int,
    item_id: int,
    media_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Remove media from a menu item (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    success = item_media_repo.remove_media_from_item(item_id, media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found on this item")

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.remove_item_media",
        resource_type="menu_item",
        resource_id=item.id,
        details={"media_id": media_id},
        organization_id=current_user.organization_id
    )

    return None


@router.post("/{menu_id}/items/{item_id}/media/bulk")
def bulk_set_item_media(
    menu_id: int,
    item_id: int,
    payload: MenuItemMediaBulkSetDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Bulk set media for a menu item - replaces existing (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Bulk set media
    item_media_repo.bulk_set_media(
        menu_item_id=item_id,
        media_ids=payload.media_ids,
        primary_media_id=payload.primary_media_id
    )

    # Get updated list
    media_list = item_media_repo.get_media_for_item_with_details(item_id)
    responses = []
    for m in media_list:
        media_response = MenuMediaResponseDTO.model_validate(m["media"]) if m["media"] else None
        response = MenuItemMediaResponseDTO(
            id=m["id"],
            menu_item_id=m["menu_item_id"],
            menu_media_id=m["menu_media_id"],
            display_order=m["display_order"],
            is_primary=m["is_primary"],
            created_at=m["created_at"],
            media=media_response
        )
        responses.append(response)

    # Audit log
    audit_logger.log_action(
        user_id=current_user.id,
        action="menu.bulk_set_item_media",
        resource_type="menu_item",
        resource_id=item.id,
        details={"media_ids": payload.media_ids, "primary_media_id": payload.primary_media_id},
        organization_id=current_user.organization_id
    )

    return success_response(data=MenuItemMediaListDTO(
        items=responses,
        total=len(responses)
    ))


@router.post("/{menu_id}/items/{item_id}/media/{media_id}/set-primary")
def set_primary_media(
    menu_id: int,
    item_id: int,
    media_id: int,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository)
):
    """Set a media as primary for a menu item (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    success = item_media_repo.set_primary(item_id, media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found on this item")

    return success_response(data={"message": "Primary media set successfully"})


@router.post("/{menu_id}/items/{item_id}/media/reorder")
def reorder_item_media(
    menu_id: int,
    item_id: int,
    payload: MenuItemMediaReorderDTO,
    current_user: CurrentUser = Depends(require_permission("menus", "edit")),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    item_media_repo: MenuItemMediaRepository = Depends(get_item_media_repository)
):
    """Reorder media for a menu item (requires menus:edit permission)"""
    # Verify menu exists
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Verify item exists
    item = menu_item_repo.find_by_id(item_id, menu_id, current_user.organization_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item_media_repo.update_display_order(item_id, payload.media_orders)

    # Get updated list
    media_list = item_media_repo.get_media_for_item_with_details(item_id)
    responses = []
    for m in media_list:
        media_response = MenuMediaResponseDTO.model_validate(m["media"]) if m["media"] else None
        response = MenuItemMediaResponseDTO(
            id=m["id"],
            menu_item_id=m["menu_item_id"],
            menu_media_id=m["menu_media_id"],
            display_order=m["display_order"],
            is_primary=m["is_primary"],
            created_at=m["created_at"],
            media=media_response
        )
        responses.append(response)

    return success_response(data=MenuItemMediaListDTO(
        items=responses,
        total=len(responses)
    ))
