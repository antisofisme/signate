import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search as SearchIcon, FileText, ExternalLink } from 'lucide-react'
import { Button, Card, CardContent, Input } from '@/components/ui'
import { search } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { SearchResult } from '@/types'

export function Search() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0.3)

  const searchMutation = useMutation({
    mutationFn: () =>
      search({
        query,
        top_k: topK,
        score_threshold: threshold,
      }),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    searchMutation.mutate()
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100'
    if (score >= 0.6) return 'text-blue-600 bg-blue-100'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-100'
    return 'text-gray-600 bg-gray-100'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Semantic Search</h1>
        <p className="text-gray-500">Search knowledge base using natural language</p>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Search Query</label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your search query..."
                  className="flex-1"
                />
                <Button type="submit" isLoading={searchMutation.isPending}>
                  <SearchIcon className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Top K Results</label>
                <Input
                  type="number"
                  min="1"
                  max="20"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Score Threshold</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                />
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {searchMutation.data && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">
            Results ({searchMutation.data.length})
          </h2>

          {searchMutation.data.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <SearchIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No results found. Try a different query or lower the threshold.</p>
            </div>
          ) : (
            searchMutation.data.map((result: SearchResult, index: number) => (
              <Card key={result.id || index}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="rounded-lg bg-gray-100 p-2 mt-1">
                        <FileText className="h-5 w-5 text-gray-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded text-xs font-medium',
                              getScoreColor(result.score)
                            )}
                          >
                            {(result.score * 100).toFixed(1)}%
                          </span>
                          <span className="text-xs text-gray-500 capitalize">
                            {result.source_type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {result.content}
                        </p>
                        {result.metadata && Object.keys(result.metadata).length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {Object.entries(result.metadata).map(([key, value]) => (
                              <span
                                key={key}
                                className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600"
                              >
                                {key}: {String(value)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    {result.metadata?.url ? (
                      <a
                        href={String(result.metadata.url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Initial state */}
      {!searchMutation.data && !searchMutation.isPending && (
        <div className="text-center py-12 text-gray-500">
          <SearchIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Enter a query to search the knowledge base.</p>
        </div>
      )}
    </div>
  )
}
