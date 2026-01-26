"""
Metrics Decorator for Use Cases

Wraps Phase 1 use cases to collect business metrics WITHOUT modifying them.
Uses decorator pattern to maintain Phase 1 immutability.

Source: Phase 2 Design & Execution Plan - Section 3.2
"""

import time
from typing import Any, Generic, TypeVar

from .prometheus_client import (
    core_decisions_total,
    core_decision_latency_seconds,
    core_workflows_total,
    core_errors_total,
)


# Type variables for generic use case
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class MetricsDecorator(Generic[TInput, TOutput]):
    """
    Wraps use cases to collect Prometheus metrics

    Metrics collected:
    - core_decisions_total: Counter by tenant_id, decision_type, outcome
    - core_decision_latency_seconds: Histogram by decision_type
    - core_workflows_total: Counter by tenant_id, state
    - core_errors_total: Counter by error_code

    Example:
        original_use_case = CreateDecisionUseCase(...)
        metrics_use_case = MetricsDecorator(original_use_case, "CreateDecision")

        # Use metrics version (same interface as original)
        output = await metrics_use_case.execute(input_dto)
    """

    def __init__(self, use_case: Any, use_case_name: str):
        """
        Initialize metrics decorator

        Args:
            use_case: Original Phase 1 use case instance
            use_case_name: Name for metrics (e.g., "CreateDecision")
        """
        self._use_case = use_case
        self._use_case_name = use_case_name

    async def execute(self, input_dto: TInput) -> TOutput:
        """
        Execute use case with metrics collection

        Args:
            input_dto: Use case input

        Returns:
            Use case output

        Raises:
            Any exception raised by original use case
        """
        start_time = time.time()

        try:
            # Call Phase 1 use case (UNCHANGED)
            output = await self._use_case.execute(input_dto)

            # Record success metrics
            self._record_success_metrics(input_dto, output, start_time)

            return output

        except Exception as e:
            # Record error metrics
            self._record_error_metrics(e)

            # Re-raise exception (don't swallow it)
            raise

    def _record_success_metrics(self, input_dto: Any, output: Any, start_time: float):
        """
        Record metrics for successful execution

        Args:
            input_dto: Use case input
            output: Use case output
            start_time: Execution start time (Unix timestamp)
        """
        duration = time.time() - start_time

        # Decision creation metrics
        if self._use_case_name == "CreateDecision":
            tenant_id = str(getattr(input_dto, "tenant_id", "unknown"))
            decision_type = getattr(input_dto, "decision_type", "unknown")
            outcome = getattr(output, "outcome", "unknown")

            # Increment decision counter
            if core_decisions_total:
                core_decisions_total.labels(
                    tenant_id=tenant_id,
                    decision_type=decision_type,
                    outcome=outcome
                ).inc()

            # Observe decision latency
            if core_decision_latency_seconds:
                core_decision_latency_seconds.labels(
                    decision_type=decision_type
                ).observe(duration)

        # Workflow metrics
        elif self._use_case_name in ["ApproveWorkflow", "RejectWorkflow", "DelegateWorkflow", "EscalateWorkflow"]:
            tenant_id = str(getattr(input_dto, "tenant_id", "unknown"))
            state = getattr(output, "current_state", "unknown")

            # Increment workflow counter
            if core_workflows_total:
                core_workflows_total.labels(
                    tenant_id=tenant_id,
                    state=state
                ).inc()

    def _record_error_metrics(self, error: Exception):
        """
        Record metrics for failed execution

        Args:
            error: Exception that was raised
        """
        error_code = type(error).__name__

        # Increment error counter
        if core_errors_total:
            core_errors_total.labels(
                error_code=error_code
            ).inc()
