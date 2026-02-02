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

// Section types for Layer B content
export type SectionType = 'OVERVIEW' | 'RULES' | 'EXAMPLES' | 'STRUCTURE' | 'DIAGRAM' | 'REFERENCE'

export interface ContentSection {
  section_id: string
  title: string
  section_type: SectionType
  content: string
  order: number
}

export interface Decision {
  decision_id: string
  decision_code: string | null  // Human-readable code: INT-A01-001-v1.0.0
  domain_id: string  // INT, ARCH, CTL, EVO
  aspect_id: string  // A01-A16
  // Backward compatibility aliases (deprecated)
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
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

  // Layer B: Detailed Content (Two-Layer Content Model)
  detailed_content?: string | null  // Full Markdown specification
  sections?: ContentSection[]  // Structured sections for selective retrieval
  content_summary?: string | null  // Token-efficient summary (~50-100 words)
}

export interface DecisionCreate {
  domain_id: string  // INT, ARCH, CTL, EVO
  aspect_id: string  // A01-A16
  // Backward compatibility aliases (deprecated)
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
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
  common_domain: boolean   // Renamed from common_group
  common_aspect: boolean   // Renamed from common_feature
  // Backward compatibility
  common_group?: boolean   // @deprecated Use common_domain instead
  common_feature?: boolean // @deprecated Use common_aspect instead
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
  common_domain: boolean   // Renamed from common_group
  common_aspect: boolean   // Renamed from common_feature
  // Backward compatibility
  common_group?: boolean   // @deprecated Use common_domain instead
  common_feature?: boolean // @deprecated Use common_aspect instead
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
  list: async (params?: { limit?: number; offset?: number; domain_id?: string; aspect_id?: string }) => {
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
  domain_id: string   // Renamed from group_id
  aspect_id: string   // Renamed from feature_id
  // Backward compatibility
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
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

// =============================================================================
// Semantic Search Types
// =============================================================================

export interface SearchHit {
  decision_id: string
  decision_code: string | null
  statement: string
  rationale: string
  score: number
  domain_id: string   // Renamed from group_id
  aspect_id: string   // Renamed from feature_id
  // Backward compatibility
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
  version: string
  tags: string[]
  matched_fields: string[]
}

export interface SemanticSearchResponse {
  query: string
  hits: SearchHit[]
  total_hits: number
  search_time_ms: number
  embedding_time_ms: number
  filters_applied: Record<string, any>
}

export interface AlignmentResult {
  decision_id: string
  decision_code: string | null
  statement: string
  similarity: number
  domain_id: string   // Renamed from group_id
  aspect_id: string   // Renamed from feature_id
  // Backward compatibility
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
  alignment_type: 'CONFLICT' | 'ALIGNED' | 'RELATED' | 'NEUTRAL'
  notes: string
}

export interface AlignmentResponse {
  proposal_statement: string
  proposal_domain_id: string | null   // Renamed from proposal_group_id
  proposal_aspect_id: string | null   // Renamed from proposal_feature_id
  // Backward compatibility
  proposal_group_id?: string | null   // @deprecated Use proposal_domain_id instead
  proposal_feature_id?: string | null // @deprecated Use proposal_aspect_id instead
  conflicts: AlignmentResult[]
  aligned: AlignmentResult[]
  related: AlignmentResult[]
  overall_alignment_score: number
  recommendation: 'PROCEED' | 'REVIEW_CONFLICTS' | 'MAJOR_CONFLICTS'
  check_time_ms: number
}

export interface SearchStats {
  total_decisions: number
  indexed_decisions: number
  index_size_mb: number
  last_indexed_at: string | null
  embedding_model: string
}

export interface SemanticSearchRequest {
  query: string
  domain_id?: string  // Filter by domain
  aspect_id?: string  // Filter by aspect
  tags?: string[]
  min_score?: number
  limit?: number
}

export interface AlignmentCheckRequest {
  statement: string
  rationale?: string
  domain_id?: string  // Filter by domain
  aspect_id?: string  // Filter by aspect
  threshold?: number
}

// =============================================================================
// Semantic Search API
// =============================================================================

export const searchApi = {
  // Semantic search
  search: async (request: SemanticSearchRequest) => {
    const response = await api.post<SemanticSearchResponse>('/api/v1/search/semantic', request)
    return response.data
  },

  // Check alignment
  checkAlignment: async (request: AlignmentCheckRequest) => {
    const response = await api.post<AlignmentResponse>('/api/v1/search/check-alignment', request)
    return response.data
  },

  // Get index stats
  getStats: async () => {
    const response = await api.get<SearchStats>('/api/v1/search/stats')
    return response.data
  },

  // Rebuild index
  rebuildIndex: async () => {
    const response = await api.post<{ message: string; indexed: number }>('/api/v1/search/rebuild-index')
    return response.data
  },

  // Clear cache
  clearCache: async () => {
    await api.delete('/api/v1/search/cache')
  },
}

// =============================================================================
// Pending Approvals Types
// =============================================================================

export interface PendingApproval {
  proposal_id: string
  decision_id: string
  decision: Decision
  proposed_by: string
  proposed_at: string
  validation_status: string
  quality_score: number
  has_conflicts: boolean
  has_duplicates: boolean
  impact_level: string
  expires_at: string | null
}

export interface PendingApprovalsResponse {
  pending: PendingApproval[]
  total_count: number
}

// =============================================================================
// Approvals API
// =============================================================================

export const approvalsApi = {
  // List pending approvals
  listPending: async (params?: { limit?: number; offset?: number }) => {
    const response = await api.get<PendingApprovalsResponse>('/api/v1/approvals/pending', { params })
    return response.data
  },

  // Approve a decision
  approve: async (proposalId: string, approvedBy: string, comment?: string) => {
    const response = await api.post<ApproveDecisionResponse>('/api/v1/decisions/approve', {
      proposal_id: proposalId,
      approved_by: approvedBy,
      approval_comment: comment,
    })
    return response.data
  },

  // Reject a decision
  reject: async (proposalId: string, rejectedBy: string, reason: string) => {
    const response = await api.post<{ result: string; message: string }>('/api/v1/decisions/reject', {
      proposal_id: proposalId,
      rejected_by: rejectedBy,
      rejection_reason: reason,
    })
    return response.data
  },
}

// =============================================================================
// MCP (Model Context Protocol) Types & API
// =============================================================================

export interface MCPAgent {
  id: string
  name: string
  description: string
  capabilities: string[]
  system_prompt?: string
  tools: string[]
  is_active: boolean
  token_budget: number
  priority: number
}

export interface MCPAgentsResponse {
  agents: MCPAgent[]
  total_count: number
  active_count: number
}

export interface MCPChecklistItem {
  id: string
  text: string
  priority: 'CRITICAL' | 'IMPORTANT' | 'SUPPLEMENTARY' | 'REFERENCE'
  category: string
  required: boolean
}

export interface MCPChecklistResponse {
  checklist: MCPChecklistItem[]
  task_type: string
  total_items: number
}

export interface MCPValidationResult {
  validation_result: 'APPROVED' | 'WARNING' | 'BLOCKED'
  violations: Array<{ action: string; rule: string; severity: string }>
  warnings: Array<{ action: string; suggestion: string }>
  approved_actions: string[]
  requires_review: boolean
}

export interface MCPTaskContextResponse {
  decisions: Array<{
    id: string
    code: string
    statement: string
    relevance_score: number
  }>
  checklist: MCPChecklistItem[]
  constraints: Array<{
    text: string
    type: string
    source_decision: string
  }>
  total_decisions: number
  execution_time_ms: number
}

export const mcpApi = {
  // List available agents
  listAgents: async (): Promise<MCPAgentsResponse> => {
    const response = await api.post<MCPAgentsResponse>('/api/v1/mcp/list-agents', {})
    return response.data
  },

  // Get checklist for task type
  getChecklist: async (taskType: string): Promise<MCPChecklistResponse> => {
    const response = await api.post<MCPChecklistResponse>('/api/v1/mcp/checklist', {
      task_type: taskType
    })
    return response.data
  },

  // Validate proposed actions
  validateActions: async (params: {
    task_type: string
    proposed_actions: string[]
  }): Promise<MCPValidationResult> => {
    const response = await api.post<MCPValidationResult>('/api/v1/mcp/validate-actions', params)
    return response.data
  },

  // Get task context
  getTaskContext: async (params: {
    intent: string
    project?: string
    target?: string
  }): Promise<MCPTaskContextResponse> => {
    const response = await api.post<MCPTaskContextResponse>('/api/v1/mcp/task-context', params)
    return response.data
  },
}

// =============================================================================
// Search Stats Types & API
// =============================================================================

export interface SearchStatsResponse {
  total_indexed: number
  qdrant_status: 'connected' | 'disconnected'
  collection_info?: {
    vectors_count: number
    indexed_vectors_count: number
    points_count: number
  }
  cache_stats?: {
    hit_rate: number
    total_requests: number
    cached_queries: number
  }
  last_rebuild?: string
}

export const searchStatsApi = {
  getStats: async (): Promise<SearchStatsResponse> => {
    const response = await api.get<SearchStatsResponse>('/api/v1/search/stats')
    return response.data
  },

  rebuildIndex: async (): Promise<{ message: string; indexed_count: number }> => {
    const response = await api.post('/api/v1/search/rebuild-index')
    return response.data
  },

  clearCache: async (): Promise<{ message: string }> => {
    const response = await api.delete('/api/v1/search/cache')
    return response.data
  },
}

// =============================================================================
// AI Classification Types & API
// =============================================================================

export interface ClassificationContext {
  classification_type: string
  prompt: string
  taxonomy: string
  expected_response: {
    format: string
    schema: {
      domain_id: string  // Renamed from group_id
      aspect_id: string  // Renamed from feature_id
      confidence: string
    }
  }
}

export interface ClassificationResult {
  domain_id: string  // INT, ARCH, CTL, EVO
  aspect_id: string  // A01-A16
  // Backward compatibility
  group_id?: string   // @deprecated Use domain_id instead
  feature_id?: string // @deprecated Use aspect_id instead
  confidence: number // 0.0-1.0
}

export interface ClassifyRequest {
  statement: string
  rationale: string
  constraints?: Array<{ type: string; statement: string }>
  classification_mode?: 'SERVER' | 'DELEGATED'
  classification_result?: ClassificationResult  // For follow-up with verdict
}

export interface ClassifyResponse {
  domain_id: string | null  // Renamed from group_id
  aspect_id: string | null  // Renamed from feature_id
  // Backward compatibility
  group_id?: string | null   // @deprecated Use domain_id instead
  feature_id?: string | null // @deprecated Use aspect_id instead
  confidence: number
  success: boolean
  classification_required: boolean
  classification_context: ClassificationContext | null
  message: string | null
}

export const classificationApi = {
  // Auto-classify decision into Group and Feature
  classify: async (request: ClassifyRequest): Promise<ClassifyResponse> => {
    const response = await api.post<ClassifyResponse>('/api/v1/classify', request)
    return response.data
  },

  // Get classification context for delegated mode (MCP)
  getContext: async (statement: string, rationale: string): Promise<ClassificationContext> => {
    const response = await api.post<any>('/api/v1/mcp/classify', {
      statement,
      rationale
    })
    return {
      classification_type: response.data.classification_type,
      prompt: response.data.prompt,
      taxonomy: response.data.taxonomy,
      expected_response: response.data.expected_response
    }
  },

  // Submit classification result (delegated mode follow-up)
  submitClassification: async (
    statement: string,
    rationale: string,
    result: ClassificationResult
  ): Promise<ClassifyResponse> => {
    const response = await api.post<ClassifyResponse>('/api/v1/classify', {
      statement,
      rationale,
      classification_result: result
    })
    return response.data
  },

  // Validate classification result
  validate: (domainId: string, aspectId: string): { valid: boolean; error: string | null } => {
    const validDomains = ['INT', 'ARCH', 'CTL', 'EVO']
    const domainAspects: Record<string, string[]> = {
      INT: ['A01', 'A02', 'A03', 'A04'],
      ARCH: ['A05', 'A06', 'A07', 'A08'],
      CTL: ['A09', 'A10', 'A11', 'A12'],
      EVO: ['A13', 'A14', 'A15', 'A16'],
    }

    if (!validDomains.includes(domainId)) {
      return { valid: false, error: `Invalid domain: ${domainId}. Must be one of: ${validDomains.join(', ')}` }
    }

    const validAspects = domainAspects[domainId] || []
    if (!validAspects.includes(aspectId)) {
      return { valid: false, error: `Aspect ${aspectId} not compatible with domain ${domainId}. Valid: ${validAspects.join(', ')}` }
    }

    return { valid: true, error: null }
  }
}

// =============================================================================
// Analytics Types & API
// =============================================================================

export interface AnalyticsSummary {
  total_decisions_tracked: number
  total_events: number
  total_feedback: number
  hot_decisions_count: number
  stale_decisions_count: number
  problematic_decisions_count: number
}

export interface DecisionStats {
  decision_id: string
  view_count: number
  apply_count: number
  skip_count: number
  feedback_count: number
  helpful_count: number
  not_helpful_count: number
  health: string
  last_viewed: string | null
  last_applied: string | null
  relevance_boost: number
}

export interface HealthDistribution {
  distribution: Record<string, number>
  total: number
}

export const analyticsApi = {
  // Get analytics summary
  getSummary: async (): Promise<AnalyticsSummary> => {
    const response = await api.get<AnalyticsSummary>('/api/v1/analytics/summary')
    return response.data
  },

  // Get decision stats
  getDecisionStats: async (decisionId: string): Promise<DecisionStats> => {
    const response = await api.get<DecisionStats>(`/api/v1/analytics/decision/${decisionId}`)
    return response.data
  },

  // Get hot decisions
  getHotDecisions: async (limit: number = 20): Promise<{ decisions: string[]; count: number }> => {
    const response = await api.get<{ decisions: string[]; count: number }>('/api/v1/analytics/hot', {
      params: { limit }
    })
    return response.data
  },

  // Get stale decisions
  getStaleDecisions: async (days: number = 30): Promise<{ decisions: string[]; count: number }> => {
    const response = await api.get<{ decisions: string[]; count: number }>('/api/v1/analytics/stale', {
      params: { days }
    })
    return response.data
  },

  // Get problematic decisions
  getProblematicDecisions: async (): Promise<{ decisions: string[]; count: number }> => {
    const response = await api.get<{ decisions: string[]; count: number }>('/api/v1/analytics/problematic')
    return response.data
  },

  // Get health distribution
  getHealthDistribution: async (): Promise<HealthDistribution> => {
    const response = await api.get<HealthDistribution>('/api/v1/analytics/health-distribution')
    return response.data
  },

  // Track event
  trackEvent: async (params: {
    event_type: 'VIEW' | 'APPLY' | 'SKIP'
    decision_id: string
    decision_code?: string
    query?: string
    file_path?: string
  }) => {
    const response = await api.post('/api/v1/analytics/track/event', params)
    return response.data
  },

  // Track feedback
  trackFeedback: async (params: {
    decision_id: string
    feedback_type: 'HELPFUL' | 'NOT_HELPFUL' | 'OUTDATED' | 'UNCLEAR' | 'WRONG_CONTEXT'
    comment?: string
  }) => {
    const response = await api.post('/api/v1/analytics/track/feedback', params)
    return response.data
  },
}

// =============================================================================
// Document Generation Types & API
// =============================================================================

export interface DocumentTypeInfo {
  type: string
  name: string
  description: string
  phase: string
  primary_audience: string
  secondary_audiences: string[]
  domains: string[]
  tags: string[]
}

export interface GeneratedDocument {
  doc_id: string
  doc_type: string
  title: string
  version: string
  output_format: string
  content: string
  word_count: number
  section_count: number
  decision_count: number
  generated_at: string
  source_decisions: string[]
}

export interface DocumentStats {
  total_document_types: number
  document_types_by_phase: Record<string, number>
  document_types_by_audience: Record<string, number>
}

export const docsApi = {
  // List document types
  listTypes: async (): Promise<DocumentTypeInfo[]> => {
    const response = await api.get<DocumentTypeInfo[]>('/api/v1/docs/types')
    return response.data
  },

  // Get document type info
  getType: async (docType: string): Promise<DocumentTypeInfo> => {
    const response = await api.get<DocumentTypeInfo>(`/api/v1/docs/types/${docType}`)
    return response.data
  },

  // Generate document
  generate: async (params: {
    doc_type: string
    title?: string
    version?: string
    output_format?: string
    scope_filter?: string
    domain_filter?: string
    tag_filter?: string[]
    max_decisions?: number
    company_name?: string
    include_toc?: boolean
    include_metadata?: boolean
  }): Promise<GeneratedDocument> => {
    const response = await api.post<GeneratedDocument>('/api/v1/docs/generate', params)
    return response.data
  },

  // Get document stats
  getStats: async (): Promise<DocumentStats> => {
    const response = await api.get<DocumentStats>('/api/v1/docs/stats')
    return response.data
  },

  // Preview document structure
  preview: async (docType: string, scopeFilter?: string, domainFilter?: string) => {
    const response = await api.get(`/api/v1/docs/preview/${docType}`, {
      params: { scope_filter: scopeFilter, domain_filter: domainFilter }
    })
    return response.data
  },
}

// =============================================================================
// Retrieval Types & API
// =============================================================================

export interface RetrievalResult {
  decision_id: string
  decision_code: string
  statement: string
  rationale: string | null
  confidence: number
  relevance_score: number
  source: string
  matched_by: string[]
}

export interface RetrievalResponse {
  results: RetrievalResult[]
  total_count: number
  from_cache: boolean
  triggered_by: string[]
  execution_time_ms: number
  token_count: number
  suggestions: string[]
}

export interface TriggerInfo {
  trigger_id: string
  name: string
  type: string
  priority: string
  matched_patterns: string[]
  decision_ids: string[]
}

export interface TriggerCheckResponse {
  triggered: boolean
  triggers: TriggerInfo[]
  decision_ids: string[]
}

export interface CacheStats {
  context_cache: {
    total_entries: number
    hit_rate: number
    avg_age_seconds: number
    memory_bytes: number
    hits: number
    misses: number
  }
  hot_cache: {
    total_entries: number
    hit_rate: number
    memory_bytes: number
  }
}

export const retrievalApi = {
  // Context-aware retrieval
  retrieve: async (params: {
    query: string
    file_path?: string
    file_content?: string
    scope_path?: string
    max_results?: number
    token_budget?: number
    use_cache?: boolean
    track_usage?: boolean
  }): Promise<RetrievalResponse> => {
    const response = await api.post<RetrievalResponse>('/api/v1/retrieval/retrieve', params)
    return response.data
  },

  // Check triggers
  checkTriggers: async (params: {
    file_path?: string
    file_content?: string
    scope_path?: string
    keywords?: string[]
  }): Promise<TriggerCheckResponse> => {
    const response = await api.post<TriggerCheckResponse>('/api/v1/retrieval/check-triggers', params)
    return response.data
  },

  // Get hot decisions
  getHotDecisions: async (limit: number = 20) => {
    const response = await api.get('/api/v1/retrieval/hot-decisions', { params: { limit } })
    return response.data
  },

  // Get cache stats
  getCacheStats: async (): Promise<CacheStats> => {
    const response = await api.get<CacheStats>('/api/v1/retrieval/cache/stats')
    return response.data
  },

  // Invalidate cache
  invalidateCache: async (scopePath?: string, decisionId?: string) => {
    const response = await api.post('/api/v1/retrieval/cache/invalidate', null, {
      params: { scope_path: scopePath, decision_id: decisionId }
    })
    return response.data
  },

  // Get context window
  getContextWindow: async (scopePath: string, maxDecisions: number = 10, tokenBudget: number = 2000) => {
    const response = await api.get('/api/v1/retrieval/context-window', {
      params: { scope_path: scopePath, max_decisions: maxDecisions, token_budget: tokenBudget }
    })
    return response.data
  },
}

// Export for backward compatibility
export default api
