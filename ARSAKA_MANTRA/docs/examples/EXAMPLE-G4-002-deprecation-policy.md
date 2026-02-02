# EXAMPLE-G4-002: Deprecation Policy

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G4-002` |
| **group_id** | GROUP-4 (Execution & Evolution) |
| **feature_id** | F-14 (Reversibility & Exit Strategy) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**APIs and features are deprecated with minimum 12-month notice. Deprecation notice cannot be shortened once published.**

---

## Rationale

12-month deprecation window because:

1. **Client Planning**: Enterprise clients have annual planning cycles. 12 months allows budget and resource allocation.

2. **Migration Time**: Complex integrations take months to migrate. 12 months gives buffer for unexpected issues.

3. **Trust Building**: Predictable deprecation builds trust. Clients can depend on our timelines.

4. **Legal Protection**: Some contracts require notice periods. 12 months exceeds most requirements.

5. **Quality Migration**: Rushed migrations cause bugs. Adequate time enables quality transitions.

---

## Deprecation Lifecycle

### Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   Deprecation Timeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NOTICE        ACTIVE DEPRECATION       SUNSET         EOL     │
│  │             │                        │              │        │
│  │◄───────────►│◄──────────────────────►│◄────────────►│        │
│  │   Day 0     │      12 months         │   Grace      │        │
│  │             │                        │   (optional) │        │
│  ▼             ▼                        ▼              ▼        │
│                                                                 │
│  Announce      Deprecation             Service        Remove   │
│  deprecation   warnings active         returns 410    from     │
│                                        Gone           system   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phases

| Phase | Duration | What Happens |
|-------|----------|--------------|
| **Notice** | Day 0 | Deprecation announced via changelog, email, docs |
| **Active Deprecation** | 12 months | Warnings in responses, migration guides available |
| **Sunset** | 1 month grace | Returns 410 Gone with migration info |
| **EOL** | After sunset | Endpoint/feature removed from system |

---

## Deprecation Categories

### API Deprecation

```http
# Deprecated endpoint response
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/customers>; rel="successor-version"
X-Deprecation-Notice: This endpoint will be removed on 2027-01-01.
                       Migrate to /api/v2/customers

{
  "data": [...],
  "_deprecation": {
    "message": "This endpoint is deprecated",
    "sunset_date": "2027-01-01",
    "migration_guide": "https://docs.example.com/migrate/v1-to-v2"
  }
}
```

### Feature Deprecation

```json
{
  "feature": "csv_export",
  "status": "deprecated",
  "deprecated_at": "2025-01-01",
  "sunset_date": "2026-01-01",
  "replacement": "xlsx_export",
  "migration_guide": "https://docs.example.com/migrate/csv-to-xlsx"
}
```

### SDK Deprecation

```python
import warnings

def old_method():
    warnings.warn(
        "old_method is deprecated and will be removed in v3.0.0. "
        "Use new_method instead. "
        "Migration guide: https://docs.example.com/migrate",
        DeprecationWarning,
        stacklevel=2
    )
    return new_method()
```

---

## Constraints

### PROHIBITION
1. **P-001**: Deprecation notice period MUST NOT be shortened after announcement
2. **P-002**: Deprecated APIs MUST NOT be removed before sunset date
3. **P-003**: Sunset date MUST NOT be earlier than 12 months from notice
4. **P-004**: Deprecation MUST NOT proceed without successor/migration path

### REQUIREMENT
1. **R-001**: Deprecation MUST be announced via changelog, email, and documentation
2. **R-002**: Deprecated endpoints MUST include deprecation headers in responses
3. **R-003**: Migration guide MUST be available before deprecation starts
4. **R-004**: Usage metrics MUST be monitored to identify affected clients

### LIMITATION
1. **L-001**: Emergency security deprecation can have 30-day notice (rare, requires VP approval)
2. **L-002**: Internal APIs may have 6-month deprecation window

---

## Invariants

These properties are ALWAYS true:

1. Minimum 12-month notice for public API deprecation
2. Deprecation notice is irrevocable (can extend, not shorten)
3. Migration path exists before deprecation announcement
4. Deprecation is communicated through multiple channels

---

## Implementation Reference

### Deprecation Registry

```python
# config/deprecations.py
DEPRECATIONS = {
    "api.v1.customers": {
        "deprecated_at": "2025-01-01",
        "sunset_date": "2026-01-01",
        "successor": "api.v2.customers",
        "migration_guide": "https://docs.example.com/migrate/customers-v1-v2",
        "reason": "Response format standardization"
    },
    "feature.csv_export": {
        "deprecated_at": "2025-02-01",
        "sunset_date": "2026-02-01",
        "successor": "feature.xlsx_export",
        "migration_guide": "https://docs.example.com/migrate/csv-xlsx",
        "reason": "Better Excel compatibility"
    }
}
```

### Middleware

```python
from fastapi import Request, Response
from datetime import datetime

@app.middleware("http")
async def deprecation_middleware(request: Request, call_next):
    response = await call_next(request)

    # Check if endpoint is deprecated
    endpoint_key = f"api.{request.url.path}"
    deprecation = DEPRECATIONS.get(endpoint_key)

    if deprecation:
        sunset = deprecation["sunset_date"]
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = sunset
        response.headers["Link"] = f'<{deprecation["successor"]}>; rel="successor-version"'

        # Log usage for tracking
        track_deprecated_usage(
            endpoint=endpoint_key,
            client=request.headers.get("X-Client-ID"),
            timestamp=datetime.now()
        )

    return response
```

### Client Notification

```python
def notify_affected_clients(deprecation_key: str):
    """Notify all clients using deprecated endpoint."""

    deprecation = DEPRECATIONS[deprecation_key]
    affected_clients = get_clients_using_endpoint(deprecation_key)

    for client in affected_clients:
        send_email(
            to=client.contact_email,
            subject=f"Deprecation Notice: {deprecation_key}",
            template="deprecation_notice",
            context={
                "endpoint": deprecation_key,
                "sunset_date": deprecation["sunset_date"],
                "migration_guide": deprecation["migration_guide"],
                "successor": deprecation["successor"]
            }
        )

        create_support_ticket(
            client_id=client.id,
            type="deprecation_migration",
            deprecation=deprecation_key
        )
```

---

## Communication Plan

### Announcement Channels

| Channel | When | Content |
|---------|------|---------|
| Changelog | Day 0 | Full deprecation details |
| Email | Day 0 | Personalized notice to affected clients |
| Documentation | Day 0 | Updated docs with deprecation banner |
| API Response | Day 0+ | Deprecation headers in responses |
| Dashboard | Day 0+ | Warning banner in admin UI |
| Reminder Email | Month 6 | Reminder with migration status |
| Final Notice | Month 11 | Final warning, 30 days remaining |

### Email Template

```
Subject: [Action Required] API Deprecation Notice - {endpoint}

Dear {client_name},

We're writing to inform you that the following API will be deprecated:

Endpoint: {endpoint}
Deprecation Date: {deprecation_date}
Sunset Date: {sunset_date}

WHAT YOU NEED TO DO:
1. Review the migration guide: {migration_guide}
2. Update your integration to use: {successor}
3. Test your changes before the sunset date

TIMELINE:
- Now: Begin migration planning
- {sunset_date - 6 months}: Recommended migration completion
- {sunset_date}: Endpoint returns 410 Gone

If you have questions, contact support@example.com or your account manager.

Best regards,
Platform Team
```

---

## Related Decisions

- EXAMPLE-G4-001: API Versioning (versioning triggers deprecation)
- EXAMPLE-G3-002: Approval Authority (deprecation requires approval)
- [Future]: Client Communication Standards (GROUP-3/F-09)

---

## Evolution Path

Deprecation policy may evolve when:
- Client feedback indicates need for different timeline
- Industry standards change
- Business model changes

Example evolution:
```
v1.0.0: "12-month deprecation window"
v1.1.0: "12-month deprecation + automated migration tools"
v2.0.0: "Tiered deprecation: 6 months (minor), 12 months (major), 24 months (platform)"
```

---

## Template Notes

**When adapting this example:**

1. Define your deprecation timeline based on client needs
2. Specify communication channels and templates
3. Include technical implementation (headers, middleware)
4. Document exception processes (security issues)
5. Show client notification workflow
