/**
 * MANTRA SDK Client
 *
 * TypeScript client for ARSAKA_MANTRA Decision System.
 *
 * Per MANTRA-LAW-006: This SDK provides read-only access and proposal capabilities.
 * All modifications require human approval through the dashboard.
 */

import type {
  MantraClientOptions,
  Decision,
  DecisionCreate,
  ListDecisionsParams,
  ValidationResult,
  FullValidationResult,
  RetrievalParams,
  RetrievalResult,
  TriggerCheckParams,
  TriggerCheckResult,
  DocumentType,
  DocumentGenerateRequest,
  GeneratedDocument,
  AnalyticsSummary,
  HealthDistribution,
  DecisionStats,
} from './types';

import {
  MantraError,
  AuthorizationError,
  NotFoundError,
  ConnectionError,
  RateLimitError,
} from './errors';

export class MantraClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(options: MantraClientOptions | string) {
    if (typeof options === 'string') {
      this.baseUrl = options.replace(/\/$/, '');
      this.timeout = 30000;
    } else {
      this.baseUrl = options.baseUrl.replace(/\/$/, '');
      this.apiKey = options.apiKey;
      this.timeout = options.timeout ?? 30000;
    }
  }

  private async request<T>(
    method: string,
    path: string,
    options?: {
      params?: Record<string, string | number | boolean | undefined>;
      body?: unknown;
    }
  ): Promise<T> {
    const url = new URL(path, this.baseUrl);

    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      });
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers,
        body: options?.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.status === 404) {
        const data = await response.json().catch(() => ({}));
        throw new NotFoundError(data.resource ?? 'Resource', data.identifier ?? 'unknown');
      }

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        throw new RateLimitError(retryAfter ? parseInt(retryAfter, 10) : undefined);
      }

      if (response.status === 403) {
        throw new AuthorizationError();
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new MantraError(
          data.message ?? `Request failed with status ${response.status}`,
          data.code,
          data.details
        );
      }

      return response.json() as Promise<T>;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof MantraError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new ConnectionError('Request timed out');
        }
        throw new ConnectionError(error.message);
      }

      throw new ConnectionError('Unknown error');
    }
  }

  // ========================================================================
  // Decision Operations
  // ========================================================================

  async getDecision(decisionId: string): Promise<Decision> {
    return this.request<Decision>('GET', `/api/v1/decisions/${decisionId}`);
  }

  async listDecisions(params?: ListDecisionsParams): Promise<Decision[]> {
    const response = await this.request<{ decisions: Decision[] }>('GET', '/api/v1/decisions', {
      params: {
        domain_id: params?.domain,
        aspect_id: params?.aspect,
        status: params?.status,
        tags: params?.tags?.join(','),
        search: params?.search,
        limit: params?.limit ?? 50,
        offset: params?.offset ?? 0,
      },
    });
    return response.decisions;
  }

  async getDecisionMatrix(): Promise<Record<string, Record<string, Decision[]>>> {
    const response = await this.request<{ matrix: Record<string, Record<string, Decision[]>> }>(
      'GET',
      '/api/v1/decisions/matrix'
    );
    return response.matrix;
  }

  async proposeDecision(decision: DecisionCreate): Promise<{ decision_id: string; status: string }> {
    return this.request<{ decision_id: string; status: string }>('POST', '/api/v1/decisions/propose', {
      body: decision,
    });
  }

  // ========================================================================
  // Validation Operations
  // ========================================================================

  async validateDecision(decision: DecisionCreate): Promise<ValidationResult> {
    return this.request<ValidationResult>('POST', '/api/v1/validate', {
      body: { record: decision },
    });
  }

  async validateFull(decision: DecisionCreate, includeAi = true): Promise<FullValidationResult> {
    return this.request<FullValidationResult>('POST', '/api/v1/validation/pipeline', {
      body: {
        record: decision,
        include_ai: includeAi,
      },
    });
  }

  async getPendingApprovals(): Promise<Array<{ decision_id: string; status: string }>> {
    const response = await this.request<{ pending: Array<{ decision_id: string; status: string }> }>(
      'GET',
      '/api/v1/validation/pending'
    );
    return response.pending;
  }

  // ========================================================================
  // Retrieval Operations
  // ========================================================================

  async retrieve(params: RetrievalParams): Promise<RetrievalResult> {
    return this.request<RetrievalResult>('POST', '/api/v1/retrieval/retrieve', {
      body: {
        query: params.query,
        file_path: params.file_path,
        file_content: params.file_content,
        scope_path: params.scope_path,
        max_results: params.max_results ?? 10,
        token_budget: params.token_budget ?? 2000,
        use_cache: params.use_cache ?? true,
      },
    });
  }

  async checkTriggers(params: TriggerCheckParams): Promise<TriggerCheckResult> {
    return this.request<TriggerCheckResult>('POST', '/api/v1/retrieval/check-triggers', {
      body: params,
    });
  }

  async getHotDecisions(limit = 10): Promise<string[]> {
    const response = await this.request<{ decisions: string[] }>('GET', '/api/v1/retrieval/hot-decisions', {
      params: { limit },
    });
    return response.decisions;
  }

  // ========================================================================
  // Document Generation
  // ========================================================================

  async listDocumentTypes(): Promise<DocumentType[]> {
    return this.request<DocumentType[]>('GET', '/api/v1/docs/types');
  }

  async generateDocument(request: DocumentGenerateRequest): Promise<GeneratedDocument> {
    return this.request<GeneratedDocument>('POST', '/api/v1/docs/generate', {
      body: request,
    });
  }

  // ========================================================================
  // Analytics Operations
  // ========================================================================

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    return this.request<AnalyticsSummary>('GET', '/api/v1/analytics/summary');
  }

  async getHealthDistribution(): Promise<HealthDistribution> {
    return this.request<HealthDistribution>('GET', '/api/v1/analytics/health-distribution');
  }

  async getDecisionStats(decisionId: string): Promise<DecisionStats> {
    return this.request<DecisionStats>('GET', `/api/v1/analytics/decisions/${decisionId}/stats`);
  }

  async trackEvent(
    decisionId: string,
    eventType: string,
    context?: Record<string, unknown>
  ): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>('POST', '/api/v1/analytics/track', {
      body: {
        decision_id: decisionId,
        event_type: eventType,
        context: context ?? {},
      },
    });
  }

  async submitFeedback(
    decisionId: string,
    isHelpful: boolean,
    comment?: string
  ): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>('POST', '/api/v1/analytics/feedback', {
      body: {
        decision_id: decisionId,
        is_helpful: isHelpful,
        comment,
      },
    });
  }

  // ========================================================================
  // Search Operations
  // ========================================================================

  async semanticSearch(
    query: string,
    options?: { domain?: string; limit?: number }
  ): Promise<Array<{ decision_id: string; score: number }>> {
    return this.request<Array<{ decision_id: string; score: number }>>('GET', '/api/v1/search', {
      params: {
        q: query,
        domain: options?.domain,
        limit: options?.limit ?? 10,
      },
    });
  }

  // ========================================================================
  // Comparison Operations
  // ========================================================================

  async compareDecisions(
    decisionId1: string,
    decisionId2: string
  ): Promise<{ differences: Array<{ field: string; left: unknown; right: unknown }> }> {
    return this.request<{ differences: Array<{ field: string; left: unknown; right: unknown }> }>(
      'GET',
      '/api/v1/decisions/compare',
      {
        params: { id1: decisionId1, id2: decisionId2 },
      }
    );
  }

  async getDecisionHistory(decisionId: string): Promise<Array<{ version: number; created_at: string }>> {
    return this.request<Array<{ version: number; created_at: string }>>(
      'GET',
      `/api/v1/decisions/${decisionId}/history`
    );
  }
}
