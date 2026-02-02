import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { enhancedValidationApi, AIProviderInfo } from '../../shared/api'
import {
  AI_PROVIDER_LABELS,
  AI_PROVIDER_COLORS,
  ARBITRATION_MODE_LABELS,
  ARBITRATION_MODE_DESCRIPTIONS,
  QUALITY_THRESHOLDS,
} from '../../shared/constants'

export default function AISettings() {
  const { data: providersInfo, isLoading, error } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: () => enhancedValidationApi.getProviders(),
    retry: false,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Configuration</h1>
        <p className="mt-2 text-gray-600">
          Configure AI providers for server-side arbitration in validation
        </p>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">AI Provider Status</h3>

        {isLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded">
            Failed to load AI provider information
          </div>
        ) : providersInfo ? (
          <div className="space-y-4">
            {/* Current Status */}
            <div className={clsx(
              'p-4 rounded-lg',
              providersInfo.is_configured ? 'bg-green-50' : 'bg-amber-50'
            )}>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{providersInfo.is_configured ? '✅' : '⚠️'}</span>
                <div>
                  <p className={clsx(
                    'font-medium',
                    providersInfo.is_configured ? 'text-green-700' : 'text-amber-700'
                  )}>
                    {providersInfo.is_configured
                      ? 'AI Provider Configured'
                      : 'AI Provider Not Configured'}
                  </p>
                  {providersInfo.current_provider && (
                    <p className="text-sm text-gray-600">
                      Active: <span className={clsx(
                        'px-2 py-0.5 rounded text-xs',
                        AI_PROVIDER_COLORS[providersInfo.current_provider] || 'bg-gray-100'
                      )}>
                        {AI_PROVIDER_LABELS[providersInfo.current_provider] || providersInfo.current_provider}
                      </span>
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Configuration Instructions */}
            {!providersInfo.is_configured && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">How to Configure</h4>
                <p className="text-sm text-blue-700 mb-2">
                  Set one of the following environment variables on the server:
                </p>
                <pre className="bg-blue-100 p-3 rounded text-xs text-blue-800 overflow-x-auto">
{`# Choose one provider and set its API key:
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Or use a generic key:
AI_API_KEY=your-api-key`}
                </pre>
              </div>
            )}

            {/* Available Providers */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Available Providers</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {providersInfo.providers.map(provider => (
                  <ProviderCard
                    key={provider.id}
                    provider={provider}
                    isActive={provider.id === providersInfo.current_provider}
                  />
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Arbitration Modes */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Arbitration Modes</h3>
        <p className="text-sm text-gray-500 mb-4">
          Choose how borderline validation cases are handled
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(ARBITRATION_MODE_LABELS).map(([mode, label]) => (
            <div key={mode} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">
                  {mode === 'SERVER' ? '🤖' : mode === 'DELEGATED' ? '👤' : '⏭️'}
                </span>
                <span className="font-medium text-gray-900">{label}</span>
              </div>
              <p className="text-sm text-gray-600">
                {ARBITRATION_MODE_DESCRIPTIONS[mode]}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* When AI is Called */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">When AI Arbitration is Triggered</h3>
        <p className="text-sm text-gray-500 mb-4">
          AI is <strong>NOT</strong> called for every validation. Only when results are ambiguous.
        </p>

        <div className="space-y-3">
          <div className="flex items-center gap-4 p-3 bg-green-50 rounded">
            <span className="text-xl">📊</span>
            <div>
              <p className="font-medium text-gray-900">Quality Score Borderline</p>
              <p className="text-sm text-gray-600">
                Score {QUALITY_THRESHOLDS.BORDERLINE_MIN}-{QUALITY_THRESHOLDS.BORDERLINE_MAX}/100
                (clear pass/fail doesn't need AI)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-3 bg-amber-50 rounded">
            <span className="text-xl">🔍</span>
            <div>
              <p className="font-medium text-gray-900">Near Duplicate</p>
              <p className="text-sm text-gray-600">
                Similarity 85-95% (exact match or clearly different doesn't need AI)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-3 bg-red-50 rounded">
            <span className="text-xl">⚡</span>
            <div>
              <p className="font-medium text-gray-900">Medium Conflict</p>
              <p className="text-sm text-gray-600">
                Severity = MEDIUM (critical auto-blocks, low auto-warns)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Estimation */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Cost Estimation (SERVER mode)</h3>
        <p className="text-sm text-gray-500 mb-4">
          Assuming ~30% of validations need AI arbitration
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-3">Provider</th>
                <th className="text-right py-2 px-3">Cost/Call</th>
                <th className="text-right py-2 px-3">Per 1000 validations</th>
                <th className="text-center py-2 px-3">Speed</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="py-2 px-3">Anthropic (Haiku)</td>
                <td className="text-right py-2 px-3 font-mono">~$0.003</td>
                <td className="text-right py-2 px-3 font-mono">~$0.90</td>
                <td className="text-center py-2 px-3">Fast</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 px-3">OpenAI (GPT-4o-mini)</td>
                <td className="text-right py-2 px-3 font-mono">~$0.003</td>
                <td className="text-right py-2 px-3 font-mono">~$0.90</td>
                <td className="text-center py-2 px-3">Fast</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 px-3">DeepSeek</td>
                <td className="text-right py-2 px-3 font-mono">~$0.001</td>
                <td className="text-right py-2 px-3 font-mono">~$0.30</td>
                <td className="text-center py-2 px-3">Fast</td>
              </tr>
              <tr className="border-b bg-green-50">
                <td className="py-2 px-3 font-medium">Groq (Llama)</td>
                <td className="text-right py-2 px-3 font-mono">~$0.0005</td>
                <td className="text-right py-2 px-3 font-mono text-green-600">~$0.15</td>
                <td className="text-center py-2 px-3">Very Fast</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 px-3">xAI (Grok)</td>
                <td className="text-right py-2 px-3 font-mono">~$0.003</td>
                <td className="text-right py-2 px-3 font-mono">~$0.90</td>
                <td className="text-center py-2 px-3">Fast</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-700">
          💡 <strong>Tip:</strong> Use DELEGATED mode with MCP/Claude Code for $0 cost -
          your AI assistant handles arbitration using your existing subscription.
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Component: Provider Card
// =============================================================================
function ProviderCard({ provider, isActive }: { provider: AIProviderInfo; isActive: boolean }) {
  return (
    <div className={clsx(
      'p-4 rounded-lg border',
      isActive ? 'border-green-500 bg-green-50' : 'border-gray-200'
    )}>
      <div className="flex items-center justify-between mb-2">
        <span className={clsx(
          'px-2 py-0.5 rounded text-xs',
          AI_PROVIDER_COLORS[provider.id] || 'bg-gray-100 text-gray-700'
        )}>
          {AI_PROVIDER_LABELS[provider.id] || provider.name}
        </span>
        {isActive && (
          <span className="text-xs text-green-600 font-medium">Active</span>
        )}
      </div>
      <p className="text-sm text-gray-600 mb-1">
        Default: <span className="font-mono text-xs">{provider.default_model}</span>
      </p>
      <div className="flex flex-wrap gap-1">
        {provider.models.slice(0, 3).map(model => (
          <span key={model} className="px-1.5 py-0.5 bg-gray-100 rounded text-xs text-gray-500">
            {model.split('/').pop()}
          </span>
        ))}
        {provider.models.length > 3 && (
          <span className="text-xs text-gray-400">+{provider.models.length - 3} more</span>
        )}
      </div>
    </div>
  )
}
