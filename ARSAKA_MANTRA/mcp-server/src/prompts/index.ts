/**
 * MANTRA MCP Prompts
 *
 * Pre-built prompts for common MANTRA workflows.
 * Updated to match MANTRA-SCHEMA-001.
 */

import { MantraClient, Decision, DOMAIN_LABELS, ASPECT_LABELS } from '../client.js'

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
        name: 'domain_id',
        description: 'The decision domain (INT, ARCH, CTL, EVO)',
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
        name: 'relevant_domains',
        description: 'Comma-separated list of relevant domains (INT, ARCH, CTL, EVO)',
        required: false
      }
    ]
  },
  {
    name: 'generate_rationale',
    description: 'Generate rationale and constraints for a decision',
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
    const domainId = args?.domain_id || ''

    // Get relevant decisions
    let decisionsContext = ''
    try {
      const decisions = await client.listDecisions({ limit: 10 })
      if (decisions.length > 0) {
        decisionsContext = '\n\nExisting Decisions:\n' +
          decisions.slice(0, 5).map((p: Decision) =>
            `- ${p.decision_code}: ${p.statement.substring(0, 80)}...`
          ).join('\n')
      }
    } catch {
      // Continue without decisions if fetch fails
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
${domainId ? `**Domain:** ${domainId} (${DOMAIN_LABELS[domainId as keyof typeof DOMAIN_LABELS] || domainId})\n` : ''}
${content}

${decisionsContext}

## Review Checklist
1. Does this decision have clear statement and rationale?
2. Are there any conflicts with existing decisions?
3. Is the scope appropriate (ORGANIZATION/DOMAIN/APPLICATION)?
4. Is the blast_radius appropriate (LOW/MEDIUM/HIGH/CRITICAL)?
5. Are constraints well-defined (PROHIBITION/REQUIREMENT/LIMITATION)?

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
          existing.slice(0, 5).map((d: Decision) =>
            `- ${d.decision_code} (${d.domain_id}/${d.aspect_id}): ${d.statement.substring(0, 60)}...`
          ).join('\n')
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

## MANTRA Taxonomy
**Domains:**
- INT: Intent & Direction (WHY/WHAT) - Aspects A01-A04
- ARCH: Architecture & Boundaries (HOW/WHERE) - Aspects A05-A08
- CTL: Control, Policy & Risk (CAN/MUST NOT) - Aspects A09-A12
- EVO: Execution & Evolution (CHANGE SAFELY) - Aspects A13-A16

Please suggest a decision with:
1. **domain_id**: Appropriate domain (INT, ARCH, CTL, EVO)
2. **aspect_id**: Appropriate aspect (A01-A16, matching domain)
3. **statement**: Clear decision statement
4. **rationale**: Why this decision makes sense
5. **constraints**: Array of {constraint_id, statement, type}
6. **invariants**: Things that must always be true
7. **scope**: ORGANIZATION, DOMAIN, or APPLICATION
8. **blast_radius**: LOW, MEDIUM, HIGH, or CRITICAL
9. **tags**: Area tags (FE, BE, DB, etc.)
10. **tech_stack**: Related technologies

Format the suggestion so it can be directly used with mantra_create_decision tool.`
          }
        }
      ]
    }
  },

  check_compliance: async (args, client) => {
    const implementation = args?.implementation || ''
    const relevantDomains = args?.relevant_domains?.split(',').map(g => g.trim()) || []

    // Get decisions from relevant domains
    let decisionsContext = ''
    try {
      const decisions = await client.listDecisions({ limit: 50 })
      const filtered = relevantDomains.length > 0
        ? decisions.filter((d: Decision) => relevantDomains.includes(d.domain_id))
        : decisions

      if (filtered.length > 0) {
        decisionsContext = '\n\nApplicable Decisions:\n' +
          filtered.slice(0, 10).map((d: Decision) =>
            `- ${d.decision_code} (${d.domain_id}/${d.aspect_id}): ${d.statement.substring(0, 60)}...`
          ).join('\n')
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
1. COMPLIANT - Implementation follows the decision
2. PARTIAL - Some aspects comply, others need adjustment
3. NON-COMPLIANT - Implementation violates the decision

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
      description: 'Generate rationale and constraints for a decision',
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Help me develop a complete rationale and constraints for the following decision.

## Decision
${decision}

${context ? `## Context\n${context}\n` : ''}

Please generate:

### Rationale
- Primary reasons for this decision
- Benefits and advantages
- How it aligns with best practices

### Constraints
For each constraint, provide:
- constraint_id (e.g., C-001, C-002)
- statement (what must/must not be done)
- type: PROHIBITION (must not), REQUIREMENT (must), or LIMITATION (bounded)

### Invariants
Things that must ALWAYS be true as a result of this decision.

### Implications
- Short-term impacts
- Long-term consequences
- Required follow-up actions
- Potential risks and mitigations

### Suggested Classifications
- scope: ORGANIZATION / DOMAIN / APPLICATION
- blast_radius: LOW / MEDIUM / HIGH / CRITICAL
- tags: Relevant area tags (FE, BE, DB, INFRA, etc.)
- tech_stack: Related technologies`
          }
        }
      ]
    }
  }
}
