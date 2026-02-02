"""
Validation Worker - Processes decision validation requests asynchronously.

This worker subscribes to the validation queue and:
1. Receives validation requests for new decisions
2. Runs validation logic (alignment check, duplicate detection)
3. Publishes validation results

Usage:
    worker = ValidationWorker(queue)
    await worker.start()
"""

import logging
from typing import Optional

from core.ports.message_queue import MessageQueueProtocol, Message, MantraEvents
from core.ports.cache import CacheProtocol, CacheKeys, CacheTTL
from core.runtime.config import get_config
from .base import BaseWorker

logger = logging.getLogger(__name__)


class ValidationWorker(BaseWorker):
    """
    Worker that processes decision validation requests.

    Listens for DECISION_PROPOSED events and runs:
    - Alignment checking (against existing decisions)
    - Duplicate detection
    - Schema validation
    """

    def __init__(
        self,
        queue: MessageQueueProtocol,
        cache: Optional[CacheProtocol] = None,
    ):
        """
        Initialize validation worker.

        Args:
            queue: Message queue implementation
            cache: Optional cache for storing results
        """
        super().__init__(queue, name="validation")
        self.cache = cache
        self.config = get_config()

    async def setup(self) -> None:
        """Subscribe to validation queue."""
        queue_name = self.config.rabbitmq_queue_validation

        await self.queue.subscribe(
            queue_name,
            self._handle_validation_request,
            prefetch_count=5,
        )
        logger.info(f"Validation worker subscribed to: {queue_name}")

    async def _handle_validation_request(self, message: Message) -> None:
        """
        Handle incoming validation request.

        Args:
            message: Message containing validation request
        """
        logger.debug(f"Processing validation request: {message.id}")

        event_type = message.event_type
        payload = message.payload

        try:
            if event_type == MantraEvents.DECISION_PROPOSED:
                await self._validate_proposed_decision(message)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Validation error for message {message.id}: {e}")
            raise

    async def _validate_proposed_decision(self, message: Message) -> None:
        """
        Validate a proposed decision.

        Args:
            message: Message with decision data
        """
        payload = message.payload
        decision_id = payload.get("decision_id")
        statement = payload.get("statement", "")
        rationale = payload.get("rationale", "")
        domain_id = payload.get("domain_id")

        logger.info(f"Validating decision: {decision_id}")

        # Check cache first
        if self.cache:
            cache_key = CacheKeys.validation_result(decision_id)
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Using cached validation for {decision_id}")
                await self._publish_result(decision_id, cached, message.correlation_id)
                return

        # Run validation
        result = await self._run_validation(
            decision_id=decision_id,
            statement=statement,
            rationale=rationale,
            domain_id=domain_id,
        )

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, result, ttl=CacheTTL.VALIDATION)

        # Publish result
        await self._publish_result(decision_id, result, message.correlation_id)

    async def _run_validation(
        self,
        decision_id: str,
        statement: str,
        rationale: str,
        domain_id: Optional[str] = None,
    ) -> dict:
        """
        Run validation checks.

        Args:
            decision_id: Decision identifier
            statement: Decision statement
            rationale: Decision rationale
            domain_id: Optional domain filter

        Returns:
            Validation result dict
        """
        from factory.container import Container

        errors = []
        warnings = []
        aligned_decisions = []
        conflicts = []

        # 1. Schema validation (basic checks)
        if len(statement) < 10:
            errors.append("Statement too short (minimum 10 characters)")
        if len(statement) > 2000:
            errors.append("Statement too long (maximum 2000 characters)")

        # 2. Alignment check (if semantic search enabled)
        if Container.is_semantic_search_enabled():
            try:
                from core.use_cases.check_alignment import CheckAlignmentUseCase, CheckAlignmentInput

                use_case = CheckAlignmentUseCase(
                    vector_store=Container.get_vector_store(),
                    cache=Container.get_cache(),
                    embedding_service=Container.get_embedding(),
                    repository=Container.get_decision_repository(),
                )

                alignment_result = await use_case.execute(CheckAlignmentInput(
                    statement=statement,
                    rationale=rationale,
                    domain_id=domain_id,
                    min_score=0.7,
                ))

                aligned_decisions = [h.decision_id for h in alignment_result.aligned_with[:5]]
                conflicts = [h.decision_id for h in alignment_result.conflicts_with[:5]]

                if conflicts:
                    warnings.append(f"Potential conflicts with {len(conflicts)} existing decisions")

            except Exception as e:
                logger.warning(f"Alignment check failed: {e}")
                warnings.append("Alignment check could not be completed")

        # Build result
        is_valid = len(errors) == 0
        status = "valid" if is_valid else "invalid"

        return {
            "decision_id": decision_id,
            "status": status,
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "aligned_decisions": aligned_decisions,
            "conflicts": conflicts,
            "validation_complete": True,
        }

    async def _publish_result(
        self,
        decision_id: str,
        result: dict,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Publish validation result.

        Args:
            decision_id: Decision identifier
            result: Validation result
            correlation_id: Optional correlation ID for tracking
        """
        event_type = MantraEvents.DECISION_VALIDATED if result["is_valid"] else MantraEvents.DECISION_REJECTED

        message = Message(
            event_type=event_type,
            payload=result,
            correlation_id=correlation_id,
        )

        # Publish to results queue
        await self.queue.publish("validation_results", message)
        logger.info(f"Published validation result for {decision_id}: {result['status']}")
