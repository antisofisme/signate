/**
 * Chat Store - Global state for AI Chat
 *
 * Manages:
 * - Chat messages
 * - Chat panel open/close state
 * - Loading states
 * - Session info
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// UUID generator with fallback for non-secure contexts (HTTP)
const generateUUID = (): string => {
  try {
    // crypto.randomUUID() only works in secure contexts (HTTPS/localhost)
    return crypto.randomUUID()
  } catch {
    // Fallback for HTTP contexts
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0
      const v = c === 'x' ? r : (r & 0x3) | 0x8
      return v.toString(16)
    })
  }
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  context?: Record<string, unknown>
}

interface ChatState {
  // State
  isOpen: boolean
  isMinimized: boolean
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  userId: string
  sessionId: string | null

  // Actions
  toggleChat: () => void
  openChat: () => void
  closeChat: () => void
  minimizeChat: () => void
  maximizeChat: () => void
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  setMessages: (messages: ChatMessage[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setSessionId: (sessionId: string) => void
  clearMessages: () => void
  getUserId: () => string
}

// Generate or retrieve user ID from localStorage
const getOrCreateUserId = (): string => {
  const stored = localStorage.getItem('arsaka-mantra-user-id')
  if (stored) return stored

  const newId = `user-${generateUUID()}`
  localStorage.setItem('arsaka-mantra-user-id', newId)
  return newId
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Initial state
      isOpen: false,
      isMinimized: false,
      messages: [],
      isLoading: false,
      error: null,
      userId: getOrCreateUserId(),
      sessionId: null,

      // Actions
      toggleChat: () => set((state) => ({
        isOpen: !state.isOpen,
        isMinimized: false,
      })),

      openChat: () => set({
        isOpen: true,
        isMinimized: false,
      }),

      closeChat: () => set({
        isOpen: false,
        isMinimized: false,
      }),

      minimizeChat: () => set({
        isMinimized: true,
      }),

      maximizeChat: () => set({
        isMinimized: false,
      }),

      addMessage: (message) => set((state) => ({
        messages: [
          ...state.messages,
          {
            ...message,
            id: generateUUID(),
            timestamp: new Date().toISOString(),
          },
        ],
      })),

      setMessages: (messages) => set({ messages }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setSessionId: (sessionId) => set({ sessionId }),

      clearMessages: () => set({ messages: [], sessionId: null }),

      getUserId: () => get().userId,
    }),
    {
      name: 'arsaka-mantra-chat',
      partialize: (state) => ({
        messages: state.messages,
        userId: state.userId,
        sessionId: state.sessionId,
      }),
    }
  )
)
