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

from .repositories import (
    MenuRepository,
    MenuItemRepository,
    MenuImportHistoryRepository,
    MenuViewRepository
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
    MenuImportHistoryListDTO
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


# ========== Menu CRUD Endpoints ==========

@router.post("", status_code=201)
async def create_menu(
    payload: MenuCreateDTO,
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Create new digital menu"""
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
        theme_color=payload.theme_color,
        whatsapp_number=payload.whatsapp_number,
        phone_number=payload.phone_number,
        contact_label=payload.contact_label,
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator)
):
    """List all menus for current organization"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator)
):
    """Get single menu by ID"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    qr_generator: QRCodeGenerator = Depends(get_qr_generator),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Update menu"""
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Soft delete menu"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository)
):
    """List items for menu"""
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

    item_responses = [MenuItemResponseDTO.model_validate(item) for item in items]

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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Add item to menu"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Update menu item"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Delete menu item"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    import_history_repo: MenuImportHistoryRepository = Depends(get_import_history_repository),
    excel_importer: ExcelImporter = Depends(get_excel_importer),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """Import menu items from Excel file"""
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
    current_user: CurrentUser = Depends(get_current_user),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    menu_item_repo: MenuItemRepository = Depends(get_menu_item_repository),
    excel_exporter: ExcelExporter = Depends(get_excel_exporter)
):
    """Export menu items to Excel file"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO

    # Get menu
    menu = menu_repo.find_by_id(menu_id, current_user.organization_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # Get all items for this menu
    items = menu_item_repo.find_all_for_export(menu_id, current_user.organization_id)

    # Convert to dict list
    items_data = [
        {
            "name": item.name,
            "price": item.price,
            "description": item.description,
            "category": item.category,
            "image_url": item.image_url,
            "video_url": item.video_url,
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
