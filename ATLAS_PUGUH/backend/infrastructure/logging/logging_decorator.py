"""
Logging Decorator for Use Cases

Wraps Phase 1 use cases to add structured logging WITHOUT modifying them.
Uses decorator pattern to maintain Phase 1 immutability.

Source: Phase 2 Design & Execution Plan - Section 3.1
"""

import time
from typing import Any, Generic, TypeVar
from .structured_logger import get_logger


# Type variable for generic use case
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class LoggingDecorator(Generic[TInput, TOutput]):
    """
    Wraps use cases to add structured logging

    Logs:
    - Input (sanitized, no PII)
    - Output (decision_id, outcome)
    - Latency (execution time)
    - Errors (exception type and message)

    Example:
        original_use_case = CreateDecisionUseCase(...)
        logged_use_case = LoggingDecorator(original_use_case, "CreateDecision")

        # Use logged version (same interface as original)
        output = await logged_use_case.execute(input_dto)
    """

    def __init__(self, use_case: Any, use_case_name: str):
        """
        Initialize logging decorator

        Args:
            use_case: Original Phase 1 use case instance
            use_case_name: Name for logging (e.g., "CreateDecision")
        """
        self._use_case = use_case
        self._use_case_name = use_case_name
        self._logger = get_logger(f"core.use_cases.{use_case_name}")

    async def execute(self, input_dto: TInput) -> TOutput:
        """
        Execute use case with logging

        Args:
            input_dto: Use case input

        Returns:
            Use case output

        Raises:
            Any exception raised by original use case
        """
        start_time = time.time()

        # Log input (sanitized)
        self._logger.info(
            f"{self._use_case_name} started",
            extra={
                "action": "execute_start",
                "use_case": self._use_case_name,
                "input": self._sanitize_input(input_dto),
            }
        )

        try:
            # Call Phase 1 use case (UNCHANGED)
            output = await self._use_case.execute(input_dto)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log success
            self._logger.info(
                f"{self._use_case_name} completed successfully",
                extra={
                    "action": "execute_success",
                    "use_case": self._use_case_name,
                    "output": self._sanitize_output(output),
                    "latency_ms": latency_ms,
                }
            )

            return output

        except Exception as e:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log error
            self._logger.error(
                f"{self._use_case_name} failed",
                extra={
                    "action": "execute_error",
                    "use_case": self._use_case_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "latency_ms": latency_ms,
                },
                exc_info=True
            )

            # Re-raise exception (don't swallow it)
            raise

    def _sanitize_input(self, input_dto: Any) -> dict:
        """
        Sanitize input DTO for logging (no PII)

        Strategy: Log field names and types, not values
        """
        sanitized = {
            "type": type(input_dto).__name__,
        }

        # Extract safe fields (IDs, types)
        if hasattr(input_dto, "tenant_id"):
            sanitized["tenant_id"] = str(input_dto.tenant_id)

        if hasattr(input_dto, "decision_type"):
            sanitized["decision_type"] = input_dto.decision_type

        if hasattr(input_dto, "workflow_id"):
            sanitized["workflow_id"] = str(input_dto.workflow_id)

        # Context: log keys only (PII protection)
        if hasattr(input_dto, "context") and input_dto.context:
            sanitized["context_keys"] = list(input_dto.context.keys())

        # Idempotency key (safe to log)
        if hasattr(input_dto, "idempotency_key") and input_dto.idempotency_key:
            sanitized["idempotency_key"] = input_dto.idempotency_key

        return sanitized

    def _sanitize_output(self, output: Any) -> dict:
        """
        Sanitize output DTO for logging

        Strategy: Log IDs and outcomes, not full context
        """
        sanitized = {
            "type": type(output).__name__,
        }

        # Extract safe fields
        if hasattr(output, "decision_id"):
            sanitized["decision_id"] = str(output.decision_id)

        if hasattr(output, "workflow_id") and output.workflow_id:
            sanitized["workflow_id"] = str(output.workflow_id)

        if hasattr(output, "outcome"):
            sanitized["outcome"] = output.outcome

        if hasattr(output, "current_state"):
            sanitized["current_state"] = output.current_state

        if hasattr(output, "rule_matched_id") and output.rule_matched_id:
            sanitized["rule_matched_id"] = str(output.rule_matched_id)

        return sanitized
