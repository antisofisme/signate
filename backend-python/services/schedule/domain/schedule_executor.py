"""
Schedule Execution Service
Background service that monitors and executes schedules
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from services.schedule.repositories.schedule_repo import ScheduleRepository
# from services.playlist.domain.content_resolver import ContentResolver  # Avoid circular import
from services.device.repositories.device_repo import DeviceRepository
from shared.websocket_manager import websocket_manager, WebSocketEventType
from shared.cache import cache
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEvent:
    """Represents a schedule activation/deactivation event"""
    schedule_id: int
    organization_id: int
    playlist_id: int
    event_type: str  # 'activate' or 'deactivate'
    event_time: datetime
    affected_device_ids: List[int]


class ScheduleExecutor:
    """
    Schedule Execution Service
    
    Runs as a background task to:
    1. Monitor active schedules
    2. Detect schedule state changes (activation/deactivation)
    3. Notify affected devices via WebSocket
    4. Update cache for content resolution
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.running = False
        self.check_interval = 60  # Check every minute
        self._active_schedules: Dict[int, Set[int]] = {}  # schedule_id -> device_ids
        self._last_check = None
        self._lock = asyncio.Lock()  # Thread safety for concurrent operations
        
    async def start(self):
        """Start the schedule execution service"""
        if self.running:
            logger.warning("Schedule executor already running")
            return
            
        self.running = True
        logger.info("Starting schedule execution service")
        
        try:
            while self.running:
                await self._check_schedules()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Schedule executor error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Schedule execution service stopped")
    
    async def stop(self):
        """Stop the schedule execution service"""
        logger.info("Stopping schedule execution service")
        self.running = False
    
    async def _check_schedules(self):
        """
        Check all schedules and detect state changes
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get database session
            with self.db_session_factory() as db:
                schedule_repo = ScheduleRepository(db)
                device_repo = DeviceRepository(db)
                
                # Get all organizations with active schedules
                organizations = self._get_organizations_with_schedules(db)
                
                for org_id in organizations:
                    await self._process_organization_schedules(
                        db, org_id, current_time
                    )
                    
            self._last_check = current_time
            
        except Exception as e:
            logger.error(f"Error checking schedules: {e}", exc_info=True)
    
    def _get_organizations_with_schedules(self, db: Session) -> List[int]:
        """Get list of organization IDs that have active schedules"""
        from sqlalchemy import select, distinct
        from services.schedule.repositories.models import Schedule
        
        result = db.execute(
            select(distinct(Schedule.organization_id))
            .where(Schedule.is_active == True)
        )
        
        return [org_id for (org_id,) in result]
    
    async def _process_organization_schedules(
        self, 
        db: Session,
        organization_id: int,
        current_time: datetime
    ):
        """
        Process schedules for a specific organization
        """
        schedule_repo = ScheduleRepository(db)
        device_repo = DeviceRepository(db)
        
        # Get active schedules
        active_schedules = schedule_repo.find_active_schedules(
            organization_id, current_time
        )
        
        # Get current active schedule IDs
        current_active_ids = {s.id for s in active_schedules}
        
        # Get previously active schedule IDs for this org (thread-safe read)
        async with self._lock:
            prev_active_ids = set()
            unknown_schedule_ids = []
            
            for sched_id, devices in self._active_schedules.items():
                # Check if schedule belongs to this org (first check current active list)
                schedule = next((s for s in active_schedules if s.id == sched_id), None)
                if schedule:
                    prev_active_ids.add(sched_id)
                else:
                    # Schedule not in current active list, need to check in DB
                    unknown_schedule_ids.append(sched_id)
            
            # Bulk query for unknown schedules to avoid N+1 problem
            if unknown_schedule_ids:
                org_schedule_ids = self._get_org_schedules_bulk(db, unknown_schedule_ids, organization_id)
                prev_active_ids.update(org_schedule_ids)
        
        # Detect newly activated schedules
        newly_activated = current_active_ids - prev_active_ids
        
        # Detect newly deactivated schedules
        newly_deactivated = prev_active_ids - current_active_ids
        
        # Process activations
        for schedule_id in newly_activated:
            schedule = next(s for s in active_schedules if s.id == schedule_id)
            await self._activate_schedule(db, schedule)
        
        # Process deactivations
        for schedule_id in newly_deactivated:
            await self._deactivate_schedule(db, schedule_id, organization_id)
    
    async def _activate_schedule(self, db: Session, schedule):
        """
        Handle schedule activation
        """
        logger.info(f"Activating schedule {schedule.id}: {schedule.name}")
        
        # Get affected devices
        affected_devices = self._get_affected_devices(db, schedule)
        device_ids = [d.id for d in affected_devices]
        
        # Store active schedule state (thread-safe)
        async with self._lock:
            self._active_schedules[schedule.id] = set(device_ids)
        
        # Clear content resolution cache for affected devices
        for device_id in device_ids:
            cache_key = f"content_resolution:{device_id}"
            cache.delete(cache_key)
        
        # Notify devices via WebSocket
        if device_ids:
            await websocket_manager.broadcast_to_devices(
                device_ids=device_ids,
                event_type=WebSocketEventType.SCHEDULE_ACTIVATED,
                data={
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "playlist_id": schedule.playlist_id,
                    "priority": schedule.priority,
                    "start_time": schedule.start_time.isoformat() if schedule.start_time else None,
                    "end_time": schedule.end_time.isoformat() if schedule.end_time else None
                }
            )
        
        # Notify admins
        await websocket_manager.broadcast_to_organization(
            organization_id=schedule.organization_id,
            event_type=WebSocketEventType.SCHEDULE_ACTIVATED,
            data={
                "schedule_id": schedule.id,
                "schedule_name": schedule.name,
                "affected_devices": len(device_ids)
            }
        )
    
    async def _deactivate_schedule(
        self, 
        db: Session,
        schedule_id: int,
        organization_id: int
    ):
        """
        Handle schedule deactivation
        """
        logger.info(f"Deactivating schedule {schedule_id}")
        
        # Get previously affected devices and remove from active schedules (thread-safe)
        async with self._lock:
            device_ids = list(self._active_schedules.get(schedule_id, []))
            self._active_schedules.pop(schedule_id, None)
        
        # Clear content resolution cache for affected devices
        for device_id in device_ids:
            cache_key = f"content_resolution:{device_id}"
            cache.delete(cache_key)
        
        # Notify devices via WebSocket
        if device_ids:
            await websocket_manager.broadcast_to_devices(
                device_ids=device_ids,
                event_type=WebSocketEventType.SCHEDULE_DEACTIVATED,
                data={
                    "schedule_id": schedule_id
                }
            )
        
        # Notify admins
        await websocket_manager.broadcast_to_organization(
            organization_id=organization_id,
            event_type=WebSocketEventType.SCHEDULE_DEACTIVATED,
            data={
                "schedule_id": schedule_id,
                "affected_devices": len(device_ids)
            }
        )
    
    def _get_affected_devices(self, db: Session, schedule) -> List:
        """
        Get all devices affected by a schedule
        """
        from services.device.repositories.device_repo import DeviceRepository
        from services.tag.repositories.tag_repo import TagRepository
        
        device_repo = DeviceRepository(db)
        tag_repo = TagRepository(db)
        
        affected_devices = []
        
        # Direct device targeting
        if schedule.device_ids:
            for device_id in schedule.device_ids:
                device = device_repo.find_by_id(device_id)
                if device and device.is_active():
                    affected_devices.append(device)
        
        # Tag-based targeting
        elif schedule.tag_ids:
            # Get all devices with specified tags
            from sqlalchemy import text
            query = text("""
                SELECT DISTINCT d.* FROM devices d
                JOIN device_tags dt ON dt.device_id = d.id
                WHERE dt.tag_id = ANY(:tag_ids)
                AND d.organization_id = :org_id
                AND d.status = 'active'
            """)
            
            result = db.execute(query, {
                "tag_ids": schedule.tag_ids,
                "org_id": schedule.organization_id
            })
            
            for row in result:
                device = device_repo._to_entity(row)
                affected_devices.append(device)

        # Apply to all devices
        elif schedule.applies_to_all:
            all_devices = device_repo.list_by_organization(
                schedule.organization_id
            )
            affected_devices = [d for d in all_devices if d.is_active()]
        
        return affected_devices
    
    def _get_org_schedules_bulk(self, db: Session, schedule_ids: List[int], organization_id: int) -> Set[int]:
        """
        Bulk check which schedules belong to an organization
        Optimized to prevent N+1 queries
        
        Args:
            db: Database session
            schedule_ids: List of schedule IDs to check
            organization_id: Organization ID
            
        Returns:
            Set of schedule IDs that belong to the organization
        """
        from services.schedule.repositories.models import Schedule
        
        if not schedule_ids:
            return set()
        
        # Single query to check all schedule IDs
        org_schedules = db.query(Schedule.id).filter(
            Schedule.id.in_(schedule_ids),
            Schedule.organization_id == organization_id
        ).all()
        
        return {schedule_id for (schedule_id,) in org_schedules}
    
    def _was_org_schedule(self, db: Session, schedule_id: int, organization_id: int) -> bool:
        """
        Check if a schedule belongs to an organization
        
        DEPRECATED: Use _get_org_schedules_bulk for better performance
        """
        from services.schedule.repositories.models import Schedule
        
        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id
        ).first()
        
        return schedule and schedule.organization_id == organization_id
    
    async def force_refresh(self, organization_id: Optional[int] = None):
        """
        Force an immediate schedule check
        
        Args:
            organization_id: If specified, only check this organization
        """
        logger.info(f"Forcing schedule refresh for org: {organization_id or 'all'}")
        
        if organization_id:
            with self.db_session_factory() as db:
                await self._process_organization_schedules(
                    db, organization_id, datetime.now(timezone.utc)
                )
        else:
            await self._check_schedules()


# Global schedule executor instance
_schedule_executor: Optional[ScheduleExecutor] = None


def get_schedule_executor() -> ScheduleExecutor:
    """Get the global schedule executor instance"""
    global _schedule_executor
    if _schedule_executor is None:
        raise RuntimeError("Schedule executor not initialized")
    return _schedule_executor


def init_schedule_executor(db_session_factory):
    """Initialize the global schedule executor"""
    global _schedule_executor
    _schedule_executor = ScheduleExecutor(db_session_factory)
    return _schedule_executor
