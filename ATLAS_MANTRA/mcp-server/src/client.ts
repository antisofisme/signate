/**
 * MANTRA Backend API Client
 *
 * Wraps calls to the MANTRA Constitutional Law backend API.
 */

export interface Decision {
  id: string
  code: string
  title: string
  group: string
  status: 'draft' | 'proposed' | 'accepted' | 'rejected' | 'superseded'
  layer: 0 | 1 | 2
  content: string
  rationale?: string
  alternatives?: string[]
  implications?: string[]
  references?: string[]
  created_at: string
  updated_at: string
  created_by?: string
  approved_by?: string
  approved_at?: string
}

export interface DecisionProposal {
  title: string
  group: string
  content: string
  rationale?: string
  alternatives?: string[]
  implications?: string[]
  references?: string[]
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  suggestions: string[]
}

export interface AuditEntry {
  id: string
  decision_id: string
  action: string
  actor: string
  timestamp: string
  details?: Record<string, unknown>
}

export interface AIHint {
  type: 'suggestion' | 'warning' | 'info'
  message: string
  related_decisions?: string[]
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
    group?: string
    status?: string
    layer?: number
    search?: string
    limit?: number
    offset?: number
  }): Promise<Decision[]> {
    const queryParams = new URLSearchParams()
    if (params?.group) queryParams.set('group', params.group)
    if (params?.status) queryParams.set('status', params.status)
    if (params?.layer !== undefined) queryParams.set('layer', String(params.layer))
    if (params?.search) queryParams.set('search', params.search)
    if (params?.limit) queryParams.set('limit', String(params.limit))
    if (params?.offset) queryParams.set('offset', String(params.offset))

    const query = queryParams.toString()
    return this.fetch<Decision[]>(`/api/v1/decisions${query ? `?${query}` : ''}`)
  }

  async getDecision(id: string): Promise<Decision> {
    return this.fetch<Decision>(`/api/v1/decisions/${id}`)
  }

  async getDecisionHistory(id: string): Promise<AuditEntry[]> {
    return this.fetch<AuditEntry[]>(`/api/v1/decisions/${id}/history`)
  }

  async compareDecisions(id1: string, id2: string): Promise<{
    decision1: Decision
    decision2: Decision
    differences: string[]
    similarities: string[]
  }> {
    return this.fetch(`/api/v1/decisions/${id1}/compare/${id2}`)
  }

  // ==================== PROPOSALS ====================

  async proposeDecision(proposal: DecisionProposal): Promise<{
    id: string
    status: string
    message: string
  }> {
    return this.fetch('/api/v1/decisions/propose', {
      method: 'POST',
      body: JSON.stringify(proposal),
    })
  }

  async challengeDecision(id: string, challenge: {
    reason: string
    alternative?: string
  }): Promise<{
    status: string
    message: string
  }> {
    return this.fetch(`/api/v1/decisions/${id}/challenge`, {
      method: 'POST',
      body: JSON.stringify(challenge),
    })
  }

  // ==================== VALIDATION ====================

  async validateDecision(decision: Partial<DecisionProposal>): Promise<ValidationResult> {
    return this.fetch<ValidationResult>('/api/v1/validate', {
      method: 'POST',
      body: JSON.stringify(decision),
    })
  }

  // ==================== GROUPS ====================

  async getGroupedDecisions(): Promise<Record<string, Decision[]>> {
    return this.fetch<Record<string, Decision[]>>('/api/v1/grouped')
  }

  // ==================== AUDIT ====================

  async getAuditLog(params?: {
    decision_id?: string
    action?: string
    limit?: number
  }): Promise<AuditEntry[]> {
    const queryParams = new URLSearchParams()
    if (params?.decision_id) queryParams.set('decision_id', params.decision_id)
    if (params?.action) queryParams.set('action', params.action)
    if (params?.limit) queryParams.set('limit', String(params.limit))

    const query = queryParams.toString()
    return this.fetch<AuditEntry[]>(`/api/v1/audit${query ? `?${query}` : ''}`)
  }

  // ==================== AI ====================

  async chat(message: string, context?: string): Promise<{
    response: string
    sources?: string[]
  }> {
    return this.fetch('/api/v1/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, context }),
    })
  }

  async getHints(context: string): Promise<AIHint[]> {
    return this.fetch<AIHint[]>('/api/v1/ai/hints', {
      method: 'POST',
      body: JSON.stringify({ context }),
    })
  }

  async getAIProviders(): Promise<string[]> {
    return this.fetch<string[]>('/api/v1/ai/providers')
  }

  // ==================== SEMANTIC SEARCH ====================

  async semanticSearch(params: {
    query: string
    limit?: number
    min_score?: number
    group_id?: string
    feature_id?: string
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
      group_id: string
      feature_id: string
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
        group_id: params.group_id,
        feature_id: params.feature_id,
        tags: params.tags,
        use_cache: params.use_cache !== false
      })
    })
  }

  async checkAlignment(params: {
    statement: string
    rationale?: string
    group_id?: string
    min_score?: number
  }): Promise<{
    status: string
    aligned_with: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      group_id: string
      feature_id: string
      version: string
      tags: string[]
    }>
    conflicts_with: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      group_id: string
      feature_id: string
      version: string
      tags: string[]
    }>
    related_decisions: Array<{
      decision_id: string
      decision_code: string
      statement: string
      rationale: string
      score: number
      group_id: string
      feature_id: string
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
        group_id: params.group_id,
        min_score: params.min_score || 0.6
      })
    })
  }

  async rebuildSearchIndex(params?: {
    force?: boolean
    batch_size?: number
    group_id?: string
  }): Promise<{
    synced_count: number
    skipped_count: number
    failed_count: number
    total_decisions: number
    execution_time_ms: number
    errors: string[]
  }> {
    return this.fetch('/api/v1/search/rebuild-index', {
      method: 'POST',
      body: JSON.stringify({
        force: params?.force || false,
        batch_size: params?.batch_size || 50,
        group_id: params?.group_id
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
}
