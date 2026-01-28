/**
 * MANTRA MCP Tools
 *
 * Tools available to AI assistants for interacting with MANTRA.
 */

import { z } from 'zod'
import { MantraClient } from '../client.js'

// Tool definitions for MCP
export const toolDefinitions = [
  {
    name: 'mantra_search_decisions',
    description: 'Search for decisions in the MANTRA constitutional law system. Use this to find relevant precedents, principles, or guidelines before making architectural or design decisions.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        query: {
          type: 'string',
          description: 'Search query (keywords, topics, or decision codes)'
        },
        group: {
          type: 'string',
          description: 'Filter by decision group (e.g., ARCH, SEC, PERF, API, DB)',
          enum: ['ARCH', 'SEC', 'PERF', 'API', 'DB', 'UI', 'INFRA', 'PROC']
        },
        status: {
          type: 'string',
          description: 'Filter by status',
          enum: ['draft', 'proposed', 'accepted', 'rejected', 'superseded']
        },
        layer: {
          type: 'number',
          description: 'Filter by layer (0=principles, 1=decisions, 2=implementations)',
          enum: [0, 1, 2]
        },
        limit: {
          type: 'number',
          description: 'Maximum results to return (default: 10)'
        }
      },
      required: ['query']
    }
  },
  {
    name: 'mantra_get_decision',
    description: 'Get full details of a specific decision by ID or code.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        id: {
          type: 'string',
          description: 'Decision ID or code (e.g., ARCH-001)'
        }
      },
      required: ['id']
    }
  },
  {
    name: 'mantra_get_principles',
    description: 'Get Layer 0 principles (immutable constitutional laws) for a specific domain. These are the foundational rules that all decisions must follow.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        domain: {
          type: 'string',
          description: 'Domain to get principles for',
          enum: ['security', 'performance', 'architecture', 'api', 'database', 'ui', 'infrastructure', 'process']
        }
      },
      required: ['domain']
    }
  },
  {
    name: 'mantra_propose_decision',
    description: 'Propose a new decision to be added to the MANTRA system. The proposal will be reviewed before acceptance.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        title: {
          type: 'string',
          description: 'Short title for the decision'
        },
        group: {
          type: 'string',
          description: 'Decision group',
          enum: ['ARCH', 'SEC', 'PERF', 'API', 'DB', 'UI', 'INFRA', 'PROC']
        },
        content: {
          type: 'string',
          description: 'Full description of the decision'
        },
        rationale: {
          type: 'string',
          description: 'Reasoning behind the decision'
        },
        alternatives: {
          type: 'array',
          items: { type: 'string' },
          description: 'Alternatives that were considered'
        },
        implications: {
          type: 'array',
          items: { type: 'string' },
          description: 'Consequences and implications of this decision'
        },
        references: {
          type: 'array',
          items: { type: 'string' },
          description: 'Related decision codes (e.g., ["ARCH-001", "SEC-002"])'
        }
      },
      required: ['title', 'group', 'content']
    }
  },
  {
    name: 'mantra_validate_decision',
    description: 'Validate a proposed decision against existing principles and rules. Use this before proposing to check compliance.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        title: {
          type: 'string',
          description: 'Decision title'
        },
        group: {
          type: 'string',
          description: 'Decision group'
        },
        content: {
          type: 'string',
          description: 'Decision content to validate'
        }
      },
      required: ['content']
    }
  },
  {
    name: 'mantra_get_hints',
    description: 'Get AI-powered hints and suggestions based on context. Useful when planning implementations to get relevant guidelines.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        context: {
          type: 'string',
          description: 'Description of what you are planning to implement or decide'
        }
      },
      required: ['context']
    }
  },
  {
    name: 'mantra_compare_decisions',
    description: 'Compare two decisions to understand their differences and similarities.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        decision1: {
          type: 'string',
          description: 'First decision ID or code'
        },
        decision2: {
          type: 'string',
          description: 'Second decision ID or code'
        }
      },
      required: ['decision1', 'decision2']
    }
  },
  {
    name: 'mantra_get_grouped',
    description: 'Get all decisions organized by group. Useful for getting an overview of decisions in each category.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  },
  {
    name: 'mantra_semantic_search',
    description: 'Search for semantically similar decisions using AI embeddings. Returns decisions ranked by semantic relevance to your query. More accurate than keyword search for finding related concepts.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        query: {
          type: 'string',
          description: 'Natural language search query describing what you are looking for'
        },
        limit: {
          type: 'number',
          description: 'Maximum results to return (default: 10, max: 100)'
        },
        min_score: {
          type: 'number',
          description: 'Minimum similarity score 0.0-1.0 (default: 0.5)'
        },
        domain_id: {
          type: 'string',
          description: 'Filter by decision domain',
          enum: ['INT', 'ARCH', 'CTL', 'EVO']
        },
        aspect_id: {
          type: 'string',
          description: 'Filter by aspect (A01-A16)'
        }
      },
      required: ['query']
    }
  },
  {
    name: 'mantra_check_alignment',
    description: 'Check if a proposed decision aligns with existing decisions. Returns potential conflicts, aligned decisions, and recommendations. ALWAYS use this before proposing a new decision.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        statement: {
          type: 'string',
          description: 'The proposed decision statement to check'
        },
        rationale: {
          type: 'string',
          description: 'The rationale for the proposed decision'
        },
        domain_id: {
          type: 'string',
          description: 'Scope the check to a specific domain',
          enum: ['INT', 'ARCH', 'CTL', 'EVO']
        }
      },
      required: ['statement']
    }
  },
  {
    name: 'mantra_search_stats',
    description: 'Get statistics about the semantic search index. Shows collection size, embedding model info, and cache status.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  }
]

// Tool handlers
type ToolHandler = (args: Record<string, unknown>, client: MantraClient) => Promise<{
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

export const toolHandlers: Record<string, ToolHandler> = {
  mantra_search_decisions: async (args, client) => {
    try {
      const decisions = await client.listDecisions({
        search: args.query as string,
        group: args.group as string | undefined,
        status: args.status as string | undefined,
        layer: args.layer as number | undefined,
        limit: (args.limit as number) || 10
      })

      if (decisions.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `No decisions found for query: "${args.query}"`
          }]
        }
      }

      const formatted = decisions.map(d =>
        `**${d.code}** - ${d.title}\n` +
        `  Status: ${d.status} | Layer: ${d.layer} | Group: ${d.group}\n` +
        `  ${d.content.substring(0, 200)}${d.content.length > 200 ? '...' : ''}`
      ).join('\n\n')

      return {
        content: [{
          type: 'text',
          text: `Found ${decisions.length} decision(s):\n\n${formatted}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error searching decisions: ${error}` }],
        isError: true
      }
    }
  },

  mantra_get_decision: async (args, client) => {
    try {
      const decision = await client.getDecision(args.id as string)

      const text = `
# ${decision.code}: ${decision.title}

**Status:** ${decision.status}
**Layer:** ${decision.layer}
**Group:** ${decision.group}
**Created:** ${decision.created_at}
${decision.approved_at ? `**Approved:** ${decision.approved_at} by ${decision.approved_by}` : ''}

## Content
${decision.content}

${decision.rationale ? `## Rationale\n${decision.rationale}` : ''}

${decision.alternatives?.length ? `## Alternatives Considered\n${decision.alternatives.map(a => `- ${a}`).join('\n')}` : ''}

${decision.implications?.length ? `## Implications\n${decision.implications.map(i => `- ${i}`).join('\n')}` : ''}

${decision.references?.length ? `## References\n${decision.references.map(r => `- ${r}`).join('\n')}` : ''}
`.trim()

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting decision: ${error}` }],
        isError: true
      }
    }
  },

  mantra_get_principles: async (args, client) => {
    try {
      const domainToGroup: Record<string, string> = {
        security: 'SEC',
        performance: 'PERF',
        architecture: 'ARCH',
        api: 'API',
        database: 'DB',
        ui: 'UI',
        infrastructure: 'INFRA',
        process: 'PROC'
      }

      const group = domainToGroup[args.domain as string]
      const decisions = await client.listDecisions({
        group,
        layer: 0, // Layer 0 = principles
        status: 'accepted'
      })

      if (decisions.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `No Layer 0 principles found for domain: ${args.domain}`
          }]
        }
      }

      const formatted = decisions.map(d =>
        `## ${d.code}: ${d.title}\n${d.content}`
      ).join('\n\n---\n\n')

      return {
        content: [{
          type: 'text',
          text: `# ${(args.domain as string).toUpperCase()} Principles (Layer 0 - Immutable)\n\n${formatted}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting principles: ${error}` }],
        isError: true
      }
    }
  },

  mantra_propose_decision: async (args, client) => {
    try {
      const result = await client.proposeDecision({
        title: args.title as string,
        group: args.group as string,
        content: args.content as string,
        rationale: args.rationale as string | undefined,
        alternatives: args.alternatives as string[] | undefined,
        implications: args.implications as string[] | undefined,
        references: args.references as string[] | undefined
      })

      return {
        content: [{
          type: 'text',
          text: `✅ Decision proposed successfully!\n\n` +
            `**ID:** ${result.id}\n` +
            `**Status:** ${result.status}\n` +
            `**Message:** ${result.message}\n\n` +
            `The proposal is now pending review. You will be notified when it is accepted or rejected.`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error proposing decision: ${error}` }],
        isError: true
      }
    }
  },

  mantra_validate_decision: async (args, client) => {
    try {
      const result = await client.validateDecision({
        title: args.title as string | undefined,
        group: args.group as string | undefined,
        content: args.content as string
      })

      let text = result.valid
        ? '✅ **Validation Passed**\n\n'
        : '❌ **Validation Failed**\n\n'

      if (result.errors.length > 0) {
        text += `### Errors\n${result.errors.map(e => `- ❌ ${e}`).join('\n')}\n\n`
      }

      if (result.warnings.length > 0) {
        text += `### Warnings\n${result.warnings.map(w => `- ⚠️ ${w}`).join('\n')}\n\n`
      }

      if (result.suggestions.length > 0) {
        text += `### Suggestions\n${result.suggestions.map(s => `- 💡 ${s}`).join('\n')}`
      }

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error validating decision: ${error}` }],
        isError: true
      }
    }
  },

  mantra_get_hints: async (args, client) => {
    try {
      const hints = await client.getHints(args.context as string)

      if (hints.length === 0) {
        return {
          content: [{
            type: 'text',
            text: 'No specific hints for this context. Proceed with standard guidelines.'
          }]
        }
      }

      const formatted = hints.map(h => {
        const icon = h.type === 'warning' ? '⚠️' : h.type === 'suggestion' ? '💡' : 'ℹ️'
        let text = `${icon} **${h.type.toUpperCase()}**: ${h.message}`
        if (h.related_decisions?.length) {
          text += `\n   Related: ${h.related_decisions.join(', ')}`
        }
        return text
      }).join('\n\n')

      return {
        content: [{
          type: 'text',
          text: `# Hints for: "${(args.context as string).substring(0, 50)}..."\n\n${formatted}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting hints: ${error}` }],
        isError: true
      }
    }
  },

  mantra_compare_decisions: async (args, client) => {
    try {
      const result = await client.compareDecisions(
        args.decision1 as string,
        args.decision2 as string
      )

      const text = `
# Comparison: ${result.decision1.code} vs ${result.decision2.code}

## ${result.decision1.code}: ${result.decision1.title}
${result.decision1.content.substring(0, 300)}...

## ${result.decision2.code}: ${result.decision2.title}
${result.decision2.content.substring(0, 300)}...

## Differences
${result.differences.map(d => `- ${d}`).join('\n')}

## Similarities
${result.similarities.map(s => `- ${s}`).join('\n')}
`.trim()

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error comparing decisions: ${error}` }],
        isError: true
      }
    }
  },

  mantra_get_grouped: async (_args, client) => {
    try {
      const grouped = await client.getGroupedDecisions()

      const text = Object.entries(grouped).map(([group, decisions]) => {
        const list = decisions.map(d => `  - ${d.code}: ${d.title} (${d.status})`).join('\n')
        return `## ${group} (${decisions.length})\n${list}`
      }).join('\n\n')

      return {
        content: [{
          type: 'text',
          text: `# All Decisions by Group\n\n${text}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting grouped decisions: ${error}` }],
        isError: true
      }
    }
  },

  mantra_semantic_search: async (args, client) => {
    try {
      const result = await client.semanticSearch({
        query: args.query as string,
        limit: (args.limit as number) || 10,
        min_score: (args.min_score as number) || 0.5,
        domain_id: args.domain_id as string | undefined,
        aspect_id: args.aspect_id as string | undefined
      })

      if (result.status === 'NOT_FOUND' || result.hits.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `No semantically similar decisions found for: "${args.query}"\n\n` +
              `Try broadening your query or adjusting the min_score (currently ${args.min_score || 0.5}).`
          }]
        }
      }

      if (result.status === 'ERROR') {
        return {
          content: [{
            type: 'text',
            text: `Semantic search error: ${result.error_message}`
          }],
          isError: true
        }
      }

      const formatted = result.hits.map((h, idx) => {
        const score = (h.score * 100).toFixed(1)
        return `### ${idx + 1}. ${h.decision_code} (${score}% match)\n` +
          `**Statement:** ${h.statement}\n` +
          `**Rationale:** ${h.rationale.substring(0, 200)}${h.rationale.length > 200 ? '...' : ''}\n` +
          `**Domain:** ${h.domain_id} | **Aspect:** ${h.aspect_id} | **Version:** ${h.version}\n` +
          `**Tags:** ${h.tags.join(', ') || 'none'}`
      }).join('\n\n---\n\n')

      const cacheNote = result.cached ? ' (cached)' : ''
      const timeNote = `${result.execution_time_ms.toFixed(1)}ms`

      return {
        content: [{
          type: 'text',
          text: `# Semantic Search Results${cacheNote}\n\n` +
            `**Query:** "${result.query}"\n` +
            `**Found:** ${result.total_count} decision(s) in ${timeNote}\n` +
            (Object.keys(result.filters_applied).length > 0
              ? `**Filters:** ${JSON.stringify(result.filters_applied)}\n`
              : '') +
            `\n---\n\n${formatted}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error in semantic search: ${error}` }],
        isError: true
      }
    }
  },

  mantra_check_alignment: async (args, client) => {
    try {
      const result = await client.checkAlignment({
        statement: args.statement as string,
        rationale: args.rationale as string | undefined,
        domain_id: args.domain_id as string | undefined
      })

      if (result.status === 'UNKNOWN' && result.error_message) {
        return {
          content: [{
            type: 'text',
            text: `Alignment check error: ${result.error_message}`
          }],
          isError: true
        }
      }

      const statusIcon = {
        'ALIGNED': '✅',
        'CONFLICTING': '⚠️',
        'PARTIAL': '🔶',
        'UNKNOWN': '❓'
      }[result.status] || '❓'

      let text = `# Alignment Check ${statusIcon}\n\n`
      text += `**Status:** ${result.status}\n`
      text += `**Checked in:** ${result.execution_time_ms.toFixed(1)}ms\n\n`

      text += `## Proposal\n`
      text += `**Statement:** ${args.statement}\n`
      if (args.rationale) {
        text += `**Rationale:** ${args.rationale}\n`
      }
      text += '\n'

      if (result.conflicts_with.length > 0) {
        text += `## ⚠️ Potential Conflicts (${result.conflicts_with.length})\n\n`
        for (const c of result.conflicts_with) {
          text += `### ${c.decision_code} (${(c.score * 100).toFixed(1)}% similar)\n`
          text += `${c.statement}\n\n`
        }
      }

      if (result.aligned_with.length > 0) {
        text += `## ✅ Aligned With (${result.aligned_with.length})\n\n`
        for (const a of result.aligned_with) {
          text += `- **${a.decision_code}**: ${a.statement.substring(0, 100)}... (${(a.score * 100).toFixed(1)}%)\n`
        }
        text += '\n'
      }

      if (result.related_decisions.length > 0) {
        text += `## 📎 Related Decisions (${result.related_decisions.length})\n\n`
        for (const r of result.related_decisions) {
          text += `- **${r.decision_code}**: ${r.statement.substring(0, 100)}... (${(r.score * 100).toFixed(1)}%)\n`
        }
        text += '\n'
      }

      if (result.recommendations.length > 0) {
        text += `## Recommendations\n\n`
        for (const rec of result.recommendations) {
          text += `${rec}\n`
        }
      }

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error checking alignment: ${error}` }],
        isError: true
      }
    }
  },

  mantra_search_stats: async (_args, client) => {
    try {
      const stats = await client.getSearchStats()

      const text = `# Semantic Search Statistics\n\n` +
        `| Property | Value |\n` +
        `|----------|-------|\n` +
        `| Collection | ${stats.collection_name} |\n` +
        `| Indexed Decisions | ${stats.count} |\n` +
        `| Vector Size | ${stats.vector_size} dimensions |\n` +
        `| Status | ${stats.status} |\n` +
        `| Cache Enabled | ${stats.cache_enabled ? 'Yes' : 'No'} |\n` +
        `| Embedding Model | ${stats.embedding_model} |\n` +
        `| Embedding Dimensions | ${stats.embedding_dimensions} |\n`

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting search stats: ${error}` }],
        isError: true
      }
    }
  }
}
