"""
Billing Services

Business logic services for billing operations.
"""

from .feature_enforcement import (
    FeatureEnforcementService,
    FeatureEnforcementError,
    FeatureNotAvailableError,
    UsageLimitExceededError,
    SubscriptionRequiredError,
    SubscriptionExpiredError,
    FeatureCheckResult,
    UsageCheckResult,
)

from .trial_abuse_prevention import (
    TrialAbusePreventionService,
    TrialAbuseError,
    DisposableEmailError,
    TrialAlreadyUsedError,
    TooManyTrialsError,
    TrialRecord,
    InMemoryTrialRepository,
)

__all__ = [
    # Feature enforcement
    "FeatureEnforcementService",
    "FeatureEnforcementError",
    "FeatureNotAvailableError",
    "UsageLimitExceededError",
    "SubscriptionRequiredError",
    "SubscriptionExpiredError",
    "FeatureCheckResult",
    "UsageCheckResult",
    # Trial abuse prevention
    "TrialAbusePreventionService",
    "TrialAbuseError",
    "DisposableEmailError",
    "TrialAlreadyUsedError",
    "TooManyTrialsError",
    "TrialRecord",
    "InMemoryTrialRepository",
]
