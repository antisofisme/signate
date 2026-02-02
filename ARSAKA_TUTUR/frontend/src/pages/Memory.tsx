import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Brain, Trash2, Lightbulb, Target, AlertCircle, Settings2 } from 'lucide-react'
import { Button, Card, CardContent, CardHeader } from '@/components/ui'
import { listFacts, deactivateFact } from '@/lib/api'
import { formatRelativeTime, cn } from '@/lib/utils'
import { toast } from 'sonner'
import type { UserFact } from '@/types'

export function Memory() {
  const queryClient = useQueryClient()

  const { data: facts, isLoading, error } = useQuery({
    queryKey: ['facts'],
    queryFn: () => listFacts({ active_only: true }),
  })

  const deleteMutation = useMutation({
    mutationFn: deactivateFact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facts'] })
      toast.success('Fact deactivated')
    },
    onError: () => {
      toast.error('Failed to deactivate fact')
    },
  })

  const handleDelete = (factId: string) => {
    if (confirm('Deactivate this fact? It will no longer be used in conversations.')) {
      deleteMutation.mutate(factId)
    }
  }

  const getFactIcon = (type: string) => {
    const icons: Record<string, typeof Lightbulb> = {
      preference: Lightbulb,
      context: Settings2,
      goal: Target,
      constraint: AlertCircle,
    }
    return icons[type] || Brain
  }

  const getFactColor = (type: string) => {
    const colors: Record<string, string> = {
      preference: 'bg-yellow-100 text-yellow-700',
      context: 'bg-blue-100 text-blue-700',
      goal: 'bg-green-100 text-green-700',
      constraint: 'bg-red-100 text-red-700',
    }
    return colors[type] || 'bg-gray-100 text-gray-700'
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-700'
    if (confidence >= 0.5) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Memory</h1>
          <p className="text-gray-500">User facts and learned information</p>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-6 w-6 text-amber-500 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Memory service temporarily unavailable</p>
              <p className="text-sm text-amber-600 mt-1">
                The memory facts feature is currently unavailable. This could be due to a backend service issue.
                Chat functionality is still available.
              </p>
            </div>
          </div>
        </div>

        {/* Still show empty state UI */}
        <div className="grid gap-4 md:grid-cols-4">
          {['preference', 'context', 'goal', 'constraint'].map((type) => {
            const Icon = getFactIcon(type)
            return (
              <Card key={type} className="opacity-50">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className={cn('rounded-lg p-2', getFactColor(type))}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">-</p>
                      <p className="text-sm text-gray-500 capitalize">{type}s</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    )
  }

  // Group facts by type
  const factsByType = facts?.reduce((acc, fact) => {
    const type = fact.fact_type
    if (!acc[type]) acc[type] = []
    acc[type].push(fact)
    return acc
  }, {} as Record<string, UserFact[]>)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Memory</h1>
        <p className="text-gray-500">User facts and learned information</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {['preference', 'context', 'goal', 'constraint'].map((type) => {
          const Icon = getFactIcon(type)
          const count = factsByType?.[type]?.length || 0
          return (
            <Card key={type}>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className={cn('rounded-lg p-2', getFactColor(type))}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-sm text-gray-500 capitalize">{type}s</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Facts List */}
      {facts?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No facts learned yet. Start chatting to build memory.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(factsByType || {}).map(([type, typeFacts]) => (
            <div key={type}>
              <h2 className="text-lg font-semibold mb-3 capitalize">{type}s</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {typeFacts.map((fact: UserFact) => {
                  const Icon = getFactIcon(fact.fact_type)
                  return (
                    <Card key={fact.id}>
                      <CardHeader className="flex flex-row items-start justify-between pb-2">
                        <div className="flex items-center gap-2">
                          <div className={cn('rounded-lg p-2', getFactColor(fact.fact_type))}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div>
                            <span className="text-xs text-gray-500 capitalize">
                              {fact.source_type}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'px-2 py-0.5 rounded text-xs font-medium',
                              getConfidenceBadge(fact.confidence)
                            )}
                          >
                            {(fact.confidence * 100).toFixed(0)}%
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(fact.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-700">{fact.content}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          Learned {formatRelativeTime(fact.created_at)}
                        </p>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
