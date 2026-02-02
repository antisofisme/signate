"""
AI Arbiter Module for MANTRA Validator

Provides AI-powered arbitration for ambiguous validation cases:
- Borderline quality scores (50-80)
- Near-duplicate classification (85-95% similarity)
- Medium-severity conflict resolution

Supports TWO modes:
1. SERVER mode: MANTRA's AI does arbitration (costs $)
2. DELEGATED mode: Client AI does arbitration (user's existing AI subscription)

IMPORTANT: AI is NOT called for every validation!
AI arbitration is ONLY invoked when validation results are ambiguous.

Supported AI Providers (SERVER mode):
- Anthropic (Claude)
- OpenAI (GPT-4, GPT-3.5)
- DeepSeek
- Groq
- xAI (Grok)
- OpenRouter (multi-model aggregator)
"""

from .base import (
    ArbiterVerdict,
    ArbiterResult,
    ArbitrationContext,
    ArbitrationMode,
    BaseArbiter
)
from .quality_arbiter import QualityArbiter
from .duplicate_classifier import DuplicateClassifier
from .conflict_arbiter import ConflictArbiter
from .decision_classifier import (
    DecisionClassifier,
    ClassificationResult,
    ClassificationContext,
    get_classification_context,
    validate_classification_result,
)
from .ai_client import (
    AIClient,
    AIConfig,
    AIProvider,
    get_ai_client,
    set_ai_client,
    create_client,
    get_available_providers,
)

__all__ = [
    # Enums and results
    'ArbiterVerdict',
    'ArbiterResult',
    'ArbitrationContext',
    'ArbitrationMode',
    # Base class
    'BaseArbiter',
    # Specific arbiters
    'QualityArbiter',
    'DuplicateClassifier',
    'ConflictArbiter',
    # Decision Classifier (auto-categorization)
    'DecisionClassifier',
    'ClassificationResult',
    'ClassificationContext',
    'get_classification_context',
    'validate_classification_result',
    # AI Client
    'AIClient',
    'AIConfig',
    'AIProvider',
    'get_ai_client',
    'set_ai_client',
    'create_client',
    'get_available_providers',
]
