/**
 * MANTRA Backend API Client
 *
 * Wraps calls to the MANTRA Constitutional Law backend API.
 * Updated to match MANTRA-SCHEMA-001 and MANTRA-LAW-001.
 */

// ============================================================================
// Types matching MANTRA-SCHEMA-001
// ============================================================================

export type DomainId = 'INT' | 'ARCH' | 'CTL' | 'EVO'
export type AspectId = 'A01' | 'A02' | 'A03' | 'A04' | 'A05' | 'A06' | 'A07' | 'A08' |
                       'A09' | 'A10' | 'A11' | 'A12' | 'A13' | 'A14' | 'A15' | 'A16'
export type Scope = 'ORGANIZATION' | 'DOMAIN' | 'APPLICATION'
export type BlastRadius = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type ConstraintType = 'PROHIBITION' | 'REQUIREMENT' | 'LIMITATION'

export interface Constraint {
  constraint_id: string
  statement: string
  type: ConstraintType
}

export interface ContentSection {
  section_id: string
  title: string
  section_type: 'OVERVIEW' | 'RULES' | 'EXAMPLES' | 'STRUCTURE' | 'DIAGRAM' | 'REFERENCE'
  content: string
  order: number
}

export interface Decision {
  decision_id: string
  decision_code: string
  domain_id: DomainId
  aspect_id: AspectId
  statement: string
  rationale: string
  constraints: Constraint[]
  invariants: string[]
  scope: Scope
  blast_radius: BlastRadius
  version: string
  created_by?: string
  created_at?: string
  approved_by?: string
  approved_at?: string
  supersedes?: string
  related_decisions: string[]
  tags: string[]
  tech_stack: string[]
  detailed_content?: string
  sections: ContentSection[]
  content_summary?: string
}

export interface DecisionCreate {
  domain_id: DomainId
  aspect_id: AspectId
  statement: string
  rationale: string
  constraints?: Constraint[]
  invariants?: string[]
  scope: Scope
  blast_radius: BlastRadius
  version: string
  created_by: string
  supersedes?: string
  related_decisions?: string[]
  tags?: string[]
  tech_stack?: string[]
  detailed_content?: string
  sections?: ContentSection[]
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  suggestions: string[]
}

export interface AIHint {
  type: 'suggestion' | 'warning' | 'info'
  message: string
  related_decisions?: string[]
}

// Domain-Aspect compatibility matrix per MANTRA-LAW-001
export const DOMAIN_ASPECT_MATRIX: Record<DomainId, AspectId[]> = {
  INT: ['A01', 'A02', 'A03', 'A04'],
  ARCH: ['A05', 'A06', 'A07', 'A08'],
  CTL: ['A09', 'A10', 'A11', 'A12'],
  EVO: ['A13', 'A14', 'A15', 'A16'],
}

export const DOMAIN_LABELS: Record<DomainId, string> = {
  INT: 'Intent & Direction (WHY/WHAT)',
  ARCH: 'Architecture & Boundaries (HOW/WHERE)',
  CTL: 'Control, Policy & Risk (CAN/MUST NOT)',
  EVO: 'Execution & Evolution (CHANGE SAFELY)',
}

export const ASPECT_LABELS: Record<AspectId, string> = {
  A01: 'Vision & Outcome',
  A02: 'Problem Statement',
  A03: 'Scope & Non-Goals',
  A04: 'Principles & Values',
  A05: 'Domain & Bounded Context',
  A06: 'Service & Module Boundary',
  A07: 'Data Ownership & Sovereignty',
  A08: 'Integration & Contract Model',
  A09: 'Policy & Rules',
  A10: 'Approval & Authority Model',
  A11: 'Security & Compliance Posture',
  A12: 'Risk & Blast Radius',
  A13: 'Decision Lifecycle',
  A14: 'Reversibility & Exit Strategy',
  A15: 'Environment & Promotion Rules',
  A16: 'Anti-Drift & Consistency',
}

export class MantraClient {
  private baseUrl: string
  private apiKey: string

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
    this.apiKey = apiKey
  }

  private async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`MANTRA API error (${response.status}): ${error}`)
    }

    return response.json() as Promise<T>
  }

  // ==================== DECISIONS ====================

  async listDecisions(params?: {
    domain_id?: DomainId
    aspect_id?: AspectId
    search?: string
    limit?: number
    offset?: number
  }): Promise<Decision[]> {
    const queryParams = new URLSearchParams()
    if (params?.domain_id) queryParams.set('domain_id', params.domain_id)
    if (params?.aspect_id) queryParams.set('aspect_id', params.aspect_id)
    if (params?.search) queryParams.set('search', params.search)
    if (params?.limit) queryParams.set('limit', String(params.limit))
    if (params?.offset) queryParams.set('offset', String(params.offset))

    const query = queryParams.toString()
    const response = await this.fetch<{ decisions: Decision[] }>(`/api/v1/decisions${query ? `?${query}` : ''}`)
    return response.decisions || []
  }

  async getDecision(id: string): Promise<Decision> {
    return this.fetch<Decision>(`/api/v1/decisions/${id}`)
  }

  // ==================== CREATE DECISION ====================

  async createDecision(decision: DecisionCreate, storedBy: string): Promise<Decision> {
    // API expects: { decision: {...}, stored_by: "..." }
    // API returns: { result, decision_id, stored_at, error_message }
    const response = await this.fetch<{
      result: string
      decision_id: string
      stored_at: string
      error_message: string | null
    }>('/api/v1/decisions', {
      method: 'POST',
      body: JSON.stringify({
        decision: decision,
        stored_by: storedBy
      }),
    })

    if (response.result !== 'STORED' || response.error_message) {
      throw new Error(response.error_message || 'Failed to create decision')
    }

    // Fetch the created decision to get full details
    return this.getDecision(response.decision_id)
  }

  // ==================== VALIDATION ====================

  async validateDecision(decision: Partial<DecisionCreate>): Promise<ValidationResult> {
    // API expects: { record: {...} }
    return this.fetch<ValidationResult>('/api/v1/validate', {
      method: 'POST',
      body: JSON.stringify({ record: decision }),
    })
  }

  // ==================== GROUPS ====================

  async getGroupedDecisions(): Promise<Record<DomainId, Decision[]>> {
    const response = await this.fetch<{ decisions: Decision[] }>('/api/v1/decisions')
    const decisions = response.decisions || []

    // Group by domain_id
    const grouped: Record<string, Decision[]> = {}
    for (const decision of decisions) {
      const key = decision.domain_id || 'UNKNOWN'
      if (!grouped[key]) {
        grouped[key] = []
      }
      grouped[key].push(decision)
    }

    return grouped as Record<DomainId, Decision[]>
  }

  // ==================== AI ====================

  async getHints(context: string): Promise<AIHint[]> {
    return this.fetch<AIHint[]>('/api/v1/ai/hints', {
      method: 'POST',
      body: JSON.stringify({ context }),
    })
  }

  // ==================== SEMANTIC SEARCH ====================

  async semanticSearch(params: {
    query: string
    limit?: number
    min_score?: number
    domain_id?: DomainId
    aspect_id?: AspectId
    tags?: string[]
    use_cache?: boolean
  }): Promise<{
    status: string
    hits: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      domain_id: DomainId
      aspect_id: AspectId
      version: string
      tags: string[]
      matched_fields: string[]
    }>
    total_count: number
    query: string
    filters_applied: Record<string, unknown>
    execution_time_ms: number
    cached: boolean
    error_message?: string
  }> {
    return this.fetch('/api/v1/search/semantic', {
      method: 'POST',
      body: JSON.stringify({
        query: params.query,
        limit: params.limit || 10,
        min_score: params.min_score || 0.5,
        domain_id: params.domain_id,
        aspect_id: params.aspect_id,
        tags: params.tags,
        use_cache: params.use_cache !== false
      })
    })
  }

  async checkAlignment(params: {
    statement: string
    rationale?: string
    domain_id?: DomainId
    min_score?: number
  }): Promise<{
    status: string
    aligned_with: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      domain_id: DomainId
      aspect_id: AspectId
      version: string
      tags: string[]
    }>
    conflicts_with: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      domain_id: DomainId
      aspect_id: AspectId
      version: string
      tags: string[]
    }>
    related_decisions: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      domain_id: DomainId
      aspect_id: AspectId
      version: string
      tags: string[]
    }>
    recommendations: string[]
    execution_time_ms: number
    error_message?: string
  }> {
    return this.fetch('/api/v1/search/check-alignment', {
      method: 'POST',
      body: JSON.stringify({
        statement: params.statement,
        rationale: params.rationale || '',
        domain_id: params.domain_id,
        min_score: params.min_score || 0.6
      })
    })
  }

  async getSearchStats(): Promise<{
    collection_name: string
    count: number
    vector_size: number
    status: string
    cache_enabled: boolean
    embedding_model: string
    embedding_dimensions: number
  }> {
    return this.fetch('/api/v1/search/stats')
  }

  // ==================== HEALTH ====================

  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    return this.fetch('/health')
  }

  // ==================== ENHANCED RETRIEVAL ====================

  async retrieve(params: {
    query: string
    file_path?: string
    file_content?: string
    scope_path?: string
    max_results?: number
    token_budget?: number
    use_cache?: boolean
    track_usage?: boolean
  }): Promise<{
    results: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale?: string
      confidence: number
      relevance_score: number
      source: string
      matched_by: string[]
    }>
    total_count: number
    from_cache: boolean
    triggered_by: string[]
    execution_time_ms: number
    token_count: number
    suggestions: string[]
  }> {
    return this.fetch('/api/v1/retrieval/retrieve', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async checkTriggers(params: {
    file_path?: string
    file_content?: string
    scope_path?: string
    keywords?: string[]
  }): Promise<{
    triggered: boolean
    triggers: Array<{
      trigger_id: string
      name: string
      type: string
      priority: string
      matched_patterns: string[]
      decision_ids: string[]
    }>
    decision_ids: string[]
  }> {
    return this.fetch('/api/v1/retrieval/check-triggers', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async getHotDecisions(limit: number = 20): Promise<{
    decisions: string[]
    count: number
    cache_size: number
    max_size: number
  }> {
    return this.fetch(`/api/v1/retrieval/hot-decisions?limit=${limit}`)
  }

  // ==================== 3-GATE VALIDATION ====================

  async validateGate1(decision: Record<string, unknown>): Promise<{
    status: string
    rules_checked: number
    rules_passed: number
    violations: Array<{
      rule_id: string
      field: string
      message: string
      severity: string
    }>
    warnings: Array<{
      rule_id: string
      field: string
      message: string
    }>
    can_proceed_to_gate2: boolean
    validation_time_ms: number
  }> {
    return this.fetch('/api/v1/validation/gate1', {
      method: 'POST',
      body: JSON.stringify(decision)
    })
  }

  async validatePipeline(params: {
    decision: Record<string, unknown>
    submitted_by: string
    auto_create_approval?: boolean
  }): Promise<{
    outcome: string
    stage: string
    decision_id: string
    decision_code: string
    gate1: Record<string, unknown> | null
    gate2: Record<string, unknown> | null
    gate3: Record<string, unknown> | null
    approval_request_id?: string
    messages: string[]
    can_activate: boolean
  }> {
    return this.fetch('/api/v1/validation/pipeline', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async getPendingApprovals(reviewerId?: string): Promise<Array<{
    request_id: string
    decision_id: string
    decision_code: string
    status: string
    submitted_by: string
    submitted_at: string
    assigned_to?: string
    gate1_passed: boolean
    gate2_passed: boolean
    comments_count: number
  }>> {
    const query = reviewerId ? `?reviewer_id=${encodeURIComponent(reviewerId)}` : ''
    return this.fetch(`/api/v1/validation/approvals/pending${query}`)
  }

  async approveDecision(params: {
    request_id: string
    approver_id: string
    approver_role?: string
    comment?: string
  }): Promise<{
    success: boolean
    status: string
    message: string
    approved_by?: string
    approved_at?: string
  }> {
    return this.fetch('/api/v1/validation/approvals/approve', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  // ==================== DOCUMENT GENERATION ====================

  async listDocumentTypes(): Promise<Array<{
    type: string
    name: string
    description: string
    phase: string
    primary_audience: string
    secondary_audiences: string[]
    domains: string[]
    tags: string[]
  }>> {
    return this.fetch('/api/v1/docs/types')
  }

  async generateDocument(params: {
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
  }): Promise<{
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
  }> {
    return this.fetch('/api/v1/docs/generate', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  // ==================== ANALYTICS ====================

  async trackEvent(params: {
    event_type: string  // VIEW, APPLY, SKIP
    decision_id: string
    decision_code?: string
    scope_path?: string
    query?: string
    file_path?: string
    user_id?: string
    session_id?: string
  }): Promise<{
    success: boolean
    event_id: string
    event_type: string
  }> {
    return this.fetch('/api/v1/analytics/track/event', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async trackFeedback(params: {
    decision_id: string
    feedback_type: string  // HELPFUL, NOT_HELPFUL, OUTDATED, UNCLEAR, WRONG_CONTEXT
    comment?: string
    context_scope?: string
    user_id?: string
  }): Promise<{
    success: boolean
    feedback_id: string
    feedback_type: string
  }> {
    return this.fetch('/api/v1/analytics/track/feedback', {
      method: 'POST',
      body: JSON.stringify(params)
    })
  }

  async getAnalyticsSummary(): Promise<{
    total_decisions_tracked: number
    total_events: number
    total_feedback: number
    hot_decisions_count: number
    stale_decisions_count: number
    problematic_decisions_count: number
  }> {
    return this.fetch('/api/v1/analytics/summary')
  }

  async getDecisionStats(decisionId: string): Promise<{
    decision_id: string
    view_count: number
    apply_count: number
    skip_count: number
    feedback_count: number
    helpful_count: number
    not_helpful_count: number
    health: string
    last_viewed?: string
    last_applied?: string
    relevance_boost: number
  }> {
    return this.fetch(`/api/v1/analytics/decision/${encodeURIComponent(decisionId)}`)
  }
}
