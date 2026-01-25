/**
 * ATLAS_CHAT_AI TypeScript SDK
 *
 * A TypeScript/JavaScript client for interacting with the ATLAS_CHAT_AI service.
 *
 * @example
 * ```typescript
 * import { ChatClient } from '@atlas/chat-ai-sdk';
 *
 * const client = new ChatClient({
 *   baseUrl: 'http://localhost:8003',
 *   tenantId: 'my-tenant',
 *   apiKey: 'sk_my_api_key',
 * });
 *
 * // Send a message
 * const response = await client.chat('Hello!');
 * console.log(response.content);
 *
 * // Stream a response
 * for await (const chunk of client.chatStream('Tell me a story')) {
 *   process.stdout.write(chunk);
 * }
 * ```
 */

// =============================================================================
// Types
// =============================================================================

export interface ChatClientConfig {
  baseUrl?: string;
  tenantId: string;
  apiKey?: string;
  jwtToken?: string;
  userId?: string;
  timeout?: number;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
}

export interface ChatResponse {
  sessionId: string;
  messageId: string;
  content: string;
  retrievedDocs: string[];
  tokenUsage?: TokenUsage;
}

export interface SearchResult {
  documentId: string;
  chunkId: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export interface Session {
  id: string;
  title?: string;
  summary?: string;
  messageCount: number;
  startedAt?: Date;
  updatedAt?: Date;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: Date;
}

export interface UserFact {
  id: string;
  factType: string;
  content: string;
  confidence: number;
  isActive: boolean;
  createdAt?: Date;
}

export interface ChatOptions {
  sessionId?: string;
  pageContext?: string;
  useRag?: boolean;
}

export class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number,
    public details?: Record<string, any>
  ) {
    super(`${code}: ${message}`);
    this.name = 'APIError';
  }
}

// =============================================================================
// Client
// =============================================================================

export class ChatClient {
  private baseUrl: string;
  private tenantId: string;
  private apiKey?: string;
  private jwtToken?: string;
  private userId?: string;
  private timeout: number;

  constructor(config: ChatClientConfig) {
    this.baseUrl = (config.baseUrl || 'http://localhost:8003').replace(/\/$/, '');
    this.tenantId = config.tenantId;
    this.apiKey = config.apiKey;
    this.jwtToken = config.jwtToken;
    this.userId = config.userId;
    this.timeout = config.timeout || 60000;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Tenant-ID': this.tenantId,
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    } else if (this.jwtToken) {
      headers['Authorization'] = `Bearer ${this.jwtToken}`;
    }

    if (this.userId) {
      headers['X-User-ID'] = this.userId;
    }

    return headers;
  }

  private async request<T>(
    method: string,
    path: string,
    options?: {
      body?: Record<string, any>;
      params?: Record<string, any>;
    }
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}/api/v1${path}`);

    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: this.getHeaders(),
        body: options?.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      const result = await response.json();

      if (!result.success) {
        throw new APIError(
          result.error?.code || 'UNKNOWN_ERROR',
          result.error?.message || 'Unknown error',
          response.status,
          result.error?.details
        );
      }

      return result.data ?? result;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ===========================================================================
  // Chat Methods
  // ===========================================================================

  /**
   * Send a chat message and get a response.
   */
  async chat(message: string, options?: ChatOptions): Promise<ChatResponse> {
    const data = await this.request<any>('POST', '/chat', {
      body: {
        message,
        session_id: options?.sessionId,
        page_context: options?.pageContext,
      },
      params: {
        use_rag: options?.useRag !== false,
      },
    });

    return {
      sessionId: data.session_id,
      messageId: data.message_id,
      content: data.content,
      retrievedDocs: data.retrieved_docs || [],
      tokenUsage: data.token_usage
        ? {
            promptTokens: data.token_usage.prompt_tokens,
            completionTokens: data.token_usage.completion_tokens,
          }
        : undefined,
    };
  }

  /**
   * Stream a chat response using Server-Sent Events.
   */
  async *chatStream(message: string, options?: ChatOptions): AsyncGenerator<string> {
    const url = new URL(`${this.baseUrl}/api/v1/chat/stream`);
    url.searchParams.set('use_rag', String(options?.useRag !== false));

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        message,
        session_id: options?.sessionId,
        page_context: options?.pageContext,
      }),
    });

    if (!response.ok) {
      throw new APIError('STREAM_ERROR', 'Failed to start stream', response.status);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new APIError('STREAM_ERROR', 'No response body', 500);
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const data = JSON.parse(line.slice(5).trim());
          if (data.content) {
            yield data.content;
          } else if (data.error) {
            throw new APIError('STREAM_ERROR', data.error, 500);
          }
        }
      }
    }
  }

  // ===========================================================================
  // Session Methods
  // ===========================================================================

  /**
   * List user's chat sessions.
   */
  async listSessions(limit = 20, offset = 0): Promise<Session[]> {
    const data = await this.request<any>('GET', '/sessions', {
      params: { limit, offset },
    });

    const sessions = Array.isArray(data) ? data : data.sessions || [];
    return sessions.map(this.parseSession);
  }

  /**
   * Get a session by ID.
   */
  async getSession(sessionId: string): Promise<Session> {
    const data = await this.request<any>('GET', `/sessions/${sessionId}`);
    return this.parseSession(data);
  }

  /**
   * Get messages for a session.
   */
  async getSessionMessages(sessionId: string, limit = 50): Promise<Message[]> {
    const data = await this.request<any>('GET', `/sessions/${sessionId}/messages`, {
      params: { limit },
    });

    const messages = Array.isArray(data) ? data : data.messages || [];
    return messages.map(this.parseMessage);
  }

  /**
   * Delete a session.
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.request('DELETE', `/sessions/${sessionId}`);
  }

  // ===========================================================================
  // Search Methods
  // ===========================================================================

  /**
   * Search the knowledge base.
   */
  async search(
    query: string,
    topK = 5,
    scoreThreshold = 0.5
  ): Promise<SearchResponse> {
    const data = await this.request<any>('POST', '/search', {
      body: {
        query,
        top_k: topK,
        score_threshold: scoreThreshold,
      },
    });

    return {
      results: (data.results || []).map((r: any) => ({
        documentId: r.document_id,
        chunkId: r.chunk_id,
        content: r.content,
        score: r.score,
        metadata: r.metadata || {},
      })),
      total: data.total || 0,
      query: data.query || query,
    };
  }

  // ===========================================================================
  // Memory Methods
  // ===========================================================================

  /**
   * List user facts from memory.
   */
  async listFacts(factType?: string, activeOnly = true): Promise<UserFact[]> {
    const data = await this.request<any>('GET', '/memory/facts', {
      params: {
        fact_type: factType,
        active_only: activeOnly,
      },
    });

    const facts = Array.isArray(data) ? data : data.facts || data;
    return facts.map((f: any) => ({
      id: f.id,
      factType: f.fact_type,
      content: f.content,
      confidence: f.confidence,
      isActive: f.is_active,
      createdAt: f.created_at ? new Date(f.created_at) : undefined,
    }));
  }

  /**
   * Create a user fact.
   */
  async createFact(
    content: string,
    factType = 'GENERAL',
    confidence = 1.0
  ): Promise<string> {
    const data = await this.request<any>('POST', '/memory/facts', {
      body: {
        fact_type: factType,
        content,
        confidence,
      },
    });

    return data.fact_id;
  }

  /**
   * Delete (deactivate) a fact.
   */
  async deleteFact(factId: string): Promise<void> {
    await this.request('DELETE', `/memory/facts/${factId}`);
  }

  /**
   * Search past sessions by semantic similarity.
   */
  async searchPastSessions(query: string, topK = 5): Promise<Session[]> {
    const data = await this.request<any>('GET', '/memory/sessions/search', {
      params: { query, top_k: topK },
    });

    const sessions = Array.isArray(data) ? data : data.sessions || data;
    return sessions.map(this.parseSession);
  }

  // ===========================================================================
  // Helpers
  // ===========================================================================

  private parseSession(data: any): Session {
    return {
      id: data.id || data.session_id,
      title: data.title,
      summary: data.summary,
      messageCount: data.message_count || 0,
      startedAt: data.started_at ? new Date(data.started_at) : undefined,
      updatedAt: data.updated_at ? new Date(data.updated_at) : undefined,
    };
  }

  private parseMessage(data: any): Message {
    return {
      id: data.id,
      role: data.role,
      content: data.content,
      createdAt: data.created_at ? new Date(data.created_at) : undefined,
    };
  }
}

export default ChatClient;
