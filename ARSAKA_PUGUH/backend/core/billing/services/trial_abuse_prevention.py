"""
Trial Abuse Prevention Service

SECURITY: Prevents trial abuse by:
1. Blocking disposable email addresses
2. Limiting trials per email domain (one per organization domain)
3. Tracking trial history to prevent repeat trials
4. Optional IP-based throttling

Usage:
    prevention = TrialAbusePreventionService(trial_repo)
    await prevention.check_can_start_trial(email, ip_address)
"""

from typing import Optional, Set
from uuid import UUID
from dataclasses import dataclass
from datetime import datetime, timedelta
import re


class TrialAbuseError(Exception):
    """Base exception for trial abuse errors."""

    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class DisposableEmailError(TrialAbuseError):
    """Raised when a disposable email is detected."""

    def __init__(self, email: str):
        super().__init__(
            message="Please use a business email address to start a trial",
            code="DISPOSABLE_EMAIL",
            details={
                "email": email,
                "action": "use_business_email",
            }
        )


class TrialAlreadyUsedError(TrialAbuseError):
    """Raised when user/org has already used a trial."""

    def __init__(self, reason: str = "email"):
        super().__init__(
            message="A trial has already been used by your organization",
            code="TRIAL_ALREADY_USED",
            details={
                "reason": reason,
                "action": "contact_sales",
            }
        )


class TooManyTrialsError(TrialAbuseError):
    """Raised when too many trial requests from same source."""

    def __init__(self, cooldown_hours: int):
        super().__init__(
            message="Too many trial requests. Please try again later.",
            code="TOO_MANY_TRIALS",
            details={
                "cooldown_hours": cooldown_hours,
                "action": "wait",
            }
        )


@dataclass
class TrialRecord:
    """Record of a trial signup for abuse detection."""

    email: str
    email_domain: str
    tenant_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    started_at: datetime
    expired_at: Optional[datetime]
    converted: bool = False


class TrialAbusePreventionService:
    """
    Service for preventing trial abuse.

    SECURITY: This is a critical service for preventing revenue loss
    from trial abuse and maintaining fair trial access.
    """

    # Common disposable email domains (partial list, extend as needed)
    DISPOSABLE_DOMAINS: Set[str] = {
        # Popular temporary email services
        "tempmail.com", "temp-mail.org", "guerrillamail.com", "guerrillamail.org",
        "mailinator.com", "throwaway.email", "yopmail.com", "10minutemail.com",
        "fakeinbox.com", "trashmail.com", "getnada.com", "maildrop.cc",
        "discard.email", "sharklasers.com", "spam4.me", "grr.la",
        "guerrillamail.net", "guerrillamail.biz", "tempail.com",
        "tempr.email", "dispostable.com", "mailnesia.com",
        "mintemail.com", "temp.email", "mohmal.com",

        # Additional domains to block
        "mailcatch.com", "10mail.org", "spambox.us", "tempmailaddress.com",
        "emailondeck.com", "fakemailgenerator.com", "throwawaymail.com",
    }

    # Free email providers that might be abused (treat differently from disposable)
    FREE_EMAIL_DOMAINS: Set[str] = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "aol.com", "icloud.com", "protonmail.com", "mail.com",
        "zoho.com", "yandex.com", "gmx.com", "live.com",
        "yahoo.co.id", "yahoo.co.uk", "gmail.co.id",
    }

    # Domains that should always be allowed (verified businesses)
    ALLOWED_DOMAINS: Set[str] = set()

    # Maximum trials per email domain (for free email providers)
    MAX_TRIALS_PER_FREE_EMAIL = 1

    # Maximum trials per business domain
    MAX_TRIALS_PER_BUSINESS_DOMAIN = 3  # Allow multiple for larger companies

    # Cooldown between trial attempts from same IP
    IP_COOLDOWN_HOURS = 24

    def __init__(
        self,
        trial_repo=None,  # Repository to store/query trial history
        strict_mode: bool = True,  # Block disposable emails
    ):
        self._trial_repo = trial_repo
        self._strict_mode = strict_mode

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address."""
        return email.lower().split("@")[-1]

    def _is_disposable_email(self, email: str) -> bool:
        """Check if email is from a disposable email service."""
        domain = self._extract_domain(email)
        return domain in self.DISPOSABLE_DOMAINS

    def _is_free_email(self, email: str) -> bool:
        """Check if email is from a free email provider."""
        domain = self._extract_domain(email)
        return domain in self.FREE_EMAIL_DOMAINS

    def _is_business_email(self, email: str) -> bool:
        """Check if email is from a business domain."""
        return not self._is_free_email(email) and not self._is_disposable_email(email)

    async def check_can_start_trial(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Check if a trial can be started for the given email.

        Raises:
            DisposableEmailError: If email is from disposable service
            TrialAlreadyUsedError: If trial already used for this domain
            TooManyTrialsError: If too many recent trial attempts

        SECURITY: Always call this before creating a trial subscription.
        """
        email = email.lower().strip()
        domain = self._extract_domain(email)

        # Check 1: Block disposable emails
        if self._strict_mode and self._is_disposable_email(email):
            raise DisposableEmailError(email)

        # Check 2: If repo available, check trial history
        if self._trial_repo:
            # Check email exact match (same person)
            existing = await self._trial_repo.find_by_email(email)
            if existing:
                raise TrialAlreadyUsedError(reason="email")

            # Check domain (same organization)
            if self._is_free_email(email):
                # For free email, just check exact email
                pass
            else:
                # For business email, check domain limit
                domain_count = await self._trial_repo.count_by_domain(domain)
                if domain_count >= self.MAX_TRIALS_PER_BUSINESS_DOMAIN:
                    raise TrialAlreadyUsedError(reason="domain")

            # Check 3: IP-based throttling
            if ip_address:
                recent_from_ip = await self._trial_repo.count_recent_by_ip(
                    ip_address,
                    hours=self.IP_COOLDOWN_HOURS
                )
                if recent_from_ip >= 2:  # Max 2 trials per IP per day
                    raise TooManyTrialsError(cooldown_hours=self.IP_COOLDOWN_HOURS)

    async def record_trial_start(
        self,
        email: str,
        tenant_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        trial_days: int = 14,
    ) -> TrialRecord:
        """
        Record a new trial start for future abuse detection.

        Call this AFTER trial subscription is created.
        """
        record = TrialRecord(
            email=email.lower().strip(),
            email_domain=self._extract_domain(email),
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            started_at=datetime.utcnow(),
            expired_at=datetime.utcnow() + timedelta(days=trial_days),
        )

        if self._trial_repo:
            await self._trial_repo.save(record)

        return record

    async def mark_trial_converted(self, tenant_id: UUID) -> None:
        """Mark a trial as converted to paid subscription."""
        if self._trial_repo:
            await self._trial_repo.mark_converted(tenant_id)

    def get_email_risk_score(self, email: str) -> dict:
        """
        Calculate a risk score for an email address.

        Returns dict with:
        - score: 0-100 (higher = more risky)
        - factors: list of risk factors
        - recommendation: "allow", "review", "block"

        SECURITY: Use this for manual review of suspicious signups.
        """
        email = email.lower().strip()
        domain = self._extract_domain(email)
        score = 0
        factors = []

        # Disposable email = high risk
        if self._is_disposable_email(email):
            score += 80
            factors.append("disposable_email_domain")

        # Free email = moderate risk
        if self._is_free_email(email):
            score += 30
            factors.append("free_email_provider")

        # Email patterns that suggest abuse
        # Random-looking local part
        local_part = email.split("@")[0]
        if len(local_part) > 20:
            score += 10
            factors.append("long_local_part")

        if re.match(r"^[a-z0-9]{10,}$", local_part):
            score += 15
            factors.append("random_looking_email")

        # Plus addressing (test+1@example.com)
        if "+" in local_part:
            score += 20
            factors.append("plus_addressing")

        # Numbers at end suggesting multiple accounts
        if re.search(r"\d{3,}$", local_part):
            score += 15
            factors.append("numbered_suffix")

        # Determine recommendation
        if score >= 70:
            recommendation = "block"
        elif score >= 40:
            recommendation = "review"
        else:
            recommendation = "allow"

        return {
            "email": email,
            "domain": domain,
            "score": min(100, score),
            "factors": factors,
            "is_disposable": self._is_disposable_email(email),
            "is_free_email": self._is_free_email(email),
            "is_business_email": self._is_business_email(email),
            "recommendation": recommendation,
        }


# ============================================================================
# Simple In-Memory Trial Repository (for development/testing)
# ============================================================================

class InMemoryTrialRepository:
    """In-memory trial record repository for testing."""

    def __init__(self):
        self._records: dict[str, TrialRecord] = {}

    async def find_by_email(self, email: str) -> Optional[TrialRecord]:
        return self._records.get(email.lower())

    async def count_by_domain(self, domain: str) -> int:
        return sum(
            1 for r in self._records.values()
            if r.email_domain == domain.lower()
        )

    async def count_recent_by_ip(self, ip_address: str, hours: int) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return sum(
            1 for r in self._records.values()
            if r.ip_address == ip_address and r.started_at > cutoff
        )

    async def save(self, record: TrialRecord) -> None:
        self._records[record.email.lower()] = record

    async def mark_converted(self, tenant_id: UUID) -> None:
        for record in self._records.values():
            if record.tenant_id == tenant_id:
                record.converted = True
                break
