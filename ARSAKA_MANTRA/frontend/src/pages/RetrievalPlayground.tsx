import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  retrievalApi,
  RetrievalResponse,
  TriggerCheckResponse,
  CacheStats,
} from '@/shared/api'

export default function RetrievalPlayground() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [query, setQuery] = useState('')
  const [filePath, setFilePath] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [scopePath, setScopePath] = useState('')
  const [maxResults, setMaxResults] = useState(10)
  const [tokenBudget, setTokenBudget] = useState(2000)

  // Results
  const [retrievalResult, setRetrievalResult] = useState<RetrievalResponse | null>(null)
  const [triggerResult, setTriggerResult] = useState<TriggerCheckResponse | null>(null)
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null)

  // Tab state
  const [activeTab, setActiveTab] = useState<'retrieve' | 'triggers' | 'cache'>('retrieve')

  useEffect(() => {
    loadCacheStats()
  }, [])

  const loadCacheStats = async () => {
    try {
      const stats = await retrievalApi.getCacheStats()
      setCacheStats(stats)
    } catch (err) {
      console.error('Failed to load cache stats:', err)
    }
  }

  const handleRetrieve = async () => {
    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const result = await retrievalApi.retrieve({
        query,
        file_path: filePath || undefined,
        file_content: fileContent || undefined,
        scope_path: scopePath || undefined,
        max_results: maxResults,
        token_budget: tokenBudget,
        use_cache: true,
        track_usage: true,
      })
      setRetrievalResult(result)
    } catch (err: any) {
      setError(err.message || 'Retrieval failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCheckTriggers = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await retrievalApi.checkTriggers({
        file_path: filePath || undefined,
        file_content: fileContent || undefined,
        scope_path: scopePath || undefined,
        keywords: query ? query.split(/\s+/) : undefined,
      })
      setTriggerResult(result)
    } catch (err: any) {
      setError(err.message || 'Trigger check failed')
    } finally {
      setLoading(false)
    }
  }

  const handleInvalidateCache = async () => {
    try {
      await retrievalApi.invalidateCache(scopePath || undefined)
      await loadCacheStats()
    } catch (err: any) {
      setError(err.message || 'Cache invalidation failed')
    }
  }

  const confidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-blue-600'
    if (confidence >= 0.4) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Retrieval Playground</h1>
        <p className="text-gray-500">Test context-aware decision retrieval</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('retrieve')}
          className={`px-4 py-2 border-b-2 ${
            activeTab === 'retrieve' ? 'border-blue-500 text-blue-600' : 'border-transparent'
          }`}
        >
          Retrieve
        </button>
        <button
          onClick={() => setActiveTab('triggers')}
          className={`px-4 py-2 border-b-2 ${
            activeTab === 'triggers' ? 'border-blue-500 text-blue-600' : 'border-transparent'
          }`}
        >
          Triggers
        </button>
        <button
          onClick={() => setActiveTab('cache')}
          className={`px-4 py-2 border-b-2 ${
            activeTab === 'cache' ? 'border-blue-500 text-blue-600' : 'border-transparent'
          }`}
        >
          Cache
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded text-sm">{error}</div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle>Context Input</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Query / Keywords</Label>
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., React component architecture"
              />
            </div>

            <div>
              <Label>File Path (optional)</Label>
              <Input
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="e.g., src/components/Auth.tsx"
              />
            </div>

            <div>
              <Label>File Content Preview (optional, first 2000 chars)</Label>
              <Textarea
                value={fileContent}
                onChange={(e) => setFileContent(e.target.value)}
                placeholder="Paste file content for context analysis..."
                rows={4}
              />
            </div>

            <div>
              <Label>Scope Path (optional)</Label>
              <Input
                value={scopePath}
                onChange={(e) => setScopePath(e.target.value)}
                placeholder="e.g., frontend/*, backend/api/*"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Max Results</Label>
                <Input
                  type="number"
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  min={1}
                  max={50}
                />
              </div>
              <div>
                <Label>Token Budget</Label>
                <Input
                  type="number"
                  value={tokenBudget}
                  onChange={(e) => setTokenBudget(Number(e.target.value))}
                  min={100}
                  max={10000}
                />
              </div>
            </div>

            <div className="flex gap-2">
              {activeTab === 'retrieve' && (
                <Button onClick={handleRetrieve} disabled={loading} className="flex-1">
                  {loading ? 'Retrieving...' : 'Retrieve Decisions'}
                </Button>
              )}
              {activeTab === 'triggers' && (
                <Button onClick={handleCheckTriggers} disabled={loading} className="flex-1">
                  {loading ? 'Checking...' : 'Check Triggers'}
                </Button>
              )}
              {activeTab === 'cache' && (
                <>
                  <Button onClick={loadCacheStats} variant="outline" className="flex-1">
                    Refresh Stats
                  </Button>
                  <Button onClick={handleInvalidateCache} variant="destructive" className="flex-1">
                    Invalidate Cache
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle>
              {activeTab === 'retrieve' && 'Retrieval Results'}
              {activeTab === 'triggers' && 'Trigger Analysis'}
              {activeTab === 'cache' && 'Cache Statistics'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activeTab === 'retrieve' && retrievalResult && (
              <div className="space-y-4">
                {/* Summary */}
                <div className="bg-gray-50 p-3 rounded text-sm">
                  <div className="grid grid-cols-2 gap-2">
                    <div>Found: <strong>{retrievalResult.total_count}</strong></div>
                    <div>Time: <strong>{retrievalResult.execution_time_ms.toFixed(1)}ms</strong></div>
                    <div>Tokens: <strong>~{retrievalResult.token_count}</strong></div>
                    <div>Cache: <strong>{retrievalResult.from_cache ? 'Hit' : 'Miss'}</strong></div>
                  </div>
                  {retrievalResult.triggered_by.length > 0 && (
                    <div className="mt-2">
                      Triggered by: <span className="font-mono text-blue-600">{retrievalResult.triggered_by.join(', ')}</span>
                    </div>
                  )}
                </div>

                {/* Results List */}
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {retrievalResult.results.map((r) => (
                    <div key={r.decision_id} className="border rounded p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <a href={`/decisions/${r.decision_id}`} className="font-mono text-blue-600 hover:underline">
                            {r.decision_code}
                          </a>
                          <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
                            {r.source}
                          </span>
                        </div>
                        <span className={`text-sm font-bold ${confidenceColor(r.confidence)}`}>
                          {(r.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm mt-1 text-gray-700">{r.statement}</p>
                      <div className="text-xs text-gray-500 mt-1">
                        Matched: {r.matched_by.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Suggestions */}
                {retrievalResult.suggestions.length > 0 && (
                  <div className="bg-yellow-50 p-3 rounded">
                    <h4 className="font-semibold text-sm mb-1">Suggestions</h4>
                    <ul className="text-sm text-yellow-700">
                      {retrievalResult.suggestions.map((s, i) => (
                        <li key={i}>• {s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'triggers' && triggerResult && (
              <div className="space-y-4">
                <div className={`p-3 rounded ${triggerResult.triggered ? 'bg-green-50' : 'bg-gray-50'}`}>
                  <p className="font-semibold">
                    {triggerResult.triggered ? '✅ Triggers Matched!' : '❌ No Triggers Matched'}
                  </p>
                  {triggerResult.triggered && (
                    <p className="text-sm text-gray-600">
                      {triggerResult.triggers.length} trigger(s), {triggerResult.decision_ids.length} decision(s)
                    </p>
                  )}
                </div>

                {triggerResult.triggers.map((t) => (
                  <div key={t.trigger_id} className="border rounded p-3">
                    <div className="font-semibold">{t.name}</div>
                    <div className="text-sm text-gray-500">
                      Type: {t.type} | Priority: {t.priority}
                    </div>
                    <div className="text-xs mt-1">
                      Matched: <span className="font-mono">{t.matched_patterns.join(', ')}</span>
                    </div>
                    <div className="text-xs mt-1">
                      Decisions: <span className="font-mono text-blue-600">{t.decision_ids.join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'cache' && cacheStats && (
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Context Cache</h4>
                  <div className="bg-gray-50 p-3 rounded grid grid-cols-2 gap-2 text-sm">
                    <div>Entries: <strong>{cacheStats.context_cache.total_entries}</strong></div>
                    <div>Hit Rate: <strong>{(cacheStats.context_cache.hit_rate * 100).toFixed(1)}%</strong></div>
                    <div>Hits: <strong>{cacheStats.context_cache.hits}</strong></div>
                    <div>Misses: <strong>{cacheStats.context_cache.misses}</strong></div>
                    <div>Avg Age: <strong>{cacheStats.context_cache.avg_age_seconds.toFixed(0)}s</strong></div>
                    <div>Memory: <strong>{(cacheStats.context_cache.memory_bytes / 1024).toFixed(1)} KB</strong></div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Hot Cache</h4>
                  <div className="bg-gray-50 p-3 rounded grid grid-cols-2 gap-2 text-sm">
                    <div>Entries: <strong>{cacheStats.hot_cache.total_entries}</strong></div>
                    <div>Hit Rate: <strong>{(cacheStats.hot_cache.hit_rate * 100).toFixed(1)}%</strong></div>
                    <div>Memory: <strong>{(cacheStats.hot_cache.memory_bytes / 1024).toFixed(1)} KB</strong></div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'retrieve' && !retrievalResult && (
              <p className="text-gray-500 text-center py-8">Enter a query and click Retrieve</p>
            )}
            {activeTab === 'triggers' && !triggerResult && (
              <p className="text-gray-500 text-center py-8">Enter context and click Check Triggers</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Help */}
      <Card className="bg-gray-50">
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-2">About Context-Aware Retrieval</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li><strong>Query:</strong> Natural language query or keywords to search for</li>
            <li><strong>File Path:</strong> Current file for pattern-based triggering (e.g., *.tsx triggers React decisions)</li>
            <li><strong>File Content:</strong> First 2000 chars of file for content analysis</li>
            <li><strong>Scope Path:</strong> Filter decisions by scope (e.g., frontend/*, backend/*)</li>
            <li><strong>Triggers:</strong> Automatic rules that activate decisions based on context</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
