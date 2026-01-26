-- Migration: 002
-- Description: Immutability enforcement via database triggers
-- Date: 2026-01-07
-- Phase: 1
-- Layer: 3 (Implementation)
-- Source: INFRA-LAY3-004 Section 3.1 (Trigger-Based Immutability)

-- =============================================================================
-- IMMUTABILITY TRIGGERS
-- =============================================================================
-- Purpose: Prevent UPDATE and DELETE on immutable tables at database level
-- Enforcement Layer: Database (2nd line of defense, after role permissions)
-- Audit: All failed attempts logged to operations_audit table
-- =============================================================================

BEGIN;

-- =============================================================================
-- TRIGGER FUNCTION: Prevent modification of immutable tables
-- =============================================================================

CREATE OR REPLACE FUNCTION prevent_immutable_modification()
RETURNS TRIGGER AS $$
BEGIN
  -- Log the violation attempt to operations_audit
  INSERT INTO operations_audit (
    audit_id,
    tenant_id,
    operation_type,
    resource_type,
    resource_id,
    actor_user_id,
    action_status,
    reason_if_denied,
    timestamp,
    trace_id
  )
  VALUES (
    uuid_generate_v4(),
    COALESCE(OLD.tenant_id, NEW.tenant_id),
    TG_OP || '_ATTEMPT',
    TG_TABLE_NAME::text,
    CASE
      WHEN TG_TABLE_NAME = 'decisions' THEN COALESCE(OLD.decision_id, NEW.decision_id)
      WHEN TG_TABLE_NAME = 'event_log' THEN COALESCE(OLD.event_id, NEW.event_id)
      WHEN TG_TABLE_NAME = 'workflow_transitions' THEN COALESCE(OLD.transition_id, NEW.transition_id)
      WHEN TG_TABLE_NAME = 'operations_audit' THEN COALESCE(OLD.audit_id, NEW.audit_id)
      ELSE NULL
    END,
    current_user::uuid,  -- Assumes current_user is set to UUID by application
    'DENIED',
    'Immutability violation: ' || TG_OP || ' attempted on immutable table ' || TG_TABLE_NAME,
    NOW(),
    NULLIF(current_setting('app.trace_id', true), '')::uuid
  );

  -- Raise exception to prevent the operation
  RAISE EXCEPTION 'Immutability violation: % operation not allowed on immutable table %',
    TG_OP, TG_TABLE_NAME
    USING HINT = 'This table is append-only. Use archival procedures for data removal.',
          ERRCODE = '23514';  -- check_violation

  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments
COMMENT ON FUNCTION prevent_immutable_modification() IS
  'Prevents UPDATE and DELETE operations on immutable tables. Logs all attempts to operations_audit.';

-- =============================================================================
-- TRIGGER: decisions table (Immutable)
-- =============================================================================

CREATE TRIGGER decisions_immutable_before_update_delete
BEFORE UPDATE OR DELETE ON decisions
FOR EACH ROW
EXECUTE FUNCTION prevent_immutable_modification();

COMMENT ON TRIGGER decisions_immutable_before_update_delete ON decisions IS
  'Prevents any UPDATE or DELETE on decisions table - all decisions are immutable';

-- =============================================================================
-- TRIGGER: event_log table (Immutable)
-- =============================================================================

CREATE TRIGGER event_log_immutable_before_update_delete
BEFORE UPDATE OR DELETE ON event_log
FOR EACH ROW
EXECUTE FUNCTION prevent_immutable_modification();

COMMENT ON TRIGGER event_log_immutable_before_update_delete ON event_log IS
  'Prevents any UPDATE or DELETE on event_log table - event log is immutable audit trail';

-- =============================================================================
-- TRIGGER: workflow_transitions table (Immutable)
-- =============================================================================

CREATE TRIGGER workflow_transitions_immutable_before_update_delete
BEFORE UPDATE OR DELETE ON workflow_transitions
FOR EACH ROW
EXECUTE FUNCTION prevent_immutable_modification();

COMMENT ON TRIGGER workflow_transitions_immutable_before_update_delete ON workflow_transitions IS
  'Prevents any UPDATE or DELETE on workflow_transitions table - transitions are immutable audit trail';

-- =============================================================================
-- TRIGGER: operations_audit table (Immutable)
-- =============================================================================

CREATE TRIGGER operations_audit_immutable_before_update_delete
BEFORE UPDATE OR DELETE ON operations_audit
FOR EACH ROW
EXECUTE FUNCTION prevent_immutable_modification();

COMMENT ON TRIGGER operations_audit_immutable_before_update_delete ON operations_audit IS
  'Prevents any UPDATE or DELETE on operations_audit table - audit trail itself is immutable';

-- =============================================================================
-- WORKFLOWS: Terminal State Immutability
-- =============================================================================
-- Note: workflows table is MUTABLE until terminal state (APPROVED or REJECTED)
-- After terminal state, only specific columns can be updated (archived_at, archive_location)
-- =============================================================================

CREATE OR REPLACE FUNCTION prevent_terminal_workflow_modification()
RETURNS TRIGGER AS $$
BEGIN
  -- If workflow is in terminal state, prevent modification of critical fields
  IF OLD.completed_at IS NOT NULL AND OLD.current_state IN ('APPROVED', 'REJECTED') THEN
    -- Allow archival updates only
    IF NEW.current_state != OLD.current_state OR
       NEW.decision_id != OLD.decision_id OR
       NEW.approver_role != OLD.approver_role OR
       NEW.delegated_to_user_id IS DISTINCT FROM OLD.delegated_to_user_id OR
       NEW.escalated_to_user_id IS DISTINCT FROM OLD.escalated_to_user_id OR
       NEW.escalation_timeout_at IS DISTINCT FROM OLD.escalation_timeout_at OR
       NEW.created_at != OLD.created_at OR
       NEW.completed_at != OLD.completed_at THEN

      -- Log the violation
      INSERT INTO operations_audit (
        audit_id, tenant_id, operation_type, resource_type, resource_id,
        actor_user_id, action_status, reason_if_denied, timestamp, trace_id
      )
      VALUES (
        uuid_generate_v4(),
        OLD.tenant_id,
        'UPDATE_ATTEMPT',
        'workflow',
        OLD.workflow_id,
        current_user::uuid,
        'DENIED',
        'Terminal workflow modification: workflow in state ' || OLD.current_state || ' cannot be modified',
        NOW(),
        NULLIF(current_setting('app.trace_id', true), '')::uuid
      );

      RAISE EXCEPTION 'Terminal workflow modification: workflow % in terminal state % cannot be modified',
        OLD.workflow_id, OLD.current_state
        USING HINT = 'Only archival fields can be updated after terminal state',
              ERRCODE = '23514';
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply trigger
CREATE TRIGGER workflows_terminal_state_immutable
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION prevent_terminal_workflow_modification();

COMMENT ON TRIGGER workflows_terminal_state_immutable ON workflows IS
  'Prevents modification of workflows in terminal state (APPROVED or REJECTED) except for archival fields';

-- =============================================================================
-- IDEMPOTENCY CACHE: Prevent modification after creation
-- =============================================================================

CREATE OR REPLACE FUNCTION prevent_idempotency_cache_modification()
RETURNS TRIGGER AS $$
BEGIN
  -- Log the violation
  INSERT INTO operations_audit (
    audit_id, tenant_id, operation_type, resource_type, resource_id,
    actor_user_id, action_status, reason_if_denied, timestamp, trace_id
  )
  VALUES (
    uuid_generate_v4(),
    COALESCE(OLD.tenant_id, NEW.tenant_id),
    TG_OP || '_ATTEMPT',
    'idempotency_cache',
    COALESCE(OLD.decision_id, NEW.decision_id),
    current_user::uuid,
    'DENIED',
    'Idempotency cache modification: ' || TG_OP || ' attempted on idempotency_cache',
    NOW(),
    NULLIF(current_setting('app.trace_id', true), '')::uuid
  );

  RAISE EXCEPTION 'Idempotency cache modification: % operation not allowed on idempotency_cache',
    TG_OP
    USING HINT = 'Idempotency keys are immutable once created',
          ERRCODE = '23514';

  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply trigger
CREATE TRIGGER idempotency_cache_immutable_before_update_delete
BEFORE UPDATE OR DELETE ON idempotency_cache
FOR EACH ROW
EXECUTE FUNCTION prevent_idempotency_cache_modification();

COMMENT ON TRIGGER idempotency_cache_immutable_before_update_delete ON idempotency_cache IS
  'Prevents any UPDATE or DELETE on idempotency_cache - keys are immutable once created';

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Use this query to verify all immutability triggers are active
-- Expected: 6 triggers total
-- =============================================================================

-- SELECT
--   tgname AS trigger_name,
--   tgrelid::regclass AS table_name,
--   CASE tgtype::integer & 2
--     WHEN 2 THEN 'BEFORE'
--     ELSE 'AFTER'
--   END AS trigger_timing,
--   CASE tgtype::integer & 66
--     WHEN 2 THEN 'INSERT'
--     WHEN 4 THEN 'DELETE'
--     WHEN 8 THEN 'UPDATE'
--     WHEN 12 THEN 'UPDATE OR DELETE'
--     ELSE 'UNKNOWN'
--   END AS trigger_event,
--   pg_get_functiondef(tgfoid) AS function_definition
-- FROM pg_trigger
-- WHERE tgname LIKE '%immutable%'
-- ORDER BY tgrelid::regclass::text, tgname;

-- =============================================================================
-- RECORD MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (migration_id, migration_name)
VALUES (2, '002_immutability_triggers');

COMMIT;

-- =============================================================================
-- END OF MIGRATION 002
-- =============================================================================
