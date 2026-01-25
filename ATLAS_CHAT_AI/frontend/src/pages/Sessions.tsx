import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Trash2, ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { listSessions, getSessionMessages, deleteSession } from '@/lib/api'
import { formatDate, formatRelativeTime, cn } from '@/lib/utils'
import { toast } from 'sonner'
import type { ChatSession, ChatMessage } from '@/types'

export function Sessions() {
  const [expandedSession, setExpandedSession] = useState<string | null>(null)

  const queryClient = useQueryClient()

  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => listSessions({ limit: 50 }),
  })

  const { data: messages } = useQuery({
    queryKey: ['sessionMessages', expandedSession],
    queryFn: () => getSessionMessages(expandedSession!),
    enabled: !!expandedSession,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      toast.success('Session deleted')
    },
    onError: () => {
      toast.error('Failed to delete session')
    },
  })

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this session?')) {
      deleteMutation.mutate(sessionId)
    }
  }

  const toggleExpand = (sessionId: string) => {
    setExpandedSession(expandedSession === sessionId ? null : sessionId)
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
      <div className="text-center text-red-500 p-4">
        Failed to load sessions. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Chat Sessions</h1>
        <p className="text-gray-500">View and manage chat history</p>
      </div>

      {sessions?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No sessions found. Start a conversation to see history here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions?.map((session: ChatSession) => (
            <Card key={session.id}>
              <CardHeader
                className="cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleExpand(session.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-blue-100 p-2">
                      <MessageSquare className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-base">
                        {session.title || `Session ${session.id.slice(0, 8)}...`}
                      </CardTitle>
                      <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {session.message_count} messages
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {session.last_message_at
                            ? formatRelativeTime(session.last_message_at)
                            : formatRelativeTime(session.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={(e) => handleDelete(session.id, e)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    {expandedSession === session.id ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </CardHeader>

              {/* Expanded Messages */}
              {expandedSession === session.id && (
                <CardContent className="border-t">
                  {session.summary && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs font-medium text-gray-500 mb-1">Summary</p>
                      <p className="text-sm text-gray-700">{session.summary}</p>
                    </div>
                  )}

                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {messages?.map((message: ChatMessage) => (
                      <div
                        key={message.id}
                        className={cn(
                          'flex',
                          message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                      >
                        <div
                          className={cn(
                            'max-w-[80%] rounded-lg px-4 py-2 text-sm',
                            message.role === 'user'
                              ? 'bg-primary text-white'
                              : 'bg-gray-100 text-gray-900'
                          )}
                        >
                          <p className="whitespace-pre-wrap">{message.content}</p>
                          <p
                            className={cn(
                              'text-xs mt-1',
                              message.role === 'user' ? 'text-white/70' : 'text-gray-500'
                            )}
                          >
                            {formatDate(message.created_at)}
                          </p>
                        </div>
                      </div>
                    ))}

                    {!messages && (
                      <div className="flex items-center justify-center py-4">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t text-xs text-gray-500 flex justify-between">
                    <span>Total tokens: {session.total_tokens}</span>
                    <span>Created: {formatDate(session.created_at)}</span>
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
