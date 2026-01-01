# Development Standards V7

> Standards #28-30: State Machine, Multi-tenancy Deep Dive, Rate Limiting

---

## Table of Contents

- [Standard #28: State Machine / Workflow Engine](#standard-28-state-machine--workflow-engine)
- [Standard #29: Multi-tenancy Deep Dive](#standard-29-multi-tenancy-deep-dive)
- [Standard #30: Rate Limiting & Throttling](#standard-30-rate-limiting--throttling)

---

## Standard #28: State Machine / Workflow Engine

### 28.1 Overview

State Machine adalah pattern untuk mengelola transisi status entity yang memiliki lifecycle kompleks. Setiap entity hanya bisa berada di satu state pada satu waktu, dan transisi antar state harus melalui jalur yang valid.

### 28.2 When to Use State Machine

| Use Case | Example States | Complexity |
|----------|----------------|------------|
| Booking/Reservation | PENDING → CONFIRMED → CHECK_IN → CHECK_OUT → COMPLETED | High |
| POS Order | DRAFT → SUBMITTED → PREPARING → READY → DELIVERED → PAID | High |
| Approval Workflow | DRAFT → PENDING_APPROVAL → APPROVED/REJECTED | Medium |
| Content Publishing | DRAFT → REVIEW → PUBLISHED → ARCHIVED | Medium |
| Payment | PENDING → PROCESSING → COMPLETED/FAILED/REFUNDED | High |
| Task/Ticket | OPEN → IN_PROGRESS → RESOLVED → CLOSED | Medium |

### 28.3 State Machine Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    STATE MACHINE ANATOMY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    transition    ┌──────────┐                     │
│  │  STATE   │ ───────────────► │  STATE   │                     │
│  │   (A)    │                  │   (B)    │                     │
│  └──────────┘                  └──────────┘                     │
│       │                             │                            │
│       │                             │                            │
│  ┌────┴────┐                  ┌────┴────┐                       │
│  │ On Enter│                  │ On Enter│                       │
│  │ On Exit │                  │ On Exit │                       │
│  └─────────┘                  └─────────┘                       │
│                                                                  │
│  Components:                                                     │
│  1. States      - Possible conditions (PENDING, CONFIRMED, etc) │
│  2. Transitions - Valid paths between states                    │
│  3. Guards      - Conditions that must be met for transition    │
│  4. Actions     - Side effects on transition (notifications)    │
│  5. History     - Audit trail of all transitions                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 28.4 State Definition Pattern

#### Database Schema

```sql
-- State definition table (per entity type)
CREATE TABLE booking_states (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7),           -- Hex color for UI
    is_initial BOOLEAN DEFAULT FALSE,
    is_final BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Valid transitions
CREATE TABLE booking_transitions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    from_state VARCHAR(50) NOT NULL REFERENCES booking_states(code),
    to_state VARCHAR(50) NOT NULL REFERENCES booking_states(code),
    name VARCHAR(100) NOT NULL,         -- "Confirm", "Cancel", "Check In"
    required_permission VARCHAR(100),    -- Permission needed
    requires_reason BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(from_state, to_state)
);

-- Transition history (audit trail)
CREATE TABLE booking_state_history (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    from_state VARCHAR(50) REFERENCES booking_states(code),
    to_state VARCHAR(50) NOT NULL REFERENCES booking_states(code),
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    transitioned_by_id INTEGER REFERENCES users(id),
    transitioned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_booking_state_history_booking ON booking_state_history(booking_id);
CREATE INDEX idx_booking_state_history_time ON booking_state_history(transitioned_at);
```

### 28.5 Booking State Machine Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BOOKING STATE MACHINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         ┌──────────┐                                    │
│                         │  DRAFT   │ (initial)                          │
│                         └────┬─────┘                                    │
│                              │ submit                                    │
│                              ▼                                           │
│                         ┌──────────┐                                    │
│              ┌─────────►│ PENDING  │◄─────────┐                         │
│              │          └────┬─────┘          │                         │
│              │               │                │                         │
│         cancel               │ confirm   modify                         │
│              │               ▼                │                         │
│              │          ┌──────────┐          │                         │
│              │          │CONFIRMED │──────────┘                         │
│              │          └────┬─────┘                                    │
│              │               │ check_in                                  │
│              │               ▼                                           │
│              │          ┌──────────┐                                    │
│              │          │CHECK_IN  │                                    │
│              │          └────┬─────┘                                    │
│              │               │ check_out                                 │
│              │               ▼                                           │
│              │          ┌──────────┐                                    │
│              │          │CHECK_OUT │                                    │
│              │          └────┬─────┘                                    │
│              │               │ complete                                  │
│              │               ▼                                           │
│              │          ┌──────────┐                                    │
│              └─────────►│COMPLETED │ (final)                            │
│                         └──────────┘                                    │
│                              │                                           │
│                         ┌────┴─────┐                                    │
│                         │CANCELLED │ (final)                            │
│                         └──────────┘                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 28.6 Backend Implementation

#### State Machine Base Class (Python)

```python
# shared/state_machine/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

@dataclass
class Transition:
    """Represents a valid state transition"""
    from_state: str
    to_state: str
    name: str
    guards: List[Callable] = None      # Conditions to check
    actions: List[Callable] = None     # Side effects to run
    required_permission: str = None
    requires_reason: bool = False

@dataclass
class TransitionResult:
    """Result of a transition attempt"""
    success: bool
    from_state: str
    to_state: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

class StateMachine(ABC):
    """Base class for state machines"""

    def __init__(self):
        self.transitions: Dict[str, List[Transition]] = {}
        self._setup_transitions()

    @abstractmethod
    def _setup_transitions(self):
        """Define valid transitions - implement in subclass"""
        pass

    def add_transition(self, transition: Transition):
        """Register a valid transition"""
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)

    def get_available_transitions(self, current_state: str) -> List[Transition]:
        """Get all valid transitions from current state"""
        return self.transitions.get(current_state, [])

    def can_transition(
        self,
        entity: Any,
        to_state: str,
        user: Any = None
    ) -> tuple[bool, Optional[str]]:
        """Check if transition is valid"""
        current_state = self._get_current_state(entity)
        transitions = self.get_available_transitions(current_state)

        # Find matching transition
        transition = next(
            (t for t in transitions if t.to_state == to_state),
            None
        )

        if not transition:
            return False, f"Invalid transition from {current_state} to {to_state}"

        # Check permission
        if transition.required_permission and user:
            if not self._has_permission(user, transition.required_permission):
                return False, f"Permission denied: {transition.required_permission}"

        # Run guards
        if transition.guards:
            for guard in transition.guards:
                result, error = guard(entity, user)
                if not result:
                    return False, error

        return True, None

    async def transition(
        self,
        entity: Any,
        to_state: str,
        user: Any = None,
        reason: str = None,
        metadata: Dict = None
    ) -> TransitionResult:
        """Execute state transition"""
        current_state = self._get_current_state(entity)

        # Validate transition
        can, error = self.can_transition(entity, to_state, user)
        if not can:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=to_state,
                error=error
            )

        # Get transition definition
        transition = next(
            t for t in self.transitions[current_state]
            if t.to_state == to_state
        )

        # Check reason requirement
        if transition.requires_reason and not reason:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=to_state,
                error="Reason is required for this transition"
            )

        # Execute transition
        try:
            # Update entity state
            await self._update_state(entity, to_state)

            # Run actions (side effects)
            if transition.actions:
                for action in transition.actions:
                    await action(entity, user, metadata)

            # Record history
            await self._record_history(
                entity=entity,
                from_state=current_state,
                to_state=to_state,
                user=user,
                reason=reason,
                metadata=metadata
            )

            return TransitionResult(
                success=True,
                from_state=current_state,
                to_state=to_state,
                metadata=metadata
            )

        except Exception as e:
            return TransitionResult(
                success=False,
                from_state=current_state,
                to_state=to_state,
                error=str(e)
            )

    @abstractmethod
    def _get_current_state(self, entity: Any) -> str:
        """Get current state of entity"""
        pass

    @abstractmethod
    async def _update_state(self, entity: Any, new_state: str):
        """Update entity to new state"""
        pass

    @abstractmethod
    async def _record_history(self, **kwargs):
        """Record transition in history"""
        pass

    def _has_permission(self, user: Any, permission: str) -> bool:
        """Check if user has permission"""
        return permission in getattr(user, 'permissions', [])
```

#### Booking State Machine Implementation

```python
# services/booking/state_machine.py
from shared.state_machine.base import StateMachine, Transition
from .models import BookingModel, BookingStateHistory
from .events import BookingEvents

class BookingStateMachine(StateMachine):
    """State machine for booking lifecycle"""

    # State constants
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    def __init__(self, db_session, event_bus):
        self.db = db_session
        self.event_bus = event_bus
        super().__init__()

    def _setup_transitions(self):
        """Define all valid booking transitions"""

        # DRAFT → PENDING
        self.add_transition(Transition(
            from_state=self.DRAFT,
            to_state=self.PENDING,
            name="Submit",
            guards=[self._guard_has_guest, self._guard_has_room],
            actions=[self._action_notify_front_desk]
        ))

        # PENDING → CONFIRMED
        self.add_transition(Transition(
            from_state=self.PENDING,
            to_state=self.CONFIRMED,
            name="Confirm",
            required_permission="booking.confirm",
            guards=[self._guard_room_available, self._guard_payment_received],
            actions=[
                self._action_reserve_room,
                self._action_send_confirmation_email
            ]
        ))

        # PENDING → CANCELLED
        self.add_transition(Transition(
            from_state=self.PENDING,
            to_state=self.CANCELLED,
            name="Cancel",
            requires_reason=True,
            actions=[self._action_release_room, self._action_notify_guest]
        ))

        # CONFIRMED → CHECK_IN
        self.add_transition(Transition(
            from_state=self.CONFIRMED,
            to_state=self.CHECK_IN,
            name="Check In",
            required_permission="booking.check_in",
            guards=[self._guard_check_in_date, self._guard_room_ready],
            actions=[
                self._action_assign_room,
                self._action_create_folio,
                self._action_issue_key_card
            ]
        ))

        # CONFIRMED → NO_SHOW
        self.add_transition(Transition(
            from_state=self.CONFIRMED,
            to_state=self.NO_SHOW,
            name="Mark No Show",
            required_permission="booking.no_show",
            requires_reason=True,
            actions=[self._action_charge_no_show_fee, self._action_release_room]
        ))

        # CHECK_IN → CHECK_OUT
        self.add_transition(Transition(
            from_state=self.CHECK_IN,
            to_state=self.CHECK_OUT,
            name="Check Out",
            required_permission="booking.check_out",
            guards=[self._guard_folio_settled],
            actions=[
                self._action_close_folio,
                self._action_release_room,
                self._action_send_thank_you_email
            ]
        ))

        # CHECK_OUT → COMPLETED
        self.add_transition(Transition(
            from_state=self.CHECK_OUT,
            to_state=self.COMPLETED,
            name="Complete",
            actions=[self._action_archive_booking, self._action_update_guest_history]
        ))

    # Guards (conditions)
    def _guard_has_guest(self, booking, user) -> tuple[bool, str]:
        if not booking.guest_id:
            return False, "Booking must have a guest"
        return True, None

    def _guard_has_room(self, booking, user) -> tuple[bool, str]:
        if not booking.room_type_id:
            return False, "Booking must have a room type"
        return True, None

    def _guard_room_available(self, booking, user) -> tuple[bool, str]:
        # Check room availability logic
        available = self._check_room_availability(booking)
        if not available:
            return False, "No rooms available for selected dates"
        return True, None

    def _guard_payment_received(self, booking, user) -> tuple[bool, str]:
        if booking.payment_status != "PAID" and booking.payment_status != "DEPOSIT":
            return False, "Payment or deposit required"
        return True, None

    def _guard_check_in_date(self, booking, user) -> tuple[bool, str]:
        from datetime import date
        if booking.check_in_date > date.today():
            return False, "Cannot check in before arrival date"
        return True, None

    def _guard_room_ready(self, booking, user) -> tuple[bool, str]:
        if booking.assigned_room and booking.assigned_room.status != "CLEAN":
            return False, "Room is not ready"
        return True, None

    def _guard_folio_settled(self, booking, user) -> tuple[bool, str]:
        if booking.folio and booking.folio.balance > 0:
            return False, f"Outstanding balance: {booking.folio.balance}"
        return True, None

    # Actions (side effects)
    async def _action_notify_front_desk(self, booking, user, metadata):
        await self.event_bus.publish(BookingEvents.SUBMITTED, {
            "booking_id": booking.id,
            "guest_name": booking.guest.name
        })

    async def _action_reserve_room(self, booking, user, metadata):
        # Reserve room inventory
        pass

    async def _action_send_confirmation_email(self, booking, user, metadata):
        await self.event_bus.publish(BookingEvents.CONFIRMED, {
            "booking_id": booking.id,
            "email": booking.guest.email,
            "confirmation_number": booking.confirmation_number
        })

    async def _action_release_room(self, booking, user, metadata):
        # Release room inventory
        pass

    async def _action_notify_guest(self, booking, user, metadata):
        # Send notification to guest
        pass

    async def _action_assign_room(self, booking, user, metadata):
        # Assign specific room
        pass

    async def _action_create_folio(self, booking, user, metadata):
        # Create guest folio for charges
        pass

    async def _action_issue_key_card(self, booking, user, metadata):
        # Issue digital/physical key
        pass

    async def _action_charge_no_show_fee(self, booking, user, metadata):
        # Charge no-show fee
        pass

    async def _action_close_folio(self, booking, user, metadata):
        # Finalize folio
        pass

    async def _action_send_thank_you_email(self, booking, user, metadata):
        await self.event_bus.publish(BookingEvents.CHECKED_OUT, {
            "booking_id": booking.id,
            "email": booking.guest.email
        })

    async def _action_archive_booking(self, booking, user, metadata):
        # Move to archive/history
        pass

    async def _action_update_guest_history(self, booking, user, metadata):
        # Update guest stay history
        pass

    # Base class implementations
    def _get_current_state(self, booking) -> str:
        return booking.status

    async def _update_state(self, booking, new_state: str):
        booking.status = new_state
        self.db.add(booking)
        await self.db.commit()

    async def _record_history(self, **kwargs):
        history = BookingStateHistory(
            booking_id=kwargs['entity'].id,
            from_state=kwargs['from_state'],
            to_state=kwargs['to_state'],
            reason=kwargs.get('reason'),
            metadata=kwargs.get('metadata', {}),
            transitioned_by_id=kwargs['user'].id if kwargs.get('user') else None
        )
        self.db.add(history)
        await self.db.commit()
```

#### Use Case Integration

```python
# services/booking/use_cases/transition_booking.py
from dataclasses import dataclass
from typing import Optional, Dict
from ..state_machine import BookingStateMachine

@dataclass
class TransitionBookingRequest:
    booking_id: int
    to_state: str
    reason: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class TransitionBookingResponse:
    success: bool
    booking_id: int
    from_state: str
    to_state: str
    error: Optional[str] = None

class TransitionBookingUseCase:
    """Transition a booking to a new state"""

    def __init__(self, booking_repo, state_machine: BookingStateMachine):
        self.booking_repo = booking_repo
        self.state_machine = state_machine

    async def execute(
        self,
        request: TransitionBookingRequest,
        current_user
    ) -> TransitionBookingResponse:
        # Get booking
        booking = await self.booking_repo.get_by_id(request.booking_id)
        if not booking:
            return TransitionBookingResponse(
                success=False,
                booking_id=request.booking_id,
                from_state="",
                to_state=request.to_state,
                error="Booking not found"
            )

        # Execute transition
        result = await self.state_machine.transition(
            entity=booking,
            to_state=request.to_state,
            user=current_user,
            reason=request.reason,
            metadata=request.metadata
        )

        return TransitionBookingResponse(
            success=result.success,
            booking_id=request.booking_id,
            from_state=result.from_state,
            to_state=result.to_state,
            error=result.error
        )
```

### 28.7 Frontend Integration

#### React Hook for State Machine

```typescript
// hooks/useStateMachine.ts
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface Transition {
  name: string;
  toState: string;
  requiresReason: boolean;
  requiredPermission?: string;
}

interface UseStateMachineOptions {
  entityType: 'booking' | 'order' | 'approval';
  entityId: number;
}

export function useStateMachine({ entityType, entityId }: UseStateMachineOptions) {
  // Get available transitions
  const { data: transitions, isLoading } = useQuery({
    queryKey: [entityType, entityId, 'transitions'],
    queryFn: () => api.get(`/${entityType}s/${entityId}/transitions`),
  });

  // Execute transition
  const transitionMutation = useMutation({
    mutationFn: ({ toState, reason, metadata }: {
      toState: string;
      reason?: string;
      metadata?: Record<string, any>;
    }) => api.post(`/${entityType}s/${entityId}/transition`, {
      to_state: toState,
      reason,
      metadata,
    }),
  });

  // Check if can transition
  const canTransition = (toState: string): boolean => {
    return transitions?.some((t: Transition) => t.toState === toState) ?? false;
  };

  return {
    transitions: transitions ?? [],
    isLoading,
    canTransition,
    transition: transitionMutation.mutate,
    isTransitioning: transitionMutation.isPending,
    error: transitionMutation.error,
  };
}
```

#### State Transition UI Component

```typescript
// components/StateTransitionButtons.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { useStateMachine } from '@/hooks/useStateMachine';

interface StateTransitionButtonsProps {
  entityType: 'booking' | 'order';
  entityId: number;
  currentState: string;
  onTransition?: () => void;
}

export function StateTransitionButtons({
  entityType,
  entityId,
  currentState,
  onTransition,
}: StateTransitionButtonsProps) {
  const [reasonDialog, setReasonDialog] = useState<{
    open: boolean;
    transition: any;
  }>({ open: false, transition: null });
  const [reason, setReason] = useState('');

  const { transitions, isLoading, transition, isTransitioning } = useStateMachine({
    entityType,
    entityId,
  });

  const handleTransition = (t: any) => {
    if (t.requiresReason) {
      setReasonDialog({ open: true, transition: t });
    } else {
      executeTransition(t.toState);
    }
  };

  const executeTransition = (toState: string, transitionReason?: string) => {
    transition(
      { toState, reason: transitionReason },
      {
        onSuccess: () => {
          setReasonDialog({ open: false, transition: null });
          setReason('');
          onTransition?.();
        },
      }
    );
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <>
      <div className="flex gap-2">
        {transitions.map((t: any) => (
          <Button
            key={t.toState}
            onClick={() => handleTransition(t)}
            disabled={isTransitioning}
            variant={getVariant(t.toState)}
          >
            {t.name}
          </Button>
        ))}
      </div>

      {/* Reason Dialog */}
      <Dialog
        open={reasonDialog.open}
        onOpenChange={(open) => setReasonDialog({ ...reasonDialog, open })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reason Required</DialogTitle>
          </DialogHeader>
          <Textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter reason for this action..."
          />
          <Button
            onClick={() => executeTransition(
              reasonDialog.transition?.toState,
              reason
            )}
            disabled={!reason.trim() || isTransitioning}
          >
            Confirm
          </Button>
        </DialogContent>
      </Dialog>
    </>
  );
}

function getVariant(state: string) {
  const variants: Record<string, 'default' | 'destructive' | 'outline'> = {
    CANCELLED: 'destructive',
    CONFIRMED: 'default',
    CHECK_IN: 'default',
    CHECK_OUT: 'outline',
  };
  return variants[state] ?? 'outline';
}
```

### 28.8 State History Timeline

```typescript
// components/StateHistoryTimeline.tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface StateHistoryTimelineProps {
  entityType: 'booking' | 'order';
  entityId: number;
}

export function StateHistoryTimeline({ entityType, entityId }: StateHistoryTimelineProps) {
  const { data: history } = useQuery({
    queryKey: [entityType, entityId, 'history'],
    queryFn: () => api.get(`/${entityType}s/${entityId}/history`),
  });

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Status History</h3>
      <div className="relative pl-6 border-l-2 border-gray-200">
        {history?.map((item: any, index: number) => (
          <div key={item.id} className="relative pb-4">
            {/* Timeline dot */}
            <div className="absolute -left-[25px] w-4 h-4 rounded-full bg-blue-500" />

            {/* Content */}
            <div className="bg-gray-50 rounded p-3">
              <div className="flex justify-between">
                <span className="font-medium">
                  {item.fromState ? `${item.fromState} → ` : ''}
                  {item.toState}
                </span>
                <span className="text-gray-500 text-sm">
                  {formatDistanceToNow(new Date(item.transitionedAt), { addSuffix: true })}
                </span>
              </div>
              {item.reason && (
                <p className="text-gray-600 text-sm mt-1">
                  Reason: {item.reason}
                </p>
              )}
              <p className="text-gray-500 text-sm">
                By: {item.transitionedBy?.name ?? 'System'}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 28.9 API Endpoints

```python
# services/booking/routes.py
from fastapi import APIRouter, Depends, HTTPException
from .use_cases.transition_booking import TransitionBookingUseCase, TransitionBookingRequest

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/{booking_id}/transitions")
async def get_available_transitions(
    booking_id: int,
    current_user = Depends(get_current_user),
    state_machine: BookingStateMachine = Depends(get_state_machine)
):
    """Get available transitions for a booking"""
    booking = await booking_repo.get_by_id(booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    transitions = state_machine.get_available_transitions(booking.status)

    # Filter by user permissions
    available = []
    for t in transitions:
        if not t.required_permission or t.required_permission in current_user.permissions:
            available.append({
                "name": t.name,
                "toState": t.to_state,
                "requiresReason": t.requires_reason,
            })

    return available

@router.post("/{booking_id}/transition")
async def transition_booking(
    booking_id: int,
    request: TransitionBookingRequest,
    current_user = Depends(get_current_user),
    use_case: TransitionBookingUseCase = Depends()
):
    """Transition booking to new state"""
    request.booking_id = booking_id
    result = await use_case.execute(request, current_user)

    if not result.success:
        raise HTTPException(400, result.error)

    return result

@router.get("/{booking_id}/history")
async def get_booking_history(
    booking_id: int,
    current_user = Depends(get_current_user),
    history_repo = Depends(get_history_repo)
):
    """Get booking state transition history"""
    history = await history_repo.get_by_booking_id(booking_id)
    return history
```

### 28.10 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Single Source of Truth | State hanya diubah melalui State Machine |
| 2 | Immutable History | Jangan pernah hapus/edit history |
| 3 | Guards vs Actions | Guards = validasi, Actions = side effects |
| 4 | Async Actions | Actions harus async untuk flexibility |
| 5 | Permission-based | Setiap transition harus check permission |
| 6 | Reason Audit | Transisi destructive WAJIB ada reason |
| 7 | Event Integration | Publish events untuk setiap transition |
| 8 | Testable | Guards dan actions harus unit testable |

---

## Standard #29: Multi-tenancy Deep Dive

### 29.1 Overview

Multi-tenancy memungkinkan satu instance aplikasi melayani banyak tenant (organization) dengan data isolation yang proper. ATLAS_PANDAWA menggunakan **Row-Level Isolation** sebagai primary approach.

### 29.2 Isolation Strategies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   MULTI-TENANCY ISOLATION STRATEGIES                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. ROW-LEVEL ISOLATION (Current - Recommended)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Single Database, Single Schema                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  users table                                             │    │   │
│  │  │  ├─ id=1, org_id=1, name="John" (Hotel A)              │    │   │
│  │  │  ├─ id=2, org_id=1, name="Jane" (Hotel A)              │    │   │
│  │  │  ├─ id=3, org_id=2, name="Bob"  (Hotel B)              │    │   │
│  │  │  └─ id=4, org_id=2, name="Alice"(Hotel B)              │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  WHERE organization_id = :current_org_id                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Simple, cost-effective, easy maintenance                           │
│  ⚠️ Requires careful query filtering                                   │
│                                                                          │
│  2. SCHEMA-LEVEL ISOLATION (Future Option)                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Single Database, Multiple Schemas                               │   │
│  │  ├─ tenant_hotel_a.users                                        │   │
│  │  ├─ tenant_hotel_a.bookings                                     │   │
│  │  ├─ tenant_hotel_b.users                                        │   │
│  │  └─ tenant_hotel_b.bookings                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Better isolation, easier backup per tenant                          │
│  ⚠️ More complex migrations, connection pooling challenges             │
│                                                                          │
│  3. DATABASE-LEVEL ISOLATION (Enterprise/Compliance)                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Separate Databases                                              │   │
│  │  ├─ hotel_a_db (separate PostgreSQL instance)                   │   │
│  │  ├─ hotel_b_db (separate PostgreSQL instance)                   │   │
│  │  └─ hotel_c_db (separate PostgreSQL instance)                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Maximum isolation, compliance-ready, custom scaling                 │
│  ⚠️ Highest cost, complex management, migration overhead               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 29.3 Current Implementation (Row-Level)

#### Database Schema Pattern

```sql
-- Every tenant-specific table MUST have organization_id
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    -- ... other columns

    -- Index for tenant filtering
    CONSTRAINT fk_booking_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

-- ALWAYS create index on organization_id
CREATE INDEX idx_bookings_organization ON bookings(organization_id);

-- Row-Level Security (PostgreSQL)
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON bookings
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### Tenant Context Middleware

```python
# shared/middleware/tenant_context.py
from contextvars import ContextVar
from fastapi import Request, HTTPException
from typing import Optional

# Context variable for current tenant
current_tenant_id: ContextVar[Optional[int]] = ContextVar('current_tenant_id', default=None)
current_tenant: ContextVar[Optional[dict]] = ContextVar('current_tenant', default=None)

class TenantContextMiddleware:
    """Middleware to set tenant context from JWT token"""

    async def __call__(self, request: Request, call_next):
        # Extract tenant from JWT token
        tenant_id = self._get_tenant_from_token(request)

        if tenant_id:
            # Set context variables
            current_tenant_id.set(tenant_id)

            # Set PostgreSQL session variable (for RLS)
            await self._set_pg_tenant_context(tenant_id)

        response = await call_next(request)

        # Clear context after request
        current_tenant_id.set(None)
        current_tenant.set(None)

        return response

    def _get_tenant_from_token(self, request: Request) -> Optional[int]:
        """Extract organization_id from JWT token"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)
        return payload.get("organization_id")

    async def _set_pg_tenant_context(self, tenant_id: int):
        """Set PostgreSQL session variable for RLS"""
        from shared.database import get_db
        async with get_db() as db:
            await db.execute(
                f"SET app.current_organization_id = '{tenant_id}'"
            )

def get_current_tenant_id() -> int:
    """Get current tenant ID from context"""
    tenant_id = current_tenant_id.get()
    if not tenant_id:
        raise HTTPException(401, "Tenant context not set")
    return tenant_id
```

#### Repository Pattern with Tenant Filtering

```python
# shared/repositories/base.py
from typing import TypeVar, Generic, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.middleware.tenant_context import get_current_tenant_id

T = TypeVar('T')

class TenantAwareRepository(Generic[T]):
    """Base repository with automatic tenant filtering"""

    def __init__(self, db: AsyncSession, model: type[T]):
        self.db = db
        self.model = model

    def _apply_tenant_filter(self, query):
        """Apply tenant filter to query"""
        tenant_id = get_current_tenant_id()
        return query.where(self.model.organization_id == tenant_id)

    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID (tenant-filtered)"""
        query = select(self.model).where(self.model.id == id)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities (tenant-filtered)"""
        query = select(self.model).offset(skip).limit(limit)
        query = self._apply_tenant_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """Create entity with tenant ID"""
        # Ensure tenant ID is set
        entity.organization_id = get_current_tenant_id()
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update(self, id: int, data: dict) -> Optional[T]:
        """Update entity (tenant-filtered)"""
        entity = await self.get_by_id(id)
        if not entity:
            return None

        for key, value in data.items():
            setattr(entity, key, value)

        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete entity (tenant-filtered)"""
        entity = await self.get_by_id(id)
        if not entity:
            return False

        await self.db.delete(entity)
        await self.db.commit()
        return True
```

### 29.4 Tenant Provisioning

#### Tenant Provisioning Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TENANT PROVISIONING FLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Sign Up Request                                                      │
│     └─► Validate company info                                           │
│         └─► Create organization record                                  │
│             └─► Create admin user                                       │
│                 └─► Setup default configuration                         │
│                     └─► Create default roles/permissions                │
│                         └─► Initialize default data                     │
│                             └─► Send welcome email                      │
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │  Signup  │ → │  Create  │ → │  Setup   │ → │  Init    │            │
│  │  Form    │   │  Tenant  │   │  Config  │   │  Data    │            │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Provisioning Service

```python
# services/platform/use_cases/provision_tenant.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ProvisionTenantRequest:
    company_name: str
    company_email: str
    admin_name: str
    admin_email: str
    admin_password: str
    subscription_plan: str = "FREE"
    settings: Optional[dict] = None

@dataclass
class ProvisionTenantResponse:
    success: bool
    organization_id: Optional[int] = None
    admin_user_id: Optional[int] = None
    error: Optional[str] = None

class ProvisionTenantUseCase:
    """Provision a new tenant with all required setup"""

    def __init__(
        self,
        org_repo,
        user_repo,
        role_repo,
        settings_repo,
        email_service
    ):
        self.org_repo = org_repo
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.settings_repo = settings_repo
        self.email_service = email_service

    async def execute(self, request: ProvisionTenantRequest) -> ProvisionTenantResponse:
        try:
            # 1. Validate uniqueness
            if await self._company_exists(request.company_email):
                return ProvisionTenantResponse(
                    success=False,
                    error="Company email already registered"
                )

            # 2. Create organization
            organization = await self._create_organization(request)

            # 3. Create admin user
            admin_user = await self._create_admin_user(request, organization.id)

            # 4. Setup default roles and permissions
            await self._setup_default_roles(organization.id)

            # 5. Initialize default settings
            await self._initialize_settings(organization.id, request.settings)

            # 6. Initialize default data (lookup tables, etc)
            await self._initialize_default_data(organization.id)

            # 7. Send welcome email
            await self._send_welcome_email(request, organization)

            return ProvisionTenantResponse(
                success=True,
                organization_id=organization.id,
                admin_user_id=admin_user.id
            )

        except Exception as e:
            # Rollback on error
            await self._rollback_provisioning(organization_id)
            return ProvisionTenantResponse(
                success=False,
                error=str(e)
            )

    async def _create_organization(self, request):
        """Create organization record"""
        return await self.org_repo.create({
            "name": request.company_name,
            "email": request.company_email,
            "subscription_plan": request.subscription_plan,
            "is_active": True,
            "created_at": datetime.utcnow()
        })

    async def _create_admin_user(self, request, org_id):
        """Create admin user for organization"""
        return await self.user_repo.create({
            "organization_id": org_id,
            "name": request.admin_name,
            "email": request.admin_email,
            "password_hash": hash_password(request.admin_password),
            "role": "ADMIN",
            "is_active": True
        })

    async def _setup_default_roles(self, org_id):
        """Setup default roles and permissions"""
        default_roles = [
            {
                "organization_id": org_id,
                "name": "Admin",
                "code": "ADMIN",
                "permissions": ["*"]
            },
            {
                "organization_id": org_id,
                "name": "Manager",
                "code": "MANAGER",
                "permissions": [
                    "booking.view", "booking.create", "booking.edit",
                    "guest.view", "guest.create", "guest.edit",
                    "report.view"
                ]
            },
            {
                "organization_id": org_id,
                "name": "Staff",
                "code": "STAFF",
                "permissions": [
                    "booking.view", "guest.view"
                ]
            }
        ]

        for role in default_roles:
            await self.role_repo.create(role)

    async def _initialize_settings(self, org_id, custom_settings):
        """Initialize organization settings"""
        default_settings = {
            "timezone": "Asia/Jakarta",
            "currency": "IDR",
            "date_format": "DD/MM/YYYY",
            "language": "id",
            "check_in_time": "14:00",
            "check_out_time": "12:00",
            # ... more defaults
        }

        # Merge custom settings
        if custom_settings:
            default_settings.update(custom_settings)

        await self.settings_repo.create({
            "organization_id": org_id,
            "settings": default_settings
        })

    async def _initialize_default_data(self, org_id):
        """Initialize default lookup data"""
        # Room types
        await self._create_default_room_types(org_id)

        # Payment methods
        await self._create_default_payment_methods(org_id)

        # Rate codes
        await self._create_default_rate_codes(org_id)

        # etc...

    async def _send_welcome_email(self, request, organization):
        """Send welcome email to admin"""
        await self.email_service.send_template(
            to=request.admin_email,
            template="tenant_welcome",
            data={
                "company_name": request.company_name,
                "admin_name": request.admin_name,
                "login_url": f"https://app.example.com/login",
                "org_id": organization.id
            }
        )
```

### 29.5 Resource Quotas

#### Quota Configuration

```python
# shared/quota/config.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class TenantQuota:
    """Quota limits per subscription plan"""
    max_users: int
    max_rooms: int
    max_storage_gb: float
    max_api_calls_per_day: int
    max_devices: int
    features: list[str]

SUBSCRIPTION_QUOTAS: Dict[str, TenantQuota] = {
    "FREE": TenantQuota(
        max_users=5,
        max_rooms=10,
        max_storage_gb=1.0,
        max_api_calls_per_day=1000,
        max_devices=2,
        features=["basic_booking", "basic_reports"]
    ),
    "STARTER": TenantQuota(
        max_users=20,
        max_rooms=50,
        max_storage_gb=10.0,
        max_api_calls_per_day=10000,
        max_devices=10,
        features=["basic_booking", "basic_reports", "pos", "housekeeping"]
    ),
    "PROFESSIONAL": TenantQuota(
        max_users=100,
        max_rooms=200,
        max_storage_gb=50.0,
        max_api_calls_per_day=100000,
        max_devices=50,
        features=["*"]  # All features
    ),
    "ENTERPRISE": TenantQuota(
        max_users=-1,  # Unlimited
        max_rooms=-1,
        max_storage_gb=-1,
        max_api_calls_per_day=-1,
        max_devices=-1,
        features=["*", "dedicated_support", "custom_integration"]
    )
}
```

#### Quota Enforcement

```python
# shared/quota/enforcement.py
from fastapi import HTTPException
from .config import SUBSCRIPTION_QUOTAS, TenantQuota

class QuotaEnforcer:
    """Enforce tenant resource quotas"""

    def __init__(self, org_repo, usage_repo):
        self.org_repo = org_repo
        self.usage_repo = usage_repo

    async def check_quota(
        self,
        org_id: int,
        resource: str,
        increment: int = 1
    ) -> bool:
        """Check if quota allows the operation"""
        org = await self.org_repo.get_by_id(org_id)
        quota = SUBSCRIPTION_QUOTAS.get(org.subscription_plan)

        if not quota:
            raise HTTPException(500, "Invalid subscription plan")

        # Get limit for resource
        limit = getattr(quota, f"max_{resource}", None)
        if limit is None:
            return True  # No limit defined

        if limit == -1:
            return True  # Unlimited

        # Get current usage
        current = await self.usage_repo.get_usage(org_id, resource)

        if current + increment > limit:
            raise HTTPException(
                403,
                f"Quota exceeded for {resource}. "
                f"Current: {current}, Limit: {limit}. "
                f"Please upgrade your plan."
            )

        return True

    async def check_feature(self, org_id: int, feature: str) -> bool:
        """Check if feature is available for tenant"""
        org = await self.org_repo.get_by_id(org_id)
        quota = SUBSCRIPTION_QUOTAS.get(org.subscription_plan)

        if "*" in quota.features:
            return True

        if feature not in quota.features:
            raise HTTPException(
                403,
                f"Feature '{feature}' is not available in your plan. "
                f"Please upgrade to access this feature."
            )

        return True

# Dependency for routes
async def enforce_quota(resource: str):
    """FastAPI dependency for quota enforcement"""
    async def _enforce(
        current_user = Depends(get_current_user),
        enforcer: QuotaEnforcer = Depends()
    ):
        await enforcer.check_quota(current_user.organization_id, resource)
    return _enforce

# Usage in routes
@router.post("/users", dependencies=[Depends(enforce_quota("users"))])
async def create_user(...):
    pass
```

### 29.6 Tenant Isolation Testing

```python
# tests/test_tenant_isolation.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_tenant_cannot_access_other_tenant_data(
    client: AsyncClient,
    tenant_a_token: str,
    tenant_b_token: str,
    tenant_a_booking_id: int
):
    """Verify tenant A cannot access tenant B's data"""

    # Tenant A can access their own booking
    response = await client.get(
        f"/api/v1/bookings/{tenant_a_booking_id}",
        headers={"Authorization": f"Bearer {tenant_a_token}"}
    )
    assert response.status_code == 200

    # Tenant B cannot access Tenant A's booking
    response = await client.get(
        f"/api/v1/bookings/{tenant_a_booking_id}",
        headers={"Authorization": f"Bearer {tenant_b_token}"}
    )
    assert response.status_code == 404  # Not found (not 403!)

@pytest.mark.asyncio
async def test_tenant_data_not_leaked_in_list(
    client: AsyncClient,
    tenant_a_token: str,
    tenant_b_booking_count: int
):
    """Verify list endpoints only return tenant's own data"""

    response = await client.get(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {tenant_a_token}"}
    )
    assert response.status_code == 200

    # Should not include tenant B's bookings
    bookings = response.json()["data"]
    for booking in bookings:
        # All bookings should belong to tenant A's organization
        assert booking["organization_id"] == TENANT_A_ORG_ID

@pytest.mark.asyncio
async def test_create_assigns_correct_tenant(
    client: AsyncClient,
    tenant_a_token: str
):
    """Verify created entities are assigned to correct tenant"""

    response = await client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {tenant_a_token}"},
        json={"guest_id": 1, "room_type_id": 1, "check_in": "2025-01-01"}
    )
    assert response.status_code == 201

    booking = response.json()
    assert booking["organization_id"] == TENANT_A_ORG_ID
```

### 29.7 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Always Filter | SETIAP query harus filter by organization_id |
| 2 | Never Trust Client | Jangan ambil org_id dari request body |
| 3 | Use Context | Gunakan middleware untuk set tenant context |
| 4 | Test Isolation | Buat test khusus untuk verify isolation |
| 5 | Index org_id | Selalu index organization_id di setiap table |
| 6 | Quota Early | Check quota di awal request, bukan di akhir |
| 7 | Soft Delete | Prefer soft delete untuk data tenant |
| 8 | Audit All | Log semua aksi dengan tenant context |

---

## Standard #30: Rate Limiting & Throttling

### 30.1 Overview

Rate Limiting melindungi sistem dari abuse, DDoS, dan memastikan fair usage antar tenant. Menggunakan **Redis** untuk distributed rate limiting.

### 30.2 Rate Limiting Strategies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RATE LIMITING STRATEGIES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. FIXED WINDOW                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Window: 1 minute │ Limit: 100 requests                         │   │
│  │  [████████████████████░░░░░░░░░░] 70/100                        │   │
│  │  00:00            00:30            01:00                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Simple implementation                                               │
│  ⚠️ Burst at window boundaries                                         │
│                                                                          │
│  2. SLIDING WINDOW (Recommended)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Sliding 1 minute │ Limit: 100 requests                         │   │
│  │  ←──────── 1 minute ────────→                                   │   │
│  │  [░░░░████████████████████░░░░] 60/100                          │   │
│  │      ↑ current time                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Smoother rate limiting                                              │
│  ✅ No burst at boundaries                                              │
│                                                                          │
│  3. TOKEN BUCKET                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Bucket: 100 tokens │ Refill: 10/sec                            │   │
│  │  ┌─────────────┐                                                │   │
│  │  │ ████████░░░░│ 80 tokens remaining                            │   │
│  │  │ ████████░░░░│ ← Refills over time                            │   │
│  │  └─────────────┘                                                │   │
│  │  Each request consumes 1 token                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Allows controlled bursts                                            │
│  ✅ Smooth rate limiting                                                │
│                                                                          │
│  4. LEAKY BUCKET                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Queue requests, process at constant rate                        │   │
│  │  ┌─────────────┐                                                │   │
│  │  │ ■ ■ ■ ■ ■ ■ │ ──► Process 10/sec                             │   │
│  │  │ ■ ■ ■ ■     │                                                 │   │
│  │  └─────────────┘                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ✅ Constant output rate                                                │
│  ⚠️ Can introduce latency                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 30.3 Rate Limit Tiers

```python
# shared/rate_limit/config.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int  # Max burst before throttling

# Per Subscription Plan
RATE_LIMITS_BY_PLAN: Dict[str, RateLimitConfig] = {
    "FREE": RateLimitConfig(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=1000,
        burst_limit=10
    ),
    "STARTER": RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=3000,
        requests_per_day=10000,
        burst_limit=30
    ),
    "PROFESSIONAL": RateLimitConfig(
        requests_per_minute=500,
        requests_per_hour=15000,
        requests_per_day=100000,
        burst_limit=100
    ),
    "ENTERPRISE": RateLimitConfig(
        requests_per_minute=2000,
        requests_per_hour=60000,
        requests_per_day=-1,  # Unlimited
        burst_limit=500
    )
}

# Per Endpoint (override plan limits)
RATE_LIMITS_BY_ENDPOINT: Dict[str, RateLimitConfig] = {
    # Auth endpoints - stricter limits
    "/api/v1/auth/login": RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=30,
        requests_per_day=100,
        burst_limit=3
    ),
    "/api/v1/auth/register": RateLimitConfig(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=20,
        burst_limit=2
    ),
    "/api/v1/auth/forgot-password": RateLimitConfig(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=20,
        burst_limit=2
    ),

    # Heavy endpoints
    "/api/v1/reports/generate": RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=50,
        requests_per_day=200,
        burst_limit=2
    ),
    "/api/v1/export": RateLimitConfig(
        requests_per_minute=2,
        requests_per_hour=20,
        requests_per_day=50,
        burst_limit=1
    )
}
```

### 30.4 Redis-Based Rate Limiter

```python
# shared/rate_limit/limiter.py
import redis.asyncio as redis
from datetime import datetime
from typing import Optional, Tuple
from fastapi import HTTPException, Request
from .config import RateLimitConfig, RATE_LIMITS_BY_PLAN, RATE_LIMITS_BY_ENDPOINT

class RateLimiter:
    """Redis-based distributed rate limiter using sliding window"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        window: str = "minute"
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit using sliding window.
        Returns (allowed, info)
        """
        now = datetime.utcnow()

        if window == "minute":
            limit = config.requests_per_minute
            window_size = 60
        elif window == "hour":
            limit = config.requests_per_hour
            window_size = 3600
        else:  # day
            limit = config.requests_per_day
            window_size = 86400

        if limit == -1:  # Unlimited
            return True, {"remaining": -1, "limit": -1}

        # Sliding window key
        window_key = f"rate_limit:{key}:{window}"

        # Current timestamp as score
        timestamp = now.timestamp()
        window_start = timestamp - window_size

        # Use Redis transaction
        pipe = self.redis.pipeline()

        # Remove old entries outside window
        pipe.zremrangebyscore(window_key, 0, window_start)

        # Count current requests in window
        pipe.zcard(window_key)

        # Add current request
        pipe.zadd(window_key, {str(timestamp): timestamp})

        # Set expiry on key
        pipe.expire(window_key, window_size)

        results = await pipe.execute()
        current_count = results[1]

        # Check limit
        allowed = current_count < limit

        info = {
            "limit": limit,
            "remaining": max(0, limit - current_count - 1),
            "reset": int(timestamp + window_size),
            "window": window
        }

        if not allowed:
            # Remove the request we just added
            await self.redis.zrem(window_key, str(timestamp))

        return allowed, info

    async def check_all_windows(
        self,
        key: str,
        config: RateLimitConfig
    ) -> Tuple[bool, dict]:
        """Check rate limit across all time windows"""

        # Check minute limit first (most likely to hit)
        allowed, info = await self.check_rate_limit(key, config, "minute")
        if not allowed:
            return False, info

        # Check hour limit
        allowed, info = await self.check_rate_limit(key, config, "hour")
        if not allowed:
            return False, info

        # Check day limit
        allowed, info = await self.check_rate_limit(key, config, "day")
        return allowed, info


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, redis_client: redis.Redis, org_repo):
        self.limiter = RateLimiter(redis_client)
        self.org_repo = org_repo

    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready"]:
            return await call_next(request)

        # Get rate limit config
        config = await self._get_config(request)

        # Build rate limit key
        key = self._build_key(request)

        # Check rate limit
        allowed, info = await self.limiter.check_all_windows(key, config)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": info["limit"],
                    "window": info["window"],
                    "retry_after": info["reset"] - int(datetime.utcnow().timestamp())
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["reset"] - int(datetime.utcnow().timestamp()))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response

    async def _get_config(self, request: Request) -> RateLimitConfig:
        """Get rate limit config for request"""

        # Check endpoint-specific limits first
        endpoint_config = RATE_LIMITS_BY_ENDPOINT.get(request.url.path)
        if endpoint_config:
            return endpoint_config

        # Get tenant's subscription plan
        org_id = self._get_org_id(request)
        if org_id:
            org = await self.org_repo.get_by_id(org_id)
            if org:
                return RATE_LIMITS_BY_PLAN.get(
                    org.subscription_plan,
                    RATE_LIMITS_BY_PLAN["FREE"]
                )

        # Default to FREE tier for unauthenticated
        return RATE_LIMITS_BY_PLAN["FREE"]

    def _build_key(self, request: Request) -> str:
        """Build rate limit key"""
        # Try to get user/tenant ID from token
        org_id = self._get_org_id(request)
        user_id = self._get_user_id(request)

        if user_id:
            # Per-user limit
            return f"user:{user_id}"
        elif org_id:
            # Per-tenant limit
            return f"org:{org_id}"
        else:
            # Per-IP limit (for unauthenticated)
            client_ip = request.client.host
            return f"ip:{client_ip}"

    def _get_org_id(self, request: Request) -> Optional[int]:
        """Extract org_id from request"""
        # From JWT token or header
        pass

    def _get_user_id(self, request: Request) -> Optional[int]:
        """Extract user_id from request"""
        # From JWT token
        pass
```

### 30.5 Brute Force Protection

```python
# shared/rate_limit/brute_force.py
from typing import Optional
import redis.asyncio as redis

class BruteForceProtection:
    """Protect against brute force attacks on authentication"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

        # Configuration
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.attempt_window = 300    # 5 minutes

    async def record_failed_attempt(
        self,
        identifier: str,  # username, email, or IP
        attempt_type: str = "login"
    ) -> dict:
        """Record a failed authentication attempt"""
        key = f"brute_force:{attempt_type}:{identifier}"

        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.attempt_window)
        results = await pipe.execute()

        attempts = results[0]

        if attempts >= self.max_attempts:
            # Lock the account/IP
            await self._lockout(identifier, attempt_type)
            return {
                "locked": True,
                "attempts": attempts,
                "lockout_seconds": self.lockout_duration
            }

        return {
            "locked": False,
            "attempts": attempts,
            "remaining": self.max_attempts - attempts
        }

    async def is_locked(
        self,
        identifier: str,
        attempt_type: str = "login"
    ) -> tuple[bool, Optional[int]]:
        """Check if identifier is locked out"""
        lockout_key = f"lockout:{attempt_type}:{identifier}"
        ttl = await self.redis.ttl(lockout_key)

        if ttl > 0:
            return True, ttl
        return False, None

    async def _lockout(self, identifier: str, attempt_type: str):
        """Lock out an identifier"""
        lockout_key = f"lockout:{attempt_type}:{identifier}"
        await self.redis.setex(lockout_key, self.lockout_duration, "1")

    async def clear_attempts(self, identifier: str, attempt_type: str = "login"):
        """Clear failed attempts after successful login"""
        key = f"brute_force:{attempt_type}:{identifier}"
        await self.redis.delete(key)


# Usage in login endpoint
@router.post("/auth/login")
async def login(
    request: LoginRequest,
    brute_force: BruteForceProtection = Depends()
):
    # Check if locked out
    locked, ttl = await brute_force.is_locked(request.email)
    if locked:
        raise HTTPException(
            429,
            f"Account temporarily locked. Try again in {ttl} seconds."
        )

    # Attempt login
    user = await authenticate(request.email, request.password)

    if not user:
        # Record failed attempt
        result = await brute_force.record_failed_attempt(request.email)

        if result["locked"]:
            raise HTTPException(
                429,
                f"Too many failed attempts. Account locked for {result['lockout_seconds']} seconds."
            )

        raise HTTPException(
            401,
            f"Invalid credentials. {result['remaining']} attempts remaining."
        )

    # Clear attempts on success
    await brute_force.clear_attempts(request.email)

    return generate_token(user)
```

### 30.6 API Response Headers

```python
# Standard rate limit headers
"""
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000000
Retry-After: 45
Content-Type: application/json

{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please retry after 45 seconds.",
    "limit": 100,
    "window": "minute",
    "retry_after": 45
}
"""
```

### 30.7 Frontend Handling

```typescript
// lib/api/rateLimitHandler.ts
import { AxiosError, AxiosResponse } from 'axios';

interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
}

// Store rate limit info
const rateLimitStore = new Map<string, RateLimitInfo>();

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Extract rate limit headers
    const limit = response.headers['x-ratelimit-limit'];
    const remaining = response.headers['x-ratelimit-remaining'];
    const reset = response.headers['x-ratelimit-reset'];

    if (limit && remaining && reset) {
      rateLimitStore.set(response.config.url || '', {
        limit: parseInt(limit),
        remaining: parseInt(remaining),
        reset: parseInt(reset),
      });
    }

    return response;
  },
  async (error: AxiosError) => {
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const data = error.response.data as any;

      // Show user-friendly message
      showToast({
        type: 'error',
        title: 'Rate Limit Exceeded',
        message: `Too many requests. Please wait ${retryAfter} seconds.`,
      });

      // Optional: Auto-retry after delay
      if (retryAfter && error.config) {
        await sleep(parseInt(retryAfter) * 1000);
        return api.request(error.config);
      }
    }

    return Promise.reject(error);
  }
);

// Hook for components
export function useRateLimit(endpoint: string) {
  const info = rateLimitStore.get(endpoint);

  return {
    limit: info?.limit ?? 0,
    remaining: info?.remaining ?? 0,
    reset: info?.reset ?? 0,
    isNearLimit: (info?.remaining ?? 100) < 10,
    percentUsed: info ? ((info.limit - info.remaining) / info.limit) * 100 : 0,
  };
}
```

### 30.8 Monitoring & Alerting

```python
# shared/rate_limit/monitoring.py
from prometheus_client import Counter, Gauge, Histogram

# Metrics
rate_limit_hits = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'plan', 'window']
)

rate_limit_remaining = Gauge(
    'rate_limit_remaining',
    'Remaining requests in current window',
    ['tenant_id', 'window']
)

request_latency = Histogram(
    'request_latency_seconds',
    'Request latency',
    ['endpoint']
)

# Alert rules (Prometheus/Grafana)
"""
# Alert when rate limit hits spike
- alert: HighRateLimitHits
  expr: rate(rate_limit_hits_total[5m]) > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate limit hits detected"
    description: "Rate limit hits are above 100/5min for {{ $labels.endpoint }}"

# Alert for potential brute force
- alert: PotentialBruteForce
  expr: rate(rate_limit_hits_total{endpoint="/api/v1/auth/login"}[5m]) > 10
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Potential brute force attack"
    description: "High login rate limit hits detected"
"""
```

### 30.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Use Redis | Distributed rate limiting requires shared state |
| 2 | Sliding Window | Prefer sliding window over fixed window |
| 3 | Multiple Windows | Check minute, hour, AND day limits |
| 4 | Per-Endpoint | Stricter limits for auth/heavy endpoints |
| 5 | Return Headers | Always return X-RateLimit-* headers |
| 6 | Retry-After | Include Retry-After for 429 responses |
| 7 | Log & Monitor | Track rate limit hits for abuse detection |
| 8 | Graceful Handling | Frontend should handle 429 gracefully |
| 9 | Document Limits | Document rate limits in API docs |
| 10 | Whitelist | Allow whitelisting for internal services |

---

## Summary

| Standard | Key Points |
|----------|------------|
| #28 State Machine | Manage complex entity lifecycles dengan valid transitions, guards, dan actions |
| #29 Multi-tenancy | Row-level isolation dengan organization_id filtering, quota enforcement |
| #30 Rate Limiting | Redis-based sliding window, per-plan limits, brute force protection |

---

*Last Updated: 2025-12-09*
