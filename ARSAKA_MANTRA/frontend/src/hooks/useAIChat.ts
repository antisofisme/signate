/**
 * useAIChat - Hook for AI chat and hints functionality
 */

import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../shared/api'
import { useChatStore } from '../stores/chatStore'

// Types
interface ChatRequest {
  message: string
  user_id: string
  context?: Record<string, unknown>
}

interface ChatResponse {
  success: boolean
  response?: string
  error?: string
  session_id?: string
  provider?: string
  model?: string
  timestamp: string
}

interface HintsRequest {
  text: string
  field_type?: string
  context?: Record<string, unknown>
}

interface HintsResponse {
  success: boolean
  hints?: {
    grammar: string
    similar: string
    suggestions: string[]
    classification?: string
  }
  error?: string
  provider?: string
  model?: string
}

interface ChatHistoryResponse {
  messages: Array<{
    id: string
    role: string
    content: string
    context?: Record<string, unknown>
    provider?: string
    created_at: string
  }>
  session_id?: string
}

// Hooks
export function useAIChat() {
  const {
    addMessage,
    setLoading,
    setError,
    setSessionId,
    getUserId,
  } = useChatStore()

  const chatMutation = useMutation({
    mutationFn: async (message: string, context?: Record<string, unknown>) => {
      const request: ChatRequest = {
        message,
        user_id: getUserId(),
        context,
      }
      const response = await api.post<ChatResponse>('/api/v1/ai/chat', request)
      return response.data
    },
    onMutate: () => {
      setLoading(true)
      setError(null)
    },
    onSuccess: (data) => {
      if (data.success && data.response) {
        addMessage({
          role: 'assistant',
          content: data.response,
        })
        if (data.session_id) {
          setSessionId(data.session_id)
        }
      } else if (data.error) {
        setError(data.error)
      }
    },
    onError: (error: Error) => {
      setError(error.message)
    },
    onSettled: () => {
      setLoading(false)
    },
  })

  const sendMessage = async (message: string, context?: Record<string, unknown>) => {
    // Add user message to store
    addMessage({
      role: 'user',
      content: message,
      context,
    })

    // Send to API
    return chatMutation.mutateAsync(message as any)
  }

  return {
    sendMessage,
    isLoading: chatMutation.isPending,
    error: chatMutation.error,
  }
}

export function useAIHints() {
  return useMutation({
    mutationFn: async (request: HintsRequest) => {
      const response = await api.post<HintsResponse>('/api/v1/ai/hints', request)
      return response.data
    },
  })
}

export function useChatHistory() {
  const getUserId = useChatStore((state) => state.getUserId)

  return useQuery({
    queryKey: ['ai-chat-history', getUserId()],
    queryFn: async () => {
      const response = await api.get<ChatHistoryResponse>(
        `/api/v1/ai/chat/history?user_id=${getUserId()}`
      )
      return response.data
    },
    enabled: false, // Only fetch when explicitly requested
  })
}

export function useClearChatHistory() {
  const { clearMessages, getUserId } = useChatStore()

  return useMutation({
    mutationFn: async () => {
      const response = await api.delete(`/api/v1/ai/chat/clear?user_id=${getUserId()}`)
      return response.data
    },
    onSuccess: () => {
      clearMessages()
    },
  })
}

export function useAIProviders() {
  return useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const response = await api.get('/api/v1/ai/providers')
      return response.data
    },
  })
}
