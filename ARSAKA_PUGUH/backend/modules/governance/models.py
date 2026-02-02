"""
ARSAKA_PUGUH Backend - Governance Module Models
Follows PANDAWA Clean Architecture standards (CORE-STD-01)

Control Plane models: Decision, Rule, Workflow, Event
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from shared.database import Base


class DecisionModel(Base):
    """Decision execution records - immutable by design"""

    __tablename__ = "decisions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Decision data
    decision_type = Column(String(100), nullable=False, index=True)
    context = Column(JSON, nullable=False)
    outcome = Column(String(100), nullable=False)
    metadata = Column(JSON, nullable=True)

    # Immutability (no updates allowed after creation)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RuleModel(Base):
    """Business rules configuration"""

    __tablename__ = "rules"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Rule data
    rule_type = Column(String(100), nullable=False, index=True)
    decision_type = Column(String(100), nullable=False, index=True)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    priority = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowModel(Base):
    """Workflow instances for approval processes"""

    __tablename__ = "workflows"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Workflow data
    workflow_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    current_step = Column(Integer, default=0, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EventModel(Base):
    """Event log for event-driven integration"""

    __tablename__ = "events"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Event data
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False)

    # Timestamps (immutable log)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
