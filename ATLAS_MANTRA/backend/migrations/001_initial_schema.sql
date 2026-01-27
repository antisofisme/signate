-- Migration: 001
-- Description: Initial schema for ATLAS_MANTRA Decision Matrix
-- Date: 2025-01-24
-- Per: MANTRA-LAW-001, MANTRA-SCHEMA-001

BEGIN;

-- ============================================================================
-- Enumerations per MANTRA-SCHEMA-001
-- ============================================================================

CREATE TYPE group_id AS ENUM ('INT', 'ARCH', 'CTL', 'EVO');

CREATE TYPE feature_id AS ENUM (
    'F01', 'F02', 'F03', 'F04',
    'F05', 'F06', 'F07', 'F08',
    'F09', 'F10', 'F11', 'F12',
    'F13', 'F14', 'F15', 'F16'
);

CREATE TYPE scope AS ENUM ('ORGANIZATION', 'DOMAIN', 'APPLICATION');

CREATE TYPE blast_radius AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

CREATE TYPE decision_status AS ENUM ('PROPOSED', 'ACTIVE', 'DEPRECATED');

CREATE TYPE constraint_type AS ENUM ('PROHIBITION', 'REQUIREMENT', 'LIMITATION');

-- ============================================================================
-- Decisions Table
-- Per MANTRA-L1-IMPL-DECISION-STORE-001: Immutable storage
-- ============================================================================

CREATE TABLE decisions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core fields per MANTRA-SCHEMA-001
    decision_id UUID UNIQUE NOT NULL,
    group_id group_id NOT NULL,
    feature_id feature_id NOT NULL,
    statement TEXT NOT NULL CHECK (length(statement) > 0),
    rationale TEXT NOT NULL CHECK (length(rationale) > 0),
    constraints JSONB NOT NULL DEFAULT '[]',
    invariants JSONB NOT NULL DEFAULT '[]',
    scope scope NOT NULL,
    blast_radius blast_radius NOT NULL,
    status decision_status NOT NULL DEFAULT 'PROPOSED',
    version VARCHAR(20) NOT NULL CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'),

    -- Optional fields
    created_by VARCHAR(200),
    approved_by VARCHAR(200),
    supersedes UUID REFERENCES decisions(decision_id),
    related_decisions JSONB DEFAULT '[]',

    -- Storage metadata
    stored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    stored_by VARCHAR(200) NOT NULL,
    storage_version INTEGER DEFAULT 1 NOT NULL,

    -- Immutability marker
    is_immutable BOOLEAN DEFAULT TRUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_decisions_group_id ON decisions(group_id);
CREATE INDEX idx_decisions_feature_id ON decisions(feature_id);
CREATE INDEX idx_decisions_status ON decisions(status);
CREATE INDEX idx_decisions_group_feature ON decisions(group_id, feature_id);
CREATE INDEX idx_decisions_created_at ON decisions(created_at);

-- Comments
COMMENT ON TABLE decisions IS 'Immutable decision storage per MANTRA-LAW-001';
COMMENT ON COLUMN decisions.is_immutable IS 'Immutability flag per MANTRA-LAW-001 §10';

-- ============================================================================
-- Event Log Table
-- Per MANTRA-L1-IMPL-DECISION-STORE-001: Audit trail
-- ============================================================================

CREATE TABLE decision_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    decision_id UUID NOT NULL,
    actor VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_events_decision_id ON decision_events(decision_id);
CREATE INDEX idx_events_event_type ON decision_events(event_type);
CREATE INDEX idx_events_recorded_at ON decision_events(recorded_at);

COMMENT ON TABLE decision_events IS 'Append-only audit trail for decision operations';

-- ============================================================================
-- Validation Results Table (Optional)
-- For storing validation history
-- ============================================================================

CREATE TABLE validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID,
    status VARCHAR(20) NOT NULL,
    violations JSONB DEFAULT '[]',
    skipped_rules JSONB DEFAULT '[]',
    advisory_notes JSONB DEFAULT '[]',
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    specification_version VARCHAR(100) NOT NULL
);

CREATE INDEX idx_validation_decision_id ON validation_results(decision_id);
CREATE INDEX idx_validation_status ON validation_results(status);
CREATE INDEX idx_validation_validated_at ON validation_results(validated_at);

COMMENT ON TABLE validation_results IS 'Validation history for audit purposes';

COMMIT;
