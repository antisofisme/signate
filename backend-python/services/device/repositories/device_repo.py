"""
Device Repository Implementation
Implements IDeviceRepository using SQLAlchemy
"""

from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, selectinload
from ..domain.device import Device
from ..domain.interfaces import IDeviceRepository
from .models import DeviceModel


class DeviceRepository(IDeviceRepository):
    """Device repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, device_id: int, organization_id: Optional[int] = None) -> Optional[Device]:
        """
        Find device by ID with organization isolation

        Args:
            device_id: Device ID
            organization_id: Organization ID for multi-tenant isolation
        """
        query = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        ).filter(DeviceModel.id == device_id)

        # SECURITY: Always filter by organization_id to prevent cross-tenant access
        if organization_id is not None:
            query = query.filter(DeviceModel.organization_id == organization_id)

        device_model = query.first()
        return self._to_entity(device_model) if device_model else None

    def get_by_id(self, device_id: int, organization_id: Optional[int] = None) -> Optional[Device]:
        """
        Get device by ID (alias for find_by_id for compatibility)

        Args:
            device_id: Device ID
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Device entity or None if not found
        """
        return self.find_by_id(device_id, organization_id)

    def find_by_code(self, unique_code: str) -> Optional[Device]:
        """
        Find device by unique activation code
        Note: Activation codes are globally unique so no org filtering needed
        """
        device_model = self.db.query(DeviceModel).filter(
            DeviceModel.unique_code == unique_code.upper()
        ).first()
        return self._to_entity(device_model) if device_model else None

    def find_by_uuid(self, device_uuid: str, organization_id: Optional[int] = None) -> Optional[Device]:
        """
        Find device by UUID (for WebOS) with organization isolation
        
        Args:
            device_uuid: Device UUID
            organization_id: Organization ID for multi-tenant isolation
        """
        query = self.db.query(DeviceModel).filter(DeviceModel.device_uuid == device_uuid)
        
        # SECURITY: Filter by organization_id if provided
        if organization_id is not None:
            query = query.filter(DeviceModel.organization_id == organization_id)
            
        device_model = query.first()
        return self._to_entity(device_model) if device_model else None

    def list_by_organization(self, organization_id: Optional[int]) -> List[Device]:
        """
        List all devices for an organization

        Args:
            organization_id: Organization ID, or None for unassigned devices

        Returns:
            List of Device entities
        """
        query = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        )

        # Handle NULL organization_id for unassigned devices
        if organization_id is None:
            # Filter unassigned devices: show only those created/expired within last 24 hours
            # This prevents showing thousands of old expired devices
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            query = query.filter(
                DeviceModel.organization_id == None,
                DeviceModel.created_at >= twenty_four_hours_ago
            )
        else:
            query = query.filter(DeviceModel.organization_id == organization_id)

        device_models = query.order_by(DeviceModel.created_at.desc()).all()

        return [self._to_entity(model) for model in device_models]

    def list_all(self) -> List[Device]:
        """List all devices regardless of organization (super admin only)"""
        device_models = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        ).order_by(DeviceModel.created_at.desc()).all()

        return [self._to_entity(model) for model in device_models]

    def create(self, device: Device) -> Device:
        """Create new device"""
        device_model = DeviceModel(
            device_type=device.device_type,
            device_name=device.device_name,
            organization_id=device.organization_id,
            unique_code=device.unique_code,
            code_expires_at=device.code_expires_at,
            device_uuid=device.device_uuid,
            ip_address=device.ip_address,
            platform=device.platform,
            screen_width=device.screen_width,
            screen_height=device.screen_height,
            viewport_width=device.viewport_width,
            viewport_height=device.viewport_height,
            device_pixel_ratio=device.device_pixel_ratio,
            user_agent=device.user_agent,
            connection_type=device.connection_type,
            connection_speed=device.connection_speed,
            model_name=device.model_name,
            firmware_version=device.firmware_version,
            status=device.status,
            last_seen_at=device.last_seen_at,
            rotation=device.rotation,
            is_volume_enabled=device.is_volume_enabled,
            room_number=device.room_number,
            location_type=device.location_type,
            is_personalization_supported=device.is_personalization_supported,
            privacy_mode=device.privacy_mode,
            assigned_playlist_id=device.assigned_playlist_id
        )
        self.db.add(device_model)
        self.db.commit()
        self.db.refresh(device_model)
        return self._to_entity(device_model)

    def update(self, device: Device) -> Device:
        """Update existing device"""
        device_model = self.db.query(DeviceModel).filter(DeviceModel.id == device.id).first()
        if not device_model:
            raise ValueError(f"Device with id {device.id} not found")

        # Update all fields
        device_model.device_type = device.device_type
        device_model.device_name = device.device_name
        device_model.organization_id = device.organization_id
        device_model.unique_code = device.unique_code
        device_model.code_expires_at = device.code_expires_at
        device_model.device_uuid = device.device_uuid
        device_model.ip_address = device.ip_address
        device_model.platform = device.platform
        device_model.screen_width = device.screen_width
        device_model.screen_height = device.screen_height
        device_model.viewport_width = device.viewport_width
        device_model.viewport_height = device.viewport_height
        device_model.device_pixel_ratio = device.device_pixel_ratio
        device_model.user_agent = device.user_agent
        device_model.connection_type = device.connection_type
        device_model.connection_speed = device.connection_speed
        device_model.model_name = device.model_name
        device_model.firmware_version = device.firmware_version
        device_model.status = device.status
        device_model.last_seen_at = device.last_seen_at
        device_model.rotation = device.rotation
        device_model.is_volume_enabled = device.is_volume_enabled
        device_model.room_number = device.room_number
        device_model.location_type = device.location_type
        device_model.is_personalization_supported = device.is_personalization_supported
        device_model.privacy_mode = device.privacy_mode
        device_model.assigned_playlist_id = device.assigned_playlist_id

        # Audit trail fields
        if device.updated_by_id is not None:
            device_model.updated_by_id = device.updated_by_id
        if device.deleted_by_id is not None:
            device_model.deleted_by_id = device.deleted_by_id
        if device.deleted_at is not None:
            device_model.deleted_at = device.deleted_at

        self.db.commit()
        self.db.refresh(device_model)
        return self._to_entity(device_model)

    def delete(self, device_id: int) -> bool:
        """Delete device"""
        device_model = self.db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device_model:
            return False

        self.db.delete(device_model)
        self.db.commit()
        return True

    def update_heartbeat(self, unique_code: str, last_seen_at: datetime) -> bool:
        """Update device last_seen_at timestamp (optimized for heartbeat)"""
        result = self.db.query(DeviceModel).filter(
            DeviceModel.unique_code == unique_code.upper()
        ).update({
            'last_seen_at': last_seen_at
        })
        self.db.commit()
        return result > 0

    def count_by_organization(self, organization_id: int) -> int:
        """Count devices for organization"""
        return self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id
        ).count()

    def find_online_devices(self, organization_id: int) -> List[Device]:
        """Find online devices (last_seen_at < 5 minutes ago)"""
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

        device_models = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        ).filter(
            DeviceModel.organization_id == organization_id,
            DeviceModel.status == 'active',
            DeviceModel.last_seen_at >= five_minutes_ago
        ).all()

        return [self._to_entity(model) for model in device_models]

    def _to_entity(self, model: DeviceModel) -> Device:
        """Convert SQLAlchemy model to domain entity"""
        return Device(
            id=model.id,
            device_type=model.device_type,
            device_name=model.device_name,
            organization_id=model.organization_id,
            unique_code=model.unique_code,
            code_expires_at=model.code_expires_at,
            device_uuid=model.device_uuid,
            ip_address=model.ip_address,
            platform=model.platform,
            screen_width=model.screen_width,
            screen_height=model.screen_height,
            viewport_width=model.viewport_width,
            viewport_height=model.viewport_height,
            device_pixel_ratio=model.device_pixel_ratio,
            user_agent=model.user_agent,
            connection_type=model.connection_type,
            connection_speed=model.connection_speed,
            model_name=model.model_name,
            firmware_version=model.firmware_version,
            status=model.status,
            last_seen_at=model.last_seen_at,
            rotation=model.rotation,
            is_volume_enabled=model.is_volume_enabled,
            room_number=model.room_number,
            location_type=model.location_type,
            is_personalization_supported=model.is_personalization_supported,
            privacy_mode=model.privacy_mode,
            assigned_playlist_id=model.assigned_playlist_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            released_at=model.released_at,
            deleted_at=model.deleted_at,
            # Audit trail fields
            created_by_id=model.created_by_id,
            updated_by_id=model.updated_by_id,
            deleted_by_id=model.deleted_by_id
        )
