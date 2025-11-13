"""
Activate Device Use Case
Activate device using 6-digit code from CMS

Updated to use centralized validators and error handling
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from ..domain.device import Device, ActivationCode
from ..domain.interfaces import IDeviceRepository
from shared.errors import ValidationError, NotFoundError, ErrorCodes
from shared.validators import validate_activation_code
from shared.websocket_manager import websocket_manager, WebSocketEventType
from shared.auth import create_device_token
from services.organization.domain.quota_service import OrganizationQuotaService
import asyncio


class ActivateDeviceUseCase:
    """
    Use case for activating device
    Called by CMS admin to activate device with code
    """

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        unique_code: str,
        organization_id: int,
        device_name: Optional[str] = None,
        room_number: Optional[str] = None,
        location_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Activate device with unique code

        Args:
            unique_code: 6-digit activation code
            organization_id: Organization ID from admin's JWT (assigns device to admin's org)
            device_name: Optional custom name
            room_number: Optional room number
            location_type: Optional location type

        Returns:
            Dict with device and JWT token

        Raises:
            ValidationError: If code invalid or expired
            NotFoundError: If device not found
        """

        # Validate code format using centralized validator
        is_valid_code, error_msg = validate_activation_code(unique_code)
        if not is_valid_code:
            raise ValidationError(
                message=error_msg,
                details={"field": "unique_code"}
            )

        # Normalize code to uppercase
        normalized_code = unique_code.upper()

        # Find device by code
        device = self.device_repo.find_by_code(normalized_code)

        if not device:
            raise NotFoundError(
                message="Device dengan kode ini tidak ditemukan",
                resource_type="device",
                resource_id=normalized_code
            )

        # Check if already activated
        if device.is_active():
            raise ValidationError(
                message="Device sudah diaktivasi sebelumnya",
                details={"device_id": device.id, "status": device.status}
            )

        # Check if code expired
        if not device.can_activate():
            raise ValidationError(
                message="Kode aktivasi sudah kadaluarsa. Silakan request kode baru dari device.",
                details={"expires_at": device.code_expires_at.isoformat() if device.code_expires_at else None}
            )

        # 🆕 Check organization device quota before activation
        # TODO: Re-enable when organizations table has quota columns (max_devices, settings)
        # db_session = self.device_repo.db
        # quota_service = OrganizationQuotaService(db_session)
        #
        # # Enforce device quota atomically to prevent race conditions
        # try:
        #     quota_service.enforce_device_quota_atomic(organization_id)
        # except ValueError as e:
        #     raise ValidationError(
        #         message=str(e),
        #         details={"organization_id": organization_id}
        #     )
        
        # 🆕 Assign device to admin's organization (from JWT token)
        device.organization_id = organization_id
        device.status = 'active'
        device.last_seen = datetime.now(timezone.utc)

        if device_name:
            device.device_name = device_name

        if room_number:
            device.room_number = room_number

        if location_type:
            device.location_type = location_type

        # Save changes
        updated_device = self.device_repo.update(device)
        
        # Generate JWT token for device
        device_token = create_device_token(
            device_id=updated_device.id,
            organization_id=updated_device.organization_id
        )
        
        # WebSocket broadcast akan dilakukan di route layer (FastAPI background task)
        # Data di-return untuk diteruskan ke broadcast
        self._broadcast_data = {
            "organization_id": updated_device.organization_id,
            "event_type": "device:activated",
            "data": {
                "device_id": updated_device.id,
                "device_name": updated_device.device_name,
                "room_number": updated_device.room_number,
                "location_type": updated_device.location_type,
                "status": updated_device.status
            }
        }

        return {
            "device": updated_device,
            "token": device_token
        }
