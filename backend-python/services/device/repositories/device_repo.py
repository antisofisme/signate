"""
Device Repository Implementation
Implements IDeviceRepository using SQLAlchemy
"""

from typing import Optional, List
from datetime import datetime, timedelta
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

    def list_by_organization(self, organization_id: int) -> List[Device]:
        """List all devices for an organization"""
        device_models = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        ).filter(
            DeviceModel.organization_id == organization_id
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
            last_seen=device.last_seen,
            rotation=device.rotation,
            volume_enabled=device.volume_enabled,
            room_number=device.room_number,
            location_type=device.location_type,
            supports_personalization=device.supports_personalization,
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
        device_model.last_seen = device.last_seen
        device_model.rotation = device.rotation
        device_model.volume_enabled = device.volume_enabled
        device_model.room_number = device.room_number
        device_model.location_type = device.location_type
        device_model.supports_personalization = device.supports_personalization
        device_model.privacy_mode = device.privacy_mode
        device_model.assigned_playlist_id = device.assigned_playlist_id

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

    def update_heartbeat(self, unique_code: str, last_seen: datetime) -> bool:
        """Update device last_seen timestamp (optimized for heartbeat)"""
        result = self.db.query(DeviceModel).filter(
            DeviceModel.unique_code == unique_code.upper()
        ).update({
            'last_seen': last_seen
        })
        self.db.commit()
        return result > 0

    def count_by_organization(self, organization_id: int) -> int:
        """Count devices for organization"""
        return self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id
        ).count()

    def find_online_devices(self, organization_id: int) -> List[Device]:
        """Find online devices (last_seen < 5 minutes ago)"""
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        device_models = self.db.query(DeviceModel).options(
            selectinload(DeviceModel.assigned_playlist),
            selectinload(DeviceModel.tags),
            selectinload(DeviceModel.commands),
            selectinload(DeviceModel.health_metrics)
        ).filter(
            DeviceModel.organization_id == organization_id,
            DeviceModel.status == 'active',
            DeviceModel.last_seen >= five_minutes_ago
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
            last_seen=model.last_seen,
            rotation=model.rotation,
            volume_enabled=model.volume_enabled,
            room_number=model.room_number,
            location_type=model.location_type,
            supports_personalization=model.supports_personalization,
            privacy_mode=model.privacy_mode,
            assigned_playlist_id=model.assigned_playlist_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            released_at=model.released_at
        )
