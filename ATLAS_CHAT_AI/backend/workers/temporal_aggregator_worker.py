"""
Temporal Aggregator Worker

Background worker that creates time-based summaries.
"""

from typing import List, Optional, Set
from datetime import datetime, date, timedelta

from .base_worker import ScheduledWorker
from ..core.entities import RequestContext, TimeSummary
from ..core.services.memory_manager import MemoryManager
from ..infrastructure.database.repositories import SessionRepository, MessageRepository
from ..shared.logging import get_logger

logger = get_logger(__name__)


class TemporalAggregatorWorker(ScheduledWorker):
    """
    Creates time-based activity summaries.

    Schedule: Daily at midnight (or every 6 hours for more frequent updates)
    Process:
    1. For each tenant/user combination with activity
    2. Create daily summary (if not exists)
    3. Create weekly summary (on Sundays or after 7 days)
    4. Create monthly summary (on 1st or after month ends)
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
        schedule_seconds: int = 21600,  # 6 hours
    ):
        super().__init__(
            name="temporal_aggregator",
            schedule_seconds=schedule_seconds,
        )
        self.memory_manager = memory_manager
        self.session_repository = session_repository
        self.message_repository = message_repository

    async def process(self) -> None:
        """Create temporal summaries for all active users."""
        logger.info("Starting temporal aggregation run...")

        # Get unique tenant/user combinations with recent activity
        active_users = await self._get_active_users()

        if not active_users:
            logger.debug("No active users for temporal aggregation")
            return

        logger.info(f"Processing temporal summaries for {len(active_users)} users")

        for tenant_id, user_id in active_users:
            try:
                await self._process_user(tenant_id, user_id)
            except Exception as e:
                logger.error(f"Failed to aggregate for {tenant_id}/{user_id}: {e}")

        logger.info("Temporal aggregation complete")

    async def _get_active_users(self) -> List[tuple]:
        """Get tenant/user combinations with recent activity."""
        # Users with activity in the last 7 days
        query = """
            SELECT DISTINCT tenant_id, user_id
            FROM chat_sessions
            WHERE updated_at > NOW() - INTERVAL '7 days'
              AND is_deleted = FALSE
            LIMIT 1000
        """

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [(row["tenant_id"], row["user_id"]) for row in rows]

    async def _process_user(self, tenant_id: str, user_id: str) -> None:
        """Create temporal summaries for a user."""
        ctx = RequestContext(
            request_id=f"worker-temporal-{tenant_id}-{user_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            tenant_config=None,
        )

        today = date.today()

        # Create daily summary for yesterday (if not exists)
        yesterday = today - timedelta(days=1)
        await self._create_daily_summary(ctx, yesterday)

        # Create weekly summary (on Monday for previous week)
        if today.weekday() == 0:  # Monday
            week_start = today - timedelta(days=7)
            await self._create_weekly_summary(ctx, week_start)

        # Create monthly summary (on 1st for previous month)
        if today.day == 1:
            if today.month == 1:
                month_start = date(today.year - 1, 12, 1)
            else:
                month_start = date(today.year, today.month - 1, 1)
            await self._create_monthly_summary(ctx, month_start)

    async def _create_daily_summary(self, ctx: RequestContext, day: date) -> None:
        """Create daily summary if not exists."""
        # Check if already exists
        existing = await self.memory_manager.get_temporal_summary(
            ctx=ctx,
            period_type="day",
            period_start=day,
        )

        if existing:
            logger.debug(f"Daily summary already exists for {day}")
            return

        # Get messages for the day
        messages = await self._get_messages_for_period(
            ctx.tenant_id, ctx.user_id, day, day
        )

        if not messages:
            logger.debug(f"No messages for daily summary {day}")
            return

        # Create summary
        await self.memory_manager.create_temporal_summary(
            ctx=ctx,
            period_type="day",
            period_start=day,
            messages=messages,
        )

        logger.info(f"Created daily summary for {ctx.user_id} on {day}")

    async def _create_weekly_summary(self, ctx: RequestContext, week_start: date) -> None:
        """Create weekly summary if not exists."""
        existing = await self.memory_manager.get_temporal_summary(
            ctx=ctx,
            period_type="week",
            period_start=week_start,
        )

        if existing:
            logger.debug(f"Weekly summary already exists for week of {week_start}")
            return

        week_end = week_start + timedelta(days=6)
        messages = await self._get_messages_for_period(
            ctx.tenant_id, ctx.user_id, week_start, week_end
        )

        if not messages:
            logger.debug(f"No messages for weekly summary {week_start}")
            return

        await self.memory_manager.create_temporal_summary(
            ctx=ctx,
            period_type="week",
            period_start=week_start,
            messages=messages,
        )

        logger.info(f"Created weekly summary for {ctx.user_id} week of {week_start}")

    async def _create_monthly_summary(self, ctx: RequestContext, month_start: date) -> None:
        """Create monthly summary if not exists."""
        existing = await self.memory_manager.get_temporal_summary(
            ctx=ctx,
            period_type="month",
            period_start=month_start,
        )

        if existing:
            logger.debug(f"Monthly summary already exists for {month_start}")
            return

        # Calculate month end
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)

        messages = await self._get_messages_for_period(
            ctx.tenant_id, ctx.user_id, month_start, month_end
        )

        if not messages:
            logger.debug(f"No messages for monthly summary {month_start}")
            return

        await self.memory_manager.create_temporal_summary(
            ctx=ctx,
            period_type="month",
            period_start=month_start,
            messages=messages,
        )

        logger.info(f"Created monthly summary for {ctx.user_id} month of {month_start}")

    async def _get_messages_for_period(
        self,
        tenant_id: str,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> List:
        """Get all messages for a time period."""
        query = """
            SELECT m.id, m.session_id, m.role, m.content,
                   m.token_count, m.created_at
            FROM chat_messages m
            JOIN chat_sessions s ON m.session_id = s.id
            WHERE s.tenant_id = $1
              AND s.user_id = $2
              AND m.created_at >= $3
              AND m.created_at < $4
              AND m.is_deleted = FALSE
            ORDER BY m.created_at ASC
            LIMIT 1000
        """

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, user_id, start_dt, end_dt)

            from ..core.entities import ChatMessage, Role

            messages = []
            for row in rows:
                messages.append(ChatMessage(
                    id=str(row["id"]),
                    session_id=str(row["session_id"]),
                    role=Role(row["role"]),
                    content=row["content"],
                    token_count=row["token_count"],
                    created_at=row["created_at"],
                ))

            return messages


class OnDemandAggregator:
    """
    On-demand temporal aggregation for specific periods.

    Useful for:
    - Generating summaries for date ranges
    - Backfilling historical summaries
    - Custom reporting periods
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        session_repository: SessionRepository,
        message_repository: MessageRepository,
    ):
        self.memory_manager = memory_manager
        self.session_repository = session_repository
        self.message_repository = message_repository

    async def generate_summary(
        self,
        ctx: RequestContext,
        period_type: str,
        period_start: date,
        force: bool = False,
    ) -> Optional[TimeSummary]:
        """
        Generate summary for a specific period.

        Args:
            ctx: Request context
            period_type: 'day', 'week', or 'month'
            period_start: Start date of period
            force: Regenerate even if exists

        Returns:
            TimeSummary or None if no data
        """
        if not force:
            existing = await self.memory_manager.get_temporal_summary(
                ctx=ctx,
                period_type=period_type,
                period_start=period_start,
            )
            if existing:
                return existing

        # Calculate period end
        if period_type == "day":
            period_end = period_start
        elif period_type == "week":
            period_end = period_start + timedelta(days=6)
        elif period_type == "month":
            if period_start.month == 12:
                period_end = date(period_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(period_start.year, period_start.month + 1, 1) - timedelta(days=1)
        else:
            raise ValueError(f"Invalid period_type: {period_type}")

        # Get messages
        messages = await self._get_messages(ctx, period_start, period_end)

        if not messages:
            return None

        # Create summary
        summary_id = await self.memory_manager.create_temporal_summary(
            ctx=ctx,
            period_type=period_type,
            period_start=period_start,
            messages=messages,
        )

        return await self.memory_manager.get_temporal_summary(
            ctx=ctx,
            period_type=period_type,
            period_start=period_start,
        )

    async def _get_messages(
        self,
        ctx: RequestContext,
        start_date: date,
        end_date: date,
    ) -> List:
        """Get messages for date range."""
        query = """
            SELECT m.id, m.session_id, m.role, m.content,
                   m.token_count, m.created_at
            FROM chat_messages m
            JOIN chat_sessions s ON m.session_id = s.id
            WHERE s.tenant_id = $1
              AND s.user_id = $2
              AND m.created_at >= $3
              AND m.created_at < $4
              AND m.is_deleted = FALSE
            ORDER BY m.created_at ASC
            LIMIT 1000
        """

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        pool = self.session_repository._db_pool.pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, ctx.tenant_id, ctx.user_id, start_dt, end_dt)

            from ..core.entities import ChatMessage, Role

            return [
                ChatMessage(
                    id=str(row["id"]),
                    session_id=str(row["session_id"]),
                    role=Role(row["role"]),
                    content=row["content"],
                    token_count=row["token_count"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def backfill(
        self,
        ctx: RequestContext,
        period_type: str,
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Backfill summaries for a date range.

        Returns number of summaries created.
        """
        created = 0
        current = start_date

        while current <= end_date:
            summary = await self.generate_summary(ctx, period_type, current)
            if summary:
                created += 1

            # Move to next period
            if period_type == "day":
                current += timedelta(days=1)
            elif period_type == "week":
                current += timedelta(days=7)
            elif period_type == "month":
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

        return created
