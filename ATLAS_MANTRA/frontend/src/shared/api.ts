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
  related_decisions: string[]
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
  related_decisions?: string[]
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

// Export for backward compatibility
export default api
