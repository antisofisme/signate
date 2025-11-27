"""Create Menu Use Case"""

import secrets
import string
from typing import Dict, Any
from datetime import datetime, timezone

from ..repositories import MenuRepository
from ..infrastructure import QRCodeGenerator
from services.audit.dtos import AuditLogAction
from shared.config import settings
import logging

logger = logging.getLogger(__name__)


class CreateMenuUseCase:
    """Use case for creating a new digital menu"""

    def __init__(
        self,
        menu_repo: MenuRepository,
        qr_generator: QRCodeGenerator,
        audit_logger=None
    ):
        self.menu_repo = menu_repo
        self.qr_generator = qr_generator
        self.audit_logger = audit_logger

    def _generate_unique_code(self) -> str:
        """
        Generate unique 12-character alphanumeric code for public URL

        Returns:
            Unique code (e.g., 'ABC123XYZ456')
        """
        max_attempts = 10

        for _ in range(max_attempts):
            # Generate random 12-char code (uppercase + digits)
            code = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(12)
            )

            # Check if code already exists
            if not self.menu_repo.exists_by_public_code(code):
                return code

        # Fallback: add timestamp to ensure uniqueness
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        return f"{timestamp[:12]}"

    async def execute(
        self,
        organization_id: int,
        created_by_id: int,
        name: str,
        menu_type: str,
        description: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new menu with auto-generated QR code

        Args:
            organization_id: Organization ID
            created_by_id: User ID who creates the menu
            name: Menu name
            menu_type: Type of menu (restaurant, laundry, spa, etc.)
            description: Menu description
            **kwargs: Additional menu fields

        Returns:
            Dict with menu data and public URLs

        Raises:
            Exception: If menu creation fails
        """
        try:
            # Generate unique public URL code
            public_url_code = self._generate_unique_code()
            logger.info(f"Generated public URL code: {public_url_code}")

            # Create menu (without QR code first)
            menu = self.menu_repo.create(
                organization_id=organization_id,
                name=name,
                menu_type=menu_type,
                public_url_code=public_url_code,
                created_by_id=created_by_id,
                description=description,
                **kwargs
            )

            # Generate public URL
            player_url = settings.PLAYER_URL  # Must be configured via environment variable
            public_url = f"{player_url}/menu/{public_url_code}"

            # Generate QR code
            try:
                qr_path = self.qr_generator.generate(
                    data=public_url,
                    menu_id=menu.id,
                    organization_id=organization_id
                )

                # Update menu with QR code path
                menu = self.menu_repo.update(
                    menu,
                    updated_by_id=created_by_id,
                    qr_code_path=qr_path,
                    qr_code_generated_at=datetime.now(timezone.utc)
                )

                logger.info(f"Generated QR code for menu {menu.id}: {qr_path}")

            except Exception as e:
                # Log error but don't fail menu creation
                logger.error(f"Failed to generate QR code for menu {menu.id}: {e}")

            # Audit log
            if self.audit_logger:
                self.audit_logger.log_action(
                    user_id=created_by_id,
                    action=AuditLogAction.MENU_CREATE,
                    resource_type="menu",
                    resource_id=menu.id,
                    details={
                        "name": name,
                        "type": menu_type,
                        "public_url_code": public_url_code
                    },
                    organization_id=organization_id
                )

            # Return menu with computed URLs
            return {
                "id": menu.id,
                "name": menu.name,
                "menu_type": menu.menu_type,
                "public_url_code": menu.public_url_code,
                "public_url": public_url,
                "qr_code_path": menu.qr_code_path,
                "qr_code_url": self.qr_generator.get_qr_url(menu.qr_code_path) if menu.qr_code_path else None,
                "created_at": menu.created_at,
            }

        except Exception as e:
            logger.error(f"Failed to create menu: {e}")
            raise
