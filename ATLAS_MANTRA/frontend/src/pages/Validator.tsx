import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import {
  enhancedValidationApi,
  ArbitrationMode,
  ArbitrationVerdictInput,
  QualityResult,
  DuplicateResult,
  ConflictResult,
  ImpactResult,
  MetadataSuggestion,
  ApprovalSummary,
  ArbitrationContext,
  AIVerdictResult,
} from '../shared/api'
import { TAG_COLORS } from '../shared/constants'

// Sample decision per MANTRA-SCHEMA-001 v2
const EXAMPLE_DECISION = {
  decision_id: "550e8400-e29b-41d4-a716-446655440000",
  group_id: "INT",
  feature_id: "F01",
  statement: "All user authentication must use multi-factor authentication",
  rationale: "Security requirement for enterprise systems. MFA reduces unauthorized access by 99.9% according to Microsoft security research.",
  constraints: [
    {
      constraint_id: "C-001",
      statement: "MFA must support TOTP and WebAuthn",
      type: "REQUIREMENT"
    }
  ],
  invariants: ["Authentication state is immutable once established"],
  scope: "ORGANIZATION",
  blast_radius: "HIGH",
  version: "1.0.0",
  tags: ["SECURITY", "BE"],
  tech_stack: ["FastAPI", "PostgreSQL"]
}

// Arbitration Mode descriptions
const ARBITRATION_MODE_INFO: Record<ArbitrationMode, { label: string; description: string; icon: string }> = {
  DELEGATED: {
    label: 'Delegated',
    description: 'You (the user) review borderline cases',
    icon: '👤'
  },
  SERVER: {
    label: 'Server AI',
    description: 'Server AI evaluates borderline cases',
    icon: '🤖'
  },
  SKIP: {
    label: 'Skip AI',
    description: 'No AI arbitration, accept uncertainty',
    icon: '⏭️'
  }
}

export default function Validator() {
  const [input, setInput] = useState(JSON.stringify(EXAMPLE_DECISION, null, 2))
  const [arbitrationMode, setArbitrationMode] = useState<ArbitrationMode>('DELEGATED')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [pendingVerdicts, setPendingVerdicts] = useState<ArbitrationVerdictInput[]>([])

  // Get AI providers info
  const { data: providersInfo } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: () => enhancedValidationApi.getProviders(),
    retry: false,
  })

  const mutation = useMutation({
    mutationFn: (request: { record: object; arbitration_verdicts?: ArbitrationVerdictInput[] }) =>
      enhancedValidationApi.validate({
        record: request.record,
        arbitration_mode: arbitrationMode,
        arbitration_verdicts: request.arbitration_verdicts,
        authorship_metadata: { author: 'frontend-user', author_type: 'human' }
      }),
  })

  const approveMutation = useMutation({
    mutationFn: (proposalId: string) =>
      enhancedValidationApi.approve({
        proposal_id: proposalId,
        approved_by: 'frontend-user',
        approval_comment: 'Approved via Validator UI'
      }),
  })

  const handleValidate = () => {
    try {
      const record = JSON.parse(input)
      setPendingVerdicts([])
      mutation.mutate({ record })
    } catch {
      alert('Invalid JSON')
    }
  }

  const handleSubmitVerdicts = () => {
    try {
      const record = JSON.parse(input)
      mutation.mutate({ record, arbitration_verdicts: pendingVerdicts })
    } catch {
      alert('Invalid JSON')
    }
  }

  const handleApprove = () => {
    if (mutation.data?.proposal_id) {
      approveMutation.mutate(mutation.data.proposal_id)
    }
  }

  const addVerdict = (context: ArbitrationContext, verdict: string) => {
    const newVerdict: ArbitrationVerdictInput = {
      arbitration_type: context.arbitration_type,
      verdict: verdict as any,
      confidence: 0.8,
      reason: `User selected ${verdict} via UI`
    }
    setPendingVerdicts(prev => [...prev.filter(v => v.arbitration_type !== context.arbitration_type), newVerdict])
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Enhanced Decision Validator</h1>
        <p className="mt-2 text-gray-600">
          Validates decisions with quality scoring, duplicate detection, conflict analysis, and impact assessment
        </p>
      </div>

      {/* Validation Features Overview */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Validation Features</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-indigo-50 rounded">
            <div className="text-indigo-600 font-medium">Schema</div>
            <div className="text-gray-500">44 rules (S, D, L)</div>
          </div>
          <div className="p-3 bg-green-50 rounded">
            <div className="text-green-600 font-medium">Quality</div>
            <div className="text-gray-500">Q-001 to Q-025</div>
          </div>
          <div className="p-3 bg-amber-50 rounded">
            <div className="text-amber-600 font-medium">Duplicates</div>
            <div className="text-gray-500">Exact + Semantic</div>
          </div>
          <div className="p-3 bg-red-50 rounded">
            <div className="text-red-600 font-medium">Conflicts</div>
            <div className="text-gray-500">Relations + Keywords</div>
          </div>
        </div>
      </div>

      {/* Arbitration Mode Selector */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">AI Arbitration Mode</h3>
          {providersInfo?.is_configured && (
            <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
              🤖 {providersInfo.current_provider} configured
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 mb-4">
          AI is only called for borderline cases (quality 50-80, similarity 85-95%, medium conflicts)
        </p>
        <div className="grid grid-cols-3 gap-3">
          {(Object.keys(ARBITRATION_MODE_INFO) as ArbitrationMode[]).map(mode => (
            <button
              key={mode}
              onClick={() => setArbitrationMode(mode)}
              className={clsx(
                'p-3 rounded-lg border text-left transition-all',
                arbitrationMode === mode
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{ARBITRATION_MODE_INFO[mode].icon}</span>
                <span className="font-medium text-gray-900">{ARBITRATION_MODE_INFO[mode].label}</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">{ARBITRATION_MODE_INFO[mode].description}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Decision Record (JSON)</h3>
            <button
              onClick={() => setInput(JSON.stringify(EXAMPLE_DECISION, null, 2))}
              className="text-xs text-indigo-600 hover:text-indigo-500"
            >
              Load Example
            </button>
          </div>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full h-80 bg-gray-50 text-gray-700 font-mono text-sm p-4 rounded border border-gray-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Paste decision JSON here..."
          />
          <button
            onClick={handleValidate}
            disabled={mutation.isPending}
            className="mt-4 btn btn-primary w-full"
          >
            {mutation.isPending ? 'Validating...' : 'Validate (Enhanced)'}
          </button>
        </div>

        {/* Result Panel */}
        <div className="bg-white rounded-lg shadow-sm border p-6 overflow-auto max-h-[600px]">
          <h3 className="font-semibold text-gray-900 mb-3">Validation Result</h3>

          {mutation.data ? (
            <div className="space-y-4">
              {/* Overall Status */}
              <ResultStatus result={mutation.data.result} />

              {/* Approval Summary */}
              {mutation.data.approval_summary && (
                <ApprovalSummaryCard
                  summary={mutation.data.approval_summary}
                  onApprove={handleApprove}
                  isApproving={approveMutation.isPending}
                  approveResult={approveMutation.data}
                  proposalId={mutation.data.proposal_id}
                />
              )}

              {/* Arbitration Required */}
              {mutation.data.arbitration_required && mutation.data.arbitration_contexts && (
                <ArbitrationPanel
                  contexts={mutation.data.arbitration_contexts}
                  onAddVerdict={addVerdict}
                  pendingVerdicts={pendingVerdicts}
                  onSubmitVerdicts={handleSubmitVerdicts}
                  isPending={mutation.isPending}
                />
              )}

              {/* AI Verdicts (from SERVER mode) */}
              {mutation.data.ai_verdicts && Object.keys(mutation.data.ai_verdicts).length > 0 && (
                <AIVerdictsCard verdicts={mutation.data.ai_verdicts} />
              )}

              {/* Toggle Advanced Results */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full text-sm text-indigo-600 hover:text-indigo-500 py-2"
              >
                {showAdvanced ? '▲ Hide Details' : '▼ Show Details'}
              </button>

              {showAdvanced && (
                <>
                  {/* Quality Score */}
                  {mutation.data.quality && <QualityCard quality={mutation.data.quality} />}

                  {/* Duplicates */}
                  {mutation.data.duplicates && <DuplicatesCard duplicates={mutation.data.duplicates} />}

                  {/* Conflicts */}
                  {mutation.data.conflicts && <ConflictsCard conflicts={mutation.data.conflicts} />}

                  {/* Impact */}
                  {mutation.data.impact && <ImpactCard impact={mutation.data.impact} />}

                  {/* Metadata Suggestions */}
                  {mutation.data.metadata_suggestions && (
                    <MetadataSuggestionsCard suggestions={mutation.data.metadata_suggestions} />
                  )}
                </>
              )}

              {/* Violations */}
              {mutation.data.violations?.length > 0 && (
                <ViolationsCard violations={mutation.data.violations} />
              )}

              {/* Warnings */}
              {mutation.data.warnings?.length > 0 && (
                <WarningsCard warnings={mutation.data.warnings} />
              )}

              {/* Meta Info */}
              <div className="text-xs text-gray-400 pt-4 border-t">
                <div>Schema: {mutation.data.schema_version}</div>
                <div>Spec: {mutation.data.specification_version}</div>
                <div>Validated: {new Date(mutation.data.validated_at).toLocaleString()}</div>
                {mutation.data.proposal_id && <div>Proposal ID: {mutation.data.proposal_id.slice(0, 8)}...</div>}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              Enter a decision record and click Validate
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Component: Result Status
// =============================================================================
function ResultStatus({ result }: { result: string }) {
  const config = {
    READY: { bg: 'bg-green-100', text: 'text-green-700', label: '✅ READY' },
    INVALID: { bg: 'bg-red-100', text: 'text-red-700', label: '❌ INVALID' },
    PENDING_ARBITRATION: { bg: 'bg-amber-100', text: 'text-amber-700', label: '⏳ PENDING ARBITRATION' },
    PENDING_APPROVAL: { bg: 'bg-blue-100', text: 'text-blue-700', label: '👁️ PENDING APPROVAL' },
  }[result] || { bg: 'bg-gray-100', text: 'text-gray-700', label: result }

  return (
    <div className={clsx('p-4 rounded text-center text-lg font-bold', config.bg, config.text)}>
      {config.label}
    </div>
  )
}

// =============================================================================
// Component: Approval Summary
// =============================================================================
function ApprovalSummaryCard({
  summary,
  onApprove,
  isApproving,
  approveResult,
  proposalId
}: {
  summary: ApprovalSummary
  onApprove: () => void
  isApproving: boolean
  approveResult?: any
  proposalId?: string | null
}) {
  const recColors = {
    APPROVE: 'text-green-600',
    REJECT: 'text-red-600',
    REVIEW: 'text-amber-600'
  }

  return (
    <div className="p-4 bg-gray-50 rounded-lg border">
      <h4 className="font-medium text-gray-900 mb-2">📋 Approval Summary</h4>

      <p className="text-sm text-gray-700 mb-3">{summary.summary_text}</p>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-gray-500">Recommendation:</span>
        <span className={clsx('font-bold', recColors[summary.recommendation])}>
          {summary.recommendation}
        </span>
      </div>

      {summary.blocking_reasons.length > 0 && (
        <div className="mb-2">
          <span className="text-xs text-red-600 font-medium">Blocking:</span>
          <ul className="text-xs text-red-700 list-disc list-inside">
            {summary.blocking_reasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      {summary.warnings.length > 0 && (
        <div className="mb-2">
          <span className="text-xs text-amber-600 font-medium">Warnings:</span>
          <ul className="text-xs text-amber-700 list-disc list-inside">
            {summary.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      {approveResult ? (
        <div className={clsx(
          'p-3 rounded text-sm',
          approveResult.result === 'STORED' || approveResult.result === 'APPROVED'
            ? 'bg-green-100 text-green-700'
            : 'bg-red-100 text-red-700'
        )}>
          {approveResult.result === 'STORED' || approveResult.result === 'APPROVED' ? (
            <>
              ✅ Decision stored! Code: <span className="font-mono">{approveResult.decision_code}</span>
            </>
          ) : (
            <>❌ {approveResult.message || approveResult.result}</>
          )}
        </div>
      ) : (
        summary.requires_user_approval && proposalId && summary.recommendation !== 'REJECT' && (
          <button
            onClick={onApprove}
            disabled={isApproving}
            className="btn btn-primary w-full mt-2"
          >
            {isApproving ? 'Approving...' : '✅ Approve & Store Decision'}
          </button>
        )
      )}
    </div>
  )
}

// =============================================================================
// Component: Arbitration Panel
// =============================================================================
function ArbitrationPanel({
  contexts,
  onAddVerdict,
  pendingVerdicts,
  onSubmitVerdicts,
  isPending
}: {
  contexts: ArbitrationContext[]
  onAddVerdict: (context: ArbitrationContext, verdict: string) => void
  pendingVerdicts: ArbitrationVerdictInput[]
  onSubmitVerdicts: () => void
  isPending: boolean
}) {
  return (
    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
      <h4 className="font-medium text-amber-800 mb-2">⚖️ Arbitration Required</h4>
      <p className="text-sm text-amber-700 mb-4">
        The following cases need your judgment. Select a verdict for each.
      </p>

      {contexts.map((ctx, idx) => {
        const currentVerdict = pendingVerdicts.find(v => v.arbitration_type === ctx.arbitration_type)

        return (
          <div key={idx} className="bg-white p-3 rounded mb-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">
                {ctx.arbitration_type}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-2">{ctx.instructions}</p>
            <div className="flex flex-wrap gap-2">
              {ctx.expected_verdicts.map(verdict => (
                <button
                  key={verdict}
                  onClick={() => onAddVerdict(ctx, verdict)}
                  className={clsx(
                    'px-3 py-1 text-sm rounded border transition-all',
                    currentVerdict?.verdict === verdict
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-300'
                  )}
                >
                  {verdict}
                </button>
              ))}
            </div>
          </div>
        )
      })}

      <button
        onClick={onSubmitVerdicts}
        disabled={isPending || pendingVerdicts.length === 0}
        className="btn btn-primary w-full mt-2"
      >
        {isPending ? 'Submitting...' : `Submit ${pendingVerdicts.length} Verdict(s)`}
      </button>
    </div>
  )
}

// =============================================================================
// Component: AI Verdicts
// =============================================================================
function AIVerdictsCard({ verdicts }: { verdicts: Record<string, AIVerdictResult> }) {
  return (
    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
      <h4 className="font-medium text-purple-800 mb-2">🤖 AI Verdicts</h4>
      {Object.entries(verdicts).map(([type, result]) => (
        <div key={type} className="bg-white p-3 rounded mb-2">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900">{type}</span>
            <span className={clsx(
              'px-2 py-0.5 text-xs rounded',
              result.verdict.includes('APPROVE') || result.verdict === 'DIFFERENT' || result.verdict === 'NOT_CONFLICT'
                ? 'bg-green-100 text-green-700'
                : result.verdict.includes('REJECT') || result.verdict === 'DUPLICATE' || result.verdict === 'BLOCKING'
                ? 'bg-red-100 text-red-700'
                : 'bg-amber-100 text-amber-700'
            )}>
              {result.verdict}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{result.reason}</p>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
            <span>Confidence: {(result.confidence * 100).toFixed(0)}%</span>
            {result.provider && <span>• Provider: {result.provider}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}

// =============================================================================
// Component: Quality Card
// =============================================================================
function QualityCard({ quality }: { quality: QualityResult }) {
  const scoreColor = quality.percentage >= 80 ? 'text-green-600' :
                     quality.percentage >= 60 ? 'text-amber-600' : 'text-red-600'

  return (
    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-green-800">📊 Quality Score</h4>
        <span className={clsx('text-2xl font-bold', scoreColor)}>
          {quality.overall_score}/{quality.max_score} ({quality.percentage.toFixed(0)}%)
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div
          className={clsx(
            'h-2 rounded-full',
            quality.percentage >= 80 ? 'bg-green-500' :
            quality.percentage >= 60 ? 'bg-amber-500' : 'bg-red-500'
          )}
          style={{ width: `${quality.percentage}%` }}
        />
      </div>

      {/* Dimensions */}
      <div className="space-y-2">
        {quality.dimensions.map(dim => (
          <div key={dim.dimension} className="text-sm">
            <div className="flex justify-between">
              <span className="text-gray-700">{dim.dimension}</span>
              <span className="text-gray-500">{dim.scored_points}/{dim.max_points}</span>
            </div>
          </div>
        ))}
      </div>

      {quality.suggestions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-green-200">
          <p className="text-xs text-green-700 font-medium mb-1">Suggestions:</p>
          <ul className="text-xs text-green-600 list-disc list-inside">
            {quality.suggestions.slice(0, 3).map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Component: Duplicates Card
// =============================================================================
function DuplicatesCard({ duplicates }: { duplicates: DuplicateResult }) {
  if (!duplicates.has_exact_duplicate && duplicates.near_duplicates.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border">
        <h4 className="font-medium text-gray-700">🔍 Duplicates</h4>
        <p className="text-sm text-gray-500">No duplicates detected</p>
      </div>
    )
  }

  return (
    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
      <h4 className="font-medium text-amber-800 mb-2">🔍 Duplicate Detection</h4>

      {duplicates.has_exact_duplicate && (
        <div className="bg-red-100 text-red-700 p-2 rounded mb-2 text-sm">
          ⛔ Exact duplicate: {duplicates.exact_duplicate_id}
        </div>
      )}

      {duplicates.near_duplicates.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-amber-700">Near duplicates:</p>
          {duplicates.near_duplicates.map(dup => (
            <div key={dup.decision_id} className="bg-white p-2 rounded text-sm">
              <div className="flex items-center justify-between">
                <span className="font-mono text-amber-800">{dup.decision_code}</span>
                <span className="text-amber-600">{(dup.similarity * 100).toFixed(0)}% similar</span>
              </div>
              <p className="text-gray-500 text-xs mt-1 truncate">{dup.statement_preview}</p>
            </div>
          ))}
        </div>
      )}

      {duplicates.supersedes_guidance && (
        <div className="mt-3 p-2 bg-blue-100 rounded text-sm">
          <p className="text-blue-800 font-medium">💡 {duplicates.supersedes_guidance.recommendation}</p>
          <p className="text-blue-700 text-xs">{duplicates.supersedes_guidance.message}</p>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Component: Conflicts Card
// =============================================================================
function ConflictsCard({ conflicts }: { conflicts: ConflictResult }) {
  if (conflicts.conflicts.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border">
        <h4 className="font-medium text-gray-700">⚡ Conflicts</h4>
        <p className="text-sm text-gray-500">No conflicts detected</p>
      </div>
    )
  }

  const severityColors = {
    CRITICAL: 'bg-red-100 text-red-700 border-red-200',
    HIGH: 'bg-orange-100 text-orange-700 border-orange-200',
    MEDIUM: 'bg-amber-100 text-amber-700 border-amber-200',
    LOW: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  }

  return (
    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
      <h4 className="font-medium text-red-800 mb-2">⚡ Conflicts ({conflicts.conflicts.length})</h4>

      {conflicts.blocking_conflicts.length > 0 && (
        <div className="mb-2 p-2 bg-red-100 rounded text-sm text-red-700">
          ⛔ {conflicts.blocking_conflicts.length} blocking conflict(s)
        </div>
      )}

      <div className="space-y-2">
        {conflicts.conflicts.map((c, idx) => (
          <div key={idx} className={clsx('p-2 rounded border text-sm', severityColors[c.severity])}>
            <div className="flex items-center justify-between">
              <span className="font-mono">{c.decision_code}</span>
              <span className="text-xs">{c.severity}</span>
            </div>
            <p className="text-xs mt-1">{c.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Component: Impact Card
// =============================================================================
function ImpactCard({ impact }: { impact: ImpactResult }) {
  const levelColors = {
    MINIMAL: 'text-green-600',
    LOW: 'text-green-600',
    MODERATE: 'text-amber-600',
    HIGH: 'text-orange-600',
    CRITICAL: 'text-red-600',
  }

  return (
    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
      <h4 className="font-medium text-blue-800 mb-2">🎯 Impact Analysis</h4>

      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div>
          <span className="text-gray-500">Risk Level:</span>
          <span className={clsx('ml-2 font-bold', levelColors[impact.risk_level])}>
            {impact.risk_level}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Score:</span>
          <span className="ml-2 font-mono">{impact.combined_risk_score}/100</span>
        </div>
      </div>

      {impact.risk_mismatch && (
        <div className="p-2 bg-amber-100 rounded text-sm text-amber-700 mb-2">
          ⚠️ {impact.risk_mismatch_warning}
        </div>
      )}

      <div className="text-xs text-gray-500">
        <div>Declared: {impact.declared_risk_score} | Calculated: {impact.calculated_risk_score}</div>
        <div>Affected decisions: {impact.affected_decisions.length}</div>
        <div>Breaking changes: {impact.breaking_changes.length}</div>
      </div>
    </div>
  )
}

// =============================================================================
// Component: Metadata Suggestions Card
// =============================================================================
function MetadataSuggestionsCard({ suggestions }: { suggestions: MetadataSuggestion }) {
  return (
    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
      <h4 className="font-medium text-purple-800 mb-2">💡 Metadata Suggestions</h4>

      <div className="space-y-2 text-sm">
        {suggestions.suggested_tags.length > 0 && (
          <div>
            <span className="text-gray-600">Tags: </span>
            <div className="flex flex-wrap gap-1 mt-1">
              {suggestions.suggested_tags.map(tag => (
                <span key={tag} className={clsx('px-2 py-0.5 rounded text-xs', TAG_COLORS[tag] || 'bg-gray-100 text-gray-700')}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {suggestions.suggested_tech_stack.length > 0 && (
          <div>
            <span className="text-gray-600">Tech Stack: </span>
            <span className="text-purple-700">{suggestions.suggested_tech_stack.join(', ')}</span>
          </div>
        )}

        <div>
          <span className="text-gray-600">Blast Radius: </span>
          <span className="font-medium text-purple-700">{suggestions.suggested_blast_radius}</span>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Component: Violations Card
// =============================================================================
function ViolationsCard({ violations }: { violations: any[] }) {
  return (
    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
      <h4 className="font-medium text-red-800 mb-2">❌ Violations ({violations.length})</h4>
      <div className="space-y-2 max-h-40 overflow-auto">
        {violations.map((v, i) => (
          <div key={i} className="p-2 bg-white rounded text-sm">
            <div className="flex items-center gap-2">
              <span className="text-red-600 font-mono">{v.rule_id}</span>
              {v.field && <span className="text-gray-400">{v.field}</span>}
            </div>
            <p className="text-gray-700 mt-1">{v.message}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// =============================================================================
// Component: Warnings Card
// =============================================================================
function WarningsCard({ warnings }: { warnings: string[] }) {
  return (
    <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
      <h4 className="font-medium text-amber-800 mb-2">⚠️ Warnings ({warnings.length})</h4>
      <ul className="text-sm text-amber-700 list-disc list-inside">
        {warnings.map((w, i) => <li key={i}>{w}</li>)}
      </ul>
    </div>
  )
}
