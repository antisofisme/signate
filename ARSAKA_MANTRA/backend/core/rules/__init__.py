"""
MANTRA Validation Rules Registry

Centralized definition of all validation rules used in the 3-Gate pipeline.

Modules:
- registry: Central rule registry and lookup
- s_rules: Schema validation rules (S-001 to S-022)
- d_rules: Decision consistency rules (D-001 to D-014)
- h_rules: Heuristic/AI validation rules (H-001 to H-010)

Usage:
    from core.rules import RuleRegistry, get_rule, get_rules_by_gate

    # Get specific rule
    rule = get_rule("S-001")

    # Get all rules for Gate 1
    gate1_rules = get_rules_by_gate(1)

    # Validate using rule
    violation = rule.validate(record)
"""

from .registry import (
    Rule,
    RuleRegistry,
    RuleCategory,
    RuleSeverity,
    RuleGate,
    get_rule,
    get_rules_by_gate,
    get_rules_by_category,
    get_all_rules,
)

__all__ = [
    "Rule",
    "RuleRegistry",
    "RuleCategory",
    "RuleSeverity",
    "RuleGate",
    "get_rule",
    "get_rules_by_gate",
    "get_rules_by_category",
    "get_all_rules",
]
