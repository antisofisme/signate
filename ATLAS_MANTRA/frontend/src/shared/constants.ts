/**
 * ATLAS_MANTRA Constants
 * Per MANTRA-LAW-001 §3 - The Four Decision Domains
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * DOMAIN MAPPING (Abbreviated Code → Law Reference)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * | Code | Law Reference   | Full Name                  | Scope          |
 * |------|-----------------|----------------------------|----------------|
 * | INT  | DOMAIN-1, §3.2  | Intent & Direction         | WHY / WHAT     |
 * | ARCH | DOMAIN-2, §3.3  | Architecture & Boundaries  | HOW / WHERE    |
 * | CTL  | DOMAIN-3, §3.4  | Control, Policy & Risk     | CAN / MUST NOT |
 * | EVO  | DOMAIN-4, §3.5  | Execution & Evolution      | CHANGE SAFELY  |
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ASPECT MAPPING (4 Aspects per Domain)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * DOMAIN-1 (INT):  A01, A02, A03, A04
 * DOMAIN-2 (ARCH): A05, A06, A07, A08
 * DOMAIN-3 (CTL):  A09, A10, A11, A12
 * DOMAIN-4 (EVO):  A13, A14, A15, A16
 *
 * Total: 4 Domains × 4 Aspects = 16 Decision Cells
 */

export const DOMAINS = ['INT', 'ARCH', 'CTL', 'EVO'] as const

/**
 * Domain to Law Reference Mapping
 * Per MANTRA-LAW-001
 */
export const DOMAIN_LAW_REFERENCES: Record<string, string> = {
  'INT': 'DOMAIN-1, §3.2',
  'ARCH': 'DOMAIN-2, §3.3',
  'CTL': 'DOMAIN-3, §3.4',
  'EVO': 'DOMAIN-4, §3.5',
}

export const ASPECTS: Record<string, readonly string[]> = {
  'INT': ['A01', 'A02', 'A03', 'A04'],
  'ARCH': ['A05', 'A06', 'A07', 'A08'],
  'CTL': ['A09', 'A10', 'A11', 'A12'],
  'EVO': ['A13', 'A14', 'A15', 'A16'],
} as const

/**
 * Domain Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const DOMAIN_LABELS: Record<string, string> = {
  'INT': 'Intent & Direction',
  'ARCH': 'Architecture & Boundaries',
  'CTL': 'Control, Policy & Risk',
  'EVO': 'Execution & Evolution',
}

/**
 * Domain Colors (hex)
 * For graph and matrix visualizations
 */
export const DOMAIN_COLORS: Record<string, string> = {
  'INT': '#2563EB',   // Blue - Intent & Direction
  'ARCH': '#7C3AED',  // Purple - Architecture & Boundaries
  'CTL': '#DC2626',   // Red - Control, Policy & Risk
  'EVO': '#059669',   // Green - Execution & Evolution
}

/**
 * Domain Tailwind Colors
 * For consistent styling across pages (bg, text, border classes)
 * Matches DOMAIN_COLORS hex values
 */
export const DOMAIN_TAILWIND_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'INT': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  'ARCH': { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  'CTL': { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  'EVO': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

/**
 * Domain Tailwind Border+Bg Combined (for simpler usage)
 */
export const DOMAIN_TAILWIND_COMBINED: Record<string, string> = {
  'INT': 'border-blue-200 bg-blue-50',
  'ARCH': 'border-purple-200 bg-purple-50',
  'CTL': 'border-red-200 bg-red-50',
  'EVO': 'border-green-200 bg-green-50',
}

/**
 * Domain Scopes
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const DOMAIN_SCOPES: Record<string, string> = {
  'INT': 'WHY / WHAT',
  'ARCH': 'HOW / WHERE',
  'CTL': 'CAN / MUST NOT',
  'EVO': 'CHANGE SAFELY',
}

/**
 * Aspect Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const ASPECT_LABELS: Record<string, string> = {
  // INT: Intent & Direction
  'A01': 'Vision & Outcome',
  'A02': 'Problem Statement',
  'A03': 'Scope & Non-Goals',
  'A04': 'Principles & Values',
  // ARCH: Architecture & Boundaries
  'A05': 'Domain & Bounded Context',
  'A06': 'Service & Module Boundary',
  'A07': 'Data Ownership & Sovereignty',
  'A08': 'Integration & Contract Model',
  // CTL: Control, Policy & Risk
  'A09': 'Policy & Rules',
  'A10': 'Approval & Authority Model',
  'A11': 'Security & Compliance Posture',
  'A12': 'Risk & Blast Radius',
  // EVO: Execution & Evolution
  'A13': 'Decision Lifecycle',
  'A14': 'Reversibility & Exit Strategy',
  'A15': 'Environment & Promotion Rules',
  'A16': 'Anti-Drift & Consistency',
}

/**
 * Aspect Icons (emoji-based for simplicity)
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const ASPECT_ICONS: Record<string, string> = {
  // INT: Intent & Direction (Blue domain)
  'A01': '🎯',  // Vision & Outcome - Target
  'A02': '❓',  // Problem Statement - Question
  'A03': '📐',  // Scope & Non-Goals - Ruler/Boundary
  'A04': '💎',  // Principles & Values - Gem/Value
  // ARCH: Architecture & Boundaries (Green domain)
  'A05': '🏗️',  // Domain & Bounded Context - Building
  'A06': '📦',  // Service & Module Boundary - Package
  'A07': '🗄️',  // Data Ownership & Sovereignty - Cabinet/Storage
  'A08': '🔗',  // Integration & Contract Model - Link
  // CTL: Control, Policy & Risk (Orange domain)
  'A09': '📋',  // Policy & Rules - Clipboard
  'A10': '👥',  // Approval & Authority Model - People
  'A11': '🛡️',  // Security & Compliance Posture - Shield
  'A12': '⚠️',  // Risk & Blast Radius - Warning
  // EVO: Execution & Evolution (Purple domain)
  'A13': '🔄',  // Decision Lifecycle - Cycle
  'A14': '↩️',  // Reversibility & Exit Strategy - Return
  'A15': '🚀',  // Environment & Promotion Rules - Rocket
  'A16': '📏',  // Anti-Drift & Consistency - Ruler
}

/**
 * Get aspect icon with fallback
 */
export function getAspectIcon(aspectId: string): string {
  return ASPECT_ICONS[aspectId] || '📄'
}

/**
 * Get aspect label with fallback
 */
export function getAspectLabel(aspectId: string): string {
  return ASPECT_LABELS[aspectId] || aspectId
}

/**
 * Get domain label with fallback
 */
export function getDomainLabel(domainId: string): string {
  return DOMAIN_LABELS[domainId] || domainId
}

/**
 * Get domain scope with fallback
 */
export function getDomainScope(domainId: string): string {
  return DOMAIN_SCOPES[domainId] || ''
}

/**
 * Area Tags (Technical Areas)
 * For categorizing decisions by affected technical area
 *
 * NOTE: ARCH here refers to "Architecture/Design Pattern" technical area,
 * NOT to be confused with ARCH decision domain (DOMAIN-2: Architecture & Boundaries)
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

// =============================================================================
// Backwards-Compatible Aliases (DEPRECATED - use DOMAINS/ASPECTS instead)
// These aliases maintain compatibility while transitioning terminology
// =============================================================================

/** @deprecated Use DOMAINS instead */
export const GROUPS = DOMAINS

/** @deprecated Use ASPECTS instead */
export const FEATURES = ASPECTS

/** @deprecated Use DOMAIN_LABELS instead */
export const GROUP_LABELS = DOMAIN_LABELS

/** @deprecated Use DOMAIN_COLORS instead */
export const GROUP_COLORS = DOMAIN_COLORS

/** @deprecated Use DOMAIN_SCOPES instead */
export const GROUP_SCOPES = DOMAIN_SCOPES

/** @deprecated Use ASPECT_LABELS instead */
export const FEATURE_LABELS = ASPECT_LABELS

/** @deprecated Use getDomainLabel instead */
export const getGroupLabel = getDomainLabel

/** @deprecated Use getAspectLabel instead */
export const getFeatureLabel = getAspectLabel
