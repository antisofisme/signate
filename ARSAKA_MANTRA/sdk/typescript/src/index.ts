/**
 * MANTRA SDK for TypeScript
 *
 * TypeScript/JavaScript client for ARSAKA_MANTRA Decision System.
 *
 * Per MANTRA-LAW-006: AI assistants have ZERO authority for:
 * - Approval (must be human)
 * - Creation (must be human authored)
 * - Modification (append-only, human approved)
 *
 * This SDK provides read-only access and proposal capabilities.
 * All proposals require human approval through the dashboard.
 */

export { MantraClient } from './client';

export type {
  // Enums
  DomainId,
  AspectId,
  ValidationStatus,
  HealthStatus,
  // Decision Types
  AuthorshipMetadata,
  DecisionCreate,
  Decision,
  // Validation Types
  ValidationViolation,
  ValidationResult,
  Gate1Result,
  Gate2Result,
  Gate3Result,
  FullValidationResult,
  // Retrieval Types
  RetrievalMatch,
  RetrievalResult,
  TriggerMatch,
  TriggerCheckResult,
  RetrievalParams,
  TriggerCheckParams,
  // Document Types
  DocumentType,
  DocumentGenerateRequest,
  GeneratedDocument,
  // Analytics Types
  AnalyticsSummary,
  HealthDistribution,
  DecisionStats,
  // Client Options
  MantraClientOptions,
  ListDecisionsParams,
} from './types';

export {
  MantraError,
  ValidationError,
  AuthorizationError,
  NotFoundError,
  ConnectionError,
  RateLimitError,
} from './errors';
