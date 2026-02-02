/**
 * Decision Versioning Utilities
 * Per MANTRA-LAW-001 §6.2 - Interpretation is CONSUMER's responsibility
 *
 * These utilities compute decision "currency" based on the supersedes chain.
 * A decision is "current" if no other decision supersedes it.
 */

import { Decision } from './api'

/**
 * Build a Set of all superseded decision IDs
 * A decision is superseded if any other decision points to it via `supersedes`
 */
export function buildSupersededSet(decisions: Decision[]): Set<string> {
  const supersededIds = new Set<string>()
  for (const d of decisions) {
    if (d.supersedes) {
      supersededIds.add(d.supersedes)
    }
  }
  return supersededIds
}

/**
 * Check if a single decision is current (not superseded by any other decision)
 *
 * @param decision - The decision to check
 * @param allDecisions - All decisions (needed to find if anything supersedes this one)
 * @returns true if the decision is current (not superseded)
 */
export function isCurrent(decision: Decision, allDecisions: Decision[]): boolean {
  return !allDecisions.some(d => d.supersedes === decision.decision_id)
}

/**
 * Check if a decision is superseded (historical)
 */
export function isSuperseded(decision: Decision, allDecisions: Decision[]): boolean {
  return !isCurrent(decision, allDecisions)
}

/**
 * Get all current decisions (not superseded by anything)
 */
export function getCurrentDecisions(allDecisions: Decision[]): Decision[] {
  const supersededSet = buildSupersededSet(allDecisions)
  return allDecisions.filter(d => !supersededSet.has(d.decision_id))
}

/**
 * Get all superseded (historical) decisions
 */
export function getSupersededDecisions(allDecisions: Decision[]): Decision[] {
  const supersededSet = buildSupersededSet(allDecisions)
  return allDecisions.filter(d => supersededSet.has(d.decision_id))
}

/**
 * Get counts for current and superseded decisions
 */
export function getDecisionCounts(allDecisions: Decision[]): {
  total: number
  current: number
  superseded: number
} {
  const supersededSet = buildSupersededSet(allDecisions)
  const current = allDecisions.filter(d => !supersededSet.has(d.decision_id)).length
  return {
    total: allDecisions.length,
    current,
    superseded: allDecisions.length - current,
  }
}

/**
 * Get counts per domain for current decisions only
 */
export function getCurrentCountsByDomain(allDecisions: Decision[]): Record<string, number> {
  const currentDecisions = getCurrentDecisions(allDecisions)
  return currentDecisions.reduce((acc, d) => {
    // Support both new (domain_id) and old (group_id) field names
    const domainId = d.domain_id || (d as any).group_id
    acc[domainId] = (acc[domainId] || 0) + 1
    return acc
  }, {} as Record<string, number>)
}

/**
 * @deprecated Use getCurrentCountsByDomain instead
 */
export function getCurrentCountsByGroup(allDecisions: Decision[]): Record<string, number> {
  return getCurrentCountsByDomain(allDecisions)
}

/**
 * Find the superseding decision for a given decision
 * Returns null if the decision is current
 */
export function findSupersedingDecision(
  decision: Decision,
  allDecisions: Decision[]
): Decision | null {
  return allDecisions.find(d => d.supersedes === decision.decision_id) || null
}

/**
 * Annotated decision with computed currency information
 */
export interface AnnotatedDecision extends Decision {
  _isCurrent: boolean
  _supersededBy: string | null // decision_id of superseding decision
  _supersededByCode: string | null // decision_code of superseding decision
}

/**
 * Annotate decisions with currency information
 * Useful for list views
 */
export function annotateDecisions(decisions: Decision[]): AnnotatedDecision[] {
  // Build map: superseded_id -> superseding decision
  const supersededMap = new Map<string, Decision>()
  for (const d of decisions) {
    if (d.supersedes) {
      supersededMap.set(d.supersedes, d)
    }
  }

  return decisions.map(d => {
    const supersedingDecision = supersededMap.get(d.decision_id)
    return {
      ...d,
      _isCurrent: !supersededMap.has(d.decision_id),
      _supersededBy: supersedingDecision?.decision_id || null,
      _supersededByCode: supersedingDecision?.decision_code || null,
    }
  })
}

/**
 * Get the latest version in a decision chain
 * Follows the supersedes chain from any decision to find the current version
 */
export function getLatestInChain(
  decision: Decision,
  allDecisions: Decision[]
): Decision {
  let current = decision
  let next = findSupersedingDecision(current, allDecisions)

  while (next) {
    current = next
    next = findSupersedingDecision(current, allDecisions)
  }

  return current
}
