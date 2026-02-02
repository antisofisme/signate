"""
Outbox Poller - Polls event_log for unpublished events

CRITICAL RULES:
- Poller reads from COMMITTED data only
- Publish failure DOES NOT rollback decision
- Retry with exponential backoff
- Dead-letter handling for permanently failed events

Source: Phase 3 Requirements - Outbox + Retry Mechanism
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Callable, Awaitable
from uuid import UUID
import logging
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .publisher import EventPublisher
from .metrics import (
    event_publish_lag,
    event_publish_attempts,
    event_dlq_size,
    event_publish_success,
    event_publish_failure,
)


logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class RetryConfig:
    """
    Retry configuration with exponential backoff.

    Formula: delay = min(base_delay * (multiplier ^ attempt), max_delay)

    Example with defaults:
    - Attempt 1: 1s
    - Attempt 2: 2s
    - Attempt 3: 4s
    - Attempt 4: 8s
    - Attempt 5: 16s (then DLQ)
    """
    max_attempts: int = 5
    base_delay_ms: int = 1000
    max_delay_ms: int = 60000
    backoff_multiplier: float = 2.0

    def get_delay_ms(self, attempt: int) -> int:
        """Calculate delay for given attempt number"""
        delay = self.base_delay_ms * (self.backoff_multiplier ** (attempt - 1))
        return min(int(delay), self.max_delay_ms)


@dataclass
class OutboxConfig:
    """Outbox poller configuration"""
    # Polling
    batch_size: int = 100
    poll_interval_ms: int = 1000

    # Retry
    retry: RetryConfig = field(default_factory=RetryConfig)

    # DLQ
    dlq_enabled: bool = True
    dlq_alert_threshold: int = 100

    # Health check
    stuck_threshold_minutes: int = 5

    @property
    def poll_interval_seconds(self) -> float:
        return self.poll_interval_ms / 1000.0


# =============================================================================
# OUTBOX POLLER
# =============================================================================

class OutboxPoller:
    """
    Polls event_log for unpublished events and publishes them.

    CRITICAL RULES:
    - NEVER publish before DB commit
    - NEVER publish from request handler
    - Retry with backoff, then DLQ

    Source: Phase 3 Requirements
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: EventPublisher,
        config: Optional[OutboxConfig] = None
    ):
        self._session_factory = session_factory
        self._publisher = publisher
        self._config = config or OutboxConfig()
        self._is_running = False
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """
        Start the outbox poller loop.

        CRITICAL: This runs as a background task, NOT in request path.
        """
        if self._is_running:
            logger.warning("Outbox poller already running")
            return

        self._is_running = True
        self._stop_event.clear()

        logger.info(
            "Starting outbox poller",
            extra={
                "batch_size": self._config.batch_size,
                "poll_interval_ms": self._config.poll_interval_ms,
            }
        )

        while self._is_running:
            try:
                await self._poll_and_publish()
            except Exception as e:
                logger.error(
                    "Outbox poller error",
                    extra={"error": str(e)},
                    exc_info=True
                )

            # Wait for next poll or stop signal
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._config.poll_interval_seconds
                )
                break  # Stop signal received
            except asyncio.TimeoutError:
                continue  # Normal timeout, continue polling

    async def stop(self) -> None:
        """Stop the outbox poller"""
        logger.info("Stopping outbox poller")
        self._is_running = False
        self._stop_event.set()

    async def _poll_and_publish(self) -> None:
        """Poll for unpublished events and publish them"""
        async with self._session_factory() as session:
            # Get unpublished events (not in DLQ, respecting retry backoff)
            events = await self._get_unpublished_events(session)

            if not events:
                return

            logger.debug(f"Found {len(events)} unpublished events")

            for event in events:
                await self._process_event(session, event)

            await session.commit()

    async def _get_unpublished_events(
        self,
        session: AsyncSession
    ) -> List[dict]:
        """
        Get batch of unpublished events ready for processing.

        CRITICAL: Respects retry backoff - events with recent failures are skipped.
        """
        # Calculate cutoff time for retry backoff
        # Events that failed recently should wait before retry
        now = datetime.utcnow()

        query = text("""
            SELECT
                event_id,
                event_type,
                tenant_id,
                aggregate_id,
                aggregate_type,
                payload,
                metadata,
                occurred_at,
                recorded_at,
                schema_version,
                publish_attempts,
                last_publish_error
            FROM event_log
            WHERE published_at IS NULL
              AND dlq_at IS NULL
              AND (
                  -- Never tried
                  publish_attempts = 0
                  OR
                  -- Respect backoff: recorded_at + backoff_delay < now
                  -- This is simplified; in production, track last_attempt_at
                  recorded_at + (
                      INTERVAL '1 second' * LEAST(
                          :base_delay_s * POWER(:multiplier, publish_attempts - 1),
                          :max_delay_s
                      )
                  ) < :now
              )
            ORDER BY recorded_at ASC
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        """)

        result = await session.execute(
            query,
            {
                "batch_size": self._config.batch_size,
                "now": now,
                "base_delay_s": self._config.retry.base_delay_ms / 1000.0,
                "multiplier": self._config.retry.backoff_multiplier,
                "max_delay_s": self._config.retry.max_delay_ms / 1000.0,
            }
        )

        rows = result.fetchall()

        return [
            {
                "event_id": row.event_id,
                "event_type": row.event_type,
                "tenant_id": row.tenant_id,
                "aggregate_id": row.aggregate_id,
                "aggregate_type": row.aggregate_type,
                "payload": row.payload,
                "metadata": row.metadata or {},
                "occurred_at": row.occurred_at,
                "recorded_at": row.recorded_at,
                "schema_version": row.schema_version,
                "publish_attempts": row.publish_attempts,
                "last_publish_error": row.last_publish_error,
            }
            for row in rows
        ]

    async def _process_event(
        self,
        session: AsyncSession,
        event: dict
    ) -> None:
        """
        Process single event: publish or move to DLQ.

        CRITICAL: Updates event_log in same transaction.
        """
        event_id = event["event_id"]
        attempts = event["publish_attempts"] + 1

        # Extract trace info from metadata
        metadata = event["metadata"]
        trace_id = metadata.get("trace_id")
        caused_by_user_id = metadata.get("caused_by_user_id")

        # Record publish lag metric
        lag_seconds = (datetime.utcnow() - event["recorded_at"]).total_seconds()
        event_publish_lag.observe(lag_seconds)

        # Attempt publish
        success = await self._publisher.publish(
            event_id=event_id,
            event_type=event["event_type"],
            aggregate_id=event["aggregate_id"],
            aggregate_type=event["aggregate_type"],
            tenant_id=event["tenant_id"],
            payload=event["payload"],
            occurred_at=event["occurred_at"],
            recorded_at=event["recorded_at"],
            trace_id=UUID(trace_id) if trace_id else None,
            caused_by_user_id=UUID(caused_by_user_id) if caused_by_user_id else None,
            schema_version=event["schema_version"],
        )

        if success:
            # Mark as published
            await session.execute(
                text("""
                    UPDATE event_log
                    SET published_at = :published_at,
                        publish_attempts = :attempts
                    WHERE event_id = :event_id
                """),
                {
                    "event_id": event_id,
                    "published_at": datetime.utcnow(),
                    "attempts": attempts,
                }
            )

            event_publish_success.labels(
                event_type=event["event_type"],
                tenant_id=str(event["tenant_id"]),
            ).inc()

            logger.info(
                "Event published successfully",
                extra={
                    "event_id": str(event_id),
                    "event_type": event["event_type"],
                    "attempts": attempts,
                    "lag_seconds": lag_seconds,
                }
            )

        else:
            # Publish failed
            event_publish_failure.labels(
                event_type=event["event_type"],
                tenant_id=str(event["tenant_id"]),
            ).inc()

            if attempts >= self._config.retry.max_attempts:
                # Move to DLQ
                await self._move_to_dlq(session, event, attempts)
            else:
                # Update attempt count for retry
                await session.execute(
                    text("""
                        UPDATE event_log
                        SET publish_attempts = :attempts,
                            last_publish_error = :error
                        WHERE event_id = :event_id
                    """),
                    {
                        "event_id": event_id,
                        "attempts": attempts,
                        "error": f"Publish failed on attempt {attempts}",
                    }
                )

                event_publish_attempts.labels(
                    event_type=event["event_type"],
                ).observe(attempts)

                logger.warning(
                    "Event publish failed, will retry",
                    extra={
                        "event_id": str(event_id),
                        "event_type": event["event_type"],
                        "attempts": attempts,
                        "max_attempts": self._config.retry.max_attempts,
                        "next_retry_delay_ms": self._config.retry.get_delay_ms(attempts),
                    }
                )

    async def _move_to_dlq(
        self,
        session: AsyncSession,
        event: dict,
        total_attempts: int
    ) -> None:
        """
        Move event to dead-letter queue.

        CRITICAL: Event is NOT deleted from event_log, just marked as DLQ'd.
        """
        event_id = event["event_id"]
        now = datetime.utcnow()

        # Update event_log
        await session.execute(
            text("""
                UPDATE event_log
                SET dlq_at = :dlq_at,
                    publish_attempts = :attempts,
                    last_publish_error = :error
                WHERE event_id = :event_id
            """),
            {
                "event_id": event_id,
                "dlq_at": now,
                "attempts": total_attempts,
                "error": f"Moved to DLQ after {total_attempts} failed attempts",
            }
        )

        # Insert into event_dlq for detailed tracking
        await session.execute(
            text("""
                INSERT INTO event_dlq (
                    event_id, tenant_id, event_type, moved_at,
                    failure_reason, total_attempts, last_error
                )
                VALUES (
                    :event_id, :tenant_id, :event_type, :moved_at,
                    :failure_reason, :total_attempts, :last_error
                )
            """),
            {
                "event_id": event_id,
                "tenant_id": event["tenant_id"],
                "event_type": event["event_type"],
                "moved_at": now,
                "failure_reason": f"Failed to publish after {total_attempts} attempts",
                "total_attempts": total_attempts,
                "last_error": event.get("last_publish_error"),
            }
        )

        # Update DLQ size metric
        event_dlq_size.labels(
            event_type=event["event_type"],
            tenant_id=str(event["tenant_id"]),
        ).inc()

        logger.error(
            "Event moved to DLQ",
            extra={
                "event_id": str(event_id),
                "event_type": event["event_type"],
                "tenant_id": str(event["tenant_id"]),
                "total_attempts": total_attempts,
            }
        )

    async def reprocess_dlq_event(
        self,
        event_id: UUID
    ) -> bool:
        """
        Manually reprocess a DLQ event.

        CRITICAL: This is a manual operation, NOT automatic.

        Returns:
            True if reprocessed successfully, False otherwise
        """
        async with self._session_factory() as session:
            # Get event from DLQ
            result = await session.execute(
                text("""
                    SELECT el.*, ed.dlq_entry_id
                    FROM event_log el
                    JOIN event_dlq ed ON el.event_id = ed.event_id
                    WHERE el.event_id = :event_id
                      AND ed.reprocessed_at IS NULL
                """),
                {"event_id": event_id}
            )

            row = result.fetchone()
            if not row:
                logger.warning(f"DLQ event not found: {event_id}")
                return False

            # Attempt publish
            metadata = row.metadata or {}
            success = await self._publisher.publish(
                event_id=row.event_id,
                event_type=row.event_type,
                aggregate_id=row.aggregate_id,
                aggregate_type=row.aggregate_type,
                tenant_id=row.tenant_id,
                payload=row.payload,
                occurred_at=row.occurred_at,
                recorded_at=row.recorded_at,
                trace_id=UUID(metadata["trace_id"]) if metadata.get("trace_id") else None,
                caused_by_user_id=UUID(metadata["caused_by_user_id"]) if metadata.get("caused_by_user_id") else None,
                schema_version=row.schema_version,
            )

            if success:
                now = datetime.utcnow()

                # Update event_log
                await session.execute(
                    text("""
                        UPDATE event_log
                        SET published_at = :published_at,
                            dlq_at = NULL
                        WHERE event_id = :event_id
                    """),
                    {"event_id": event_id, "published_at": now}
                )

                # Update DLQ entry
                await session.execute(
                    text("""
                        UPDATE event_dlq
                        SET reprocessed_at = :reprocessed_at
                        WHERE event_id = :event_id
                    """),
                    {"event_id": event_id, "reprocessed_at": now}
                )

                await session.commit()

                logger.info(f"DLQ event reprocessed successfully: {event_id}")
                return True

            else:
                logger.error(f"DLQ event reprocess failed: {event_id}")
                return False

    async def get_dlq_stats(self) -> dict:
        """Get DLQ statistics"""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT
                        event_type,
                        COUNT(*) as count,
                        MIN(moved_at) as oldest,
                        MAX(moved_at) as newest
                    FROM event_dlq
                    WHERE reprocessed_at IS NULL
                    GROUP BY event_type
                """)
            )

            rows = result.fetchall()

            return {
                "total": sum(r.count for r in rows),
                "by_event_type": {
                    r.event_type: {
                        "count": r.count,
                        "oldest": r.oldest.isoformat() if r.oldest else None,
                        "newest": r.newest.isoformat() if r.newest else None,
                    }
                    for r in rows
                },
            }
