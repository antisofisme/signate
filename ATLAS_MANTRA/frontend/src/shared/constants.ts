/**
 * ATLAS_MANTRA Constants
 * Per MANTRA-LAW-001 §3 - The Four Decision Groups
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * GROUP MAPPING (Abbreviated Code → Law Reference)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * | Code | Law Reference | Full Name                  | Scope          |
 * |------|---------------|----------------------------|----------------|
 * | INT  | GROUP-1, §3.2 | Intent & Direction         | WHY / WHAT     |
 * | ARCH | GROUP-2, §3.3 | Architecture & Boundaries  | HOW / WHERE    |
 * | CTL  | GROUP-3, §3.4 | Control, Policy & Risk     | CAN / MUST NOT |
 * | EVO  | GROUP-4, §3.5 | Execution & Evolution      | CHANGE SAFELY  |
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * FEATURE MAPPING (4 Features per Group)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * GROUP-1 (INT):  F01, F02, F03, F04
 * GROUP-2 (ARCH): F05, F06, F07, F08
 * GROUP-3 (CTL):  F09, F10, F11, F12
 * GROUP-4 (EVO):  F13, F14, F15, F16
 *
 * Total: 4 Groups × 4 Features = 16 Decision Cells
 */

export const GROUPS = ['INT', 'ARCH', 'CTL', 'EVO'] as const

/**
 * Group to Law Reference Mapping
 * Per MANTRA-LAW-001
 */
export const GROUP_LAW_REFERENCES: Record<string, string> = {
  'INT': 'GROUP-1, §3.2',
  'ARCH': 'GROUP-2, §3.3',
  'CTL': 'GROUP-3, §3.4',
  'EVO': 'GROUP-4, §3.5',
}

export const FEATURES: Record<string, readonly string[]> = {
  'INT': ['F01', 'F02', 'F03', 'F04'],
  'ARCH': ['F05', 'F06', 'F07', 'F08'],
  'CTL': ['F09', 'F10', 'F11', 'F12'],
  'EVO': ['F13', 'F14', 'F15', 'F16'],
} as const

/**
 * Group Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const GROUP_LABELS: Record<string, string> = {
  'INT': 'Intent & Direction',
  'ARCH': 'Architecture & Boundaries',
  'CTL': 'Control, Policy & Risk',
  'EVO': 'Execution & Evolution',
}

/**
 * Group Colors (hex)
 * For graph and matrix visualizations
 */
export const GROUP_COLORS: Record<string, string> = {
  'INT': '#2563EB',   // Blue - Intent & Direction
  'ARCH': '#7C3AED',  // Purple - Architecture & Boundaries
  'CTL': '#DC2626',   // Red - Control, Policy & Risk
  'EVO': '#059669',   // Green - Execution & Evolution
}

/**
 * Group Scopes
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const GROUP_SCOPES: Record<string, string> = {
  'INT': 'WHY / WHAT',
  'ARCH': 'HOW / WHERE',
  'CTL': 'CAN / MUST NOT',
  'EVO': 'CHANGE SAFELY',
}

/**
 * Feature Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const FEATURE_LABELS: Record<string, string> = {
  // INT: Intent & Direction
  'F01': 'Vision & Outcome',
  'F02': 'Problem Statement',
  'F03': 'Scope & Non-Goals',
  'F04': 'Principles & Values',
  // ARCH: Architecture & Boundaries
  'F05': 'Domain & Bounded Context',
  'F06': 'Service & Module Boundary',
  'F07': 'Data Ownership & Sovereignty',
  'F08': 'Integration & Contract Model',
  // CTL: Control, Policy & Risk
  'F09': 'Policy & Rules',
  'F10': 'Approval & Authority Model',
  'F11': 'Security & Compliance Posture',
  'F12': 'Risk & Blast Radius',
  // EVO: Execution & Evolution
  'F13': 'Decision Lifecycle',
  'F14': 'Reversibility & Exit Strategy',
  'F15': 'Environment & Promotion Rules',
  'F16': 'Anti-Drift & Consistency',
}

/**
 * Get feature label with fallback
 */
export function getFeatureLabel(featureId: string): string {
  return FEATURE_LABELS[featureId] || featureId
}

/**
 * Get group label with fallback
 */
export function getGroupLabel(groupId: string): string {
  return GROUP_LABELS[groupId] || groupId
}

/**
 * Get group scope with fallback
 */
export function getGroupScope(groupId: string): string {
  return GROUP_SCOPES[groupId] || ''
}

/**
 * Area Tags (Technical Areas)
 * For categorizing decisions by affected technical area
 *
 * NOTE: ARCH here refers to "Architecture/Design Pattern" technical area,
 * NOT to be confused with ARCH decision group (GROUP-2: Architecture & Boundaries)
 *
 * 12 Technical Areas:
 * - Core Development: FE, BE, DB, API
 * - Infrastructure & Operations: INFRA, CICD, DEVOPS
 * - Quality & Security: SECURITY, TESTING, PERF
 * - Architecture & Data: DATA, ARCH
 */
export const AREA_TAGS = [
  'FE', 'BE', 'DB', 'API',           // Core Development
  'INFRA', 'CICD', 'DEVOPS',         // Infrastructure & Operations
  'SECURITY', 'TESTING', 'PERF',     // Quality & Security
  'DATA', 'ARCH',                     // Architecture & Data
] as const

export const TAG_LABELS: Record<string, string> = {
  // Core Development
  'FE': 'Frontend',
  'BE': 'Backend',
  'DB': 'Database',
  'API': 'API Design',
  // Infrastructure & Operations
  'INFRA': 'Infrastructure',
  'CICD': 'CI/CD',
  'DEVOPS': 'DevOps',
  // Quality & Security
  'SECURITY': 'Security',
  'TESTING': 'Testing',
  'PERF': 'Performance',
  // Architecture & Data
  'DATA': 'Data Engineering',
  'ARCH': 'Architecture',
  // Fallback
  'OTHER': 'Other',
}

export const TAG_COLORS: Record<string, string> = {
  // Core Development
  'FE': 'bg-blue-100 text-blue-700',
  'BE': 'bg-green-100 text-green-700',
  'DB': 'bg-cyan-100 text-cyan-700',
  'API': 'bg-teal-100 text-teal-700',
  // Infrastructure & Operations
  'INFRA': 'bg-purple-100 text-purple-700',
  'CICD': 'bg-orange-100 text-orange-700',
  'DEVOPS': 'bg-amber-100 text-amber-700',
  // Quality & Security
  'SECURITY': 'bg-red-100 text-red-700',
  'TESTING': 'bg-pink-100 text-pink-700',
  'PERF': 'bg-yellow-100 text-yellow-700',
  // Architecture & Data
  'DATA': 'bg-indigo-100 text-indigo-700',
  'ARCH': 'bg-violet-100 text-violet-700',
  // Fallback
  'OTHER': 'bg-gray-100 text-gray-500',
}

/**
 * Relation Types
 * Per Decision Graph Model
 */
export const RELATION_TYPES = ['depends_on', 'conflicts_with', 'informed_by'] as const

export const RELATION_LABELS: Record<string, string> = {
  'depends_on': 'Depends On',
  'conflicts_with': 'Conflicts With',
  'informed_by': 'Informed By',
  'supersedes': 'Supersedes',  // Special case - stored in separate field
}

export const RELATION_COLORS: Record<string, string> = {
  'depends_on': '#2563EB',     // Blue
  'conflicts_with': '#DC2626', // Red
  'informed_by': '#059669',    // Green
  'supersedes': '#F59E0B',     // Amber
}

export const RELATION_EDGE_STYLES: Record<string, { stroke: string; strokeDasharray?: string }> = {
  'depends_on': { stroke: '#2563EB' },
  'conflicts_with': { stroke: '#DC2626', strokeDasharray: '5,5' },
  'informed_by': { stroke: '#059669', strokeDasharray: '3,3' },
  'supersedes': { stroke: '#F59E0B' },
}

/**
 * Common Tech Stack Items
 * Suggestions for tech_stack field
 * Matches keywords in metadata_inference.py
 */
export const COMMON_TECH_STACK = [
  // Languages
  'Python', 'TypeScript', 'JavaScript',
  // Frontend Frameworks
  'React', 'Vue', 'Angular', 'Svelte', 'Next.js', 'Vite',
  // Frontend Libraries
  'Tailwind CSS', 'Zustand', 'TanStack Query',
  // Backend Frameworks
  'FastAPI', 'Django', 'Flask', 'Express', 'NestJS',
  // Backend Libraries
  'Pydantic', 'SQLAlchemy',
  // Databases
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'TimescaleDB',
  'Elasticsearch', 'Qdrant',
  // Infrastructure
  'Docker', 'Kubernetes', 'Nomad', 'Consul', 'Terraform',
  // Cloud Providers
  'AWS', 'GCP', 'Azure',
  // Web Servers / Proxy
  'Nginx', 'Traefik',
  // Storage
  'S3', 'MinIO',
  // Message Queues
  'RabbitMQ', 'Kafka', 'Celery',
  // API & Protocols
  'GraphQL', 'REST', 'gRPC', 'WebSocket', 'MCP',
  // CI/CD
  'GitHub Actions', 'GitLab CI', 'Jenkins', 'ArgoCD',
  // Data & AI
  'Pandas', 'Airflow', 'LangChain', 'OpenAI', 'Anthropic',
] as const

// =============================================================================
// Validation Status Constants
// =============================================================================

export const VALIDATION_STATUS = ['READY', 'INVALID', 'PENDING_ARBITRATION', 'PENDING_APPROVAL'] as const

export const VALIDATION_STATUS_COLORS: Record<string, string> = {
  'READY': 'bg-green-100 text-green-700',
  'INVALID': 'bg-red-100 text-red-700',
  'PENDING_ARBITRATION': 'bg-amber-100 text-amber-700',
  'PENDING_APPROVAL': 'bg-blue-100 text-blue-700',
}

export const VALIDATION_STATUS_LABELS: Record<string, string> = {
  'READY': 'Ready to Store',
  'INVALID': 'Invalid',
  'PENDING_ARBITRATION': 'Needs Arbitration',
  'PENDING_APPROVAL': 'Awaiting Approval',
}

// =============================================================================
// AI Arbitration Constants
// =============================================================================

export const ARBITRATION_MODES = ['SERVER', 'DELEGATED', 'SKIP'] as const

export const ARBITRATION_MODE_LABELS: Record<string, string> = {
  'SERVER': 'Server AI',
  'DELEGATED': 'Delegated',
  'SKIP': 'Skip AI',
}

export const ARBITRATION_MODE_DESCRIPTIONS: Record<string, string> = {
  'SERVER': 'MANTRA server AI evaluates borderline cases (costs $ per call)',
  'DELEGATED': 'You (the user) review and decide on borderline cases',
  'SKIP': 'No AI arbitration, accept validation uncertainty',
}

export const ARBITRATION_TYPES = ['QUALITY', 'DUPLICATE', 'CONFLICT'] as const

export const ARBITRATION_TYPE_LABELS: Record<string, string> = {
  'QUALITY': 'Quality Assessment',
  'DUPLICATE': 'Duplicate Classification',
  'CONFLICT': 'Conflict Resolution',
}

export const ARBITER_VERDICTS = {
  // Quality verdicts
  APPROVE: 'Approve decision as-is',
  REJECT: 'Reject decision',
  NEEDS_IMPROVEMENT: 'Requires improvements before approval',
  // Duplicate verdicts
  DUPLICATE: 'This is a duplicate (block)',
  EVOLUTION: 'This is an evolution (should supersede)',
  DIFFERENT: 'Different enough to coexist',
  // Conflict verdicts
  BLOCKING: 'Real conflict, cannot coexist',
  WARNING: 'Potential tension, proceed with caution',
  NOT_CONFLICT: 'False positive, no conflict',
}

// =============================================================================
// AI Provider Constants
// =============================================================================

export const AI_PROVIDERS = ['anthropic', 'openai', 'deepseek', 'groq', 'xai', 'openrouter'] as const

export const AI_PROVIDER_LABELS: Record<string, string> = {
  'anthropic': 'Anthropic (Claude)',
  'openai': 'OpenAI (GPT)',
  'deepseek': 'DeepSeek',
  'groq': 'Groq (Llama)',
  'xai': 'xAI (Grok)',
  'openrouter': 'OpenRouter',
}

export const AI_PROVIDER_COLORS: Record<string, string> = {
  'anthropic': 'bg-orange-100 text-orange-700',
  'openai': 'bg-green-100 text-green-700',
  'deepseek': 'bg-blue-100 text-blue-700',
  'groq': 'bg-purple-100 text-purple-700',
  'xai': 'bg-gray-100 text-gray-700',
  'openrouter': 'bg-indigo-100 text-indigo-700',
}

// =============================================================================
// Quality Score Constants
// =============================================================================

export const QUALITY_THRESHOLDS = {
  EXCELLENT: 80,
  GOOD: 60,
  BORDERLINE_MIN: 50,
  BORDERLINE_MAX: 80,
  FAIL: 50,
}

export const QUALITY_DIMENSION_LABELS: Record<string, string> = {
  'Statement': 'Statement Quality',
  'Rationale': 'Rationale Quality',
  'Constraints': 'Constraints Quality',
  'Metadata': 'Metadata Completeness',
  'Advanced': 'Advanced Metrics (Coherence, Readability)',
}

// =============================================================================
// Impact/Risk Constants
// =============================================================================

export const RISK_LEVELS = ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'] as const

export const RISK_LEVEL_COLORS: Record<string, string> = {
  'MINIMAL': 'bg-green-100 text-green-700',
  'LOW': 'bg-green-100 text-green-700',
  'MODERATE': 'bg-amber-100 text-amber-700',
  'HIGH': 'bg-orange-100 text-orange-700',
  'CRITICAL': 'bg-red-100 text-red-700',
}

export const BLAST_RADIUS_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const

export const SCOPE_OPTIONS = ['ORGANIZATION', 'DOMAIN', 'APPLICATION'] as const
