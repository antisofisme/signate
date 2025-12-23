# Architectural Design Patterns & Concepts

> **Date**: 2025-12-23
> **Status**: Draft
> **Purpose**: Fundamental design patterns for building scalable, safe SaaS applications
> **Audience**: Architects, Senior Developers, Technical Leads

---

## Philosophy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DESIGN PHILOSOPHY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Great systems are NOT about:                                          │
│  ✗ Maximum flexibility                                                 │
│  ✗ Supporting every use case                                           │
│  ✗ Clever architecture                                                 │
│                                                                         │
│  Great systems ARE about:                                              │
│  ✓ Minimal attack surface                                              │
│  ✓ Difficult to misuse                                                 │
│  ✓ Clear constraints & guardrails                                      │
│  ✓ Data integrity & auditability                                       │
│                                                                         │
│  Core Principle:                                                       │
│  > Make the right way the easy way.                                    │
│  > Make the wrong way impossible.                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Frontend Design Patterns

### Pattern #1: App Shell + Capability-Based UI

**Problem:**
Traditional app: Menu shows all features, user confusion on what's available
```
❌ Menu shows 50 features → User confused → Support tickets
❌ No visibility control → Unauthorized access risk
❌ Same UI for all users → Bad UX for basic users
```

**Solution: Build UI based on capabilities, not pages**

```typescript
// Frontend/src/shell/navbar.tsx
interface NavItem {
  module: string
  label: string
  icon: React.ReactNode
  requiredPermission: string
  path: string
}

export function AppShellNavbar() {
  const { subscribedModules, userPermissions } = useAppContext()

  // Only show modules user can access
  const visibleModules: NavItem[] = [
    {
      module: 'pms',
      label: 'Property Management',
      icon: <BuildingIcon />,
      requiredPermission: 'pms:access',
      path: '/app/pms'
    },
    {
      module: 'accounting',
      label: 'Accounting',
      icon: <CalculatorIcon />,
      requiredPermission: 'accounting:access',
      path: '/app/accounting'
    },
    // ... more modules
  ].filter(item => {
    // Check subscription
    const subscribed = subscribedModules.includes(item.module)
    // Check permission
    const permitted = hasPermission(userPermissions, item.requiredPermission)
    return subscribed && permitted
  })

  return (
    <nav>
      {visibleModules.map(item => (
        <NavLink key={item.module} to={item.path}>
          {item.icon} {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
```

**Use Cases:**
- SaaS with modular modules
- Different subscription tiers
- Role-based feature access
- Simplified UX for basic users

**Benefits:**
✓ Cleaner UX
✓ Fewer support tickets
✓ Better security (hidden = harder to discover)
✓ Natural for SaaS pricing tiers

---

### Pattern #2: Data-as-State, UI-as-Function

**Problem:**
Traditional approach: UI stores data locally
```typescript
❌ User data in multiple places (API, component state, localStorage)
❌ Sync issues → Stale data displayed
❌ Hard to debug → Where is the truth?
```

**Solution: Single source of truth, UI reflects state**

```typescript
// ✅ CORRECT: React Query as single source of truth
import { useQuery } from '@tanstack/react-query'

export function ReservationList() {
  // Single source of truth
  const { data: reservations, isLoading, error } = useQuery({
    queryKey: ['reservations', { tenantId, month }],
    queryFn: () => api.getReservations({ tenantId, month }),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000    // Cache for 10 minutes
  })

  // UI is pure function of data
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorBanner error={error} />

  return (
    <div>
      {reservations?.map(res => (
        <ReservationCard key={res.id} reservation={res} />
      ))}
    </div>
  )
}

// Create reservation and auto-update cache
export function CreateReservationForm() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (data) => api.createReservation(data),
    onSuccess: (newReservation) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['reservations'] })

      // Or optimistic update
      queryClient.setQueryData(['reservations'], (old) => [
        ...old,
        newReservation
      ])
    }
  })

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      mutation.mutate(formData)
    }}>
      {/* form fields */}
    </form>
  )
}
```

**Architecture:**
```
┌────────────────────────────────────────────┐
│         React Query Cache                   │
│  (Single Source of Truth)                   │
└────────────────┬─────────────────────────────┘
                 │
    ┌────────────┴────────────┬──────────────┐
    ▼                         ▼              ▼
┌─────────┐           ┌──────────────┐  ┌────────┐
│Component│           │ useQuery     │  │useMutation
│ 1       │           │ Auto-refetch │  │On-success
└─────────┘           └──────────────┘  └────────┘
```

**Benefits:**
✓ Single source of truth
✓ Automatic cache invalidation
✓ Built-in optimistic updates
✓ No manual sync
✓ Easier debugging

**Trade-offs:**
✗ Dependency on React Query
✗ Network-dependent

---

### Pattern #3: Optimistic UI Updates (Selective)

**Problem:**
User perceives lag on slow networks
```
❌ Toggle room status → wait 2s for response
❌ Worse on slow 3G → perception of slowness
```

**Solution: Update UI immediately, revert if fails (selectively)**

```typescript
// ✅ Optimistic update for non-critical operations
export function RoomStatusToggle({ roomId, currentStatus }) {
  const queryClient = useQueryClient()
  const [optimisticStatus, setOptimisticStatus] = useState(currentStatus)

  const mutation = useMutation({
    mutationFn: async (newStatus) => {
      // Immediately update UI (optimistic)
      setOptimisticStatus(newStatus)

      // Update cache
      queryClient.setQueryData(['room', roomId], (old) => ({
        ...old,
        status: newStatus
      }))

      // Send to server
      try {
        await api.updateRoomStatus(roomId, newStatus)
      } catch (error) {
        // Revert on error
        setOptimisticStatus(currentStatus)
        queryClient.invalidateQueries({ queryKey: ['room', roomId] })
        throw error
      }
    },
    onError: (error) => {
      // Show error toast
      showErrorMessage(`Failed to update room: ${error.message}`)
    }
  })

  return (
    <button
      onClick={() => mutation.mutate(oppositeStatus)}
      disabled={mutation.isPending}
    >
      {optimisticStatus === 'available' ? 'Mark Occupied' : 'Mark Available'}
    </button>
  )
}

// ❌ DO NOT use optimistic for critical operations
// Example: Accounting invoice approval
export function InvoiceApprovalButton({ invoiceId }) {
  const mutation = useMutation({
    mutationFn: (data) => api.approveInvoice(invoiceId, data),
    // NO optimistic update here!
    // Wait for actual response before updating UI
    onSuccess: () => {
      showSuccessMessage('Invoice approved')
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
    }
  })

  return (
    <button onClick={() => mutation.mutate({})}>
      Approve Invoice
    </button>
  )
}
```

**When to Use:**
✅ Room status, checkbox toggles, draft saves
✅ Non-financial operations
✅ Operations user can easily undo

**When NOT to Use:**
❌ Financial transactions (invoices, payments)
❌ Data deletion
❌ Schema-changing operations
❌ Anything requiring strict consistency

**Benefits:**
✓ Perceived performance
✓ Better UX on slow networks
✓ Automatic rollback on error

---

## Part 2: Backend Design Patterns

### Pattern #4: Event as First-Class Citizen

**Problem:**
Traditional approach: Function calls = tight coupling
```
❌ PMS calls Accounting to record charge
❌ Accounting calls Reporting to update stats
❌ Reporting calls Email to send summary
❌ If Email is slow → entire chain blocked
```

**Solution: Events as system contracts**

```python
# backend/services/pms/events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ReservationCreatedEvent:
    """Immutable event: reservation was created"""
    event_type: str = "reservation.created"
    event_id: str  # Unique event ID for idempotency
    timestamp: datetime
    tenant_id: str
    reservation_id: str
    guest_id: str
    check_in: datetime
    check_out: datetime
    room_id: str
    total_amount: float
    currency: str
    metadata: dict = None  # For extensibility

    def to_dict(self) -> dict:
        return {
            'event_type': self.event_type,
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'tenant_id': self.tenant_id,
            'reservation_id': self.reservation_id,
            'guest_id': self.guest_id,
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
            'room_id': self.room_id,
            'total_amount': total_amount,
            'currency': currency,
            'metadata': metadata
        }

# backend/services/pms/service.py
class ReservationService:
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus

    async def create_reservation(self, data):
        # 1. Create in database (write model)
        reservation = Reservation(**data)
        self.db.add(reservation)
        await self.db.commit()

        # 2. Publish event (fire and forget)
        event = ReservationCreatedEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            tenant_id=data['tenant_id'],
            reservation_id=reservation.id,
            # ... other fields
        )

        await self.event_bus.publish(event)

        return reservation

# backend/services/accounting/handlers.py
class AccountingEventHandlers:
    def __init__(self, db, ledger_service):
        self.db = db
        self.ledger_service = ledger_service

    async def on_reservation_created(self, event: ReservationCreatedEvent):
        """Handle reservation creation (async, eventual consistency)"""
        # Create folio/ledger entry
        ledger = Ledger(
            tenant_id=event.tenant_id,
            reservation_id=event.reservation_id,
            amount=event.total_amount,
            currency=event.currency,
            posted_date=event.timestamp,
            description=f"Reservation {event.reservation_id}"
        )
        self.db.add(ledger)
        await self.db.commit()

        # Publish follow-up event
        await self.event_bus.publish(
            FolioCreatedEvent(
                event_id=str(uuid.uuid4()),
                folio_id=ledger.id,
                reservation_id=event.reservation_id,
                # ...
            )
        )

# backend/shared/event_bus.py
class EventBus:
    def __init__(self, message_queue):
        self.queue = message_queue  # RabbitMQ, Kafka, etc.

    async def publish(self, event):
        """Publish event to message queue"""
        message = {
            'event_type': event.event_type,
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'data': event.to_dict()
        }

        # Idempotency: use event_id as dedup key
        await self.queue.publish(
            exchange='events',
            routing_key=event.event_type,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                message_id=event.event_id,  # For dedup
                delivery_mode=2  # Persistent
            )
        )

    async def subscribe(self, event_type: str, handler):
        """Subscribe to event type"""
        await self.queue.subscribe(
            queue=f'{event_type}_handlers',
            routing_key=event_type,
            callback=handler
        )
```

**Architecture:**
```
PMS Service              Accounting Service          Reporting Service
┌──────────────┐         ┌──────────────┐           ┌──────────────┐
│Create        │         │Subscribe to  │           │Subscribe to  │
│Reservation   │         │reservation.  │           │folio.created │
└──────┬───────┘         │created       │           └──────────────┘
       │                 └──────────────┘
       │ Publish
       ▼
    ┌────────────────────────────┐
    │  Event Bus (RabbitMQ/Kafka)│
    │  (event queue)             │
    └────────────────────────────┘
       │        │
       ▼        ▼
    Accounting  Reporting  (independent, parallel processing)
```

**Benefits:**
✓ Decoupled services
✓ Parallel processing
✓ Natural for distributed systems
✓ Event replay for auditing
✓ Easier scaling

**Trade-offs:**
✗ Eventual consistency (brief window of inconsistency)
✗ More complex debugging

**Idempotency:**
Always use `event_id` to prevent duplicate processing:
```python
# In event handler
existing = db.query(ProcessedEvent).filter_by(
    event_id=event.event_id
).first()

if existing:
    return  # Already processed, skip

# Process event...

# Mark as processed
db.add(ProcessedEvent(event_id=event.event_id))
db.commit()
```

---

### Pattern #5: Read Model ≠ Write Model (CQRS Pragmatic)

**Problem:**
Single model tries to do both writes and reads
```
❌ Write model optimized for transactions
❌ Read model needs denormalization
❌ Conflicting requirements
```

**Solution: Separate models for read and write**

```python
# backend/services/pms/models.py (WRITE MODEL)
class Reservation(Base):
    """Normalized for data integrity"""
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(String)  # pending, confirmed, checked_in, checked_out
    base_rate = Column(Numeric)

    # Relationships (for writes)
    guest = relationship("Guest")
    room = relationship("Room")

# backend/services/reporting/models.py (READ MODEL)
class ReservationDashboard(Base):
    """Denormalized for fast reads"""
    __tablename__ = "dashboard_reservations"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True)
    guest_name = Column(String, index=True)  # Denormalized
    guest_email = Column(String)
    room_number = Column(String, index=True)  # Denormalized
    room_type = Column(String)
    building = Column(String)  # Denormalized from room.building
    check_in = Column(DateTime, index=True)
    check_out = Column(DateTime, index=True)
    status = Column(String, index=True)
    total_revenue = Column(Numeric)
    occupancy_rate = Column(Float)

    # No relationships, all data flattened
    # Optimized for dashboard queries

# backend/services/reporting/event_handlers.py
class ReservationDashboardUpdater:
    """Listen to PMS events and update dashboard read model"""

    async def on_reservation_created(self, event):
        # Get guest and room info via API (read-only)
        guest = await pms_api.get_guest(event.guest_id)
        room = await pms_api.get_room(event.room_id)

        # Create denormalized dashboard record
        dashboard = ReservationDashboard(
            tenant_id=event.tenant_id,
            guest_name=guest['name'],
            guest_email=guest['email'],
            room_number=room['number'],
            room_type=room['type'],
            building=room['building'],
            check_in=event.check_in,
            check_out=event.check_out,
            status='pending',
            total_revenue=event.total_amount,
            occupancy_rate=0.0
        )

        self.db.add(dashboard)
        await self.db.commit()

# API usage
@router.get("/dashboard/reservations")
async def get_dashboard(
    tenant_id: str,
    start_date: date,
    end_date: date,
    db = Depends(get_db)
):
    """Fast query on denormalized read model"""
    # Simple query without joins
    reservations = await db.query(ReservationDashboard).filter(
        ReservationDashboard.tenant_id == tenant_id,
        ReservationDashboard.check_in >= start_date,
        ReservationDashboard.check_out <= end_date
    ).all()

    return {
        'total': len(reservations),
        'by_status': group_by_status(reservations),
        'by_building': group_by_building(reservations)
    }
```

**Architecture:**
```
WRITE SIDE (Normalized)    EVENT    READ SIDE (Denormalized)
┌────────────────────┐     ────►   ┌────────────────────┐
│ Reservation        │            │ ReservationDash    │
│ (normalized)       │            │ (flat, fast)       │
│                    │            │                    │
│ - reservation_id   │            │ - id               │
│ - room_id (FK)     │            │ - guest_name       │
│ - guest_id (FK)    │            │ - room_number      │
│ - status           │            │ - building         │
│ - base_rate        │            │ - occupancy_rate   │
└────────────────────┘            └────────────────────┘

Optimized for:              Optimized for:
- ACID transactions         - Fast reads
- Data consistency          - Aggregations
- No duplication            - Denormalization OK
```

**Benefits:**
✓ Fast dashboard queries
✓ Complex aggregations easy
✓ Decouple write & read requirements
✓ Easier to scale reads independently

**Trade-offs:**
✗ Slight inconsistency (eventual consistency)
✗ Double the data storage
✗ Need event handlers to keep in sync

---

### Pattern #6: Append-Only Core Data

**Problem:**
Delete sensitive data → Can't audit
Update financial data → Lost history
```
❌ Accounting ledger entry deleted → Can't track history
❌ Invoice modified → Can't see what changed
❌ Violates accounting standards
```

**Solution: Append-only for critical data**

```python
# backend/models.py (APPEND-ONLY)
class GeneralLedger(Base):
    """Financial spine - NEVER update or delete"""
    __tablename__ = "general_ledger"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, index=True)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"))

    # Posted date (immutable)
    posted_date = Column(DateTime, index=True)

    # Transaction details (immutable)
    debit = Column(Numeric(10, 2))  # NULL if credit
    credit = Column(Numeric(10, 2))  # NULL if debit
    amount = Column(Numeric(10, 2))  # Signed (debit positive, credit negative)

    # Reference (immutable)
    reference_type = Column(String)  # "invoice", "payment", "journal_entry"
    reference_id = Column(Integer)
    description = Column(String)

    # Audit trail (immutable)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))

    # NO update_at, NO modified_by, NO delete

# Prevent updates/deletes
class GeneralLedgerRepo:
    async def record(self, tenant_id, account_id, amount, reference):
        """ONLY INSERT, never update"""
        entry = GeneralLedger(
            tenant_id=tenant_id,
            account_id=account_id,
            posted_date=datetime.utcnow(),
            debit=amount if amount > 0 else None,
            credit=amount if amount < 0 else None,
            amount=amount,
            reference_type=reference['type'],
            reference_id=reference['id'],
            description=reference['description'],
            created_by_id=reference['user_id']
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def update(self, entry_id, data):
        """FORBIDDEN - never update ledger entries"""
        raise ValueError("General ledger entries are immutable")

    async def delete(self, entry_id):
        """FORBIDDEN - never delete ledger entries"""
        raise ValueError("General ledger entries are immutable")

# Database constraint
class GeneralLedgerConstraint(Base):
    """Enforce append-only at database level"""
    # Create database trigger
    __table_args__ = (
        CheckConstraint('created_at IS NOT NULL'),
    )

# Migration
migration = """
CREATE TRIGGER prevent_ledger_update
BEFORE UPDATE ON general_ledger
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ledger is append-only';
END;

CREATE TRIGGER prevent_ledger_delete
BEFORE DELETE ON general_ledger
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ledger is append-only';
END;
"""

# If correction needed: use reversal entry (not deletion)
async def reverse_entry(original_entry_id, reason):
    """Correct mistake by creating reversal entry"""
    original = await db.get(GeneralLedger, original_entry_id)

    # Create new entry that reverses original
    reversal = GeneralLedger(
        tenant_id=original.tenant_id,
        account_id=original.account_id,
        posted_date=datetime.utcnow(),
        debit=original.credit,  # Reverse: debit ↔ credit
        credit=original.debit,
        amount=-original.amount,
        reference_type='reversal',
        reference_id=original.id,
        description=f"Reversal of entry {original.id}: {reason}",
        created_by_id=current_user.id
    )

    db.add(reversal)
    await db.commit()
    return reversal
```

**Audit Trail:**
```
Entry 1: Reservation charge         Debit: 1000
Entry 2: Guest payment received     Credit: 1000
Entry 3: Reversal (wrong rate)      Credit: 100  ← Shows correction
Entry 4: Correction (right rate)    Credit: 100

Complete history visible. No deletions. Complies with auditing standards.
```

**Benefits:**
✓ Complete audit trail
✓ Legal compliance
✓ Immutable history
✓ Impossible to hide transactions
✓ Easier forensics

**Where to Use:**
- Financial ledgers ✅
- Audit logs ✅
- Payment transactions ✅
- Tax records ✅

**Where NOT to Use:**
- Operational data (guests, rooms) - use soft delete instead
- Temporary data
- Cache data

---

### Pattern #7: Semantic Layer (No Free SQL)

**Problem:**
Users write arbitrary SQL
```sql
❌ SELECT * FROM accounting.ledger WHERE amount > 10000
❌ SELECT * FROM guests WHERE passport LIKE '%xyz%'
❌ SELECT * FROM invoices LEFT JOIN guests...
❌ No access control, no audit, no type safety
```

**Solution: Semantic layer - map business concepts to data**

```python
# backend/shared/semantic_layer.py
from enum import Enum
from typing import List, Dict

class ReportingMetric(str, Enum):
    """Business concepts, not database columns"""
    TOTAL_REVENUE = "total_revenue"
    AVERAGE_RATE = "average_rate"
    OCCUPANCY_RATE = "occupancy_rate"
    GUEST_COUNT = "guest_count"
    PENDING_INVOICES = "pending_invoices"

class ReportingDimension(str, Enum):
    """Valid group-by dimensions"""
    DATE = "date"
    BUILDING = "building"
    ROOM_TYPE = "room_type"
    STATUS = "status"

# Semantic mapping
SEMANTIC_MAP = {
    ReportingMetric.TOTAL_REVENUE: {
        'source': 'accounting.general_ledger',
        'column': 'amount',
        'aggregation': 'SUM',
        'filters': {
            'account_id': 1000,  # Revenue account
            'posted_date__gte': 'period_start'
        },
        'permissions': ['accounting:read', 'reports:read']
    },
    ReportingMetric.OCCUPANCY_RATE: {
        'source': 'reporting.room_metrics',
        'column': 'occupancy_pct',
        'aggregation': 'AVG',
        'permissions': ['pms:read']
    },
    # ... more metrics
}

DIMENSION_MAP = {
    ReportingDimension.DATE: {
        'column': 'posted_date',
        'type': 'date',
        'table': 'general_ledger'
    },
    ReportingDimension.BUILDING: {
        'column': 'building',
        'type': 'string',
        'table': 'rooms'
    },
    # ... more dimensions
}

# Safe query builder
class SemanticQueryBuilder:
    def __init__(self, user_permissions: List[str]):
        self.permissions = user_permissions

    def build_report(
        self,
        metrics: List[ReportingMetric],
        dimensions: List[ReportingDimension],
        filters: Dict
    ) -> str:
        """Build SQL from semantic request"""

        # 1. Validate metrics
        for metric in metrics:
            if metric not in SEMANTIC_MAP:
                raise ValueError(f"Unknown metric: {metric}")

            # Check permissions
            required = SEMANTIC_MAP[metric]['permissions']
            if not any(p in self.permissions for p in required):
                raise PermissionError(f"Cannot access {metric}")

        # 2. Validate dimensions
        for dim in dimensions:
            if dim not in DIMENSION_MAP:
                raise ValueError(f"Unknown dimension: {dim}")

        # 3. Build safe SQL (no injection)
        sql = self._build_sql(metrics, dimensions, filters)
        return sql

    def _build_sql(self, metrics, dimensions, filters):
        """Build parameterized SQL"""
        # Implementation builds safe SQL with parameters
        # No string concatenation, always parameterized
        pass

# API endpoint
@router.post("/reports/custom")
async def create_custom_report(
    request: ReportRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create report via semantic layer"""

    # Validate request
    builder = SemanticQueryBuilder(
        user_permissions=current_user.permissions
    )

    # Build safe SQL
    try:
        sql = builder.build_report(
            metrics=request.metrics,
            dimensions=request.dimensions,
            filters=request.filters
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(400, str(e))

    # Execute
    result = await db.execute(sql)

    return {
        'metrics': request.metrics,
        'dimensions': request.dimensions,
        'data': result.fetchall()
    }
```

**Benefits:**
✓ Type-safe
✓ Permission-controlled
✓ Auditable
✓ Prevents SQL injection
✓ Clear business semantics
✓ Easy to version/change

**Trade-offs:**
✗ Requires upfront semantic mapping
✗ Less flexible than raw SQL

---

## Part 3: Cross-Cutting Patterns

### Pattern #8: Explicit Context Everywhere

**Problem:**
Implicit context = confusion
```
❌ Which tenant is this for?
❌ What's the user's timezone?
❌ What currency is this amount in?
❌ Bugs from missing context
```

**Solution: Always explicit context**

```python
# backend/models.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RequestContext:
    """EXPLICIT context for every operation"""
    tenant_id: str          # Which organization
    user_id: int            # Who is doing this
    user_role: str          # What permissions
    request_id: str         # For tracing
    timestamp: datetime     # When
    timezone: str           # User's timezone (e.g., "Asia/Jakarta")
    currency: str           # Tenant's currency (e.g., "IDR")

    @classmethod
    def from_request(cls, request: Request) -> RequestContext:
        """Extract context from HTTP request"""
        token = verify_jwt(request.headers['Authorization'])

        return RequestContext(
            tenant_id=request.headers['X-Tenant-ID'],
            user_id=token['sub'],
            user_role=token['role'],
            request_id=request.headers.get('X-Request-ID', str(uuid.uuid4())),
            timestamp=datetime.utcnow(),
            timezone=request.headers.get('X-Timezone', 'UTC'),
            currency=request.headers.get('X-Currency', 'USD')
        )

# backend/services/pms/service.py
class ReservationService:
    async def create_reservation(
        self,
        ctx: RequestContext,  # ← Always first parameter
        guest_id: int,
        room_id: int,
        check_in: datetime
    ):
        """Create reservation with explicit context"""

        # Validate tenant access
        guest = await self.db.get(Guest, guest_id)
        if guest.tenant_id != ctx.tenant_id:
            raise PermissionError("Access denied")

        # Create with context
        reservation = Reservation(
            tenant_id=ctx.tenant_id,      # ← Explicit
            guest_id=guest_id,
            room_id=room_id,
            check_in=check_in,
            created_by_id=ctx.user_id,    # ← Explicit
            created_at=ctx.timestamp      # ← Explicit
        )

        await self.db.add(reservation)
        await self.db.commit()

        return reservation

# frontend/api/client.ts
const api = new APIClient({
  baseURL: process.env.REACT_APP_API_URL
})

// Add context headers to every request
api.interceptors.request.use((config) => {
  const { tenantId } = useAppContext()
  const { timezone } = useUserPreferences()

  return {
    ...config,
    headers: {
      ...config.headers,
      'X-Tenant-ID': tenantId,
      'X-Timezone': timezone,
      'X-Request-ID': generateRequestId()
    }
  }
})
```

**Benefits:**
✓ No implicit assumptions
✓ Easy to audit
✓ Multi-tenant safety
✓ Timezone-aware
✓ Currency-aware
✓ Tracing-enabled

---

### Pattern #9: Version Everything

**Problem:**
API changes break clients
```
❌ Rename field → Legacy app breaks
❌ Change pricing model → Old subscriptions confused
❌ Update invoice template → Historical invoices wrong
```

**Solution: Version all contracts and data**

```python
# backend/api/v1/reservations.py
from fastapi import APIRouter

router_v1 = APIRouter(prefix="/api/v1")

@router_v1.get("/reservations/{id}")
async def get_reservation_v1(id: int) -> dict:
    """v1 API response"""
    res = await db.get(Reservation, id)
    return {
        'id': res.id,
        'room_id': res.room_id,  # Old schema
        'total': res.base_rate * (res.check_out - res.check_in).days
    }

# backend/api/v2/reservations.py
@router_v2.get("/reservations/{id}")
async def get_reservation_v2(id: int) -> dict:
    """v2 API response (enhanced)"""
    res = await db.get(Reservation, id)
    return {
        'id': res.id,
        'room_id': res.room_id,
        'room_type': res.room.type,  # New: room type
        'guest_name': res.guest.name,  # New: guest name
        'total': res.total_amount,  # New: pre-calculated
        'currency': res.currency  # New: explicit currency
    }

# frontend/api/client.ts
// Client requests specific version
const response = await fetch('/api/v2/reservations/123', {
  headers: {
    'Accept': 'application/vnd.app+json;version=2'
  }
})

# Pricing versioning
class PricingRule(Base):
    """Track pricing model versions"""
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String)
    pricing_version = Column(String)  # "v1", "v2", "v3"
    effective_date = Column(DateTime)
    is_active = Column(Boolean)

    # Pricing details
    base_rate = Column(Numeric)
    weekend_multiplier = Column(Numeric)
    currency = Column(String)

# Use correct version for each reservation
async def get_reservation_total(
    reservation_id: int,
    ctx: RequestContext
):
    res = await db.get(Reservation, reservation_id)

    # Get pricing rule version ACTIVE at reservation date
    pricing = await db.query(PricingRule).filter(
        PricingRule.tenant_id == ctx.tenant_id,
        PricingRule.effective_date <= res.check_in,
        PricingRule.is_active == True
    ).order_by(PricingRule.effective_date.desc()).first()

    # Calculate with historical pricing
    nights = (res.check_out - res.check_in).days
    if is_weekend(res.check_in):
        rate = pricing.base_rate * pricing.weekend_multiplier
    else:
        rate = pricing.base_rate

    return nights * rate

# Invoice template versioning
class InvoiceTemplate(Base):
    version = Column(String)  # "2024-01", "2024-02"
    effective_date = Column(DateTime)
    html_template = Column(Text)
    is_active = Column(Boolean)

# When generating invoice, use template version from that period
async def generate_invoice(invoice_id: int):
    invoice = await db.get(Invoice, invoice_id)

    # Use template active at invoice date
    template = await db.query(InvoiceTemplate).filter(
        InvoiceTemplate.effective_date <= invoice.created_at,
        InvoiceTemplate.is_active == True
    ).order_by(InvoiceTemplate.effective_date.desc()).first()

    # Render with historical template
    html = render_template(template.html_template, invoice_data)
    return html
```

**Versioning Strategy:**
```
┌─────────────────────────────────────────┐
│ API Routes                              │
├─────────────────────────────────────────┤
│ /api/v1/reservations    (old format)   │
│ /api/v2/reservations    (new format)   │
│ /api/v3/reservations    (enhanced)     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Data Models                             │
├─────────────────────────────────────────┤
│ Pricing v1 (2024-01-01 to 2024-05-31) │
│ Pricing v2 (2024-06-01 to current)    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Documents                               │
├─────────────────────────────────────────┤
│ Invoice template v2023 (historical)    │
│ Invoice template v2024 (current)       │
└─────────────────────────────────────────┘
```

**Benefits:**
✓ Backward compatibility
✓ Gradual migration
✓ Historical accuracy
✓ No breaking changes
✓ Better support

---

### Pattern #10: Feature Flags as Architecture

**Problem:**
Feature deployed → Bugs in production → Rollback takes time
```
❌ Deploy new feature
❌ Bug discovered
❌ Rollback entire service
❌ Lost 30 minutes
```

**Solution: Feature flags for instant control**

```python
# backend/shared/feature_flags.py
from enum import Enum

class FeatureFlag(str, Enum):
    """Feature flags as first-class citizens"""
    ACCOUNTING_MODULE_ENABLED = "accounting.enabled"
    NEW_CHECKOUT_FLOW = "pms.checkout_v2"
    DYNAMIC_PRICING = "pms.dynamic_pricing"
    EMAIL_NOTIFICATIONS = "notifications.email"

# Feature flag store
class FeatureFlagService:
    def __init__(self, db):
        self.db = db
        self.cache = {}

    async def is_enabled(
        self,
        flag: FeatureFlag,
        ctx: RequestContext
    ) -> bool:
        """Check if feature is enabled for this context"""

        # Check cache (with 1-minute TTL)
        cache_key = f"{flag}:{ctx.tenant_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query database
        feature = await self.db.query(FeatureFlagConfig).filter(
            FeatureFlagConfig.flag_name == flag,
            FeatureFlagConfig.tenant_id == ctx.tenant_id
        ).first()

        # Default: global setting if no tenant override
        if not feature:
            feature = await self.db.query(FeatureFlagConfig).filter(
                FeatureFlagConfig.flag_name == flag,
                FeatureFlagConfig.tenant_id.is_(None)
            ).first()

        is_enabled = feature.is_enabled if feature else False

        # Cache
        self.cache[cache_key] = is_enabled
        return is_enabled

# Usage in service
class PmsService:
    async def checkout(self, ctx: RequestContext, booking_id: int):
        # Check feature flag
        use_new_flow = await feature_flags.is_enabled(
            FeatureFlag.NEW_CHECKOUT_FLOW,
            ctx
        )

        if use_new_flow:
            return await self._checkout_v2(booking_id, ctx)
        else:
            return await self._checkout_v1(booking_id, ctx)

    async def _checkout_v1(self, booking_id, ctx):
        # Old implementation
        pass

    async def _checkout_v2(self, booking_id, ctx):
        # New implementation
        pass

# Frontend
export function CheckoutButton({ bookingId }) {
  const { featureFlags } = useAppContext()
  const useNewFlow = featureFlags['pms.checkout_v2']

  return (
    <button onClick={() => {
      if (useNewFlow) {
        navigate('/checkout-v2')
      } else {
        navigate('/checkout')
      }
    }}>
      Continue to Checkout
    </button>
  )
}

# Feature rollout strategy
class FeatureFlagConfig(Base):
    """Feature flag configuration"""
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True)
    flag_name = Column(String, index=True)
    tenant_id = Column(String, nullable=True)  # None = global
    is_enabled = Column(Boolean)
    rollout_percentage = Column(Integer, default=100)  # Canary rollout

    # Metadata
    description = Column(String)
    enabled_date = Column(DateTime)
    expected_removal_date = Column(DateTime)  # Cleanup reminder

# Canary rollout: enable for 10% of users
rollout = FeatureFlagConfig(
    flag_name=FeatureFlag.NEW_CHECKOUT_FLOW,
    is_enabled=True,
    rollout_percentage=10,  # ← Only 10% get new flow
    description="New checkout with improved UX"
)

# Hash user ID to ensure consistent bucket
def should_enable_for_user(user_id: int, rollout_pct: int) -> bool:
    hash_value = hash(f"user_{user_id}") % 100
    return hash_value < rollout_pct
```

**Deployment Flow:**
```
1. Deploy code with flag OFF
   (All users see old feature)

2. Enable flag for 10% (canary)
   (Monitor metrics)

3. If metrics good → 50%
   (Still safe)

4. If still good → 100%
   (Full rollout)

5. Monitor for 1 week → Remove old code
   (Cleanup)

All without redeploying!
```

**Benefits:**
✓ Instant rollback
✓ Canary deployments
✓ A/B testing
✓ Gradual rollout
✓ No down time

---

## Part 4: Product/UX Patterns

### Pattern #11: User Error is System Failure

**Problem:**
User forgets to check invoice total
```
❌ User approves invoice with wrong amount
❌ "User error"
❌ Support ticket
❌ Refund process
```

**Solution: Make it impossible to make the mistake**

```typescript
// ❌ BAD: Just approval button
<button onClick={approve}>Approve Invoice</button>

// ✅ GOOD: Preview before approval
export function InvoiceApprovalFlow({ invoiceId }) {
  const [step, setStep] = useState('preview')  // preview → confirm → done
  const { data: invoice } = useQuery(...)

  if (step === 'preview') {
    return (
      <div>
        <h2>Review Invoice Before Approval</h2>

        {/* Full preview */}
        <InvoicePreview invoice={invoice} />

        {/* Highlight key details */}
        <div className="approval-summary">
          <div className="summary-item">
            <label>Total Amount</label>
            <value className="large">{invoice.total}</value>
          </div>
          <div className="summary-item">
            <label>Due Date</label>
            <value>{invoice.due_date}</value>
          </div>
          <div className="summary-item">
            <label>Invoice Period</label>
            <value>{invoice.period}</value>
          </div>
        </div>

        <button onClick={() => setStep('confirm')}>
          Looks Good, Continue
        </button>
      </div>
    )
  }

  if (step === 'confirm') {
    return (
      <div>
        <h2>Confirm Approval</h2>

        {/* Force explicit confirmation */}
        <div className="confirmation-checklist">
          <label>
            <input
              type="checkbox"
              onChange={(e) => setAllowedToApprove(e.target.checked)}
            />
            I have reviewed the invoice amount of {invoice.total}
          </label>

          <label>
            <input
              type="checkbox"
              onChange={(e) => setAllowedToApprove2(e.target.checked)}
            />
            I confirm this invoice is for the correct period
          </label>
        </div>

        <button
          onClick={approve}
          disabled={!allowedToApprove || !allowedToApprove2}
        >
          Approve Invoice
        </button>
      </div>
    )
  }
}

// Backend safeguards
@router.post("/invoices/{id}/approve")
async def approve_invoice(
    id: int,
    ctx: RequestContext,
    db = Depends(get_db)
):
    invoice = await db.get(Invoice, id)

    # Validation
    if invoice.status != 'pending':
        raise HTTPException(400, "Invoice already processed")

    if invoice.tenant_id != ctx.tenant_id:
        raise PermissionError("Access denied")

    # Check amount is reasonable (anti-fraud)
    avg_amount = await calculate_average_invoice_amount(ctx.tenant_id)
    if invoice.amount > avg_amount * 2:
        # Require additional approval
        raise HTTPException(
            403,
            "Invoice amount 2x above average. Requires manager approval."
        )

    # Approval
    invoice.approved_at = datetime.utcnow()
    invoice.approved_by_id = ctx.user_id
    invoice.status = 'approved'

    await db.commit()

    return invoice
```

**Safeguards:**
1. **Preview** - See before action
2. **Explicit confirmation** - Click checkboxes
3. **Amount validation** - Flag unusual amounts
4. **Audit trail** - Who approved when
5. **Reversibility** - Can reverse if mistake

**Benefits:**
✓ Fewer support tickets
✓ Better data quality
✓ User confidence
✓ Auditable decisions

---

### Pattern #12: Observability as UX

**Problem:**
API fails → Generic error → User confused
```
❌ "An error occurred"
❌ User doesn't know what went wrong
❌ Support escalation
```

**Solution: Explain errors to user and support**

```python
# backend/models.py
@dataclass
class ApplicationError(Exception):
    """Error with user-facing explanation"""
    code: str                  # Machine-readable: "PERIOD_LOCKED"
    message: str              # For logs/engineers
    user_message: str         # For UI to display
    details: dict = None      # For debugging
    trace_id: str = None      # For support to investigate

    def to_response(self) -> dict:
        return {
            'error': {
                'code': self.code,
                'message': self.user_message,  # ← What user sees
                'trace_id': self.trace_id,     # ← For support reference
                'details': self.details if self.details else {}
            }
        }

# Service
class InvoiceApprovalService:
    async def approve_invoice(self, invoice_id: int, ctx: RequestContext):
        invoice = await db.get(Invoice, invoice_id)

        # Check if period is locked
        period = await db.get(AccountingPeriod, invoice.period_id)

        if period.is_locked:
            # Rich error for user
            raise ApplicationError(
                code="PERIOD_LOCKED",
                message="Cannot approve invoice for locked period",
                user_message=(
                    f"The accounting period ({period.name}) is locked. "
                    f"Contact your accounting manager to unlock it."
                ),
                details={
                    'period_id': period.id,
                    'period_name': period.name,
                    'locked_by': period.locked_by.name,
                    'locked_at': period.locked_at.isoformat(),
                    'unlock_procedure': 'Contact accounting@company.com'
                },
                trace_id=ctx.request_id
            )

# Frontend
const { mutate: approveInvoice } = useMutation({
  mutationFn: (id) => api.post(`/invoices/${id}/approve`),
  onError: (error) => {
    const apiError = error.response.data.error

    // Show user-friendly message
    showError({
      title: 'Cannot Approve',
      message: apiError.message,
      details: apiError.details
    })

    // Log trace ID for support
    console.log(`Error trace: ${apiError.trace_id}`)
    copyToClipboard(apiError.trace_id)
  }
})

# Observability
@app.exception_handler(ApplicationError)
async def handle_application_error(request: Request, exc: ApplicationError):
    # Log with full context
    logger.error(
        "Application error",
        extra={
            'code': exc.code,
            'message': exc.message,
            'details': exc.details,
            'trace_id': exc.trace_id,
            'path': request.url.path,
            'method': request.method
        }
    )

    return JSONResponse(
        status_code=400,
        content=exc.to_response()
    )
```

**Error Response Example:**
```json
{
  "error": {
    "code": "PERIOD_LOCKED",
    "message": "The accounting period (Jan 2024) is locked. Contact your accounting manager to unlock it.",
    "trace_id": "trace_abc123xyz",
    "details": {
      "period_id": 42,
      "period_name": "January 2024",
      "locked_by": "John Admin",
      "locked_at": "2024-01-31T23:59:59Z",
      "unlock_procedure": "Contact accounting@company.com"
    }
  }
}
```

**Benefits:**
✓ User understands what happened
✓ User knows how to fix
✓ Support can help with trace ID
✓ Fewer escalations
✓ Better product feedback

---

## Summary Table

| Pattern | Category | When to Use | Key Benefit |
|---------|----------|------------|------------|
| #1: App Shell | Frontend | SaaS with modules | Clean UX, permission control |
| #2: Data-as-State | Frontend | React apps | Single source of truth |
| #3: Optimistic UI | Frontend | Non-critical actions | Perceived performance |
| #4: Events | Backend | Multi-service system | Decoupling |
| #5: CQRS | Backend | Complex reads | Fast queries |
| #6: Append-Only | Backend | Financial/audit data | Immutable history |
| #7: Semantic Layer | Backend | Open reporting | Safety + flexibility |
| #8: Explicit Context | Cross | Every API | Multi-tenant safety |
| #9: Versioning | Cross | APIs & data | Backward compatibility |
| #10: Feature Flags | Cross | Any feature | Instant control |
| #11: Error Prevention | Product | Critical operations | Fewer mistakes |
| #12: Observability | Product | Error handling | User understanding |

---

**Related Documents:**
- ARCH-05: Frontend Architecture (implementation details)
- ARCH-02: Module Architecture (within-repo patterns)
- ARCH-06: Repository Governance (multi-repo patterns)
- SEC-01: Security & Authentication (security patterns)
- STD-02: Frontend-Backend Validation (validation patterns)
