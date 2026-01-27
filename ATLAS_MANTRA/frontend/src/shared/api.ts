import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// =============================================================================
// Types
// =============================================================================

export interface Constraint {
  constraint_id: string
  type: 'PROHIBITION' | 'REQUIREMENT' | 'LIMITATION'
  statement: string
}

export type RelationType = 'depends_on' | 'conflicts_with' | 'informed_by'

export interface Relation {
  target_id: string
  type: RelationType
}

export interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-F01-001-v1.0.0
  group_id: string
  feature_id: string
  statement: string
  rationale: string
  constraints: Constraint[]
  invariants: string[]
  scope: 'ORGANIZATION' | 'DOMAIN' | 'APPLICATION'
  blast_radius: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  version: string
  created_by: string
  created_at: string
  approved_by: string | null
  approved_at: string | null
  supersedes: string | null
  related_decisions: string[]  // DEPRECATED: Use relations instead
  relations: Relation[]  // Typed relations: depends_on, conflicts_with, informed_by
  tags: string[]  // Area tags: FE, BE, DB, INFRA, CICD, API, SECURITY, DEVOPS
  tech_stack: string[]  // Technologies: React, FastAPI, PostgreSQL, Docker, etc.
}

export interface DecisionCreate {
  group_id: string
  feature_id: string
  statement: string
  rationale: string
  constraints?: Constraint[]
  invariants?: string[]
  scope: string
  blast_radius: string
  version: string
  created_by: string
  supersedes?: string | null
  related_decisions?: string[]  // DEPRECATED: Use relations instead
  relations?: Relation[]  // Typed relations
  tags?: string[]
  tech_stack?: string[]
}

export interface DecisionListResponse {
  decisions: Decision[]
  total_count: number
  limit: number
  offset: number
}

export interface StoreResponse {
  result: 'STORED' | 'ALREADY_EXISTS' | 'STORE_ERROR' | 'INVALID_SUPERSEDES'
  decision_id: string | null
  stored_at: string | null
  error_message: string | null
}

export interface Violation {
  rule_id: string
  level: string
  message: string
  field: string | null
  failure_result: string
  governing_reference: string
}

export interface ProposeResponse {
  result: 'READY' | 'INVALID'
  proposal_id: string
  decision_id: string
  decision: Decision | null
  validation_status: string
  violations: Violation[]
  advisory_notes: string[]
  warnings: string[]  // Explicit warnings (e.g., invalid authorship_metadata)
  skipped_rules: string[]  // Rules skipped due to missing metadata
  proposed_at: string
}

export interface ChallengeRequest {
  challenger: string
  challenge_rationale: string
  proposed_replacement: DecisionCreate
}

export interface ChallengeResponse {
  result: 'STORED'
  challenged_decision_id: string
  new_decision_id: string
  stored_at: string
  error_message: string | null
}

export interface CompareResponse {
  result: 'COMPARABLE' | 'NOT_FOUND_A' | 'NOT_FOUND_B' | 'NOT_FOUND_BOTH' | 'ERROR'
  decision_a: Decision | null
  decision_b: Decision | null
  differences: FieldDifference[]
  is_supersedes_chain: boolean
  supersedes_direction: string | null
  common_group: boolean
  common_feature: boolean
  error_message: string | null
}

export interface FieldDifference {
  field_name: string  // Changed from 'field' to match backend
  value_a: any
  value_b: any
  change_type: 'modified' | 'added' | 'removed'
}

export interface HistoryResponse {
  result: 'COMPARABLE' | 'NOT_FOUND' | 'ERROR'
  decision_id: string
  chain: Decision[]
  total_versions: number
  error_message: string | null
}

// Typed audit metadata interfaces
export interface ProposedMetadata {
  _metadata_type: 'ProposedMetadata'
  proposal_id: string
  validation_status: string
  violations_count: number
}

export interface StoredMetadata {
  _metadata_type: 'StoredMetadata'
  storage_version: number
  supersedes: string | null
  version: string
}

export interface ChallengeMetadata {
  _metadata_type: 'ChallengeMetadata'
  challenged_decision_id: string
  challenge_rationale: string
  new_decision_id: string | null
}

export interface CompareMetadata {
  _metadata_type: 'CompareMetadata'
  compared_with: string
  differences_count: number
  is_supersedes_chain: boolean
  common_group: boolean
  common_feature: boolean
}

export interface ReadMetadata {
  _metadata_type: 'ReadMetadata'
  operation: string
  chain_length?: number
  filters?: Record<string, any>
}

export type AuditMetadata =
  | ProposedMetadata
  | StoredMetadata
  | ChallengeMetadata
  | CompareMetadata
  | ReadMetadata
  | Record<string, any>  // Fallback for unknown types

export interface AuditEntry {
  event_id: string
  event_type: 'DECISION_PROPOSED' | 'DECISION_VALIDATED' | 'DECISION_STORED' | 'DECISION_READ' | 'DECISION_COMPARED' | 'CHALLENGE_CREATED'
  actor: string
  actor_type: 'human' | 'ai'
  decision_id: string | null
  timestamp: string
  metadata: AuditMetadata
}

export interface AuditResponse {
  result: 'RETRIEVED'
  entries: AuditEntry[]
  total_count: number
  limit: number
  offset: number
  error_message: string | null
}

// =============================================================================
// API Key Types
// =============================================================================

export interface ApiKey {
  id: string
  name: string
  description: string | null
  key_prefix: string
  permissions: string[]
  is_active: boolean
  created_at: string
  expires_at: string | null
  last_used_at: string | null
  revoked_at: string | null
  created_by: string
}

export interface ApiKeyCreateRequest {
  name: string
  description?: string
  permissions?: string[]
  expires_at?: string | null
}

export interface ApiKeyCreatedResponse extends ApiKey {
  full_key: string  // Only shown once!
  warning: string
}

export interface ApiKeyListResponse {
  keys: ApiKey[]
  total_count: number
}

// =============================================================================
// API Functions
// =============================================================================

export const decisionsApi = {
  // List all decisions
  list: async (params?: { limit?: number; offset?: number; group_id?: string; feature_id?: string }) => {
    const response = await api.get<DecisionListResponse>('/api/v1/decisions', { params })
    return response.data
  },

  // Get single decision
  get: async (decisionId: string) => {
    const response = await api.get<Decision>(`/api/v1/decisions/${decisionId}`)
    return response.data
  },

  // Store a new decision
  // decision_id: Optional ID from propose, preserves ID continuity
  store: async (decision: DecisionCreate, storedBy: string, decisionId?: string) => {
    const response = await api.post<StoreResponse>('/api/v1/decisions', {
      decision,
      stored_by: storedBy,
      decision_id: decisionId,
    })
    return response.data
  },

  // Propose a decision (validate without storing)
  propose: async (decision: DecisionCreate, proposedBy: string) => {
    const response = await api.post<ProposeResponse>('/api/v1/decisions/propose', {
      decision,
      proposed_by: proposedBy,
    })
    return response.data
  },

  // Challenge a decision (create superseding decision)
  challenge: async (decisionId: string, request: ChallengeRequest) => {
    const response = await api.post<ChallengeResponse>(
      `/api/v1/decisions/${decisionId}/challenge`,
      request
    )
    return response.data
  },

  // Compare two decisions
  compare: async (decisionIdA: string, decisionIdB: string, actor: string) => {
    const response = await api.get<CompareResponse>(
      `/api/v1/decisions/${decisionIdA}/compare/${decisionIdB}`,
      { params: { actor } }
    )
    return response.data
  },

  // Get decision history (supersedes chain)
  history: async (decisionId: string, actor: string) => {
    const response = await api.get<HistoryResponse>(
      `/api/v1/decisions/${decisionId}/history`,
      { params: { actor } }
    )
    return response.data
  },
}

export const auditApi = {
  // List audit entries
  list: async (params?: { limit?: number; offset?: number; event_type?: string; actor?: string }) => {
    const response = await api.get<AuditResponse>('/api/v1/audit', { params })
    return response.data
  },
}

export const apiKeysApi = {
  // List all API keys
  list: async (params?: { limit?: number; offset?: number }) => {
    const response = await api.get<ApiKeyListResponse>('/api/v1/api-keys', { params })
    return response.data
  },

  // Create a new API key
  create: async (request: ApiKeyCreateRequest, createdBy: string) => {
    const response = await api.post<ApiKeyCreatedResponse>('/api/v1/api-keys', request, {
      params: { created_by: createdBy }
    })
    return response.data
  },

  // Get single API key
  get: async (keyId: string) => {
    const response = await api.get<ApiKey>(`/api/v1/api-keys/${keyId}`)
    return response.data
  },

  // Update API key
  update: async (keyId: string, request: { name?: string; description?: string }) => {
    const response = await api.put<ApiKey>(`/api/v1/api-keys/${keyId}`, request)
    return response.data
  },

  // Revoke API key
  revoke: async (keyId: string) => {
    const response = await api.post<ApiKey>(`/api/v1/api-keys/${keyId}/revoke`)
    return response.data
  },

  // Delete API key
  delete: async (keyId: string) => {
    await api.delete(`/api/v1/api-keys/${keyId}`)
  },
}

// =============================================================================
// Enhanced Validation Types
// =============================================================================

export type ArbitrationMode = 'SERVER' | 'DELEGATED' | 'SKIP'
export type ArbitrationType = 'QUALITY' | 'DUPLICATE' | 'CONFLICT'
export type ArbiterVerdict = 'APPROVE' | 'REJECT' | 'NEEDS_IMPROVEMENT' | 'DUPLICATE' | 'EVOLUTION' | 'DIFFERENT' | 'BLOCKING' | 'WARNING' | 'NOT_CONFLICT'

export interface QualityDimension {
  dimension: string
  max_points: number
  scored_points: number
  details: { rule_id: string; points: number; max_points: number; reason: string }[]
}

export interface QualityResult {
  overall_score: number
  max_score: number
  percentage: number
  is_passing: boolean
  dimensions: QualityDimension[]
  suggestions: string[]
}

export interface DuplicateMatch {
  decision_id: string
  decision_code: string
  similarity: number
  group_id: string
  feature_id: string
  statement_preview: string
}

export interface SupersedesGuidance {
  detected_duplicate_id: string
  detected_duplicate_code: string
  similarity: number
  recommendation: 'SUPERSEDES' | 'RELATION'
  message: string
  auto_populate: Record<string, any>
}

export interface DuplicateResult {
  has_exact_duplicate: boolean
  exact_duplicate_id: string | null
  near_duplicates: DuplicateMatch[]
  max_similarity: number
  supersedes_guidance: SupersedesGuidance | null
}

export interface ConflictItem {
  decision_id: string
  decision_code: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  conflict_type: string
  description: string
}

export interface ConflictResult {
  has_blocking_conflicts: boolean
  conflicts: ConflictItem[]
  blocking_conflicts: ConflictItem[]
  advisory_conflicts: ConflictItem[]
}

export interface AffectedDecision {
  decision_id: string
  decision_code: string
  impact_type: string
  description: string
}

export interface BreakingChange {
  type: string
  description: string
  dependent_decisions: string[]
}

export interface ImpactResult {
  declared_risk_score: number
  calculated_risk_score: number
  combined_risk_score: number
  risk_level: 'MINIMAL' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
  risk_mismatch: boolean
  risk_mismatch_warning: string | null
  affected_decisions: AffectedDecision[]
  breaking_changes: BreakingChange[]
}

export interface MetadataSuggestion {
  suggested_tags: string[]
  suggested_tech_stack: string[]
  suggested_blast_radius: string
  confidence: { tags: number; tech_stack: number; blast_radius: number }
}

export interface ArbitrationContext {
  arbitration_type: ArbitrationType
  prompt_template: string
  context_data: Record<string, any>
  expected_verdicts: string[]
  instructions: string
}

export interface ArbitrationVerdictInput {
  arbitration_type: ArbitrationType
  verdict: ArbiterVerdict
  confidence: number
  reason: string
}

export interface AIVerdictResult {
  verdict: ArbiterVerdict
  confidence: number
  reason: string
  source: 'SERVER_AI' | 'DELEGATED'
  provider?: string
}

export interface ApprovalSummary {
  requires_user_approval: boolean
  blocking_reasons: string[]
  warnings: string[]
  quality_concerns: string[]
  duplicate_concerns: string[]
  conflict_concerns: string[]
  impact_concerns: string[]
  recommendation: 'APPROVE' | 'REJECT' | 'REVIEW'
  summary_text: string
}

export interface EnhancedValidationResponse {
  result: 'READY' | 'INVALID' | 'PENDING_ARBITRATION' | 'PENDING_APPROVAL'
  proposal_id: string | null
  decision_id: string | null
  decision: Decision | null

  // Basic validation
  validation_status: string
  violations: Violation[]
  warnings: string[]
  skipped_rules: string[]
  advisory_notes: string[]

  // Enhanced validation results
  quality: QualityResult | null
  duplicates: DuplicateResult | null
  conflicts: ConflictResult | null
  impact: ImpactResult | null
  metadata_suggestions: MetadataSuggestion | null

  // Arbitration
  arbitration_required: boolean
  arbitration_contexts: ArbitrationContext[] | null
  ai_verdicts: Record<string, AIVerdictResult> | null

  // Approval flow
  approval_summary: ApprovalSummary | null

  schema_version: string
  specification_version: string
  validated_at: string
}

export interface EnhancedValidateRequest {
  record: Record<string, any>
  authorship_metadata?: { author: string; author_type: 'human' | 'ai'; session_id?: string }
  arbitration_mode?: ArbitrationMode
  arbitration_verdicts?: ArbitrationVerdictInput[]
}

export interface ApproveDecisionRequest {
  proposal_id: string
  approved_by: string
  approval_comment?: string
}

export interface ApproveDecisionResponse {
  result: 'APPROVED' | 'STORED' | 'REJECTED' | 'NOT_FOUND' | 'ERROR'
  decision_id: string | null
  decision_code: string | null
  stored_at: string | null
  message: string | null
}

// AI Provider Types
export interface AIProviderInfo {
  id: string
  name: string
  default_model: string
  models: string[]
}

export interface AIProvidersResponse {
  providers: AIProviderInfo[]
  current_provider: string | null
  is_configured: boolean
}

// =============================================================================
// Enhanced Validation API
// =============================================================================

export const enhancedValidationApi = {
  // Validate with enhanced features
  validate: async (request: EnhancedValidateRequest) => {
    const response = await api.post<EnhancedValidationResponse>('/api/v1/validate/enhanced', request)
    return response.data
  },

  // Approve a pending decision
  approve: async (request: ApproveDecisionRequest) => {
    const response = await api.post<ApproveDecisionResponse>('/api/v1/decisions/approve', request)
    return response.data
  },

  // Get available AI providers
  getProviders: async () => {
    const response = await api.get<AIProvidersResponse>('/api/v1/ai/providers')
    return response.data
  },
}

// Export for backward compatibility
export default api
