/**
 * MANTRA SDK Types
 *
 * TypeScript type definitions for ARSAKA_MANTRA Decision System.
 */

// ============================================================================
// Enums
// ============================================================================

export type DomainId = 'INT' | 'ARCH' | 'CTL' | 'EVO';

export type AspectId =
  | 'A01' | 'A02' | 'A03' | 'A04'
  | 'A05' | 'A06' | 'A07' | 'A08'
  | 'A09' | 'A10' | 'A11' | 'A12'
  | 'A13' | 'A14' | 'A15' | 'A16';

export type ValidationStatus = 'VALID' | 'INVALID' | 'ADVISORY';

export type HealthStatus = 'HEALTHY' | 'GOOD' | 'WARNING' | 'POOR' | 'CRITICAL' | 'NEW';

// ============================================================================
// Decision Types
// ============================================================================

export interface AuthorshipMetadata {
  authored_by: string;
  authored_at?: string;
  organization?: string;
  role?: string;
}

export interface DecisionCreate {
  code: string;
  domain_id: DomainId;
  aspect_id: AspectId;
  statement: string;
  rationale: string;
  scope?: string[];
  tags?: string[];
  depends_on?: string[];
  conflicts_with?: string[];
  supersedes?: string;
  metadata?: Record<string, unknown>;
  authorship: AuthorshipMetadata;
}

export interface Decision {
  id: string;
  code: string;
  domain_id: DomainId;
  aspect_id: AspectId;
  statement: string;
  rationale: string;
  scope: string[];
  tags: string[];
  depends_on: string[];
  conflicts_with: string[];
  supersedes?: string;
  superseded_by?: string;
  version: number;
  status: string;
  created_at: string;
  updated_at: string;
  authorship: AuthorshipMetadata;
  metadata: Record<string, unknown>;
  approval_status: string;
  health_status?: HealthStatus;
}

// ============================================================================
// Validation Types
// ============================================================================

export interface ValidationViolation {
  rule_id: string;
  severity: 'HARD' | 'SOFT';
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

export interface ValidationResult {
  status: ValidationStatus;
  violations: ValidationViolation[];
  skipped_rules: string[];
  advisory_notes: string[];
  validated_at: string;
  schema_version: string;
}

export interface Gate1Result {
  passed: boolean;
  violations: ValidationViolation[];
  rule_count: number;
}

export interface Gate2Result {
  passed: boolean;
  suggestions: string[];
  confidence: number;
  model_used: string;
}

export interface Gate3Result {
  required: boolean;
  pending: boolean;
  approved_by?: string;
  approved_at?: string;
}

export interface FullValidationResult {
  gate1: Gate1Result;
  gate2: Gate2Result;
  gate3: Gate3Result;
  overall_status: string;
  can_proceed: boolean;
}

// ============================================================================
// Retrieval Types
// ============================================================================

export interface RetrievalMatch {
  decision_id: string;
  decision_code: string;
  statement: string;
  confidence: number;
  source: 'keyword' | 'semantic' | 'trigger';
  matched_by: string[];
}

export interface RetrievalResult {
  results: RetrievalMatch[];
  total_count: number;
  token_count: number;
  execution_time_ms: number;
  from_cache: boolean;
  triggered_by: string[];
  suggestions: string[];
}

export interface TriggerMatch {
  trigger_id: string;
  name: string;
  type: string;
  priority: number;
  matched_patterns: string[];
  decision_ids: string[];
}

export interface TriggerCheckResult {
  triggered: boolean;
  triggers: TriggerMatch[];
  decision_ids: string[];
}

export interface RetrievalParams {
  query: string;
  file_path?: string;
  file_content?: string;
  scope_path?: string;
  max_results?: number;
  token_budget?: number;
  use_cache?: boolean;
}

export interface TriggerCheckParams {
  file_path?: string;
  file_content?: string;
  scope_path?: string;
  keywords?: string[];
}

// ============================================================================
// Document Types
// ============================================================================

export interface DocumentType {
  type: string;
  name: string;
  description: string;
  phase: string;
  primary_audience: string;
}

export interface DocumentGenerateRequest {
  doc_type: string;
  title?: string;
  company_name?: string;
  domain_filter?: string;
  scope_filter?: string;
  max_decisions?: number;
  include_toc?: boolean;
  include_metadata?: boolean;
}

export interface GeneratedDocument {
  title: string;
  content: string;
  doc_type: string;
  word_count: number;
  section_count: number;
  decision_count: number;
  source_decisions: string[];
  generated_at: string;
}

// ============================================================================
// Analytics Types
// ============================================================================

export interface AnalyticsSummary {
  total_decisions_tracked: number;
  total_events: number;
  total_feedback: number;
  hot_decisions_count: number;
  stale_decisions_count: number;
  problematic_decisions_count: number;
}

export interface HealthDistribution {
  distribution: Record<string, number>;
  total: number;
}

export interface DecisionStats {
  decision_id: string;
  view_count: number;
  apply_count: number;
  positive_feedback: number;
  negative_feedback: number;
  last_accessed?: string;
  health_status: HealthStatus;
}

// ============================================================================
// Client Options
// ============================================================================

export interface MantraClientOptions {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface ListDecisionsParams {
  domain?: DomainId;
  aspect?: AspectId;
  status?: string;
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}
