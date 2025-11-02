"""
Device Service - Business Logic Layer untuk Device Management
=============================================================

SERVICE LAYER - Tempat SEMUA business logic
- Validasi business rules
- Orchestration (call multiple repositories)
- Transform data
- Error handling

TIDAK BOLEH:
- Direct database query (harus via repository)
- HTTP handling (itu tugas API layer)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.repositories import DeviceRepository
from app.core.exceptions import (
    DeviceNotFoundException,
    DeviceAlreadyActivatedException,
    InvalidActivationCodeException
)

logger = logging.getLogger(__name__)


class DeviceService:
    """
    Device Business Logic

    Responsibilities:
    - Validate business rules
    - Coordinate between repositories
    - Log business events
    - Handle errors gracefully
    """

    def __init__(self, db: Session):
        self.db = db
        self.device_repo = DeviceRepository(db)
        # Could add other repos if needed:
        # self.activity_repo = ActivityRepository(db)

    # =========================================================================
    # DEVICE CRUD dengan Business Logic
    # =========================================================================

    def get_device(self, device_id: int) -> Dict:
        """
        Get device by ID dengan business logic

        Adds:
        - Status calculation (online/offline)
        - Last seen human-readable
        """
        device = self.device_repo.get(device_id)
        if not device:
            raise DeviceNotFoundException(f"Device {device_id} not found")

        return self._enrich_device_data(device)

    def get_organization_devices(
        self,
        organization_id: int,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get devices dengan pagination dan enrichment

        Returns:
            {
                "items": [...],
                "total": 100,
                "page": 1,
                "per_page": 20,
                "pages": 5
            }
        """
        skip = (page - 1) * per_page

        devices = self.device_repo.get_by_organization(
            organization_id=organization_id,
            status=status,
            skip=skip,
            limit=per_page
        )

        total = self.device_repo.count({"organization_id": organization_id})

        return {
            "items": [self._enrich_device_data(d) for d in devices],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def create_device(
        self,
        organization_id: int,
        name: str,
        location: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Create new device dengan validation

        Business rules:
        - Name required
        - Generate unique activation code
        - Initial status = "pending"
        """
        # Validation
        if not name or len(name.strip()) == 0:
            raise ValueError("Device name is required")

        # Generate activation code
        activation_code = self._generate_activation_code()

        device_data = {
            "organization_id": organization_id,
            "name": name.strip(),
            "location": location,
            "activation_code": activation_code,
            "status": "pending",
            "created_at": datetime.utcnow(),
            **kwargs
        }

        device = self.device_repo.create(device_data)

        logger.info(f"Device created: {device.id} - {device.name}")

        # TODO: Log activity
        # self.activity_repo.log("device_created", device.id)

        return self._enrich_device_data(device)

    def update_device(
        self,
        device_id: int,
        updates: Dict[str, Any]
    ) -> Dict:
        """
        Update device dengan validation

        Business rules:
        - Cannot change device_id once activated
        - Cannot change organization_id
        """
        device = self.device_repo.get(device_id)
        if not device:
            raise DeviceNotFoundException(f"Device {device_id} not found")

        # Validation
        if "device_id" in updates and device.status == "active":
            raise ValueError("Cannot change device_id for activated device")

        if "organization_id" in updates:
            raise ValueError("Cannot change organization")

        # Update
        updated_device = self.device_repo.update(device_id, updates)

        logger.info(f"Device updated: {device_id}")

        return self._enrich_device_data(updated_device)

    def delete_device(self, device_id: int) -> bool:
        """
        Delete device (soft delete preferred)

        Business rule:
        - Log activity before delete
        - Check if device is used in playlists
        """
        device = self.device_repo.get(device_id)
        if not device:
            raise DeviceNotFoundException(f"Device {device_id} not found")

        # TODO: Check if device has active assignments
        # if self.has_active_assignments(device_id):
        #     raise ValueError("Cannot delete device with active assignments")

        # Soft delete
        self.device_repo.deactivate_device(device_id)

        logger.warning(f"Device deactivated: {device_id} - {device.name}")

        return True

    # =========================================================================
    # DEVICE ACTIVATION (Business Critical)
    # =========================================================================

    def activate_device(
        self,
        device_id: str,
        activation_code: str
    ) -> Dict:
        """
        Activate device dengan validation

        Business rules:
        - Activation code must be valid
        - Device cannot be already activated
        - Set status to "active"
        - Record activation timestamp
        """
        # Find device by activation code
        device = self.device_repo.get_by_field("activation_code", activation_code)
        if not device:
            logger.warning(f"Invalid activation code: {activation_code}")
            raise InvalidActivationCodeException("Invalid activation code")

        # Check if already activated
        if device.status == "active":
            logger.warning(f"Device already activated: {device.id}")
            raise DeviceAlreadyActivatedException(
                f"Device {device.name} is already activated"
            )

        # Activate
        activated = self.device_repo.activate_device(device_id, activation_code)
        if not activated:
            raise ValueError("Failed to activate device")

        logger.info(f"Device activated: {device.id} - {device.name} ({device_id})")

        # TODO: Log activity
        # self.activity_repo.log("device_activated", device.id)

        return self._enrich_device_data(activated)

    def process_heartbeat(self, device_id: str) -> bool:
        """
        Process device heartbeat

        Business logic:
        - Update last_seen
        - Auto-reactivate if was offline
        """
        success = self.device_repo.update_heartbeat(device_id)

        if success:
            logger.debug(f"Heartbeat received: {device_id}")

        return success

    # =========================================================================
    # DEVICE ANALYTICS & REPORTING
    # =========================================================================

    def get_device_dashboard(self, organization_id: int) -> Dict:
        """
        Get comprehensive device dashboard data

        Combines:
        - Device stats
        - Online/offline counts
        - Recent activities
        """
        stats = self.device_repo.get_device_stats(organization_id)
        online_devices = self.device_repo.get_online_devices(organization_id)
        offline_devices = self.device_repo.get_offline_devices(organization_id)

        return {
            "stats": stats,
            "online": len(online_devices),
            "offline": len(offline_devices),
            "online_devices": [self._device_summary(d) for d in online_devices[:10]],
            "offline_devices": [self._device_summary(d) for d in offline_devices[:10]]
        }

    def search_devices(
        self,
        organization_id: int,
        query: str
    ) -> List[Dict]:
        """
        Search devices dengan enrichment

        Business logic:
        - Trim whitespace
        - Min 2 characters
        - Return enriched results
        """
        if not query or len(query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")

        devices = self.device_repo.search_devices(
            organization_id,
            query.strip()
        )

        return [self._enrich_device_data(d) for d in devices]

    # =========================================================================
    # HELPER METHODS (Private)
    # =========================================================================

    def _enrich_device_data(self, device: Any) -> Dict:
        """
        Add computed fields to device data

        Adds:
        - is_online (bool)
        - last_seen_human (string)
        - status_display (string)
        """
        from datetime import timedelta

        is_online = False
        if device.last_seen:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            is_online = device.last_seen >= five_minutes_ago

        last_seen_human = "Never"
        if device.last_seen:
            delta = datetime.utcnow() - device.last_seen
            if delta.seconds < 60:
                last_seen_human = f"{delta.seconds}s ago"
            elif delta.seconds < 3600:
                last_seen_human = f"{delta.seconds // 60}m ago"
            elif delta.days < 1:
                last_seen_human = f"{delta.seconds // 3600}h ago"
            else:
                last_seen_human = f"{delta.days}d ago"

        return {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name,
            "location": device.location,
            "status": device.status,
            "is_online": is_online,
            "last_seen": device.last_seen,
            "last_seen_human": last_seen_human,
            "created_at": device.created_at,
            # Add more fields as needed
        }

    def _device_summary(self, device: Any) -> Dict:
        """Lightweight device summary for lists"""
        return {
            "id": device.id,
            "name": device.name,
            "location": device.location,
            "status": device.status
        }

    def _generate_activation_code(self) -> str:
        """
        Generate unique 6-digit activation code

        Business rule: Must be unique in database
        """
        import random

        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Check if unique
            existing = self.device_repo.get_by_field("activation_code", code)
            if not existing:
                return code
