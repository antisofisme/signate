"""
Schedule Repository
Data access layer for schedule operations
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func
from datetime import date, time, datetime

from services.schedule.repositories.models import Schedule
from services.schedule.dtos import CreateScheduleRequest, UpdateScheduleRequest


class ScheduleRepository:
    """Repository for schedule data access"""

    def __init__(self, db: Session):
        self.db = db

    def create_schedule(
        self,
        organization_id: int,
        request: CreateScheduleRequest,
        created_by_id: int
    ) -> Schedule:
        """Create new schedule"""
        # Convert RecurrencePattern to dict if present
        recurrence_pattern_dict = None
        if request.recurrence_pattern:
            recurrence_pattern_dict = request.recurrence_pattern.model_dump(exclude_none=True)

        schedule = Schedule(
            organization_id=organization_id,
            name=request.name,
            description=request.description,
            playlist_id=request.playlist_id,
            device_ids=request.device_ids,  # Target devices
            start_date=request.start_date,
            end_date=request.end_date,
            start_time=request.start_time,
            end_time=request.end_time,
            recurrence_type=request.recurrence_type or 'once',
            recurrence_pattern=recurrence_pattern_dict,
            exceptions=request.exception_dates,  # Map DTO exception_dates to DB exceptions column
            color=request.color,
            mode=request.mode,  # 'override' or 'rotate' (Migration 056)
            is_active=request.is_active,
            created_by_id=created_by_id  # Audit trail (Migration 046)
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def get_schedule_by_id(
        self,
        schedule_id: int,
        organization_id: int
    ) -> Optional[Schedule]:
        """Get schedule by ID (excludes soft-deleted)"""
        return self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.id == schedule_id,
                Schedule.organization_id == organization_id,
                Schedule.deleted_at == None  # Exclude soft-deleted
            )
        ).first()

    def get_schedules(
        self,
        organization_id: int,
        playlist_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        recurrence_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Schedule], int]:
        """Get schedules with filters (excludes soft-deleted)"""
        query = self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.deleted_at == None  # Exclude soft-deleted
            )
        )

        if playlist_id is not None:
            query = query.filter(Schedule.playlist_id == playlist_id)
        if is_active is not None:
            query = query.filter(Schedule.is_active == is_active)
        if recurrence_type:
            query = query.filter(Schedule.recurrence_type == recurrence_type)

        total = query.count()
        schedules = query.order_by(
            Schedule.start_date.desc()
        ).offset(skip).limit(limit).all()

        return schedules, total

    def update_schedule(
        self,
        schedule: Schedule,
        request: UpdateScheduleRequest,
        updated_by_id: Optional[int] = None
    ) -> Schedule:
        """Update schedule"""
        update_data = request.model_dump(exclude_none=True)

        # Handle recurrence_pattern separately
        if 'recurrence_pattern' in update_data and update_data['recurrence_pattern']:
            update_data['recurrence_pattern'] = update_data['recurrence_pattern'].model_dump(exclude_none=True)

        # Map exception_dates from DTO to exceptions column in DB
        if 'exception_dates' in update_data:
            update_data['exceptions'] = update_data.pop('exception_dates')

        for key, value in update_data.items():
            setattr(schedule, key, value)

        # Set audit trail (Migration 046)
        if updated_by_id is not None:
            schedule.updated_by_id = updated_by_id

        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def delete_schedule(
        self,
        schedule_id: int,
        organization_id: int,
        deleted_by_id: Optional[int] = None
    ) -> bool:
        """Soft delete schedule with audit tracking"""
        schedule = self.get_schedule_by_id(schedule_id, organization_id)
        if not schedule:
            return False

        # Soft delete with audit tracking
        from datetime import datetime, timezone
        schedule.deleted_at = datetime.now(timezone.utc)
        schedule.is_active = False
        if deleted_by_id is not None:
            schedule.deleted_by_id = deleted_by_id

        self.db.commit()
        return True

    def get_active_schedules_at(
        self,
        organization_id: int,
        check_date: date,
        check_time: Optional[time] = None
    ) -> List[Schedule]:
        """
        Get active schedules at specific date/time
        Returns schedules ordered by start_date (newest first)
        """
        query = self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.is_active == True,
                Schedule.deleted_at == None,  # Exclude soft-deleted
                Schedule.start_date <= check_date,
                or_(
                    Schedule.end_date == None,
                    Schedule.end_date >= check_date
                )
            )
        )

        schedules = query.order_by(Schedule.start_date.desc()).all()

        # Filter by time if provided
        if check_time:
            time_filtered = []
            for schedule in schedules:
                # If no time range specified, schedule is active all day
                if schedule.start_time is None and schedule.end_time is None:
                    time_filtered.append(schedule)
                # Check if current time is within range
                elif schedule.start_time and schedule.end_time:
                    if schedule.start_time <= check_time <= schedule.end_time:
                        time_filtered.append(schedule)
            return time_filtered

        return schedules

    def get_conflicting_schedules(
        self,
        organization_id: int,
        playlist_id: int,
        start_date: date,
        end_date: Optional[date],
        start_time: Optional[time],
        end_time: Optional[time],
        exclude_schedule_id: Optional[int] = None
    ) -> List[Schedule]:
        """Find schedules that conflict with given parameters"""
        query = self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.playlist_id == playlist_id,
                Schedule.is_active == True,
                Schedule.deleted_at == None,  # Exclude soft-deleted
                # Date overlap check
                Schedule.start_date <= (end_date or start_date),
                or_(
                    Schedule.end_date == None,
                    Schedule.end_date >= start_date
                )
            )
        )

        if exclude_schedule_id:
            query = query.filter(Schedule.id != exclude_schedule_id)

        schedules = query.all()

        # Filter by time overlap if time range specified
        if start_time and end_time:
            time_conflicts = []
            for schedule in schedules:
                # If schedule has no time range, it conflicts all day
                if schedule.start_time is None and schedule.end_time is None:
                    time_conflicts.append(schedule)
                # Check time overlap
                elif schedule.start_time and schedule.end_time:
                    # Time ranges overlap if: start1 <= end2 AND end1 >= start2
                    if start_time <= schedule.end_time and end_time >= schedule.start_time:
                        time_conflicts.append(schedule)
            return time_conflicts

        return schedules

    def get_schedules_by_playlist(
        self,
        organization_id: int,
        playlist_id: int
    ) -> List[Schedule]:
        """Get all schedules for a playlist (excludes soft-deleted)"""
        return self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.playlist_id == playlist_id,
                Schedule.deleted_at == None  # Exclude soft-deleted
            )
        ).order_by(Schedule.start_date.desc()).all()

    def deactivate_schedule(
        self,
        schedule_id: int,
        organization_id: int
    ) -> bool:
        """Deactivate schedule (soft delete)"""
        schedule = self.get_schedule_by_id(schedule_id, organization_id)
        if not schedule:
            return False

        schedule.is_active = False
        self.db.commit()
        return True
    
    def find_active_schedules(
        self,
        organization_id: int,
        current_time: datetime
    ) -> List[Schedule]:
        """Find all active schedules for an organization at current time"""
        current_date = current_time.date()

        # Query active schedules (excludes soft-deleted)
        query = self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.is_active == True,
                Schedule.deleted_at == None,  # Exclude soft-deleted
                # Date range check
                or_(
                    Schedule.start_date == None,
                    Schedule.start_date <= current_date
                ),
                or_(
                    Schedule.end_date == None,
                    Schedule.end_date >= current_date
                )
            )
        )

        return query.order_by(Schedule.start_date.desc()).all()

    def get_schedules_for_device(
        self,
        organization_id: int,
        device_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[Schedule]:
        """
        Get schedules for player/device (public endpoint use)

        Filters by:
        - organization_id (required)
        - is_active (default True)
        - device targeting: device_ids contains device_id, or applies_to_all is True

        Returns schedules ordered by start_date (newest first)
        """
        from sqlalchemy import cast, String
        from sqlalchemy.dialects.postgresql import JSONB

        query = self.db.query(Schedule).options(
            selectinload(Schedule.playlist)
        ).filter(
            and_(
                Schedule.organization_id == organization_id,
                Schedule.is_active == is_active,
                Schedule.deleted_at == None  # Exclude soft-deleted
            )
        )

        # If device_id provided, filter by device targeting
        if device_id is not None:
            # Schedule targets this device if:
            # 1. device_ids contains this device_id, OR
            # 2. applies_to_all is True, OR
            # 3. device_ids is NULL/empty AND tag_ids is NULL/empty AND applies_to_all is NULL
            #    (legacy schedules that apply to all)
            query = query.filter(
                or_(
                    # Device explicitly in device_ids array
                    Schedule.device_ids.contains([device_id]),
                    # Applies to all devices
                    Schedule.applies_to_all == True,
                    # Legacy: no targeting specified = applies to all
                    and_(
                        or_(Schedule.device_ids == None, Schedule.device_ids == []),
                        or_(Schedule.tag_ids == None, Schedule.tag_ids == []),
                        or_(Schedule.applies_to_all == None, Schedule.applies_to_all == False)
                    )
                )
            )

        return query.order_by(Schedule.start_date.desc()).all()
