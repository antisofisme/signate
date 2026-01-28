/**
 * Decision Creation Wizard
 * Multi-step form for creating new decisions with validation preview
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import {
  decisionsApi,
  enhancedValidationApi,
  DecisionCreate,
  EnhancedValidationResponse,
  Constraint,
  Relation,
} from '../shared/api'
import {
  DOMAINS,
  ASPECTS,
  DOMAIN_LABELS,
  ASPECT_LABELS,
  DOMAIN_COLORS,
} from '../shared/constants'

// =============================================================================
// Types
// =============================================================================

interface WizardState {
  // Step 1: Basic Info
  domain_id: string
  aspect_id: string
  statement: string
  rationale: string

  // Step 2: Metadata
  scope: string
  blast_radius: string
  version: string
  tags: string[]
  tech_stack: string[]

  // Step 3: Constraints
  constraints: Constraint[]
  invariants: string[]

  // Step 4: Relations
  supersedes: string
  relations: Relation[]

  // Author
  created_by: string
}

const initialState: WizardState = {
  domain_id: '',
  aspect_id: '',
  statement: '',
  rationale: '',
  scope: 'APPLICATION',
  blast_radius: 'LOW',
  version: '1.0.0',
  tags: [],
  tech_stack: [],
  constraints: [],
  invariants: [],
  supersedes: '',
  relations: [],
  created_by: '',
}

const STEPS = [
  { id: 1, name: 'Basic Info', description: 'Statement & Rationale' },
  { id: 2, name: 'Metadata', description: 'Scope, Tags, Tech Stack' },
  { id: 3, name: 'Constraints', description: 'Rules & Invariants' },
  { id: 4, name: 'Relations', description: 'Dependencies & Links' },
  { id: 5, name: 'Review', description: 'Validate & Submit' },
]

const SCOPES = ['APPLICATION', 'DOMAIN', 'ORGANIZATION']
const BLAST_RADII = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const COMMON_TAGS = ['FE', 'BE', 'DB', 'INFRA', 'CICD', 'API', 'SECURITY', 'DEVOPS']
const COMMON_TECH = ['React', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes', 'TypeScript', 'Python']

// =============================================================================
// Component
// =============================================================================

export default function DecisionWizard() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [state, setState] = useState<WizardState>(initialState)
  const [validation, setValidation] = useState<EnhancedValidationResponse | null>(null)
  const [autoValidate] = useState(true)

  // Fetch existing decisions for relation selection
  const { data: decisions } = useQuery({
    queryKey: ['decisions-for-wizard'],
    queryFn: () => decisionsApi.list({ limit: 500 }),
  })

  // Enhanced validation mutation
  const validateMutation = useMutation({
    mutationFn: () => {
      const record = buildDecisionRecord()
      return enhancedValidationApi.validate({
        record,
        authorship_metadata: {
          author: state.created_by || 'wizard-user',
          author_type: 'human',
        },
        arbitration_mode: 'DELEGATED',
      })
    },
    onSuccess: (data) => {
      setValidation(data)
    },
  })

  // Store decision mutation
  const storeMutation = useMutation({
    mutationFn: async () => {
      const decision = buildDecisionRecord() as DecisionCreate
      return decisionsApi.store(
        decision,
        state.created_by || 'wizard-user',
        validation?.decision_id || undefined
      )
    },
    onSuccess: (data) => {
      if (data.result === 'STORED' && data.decision_id) {
        navigate(`/decisions/${data.decision_id}`)
      }
    },
  })

  // Build decision record from wizard state
  const buildDecisionRecord = () => ({
    domain_id: state.domain_id,
    aspect_id: state.aspect_id,
    statement: state.statement,
    rationale: state.rationale,
    scope: state.scope,
    blast_radius: state.blast_radius,
    version: state.version,
    tags: state.tags,
    tech_stack: state.tech_stack,
    constraints: state.constraints,
    invariants: state.invariants,
    supersedes: state.supersedes || null,
    relations: state.relations,
    created_by: state.created_by || 'wizard-user',
  })

  // Auto-validate on step 5
  useEffect(() => {
    if (currentStep === 5 && autoValidate && !validateMutation.isPending) {
      validateMutation.mutate()
    }
  }, [currentStep])

  const updateState = (updates: Partial<WizardState>) => {
    setState((prev) => ({ ...prev, ...updates }))
  }

  const canProceed = (): boolean => {
    switch (currentStep) {
      case 1:
        return !!state.domain_id && !!state.aspect_id && state.statement.length >= 20 && state.rationale.length >= 20
      case 2:
        return !!state.scope && !!state.blast_radius && !!state.version
      case 3:
        return true // Optional
      case 4:
        return true // Optional
      case 5:
        return validation?.result === 'READY' || validation?.result === 'PENDING_APPROVAL'
      default:
        return false
    }
  }

  const handleNext = () => {
    if (canProceed() && currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = () => {
    if (validation?.result === 'READY') {
      storeMutation.mutate()
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create New Decision</h1>
        <p className="mt-2 text-gray-600">
          Follow the wizard to create a well-structured decision with validation
        </p>
      </div>

      {/* Progress Steps */}
      <nav className="bg-white rounded-lg shadow-sm border p-4">
        <ol className="flex items-center">
          {STEPS.map((step, idx) => (
            <li key={step.id} className={clsx('flex items-center', idx < STEPS.length - 1 && 'flex-1')}>
              <button
                onClick={() => step.id <= currentStep && setCurrentStep(step.id)}
                disabled={step.id > currentStep}
                className={clsx(
                  'flex items-center gap-2 text-sm font-medium transition-colors',
                  step.id === currentStep && 'text-indigo-600',
                  step.id < currentStep && 'text-green-600 cursor-pointer',
                  step.id > currentStep && 'text-gray-400 cursor-not-allowed'
                )}
              >
                <span
                  className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
                    step.id === currentStep && 'bg-indigo-600 text-white',
                    step.id < currentStep && 'bg-green-600 text-white',
                    step.id > currentStep && 'bg-gray-200 text-gray-500'
                  )}
                >
                  {step.id < currentStep ? '✓' : step.id}
                </span>
                <div className="hidden sm:block">
                  <div className="font-medium">{step.name}</div>
                  <div className="text-xs text-gray-500">{step.description}</div>
                </div>
              </button>
              {idx < STEPS.length - 1 && (
                <div className={clsx('flex-1 h-0.5 mx-4', step.id < currentStep ? 'bg-green-600' : 'bg-gray-200')} />
              )}
            </li>
          ))}
        </ol>
      </nav>

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        {currentStep === 1 && (
          <Step1BasicInfo state={state} updateState={updateState} />
        )}
        {currentStep === 2 && (
          <Step2Metadata state={state} updateState={updateState} />
        )}
        {currentStep === 3 && (
          <Step3Constraints state={state} updateState={updateState} />
        )}
        {currentStep === 4 && (
          <Step4Relations state={state} updateState={updateState} decisions={decisions?.decisions || []} />
        )}
        {currentStep === 5 && (
          <Step5Review
            state={state}
            validation={validation}
            isValidating={validateMutation.isPending}
            onRevalidate={() => validateMutation.mutate()}
          />
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className={clsx(
            'px-4 py-2 rounded-lg font-medium transition-colors',
            currentStep === 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          Back
        </button>

        <div className="flex gap-3">
          {currentStep === 5 ? (
            <button
              onClick={handleSubmit}
              disabled={!canProceed() || storeMutation.isPending}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors',
                canProceed()
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              )}
            >
              {storeMutation.isPending ? 'Storing...' : 'Store Decision'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors',
                canProceed()
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              )}
            >
              Next
            </button>
          )}
        </div>
      </div>

      {/* Store Error */}
      {storeMutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Error: {(storeMutation.error as Error).message}</p>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Step Components
// =============================================================================

function Step1BasicInfo({
  state,
  updateState,
}: {
  state: WizardState
  updateState: (updates: Partial<WizardState>) => void
}) {
  const aspectsForDomain = state.domain_id ? ASPECTS[state.domain_id] || [] : []

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

      {/* Domain & Aspect */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Decision Domain <span className="text-red-500">*</span>
          </label>
          <select
            value={state.domain_id}
            onChange={(e) => updateState({ domain_id: e.target.value, aspect_id: '' })}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select domain...</option>
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {d} - {DOMAIN_LABELS[d]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Aspect <span className="text-red-500">*</span>
          </label>
          <select
            value={state.aspect_id}
            onChange={(e) => updateState({ aspect_id: e.target.value })}
            disabled={!state.domain_id}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
          >
            <option value="">Select aspect...</option>
            {aspectsForDomain.map((a) => (
              <option key={a} value={a}>
                {a} - {ASPECT_LABELS[a]}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Cell Preview */}
      {state.domain_id && state.aspect_id && (
        <div
          className="p-4 rounded-lg border-2"
          style={{ borderColor: DOMAIN_COLORS[state.domain_id] || '#6B7280' }}
        >
          <div className="text-sm text-gray-500">Selected Cell</div>
          <div className="font-bold text-lg">
            {state.domain_id} / {state.aspect_id}
          </div>
          <div className="text-sm text-gray-600">
            {DOMAIN_LABELS[state.domain_id]} - {ASPECT_LABELS[state.aspect_id]}
          </div>
        </div>
      )}

      {/* Statement */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Statement <span className="text-red-500">*</span>
          <span className="text-gray-400 ml-2">({state.statement.length} chars, min 20)</span>
        </label>
        <textarea
          value={state.statement}
          onChange={(e) => updateState({ statement: e.target.value })}
          placeholder="A clear, actionable statement of what SHALL or SHALL NOT be done..."
          rows={3}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
        />
        <p className="mt-1 text-xs text-gray-500">
          Use SHALL for requirements, SHALL NOT for prohibitions. Be specific and measurable.
        </p>
      </div>

      {/* Rationale */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Rationale <span className="text-red-500">*</span>
          <span className="text-gray-400 ml-2">({state.rationale.length} chars, min 20)</span>
        </label>
        <textarea
          value={state.rationale}
          onChange={(e) => updateState({ rationale: e.target.value })}
          placeholder="Why this decision was made. Include context, alternatives considered, and trade-offs..."
          rows={4}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Author */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={state.created_by}
          onChange={(e) => updateState({ created_by: e.target.value })}
          placeholder="Enter your name"
          className="w-full md:w-1/2 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  )
}

function Step2Metadata({
  state,
  updateState,
}: {
  state: WizardState
  updateState: (updates: Partial<WizardState>) => void
}) {
  const [tagInput, setTagInput] = useState('')
  const [techInput, setTechInput] = useState('')

  const addTag = (tag: string) => {
    if (tag && !state.tags.includes(tag)) {
      updateState({ tags: [...state.tags, tag] })
    }
    setTagInput('')
  }

  const removeTag = (tag: string) => {
    updateState({ tags: state.tags.filter((t) => t !== tag) })
  }

  const addTech = (tech: string) => {
    if (tech && !state.tech_stack.includes(tech)) {
      updateState({ tech_stack: [...state.tech_stack, tech] })
    }
    setTechInput('')
  }

  const removeTech = (tech: string) => {
    updateState({ tech_stack: state.tech_stack.filter((t) => t !== tech) })
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Metadata & Classification</h3>

      {/* Scope & Blast Radius */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Scope</label>
          <select
            value={state.scope}
            onChange={(e) => updateState({ scope: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            {SCOPES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Blast Radius</label>
          <select
            value={state.blast_radius}
            onChange={(e) => updateState({ blast_radius: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            {BLAST_RADII.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Version</label>
          <input
            type="text"
            value={state.version}
            onChange={(e) => updateState({ version: e.target.value })}
            placeholder="1.0.0"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Area Tags</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {COMMON_TAGS.map((tag) => (
            <button
              key={tag}
              onClick={() => (state.tags.includes(tag) ? removeTag(tag) : addTag(tag))}
              className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium transition-colors',
                state.tags.includes(tag)
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {tag}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag(tagInput))}
            placeholder="Add custom tag..."
            className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={() => addTag(tagInput)}
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Add
          </button>
        </div>
        {state.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {state.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-sm flex items-center gap-1"
              >
                {tag}
                <button onClick={() => removeTag(tag)} className="text-indigo-500 hover:text-indigo-700">
                  x
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tech Stack */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Tech Stack</label>
        <div className="flex flex-wrap gap-2 mb-2">
          {COMMON_TECH.map((tech) => (
            <button
              key={tech}
              onClick={() => (state.tech_stack.includes(tech) ? removeTech(tech) : addTech(tech))}
              className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium transition-colors',
                state.tech_stack.includes(tech)
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {tech}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={techInput}
            onChange={(e) => setTechInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTech(techInput))}
            placeholder="Add custom technology..."
            className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={() => addTech(techInput)}
            className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Add
          </button>
        </div>
        {state.tech_stack.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {state.tech_stack.map((tech) => (
              <span
                key={tech}
                className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm flex items-center gap-1"
              >
                {tech}
                <button onClick={() => removeTech(tech)} className="text-green-500 hover:text-green-700">
                  x
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Step3Constraints({
  state,
  updateState,
}: {
  state: WizardState
  updateState: (updates: Partial<WizardState>) => void
}) {
  const [constraintType, setConstraintType] = useState<'PROHIBITION' | 'REQUIREMENT' | 'LIMITATION'>('REQUIREMENT')
  const [constraintStatement, setConstraintStatement] = useState('')
  const [invariantInput, setInvariantInput] = useState('')

  const addConstraint = () => {
    if (constraintStatement.trim()) {
      const newConstraint: Constraint = {
        constraint_id: `c-${Date.now()}`,
        type: constraintType,
        statement: constraintStatement.trim(),
      }
      updateState({ constraints: [...state.constraints, newConstraint] })
      setConstraintStatement('')
    }
  }

  const removeConstraint = (id: string) => {
    updateState({ constraints: state.constraints.filter((c) => c.constraint_id !== id) })
  }

  const addInvariant = () => {
    if (invariantInput.trim() && !state.invariants.includes(invariantInput.trim())) {
      updateState({ invariants: [...state.invariants, invariantInput.trim()] })
      setInvariantInput('')
    }
  }

  const removeInvariant = (inv: string) => {
    updateState({ invariants: state.invariants.filter((i) => i !== inv) })
  }

  const constraintColors = {
    PROHIBITION: 'bg-red-100 text-red-700 border-red-200',
    REQUIREMENT: 'bg-blue-100 text-blue-700 border-blue-200',
    LIMITATION: 'bg-amber-100 text-amber-700 border-amber-200',
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Constraints & Invariants</h3>

      {/* Constraints */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Constraints</label>
        <div className="flex gap-2 mb-2">
          <select
            value={constraintType}
            onChange={(e) => setConstraintType(e.target.value as any)}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="REQUIREMENT">REQUIREMENT</option>
            <option value="PROHIBITION">PROHIBITION</option>
            <option value="LIMITATION">LIMITATION</option>
          </select>
          <input
            type="text"
            value={constraintStatement}
            onChange={(e) => setConstraintStatement(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addConstraint())}
            placeholder="Enter constraint statement..."
            className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={addConstraint}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Add
          </button>
        </div>

        {state.constraints.length > 0 && (
          <div className="space-y-2">
            {state.constraints.map((c) => (
              <div key={c.constraint_id} className={clsx('p-3 rounded-lg border', constraintColors[c.type])}>
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-bold">{c.type}</span>
                    <p className="text-sm mt-1">{c.statement}</p>
                  </div>
                  <button
                    onClick={() => removeConstraint(c.constraint_id)}
                    className="text-gray-500 hover:text-red-600"
                  >
                    x
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {state.constraints.length === 0 && (
          <p className="text-sm text-gray-500 italic">No constraints added (optional)</p>
        )}
      </div>

      {/* Invariants */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Invariants</label>
        <p className="text-xs text-gray-500 mb-2">
          Properties that must ALWAYS be true, regardless of system state
        </p>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={invariantInput}
            onChange={(e) => setInvariantInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addInvariant())}
            placeholder="e.g., All API responses must include request_id"
            className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={addInvariant}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Add
          </button>
        </div>

        {state.invariants.length > 0 && (
          <div className="space-y-2">
            {state.invariants.map((inv) => (
              <div key={inv} className="p-3 rounded-lg border bg-purple-50 text-purple-700 border-purple-200">
                <div className="flex justify-between items-center">
                  <p className="text-sm">{inv}</p>
                  <button onClick={() => removeInvariant(inv)} className="text-purple-500 hover:text-red-600">
                    x
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {state.invariants.length === 0 && (
          <p className="text-sm text-gray-500 italic">No invariants added (optional)</p>
        )}
      </div>
    </div>
  )
}

function Step4Relations({
  state,
  updateState,
  decisions,
}: {
  state: WizardState
  updateState: (updates: Partial<WizardState>) => void
  decisions: any[]
}) {
  const [relationType, setRelationType] = useState<'depends_on' | 'conflicts_with' | 'informed_by'>('depends_on')
  const [targetId, setTargetId] = useState('')

  const addRelation = () => {
    if (targetId && !state.relations.some((r) => r.target_id === targetId)) {
      updateState({
        relations: [...state.relations, { target_id: targetId, type: relationType }],
      })
      setTargetId('')
    }
  }

  const removeRelation = (targetId: string) => {
    updateState({ relations: state.relations.filter((r) => r.target_id !== targetId) })
  }

  const relationColors = {
    depends_on: 'bg-blue-100 text-blue-700',
    conflicts_with: 'bg-red-100 text-red-700',
    informed_by: 'bg-green-100 text-green-700',
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Relations & Dependencies</h3>

      {/* Supersedes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Supersedes (Replaces)</label>
        <p className="text-xs text-gray-500 mb-2">
          If this decision replaces an existing one, select it here
        </p>
        <select
          value={state.supersedes}
          onChange={(e) => updateState({ supersedes: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">None (new decision)</option>
          {decisions.map((d) => (
            <option key={d.decision_id} value={d.decision_id}>
              {d.decision_code || d.decision_id.slice(0, 8)} - {d.statement.slice(0, 50)}...
            </option>
          ))}
        </select>
      </div>

      {/* Relations */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Relations</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
          <select
            value={relationType}
            onChange={(e) => setRelationType(e.target.value as any)}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            <option value="depends_on">Depends On</option>
            <option value="conflicts_with">Conflicts With</option>
            <option value="informed_by">Informed By</option>
          </select>
          <select
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 md:col-span-2"
          >
            <option value="">Select decision...</option>
            {decisions.map((d) => (
              <option key={d.decision_id} value={d.decision_id}>
                {d.decision_code || d.decision_id.slice(0, 8)} - {d.statement.slice(0, 40)}...
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={addRelation}
          disabled={!targetId}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300"
        >
          Add Relation
        </button>

        {state.relations.length > 0 && (
          <div className="mt-4 space-y-2">
            {state.relations.map((rel) => {
              const target = decisions.find((d) => d.decision_id === rel.target_id)
              return (
                <div
                  key={rel.target_id}
                  className={clsx('p-3 rounded-lg flex justify-between items-center', relationColors[rel.type])}
                >
                  <div>
                    <span className="text-xs font-bold uppercase">{rel.type.replace('_', ' ')}</span>
                    <p className="text-sm font-mono">
                      {target?.decision_code || rel.target_id.slice(0, 8)}
                    </p>
                  </div>
                  <button onClick={() => removeRelation(rel.target_id)} className="hover:text-red-600">
                    x
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {state.relations.length === 0 && (
          <p className="text-sm text-gray-500 italic mt-2">No relations added (optional)</p>
        )}
      </div>
    </div>
  )
}

function Step5Review({
  state,
  validation,
  isValidating,
  onRevalidate,
}: {
  state: WizardState
  validation: EnhancedValidationResponse | null
  isValidating: boolean
  onRevalidate: () => void
}) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Review & Validate</h3>
        <button
          onClick={onRevalidate}
          disabled={isValidating}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300"
        >
          {isValidating ? 'Validating...' : 'Re-validate'}
        </button>
      </div>

      {/* Decision Preview */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-700 mb-3">Decision Preview</h4>
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-gray-500">Cell:</span>{' '}
            <span className="font-mono font-bold">
              {state.domain_id}/{state.aspect_id}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Statement:</span>{' '}
            <span className="text-gray-900">{state.statement}</span>
          </div>
          <div>
            <span className="text-gray-500">Scope:</span> {state.scope} |{' '}
            <span className="text-gray-500">Blast Radius:</span> {state.blast_radius} |{' '}
            <span className="text-gray-500">Version:</span> {state.version}
          </div>
          {state.tags.length > 0 && (
            <div>
              <span className="text-gray-500">Tags:</span> {state.tags.join(', ')}
            </div>
          )}
          {state.tech_stack.length > 0 && (
            <div>
              <span className="text-gray-500">Tech:</span> {state.tech_stack.join(', ')}
            </div>
          )}
        </div>
      </div>

      {/* Validation Results */}
      {isValidating && (
        <div className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-2 text-gray-500">Running enhanced validation...</p>
        </div>
      )}

      {validation && !isValidating && (
        <div className="space-y-4">
          {/* Result Badge */}
          <div
            className={clsx(
              'p-4 rounded-lg border',
              validation.result === 'READY' && 'bg-green-50 border-green-200',
              validation.result === 'INVALID' && 'bg-red-50 border-red-200',
              validation.result === 'PENDING_APPROVAL' && 'bg-amber-50 border-amber-200'
            )}
          >
            <div className="flex items-center gap-2">
              <span className="text-2xl">
                {validation.result === 'READY' && '✅'}
                {validation.result === 'INVALID' && '❌'}
                {validation.result === 'PENDING_APPROVAL' && '⏳'}
              </span>
              <div>
                <div className="font-bold">{validation.result}</div>
                {validation.approval_summary && (
                  <p className="text-sm">{validation.approval_summary.summary_text}</p>
                )}
              </div>
            </div>
          </div>

          {/* Quality Score */}
          {validation.quality && (
            <div className="bg-white rounded-lg border p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Quality Score</span>
                <span
                  className={clsx(
                    'font-bold text-lg',
                    validation.quality.percentage >= 80 && 'text-green-600',
                    validation.quality.percentage >= 60 && validation.quality.percentage < 80 && 'text-amber-600',
                    validation.quality.percentage < 60 && 'text-red-600'
                  )}
                >
                  {validation.quality.percentage.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={clsx(
                    'h-2 rounded-full transition-all',
                    validation.quality.percentage >= 80 && 'bg-green-600',
                    validation.quality.percentage >= 60 && validation.quality.percentage < 80 && 'bg-amber-600',
                    validation.quality.percentage < 60 && 'bg-red-600'
                  )}
                  style={{ width: `${validation.quality.percentage}%` }}
                />
              </div>
            </div>
          )}

          {/* Violations */}
          {validation.violations.length > 0 && (
            <div className="bg-red-50 rounded-lg border border-red-200 p-4">
              <h4 className="font-medium text-red-700 mb-2">
                Violations ({validation.violations.length})
              </h4>
              <ul className="space-y-1 text-sm text-red-600">
                {validation.violations.map((v, i) => (
                  <li key={i}>• {v.message}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {validation.warnings.length > 0 && (
            <div className="bg-amber-50 rounded-lg border border-amber-200 p-4">
              <h4 className="font-medium text-amber-700 mb-2">
                Warnings ({validation.warnings.length})
              </h4>
              <ul className="space-y-1 text-sm text-amber-600">
                {validation.warnings.map((w, i) => (
                  <li key={i}>• {w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata Suggestions */}
          {validation.metadata_suggestions && (
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
              <h4 className="font-medium text-blue-700 mb-2">Suggestions</h4>
              <div className="text-sm text-blue-600 space-y-1">
                {validation.metadata_suggestions.suggested_tags.length > 0 && (
                  <p>Suggested tags: {validation.metadata_suggestions.suggested_tags.join(', ')}</p>
                )}
                {validation.metadata_suggestions.suggested_tech_stack.length > 0 && (
                  <p>Suggested tech: {validation.metadata_suggestions.suggested_tech_stack.join(', ')}</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
