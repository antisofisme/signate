"""Bulk Import Menu Items Use Case"""

from typing import Dict, Any, List
from fastapi import UploadFile

from ..repositories import MenuRepository, MenuItemRepository, MenuImportHistoryRepository
from ..repositories.models import MenuItemModel
from ..infrastructure import ExcelImporter
from services.audit.dtos import AuditLogAction
import logging

logger = logging.getLogger(__name__)


class BulkImportItemsUseCase:
    """Use case for importing menu items from Excel"""

    def __init__(
        self,
        menu_repo: MenuRepository,
        menu_item_repo: MenuItemRepository,
        import_history_repo: MenuImportHistoryRepository,
        excel_importer: ExcelImporter,
        audit_logger=None
    ):
        self.menu_repo = menu_repo
        self.menu_item_repo = menu_item_repo
        self.import_history_repo = import_history_repo
        self.excel_importer = excel_importer
        self.audit_logger = audit_logger

    async def execute(
        self,
        menu_id: int,
        organization_id: int,
        imported_by_id: int,
        file: UploadFile,
        replace_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import menu items from Excel file

        Args:
            menu_id: Menu ID
            organization_id: Organization ID
            imported_by_id: User ID who imports
            file: Excel file (UploadFile from FastAPI)
            replace_existing: If True, delete existing items before import

        Returns:
            Import result with statistics

        Raises:
            ValueError: If menu not found or file invalid
            Exception: If import fails
        """
        try:
            # Verify menu exists and belongs to organization
            menu = self.menu_repo.find_by_id(menu_id, organization_id)
            if not menu:
                raise ValueError(f"Menu {menu_id} not found")

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            logger.info(
                f"Starting Excel import for menu {menu_id}, file: {file.filename}, size: {file_size} bytes"
            )

            # Parse Excel file
            try:
                valid_items, errors = self.excel_importer.parse(
                    file_content=file_content,
                    menu_id=menu_id,
                    organization_id=organization_id
                )
            except ValueError as e:
                # Invalid file format
                logger.error(f"Invalid Excel file: {e}")

                # Create failed import history
                history = self.import_history_repo.create(
                    menu_id=menu_id,
                    organization_id=organization_id,
                    filename=file.filename,
                    file_size=file_size,
                    rows_total=0,
                    rows_success=0,
                    rows_failed=0,
                    imported_by_id=imported_by_id,
                    errors=[{"row": 0, "error": str(e)}]
                )

                return {
                    "id": history.id,
                    "filename": file.filename,
                    "rows_total": 0,
                    "rows_success": 0,
                    "rows_failed": 0,
                    "errors": [{"row": 0, "error": str(e)}],
                    "status": "failed"
                }

            # Replace existing items if requested
            if replace_existing and valid_items:
                deleted_count = self.menu_item_repo.delete_all_by_menu(menu_id, organization_id)
                logger.info(f"Replaced {deleted_count} existing items in menu {menu_id}")

            # Bulk insert valid items
            success_count = 0
            if valid_items:
                try:
                    # Convert dicts to MenuItemModel instances
                    item_models = [
                        MenuItemModel(**item_data)
                        for item_data in valid_items
                    ]

                    # Bulk insert
                    self.menu_item_repo.bulk_create(item_models)
                    success_count = len(item_models)

                    logger.info(f"Successfully imported {success_count} items")

                except Exception as e:
                    logger.error(f"Failed to bulk insert items: {e}")
                    errors.append({
                        "row": 0,
                        "error": f"Database error: {str(e)}"
                    })

            # Create import history record
            rows_total = len(valid_items) + len(errors)
            history = self.import_history_repo.create(
                menu_id=menu_id,
                organization_id=organization_id,
                filename=file.filename,
                file_size=file_size,
                rows_total=rows_total,
                rows_success=success_count,
                rows_failed=len(errors),
                imported_by_id=imported_by_id,
                errors=errors if errors else None
            )

            # Audit log
            if self.audit_logger:
                self.audit_logger.log_action(
                    user_id=imported_by_id,
                    action=AuditLogAction.MENU_IMPORT_ITEMS,
                    resource_type="menu",
                    resource_id=menu_id,
                    details={
                        "filename": file.filename,
                        "total": rows_total,
                        "success": success_count,
                        "failed": len(errors),
                        "replace_existing": replace_existing
                    },
                    organization_id=organization_id
                )

            return {
                "id": history.id,
                "filename": file.filename,
                "rows_total": rows_total,
                "rows_success": success_count,
                "rows_failed": len(errors),
                "errors": errors if errors else [],
                "status": "success" if len(errors) == 0 else "partial"
            }

        except Exception as e:
            logger.error(f"Failed to import menu items: {e}")
            raise
