"""
Tracing Decorator for Use Cases

Wraps Phase 1 use cases to create explicit spans WITHOUT modifying them.
Uses decorator pattern to maintain Phase 1 immutability.

Source: Phase 2 Design & Execution Plan - Section 3.3
"""

from typing import Any, Generic, TypeVar
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .opentelemetry_config import get_tracer


# Type variables for generic use case
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class TracingDecorator(Generic[TInput, TOutput]):
    """
    Wraps use cases to create distributed tracing spans

    Creates span hierarchy:
    - Parent span: Use case execution
    - Child spans: Auto-instrumented (SQLAlchemy queries)

    Example:
        original_use_case = CreateDecisionUseCase(...)
        traced_use_case = TracingDecorator(original_use_case, "CreateDecision")

        # Use traced version (same interface as original)
        output = await traced_use_case.execute(input_dto)
    """

    def __init__(self, use_case: Any, use_case_name: str):
        """
        Initialize tracing decorator

        Args:
            use_case: Original Phase 1 use case instance
            use_case_name: Name for span (e.g., "CreateDecision")
        """
        self._use_case = use_case
        self._use_case_name = use_case_name
        self._tracer = get_tracer(f"core.use_cases.{use_case_name}")

    async def execute(self, input_dto: TInput) -> TOutput:
        """
        Execute use case with tracing span

        Args:
            input_dto: Use case input

        Returns:
            Use case output

        Raises:
            Any exception raised by original use case
        """
        # Create span for use case execution
        with self._tracer.start_as_current_span(
            f"use_case.{self._use_case_name}.execute",
            attributes=self._get_span_attributes(input_dto)
        ) as span:
            try:
                # Call Phase 1 use case (UNCHANGED)
                output = await self._use_case.execute(input_dto)

                # Mark span as successful
                span.set_status(Status(StatusCode.OK))

                # Add output attributes
                self._add_output_attributes(span, output)

                return output

            except Exception as e:
                # Mark span as error
                span.set_status(
                    Status(StatusCode.ERROR, description=str(e))
                )
                span.record_exception(e)

                # Re-raise exception (don't swallow it)
                raise

    def _get_span_attributes(self, input_dto: Any) -> dict:
        """
        Extract span attributes from input DTO

        Args:
            input_dto: Use case input

        Returns:
            Dictionary of span attributes (safe for tracing, no PII)
        """
        attributes = {
            "use_case.name": self._use_case_name,
            "use_case.input_type": type(input_dto).__name__,
        }

        # Add safe fields (IDs, types)
        if hasattr(input_dto, "tenant_id"):
            attributes["tenant_id"] = str(input_dto.tenant_id)

        if hasattr(input_dto, "decision_type"):
            attributes["decision_type"] = input_dto.decision_type

        if hasattr(input_dto, "workflow_id"):
            attributes["workflow_id"] = str(input_dto.workflow_id)

        # Context: log keys count only (PII protection)
        if hasattr(input_dto, "context") and input_dto.context:
            attributes["context_keys_count"] = len(input_dto.context)

        # Idempotency key (safe to trace)
        if hasattr(input_dto, "idempotency_key") and input_dto.idempotency_key:
            attributes["idempotency_key"] = input_dto.idempotency_key

        return attributes

    def _add_output_attributes(self, span: trace.Span, output: Any):
        """
        Add output attributes to span

        Args:
            span: Current span
            output: Use case output
        """
        span.set_attribute("use_case.output_type", type(output).__name__)

        # Add safe fields
        if hasattr(output, "decision_id"):
            span.set_attribute("decision_id", str(output.decision_id))

        if hasattr(output, "workflow_id") and output.workflow_id:
            span.set_attribute("workflow_id", str(output.workflow_id))

        if hasattr(output, "outcome"):
            span.set_attribute("outcome", output.outcome)

        if hasattr(output, "current_state"):
            span.set_attribute("workflow_state", output.current_state)
