// =============================================================================
// ATLAS_CHAT_AI Types
// =============================================================================

// API Response
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
  meta?: {
    total?: number
    page?: number
    limit?: number
  }
}

// Tenant
export interface TenantConfig {
  id: string
  name: string
  description?: string
  llm_config: LLMConfig
  embedding_config: EmbeddingConfig
  rag_config: RAGConfig
  system_prompt?: string
  persona_name?: string
  max_context_tokens: number
  max_response_tokens: number
  max_messages_per_session: number
  max_sessions_per_user: number
  features: TenantFeatures
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LLMConfig {
  provider: string
  model: string
  temperature: number
  max_tokens: number
}

export interface EmbeddingConfig {
  provider: string
  model: string
  dimensions: number
}

export interface RAGConfig {
  strategy: 'vanilla' | 'hybrid'
  reranker_enabled: boolean
  reranker_provider?: string
  top_k: number
  score_threshold: number
}

export interface TenantFeatures {
  memory_extraction: boolean
  temporal_memory: boolean
  streaming: boolean
  session_summarization: boolean
}

// User
export interface User {
  id: string
  tenant_id: string
  external_user_id: string
  email?: string
  display_name: string
  role: 'admin' | 'user' | 'readonly'
  custom_permissions: string[]
  is_active: boolean
  last_seen_at?: string
  created_at: string
  updated_at: string
}

// API Key
export interface APIKey {
  id: string
  tenant_id: string
  name: string
  key_prefix: string
  permissions: string[]
  rate_limit_per_minute: number
  expires_at?: string
  last_used_at?: string
  is_active: boolean
  created_by: string
  created_at: string
}

export interface APIKeyWithSecret extends APIKey {
  api_key: string // Full key, only returned on creation
}

// Chat
export interface ChatSession {
  id: string
  tenant_id?: string
  user_id?: string
  title?: string | null
  summary?: string | null
  message_count: number
  total_tokens?: number
  is_active?: boolean
  last_message_at?: string | null
  started_at?: string  // API returns started_at
  created_at?: string  // Keep for backwards compatibility
  updated_at?: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  token_count: number
  sources?: SearchResult[]
  created_at: string
}

export interface ChatRequest {
  message: string
  session_id?: string
  page_context?: string
  use_rag?: boolean
  stream?: boolean
}

export interface ChatResponse {
  session_id: string
  message_id: string
  response: string
  sources?: SearchResult[]
  token_usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

// Search
export interface SearchResult {
  id: string
  content: string
  metadata: Record<string, unknown>
  score: number
  source_type: string
}

export interface SearchRequest {
  query: string
  top_k?: number
  score_threshold?: number
  filter?: Record<string, unknown>
}

// Memory
export interface UserFact {
  id: string
  tenant_id: string
  user_id: string
  fact_type: 'preference' | 'context' | 'goal' | 'constraint'
  content: string
  confidence: number
  source_type: 'explicit' | 'inferred' | 'system'
  is_active: boolean
  created_at: string
  updated_at: string
}

// Audit
export interface AuditLog {
  id: string
  tenant_id: string
  actor_type: 'user' | 'api_key' | 'system'
  actor_id: string
  action: string
  resource_type: string
  resource_id?: string
  request_id?: string
  ip_address?: string
  details?: Record<string, unknown>
  status: 'success' | 'failure'
  created_at: string
}

// Stats
export interface SystemStats {
  total_tenants: number
  active_tenants: number
  total_users: number
  active_sessions_today: number
  total_messages_today: number
  total_documents: number
  total_facts: number
  cache_hit_rate: number
  average_response_time_ms: number
}

// Form Types
export interface TenantFormData {
  name: string
  description?: string
  system_prompt?: string
  persona_name?: string
  llm_provider: string
  llm_model: string
  llm_temperature: number
  llm_max_tokens: number
  embedding_provider: string
  embedding_model: string
  rag_strategy: 'vanilla' | 'hybrid'
  rag_top_k: number
  rag_score_threshold: number
  features_memory_extraction: boolean
  features_temporal_memory: boolean
  features_streaming: boolean
  features_session_summarization: boolean
}

export interface UserFormData {
  external_user_id: string
  email?: string
  display_name: string
  role: 'admin' | 'user' | 'readonly'
}

export interface APIKeyFormData {
  name: string
  permissions: string[]
  rate_limit_per_minute: number
  expires_in_days?: number
}
