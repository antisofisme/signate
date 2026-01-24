/**
 * ATLAS_MANTRA Constants
 * Per MANTRA-LAW-001 §3 - The Four Decision Groups
 */

export const GROUPS = ['GROUP-1', 'GROUP-2', 'GROUP-3', 'GROUP-4'] as const

export const FEATURES: Record<string, readonly string[]> = {
  'GROUP-1': ['F-01', 'F-02', 'F-03', 'F-04'],
  'GROUP-2': ['F-05', 'F-06', 'F-07', 'F-08'],
  'GROUP-3': ['F-09', 'F-10', 'F-11', 'F-12'],
  'GROUP-4': ['F-13', 'F-14', 'F-15', 'F-16'],
} as const

/**
 * Group Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const GROUP_LABELS: Record<string, string> = {
  'GROUP-1': 'Intent & Direction',
  'GROUP-2': 'Architecture & Boundaries',
  'GROUP-3': 'Control, Policy & Risk',
  'GROUP-4': 'Execution & Evolution',
}

/**
 * Group Scopes
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const GROUP_SCOPES: Record<string, string> = {
  'GROUP-1': 'WHY / WHAT',
  'GROUP-2': 'HOW / WHERE',
  'GROUP-3': 'CAN / MUST NOT',
  'GROUP-4': 'CHANGE SAFELY',
}

/**
 * Feature Labels
 * Per MANTRA-LAW-001 §3.2-§3.5
 */
export const FEATURE_LABELS: Record<string, string> = {
  // GROUP-1: Intent & Direction
  'F-01': 'Vision & Outcome',
  'F-02': 'Problem Statement',
  'F-03': 'Scope & Non-Goals',
  'F-04': 'Principles & Values',
  // GROUP-2: Architecture & Boundaries
  'F-05': 'Domain & Bounded Context',
  'F-06': 'Service & Module Boundary',
  'F-07': 'Data Ownership & Sovereignty',
  'F-08': 'Integration & Contract Model',
  // GROUP-3: Control, Policy & Risk
  'F-09': 'Policy & Rules',
  'F-10': 'Approval & Authority Model',
  'F-11': 'Security & Compliance Posture',
  'F-12': 'Risk & Blast Radius',
  // GROUP-4: Execution & Evolution
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
