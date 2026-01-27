/**
 * MANTRA MCP Prompts
 *
 * Pre-built prompts for common MANTRA workflows.
 */

import { MantraClient } from '../client.js'

// Prompt definitions
export const promptDefinitions = [
  {
    name: 'review_decision',
    description: 'Review a proposed decision for compliance with MANTRA principles',
    arguments: [
      {
        name: 'decision_content',
        description: 'The decision content to review',
        required: true
      },
      {
        name: 'group',
        description: 'The decision group (ARCH, SEC, etc.)',
        required: false
      }
    ]
  },
  {
    name: 'suggest_decision',
    description: 'Get suggestions for creating a decision based on a problem statement',
    arguments: [
      {
        name: 'problem',
        description: 'Description of the problem or requirement',
        required: true
      },
      {
        name: 'context',
        description: 'Additional context about the project or constraints',
        required: false
      }
    ]
  },
  {
    name: 'check_compliance',
    description: 'Check if an implementation plan complies with MANTRA decisions',
    arguments: [
      {
        name: 'implementation',
        description: 'Description of the proposed implementation',
        required: true
      },
      {
        name: 'relevant_groups',
        description: 'Comma-separated list of relevant decision groups',
        required: false
      }
    ]
  },
  {
    name: 'generate_rationale',
    description: 'Generate rationale and alternatives for a decision',
    arguments: [
      {
        name: 'decision',
        description: 'The decision being made',
        required: true
      },
      {
        name: 'context',
        description: 'Context and constraints',
        required: false
      }
    ]
  }
]

// Prompt handlers
type PromptHandler = (args: Record<string, string> | undefined, client: MantraClient) => Promise<{
  description?: string
  messages: Array<{
    role: 'user' | 'assistant'
    content: {
      type: 'text'
      text: string
    }
  }>
}>

export const promptHandlers: Record<string, PromptHandler> = {
  review_decision: async (args, client) => {
    const content = args?.decision_content || ''
    const group = args?.group || ''

    // Get relevant principles
    let principlesContext = ''
    try {
      const principles = await client.listDecisions({ layer: 0, status: 'accepted' })
      if (principles.length > 0) {
        principlesContext = '\n\nRelevant Layer 0 Principles:\n' +
          principles.slice(0, 5).map(p => `- ${p.code}: ${p.title}`).join('\n')
      }
    } catch {
      // Continue without principles if fetch fails
    }

    return {
      description: 'Review a decision for MANTRA compliance',
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Please review the following proposed decision for compliance with MANTRA constitutional principles.

## Proposed Decision
${group ? `**Group:** ${group}\n` : ''}
${content}

${principlesContext}

## Review Checklist
1. Does this decision align with Layer 0 principles?
2. Are there any conflicts with existing decisions?
3. Is the scope appropriate (not too broad or narrow)?
4. Are implications and alternatives considered?
5. Is the rationale clear and justified?

Please provide:
- Overall assessment (APPROVE / NEEDS CHANGES / REJECT)
- Specific feedback for each checklist item
- Suggested improvements if needed`
          }
        }
      ]
    }
  },

  suggest_decision: async (args, client) => {
    const problem = args?.problem || ''
    const context = args?.context || ''

    // Get relevant existing decisions
    let existingContext = ''
    try {
      const existing = await client.listDecisions({ limit: 10 })
      if (existing.length > 0) {
        existingContext = '\n\nExisting Related Decisions:\n' +
          existing.slice(0, 5).map(d => `- ${d.code}: ${d.title}`).join('\n')
      }
    } catch {
      // Continue without existing decisions
    }

    return {
      description: 'Suggest a decision based on problem statement',
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `I need help creating a MANTRA decision for the following problem.

## Problem Statement
${problem}

${context ? `## Additional Context\n${context}\n` : ''}
${existingContext}

Please suggest a decision with:
1. **Title**: Clear, concise title
2. **Group**: Appropriate group (ARCH, SEC, PERF, API, DB, UI, INFRA, PROC)
3. **Content**: Full decision description
4. **Rationale**: Why this decision makes sense
5. **Alternatives**: Other options that were considered
6. **Implications**: Consequences of this decision
7. **References**: Related existing decisions if any

Format the suggestion so it can be directly used with mantra_propose_decision tool.`
          }
        }
      ]
    }
  },

  check_compliance: async (args, client) => {
    const implementation = args?.implementation || ''
    const relevantGroups = args?.relevant_groups?.split(',').map(g => g.trim()) || []

    // Get decisions from relevant groups
    let decisionsContext = ''
    try {
      const decisions = await client.listDecisions({ status: 'accepted', limit: 20 })
      const filtered = relevantGroups.length > 0
        ? decisions.filter(d => relevantGroups.includes(d.group))
        : decisions

      if (filtered.length > 0) {
        decisionsContext = '\n\nApplicable Decisions:\n' +
          filtered.map(d => `- ${d.code} (${d.group}): ${d.title}`).join('\n')
      }
    } catch {
      // Continue without decisions
    }

    return {
      description: 'Check implementation compliance with MANTRA',
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Please check if the following implementation plan complies with MANTRA decisions.

## Proposed Implementation
${implementation}

${decisionsContext}

## Compliance Check
For each applicable decision, determine:
1. ✅ COMPLIANT - Implementation follows the decision
2. ⚠️ PARTIAL - Some aspects comply, others need adjustment
3. ❌ NON-COMPLIANT - Implementation violates the decision

Provide:
- Compliance status for each relevant decision
- Specific issues if non-compliant
- Recommendations for achieving full compliance`
          }
        }
      ]
    }
  },

  generate_rationale: async (args, _client) => {
    const decision = args?.decision || ''
    const context = args?.context || ''

    return {
      description: 'Generate rationale and alternatives for a decision',
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Help me develop a complete rationale for the following decision.

## Decision
${decision}

${context ? `## Context\n${context}\n` : ''}

Please generate:

### Rationale
- Primary reasons for this decision
- Benefits and advantages
- How it aligns with best practices

### Alternatives Considered
For each alternative:
- What the alternative is
- Pros and cons
- Why it was not chosen

### Implications
- Short-term impacts
- Long-term consequences
- Required follow-up actions
- Potential risks and mitigations

### Success Criteria
- How to measure if this decision is successful
- Key metrics or indicators`
          }
        }
      ]
    }
  }
}
