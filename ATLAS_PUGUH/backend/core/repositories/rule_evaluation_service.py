"""
Rule Evaluation Service Implementation

Evaluates rule conditions against decision context.
Source: INFRA-LAY3-002 §1 (Rule Evaluation Engine Standards)
"""

from typing import List, Any

from ..domain import Context, Outcome
from ..use_cases.interfaces import IRuleEvaluationService, Rule, RuleEvaluationResult


class RuleEvaluationService(IRuleEvaluationService):
    """
    Rule evaluation service
    First-match-wins, deterministic evaluation
    Source: INFRA-LAY3-002 §1.1
    """

    async def evaluate(
        self,
        rules: List[Rule],
        context: Context
    ) -> RuleEvaluationResult:
        """
        Evaluate rules against context
        Returns: outcome + matched rule (if any)

        Semantics:
        - First rule that matches → outcome determined
        - Remaining rules skipped
        - No match → outcome DENIED (fail-closed)
        Source: INFRA-LAY3-002 §1.1
        """
        for rule in rules:
            if self._evaluate_conditions(rule.conditions, context):
                outcome = self._extract_outcome(rule.action)
                return RuleEvaluationResult(
                    outcome=outcome,
                    rule_matched_id=rule.rule_id,
                    rule_version=rule.version
                )

        return RuleEvaluationResult(
            outcome=Outcome.DENIED,
            rule_matched_id=None,
            rule_version=None
        )

    def _evaluate_conditions(self, conditions: dict, context: Context) -> bool:
        """
        Evaluate rule conditions
        Source: INFRA-LAY3-002 §1.2 (Condition Evaluation Standards)

        Supported operators:
        - ==, !=, <, <=, >, >= (comparisons)
        - AND, OR, NOT (boolean logic)
        - contains (string substring)
        """
        operator = conditions.get('operator')

        if operator == 'AND':
            return all(
                self._evaluate_conditions(cond, context)
                for cond in conditions.get('conditions', [])
            )

        if operator == 'OR':
            return any(
                self._evaluate_conditions(cond, context)
                for cond in conditions.get('conditions', [])
            )

        if operator == 'NOT':
            inner = conditions.get('condition', {})
            return not self._evaluate_conditions(inner, context)

        field = conditions.get('field')
        value = conditions.get('value')

        if not field:
            return False

        context_value = context.get(field)

        if operator == '==':
            return context_value == value

        if operator == '!=':
            return context_value != value

        if operator == '>':
            return self._safe_compare(context_value, value, lambda a, b: a > b)

        if operator == '>=':
            return self._safe_compare(context_value, value, lambda a, b: a >= b)

        if operator == '<':
            return self._safe_compare(context_value, value, lambda a, b: a < b)

        if operator == '<=':
            return self._safe_compare(context_value, value, lambda a, b: a <= b)

        if operator == 'contains':
            if isinstance(context_value, str) and isinstance(value, str):
                return value in context_value
            return False

        return False

    def _safe_compare(self, context_value: Any, rule_value: Any, comparator) -> bool:
        """
        Safe numeric comparison
        Source: INFRA-LAY3-002 §1.3 (Error Handling)
        Type mismatch → return False (condition does not match)
        """
        try:
            if context_value is None or rule_value is None:
                return False
            return comparator(context_value, rule_value)
        except (TypeError, ValueError):
            return False

    def _extract_outcome(self, action: dict) -> Outcome:
        """
        Extract outcome from rule action
        Default: DENIED (fail-closed)
        """
        outcome_str = action.get('outcome', 'DENIED')

        if outcome_str == 'ALLOWED':
            return Outcome.ALLOWED
        if outcome_str == 'DENIED':
            return Outcome.DENIED
        if outcome_str == 'REQUIRE_APPROVAL':
            return Outcome.REQUIRE_APPROVAL

        return Outcome.DENIED
