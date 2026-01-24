import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { api } from '../shared/api'

// Sample decision per MANTRA-SCHEMA-001 v2 (no status field)
const EXAMPLE_DECISION = {
  decision_id: "550e8400-e29b-41d4-a716-446655440000",
  group_id: "GROUP-1",
  feature_id: "F-01",
  statement: "All user authentication must use multi-factor authentication",
  rationale: "Security requirement for enterprise systems",
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
  version: "1.0.0"
}

export default function Validator() {
  const [input, setInput] = useState(JSON.stringify(EXAMPLE_DECISION, null, 2))

  const mutation = useMutation({
    mutationFn: (record: object) =>
      api.post('/api/v1/validate', { record }).then(r => r.data),
  })

  const handleValidate = () => {
    try {
      const record = JSON.parse(input)
      mutation.mutate(record)
    } catch {
      alert('Invalid JSON')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Decision Validator</h1>
        <p className="mt-2 text-gray-600">
          Validates decision records against MANTRA-SCHEMA-001 v2 and MANTRA-SPEC-001 v1.2.0
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">44 Validation Rules</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="p-3 bg-gray-50 rounded">
            <div className="text-indigo-600 font-medium">Level 1: Schema</div>
            <div className="text-gray-500">S-001 to S-022 (20 active)</div>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <div className="text-indigo-600 font-medium">Level 2: Consistency</div>
            <div className="text-gray-500">D-001 to D-014 (14 rules)</div>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <div className="text-indigo-600 font-medium">Level 3: Law Compliance</div>
            <div className="text-gray-500">L-001 to L-011 (10 active)</div>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Note: S-019, S-020, L-007 deprecated per AMENDMENT-001 (status field removed)
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
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
            {mutation.isPending ? 'Validating...' : 'Validate'}
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Validation Result</h3>
          {mutation.data ? (
            <div className="space-y-4">
              <div
                className={clsx(
                  'p-4 rounded text-center text-lg font-bold',
                  mutation.data.status === 'VALID' ? 'bg-green-100 text-green-700' :
                  mutation.data.status === 'INVALID' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                )}
              >
                {mutation.data.status}
              </div>

              {mutation.data.violations?.length > 0 && (
                <div>
                  <h4 className="text-gray-500 text-sm mb-2">Violations</h4>
                  <div className="space-y-2 max-h-40 overflow-auto">
                    {mutation.data.violations.map((v: any, i: number) => (
                      <div key={i} className="p-2 bg-red-50 rounded text-sm">
                        <div className="flex items-center space-x-2">
                          <span className="text-red-600 font-mono">{v.rule_id}</span>
                          <span className="text-gray-500">{v.field}</span>
                        </div>
                        <p className="text-gray-700 mt-1">{v.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {mutation.data.skipped_rules?.length > 0 && (
                <div>
                  <h4 className="text-gray-500 text-sm mb-2">Skipped Rules</h4>
                  <div className="flex flex-wrap gap-2">
                    {mutation.data.skipped_rules.map((r: string) => (
                      <span key={r} className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-500">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {mutation.data.advisory_notes?.length > 0 && (
                <div>
                  <h4 className="text-gray-500 text-sm mb-2">Advisory Notes</h4>
                  {mutation.data.advisory_notes.map((note: string, i: number) => (
                    <p key={i} className="text-sm text-yellow-600">{note}</p>
                  ))}
                </div>
              )}

              <div className="text-xs text-gray-400">
                <div>Schema Version: {mutation.data.schema_version}</div>
                <div>Spec Version: {mutation.data.specification_version}</div>
                <div>Validated At: {new Date(mutation.data.validated_at).toLocaleString()}</div>
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
