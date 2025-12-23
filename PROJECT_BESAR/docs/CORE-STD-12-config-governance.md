# Development Standards V12

> **Date**: 2025-12-10
> **Standards**: #43 (Config Governance)
> **Status**: Approved

---

## Standard #43: Configuration Governance

### Overview

Standar untuk **mengelola perubahan konfigurasi** secara aman dan terkontrol. Mencakup:

1. **Change Rules** - Kapan dan bagaimana config bisa diubah
2. **Dependencies** - Ketergantungan antar config
3. **Rollback** - Kembalikan ke versi sebelumnya
4. **Notification** - Beritahu pihak terkait
5. **Approval Workflow** - Proses persetujuan
6. **Preview/Simulation** - Simulasi sebelum apply
7. **Cache Invalidation** - Sinkronisasi cache
8. **Import/Export** - Transfer config antar environment
9. **Validation** - Batasan dan validasi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION GOVERNANCE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Config Change Request                                                     │
│          │                                                                  │
│          ▼                                                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │  Validate   │────►│  Approval   │────►│   Apply     │                  │
│   │  & Preview  │     │  Workflow   │     │  & Notify   │                  │
│   └─────────────┘     └─────────────┘     └─────────────┘                  │
│          │                   │                   │                          │
│          ▼                   ▼                   ▼                          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │ Dependencies│     │   Audit     │     │   Cache     │                  │
│   │   Check     │     │   Trail     │     │ Invalidate  │                  │
│   └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 43.1 Config Change Rules

#### 43.1.1 Change Rule Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONFIG CHANGE RULES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. FREE                    2. FUTURE_ONLY                                  │
│  ┌─────────────────┐        ┌─────────────────┐                            │
│  │ Bebas diubah    │        │ Hanya untuk     │                            │
│  │ kapan saja      │        │ transaksi baru  │                            │
│  │                 │        │                 │                            │
│  │ UI settings,    │        │ Tax rate,       │                            │
│  │ notifications   │        │ pricing, fees   │                            │
│  └─────────────────┘        └─────────────────┘                            │
│                                                                             │
│  3. SCHEDULED               4. RECONCILIATION_REQUIRED                      │
│  ┌─────────────────┐        ┌─────────────────┐                            │
│  │ Berlaku mulai   │        │ Perlu review    │                            │
│  │ tanggal tertentu│        │ & adjustment    │                            │
│  │                 │        │                 │                            │
│  │ Rate changes,   │        │ Error fix,      │                            │
│  │ policy updates  │        │ retroactive     │                            │
│  └─────────────────┘        └─────────────────┘                            │
│                                                                             │
│  5. PERIOD_LOCKED                                                           │
│  ┌─────────────────┐                                                        │
│  │ Tidak bisa ubah │                                                        │
│  │ setelah period  │                                                        │
│  │ closed          │                                                        │
│  │                 │                                                        │
│  │ Financial,      │                                                        │
│  │ compliance      │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.1.2 Database Schema

```sql
-- Extend config_definitions dengan change rules
ALTER TABLE config_definitions ADD COLUMN IF NOT EXISTS change_rule VARCHAR(50)
    NOT NULL DEFAULT 'future_only'
    CHECK (change_rule IN ('free', 'future_only', 'scheduled', 'reconciliation_required', 'period_locked'));

ALTER TABLE config_definitions ADD COLUMN IF NOT EXISTS reconciliation_type VARCHAR(50)
    CHECK (reconciliation_type IN ('none', 'auto_adjust', 'manual_review', 'manager_approval'));

ALTER TABLE config_definitions ADD COLUMN IF NOT EXISTS affects_financial BOOLEAN DEFAULT false;

ALTER TABLE config_definitions ADD COLUMN IF NOT EXISTS notification_config JSONB DEFAULT '{}';
-- {"notify_roles": ["finance_manager"], "channels": ["email", "in_app"]}

ALTER TABLE config_definitions ADD COLUMN IF NOT EXISTS approval_config JSONB DEFAULT '{}';
-- {"required_role": "manager", "min_approvers": 1}

-- Config versions dengan effective dates
CREATE TABLE tenant_config_versions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL REFERENCES config_definitions(config_key),
    config_value JSONB NOT NULL,

    -- Effective period
    effective_from DATE NOT NULL,
    effective_to DATE,  -- NULL = currently active

    -- Version info
    version_number INTEGER NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'scheduled', 'superseded', 'rolled_back')),

    -- Audit
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rollback_of INTEGER REFERENCES tenant_config_versions(id),
    rollback_reason TEXT,

    UNIQUE(organization_id, config_key, effective_from)
);

CREATE INDEX idx_config_versions_lookup
    ON tenant_config_versions(organization_id, config_key, effective_from DESC);

CREATE INDEX idx_config_versions_status
    ON tenant_config_versions(organization_id, status) WHERE status IN ('active', 'scheduled');
```

#### 43.1.3 Config Snapshot Pattern

```python
# PENTING: Simpan config values di transaksi, BUKAN lookup saat display!

# ❌ SALAH - Lookup saat display (nilai bisa berubah)
class Bill:
    async def get_tax_amount(self):
        tax_rate = await config.get(self.org_id, "pms.pricing.tax_rate")
        return self.subtotal * tax_rate / 100  # Nilai bisa beda dari saat bill dibuat!

# ✅ BENAR - Simpan snapshot saat create
class BillService:
    async def create_bill(self, org_id: int, reservation_id: int) -> Bill:
        # Snapshot semua config yang relevan saat bill dibuat
        config_snapshot = await self._create_config_snapshot(org_id, [
            "pms.pricing.tax_rate",
            "pms.pricing.service_charge",
            "pms.pricing.room_total_formula",
            "pms.pricing.rounding_method",
        ])

        bill = Bill(
            organization_id=org_id,
            reservation_id=reservation_id,
            subtotal=subtotal,
            # Simpan individual values untuk query/reporting
            tax_rate=config_snapshot["pms.pricing.tax_rate"],
            service_charge=config_snapshot["pms.pricing.service_charge"],
            # Simpan full snapshot untuk audit trail
            config_snapshot=config_snapshot,
            config_snapshot_at=datetime.now(),
        )

        return await self.repository.create(bill)

    async def _create_config_snapshot(
        self,
        org_id: int,
        config_keys: list[str]
    ) -> dict:
        """Create snapshot of config values at current time"""
        snapshot = {}
        for key in config_keys:
            snapshot[key] = await self.config.get(org_id, key)
        return snapshot
```

#### 43.1.4 Change Rule by Config Type

| Config Category | Change Rule | Reconciliation | Example |
|-----------------|-------------|----------------|---------|
| **UI/Display** | `free` | None | theme, language |
| **Operational** | `future_only` | None | default_time, min_stay |
| **Pricing** | `future_only` + `scheduled` | If retroactive | tax_rate, service_charge |
| **Formula** | `future_only` | If retroactive | room_total_formula |
| **Financial** | `period_locked` | Manager approval | currency, rounding |
| **Compliance** | `period_locked` | Multi-level approval | tax_codes |

---

### 43.2 Config Dependencies

#### 43.2.1 Dependency Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONFIG DEPENDENCIES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. FORMULA DEPENDENCY                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  room_total_formula = "room_rate * nights * (1 + tax_rate/100)"     │   │
│  │                                                  ▲                   │   │
│  │                                                  │                   │   │
│  │                                       Uses tax_rate variable        │   │
│  │                                                                      │   │
│  │  Jika tax_rate dihapus → formula BREAK                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. LOGICAL DEPENDENCY                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  require_deposit = true                                              │   │
│  │         │                                                            │   │
│  │         └──► deposit_amount harus ada dan valid                     │   │
│  │                                                                      │   │
│  │  Jika require_deposit=true tapi deposit_amount=0 → invalid          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. TEMPORAL DEPENDENCY                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  checkin_time = "14:00"                                              │   │
│  │  checkout_time = "12:00"                                             │   │
│  │                                                                      │   │
│  │  Constraint: checkout_time < checkin_time (same day)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.2.2 Database Schema for Dependencies

```sql
-- Config dependencies table
CREATE TABLE config_dependencies (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Source config (yang depend)
    source_config_key VARCHAR(100) NOT NULL REFERENCES config_definitions(config_key),

    -- Target config (yang di-depend)
    target_config_key VARCHAR(100) NOT NULL REFERENCES config_definitions(config_key),

    -- Dependency type
    dependency_type VARCHAR(50) NOT NULL
        CHECK (dependency_type IN ('formula', 'logical', 'temporal', 'conditional')),

    -- Dependency details
    dependency_rule JSONB,  -- {"condition": "source.value == true", "requires": "target.value > 0"}

    -- Error message jika dependency tidak terpenuhi
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_config_key, target_config_key)
);

-- Index untuk lookup
CREATE INDEX idx_config_deps_source ON config_dependencies(source_config_key);
CREATE INDEX idx_config_deps_target ON config_dependencies(target_config_key);
```

#### 43.2.3 Dependency Validation Service

```python
class ConfigDependencyService:
    """Service untuk validasi config dependencies"""

    async def validate_change(
        self,
        org_id: int,
        config_key: str,
        new_value: Any
    ) -> DependencyValidationResult:
        """Validate config change against dependencies"""

        errors = []
        warnings = []

        # 1. Check configs that depend on this config
        dependents = await self._get_dependents(config_key)
        for dep in dependents:
            if dep.dependency_type == 'formula':
                # Check if this config is used in any formula
                if not await self._validate_formula_dependency(org_id, dep, new_value):
                    errors.append(f"Config '{dep.source_config_key}' uses this value in formula")

            elif dep.dependency_type == 'logical':
                if not await self._validate_logical_dependency(org_id, dep, new_value):
                    errors.append(dep.error_message)

        # 2. Check configs this config depends on
        dependencies = await self._get_dependencies(config_key)
        for dep in dependencies:
            if not await self._validate_dependency_satisfied(org_id, dep, new_value):
                errors.append(dep.error_message)

        return DependencyValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def validate_delete(
        self,
        config_key: str
    ) -> DependencyValidationResult:
        """Check if config can be deleted (no dependents)"""

        dependents = await self._get_dependents(config_key)
        if dependents:
            return DependencyValidationResult(
                valid=False,
                errors=[
                    f"Cannot delete: used by {', '.join(d.source_config_key for d in dependents)}"
                ]
            )

        return DependencyValidationResult(valid=True)

    async def get_dependency_graph(
        self,
        config_key: str
    ) -> dict:
        """Get full dependency graph for visualization"""

        return {
            "config": config_key,
            "depends_on": await self._get_dependencies(config_key),
            "depended_by": await self._get_dependents(config_key)
        }
```

#### 43.2.4 Auto-Extract Formula Dependencies

```python
async def extract_formula_dependencies(formula: str) -> list[str]:
    """Extract variable names from formula string"""
    import re

    # Find all variable-like tokens (not numbers, not operators)
    pattern = r'\b([a-z_][a-z0-9_]*)\b'
    tokens = re.findall(pattern, formula.lower())

    # Filter out known functions
    functions = {'min', 'max', 'abs', 'round', 'if', 'else'}
    variables = [t for t in tokens if t not in functions]

    return list(set(variables))

# Usage saat save formula config
async def save_formula_config(org_id: int, config_key: str, formula: str):
    # Extract dependencies
    variables = await extract_formula_dependencies(formula)

    # Auto-create dependency records
    for var in variables:
        target_key = await find_config_by_variable_name(var)
        if target_key:
            await create_dependency(
                source=config_key,
                target=target_key,
                type='formula'
            )
```

---

### 43.3 Config Rollback

#### 43.3.1 Rollback Concept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIG ROLLBACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Version Timeline:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  V1          V2          V3          V4 (Rollback)                  │   │
│  │  ┌───┐       ┌───┐       ┌───┐       ┌───┐                          │   │
│  │  │10%│ ───►  │11%│ ───►  │15%│ ───►  │11%│                          │   │
│  │  └───┘       └───┘       └───┘       └───┘                          │   │
│  │  Jan         Feb         Mar ❌       Mar ✓                          │   │
│  │                          (Error)     (Rollback to V2)               │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Rollback creates NEW version with OLD value, not delete history           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.3.2 Rollback Service

```python
class ConfigRollbackService:
    """Service untuk rollback config ke versi sebelumnya"""

    async def get_version_history(
        self,
        org_id: int,
        config_key: str,
        limit: int = 10
    ) -> list[ConfigVersion]:
        """Get version history untuk config"""

        return await self.db.fetch_all("""
            SELECT
                id, config_value, effective_from, effective_to,
                version_number, status, created_by, created_at,
                rollback_of, rollback_reason
            FROM tenant_config_versions
            WHERE organization_id = $1 AND config_key = $2
            ORDER BY version_number DESC
            LIMIT $3
        """, org_id, config_key, limit)

    async def rollback_to_version(
        self,
        org_id: int,
        config_key: str,
        target_version_id: int,
        user_id: int,
        reason: str
    ) -> ConfigRollbackResult:
        """Rollback config ke versi tertentu"""

        # 1. Get target version
        target = await self._get_version(target_version_id)
        if not target:
            raise ConfigVersionNotFoundError()

        # 2. Get current version
        current = await self._get_active_version(org_id, config_key)

        # 3. Check if rollback requires reconciliation
        definition = await self._get_definition(config_key)
        needs_reconciliation = (
            definition.change_rule in ['reconciliation_required', 'period_locked']
            and definition.affects_financial
        )

        if needs_reconciliation:
            # Create reconciliation request instead of direct rollback
            return await self._create_rollback_reconciliation(
                org_id, config_key, current, target, user_id, reason
            )

        # 4. Create new version with old value (rollback)
        new_version = await self._create_rollback_version(
            org_id=org_id,
            config_key=config_key,
            value=target.config_value,
            rollback_of=current.id,
            reason=reason,
            user_id=user_id
        )

        # 5. Mark current as superseded
        await self._supersede_version(current.id)

        # 6. Invalidate cache
        await self._invalidate_cache(org_id, config_key)

        # 7. Send notifications
        await self._notify_rollback(org_id, config_key, current, new_version)

        return ConfigRollbackResult(
            success=True,
            new_version=new_version,
            rolled_back_from=current,
            rolled_back_to=target
        )

    async def _create_rollback_version(
        self,
        org_id: int,
        config_key: str,
        value: Any,
        rollback_of: int,
        reason: str,
        user_id: int
    ) -> ConfigVersion:
        """Create new version for rollback"""

        # Get next version number
        max_version = await self.db.fetch_one("""
            SELECT MAX(version_number) as max_v
            FROM tenant_config_versions
            WHERE organization_id = $1 AND config_key = $2
        """, org_id, config_key)

        next_version = (max_version['max_v'] or 0) + 1

        return await self.db.fetch_one("""
            INSERT INTO tenant_config_versions (
                organization_id, config_key, config_value,
                effective_from, version_number, status,
                created_by, rollback_of, rollback_reason
            ) VALUES ($1, $2, $3, CURRENT_DATE, $4, 'active', $5, $6, $7)
            RETURNING *
        """, org_id, config_key, value, next_version, user_id, rollback_of, reason)
```

#### 43.3.3 Rollback UI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Config History: pms.pricing.tax_rate                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────┬────────┬────────────┬─────────────┬────────────┬───────────────┐ │
│  │ Ver  │ Value  │ Effective  │ Changed By  │ Status     │ Action        │ │
│  ├──────┼────────┼────────────┼─────────────┼────────────┼───────────────┤ │
│  │ V4   │ 11%    │ 15 Mar     │ Admin       │ ● Active   │               │ │
│  │      │        │            │ (rollback)  │            │               │ │
│  ├──────┼────────┼────────────┼─────────────┼────────────┼───────────────┤ │
│  │ V3   │ 15%    │ 10 Mar     │ Admin       │ ○ Rolled   │               │ │
│  │      │        │            │             │   Back     │               │ │
│  ├──────┼────────┼────────────┼─────────────┼────────────┼───────────────┤ │
│  │ V2   │ 11%    │ 01 Feb     │ Manager     │ ○ Super-   │ [Rollback]    │ │
│  │      │        │            │             │   seded    │               │ │
│  ├──────┼────────┼────────────┼─────────────┼────────────┼───────────────┤ │
│  │ V1   │ 10%    │ 01 Jan     │ System      │ ○ Super-   │ [Rollback]    │ │
│  │      │        │            │             │   seded    │               │ │
│  └──────┴────────┴────────────┴─────────────┴────────────┴───────────────┘ │
│                                                                             │
│  V4 Note: "Rollback from V3 - tax rate was incorrect"                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 43.4 Config Notification

#### 43.4.1 Notification Configuration

```sql
-- notification_config in config_definitions
{
    "notify_on_change": true,
    "notify_roles": ["finance_manager", "revenue_manager"],
    "notify_channels": ["email", "in_app"],
    "require_acknowledgment": true,
    "urgent": false
}
```

#### 43.4.2 Notification Service

```python
class ConfigNotificationService:
    """Service untuk notify stakeholders saat config berubah"""

    async def notify_config_change(
        self,
        org_id: int,
        config_key: str,
        old_value: Any,
        new_value: Any,
        changed_by: int,
        change_type: str  # 'update', 'rollback', 'scheduled'
    ):
        """Send notifications for config change"""

        definition = await self._get_definition(config_key)
        notif_config = definition.get('notification_config', {})

        if not notif_config.get('notify_on_change', False):
            return

        # Get users to notify
        recipients = await self._get_recipients(
            org_id,
            notif_config.get('notify_roles', [])
        )

        # Prepare notification content
        notification = ConfigChangeNotification(
            config_key=config_key,
            config_name=definition['config_name'],
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_type=change_type,
            require_ack=notif_config.get('require_acknowledgment', False),
            urgent=notif_config.get('urgent', False)
        )

        # Send via configured channels
        channels = notif_config.get('notify_channels', ['in_app'])

        for channel in channels:
            if channel == 'email':
                await self._send_email_notification(recipients, notification)
            elif channel == 'in_app':
                await self._send_inapp_notification(recipients, notification)
            elif channel == 'whatsapp':
                await self._send_whatsapp_notification(recipients, notification)

    async def get_pending_acknowledgments(
        self,
        org_id: int,
        user_id: int
    ) -> list[ConfigChangeNotification]:
        """Get config changes that need user acknowledgment"""

        return await self.db.fetch_all("""
            SELECT cn.*
            FROM config_change_notifications cn
            LEFT JOIN config_acknowledgments ca
                ON ca.notification_id = cn.id AND ca.user_id = $2
            WHERE cn.organization_id = $1
              AND cn.require_acknowledgment = true
              AND ca.id IS NULL
            ORDER BY cn.created_at DESC
        """, org_id, user_id)

    async def acknowledge_change(
        self,
        notification_id: int,
        user_id: int
    ):
        """User acknowledges they've seen the config change"""

        await self.db.execute("""
            INSERT INTO config_acknowledgments (notification_id, user_id, acknowledged_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (notification_id, user_id) DO NOTHING
        """, notification_id, user_id)
```

#### 43.4.3 Acknowledgment Tracking

```sql
-- Config change notifications
CREATE TABLE config_change_notifications (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    config_key VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    change_type VARCHAR(20) NOT NULL,  -- 'update', 'rollback', 'scheduled'
    changed_by INTEGER REFERENCES users(id),
    require_acknowledgment BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Acknowledgments
CREATE TABLE config_acknowledgments (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES config_change_notifications(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(notification_id, user_id)
);

CREATE INDEX idx_config_notif_org ON config_change_notifications(organization_id, created_at DESC);
CREATE INDEX idx_config_ack_user ON config_acknowledgments(user_id, acknowledged_at DESC);
```

---

### 43.5 Config Approval Workflow

#### 43.5.1 Approval Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONFIG APPROVAL WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┬─────────────────────┬───────────────────────┐        │
│  │ Config Category  │ Approval Required   │ Approver              │        │
│  ├──────────────────┼─────────────────────┼───────────────────────┤        │
│  │ UI/Display       │ None                │ Self-approve          │        │
│  │ Operational      │ Supervisor          │ Duty Manager          │        │
│  │ Pricing          │ Manager             │ Revenue Manager       │        │
│  │ Financial        │ Director            │ Finance Director      │        │
│  │ Compliance       │ Multi-level         │ GM → Legal → CFO      │        │
│  │ Retroactive      │ Manager + Finance   │ Dept Head + Finance   │        │
│  └──────────────────┴─────────────────────┴───────────────────────┘        │
│                                                                             │
│  Workflow:                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Request │───►│ Pending │───►│Approved │───►│ Applied │                 │
│  └─────────┘    └────┬────┘    └─────────┘    └─────────┘                 │
│                      │                                                      │
│                      ▼                                                      │
│                 ┌─────────┐                                                 │
│                 │Rejected │                                                 │
│                 └─────────┘                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.5.2 Approval Database Schema

```sql
-- Config change requests (for approval workflow)
CREATE TABLE config_change_requests (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    config_key VARCHAR(100) NOT NULL,

    -- Change details
    current_value JSONB,
    requested_value JSONB,
    effective_from DATE,
    change_reason TEXT,

    -- Request info
    requested_by INTEGER NOT NULL REFERENCES users(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'applied', 'cancelled')),

    -- Impact analysis
    impact_analysis JSONB,  -- {"affected_transactions": 45, "total_adjustment": 2450000}

    -- Approval details
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Application
    applied_at TIMESTAMPTZ,
    applied_version_id INTEGER REFERENCES tenant_config_versions(id)
);

-- Multi-level approvals
CREATE TABLE config_approval_steps (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES config_change_requests(id),
    step_order INTEGER NOT NULL,
    required_role VARCHAR(100) NOT NULL,

    -- Approval
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'skipped')),
    comments TEXT,

    UNIQUE(request_id, step_order)
);

CREATE INDEX idx_config_requests_org ON config_change_requests(organization_id, status);
CREATE INDEX idx_config_requests_pending ON config_change_requests(status, requested_at)
    WHERE status = 'pending';
```

#### 43.5.3 Approval Service

```python
class ConfigApprovalService:
    """Service untuk manage config approval workflow"""

    async def create_change_request(
        self,
        org_id: int,
        config_key: str,
        new_value: Any,
        effective_from: date,
        reason: str,
        user_id: int
    ) -> ConfigChangeRequest:
        """Create config change request"""

        definition = await self._get_definition(config_key)
        current_value = await self.config.get(org_id, config_key)

        # Calculate impact if financial config
        impact = None
        if definition.affects_financial and effective_from < date.today():
            impact = await self._calculate_impact(
                org_id, config_key, current_value, new_value, effective_from
            )

        # Create request
        request = await self.db.fetch_one("""
            INSERT INTO config_change_requests (
                organization_id, config_key, current_value, requested_value,
                effective_from, change_reason, requested_by, impact_analysis
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """, org_id, config_key, current_value, new_value,
             effective_from, reason, user_id, impact)

        # Create approval steps based on approval_config
        approval_config = definition.get('approval_config', {})
        await self._create_approval_steps(request.id, approval_config)

        # Notify approvers
        await self._notify_approvers(request)

        return request

    async def approve_step(
        self,
        request_id: int,
        user_id: int,
        comments: str = None
    ) -> ApprovalResult:
        """Approve current step in workflow"""

        # Get pending step for this user's role
        step = await self._get_pending_step_for_user(request_id, user_id)
        if not step:
            raise ApprovalError("No pending approval step for this user")

        # Mark step as approved
        await self.db.execute("""
            UPDATE config_approval_steps
            SET approved_by = $1, approved_at = NOW(), status = 'approved', comments = $2
            WHERE id = $3
        """, user_id, comments, step.id)

        # Check if all steps approved
        all_approved = await self._check_all_steps_approved(request_id)

        if all_approved:
            # Apply the config change
            return await self._apply_approved_request(request_id, user_id)

        # Notify next approver
        await self._notify_next_approver(request_id)

        return ApprovalResult(status='pending_next_approval')

    async def reject_request(
        self,
        request_id: int,
        user_id: int,
        reason: str
    ) -> ApprovalResult:
        """Reject config change request"""

        await self.db.execute("""
            UPDATE config_change_requests
            SET status = 'rejected', approved_by = $1, approved_at = NOW(),
                rejection_reason = $2
            WHERE id = $3
        """, user_id, reason, request_id)

        # Notify requester
        await self._notify_rejection(request_id, reason)

        return ApprovalResult(status='rejected', reason=reason)
```

---

### 43.6 Config Preview/Simulation

#### 43.6.1 Preview Service

```python
class ConfigPreviewService:
    """Service untuk preview/simulate config change impact"""

    async def preview_change(
        self,
        org_id: int,
        config_key: str,
        new_value: Any,
        effective_from: date = None
    ) -> ConfigPreviewResult:
        """Preview impact of config change"""

        definition = await self._get_definition(config_key)
        current_value = await self.config.get(org_id, config_key)

        result = ConfigPreviewResult(
            config_key=config_key,
            current_value=current_value,
            new_value=new_value,
            effective_from=effective_from or date.today()
        )

        # 1. Sample calculation comparison
        if definition.config_type in ['number', 'formula']:
            result.sample_calculations = await self._generate_sample_calculations(
                org_id, config_key, current_value, new_value
            )

        # 2. Affected transactions (if retroactive)
        if effective_from and effective_from < date.today():
            result.affected_transactions = await self._count_affected_transactions(
                org_id, config_key, effective_from
            )
            result.total_adjustment = await self._calculate_total_adjustment(
                org_id, config_key, current_value, new_value, effective_from
            )

        # 3. Dependencies impact
        result.dependency_warnings = await self._check_dependency_impact(
            org_id, config_key, new_value
        )

        # 4. Approval requirements
        result.requires_approval = await self._check_approval_required(
            definition, effective_from
        )

        return result

    async def _generate_sample_calculations(
        self,
        org_id: int,
        config_key: str,
        old_value: Any,
        new_value: Any
    ) -> list[SampleCalculation]:
        """Generate before/after sample calculations"""

        samples = []

        # Get sample scenarios based on config type
        if 'tax' in config_key or 'service' in config_key:
            scenarios = [
                {"room_rate": 500000, "nights": 1, "label": "1 Night Standard"},
                {"room_rate": 500000, "nights": 3, "label": "3 Nights Standard"},
                {"room_rate": 1000000, "nights": 2, "label": "2 Nights Suite"},
            ]

            for scenario in scenarios:
                before = await self._calculate_with_value(
                    org_id, scenario, config_key, old_value
                )
                after = await self._calculate_with_value(
                    org_id, scenario, config_key, new_value
                )

                samples.append(SampleCalculation(
                    label=scenario['label'],
                    before=before,
                    after=after,
                    difference=after - before,
                    percentage_change=((after - before) / before * 100) if before else 0
                ))

        return samples
```

#### 43.6.2 Preview UI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Preview: Change tax_rate 11% → 12%                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Sample Calculations:                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ Scenario              │ Before (11%)  │ After (12%)   │ Difference    ││
│  ├───────────────────────┼───────────────┼───────────────┼───────────────┤│
│  │ 1 Night Standard      │ Rp 555,000    │ Rp 560,000    │ +Rp 5,000     ││
│  │ 3 Nights Standard     │ Rp 1,665,000  │ Rp 1,680,000  │ +Rp 15,000    ││
│  │ 2 Nights Suite        │ Rp 2,220,000  │ Rp 2,240,000  │ +Rp 20,000    ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ⚠️  Retroactive Impact (if effective from 01/12/2024):                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ • 45 bills will be affected                                            ││
│  │ • Total adjustment: Rp 2,450,000                                       ││
│  │ • Requires manager approval                                            ││
│  │ • Accounting adjustment entries will be created                        ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Dependencies:                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ ✓ room_total_formula uses tax_rate - will use new value               ││
│  │ ✓ No circular dependencies detected                                    ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  [ Cancel ]                    [ Apply Immediately ]  [ Schedule ]         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 43.7 Config Cache Invalidation

#### 43.7.1 Cache Invalidation Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CACHE INVALIDATION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Config Change                                                              │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────┐                                                            │
│  │   Redis     │ ◄─── DELETE config:{org}:{key}                            │
│  │   Cache     │                                                            │
│  └─────────────┘                                                            │
│       │                                                                     │
│       │ Publish: config.changed.{org}.{key}                                │
│       ▼                                                                     │
│  ┌─────────────┐                                                            │
│  │  RabbitMQ   │                                                            │
│  │  Exchange   │                                                            │
│  └─────────────┘                                                            │
│       │                                                                     │
│       ├───────────────────┬───────────────────┐                            │
│       ▼                   ▼                   ▼                             │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐                       │
│  │ API     │         │ Worker  │         │ Worker  │                       │
│  │ Server  │         │ Node 1  │         │ Node 2  │                       │
│  │         │         │         │         │         │                       │
│  │ Clear   │         │ Clear   │         │ Clear   │                       │
│  │ Local   │         │ Local   │         │ Local   │                       │
│  │ Cache   │         │ Cache   │         │ Cache   │                       │
│  └─────────┘         └─────────┘         └─────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.7.2 Cache Invalidation Implementation

```python
class ConfigCacheService:
    """Service untuk manage config caching dan invalidation"""

    def __init__(self, redis: Redis, rabbitmq: RabbitMQ):
        self.redis = redis
        self.rabbitmq = rabbitmq
        self.local_cache = TTLCache(maxsize=1000, ttl=60)  # 1 minute local cache

    async def get(self, org_id: int, config_key: str) -> Any:
        """Get config with multi-level caching"""

        cache_key = f"config:{org_id}:{config_key}"

        # 1. Check local cache (fastest)
        if cache_key in self.local_cache:
            return self.local_cache[cache_key]

        # 2. Check Redis cache
        cached = await self.redis.get(cache_key)
        if cached:
            self.local_cache[cache_key] = cached
            return cached

        # 3. Query database
        value = await self._fetch_from_db(org_id, config_key)

        # 4. Store in both caches
        await self.redis.set(cache_key, value, ex=300)  # 5 min Redis TTL
        self.local_cache[cache_key] = value

        return value

    async def invalidate(self, org_id: int, config_key: str):
        """Invalidate config cache across all nodes"""

        cache_key = f"config:{org_id}:{config_key}"

        # 1. Delete from Redis
        await self.redis.delete(cache_key)

        # 2. Clear local cache
        self.local_cache.pop(cache_key, None)

        # 3. Broadcast to all nodes via RabbitMQ
        await self.rabbitmq.publish(
            exchange='config_events',
            routing_key=f'config.invalidated.{org_id}',
            message={
                'event': 'config_invalidated',
                'org_id': org_id,
                'config_key': config_key,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def handle_invalidation_event(self, message: dict):
        """Handle cache invalidation event from other nodes"""

        cache_key = f"config:{message['org_id']}:{message['config_key']}"
        self.local_cache.pop(cache_key, None)


# Setup consumer on application startup
async def setup_cache_invalidation_consumer(cache_service: ConfigCacheService):
    """Setup RabbitMQ consumer for cache invalidation events"""

    await rabbitmq.consume(
        queue='config_cache_invalidation',
        exchange='config_events',
        routing_key='config.invalidated.*',
        callback=cache_service.handle_invalidation_event
    )
```

---

### 43.8 Config Import/Export

#### 43.8.1 Export Format

```python
class ConfigExportService:
    """Service untuk export/import config"""

    async def export_configs(
        self,
        org_id: int,
        module: str = None,
        include_history: bool = False
    ) -> ConfigExport:
        """Export configs to portable format"""

        query = """
            SELECT
                cd.config_key, cd.config_name, cd.config_type,
                cd.module, cd.category, cd.default_value,
                cd.validation_rules, cd.ui_config, cd.change_rule,
                COALESCE(tc.config_value, cd.default_value) as current_value
            FROM config_definitions cd
            LEFT JOIN tenant_configs tc
                ON tc.config_key = cd.config_key
                AND tc.organization_id = $1
            WHERE cd.is_active = true
        """

        if module:
            query += f" AND cd.module = '{module}'"

        configs = await self.db.fetch_all(query, org_id)

        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "organization_id": org_id,
            "module": module,
            "configs": [
                {
                    "key": c['config_key'],
                    "value": c['current_value'],
                    "is_default": c['current_value'] == c['default_value']
                }
                for c in configs
            ]
        }

        if include_history:
            export_data["history"] = await self._export_history(org_id, module)

        return ConfigExport(**export_data)

    async def import_configs(
        self,
        org_id: int,
        import_data: ConfigExport,
        user_id: int,
        mode: str = 'merge'  # 'merge', 'replace', 'skip_existing'
    ) -> ConfigImportResult:
        """Import configs from export file"""

        results = {
            'imported': [],
            'skipped': [],
            'errors': []
        }

        for config in import_data.configs:
            try:
                # Check if config definition exists
                definition = await self._get_definition(config['key'])
                if not definition:
                    results['errors'].append({
                        'key': config['key'],
                        'error': 'Config definition not found'
                    })
                    continue

                # Check existing value
                existing = await self.config.get(org_id, config['key'])

                if existing and mode == 'skip_existing':
                    results['skipped'].append(config['key'])
                    continue

                # Validate value
                await self._validate_value(definition, config['value'])

                # Import
                await self.config.set(
                    org_id=org_id,
                    config_key=config['key'],
                    value=config['value'],
                    user_id=user_id,
                    reason=f"Imported from export file"
                )

                results['imported'].append(config['key'])

            except Exception as e:
                results['errors'].append({
                    'key': config['key'],
                    'error': str(e)
                })

        return ConfigImportResult(**results)
```

#### 43.8.2 Export File Format

```yaml
# config_export_2024-12-10.yaml
version: "1.0"
exported_at: "2024-12-10T14:30:00Z"
organization_id: 123
module: "pms"

configs:
  - key: "pms.pricing.tax_rate"
    value: 11
    is_default: false

  - key: "pms.pricing.service_charge"
    value: 10
    is_default: false

  - key: "pms.checkin.default_time"
    value: "14:00"
    is_default: true

  - key: "pms.checkout.default_time"
    value: "12:00"
    is_default: true

# Optional history
history:
  - key: "pms.pricing.tax_rate"
    versions:
      - version: 1
        value: 10
        effective_from: "2024-01-01"
      - version: 2
        value: 11
        effective_from: "2024-06-01"
```

#### 43.8.3 Import UI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Import Configuration                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  File: [ config_export_2024-12-10.yaml        ] [Browse]                   │
│                                                                             │
│  Import Mode:                                                               │
│  ○ Merge (update existing, add new)                                        │
│  ○ Replace (overwrite all)                                                 │
│  ○ Skip existing (only add new)                                            │
│                                                                             │
│  Preview:                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ Config Key                    │ Current    │ Import     │ Action       ││
│  ├───────────────────────────────┼────────────┼────────────┼──────────────┤│
│  │ pms.pricing.tax_rate          │ 10%        │ 11%        │ ⚠️ Update    ││
│  │ pms.pricing.service_charge    │ 10%        │ 10%        │ ✓ Same       ││
│  │ pms.checkin.default_time      │ 14:00      │ 14:00      │ ✓ Same       ││
│  │ pms.checkout.default_time     │ -          │ 12:00      │ ➕ New       ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Summary: 1 update, 2 same, 1 new                                          │
│                                                                             │
│  [ Cancel ]                                              [ Import ]        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 43.9 Config Validation & Limits

#### 43.9.1 Validation Rules

```python
# Validation rule types in config_definitions.validation_rules

{
    # Numeric limits
    "min": 0,
    "max": 100,
    "step": 0.01,  # For decimals

    # String constraints
    "minLength": 1,
    "maxLength": 255,
    "pattern": "^[A-Z]{2,3}$",  # Regex

    # Enum values
    "enum": ["round_up", "round_down", "round_nearest"],

    # Required
    "required": true,

    # Custom validation
    "custom": "validate_time_format",  # Function name

    # Cross-config validation
    "cross_validation": [
        {
            "rule": "less_than",
            "target": "pms.checkout.default_time",
            "message": "Check-in time must be after checkout time"
        }
    ],

    # Business rules
    "business_rules": [
        {
            "rule": "sum_max",
            "configs": ["pms.pricing.tax_rate", "pms.pricing.service_charge"],
            "max": 30,
            "message": "Total tax + service cannot exceed 30%"
        }
    ]
}
```

#### 43.9.2 Validation Service

```python
class ConfigValidationService:
    """Service untuk validasi config values"""

    async def validate(
        self,
        org_id: int,
        config_key: str,
        value: Any
    ) -> ValidationResult:
        """Validate config value against all rules"""

        definition = await self._get_definition(config_key)
        rules = definition.get('validation_rules', {})
        errors = []

        # 1. Type validation
        if not self._validate_type(value, definition['config_type']):
            errors.append(f"Invalid type. Expected {definition['config_type']}")
            return ValidationResult(valid=False, errors=errors)

        # 2. Numeric limits
        if rules.get('min') is not None and value < rules['min']:
            errors.append(f"Value must be at least {rules['min']}")
        if rules.get('max') is not None and value > rules['max']:
            errors.append(f"Value must be at most {rules['max']}")

        # 3. String constraints
        if isinstance(value, str):
            if rules.get('minLength') and len(value) < rules['minLength']:
                errors.append(f"Minimum length is {rules['minLength']}")
            if rules.get('maxLength') and len(value) > rules['maxLength']:
                errors.append(f"Maximum length is {rules['maxLength']}")
            if rules.get('pattern'):
                import re
                if not re.match(rules['pattern'], value):
                    errors.append(f"Value must match pattern {rules['pattern']}")

        # 4. Enum validation
        if rules.get('enum') and value not in rules['enum']:
            errors.append(f"Value must be one of: {', '.join(rules['enum'])}")

        # 5. Cross-config validation
        for cross_rule in rules.get('cross_validation', []):
            if not await self._validate_cross_config(org_id, value, cross_rule):
                errors.append(cross_rule.get('message', 'Cross-config validation failed'))

        # 6. Business rules
        for biz_rule in rules.get('business_rules', []):
            if not await self._validate_business_rule(org_id, config_key, value, biz_rule):
                errors.append(biz_rule.get('message', 'Business rule validation failed'))

        # 7. Custom validation
        if rules.get('custom'):
            custom_result = await self._run_custom_validation(rules['custom'], value)
            if not custom_result.valid:
                errors.extend(custom_result.errors)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    async def _validate_cross_config(
        self,
        org_id: int,
        value: Any,
        rule: dict
    ) -> bool:
        """Validate against another config value"""

        target_value = await self.config.get(org_id, rule['target'])

        if rule['rule'] == 'less_than':
            return value < target_value
        elif rule['rule'] == 'greater_than':
            return value > target_value
        elif rule['rule'] == 'not_equal':
            return value != target_value

        return True

    async def _validate_business_rule(
        self,
        org_id: int,
        config_key: str,
        value: Any,
        rule: dict
    ) -> bool:
        """Validate business rules across multiple configs"""

        if rule['rule'] == 'sum_max':
            total = value
            for other_key in rule['configs']:
                if other_key != config_key:
                    other_value = await self.config.get_number(org_id, other_key)
                    total += other_value
            return total <= rule['max']

        elif rule['rule'] == 'sum_min':
            total = value
            for other_key in rule['configs']:
                if other_key != config_key:
                    other_value = await self.config.get_number(org_id, other_key)
                    total += other_value
            return total >= rule['min']

        return True
```

---

### 43.10 Reconciliation Process

#### 43.10.1 Reconciliation Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RECONCILIATION WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Request          2. Analysis        3. Approval       4. Apply          │
│  ┌─────────┐         ┌─────────┐        ┌─────────┐      ┌─────────┐       │
│  │ Admin   │         │ System  │        │ Manager │      │ System  │       │
│  │ submits │  ───►   │ analyze │  ───►  │ reviews │ ───► │ applies │       │
│  │ change  │         │ impact  │        │ & approve│     │ changes │       │
│  └─────────┘         └─────────┘        └─────────┘      └─────────┘       │
│                           │                                   │             │
│                           ▼                                   ▼             │
│                      ┌─────────┐                        ┌─────────┐        │
│                      │ Generate│                        │ Create  │        │
│                      │ report  │                        │ journal │        │
│                      │ preview │                        │ entries │        │
│                      └─────────┘                        └─────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.10.2 Reconciliation Database Schema

```sql
-- Reconciliation records
CREATE TABLE config_reconciliations (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),

    -- Config change info
    config_key VARCHAR(100) NOT NULL,
    old_value JSONB NOT NULL,
    new_value JSONB NOT NULL,

    -- Affected period
    affected_from DATE NOT NULL,
    affected_to DATE NOT NULL,

    -- Impact summary
    affected_transaction_count INTEGER NOT NULL DEFAULT 0,
    total_adjustment_amount DECIMAL(20,4) DEFAULT 0,

    -- Detailed affected items
    affected_items JSONB,  -- [{id, type, old_amount, new_amount, adjustment}]

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'applied', 'cancelled')),

    -- Request
    requested_by INTEGER NOT NULL REFERENCES users(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    request_reason TEXT,

    -- Approval
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Application
    applied_at TIMESTAMPTZ,
    applied_by INTEGER REFERENCES users(id),

    -- Accounting entries created
    journal_entry_ids INTEGER[]
);

CREATE INDEX idx_reconciliations_org ON config_reconciliations(organization_id, status);
CREATE INDEX idx_reconciliations_pending ON config_reconciliations(status, requested_at)
    WHERE status = 'pending';
```

#### 43.10.3 Reconciliation Service

```python
class ConfigReconciliationService:
    """Service untuk handle config reconciliation"""

    async def create_reconciliation(
        self,
        org_id: int,
        config_key: str,
        new_value: Any,
        affected_from: date,
        user_id: int,
        reason: str
    ) -> ConfigReconciliation:
        """Create reconciliation request for retroactive config change"""

        old_value = await self.config.get_effective(org_id, config_key, affected_from)

        # Analyze affected transactions
        affected = await self._analyze_affected_transactions(
            org_id, config_key, old_value, new_value, affected_from
        )

        # Create reconciliation record
        recon = await self.db.fetch_one("""
            INSERT INTO config_reconciliations (
                organization_id, config_key, old_value, new_value,
                affected_from, affected_to,
                affected_transaction_count, total_adjustment_amount,
                affected_items, requested_by, request_reason
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_DATE, $6, $7, $8, $9, $10)
            RETURNING *
        """, org_id, config_key, old_value, new_value, affected_from,
             affected['count'], affected['total'], affected['items'],
             user_id, reason)

        # Notify approvers
        await self._notify_reconciliation_request(recon)

        return recon

    async def _analyze_affected_transactions(
        self,
        org_id: int,
        config_key: str,
        old_value: Any,
        new_value: Any,
        from_date: date
    ) -> dict:
        """Analyze which transactions are affected and calculate adjustments"""

        # Determine which table to query based on config
        if 'pms.pricing' in config_key:
            return await self._analyze_bills(org_id, config_key, old_value, new_value, from_date)
        elif 'pos.pricing' in config_key:
            return await self._analyze_pos_orders(org_id, config_key, old_value, new_value, from_date)

        return {'count': 0, 'total': Decimal(0), 'items': []}

    async def apply_reconciliation(
        self,
        recon_id: int,
        user_id: int
    ) -> ReconciliationResult:
        """Apply approved reconciliation"""

        recon = await self._get_reconciliation(recon_id)

        if recon.status != 'approved':
            raise ReconciliationError("Reconciliation must be approved first")

        # 1. Update config with new value
        await self.config.set_with_effective_date(
            org_id=recon.organization_id,
            config_key=recon.config_key,
            value=recon.new_value,
            effective_from=recon.affected_from,
            user_id=user_id,
            reason=f"Reconciliation #{recon_id}"
        )

        # 2. Create adjustment journal entries
        journal_ids = await self._create_adjustment_entries(recon)

        # 3. Update reconciliation status
        await self.db.execute("""
            UPDATE config_reconciliations
            SET status = 'applied', applied_at = NOW(), applied_by = $1,
                journal_entry_ids = $2
            WHERE id = $3
        """, user_id, journal_ids, recon_id)

        # 4. Send notifications
        await self._notify_reconciliation_applied(recon)

        return ReconciliationResult(
            success=True,
            adjustments_created=len(journal_ids),
            total_adjustment=recon.total_adjustment_amount
        )
```

---

### 43.11 Config Governance Summary

| Topic | Implementation |
|-------|----------------|
| **Change Rules** | 5 types: free, future_only, scheduled, reconciliation_required, period_locked |
| **Dependencies** | Auto-detect formula deps, validate before change/delete |
| **Rollback** | Version history, one-click rollback, audit trail |
| **Notification** | Role-based, multi-channel, acknowledgment tracking |
| **Approval** | Multi-level workflow, configurable per category |
| **Preview** | Sample calculations, impact analysis, dependency check |
| **Cache** | Multi-level (local + Redis), pub/sub invalidation |
| **Import/Export** | YAML/JSON format, merge modes, preview before import |
| **Validation** | Type, limits, cross-config, business rules |
| **Reconciliation** | Impact analysis, approval workflow, adjustment entries |

---

### 43.12 Context-Aware Visibility Configuration

#### 43.12.1 Overview

Pattern untuk **master data terpusat** yang memiliki **visibility berbeda** per context (module, outlet, cashier, channel, dll).

**Use Cases:**
- Payment methods: FO kasir lihat semua, FB kasir lihat subset
- Menu items: Outlet A punya menu berbeda dari Outlet B
- Room types: Channel A hanya jual room type tertentu
- Reports: Role A lihat report X, Role B lihat report Y

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CONTEXT-AWARE VISIBILITY PATTERN                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                    MASTER DATA (Centralized)                       │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │     │
│  │  │ Cash     │ │ Credit   │ │ Transfer │ │ E-Wallet │             │     │
│  │  │ Payment  │ │ Card     │ │ Bank     │ │ (OVO,GoPay)│            │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│            ┌──────────────────┼──────────────────┐                         │
│            ▼                  ▼                  ▼                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │ FO CASHIER      │ │ FB CASHIER      │ │ SPA CASHIER     │               │
│  │ ● Cash       ✓  │ │ ● Cash       ✓  │ │ ● Cash       ✓  │               │
│  │ ● Credit     ✓  │ │ ● Credit     ✓  │ │ ● Credit     ✓  │               │
│  │ ● Transfer   ✓  │ │ ● Transfer   ✗  │ │ ● Transfer   ✗  │               │
│  │ ● E-Wallet   ✓  │ │ ● E-Wallet   ✓  │ │ ● E-Wallet   ✗  │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.12.2 Database Schema

```sql
-- Generic entity-context visibility table
CREATE TABLE entity_context_visibility (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Entity (what)
    entity_type VARCHAR(50) NOT NULL,  -- 'payment_method', 'menu_item', 'room_type', 'report'
    entity_id INTEGER NOT NULL,         -- Reference to master data

    -- Context (where/who)
    context_type VARCHAR(50) NOT NULL,  -- 'module', 'outlet', 'cashier', 'channel', 'role'
    context_id INTEGER NOT NULL,        -- Reference to context (module_id, outlet_id, etc)

    -- Visibility
    is_visible BOOLEAN NOT NULL DEFAULT true,

    -- Optional settings per context
    settings JSONB DEFAULT '{}',
    -- For payment: {"default": true, "min_amount": 0, "max_amount": null}
    -- For menu: {"display_order": 1, "price_override": null}
    -- For report: {"can_export": true, "max_rows": 10000}

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by INTEGER REFERENCES users(id),

    UNIQUE(organization_id, entity_type, entity_id, context_type, context_id)
);

-- Indexes for fast lookup
CREATE INDEX idx_visibility_entity
    ON entity_context_visibility(organization_id, entity_type, context_type, context_id)
    WHERE is_visible = true;

CREATE INDEX idx_visibility_context
    ON entity_context_visibility(organization_id, context_type, context_id, entity_type);

-- For specific entity types, create materialized views if needed
CREATE VIEW v_payment_method_visibility AS
SELECT
    ecv.organization_id,
    ecv.context_type,
    ecv.context_id,
    pm.id as payment_method_id,
    pm.name as payment_method_name,
    pm.payment_type,
    COALESCE(ecv.is_visible, true) as is_visible,
    ecv.settings
FROM payment_methods pm
LEFT JOIN entity_context_visibility ecv
    ON ecv.entity_type = 'payment_method'
    AND ecv.entity_id = pm.id
    AND ecv.organization_id = pm.organization_id;
```

#### 43.12.3 Visibility Service

```python
class ContextVisibilityService:
    """Service untuk manage entity visibility per context"""

    async def get_visible_entities(
        self,
        org_id: int,
        entity_type: str,
        context_type: str,
        context_id: int,
        include_settings: bool = False
    ) -> list[VisibleEntity]:
        """Get all visible entities for a specific context"""

        # Get all entities of this type
        all_entities = await self._get_all_entities(org_id, entity_type)

        # Get visibility overrides
        visibility_map = await self._get_visibility_map(
            org_id, entity_type, context_type, context_id
        )

        result = []
        for entity in all_entities:
            # Default visibility (true if no override)
            visibility = visibility_map.get(entity.id, {'is_visible': True, 'settings': {}})

            if visibility['is_visible']:
                result.append(VisibleEntity(
                    entity_id=entity.id,
                    entity_data=entity,
                    settings=visibility['settings'] if include_settings else None
                ))

        return result

    async def get_payment_methods_for_cashier(
        self,
        org_id: int,
        cashier_id: int
    ) -> list[PaymentMethod]:
        """Get payment methods available for specific cashier"""

        return await self.db.fetch_all("""
            SELECT
                pm.*,
                COALESCE(ecv.settings->>'default', 'false')::boolean as is_default,
                ecv.settings->>'min_amount' as min_amount,
                ecv.settings->>'max_amount' as max_amount
            FROM payment_methods pm
            LEFT JOIN entity_context_visibility ecv
                ON ecv.organization_id = pm.organization_id
                AND ecv.entity_type = 'payment_method'
                AND ecv.entity_id = pm.id
                AND ecv.context_type = 'cashier'
                AND ecv.context_id = $2
            WHERE pm.organization_id = $1
              AND pm.is_active = true
              AND COALESCE(ecv.is_visible, true) = true
            ORDER BY COALESCE((ecv.settings->>'display_order')::int, 999), pm.name
        """, org_id, cashier_id)

    async def get_menu_items_for_outlet(
        self,
        org_id: int,
        outlet_id: int
    ) -> list[MenuItem]:
        """Get menu items available for specific outlet"""

        return await self.db.fetch_all("""
            SELECT
                mi.*,
                COALESCE(
                    (ecv.settings->>'price_override')::decimal,
                    mi.base_price
                ) as effective_price,
                (ecv.settings->>'display_order')::int as display_order
            FROM menu_items mi
            LEFT JOIN entity_context_visibility ecv
                ON ecv.organization_id = mi.organization_id
                AND ecv.entity_type = 'menu_item'
                AND ecv.entity_id = mi.id
                AND ecv.context_type = 'outlet'
                AND ecv.context_id = $2
            WHERE mi.organization_id = $1
              AND mi.is_active = true
              AND COALESCE(ecv.is_visible, true) = true
            ORDER BY COALESCE((ecv.settings->>'display_order')::int, 999), mi.name
        """, org_id, outlet_id)

    async def set_visibility(
        self,
        org_id: int,
        entity_type: str,
        entity_id: int,
        context_type: str,
        context_id: int,
        is_visible: bool,
        settings: dict = None,
        user_id: int = None
    ) -> EntityContextVisibility:
        """Set visibility for entity in specific context"""

        return await self.db.fetch_one("""
            INSERT INTO entity_context_visibility (
                organization_id, entity_type, entity_id,
                context_type, context_id, is_visible, settings,
                created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
            ON CONFLICT (organization_id, entity_type, entity_id, context_type, context_id)
            DO UPDATE SET
                is_visible = EXCLUDED.is_visible,
                settings = COALESCE(EXCLUDED.settings, entity_context_visibility.settings),
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by
            RETURNING *
        """, org_id, entity_type, entity_id, context_type, context_id,
             is_visible, settings, user_id)

    async def bulk_set_visibility(
        self,
        org_id: int,
        entity_type: str,
        context_type: str,
        context_id: int,
        visibility_list: list[dict],  # [{entity_id, is_visible, settings}]
        user_id: int = None
    ) -> int:
        """Bulk update visibility for multiple entities"""

        updated = 0
        for item in visibility_list:
            await self.set_visibility(
                org_id=org_id,
                entity_type=entity_type,
                entity_id=item['entity_id'],
                context_type=context_type,
                context_id=context_id,
                is_visible=item['is_visible'],
                settings=item.get('settings'),
                user_id=user_id
            )
            updated += 1

        return updated
```

#### 43.12.4 Visibility Matrix UI Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Payment Method Visibility per Cashier                          [Save All]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┬────────────┬────────────┬────────────┬───────────┐ │
│  │ Payment Method     │ FO Cashier │ FB Cashier │ SPA Cashier│ Minimarket│ │
│  ├────────────────────┼────────────┼────────────┼────────────┼───────────┤ │
│  │ Cash               │    ☑ ⚙️    │    ☑ ⚙️    │    ☑ ⚙️    │    ☑ ⚙️   │ │
│  │ Credit Card (EDC)  │    ☑ ⚙️    │    ☑ ⚙️    │    ☑ ⚙️    │    ☐      │ │
│  │ Bank Transfer      │    ☑ ⚙️    │    ☐       │    ☐       │    ☐      │ │
│  │ City Ledger        │    ☑ ⚙️    │    ☑ ⚙️    │    ☐       │    ☐      │ │
│  │ OVO                │    ☑       │    ☑       │    ☑       │    ☑      │ │
│  │ GoPay              │    ☑       │    ☑       │    ☑       │    ☑      │ │
│  │ QRIS               │    ☑       │    ☑       │    ☑       │    ☑      │ │
│  │ Room Charge        │    ☑ ⚙️    │    ☑ ⚙️    │    ☑ ⚙️    │    ☐      │ │
│  │ Voucher            │    ☑       │    ☑       │    ☐       │    ☐      │ │
│  └────────────────────┴────────────┴────────────┴────────────┴───────────┘ │
│                                                                             │
│  ☑ = Enabled   ☐ = Disabled   ⚙️ = Has custom settings                     │
│                                                                             │
│  Legend:                                                                    │
│  • Click checkbox to enable/disable                                         │
│  • Click ⚙️ to edit custom settings (default, min/max amount, etc)         │
│  • Changes auto-save on toggle                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.12.5 Settings Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings: Credit Card (EDC) for FO Cashier                         [x]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☑ Set as default payment method                                           │
│                                                                             │
│  Amount Limits:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Minimum: [     0     ]   Maximum: [ ____________ ] (blank = no limit)│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Display Order: [ 2 ]                                                       │
│                                                                             │
│  Notes: _____________________________________________                       │
│         _____________________________________________                       │
│                                                                             │
│                                              [ Cancel ]  [ Save Settings ]  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.12.6 Menu Item per Outlet

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Menu Item Visibility per Outlet                                [Save All]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Filter: [All Categories ▼]  Search: [________________]                     │
│                                                                             │
│  ┌────────────────────┬──────────┬──────────┬──────────┬──────────────────┐│
│  │ Menu Item          │ Base     │ Restoran │ Pool Bar │ Room Service     ││
│  │                    │ Price    │          │          │                  ││
│  ├────────────────────┼──────────┼──────────┼──────────┼──────────────────┤│
│  │ ☕ Coffee          │          │          │          │                  ││
│  │   Espresso         │ 25,000   │ ☑        │ ☑        │ ☑ +10%          ││
│  │   Cappuccino       │ 35,000   │ ☑        │ ☑        │ ☑ +10%          ││
│  │   Latte            │ 38,000   │ ☑        │ ☑        │ ☑ +10%          ││
│  │ 🍔 Food            │          │          │          │                  ││
│  │   Nasi Goreng      │ 55,000   │ ☑        │ ☑        │ ☑ +15%          ││
│  │   Mie Goreng       │ 50,000   │ ☑        │ ☐        │ ☑ +15%          ││
│  │   Club Sandwich    │ 75,000   │ ☑        │ ☑        │ ☑ +15%          ││
│  │ 🍺 Beverage        │          │          │          │                  ││
│  │   Bintang Beer     │ 45,000   │ ☑        │ ☑        │ ☐               ││
│  │   Wine Glass       │ 120,000  │ ☑        │ ☑        │ ☐               ││
│  └────────────────────┴──────────┴──────────┴──────────┴──────────────────┘│
│                                                                             │
│  Price Override: Click cell to set custom price for outlet                 │
│  "+10%" = Room Service markup applied                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 43.12.7 Common Use Cases

| Entity Type | Context Type | Use Case |
|-------------|--------------|----------|
| `payment_method` | `cashier` | Kasir FO bisa terima semua payment, kasir FB hanya cash/card/room charge |
| `payment_method` | `module` | Module POS hanya support payment tertentu |
| `menu_item` | `outlet` | Menu berbeda per outlet (restaurant vs pool bar) |
| `menu_item` | `channel` | Menu untuk dine-in vs delivery berbeda |
| `room_type` | `channel` | Booking.com hanya jual room type tertentu |
| `room_type` | `rate_plan` | Rate plan tertentu hanya untuk room type tertentu |
| `report` | `role` | Report keuangan hanya untuk role finance |
| `report` | `department` | Report departemen hanya untuk dept terkait |
| `feature` | `module` | Feature X hanya aktif di module tertentu |
| `tax_type` | `outlet` | Tax berbeda per outlet (some outlets tax-free) |

#### 43.12.8 API Endpoints

```yaml
# Get visible entities for context
GET /api/v1/visibility/{entity_type}
Query Parameters:
  - context_type: string (required)
  - context_id: integer (required)
  - include_settings: boolean (default: false)
Response:
  - entities: array of visible entities with optional settings

# Get visibility matrix
GET /api/v1/visibility/{entity_type}/matrix
Query Parameters:
  - context_type: string (required)
Response:
  - entities: array of all entities
  - contexts: array of all contexts
  - visibility: map of {entity_id: {context_id: {is_visible, settings}}}

# Set single visibility
PUT /api/v1/visibility/{entity_type}/{entity_id}
Body:
  - context_type: string
  - context_id: integer
  - is_visible: boolean
  - settings: object (optional)

# Bulk set visibility
PUT /api/v1/visibility/{entity_type}/bulk
Body:
  - context_type: string
  - context_id: integer
  - visibility: array of {entity_id, is_visible, settings}

# Copy visibility from one context to another
POST /api/v1/visibility/{entity_type}/copy
Body:
  - source_context_type: string
  - source_context_id: integer
  - target_context_type: string
  - target_context_id: integer
```

#### 43.12.9 Integration with Config Governance

Context-Aware Visibility mengikuti prinsip yang sama dengan Config Governance:

1. **Change Rules**: Visibility changes biasanya `free` (bisa diubah kapan saja)
2. **Audit Trail**: Semua perubahan visibility di-track di `created_by`, `updated_by`
3. **Cache Invalidation**: Clear cache saat visibility berubah
4. **No Retroactive Effect**: Visibility hanya affect transaksi baru

```python
class VisibilityChangeService:
    """Service to handle visibility changes with governance"""

    async def change_visibility(
        self,
        org_id: int,
        entity_type: str,
        entity_id: int,
        context_type: str,
        context_id: int,
        is_visible: bool,
        user_id: int
    ):
        # 1. Check permission (can user modify this context?)
        await self._check_permission(user_id, context_type, context_id)

        # 2. Update visibility
        result = await self.visibility_service.set_visibility(
            org_id, entity_type, entity_id, context_type, context_id,
            is_visible, user_id=user_id
        )

        # 3. Invalidate cache
        await self._invalidate_visibility_cache(org_id, entity_type, context_type, context_id)

        # 4. Audit log
        await self.audit.log(
            org_id=org_id,
            action='visibility_changed',
            entity_type=entity_type,
            entity_id=entity_id,
            context=f"{context_type}:{context_id}",
            old_value={'is_visible': not is_visible},
            new_value={'is_visible': is_visible},
            user_id=user_id
        )

        return result
```

---

## Summary

| Standard | Topic | Decision |
|----------|-------|----------|
| #43 | Config Governance | Change rules, dependencies, rollback, notification, approval, preview, cache, import/export, validation, reconciliation, context-aware visibility |

### Section List

| Section | Topic |
|---------|-------|
| 43.1 | Config Change Rules |
| 43.2 | Config Dependencies |
| 43.3 | Config Rollback |
| 43.4 | Config Notification |
| 43.5 | Config Approval Workflow |
| 43.6 | Config Preview/Simulation |
| 43.7 | Config Cache Invalidation |
| 43.8 | Config Import/Export |
| 43.9 | Config Validation & Limits |
| 43.10 | Reconciliation Process |
| 43.11 | Config Governance Summary |
| 43.12 | Context-Aware Visibility Configuration |

---

*Last Updated: 2025-12-10 (Section 43.12 Context-Aware Visibility Added)*
