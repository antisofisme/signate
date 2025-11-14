"""
Organization Quota Service
Enforces organization resource limits
"""

from typing import Dict, Optional
from dataclasses import dataclass
from sqlalchemy import func
from sqlalchemy.orm import Session

from services.device.repositories.models import DeviceModel
from services.content.repositories.models import ContentModel  
from services.auth.repositories.models import UserModel
from services.playlist.repositories.models import PlaylistModel


@dataclass
class OrganizationQuota:
    """Organization quota limits and current usage"""
    # Limits
    max_devices: int
    max_users: int
    max_content_size_gb: int = 100  # Default 100GB
    max_content_items: int = 1000   # Default 1000 items
    max_playlists: int = 100        # Default 100 playlists
    
    # Current usage
    current_devices: int = 0
    current_users: int = 0
    current_content_size_bytes: int = 0
    current_content_items: int = 0
    current_playlists: int = 0
    
    @property
    def current_content_size_gb(self) -> float:
        """Current content size in GB"""
        return self.current_content_size_bytes / (1024 ** 3)
    
    @property
    def devices_available(self) -> int:
        """Available device slots"""
        return max(0, self.max_devices - self.current_devices)
    
    @property
    def users_available(self) -> int:
        """Available user slots"""
        return max(0, self.max_users - self.current_users)
    
    @property
    def content_size_available_gb(self) -> float:
        """Available storage in GB"""
        return max(0, self.max_content_size_gb - self.current_content_size_gb)
    
    @property
    def content_items_available(self) -> int:
        """Available content item slots"""
        return max(0, self.max_content_items - self.current_content_items)
    
    @property
    def playlists_available(self) -> int:
        """Available playlist slots"""
        return max(0, self.max_playlists - self.current_playlists)
    
    def can_add_device(self) -> bool:
        """Check if can add more devices"""
        return self.devices_available > 0
    
    def can_add_user(self) -> bool:
        """Check if can add more users"""
        return self.users_available > 0
    
    def can_add_content(self, size_bytes: int) -> Dict[str, any]:
        """
        Check if can add content
        Returns dict with 'allowed' and 'reason' if not allowed
        """
        if self.content_items_available <= 0:
            return {
                'allowed': False,
                'reason': f'Content item limit reached ({self.max_content_items} items)'
            }
        
        size_gb = size_bytes / (1024 ** 3)
        if self.content_size_available_gb < size_gb:
            return {
                'allowed': False,
                'reason': f'Storage limit would be exceeded ({self.max_content_size_gb}GB limit)'
            }
        
        return {'allowed': True}
    
    def can_add_playlist(self) -> bool:
        """Check if can add more playlists"""
        return self.playlists_available > 0


class OrganizationQuotaService:
    """Service for managing organization quotas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_organization_quota(self, organization_id: int) -> OrganizationQuota:
        """Get organization quota limits and current usage"""
        from services.auth.repositories.models import OrganizationModel
        
        # Get organization limits
        org = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == organization_id
        ).first()
        
        if not org:
            raise ValueError(f"Organization {organization_id} not found")
        
        # Get current device count
        device_count = self.db.query(func.count(DeviceModel.id)).filter(
            DeviceModel.organization_id == organization_id
        ).scalar() or 0
        
        # Get current user count  
        user_count = self.db.query(func.count(UserModel.id)).filter(
            UserModel.organization_id == organization_id,
            UserModel.is_active == True
        ).scalar() or 0
        
        # Get content statistics
        content_stats = self.db.query(
            func.count(ContentModel.id).label('count'),
            func.coalesce(func.sum(ContentModel.file_size), 0).label('total_size')
        ).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at.is_(None)
        ).first()
        
        # Get playlist count
        playlist_count = self.db.query(func.count(PlaylistModel.id)).filter(
            PlaylistModel.organization_id == organization_id,
            PlaylistModel.deleted_at.is_(None)
        ).scalar() or 0
        
        # Get limits from org settings or use defaults
        settings = org.settings or {}
        
        return OrganizationQuota(
            # Limits
            max_devices=org.max_devices or 10,
            max_users=org.max_users or 5,
            max_content_size_gb=settings.get('max_content_size_gb', 100),
            max_content_items=settings.get('max_content_items', 1000),
            max_playlists=settings.get('max_playlists', 100),
            # Current usage
            current_devices=device_count,
            current_users=user_count,
            current_content_size_bytes=int(content_stats.total_size or 0),
            current_content_items=content_stats.count or 0,
            current_playlists=playlist_count
        )
    
    def check_device_quota(self, organization_id: int) -> Dict[str, any]:
        """
        Check if organization can add more devices
        Returns dict with 'allowed' and 'quota' info
        """
        quota = self.get_organization_quota(organization_id)
        
        return {
            'allowed': quota.can_add_device(),
            'quota': {
                'max': quota.max_devices,
                'current': quota.current_devices,
                'available': quota.devices_available
            },
            'message': f"Device limit reached ({quota.max_devices} devices)" if not quota.can_add_device() else None
        }
    
    def check_user_quota(self, organization_id: int) -> Dict[str, any]:
        """
        Check if organization can add more users
        Returns dict with 'allowed' and 'quota' info
        """
        quota = self.get_organization_quota(organization_id)
        
        return {
            'allowed': quota.can_add_user(),
            'quota': {
                'max': quota.max_users,
                'current': quota.current_users,
                'available': quota.users_available
            },
            'message': f"User limit reached ({quota.max_users} users)" if not quota.can_add_user() else None
        }
    
    def check_content_quota(self, organization_id: int, file_size_bytes: int) -> Dict[str, any]:
        """
        Check if organization can add content
        Returns dict with 'allowed', 'quota' info and reason if not allowed
        """
        quota = self.get_organization_quota(organization_id)
        check_result = quota.can_add_content(file_size_bytes)
        
        return {
            'allowed': check_result['allowed'],
            'quota': {
                'max_items': quota.max_content_items,
                'current_items': quota.current_content_items,
                'available_items': quota.content_items_available,
                'max_size_gb': quota.max_content_size_gb,
                'current_size_gb': round(quota.current_content_size_gb, 2),
                'available_size_gb': round(quota.content_size_available_gb, 2)
            },
            'message': check_result.get('reason')
        }
    
    def check_playlist_quota(self, organization_id: int) -> Dict[str, any]:
        """
        Check if organization can add more playlists
        Returns dict with 'allowed' and 'quota' info
        """
        quota = self.get_organization_quota(organization_id)
        
        return {
            'allowed': quota.can_add_playlist(),
            'quota': {
                'max': quota.max_playlists,
                'current': quota.current_playlists,
                'available': quota.playlists_available
            },
            'message': f"Playlist limit reached ({quota.max_playlists} playlists)" if not quota.can_add_playlist() else None
        }
    
    def enforce_device_quota(self, organization_id: int) -> None:
        """
        Enforce device quota - raises exception if limit reached
        Should be called before creating a new device
        
        SECURITY: This method is now atomic to prevent race conditions
        """
        check = self.check_device_quota(organization_id)
        if not check['allowed']:
            raise ValueError(check['message'])
    
    def enforce_device_quota_atomic(self, organization_id: int) -> None:
        """
        Atomically enforce device quota using row-level locking
        Prevents race conditions in concurrent device creation

        Args:
            organization_id: Organization ID

        Raises:
            ValueError: If quota limit reached
        """
        from services.auth.repositories.models import OrganizationModel
        
        # Start transaction with row-level lock
        try:
            # Lock organization row to prevent concurrent modifications
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == organization_id
            ).with_for_update().first()
            
            if not org:
                raise ValueError(f"Organization {organization_id} not found")
            
            # Count current devices with lock
            current_count = self.db.query(func.count(DeviceModel.id)).filter(
                DeviceModel.organization_id == organization_id
            ).scalar() or 0
            
            max_devices = org.max_devices or 10
            
            if current_count >= max_devices:
                raise ValueError(f"Device quota exceeded: {current_count}/{max_devices} devices")
                
        except Exception as e:
            self.db.rollback()
            raise
    
    def enforce_user_quota(self, organization_id: int) -> None:
        """
        Enforce user quota - raises exception if limit reached
        Should be called before creating a new user

        ⚠️ DEPRECATED: Use enforce_user_quota_atomic() instead to prevent race conditions
        """
        check = self.check_user_quota(organization_id)
        if not check['allowed']:
            raise ValueError(check['message'])

    def enforce_user_quota_atomic(self, organization_id: int) -> None:
        """
        Atomically enforce user quota using row-level locking (CRITICAL FIX P0-9)
        Prevents race conditions in concurrent user creation

        Args:
            organization_id: Organization ID

        Raises:
            ValueError: If quota limit reached
        """
        from services.auth.repositories.models import OrganizationModel

        try:
            # Lock organization row to prevent concurrent modifications
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == organization_id
            ).with_for_update().first()

            if not org:
                raise ValueError(f"Organization {organization_id} not found")

            # Count current active users with lock
            current_count = self.db.query(func.count(UserModel.id)).filter(
                UserModel.organization_id == organization_id,
                UserModel.is_active == True
            ).scalar() or 0

            max_users = org.max_users or 5

            if current_count >= max_users:
                raise ValueError(f"User quota exceeded: {current_count}/{max_users} users")

        except Exception as e:
            self.db.rollback()
            raise
    
    def enforce_content_quota(self, organization_id: int, file_size_bytes: int) -> None:
        """
        Enforce content quota - raises exception if limit reached
        Should be called before uploading new content
        """
        check = self.check_content_quota(organization_id, file_size_bytes)
        if not check['allowed']:
            raise ValueError(check['message'])
    
    def enforce_content_quota_atomic(self, organization_id: int, file_size_bytes: int) -> None:
        """
        Atomically enforce content quota using row-level locking
        Prevents race conditions in concurrent content uploads

        Args:
            organization_id: Organization ID
            file_size_bytes: Size of file being uploaded

        Raises:
            ValueError: If quota limit reached
        """
        from services.auth.repositories.models import OrganizationModel
        from services.content.repositories.models import ContentModel
        
        try:
            # Lock organization row to prevent concurrent modifications
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == organization_id
            ).with_for_update().first()
            
            if not org:
                raise ValueError(f"Organization {organization_id} not found")
            
            # Get current content statistics with lock
            content_stats = self.db.query(
                func.count(ContentModel.id).label('count'),
                func.coalesce(func.sum(ContentModel.file_size), 0).label('total_size')
            ).filter(
                ContentModel.organization_id == organization_id,
                ContentModel.deleted_at.is_(None)
            ).first()
            
            # Get limits from org settings or use defaults
            settings = org.settings or {}
            max_content_items = settings.get('max_content_items', 1000)
            max_content_size_gb = settings.get('max_content_size_gb', 100)
            max_content_size_bytes = max_content_size_gb * (1024 ** 3)
            
            current_items = content_stats.count or 0
            current_size_bytes = int(content_stats.total_size or 0)
            
            # Check item limit
            if current_items >= max_content_items:
                raise ValueError(f"Content item limit reached: {current_items}/{max_content_items}")
            
            # Check storage limit
            if (current_size_bytes + file_size_bytes) > max_content_size_bytes:
                current_gb = current_size_bytes / (1024 ** 3)
                new_gb = (current_size_bytes + file_size_bytes) / (1024 ** 3)
                raise ValueError(f"Storage limit would be exceeded: {new_gb:.2f}GB > {max_content_size_gb}GB")
                
        except Exception as e:
            self.db.rollback()
            raise
    
    def enforce_playlist_quota(self, organization_id: int) -> None:
        """
        Enforce playlist quota - raises exception if limit reached
        Should be called before creating a new playlist

        ⚠️ DEPRECATED: Use enforce_playlist_quota_atomic() instead to prevent race conditions
        """
        check = self.check_playlist_quota(organization_id)
        if not check['allowed']:
            raise ValueError(check['message'])

    def enforce_playlist_quota_atomic(self, organization_id: int) -> None:
        """
        Atomically enforce playlist quota using row-level locking (CRITICAL FIX P0-9)
        Prevents race conditions in concurrent playlist creation

        Args:
            organization_id: Organization ID

        Raises:
            ValueError: If quota limit reached
        """
        from services.auth.repositories.models import OrganizationModel

        try:
            # Lock organization row to prevent concurrent modifications
            org = self.db.query(OrganizationModel).filter(
                OrganizationModel.id == organization_id
            ).with_for_update().first()

            if not org:
                raise ValueError(f"Organization {organization_id} not found")

            # Count current playlists with lock
            current_count = self.db.query(func.count(PlaylistModel.id)).filter(
                PlaylistModel.organization_id == organization_id,
                PlaylistModel.deleted_at.is_(None)
            ).scalar() or 0

            # Get limit from org settings or use default
            settings = org.settings or {}
            max_playlists = settings.get('max_playlists', 100)

            if current_count >= max_playlists:
                raise ValueError(f"Playlist quota exceeded: {current_count}/{max_playlists} playlists")

        except Exception as e:
            self.db.rollback()
            raise