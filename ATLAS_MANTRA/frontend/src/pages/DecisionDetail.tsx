import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { decisionsApi, Decision, ChallengeRequest } from '../shared/api'
import { DOMAIN_LABELS, ASPECT_LABELS, TAG_LABELS, TAG_COLORS } from '../shared/constants'
import { useState } from 'react'
import { SkeletonDecisionDetail } from '../components/ui/skeleton'
import { InfoTooltip } from '../components/ui/tooltip'
import { HintsButton } from '../components/ai'

export default function DecisionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showChallengeForm, setShowChallengeForm] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const { data: decision, isLoading, error } = useQuery({
    queryKey: ['decision', id],
    queryFn: () => decisionsApi.get(id!),
    enabled: !!id,
  })

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['decision-history', id],
    queryFn: () => decisionsApi.history(id!, 'frontend-user'),
    enabled: !!id && showHistory,
  })

  const [challengeError, setChallengeError] = useState<string | null>(null)

  const challengeMutation = useMutation({
    mutationFn: (request: ChallengeRequest) => decisionsApi.challenge(id!, request),
    onSuccess: (result) => {
      setChallengeError(null)
      queryClient.invalidateQueries({ queryKey: ['decisions'] })
      queryClient.invalidateQueries({ queryKey: ['decision', id] })
      queryClient.invalidateQueries({ queryKey: ['audit'] })
      navigate(`/decisions/${result.new_decision_id}`)
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.message || 'Challenge failed'
      setChallengeError(message)
    },
  })

  if (isLoading) {
    return <SkeletonDecisionDetail />
  }

  if (error || !decision) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl text-red-600">Decision not found</h2>
        <Link to="/decisions" className="text-indigo-600 mt-4 inline-block">
          Back to decisions
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb Navigation */}
      <nav className="flex items-center space-x-2 text-sm">
        <Link to="/" className="text-gray-500 hover:text-gray-700">Home</Link>
        <span className="text-gray-300">/</span>
        <Link to="/decisions" className="text-gray-500 hover:text-gray-700">Decisions</Link>
        <span className="text-gray-300">/</span>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          (decision.domain_id || (decision as any).group_id) === 'INT' ? 'bg-blue-100 text-blue-800' :
          (decision.domain_id || (decision as any).group_id) === 'ARCH' ? 'bg-green-100 text-green-800' :
          (decision.domain_id || (decision as any).group_id) === 'CTL' ? 'bg-purple-100 text-purple-800' :
          'bg-orange-100 text-orange-800'
        }`}>
          {DOMAIN_LABELS[decision.domain_id || (decision as any).group_id]}
        </span>
        <span className="text-gray-300">/</span>
        <span className="text-gray-700 font-medium">{decision.aspect_id || (decision as any).feature_id}</span>
      </nav>

      {/* Decision Code Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            {/* Primary: Decision Code */}
            <h1 className="text-3xl font-bold font-mono tracking-wide">
              {decision.decision_code || `DEC-${decision.decision_id.slice(0, 8)}`}
            </h1>

            {/* Domain & Aspect Labels */}
            <div className="flex items-center gap-3 mt-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                (decision.domain_id || (decision as any).group_id) === 'INT' ? 'bg-blue-200 text-blue-900' :
                (decision.domain_id || (decision as any).group_id) === 'ARCH' ? 'bg-green-200 text-green-900' :
                (decision.domain_id || (decision as any).group_id) === 'CTL' ? 'bg-purple-200 text-purple-900' :
                'bg-orange-200 text-orange-900'
              }`}>
                {DOMAIN_LABELS[decision.domain_id || (decision as any).group_id]}
              </span>
              <span className="text-indigo-200">-</span>
              <span className="text-indigo-100">
                {decision.aspect_id || (decision as any).feature_id}: {ASPECT_LABELS[decision.aspect_id || (decision as any).feature_id]}
              </span>
            </div>

            {/* Version Info */}
            <div className="flex items-center gap-4 mt-3 text-indigo-200 text-sm">
              <span className="font-mono bg-indigo-900/50 px-2 py-1 rounded">v{decision.version}</span>
              <span>by {decision.created_by || 'Unknown'}</span>
              {decision.created_at && (
                <span>{new Date(decision.created_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>

          {/* Blast Radius Badge */}
          <span className={`px-4 py-2 rounded-lg text-sm font-bold ${
            decision.blast_radius === 'CRITICAL' ? 'bg-red-500 text-white' :
            decision.blast_radius === 'HIGH' ? 'bg-orange-500 text-white' :
            decision.blast_radius === 'MEDIUM' ? 'bg-yellow-500 text-yellow-900' :
            'bg-green-500 text-white'
          }`}>
            {decision.blast_radius}
          </span>
        </div>

        {/* UUID (secondary) */}
        <div className="mt-4 pt-4 border-t border-indigo-500/30">
          <span className="text-xs text-indigo-300">UUID: </span>
          <span className="text-xs font-mono text-indigo-200">{decision.decision_id}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <Link
          to="/decisions"
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to List
        </Link>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {showHistory ? 'Hide History' : 'Show History'}
          </button>
          <button
            onClick={() => setShowChallengeForm(!showChallengeForm)}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Challenge
          </button>
        </div>
      </div>

      {/* Version History Panel */}
      {showHistory && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Version History ({historyData?.total_versions ?? 0} versions)
          </h3>
          {historyLoading ? (
            <div className="text-blue-600">Loading history...</div>
          ) : historyData?.chain?.length ? (
            <div className="space-y-3">
              {historyData.chain.map((dec: Decision) => (
                <div
                  key={dec.decision_id}
                  className={`p-4 rounded-lg ${dec.decision_id === id ? 'bg-blue-100 border-2 border-blue-400' : 'bg-white border'}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm text-blue-800 font-semibold">
                        {dec.decision_code || dec.decision_id.slice(0, 8)}
                      </span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                        v{dec.version}
                      </span>
                      <span className="text-sm text-gray-600">by {dec.created_by}</span>
                      <span className="text-xs text-gray-400">
                        {new Date(dec.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {dec.decision_id === id ? (
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">Current</span>
                    ) : (
                      <Link
                        to={`/decisions/${dec.decision_id}`}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        View
                      </Link>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 mt-2 line-clamp-2">{dec.statement}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500">No version history available</div>
          )}
        </div>
      )}

      {/* Challenge Form */}
      {showChallengeForm && (
        <>
          {challengeError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <strong>Error:</strong> {challengeError}
            </div>
          )}
          <ChallengeForm
            decision={decision}
            onSubmit={(request) => {
              setChallengeError(null)
              challengeMutation.mutate(request)
            }}
            onCancel={() => {
              setChallengeError(null)
              setShowChallengeForm(false)
            }}
            isSubmitting={challengeMutation.isPending}
          />
        </>
      )}

      {/* Statement & Rationale */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Statement
        </h3>
        <p className="text-gray-700 text-lg leading-relaxed">{decision.statement}</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Rationale
        </h3>
        <p className="text-gray-700 whitespace-pre-wrap">{decision.rationale}</p>
      </div>

      {/* Metadata Grid */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Metadata</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide flex items-center gap-1">
              Scope
              <InfoTooltip content="APPLICATION (local), TEAM, DEPARTMENT, ORGANIZATION (global)" />
            </label>
            <p className="text-gray-900 font-medium">{decision.scope}</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide flex items-center gap-1">
              Blast Radius
              <InfoTooltip content="CRITICAL (org-wide impact), HIGH (multi-team), MEDIUM (team), LOW (component)" />
            </label>
            <span className={`inline-flex px-2 py-1 rounded text-sm font-medium ${
              decision.blast_radius === 'CRITICAL' ? 'bg-red-100 text-red-800' :
              decision.blast_radius === 'HIGH' ? 'bg-orange-100 text-orange-800' :
              decision.blast_radius === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {decision.blast_radius}
            </span>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide">Created By</label>
            <p className="text-gray-900">{decision.created_by || 'Unknown'}</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide">Created At</label>
            <p className="text-gray-900">
              {decision.created_at ? new Date(decision.created_at).toLocaleString() : 'Unknown'}
            </p>
          </div>
        </div>
      </div>

      {/* Tags & Tech Stack */}
      <div className="grid grid-cols-2 gap-6">
        {/* Area Tags */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            Area Tags
          </h3>
          {decision.tags?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {decision.tags.map((tag: string) => (
                <Link
                  key={tag}
                  to={`/tech-stack?tag=${tag}`}
                  className={`px-3 py-1 rounded-full text-sm font-medium cursor-pointer hover:opacity-80 transition-opacity ${TAG_COLORS[tag] || 'bg-gray-100 text-gray-700'}`}
                  title={`View all ${TAG_LABELS[tag] || tag} decisions`}
                >
                  {TAG_LABELS[tag] || tag}
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No tags assigned</p>
          )}
        </div>

        {/* Tech Stack */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Tech Stack
          </h3>
          {decision.tech_stack?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {decision.tech_stack.map((tech: string) => (
                <span
                  key={tech}
                  className="px-3 py-1 bg-gray-100 rounded text-sm text-gray-700"
                >
                  {tech}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No tech stack specified</p>
          )}
        </div>
      </div>

      {/* Version Chain */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Version Chain
        </h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide">Supersedes</label>
            {decision.supersedes ? (
              <Link
                to={`/decisions/${decision.supersedes}`}
                className="text-indigo-600 hover:text-indigo-500 font-mono block mt-1"
              >
                {decision.supersedes.slice(0, 12)}...
              </Link>
            ) : (
              <p className="text-gray-400 mt-1">None (original decision)</p>
            )}
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wide">Related Decisions</label>
            {decision.related_decisions?.length > 0 ? (
              <div className="space-y-1 mt-1">
                {decision.related_decisions.map((rel: string) => (
                  <Link
                    key={rel}
                    to={`/decisions/${rel}`}
                    className="text-indigo-600 hover:text-indigo-500 font-mono block text-sm"
                  >
                    {rel.slice(0, 12)}...
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 mt-1">None</p>
            )}
          </div>
        </div>
      </div>

      {/* Constraints */}
      {decision.constraints?.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Constraints ({decision.constraints.length})
          </h3>
          <div className="space-y-3">
            {decision.constraints.map((c: any, i: number) => (
              <div key={i} className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-sm font-mono text-gray-600">{c.constraint_id}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    c.type === 'PROHIBITION' ? 'bg-red-100 text-red-700' :
                    c.type === 'REQUIREMENT' ? 'bg-blue-100 text-blue-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>{c.type}</span>
                </div>
                <p className="text-gray-700">{c.statement}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Invariants */}
      {decision.invariants?.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Invariants ({decision.invariants.length})
          </h3>
          <ul className="space-y-2">
            {decision.invariants.map((inv: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-gray-700">
                <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {inv}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// Challenge Form Component
function ChallengeForm({
  decision,
  onSubmit,
  onCancel,
  isSubmitting
}: {
  decision: Decision
  onSubmit: (request: ChallengeRequest) => void
  onCancel: () => void
  isSubmitting: boolean
}) {
  const [challenger, setChallenger] = useState('')
  const [rationale, setRationale] = useState('')
  const [newStatement, setNewStatement] = useState(decision.statement)
  const [newRationale, setNewRationale] = useState(decision.rationale)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Calculate new version
    const currentParts = decision.version.split('.').map(Number)
    const newVersion = `${currentParts[0]}.${currentParts[1] + 1}.0`

    onSubmit({
      challenger,
      challenge_rationale: rationale,
      proposed_replacement: {
        // Support both new (domain_id/aspect_id) and old (group_id/feature_id) API field names
        domain_id: decision.domain_id || (decision as any).group_id,
        aspect_id: decision.aspect_id || (decision as any).feature_id,
        group_id: decision.domain_id || (decision as any).group_id,
        feature_id: decision.aspect_id || (decision as any).feature_id,
        statement: newStatement,
        rationale: newRationale,
        constraints: decision.constraints,
        invariants: decision.invariants,
        scope: decision.scope,
        blast_radius: decision.blast_radius,
        version: newVersion,
        created_by: challenger,
        supersedes: decision.decision_id,
        related_decisions: [decision.decision_id],
      },
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-orange-50 border border-orange-200 rounded-lg p-6">
      <h3 className="font-semibold text-orange-900 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        Challenge Decision: {decision.decision_code || decision.decision_id.slice(0, 12)}
      </h3>

      <p className="text-sm text-orange-700 mb-4">
        Challenging creates a <strong>new decision</strong> that supersedes this one.
        The original decision remains immutable in the system.
      </p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Your Name (Challenger) *
          </label>
          <input
            type="text"
            value={challenger}
            onChange={(e) => setChallenger(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            placeholder="e.g., John Smith"
            required
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              Why are you challenging? *
            </label>
            <HintsButton
              text={rationale}
              fieldType="challenge_rationale"
              context={{ decision_id: decision.decision_id, domain_id: decision.domain_id || (decision as any).group_id }}
              onApplyGrammar={(corrected) => setRationale(corrected)}
            />
          </div>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            rows={2}
            placeholder="Explain the reason for this challenge..."
            required
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              New Statement *
            </label>
            <HintsButton
              text={newStatement}
              fieldType="statement"
              context={{ decision_id: decision.decision_id, domain_id: decision.domain_id || (decision as any).group_id, aspect_id: decision.aspect_id || (decision as any).feature_id }}
              onApplyGrammar={(corrected) => setNewStatement(corrected)}
            />
          </div>
          <textarea
            value={newStatement}
            onChange={(e) => setNewStatement(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            rows={2}
            required
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              New Rationale *
            </label>
            <HintsButton
              text={newRationale}
              fieldType="rationale"
              context={{ decision_id: decision.decision_id, domain_id: decision.domain_id || (decision as any).group_id, aspect_id: decision.aspect_id || (decision as any).feature_id }}
              onApplyGrammar={(corrected) => setNewRationale(corrected)}
            />
          </div>
          <textarea
            value={newRationale}
            onChange={(e) => setNewRationale(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
            rows={3}
            required
          />
        </div>

        <div className="flex items-center gap-3 pt-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Challenge'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </form>
  )
}
