/**
 * MANTRA MCP Resources
 *
 * Resources that can be read by AI assistants.
 * Resources are read-only data sources.
 */

import { MantraClient } from '../client.js'

// Resource definitions
export const resourceDefinitions = [
  {
    uri: 'mantra://decisions',
    name: 'All Decisions',
    description: 'List of all decisions in the MANTRA system',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://decisions/accepted',
    name: 'Accepted Decisions',
    description: 'List of all accepted (active) decisions',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://principles',
    name: 'Layer 0 Principles',
    description: 'Immutable constitutional principles (Layer 0)',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://groups',
    name: 'Decision Groups',
    description: 'All decisions organized by group',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://decisions/{id}',
    name: 'Single Decision',
    description: 'Get a specific decision by ID or code',
    mimeType: 'application/json'
  },
  {
    uri: 'mantra://audit',
    name: 'Audit Log',
    description: 'Recent audit log entries',
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

  'mantra://decisions/accepted': async (uri, client) => {
    const decisions = await client.listDecisions({ status: 'accepted', limit: 100 })
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(decisions, null, 2)
      }]
    }
  },

  'mantra://principles': async (uri, client) => {
    const decisions = await client.listDecisions({ layer: 0, status: 'accepted' })
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(decisions, null, 2)
      }]
    }
  },

  'mantra://groups': async (uri, client) => {
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
    // Extract ID from URI: mantra://decisions/ARCH-001 -> ARCH-001
    const id = uri.replace('mantra://decisions/', '')
    const decision = await client.getDecision(id)
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(decision, null, 2)
      }]
    }
  },

  'mantra://audit': async (uri, client) => {
    const audit = await client.getAuditLog({ limit: 50 })
    return {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(audit, null, 2)
      }]
    }
  }
}
