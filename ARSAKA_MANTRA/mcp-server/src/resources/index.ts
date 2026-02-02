/**
 * MANTRA MCP Resources
 *
 * Resources that can be read by AI assistants.
 * Resources are read-only data sources.
 * Updated to match MANTRA-SCHEMA-001.
 */

import { MantraClient, DOMAIN_LABELS, ASPECT_LABELS } from '../client.js'

// Resource definitions
export const resourceDefinitions = [
  {
    uri: 'mantra://decisions',
    name: 'All Decisions',
    description: 'List of all decisions in the MANTRA system',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://taxonomy',
    name: 'Decision Taxonomy',
    description: 'MANTRA 4x4 decision taxonomy (4 Domains x 4 Aspects)',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://domains',
    name: 'Decisions by Domain',
    description: 'All decisions organized by domain (INT, ARCH, CTL, EVO)',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://decisions/{id}',
    name: 'Single Decision',
    description: 'Get a specific decision by ID or code',
    mimeType: 'application/json'
  }
]

// Resource handlers
type ResourceHandler = (uri: string, client: MantraClient) => Promise<{
  contents: Array<{
    uri: string
    mimeType: string
    text: string
  }>
}>

export const resourceHandlers: Record<string, ResourceHandler> = {
  'mantra://decisions': async (uri, client) => {
    const decisions = await client.listDecisions({ limit: 100 })
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(decisions, null, 2)
      }]
    }
  },

  'mantra://taxonomy': async (uri, _client) => {
    const taxonomy = {
      domains: DOMAIN_LABELS,
      aspects: ASPECT_LABELS,
      matrix: {
        INT: ['A01', 'A02', 'A03', 'A04'],
        ARCH: ['A05', 'A06', 'A07', 'A08'],
        CTL: ['A09', 'A10', 'A11', 'A12'],
        EVO: ['A13', 'A14', 'A15', 'A16']
      }
    }
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(taxonomy, null, 2)
      }]
    }
  },

  'mantra://domains': async (uri, client) => {
    const grouped = await client.getGroupedDecisions()
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(grouped, null, 2)
      }]
    }
  },

  'mantra://decisions/{id}': async (uri, client) => {
    // Extract ID from URI: mantra://decisions/INT-A01-001-v1.0.0 -> INT-A01-001-v1.0.0
    const id = uri.replace('mantra://decisions/', '')
    const decision = await client.getDecision(id)
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(decision, null, 2)
      }]
    }
  }
}
