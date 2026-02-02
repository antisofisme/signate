/**
 * MANTRA MCP Tools
 *
 * Tools available to AI assistants for interacting with MANTRA.
 * Updated to match MANTRA-SCHEMA-001 and MANTRA-LAW-001.
 *
 * 4 Domains (INT, ARCH, CTL, EVO) x 4 Aspects (A01-A16) = 16 Decision Taxonomy
 */

import {
  MantraClient,
  Decision,
  DecisionCreate,
  Constraint,
  DomainId,
  AspectId,
  Scope,
  BlastRadius,
  DOMAIN_LABELS,
  ASPECT_LABELS,
  DOMAIN_ASPECT_MATRIX
} from '../client.js'

// Tool definitions for MCP - matching MANTRA-SCHEMA-001
export const toolDefinitions = [
  {
    name: 'mantra_search_decisions',
    description: 'Search for decisions in the MANTRA constitutional law system. Use this to find relevant precedents before making architectural decisions.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        query: {
          type: 'string',
          description: 'Search query (keywords, topics, or decision codes)'
        },
        domain_id: {
          type: 'string',
          description: 'Filter by domain: INT (Intent), ARCH (Architecture), CTL (Control), EVO (Evolution)',
          enum: ['INT', 'ARCH', 'CTL', 'EVO']
        },
        aspect_id: {
          type: 'string',
          description: 'Filter by aspect (A01-A16)',
          enum: ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08',
                 'A09', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16']
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
    description: 'Get full details of a specific decision by ID or code (e.g., INT-A01-001-v1.0.0).',
    inputSchema: {
      type: 'object' as const,
      properties: {
        id: {
          type: 'string',
          description: 'Decision ID (UUID) or code (e.g., INT-A01-001-v1.0.0)'
        }
      },
      required: ['id']
    }
  },
  {
    name: 'mantra_create_decision',
    description: `Create a new decision in the MANTRA system. Per MANTRA-LAW-001, decisions are IMMUTABLE once created.

REQUIRED FIELDS:
- domain_id: INT (Intent), ARCH (Architecture), CTL (Control), EVO (Evolution)
- aspect_id: Must match domain (INT: A01-A04, ARCH: A05-A08, CTL: A09-A12, EVO: A13-A16)
- statement: What the decision is (clear, actionable)
- rationale: Why the decision was made
- scope: ORGANIZATION, DOMAIN, or APPLICATION
- blast_radius: LOW, MEDIUM, HIGH, or CRITICAL
- version: Semver format (e.g., "1.0.0")
- created_by: Human identifier (AI cannot create decisions per MANTRA-LAW-001)

OPTIONAL FIELDS:
- constraints: Array of {constraint_id, statement, type: PROHIBITION|REQUIREMENT|LIMITATION}
- invariants: Array of strings (things that must always be true)
- tags: Array of area tags (FE, BE, DB, INFRA, etc.)
- tech_stack: Array of technologies`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        domain_id: {
          type: 'string',
          description: 'Domain: INT (Intent & Direction), ARCH (Architecture), CTL (Control & Policy), EVO (Evolution)',
          enum: ['INT', 'ARCH', 'CTL', 'EVO']
        },
        aspect_id: {
          type: 'string',
          description: 'Aspect within domain. INT: A01-A04, ARCH: A05-A08, CTL: A09-A12, EVO: A13-A16',
          enum: ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08',
                 'A09', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16']
        },
        statement: {
          type: 'string',
          description: 'Clear statement of what the decision is (10-200 words)'
        },
        rationale: {
          type: 'string',
          description: 'Why this decision was made (20-500 words)'
        },
        scope: {
          type: 'string',
          description: 'Decision scope',
          enum: ['ORGANIZATION', 'DOMAIN', 'APPLICATION']
        },
        blast_radius: {
          type: 'string',
          description: 'Impact level if violated',
          enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        },
        version: {
          type: 'string',
          description: 'Semantic version (e.g., "1.0.0")'
        },
        created_by: {
          type: 'string',
          description: 'Human identifier who authored this decision'
        },
        constraints: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              constraint_id: { type: 'string', description: 'Unique ID (e.g., C-001)' },
              statement: { type: 'string', description: 'Constraint statement' },
              type: { type: 'string', enum: ['PROHIBITION', 'REQUIREMENT', 'LIMITATION'] }
            },
            required: ['constraint_id', 'statement', 'type']
          },
          description: 'Constraints enforced by this decision'
        },
        invariants: {
          type: 'array',
          items: { type: 'string' },
          description: 'Things that must always be true'
        },
        tags: {
          type: 'array',
          items: { type: 'string' },
          description: 'Area tags: FE, BE, DB, INFRA, CICD, API, SECURITY, DEVOPS'
        },
        tech_stack: {
          type: 'array',
          items: { type: 'string' },
          description: 'Technologies: React, FastAPI, PostgreSQL, Docker, etc.'
        },
        detailed_content: {
          type: 'string',
          description: 'Full specification in Markdown (Layer B content)'
        }
      },
      required: ['domain_id', 'aspect_id', 'statement', 'rationale', 'scope', 'blast_radius', 'version', 'created_by']
    }
  },
  {
    name: 'mantra_validate_decision',
    description: 'Validate a proposed decision against MANTRA schema and rules. Use this BEFORE creating to check compliance.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        domain_id: {
          type: 'string',
          enum: ['INT', 'ARCH', 'CTL', 'EVO']
        },
        aspect_id: {
          type: 'string',
          enum: ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08',
                 'A09', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16']
        },
        statement: {
          type: 'string',
          description: 'Decision statement to validate'
        },
        rationale: {
          type: 'string',
          description: 'Decision rationale to validate'
        }
      },
      required: ['statement']
    }
  },
  {
    name: 'mantra_get_hints',
    description: 'Get AI-powered hints and suggestions based on context. Useful when planning implementations.',
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
    name: 'mantra_get_grouped',
    description: 'Get all decisions organized by domain (INT, ARCH, CTL, EVO). Useful for overview.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  },
  {
    name: 'mantra_semantic_search',
    description: 'Search for semantically similar decisions using AI embeddings. More accurate than keyword search.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        query: {
          type: 'string',
          description: 'Natural language search query'
        },
        limit: {
          type: 'number',
          description: 'Maximum results (default: 10, max: 100)'
        },
        min_score: {
          type: 'number',
          description: 'Minimum similarity score 0.0-1.0 (default: 0.5)'
        },
        domain_id: {
          type: 'string',
          description: 'Filter by domain',
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
    description: 'Check if a proposed decision aligns with existing decisions. ALWAYS use this before creating a new decision.',
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
    description: 'Get statistics about the semantic search index.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  },
  {
    name: 'mantra_get_taxonomy',
    description: 'Get the MANTRA 4x4 decision taxonomy (4 Domains x 4 Aspects). Use this to understand the classification system.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  },
  // ==================== NEW TOOLS: Enhanced Retrieval ====================
  {
    name: 'mantra_retrieve',
    description: `Context-aware decision retrieval. Use this when you need decisions relevant to your current coding context.

Features:
- Analyzes file path and content for context
- Triggers relevant decisions based on patterns
- Caches results for fast repeated queries
- Tracks usage for analytics

Best for: Finding decisions while coding, getting context-specific guidance.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        query: {
          type: 'string',
          description: 'Natural language query or code context description'
        },
        file_path: {
          type: 'string',
          description: 'Current file path for context (e.g., src/components/Auth.tsx)'
        },
        file_content: {
          type: 'string',
          description: 'First 2000 chars of current file for analysis'
        },
        scope_path: {
          type: 'string',
          description: 'Scope path filter (e.g., "frontend/*", "backend/api/*")'
        },
        max_results: {
          type: 'number',
          description: 'Maximum results (default: 10, max: 50)'
        },
        token_budget: {
          type: 'number',
          description: 'Token budget for response (default: 2000)'
        }
      },
      required: ['query']
    }
  },
  {
    name: 'mantra_check_triggers',
    description: 'Check which decision triggers match a given context. Useful for understanding why certain decisions are returned.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        file_path: {
          type: 'string',
          description: 'File path to check triggers against'
        },
        file_content: {
          type: 'string',
          description: 'File content to analyze'
        },
        scope_path: {
          type: 'string',
          description: 'Scope path to check'
        },
        keywords: {
          type: 'array',
          items: { type: 'string' },
          description: 'Additional keywords to check'
        }
      }
    }
  },
  // ==================== NEW TOOLS: 3-Gate Validation ====================
  {
    name: 'mantra_validate_full',
    description: `Run the full 3-gate validation pipeline on a proposed decision.

Pipeline stages:
1. Gate 1 (Deterministic): Schema validation, field rules - HARD block
2. Gate 2 (AI Heuristic): Quality check, conflict detection - SOFT warning
3. Gate 3 (Human Approval): Creates approval request - HARD block

Per MANTRA-LAW-001 §6: AI has ZERO approval authority. Use this to prepare decisions for human review.`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        decision: {
          type: 'object',
          description: 'The decision record to validate (full schema)',
          properties: {
            domain_id: { type: 'string', enum: ['INT', 'ARCH', 'CTL', 'EVO'] },
            aspect_id: { type: 'string' },
            statement: { type: 'string' },
            rationale: { type: 'string' },
            scope: { type: 'string', enum: ['ORGANIZATION', 'DOMAIN', 'APPLICATION'] },
            blast_radius: { type: 'string', enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] },
            version: { type: 'string' },
            constraints: { type: 'array' },
            invariants: { type: 'array' },
            tags: { type: 'array' }
          }
        },
        submitted_by: {
          type: 'string',
          description: 'Human identifier submitting this decision (REQUIRED - AI cannot submit)'
        },
        auto_create_approval: {
          type: 'boolean',
          description: 'Auto-create approval request if Gate 1 & 2 pass (default: true)'
        }
      },
      required: ['decision', 'submitted_by']
    }
  },
  {
    name: 'mantra_pending_approvals',
    description: 'List decisions pending human approval. Useful for workflow visibility.',
    inputSchema: {
      type: 'object' as const,
      properties: {
        reviewer_id: {
          type: 'string',
          description: 'Filter by assigned reviewer (optional)'
        }
      }
    }
  },
  // ==================== NEW TOOLS: Document Generation ====================
  {
    name: 'mantra_generate_document',
    description: `Generate documentation from MANTRA decisions. Single source of truth → multiple document outputs.

Available document types:
- PRD: Product Requirements Document
- TECH_SPEC: Technical Specification
- API_SPEC: API Specification
- SECURITY_SPEC: Security Specification
- TEST_PLAN: Test Plan
- ADR: Architecture Decision Records
- EXEC_SUMMARY: Executive Summary
- USER_MANUAL: User Manual
- And more (22 types total)

Output formats: MARKDOWN, HTML, PDF`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        doc_type: {
          type: 'string',
          description: 'Document type to generate',
          enum: ['PRD', 'TECH_SPEC', 'API_SPEC', 'SECURITY_SPEC', 'TEST_PLAN', 'ADR',
                 'EXEC_SUMMARY', 'USER_MANUAL', 'FEATURE_SPEC', 'THREAT_MODEL',
                 'DEPLOYMENT_GUIDE', 'RUNBOOK', 'FAQ', 'CHANGELOG']
        },
        title: {
          type: 'string',
          description: 'Custom document title (optional)'
        },
        scope_filter: {
          type: 'string',
          description: 'Filter decisions by scope path'
        },
        domain_filter: {
          type: 'string',
          description: 'Filter by domain (INT, ARCH, CTL, EVO)'
        },
        tag_filter: {
          type: 'array',
          items: { type: 'string' },
          description: 'Filter by tags'
        },
        max_decisions: {
          type: 'number',
          description: 'Maximum decisions to include'
        },
        company_name: {
          type: 'string',
          description: 'Company name for document header'
        }
      },
      required: ['doc_type']
    }
  },
  {
    name: 'mantra_list_doc_types',
    description: 'List all available document types with their descriptions and target audiences.',
    inputSchema: {
      type: 'object' as const,
      properties: {}
    }
  },
  // ==================== NEW TOOLS: Analytics ====================
  {
    name: 'mantra_track_usage',
    description: `Track decision usage events. Helps improve retrieval relevance over time.

Event types:
- VIEW: Decision was shown/retrieved
- APPLY: Decision was applied/used
- SKIP: Decision was shown but skipped`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        event_type: {
          type: 'string',
          description: 'Event type',
          enum: ['VIEW', 'APPLY', 'SKIP']
        },
        decision_id: {
          type: 'string',
          description: 'Decision ID or code'
        },
        query: {
          type: 'string',
          description: 'Search query that led to this decision'
        },
        file_path: {
          type: 'string',
          description: 'File context where decision was used'
        }
      },
      required: ['event_type', 'decision_id']
    }
  },
  {
    name: 'mantra_feedback',
    description: `Submit feedback on a decision. Helps identify problematic decisions.

Feedback types:
- HELPFUL: Decision was useful
- NOT_HELPFUL: Decision was not useful
- OUTDATED: Decision seems outdated
- UNCLEAR: Decision is unclear
- WRONG_CONTEXT: Wrong decision for the context`,
    inputSchema: {
      type: 'object' as const,
      properties: {
        decision_id: {
          type: 'string',
          description: 'Decision ID or code'
        },
        feedback_type: {
          type: 'string',
          description: 'Type of feedback',
          enum: ['HELPFUL', 'NOT_HELPFUL', 'OUTDATED', 'UNCLEAR', 'WRONG_CONTEXT']
        },
        comment: {
          type: 'string',
          description: 'Additional feedback comment'
        }
      },
      required: ['decision_id', 'feedback_type']
    }
  },
  {
    name: 'mantra_analytics_summary',
    description: 'Get overall analytics summary including hot, stale, and problematic decisions.',
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
        domain_id: args.domain_id as DomainId | undefined,
        aspect_id: args.aspect_id as AspectId | undefined,
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

      const formatted = decisions.map((d: Decision) => {
        const domainLabel = DOMAIN_LABELS[d.domain_id] || d.domain_id
        const aspectLabel = ASPECT_LABELS[d.aspect_id] || d.aspect_id
        return `**${d.decision_code}**\n` +
          `  Domain: ${d.domain_id} (${domainLabel})\n` +
          `  Aspect: ${d.aspect_id} (${aspectLabel})\n` +
          `  Statement: ${d.statement.substring(0, 150)}${d.statement.length > 150 ? '...' : ''}\n` +
          `  Scope: ${d.scope} | Blast Radius: ${d.blast_radius}`
      }).join('\n\n')

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

      const constraintsList = decision.constraints.length > 0
        ? decision.constraints.map(c => `- **${c.constraint_id}** [${c.type}]: ${c.statement}`).join('\n')
        : '(none)'

      const invariantsList = decision.invariants.length > 0
        ? decision.invariants.map(i => `- ${i}`).join('\n')
        : '(none)'

      const text = `
# ${decision.decision_code}

**Domain:** ${decision.domain_id} (${DOMAIN_LABELS[decision.domain_id]})
**Aspect:** ${decision.aspect_id} (${ASPECT_LABELS[decision.aspect_id]})
**Scope:** ${decision.scope}
**Blast Radius:** ${decision.blast_radius}
**Version:** ${decision.version}
**Created:** ${decision.created_at} by ${decision.created_by || 'unknown'}

## Statement
${decision.statement}

## Rationale
${decision.rationale}

## Constraints
${constraintsList}

## Invariants
${invariantsList}

${decision.tags?.length ? `**Tags:** ${decision.tags.join(', ')}` : ''}
${decision.tech_stack?.length ? `**Tech Stack:** ${decision.tech_stack.join(', ')}` : ''}
${decision.detailed_content ? `\n---\n## Detailed Content (Layer B)\n${decision.detailed_content}` : ''}
`.trim()

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting decision: ${error}` }],
        isError: true
      }
    }
  },

  mantra_create_decision: async (args, client) => {
    try {
      // Validate domain-aspect compatibility
      const domainId = args.domain_id as DomainId
      const aspectId = args.aspect_id as AspectId
      const validAspects = DOMAIN_ASPECT_MATRIX[domainId]

      if (!validAspects.includes(aspectId)) {
        return {
          content: [{
            type: 'text',
            text: `❌ Invalid aspect for domain.\n\n` +
              `Domain ${domainId} (${DOMAIN_LABELS[domainId]}) only accepts aspects: ${validAspects.join(', ')}\n\n` +
              `You provided: ${aspectId}`
          }],
          isError: true
        }
      }

      const decision: DecisionCreate = {
        domain_id: domainId,
        aspect_id: aspectId,
        statement: args.statement as string,
        rationale: args.rationale as string,
        scope: args.scope as Scope,
        blast_radius: args.blast_radius as BlastRadius,
        version: args.version as string,
        created_by: args.created_by as string,
        constraints: args.constraints as Constraint[] | undefined,
        invariants: args.invariants as string[] | undefined,
        tags: args.tags as string[] | undefined,
        tech_stack: args.tech_stack as string[] | undefined,
        detailed_content: args.detailed_content as string | undefined
      }

      const result = await client.createDecision(decision, args.created_by as string)

      return {
        content: [{
          type: 'text',
          text: `✅ Decision created successfully!\n\n` +
            `**Code:** ${result.decision_code}\n` +
            `**ID:** ${result.decision_id}\n` +
            `**Domain:** ${result.domain_id} (${DOMAIN_LABELS[result.domain_id]})\n` +
            `**Aspect:** ${result.aspect_id} (${ASPECT_LABELS[result.aspect_id]})\n` +
            `**Scope:** ${result.scope}\n` +
            `**Blast Radius:** ${result.blast_radius}\n\n` +
            `⚠️ Per MANTRA-LAW-001, this decision is now IMMUTABLE.`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error creating decision: ${error}` }],
        isError: true
      }
    }
  },

  mantra_validate_decision: async (args, client) => {
    try {
      // Local validation first
      const errors: string[] = []
      const warnings: string[] = []

      if (args.domain_id && args.aspect_id) {
        const domainId = args.domain_id as DomainId
        const aspectId = args.aspect_id as AspectId
        const validAspects = DOMAIN_ASPECT_MATRIX[domainId]

        if (!validAspects.includes(aspectId)) {
          errors.push(`Aspect ${aspectId} is not valid for domain ${domainId}. Valid aspects: ${validAspects.join(', ')}`)
        }
      }

      if (!args.statement || (args.statement as string).length < 10) {
        errors.push('Statement must be at least 10 characters')
      }

      if (!args.rationale || (args.rationale as string).length < 20) {
        warnings.push('Rationale should be at least 20 characters for clarity')
      }

      // Try API validation
      try {
        const result = await client.validateDecision({
          domain_id: args.domain_id as DomainId,
          aspect_id: args.aspect_id as AspectId,
          statement: args.statement as string,
          rationale: args.rationale as string
        })

        errors.push(...result.errors)
        warnings.push(...result.warnings)
      } catch {
        // API validation not available, use local only
      }

      const valid = errors.length === 0

      let text = valid
        ? '✅ **Validation Passed**\n\n'
        : '❌ **Validation Failed**\n\n'

      if (errors.length > 0) {
        text += `### Errors\n${errors.map(e => `- ❌ ${e}`).join('\n')}\n\n`
      }

      if (warnings.length > 0) {
        text += `### Warnings\n${warnings.map(w => `- ⚠️ ${w}`).join('\n')}\n\n`
      }

      if (valid && args.domain_id && args.aspect_id) {
        text += `### Ready to Create\n`
        text += `Domain: ${args.domain_id} (${DOMAIN_LABELS[args.domain_id as DomainId]})\n`
        text += `Aspect: ${args.aspect_id} (${ASPECT_LABELS[args.aspect_id as AspectId]})\n`
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

  mantra_get_grouped: async (_args, client) => {
    try {
      const grouped = await client.getGroupedDecisions()

      const domains: DomainId[] = ['INT', 'ARCH', 'CTL', 'EVO']
      const text = domains.map(domain => {
        const decisions = grouped[domain] || []
        const label = DOMAIN_LABELS[domain]
        const list = decisions.length > 0
          ? decisions.map((d: Decision) => {
              return `  - **${d.decision_code}**: ${d.statement.substring(0, 60)}${d.statement.length > 60 ? '...' : ''}`
            }).join('\n')
          : '  (no decisions yet)'
        return `## ${domain} - ${label} (${decisions.length})\n${list}`
      }).join('\n\n')

      const totalCount = Object.values(grouped).reduce((sum, arr) => sum + arr.length, 0)

      return {
        content: [{
          type: 'text',
          text: `# MANTRA Decisions by Domain\n\n**Total:** ${totalCount} decisions\n\n${text}`
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
        domain_id: args.domain_id as DomainId | undefined,
        aspect_id: args.aspect_id as AspectId | undefined
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
          `**Domain:** ${h.domain_id} | **Aspect:** ${h.aspect_id}\n` +
          `**Tags:** ${h.tags.join(', ') || 'none'}`
      }).join('\n\n---\n\n')

      return {
        content: [{
          type: 'text',
          text: `# Semantic Search Results\n\n` +
            `**Query:** "${result.query}"\n` +
            `**Found:** ${result.total_count} decision(s) in ${result.execution_time_ms.toFixed(1)}ms\n` +
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
        domain_id: args.domain_id as DomainId | undefined
      })

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

      if (result.recommendations.length > 0) {
        text += `## Recommendations\n\n`
        for (const rec of result.recommendations) {
          text += `${rec}\n`
        }
      } else if (result.status === 'ALIGNED' && result.conflicts_with.length === 0) {
        text += `## Recommendations\n\n🆕 No similar decisions found. This appears to be a new area.\n`
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
        `| Embedding Model | ${stats.embedding_model} |\n`

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting search stats: ${error}` }],
        isError: true
      }
    }
  },

  mantra_get_taxonomy: async (_args, _client) => {
    const text = `# MANTRA 4x4 Decision Taxonomy

Per MANTRA-LAW-001, decisions are classified using 4 Domains x 4 Aspects = 16 categories.

## Domains

| Code | Name | Scope |
|------|------|-------|
| **INT** | Intent & Direction | WHY / WHAT |
| **ARCH** | Architecture & Boundaries | HOW / WHERE |
| **CTL** | Control, Policy & Risk | CAN / MUST NOT |
| **EVO** | Execution & Evolution | CHANGE SAFELY |

## Aspects by Domain

### INT (Intent & Direction)
| Aspect | Name |
|--------|------|
| A01 | Vision & Outcome |
| A02 | Problem Statement |
| A03 | Scope & Non-Goals |
| A04 | Principles & Values |

### ARCH (Architecture & Boundaries)
| Aspect | Name |
|--------|------|
| A05 | Domain & Bounded Context |
| A06 | Service & Module Boundary |
| A07 | Data Ownership & Sovereignty |
| A08 | Integration & Contract Model |

### CTL (Control, Policy & Risk)
| Aspect | Name |
|--------|------|
| A09 | Policy & Rules |
| A10 | Approval & Authority Model |
| A11 | Security & Compliance Posture |
| A12 | Risk & Blast Radius |

### EVO (Execution & Evolution)
| Aspect | Name |
|--------|------|
| A13 | Decision Lifecycle |
| A14 | Reversibility & Exit Strategy |
| A15 | Environment & Promotion Rules |
| A16 | Anti-Drift & Consistency |

## Example Decision Codes

- \`INT-A01-001-v1.0.0\` - First Vision decision
- \`ARCH-A06-003-v2.0.0\` - Third Service Boundary decision, version 2
- \`CTL-A11-001-v1.0.0\` - First Security decision
`

    return { content: [{ type: 'text', text }] }
  },

  // ==================== NEW HANDLERS: Enhanced Retrieval ====================

  mantra_retrieve: async (args, client) => {
    try {
      const result = await client.retrieve({
        query: args.query as string,
        file_path: args.file_path as string | undefined,
        file_content: args.file_content as string | undefined,
        scope_path: args.scope_path as string | undefined,
        max_results: (args.max_results as number) || 10,
        token_budget: (args.token_budget as number) || 2000,
        use_cache: true,
        track_usage: true
      })

      if (result.results.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `No relevant decisions found for: "${args.query}"\n\n` +
              `Suggestions:\n${result.suggestions.length > 0 ? result.suggestions.map(s => `- ${s}`).join('\n') : '- Try a broader query'}`
          }]
        }
      }

      const formatted = result.results.map((r, idx) => {
        const confidence = (r.confidence * 100).toFixed(0)
        return `### ${idx + 1}. ${r.decision_code} (${confidence}% confidence)\n` +
          `**Statement:** ${r.statement}\n` +
          `**Source:** ${r.source} | **Matched by:** ${r.matched_by.join(', ')}\n` +
          (r.rationale ? `> ${r.rationale.substring(0, 150)}...` : '')
      }).join('\n\n---\n\n')

      let text = `# Context-Aware Retrieval Results\n\n`
      text += `**Query:** "${args.query}"\n`
      if (args.file_path) text += `**File:** ${args.file_path}\n`
      text += `**Found:** ${result.total_count} decision(s) in ${result.execution_time_ms.toFixed(1)}ms\n`
      text += `**From Cache:** ${result.from_cache ? 'Yes' : 'No'}\n`
      if (result.triggered_by.length > 0) {
        text += `**Triggered by:** ${result.triggered_by.join(', ')}\n`
      }
      text += `**Token Count:** ~${result.token_count}\n\n`
      text += `---\n\n${formatted}`

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error in context retrieval: ${error}` }],
        isError: true
      }
    }
  },

  mantra_check_triggers: async (args, client) => {
    try {
      const result = await client.checkTriggers({
        file_path: args.file_path as string | undefined,
        file_content: args.file_content as string | undefined,
        scope_path: args.scope_path as string | undefined,
        keywords: args.keywords as string[] | undefined
      })

      if (!result.triggered) {
        return {
          content: [{
            type: 'text',
            text: `No triggers matched for the given context.\n\n` +
              `Checked:\n` +
              (args.file_path ? `- File: ${args.file_path}\n` : '') +
              (args.scope_path ? `- Scope: ${args.scope_path}\n` : '') +
              (args.keywords ? `- Keywords: ${(args.keywords as string[]).join(', ')}` : '')
          }]
        }
      }

      const triggersText = result.triggers.map(t => {
        return `### ${t.name}\n` +
          `- **Type:** ${t.type}\n` +
          `- **Priority:** ${t.priority}\n` +
          `- **Matched:** ${t.matched_patterns.join(', ')}\n` +
          `- **Decisions:** ${t.decision_ids.join(', ')}`
      }).join('\n\n')

      return {
        content: [{
          type: 'text',
          text: `# Trigger Analysis\n\n` +
            `**Triggered:** Yes (${result.triggers.length} trigger(s))\n` +
            `**Total Decisions:** ${result.decision_ids.length}\n\n` +
            `## Matched Triggers\n\n${triggersText}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error checking triggers: ${error}` }],
        isError: true
      }
    }
  },

  // ==================== NEW HANDLERS: 3-Gate Validation ====================

  mantra_validate_full: async (args, client) => {
    try {
      // Check if submitted_by looks like AI
      const submittedBy = args.submitted_by as string
      if (submittedBy.toLowerCase().startsWith('ai:') || submittedBy.toLowerCase().includes('claude') || submittedBy.toLowerCase().includes('gpt')) {
        return {
          content: [{
            type: 'text',
            text: `❌ **MANTRA-LAW-001 §6 Violation**\n\n` +
              `AI cannot submit decisions for approval.\n\n` +
              `The \`submitted_by\` field must be a human identifier.\n` +
              `Provided: "${submittedBy}"`
          }],
          isError: true
        }
      }

      const result = await client.validatePipeline({
        decision: args.decision as Record<string, unknown>,
        submitted_by: submittedBy,
        auto_create_approval: (args.auto_create_approval as boolean) !== false
      })

      const outcomeIcon = {
        'APPROVED': '✅',
        'PENDING_APPROVAL': '⏳',
        'REJECTED_GATE1': '❌',
        'REJECTED_GATE2': '⚠️',
        'REJECTED': '❌'
      }[result.outcome] || '❓'

      let text = `# Validation Pipeline Result ${outcomeIcon}\n\n`
      text += `**Outcome:** ${result.outcome}\n`
      text += `**Stage:** ${result.stage}\n`
      text += `**Decision ID:** ${result.decision_id}\n`
      text += `**Decision Code:** ${result.decision_code}\n`
      text += `**Can Activate:** ${result.can_activate ? 'Yes' : 'No'}\n`

      if (result.approval_request_id) {
        text += `**Approval Request ID:** ${result.approval_request_id}\n`
      }

      text += `\n## Messages\n\n`
      text += result.messages.map(m => `- ${m}`).join('\n')

      if (result.gate1) {
        text += `\n\n## Gate 1 (Deterministic)\n`
        text += `Status: ${(result.gate1 as Record<string, unknown>).status || 'N/A'}\n`
      }

      if (result.gate2) {
        text += `\n\n## Gate 2 (AI Heuristic)\n`
        text += `Quality Score: ${(result.gate2 as Record<string, unknown>).quality_score || 'N/A'}\n`
      }

      if (result.outcome === 'PENDING_APPROVAL') {
        text += `\n\n---\n⏳ **Awaiting Human Approval**\n`
        text += `Per MANTRA-LAW-001 §6, a human reviewer must approve this decision.`
      }

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error in validation pipeline: ${error}` }],
        isError: true
      }
    }
  },

  mantra_pending_approvals: async (args, client) => {
    try {
      const approvals = await client.getPendingApprovals(args.reviewer_id as string | undefined)

      if (approvals.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `No pending approvals found.${args.reviewer_id ? ` (filtered by reviewer: ${args.reviewer_id})` : ''}`
          }]
        }
      }

      const list = approvals.map(a => {
        return `### ${a.decision_code}\n` +
          `- **Request ID:** ${a.request_id}\n` +
          `- **Submitted by:** ${a.submitted_by}\n` +
          `- **Submitted at:** ${a.submitted_at}\n` +
          `- **Gate 1:** ${a.gate1_passed ? '✅' : '❌'} | **Gate 2:** ${a.gate2_passed ? '✅' : '⚠️'}\n` +
          `- **Comments:** ${a.comments_count}`
      }).join('\n\n')

      return {
        content: [{
          type: 'text',
          text: `# Pending Approvals (${approvals.length})\n\n` +
            `Per MANTRA-LAW-001 §6, these decisions require human approval.\n\n` +
            list
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting pending approvals: ${error}` }],
        isError: true
      }
    }
  },

  // ==================== NEW HANDLERS: Document Generation ====================

  mantra_generate_document: async (args, client) => {
    try {
      const result = await client.generateDocument({
        doc_type: args.doc_type as string,
        title: args.title as string | undefined,
        scope_filter: args.scope_filter as string | undefined,
        domain_filter: args.domain_filter as string | undefined,
        tag_filter: args.tag_filter as string[] | undefined,
        max_decisions: args.max_decisions as number | undefined,
        company_name: args.company_name as string | undefined,
        include_toc: true,
        include_metadata: true
      })

      let text = `# Document Generated: ${result.doc_type}\n\n`
      text += `**Title:** ${result.title}\n`
      text += `**Version:** ${result.version}\n`
      text += `**Format:** ${result.output_format}\n`
      text += `**Generated:** ${result.generated_at}\n`
      text += `**Word Count:** ${result.word_count}\n`
      text += `**Sections:** ${result.section_count}\n`
      text += `**Decisions:** ${result.decision_count}\n`
      text += `**Source Decisions:** ${result.source_decisions.join(', ')}\n\n`
      text += `---\n\n`
      text += result.content

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error generating document: ${error}` }],
        isError: true
      }
    }
  },

  mantra_list_doc_types: async (_args, client) => {
    try {
      const types = await client.listDocumentTypes()

      const byPhase: Record<string, typeof types> = {}
      for (const t of types) {
        if (!byPhase[t.phase]) byPhase[t.phase] = []
        byPhase[t.phase].push(t)
      }

      let text = `# Available Document Types (${types.length})\n\n`

      for (const [phase, docs] of Object.entries(byPhase)) {
        text += `## ${phase} Phase\n\n`
        text += `| Type | Name | Audience |\n`
        text += `|------|------|----------|\n`
        for (const d of docs) {
          text += `| ${d.type} | ${d.name} | ${d.primary_audience} |\n`
        }
        text += '\n'
      }

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error listing document types: ${error}` }],
        isError: true
      }
    }
  },

  // ==================== NEW HANDLERS: Analytics ====================

  mantra_track_usage: async (args, client) => {
    try {
      const result = await client.trackEvent({
        event_type: args.event_type as string,
        decision_id: args.decision_id as string,
        query: args.query as string | undefined,
        file_path: args.file_path as string | undefined
      })

      return {
        content: [{
          type: 'text',
          text: `✅ Usage tracked: ${result.event_type} on ${args.decision_id}\n` +
            `Event ID: ${result.event_id}`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error tracking usage: ${error}` }],
        isError: true
      }
    }
  },

  mantra_feedback: async (args, client) => {
    try {
      const result = await client.trackFeedback({
        decision_id: args.decision_id as string,
        feedback_type: args.feedback_type as string,
        comment: args.comment as string | undefined
      })

      const emoji = {
        'HELPFUL': '👍',
        'NOT_HELPFUL': '👎',
        'OUTDATED': '📅',
        'UNCLEAR': '❓',
        'WRONG_CONTEXT': '🚫'
      }[result.feedback_type] || '📝'

      return {
        content: [{
          type: 'text',
          text: `${emoji} Feedback recorded: ${result.feedback_type} on ${args.decision_id}\n` +
            `Feedback ID: ${result.feedback_id}\n\n` +
            `Thank you for helping improve MANTRA decision quality!`
        }]
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error submitting feedback: ${error}` }],
        isError: true
      }
    }
  },

  mantra_analytics_summary: async (_args, client) => {
    try {
      const summary = await client.getAnalyticsSummary()

      const text = `# MANTRA Analytics Summary\n\n` +
        `| Metric | Value |\n` +
        `|--------|-------|\n` +
        `| Decisions Tracked | ${summary.total_decisions_tracked} |\n` +
        `| Total Events | ${summary.total_events} |\n` +
        `| Total Feedback | ${summary.total_feedback} |\n` +
        `| Hot Decisions | ${summary.hot_decisions_count} |\n` +
        `| Stale Decisions | ${summary.stale_decisions_count} |\n` +
        `| Problematic Decisions | ${summary.problematic_decisions_count} |\n\n` +
        (summary.problematic_decisions_count > 0
          ? `⚠️ ${summary.problematic_decisions_count} decision(s) have negative feedback and need attention.`
          : '✅ No problematic decisions detected.')

      return { content: [{ type: 'text', text }] }
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error getting analytics: ${error}` }],
        isError: true
      }
    }
  }
}
