/**
 * ATLAS_MANTRA Constants
 * Per MANTRA-LAW-001 §3 - The Four Decision Groups
 */

export const GROUPS = ['INT', 'ARCH', 'CTL', 'EVO'] as const

export const FEATURES: Record<string, readonly string[]> = {
  'INT': ['F-01', 'F-02', 'F-03', 'F-04'],
  'ARCH': ['F-05', 'F-06', 'F-07', 'F-08'],
  'CTL': ['F-09', 'F-10', 'F-11', 'F-12'],
  'EVO': ['F-13', 'F-14', 'F-15', 'F-16'],
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
  'F-01': 'Vision & Outcome',
  'F-02': 'Problem Statement',
  'F-03': 'Scope & Non-Goals',
  'F-04': 'Principles & Values',
  // ARCH: Architecture & Boundaries
  'F-05': 'Domain & Bounded Context',
  'F-06': 'Service & Module Boundary',
  'F-07': 'Data Ownership & Sovereignty',
  'F-08': 'Integration & Contract Model',
  // CTL: Control, Policy & Risk
  'F-09': 'Policy & Rules',
  'F-10': 'Approval & Authority Model',
  'F-11': 'Security & Compliance Posture',
  'F-12': 'Risk & Blast Radius',
  // EVO: Execution & Evolution
  'F-13': 'Decision Lifecycle',
  'F-14': 'Reversibility & Exit Strategy',
  'F-15': 'Environment & Promotion Rules',
  'F-16': 'Anti-Drift & Consistency',
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
