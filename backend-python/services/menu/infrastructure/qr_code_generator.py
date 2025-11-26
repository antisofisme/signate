"""QR Code Generator for Digital Menus"""

import qrcode
from pathlib import Path
from typing import Optional
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Generate QR codes for menu public URLs"""

    def __init__(self):
        # QR codes stored in content directory under qr_codes/
        self.qr_dir = Path(settings.UPLOAD_DIR) / "qr_codes"
        self.qr_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        data: str,
        menu_id: int,
        organization_id: int
    ) -> str:
        """
        Generate QR code image and return storage path

        Args:
            data: URL to encode (e.g., https://player.zhmhotels.online/menu/ABC123)
            menu_id: Menu ID for filename
            organization_id: Organization ID for filename

        Returns:
            Relative path to QR code image (e.g., "qr_codes/menu_123_org_4.png")

        Raises:
            Exception: If QR code generation fails
        """
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Auto-size
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Add data
            qr.add_data(data)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")

            # Save to file
            filename = f"menu_{menu_id}_org_{organization_id}.png"
            file_path = self.qr_dir / filename

            # Save image
            img.save(file_path)

            # Return relative path for database storage
            relative_path = f"qr_codes/{filename}"
            logger.info(f"Generated QR code: {relative_path}")

            return relative_path

        except Exception as e:
            logger.error(f"Failed to generate QR code for menu {menu_id}: {e}")
            raise

    def regenerate(
        self,
        data: str,
        menu_id: int,
        organization_id: int,
        old_path: Optional[str] = None
    ) -> str:
        """
        Regenerate QR code (delete old one if exists)

        Args:
            data: URL to encode
            menu_id: Menu ID
            organization_id: Organization ID
            old_path: Old QR code path to delete

        Returns:
            New relative path to QR code image
        """
        # Delete old QR code if exists
        if old_path:
            try:
                old_file = Path(settings.UPLOAD_DIR) / old_path
                if old_file.exists():
                    old_file.unlink()
                    logger.info(f"Deleted old QR code: {old_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old QR code {old_path}: {e}")

        # Generate new QR code
        return self.generate(data, menu_id, organization_id)

    def get_qr_url(self, qr_code_path: str) -> str:
        """
        Get public URL for QR code image

        Args:
            qr_code_path: Relative path (e.g., "qr_codes/menu_123_org_4.png")

        Returns:
            Full public URL (e.g., "https://api.zhmhotels.online/qr_codes/menu_123_org_4.png")
        """
        if not qr_code_path:
            return ""

        return f"{settings.PUBLIC_BASE_URL}/{qr_code_path}"

    def delete(self, qr_code_path: str) -> bool:
        """
        Delete QR code file

        Args:
            qr_code_path: Relative path to QR code

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = Path(settings.UPLOAD_DIR) / qr_code_path
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted QR code: {qr_code_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete QR code {qr_code_path}: {e}")
            return False
