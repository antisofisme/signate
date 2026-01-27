/**
 * FloatingChat - Persistent AI chat widget
 *
 * Features:
 * - Fixed position at bottom-right
 * - Persists across page navigation
 * - Minimizable
 * - Chat history preserved in Zustand store
 * - Provider selection (OpenAI, DeepSeek, etc.)
 */

import { useState, useRef, useEffect } from 'react'
import { clsx } from 'clsx'
import { useChatStore } from '../../stores/chatStore'
import { useAIChat, useClearChatHistory, useAIProviders } from '../../hooks/useAIChat'
import { useLocation } from 'react-router-dom'

// Chat Button (toggle)
function ChatButton() {
  const { isOpen, toggleChat, messages } = useChatStore()
  const hasMessages = messages.length > 0

  return (
    <button
      onClick={toggleChat}
      className={clsx(
        "fixed bottom-6 right-6 z-50",
        "w-14 h-14 rounded-full shadow-lg",
        "flex items-center justify-center",
        "transition-all duration-300 hover:scale-105",
        isOpen
          ? "bg-gray-600 hover:bg-gray-700"
          : "bg-indigo-600 hover:bg-indigo-700",
        "text-white"
      )}
      title={isOpen ? "Close Mantra" : "Open Mantra"}
    >
      {isOpen ? (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ) : (
        <>
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          {hasMessages && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center">
              {messages.length > 9 ? '9+' : messages.length}
            </span>
          )}
        </>
      )}
    </button>
  )
}

// Single message bubble
function ChatMessage({ message }: { message: { role: string; content: string; timestamp: string } }) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[85%] rounded-lg px-4 py-2 text-sm",
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-gray-100 text-gray-800"
        )}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        <div className={clsx(
          "text-xs mt-1",
          isUser ? "text-indigo-200" : "text-gray-400"
        )}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

// Provider labels
const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI (GPT-4o)',
  deepseek: 'DeepSeek',
  groq: 'Groq',
  openrouter: 'OpenRouter',
}

// Chat panel
function ChatPanel() {
  const { isOpen, isMinimized, messages, isLoading, error, minimizeChat, maximizeChat, closeChat } = useChatStore()
  const { sendMessage } = useAIChat()
  const clearHistory = useClearChatHistory()
  const { data: providersData } = useAIProviders()
  const [input, setInput] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string>('openai')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const location = useLocation()

  // Update selected provider from API
  useEffect(() => {
    if (providersData?.current_provider) {
      setSelectedProvider(providersData.current_provider)
    }
  }, [providersData])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus()
    }
  }, [isOpen, isMinimized])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const message = input.trim()
    setInput('')

    // Include current page as context
    await sendMessage(message, {
      page: location.pathname,
      provider: selectedProvider,
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) return null

  if (isMinimized) {
    return (
      <div
        className="fixed bottom-24 right-6 z-50 bg-white rounded-lg shadow-xl border cursor-pointer hover:shadow-2xl transition-shadow"
        onClick={maximizeChat}
      >
        <div className="px-4 py-3 flex items-center gap-2">
          <span className="text-indigo-600">🤖</span>
          <span className="text-sm text-gray-700">Mantra</span>
          <span className="text-xs text-gray-400">({messages.length} messages)</span>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-24 right-6 z-50 w-[480px] bg-white rounded-lg shadow-2xl border flex flex-col max-h-[80vh]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-indigo-600 text-white rounded-t-lg">
        <div className="flex items-center gap-2">
          <span>🤖</span>
          <span className="font-medium">Mantra</span>
          <span className="text-xs text-indigo-200">
            ({PROVIDER_LABELS[selectedProvider] || selectedProvider})
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={clsx(
              "p-1.5 rounded transition-colors",
              showSettings ? "bg-indigo-500" : "hover:bg-indigo-500"
            )}
            title="Settings"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            onClick={() => clearHistory.mutate()}
            className="p-1.5 hover:bg-indigo-500 rounded transition-colors"
            title="Clear history"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
          <button
            onClick={minimizeChat}
            className="p-1.5 hover:bg-indigo-500 rounded transition-colors"
            title="Minimize"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={closeChat}
            className="p-1.5 hover:bg-indigo-500 rounded transition-colors"
            title="Close"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="border-b bg-gray-50 p-3">
          <label className="block text-xs font-medium text-gray-700 mb-1">AI Provider</label>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="w-full text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {providersData?.available_providers?.map((provider: string) => (
              <option key={provider} value={provider}>
                {PROVIDER_LABELS[provider] || provider}
              </option>
            )) || (
              <>
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="deepseek">DeepSeek</option>
              </>
            )}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Switch between AI providers for different response styles.
          </p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[300px] max-h-[500px]">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <div className="text-4xl mb-2">🤖</div>
            <p className="text-sm">I'm Mantra - your intellectual sparring partner.</p>
            <p className="text-xs mt-1">Challenge your ideas. Test your reasoning.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="animate-pulse">●</div>
                <div className="animate-pulse animation-delay-200">●</div>
                <div className="animate-pulse animation-delay-400">●</div>
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="bg-red-50 text-red-600 text-xs p-2 rounded">
            Error: {error}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows={3}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={clsx(
              "px-4 rounded-lg transition-colors",
              input.trim() && !isLoading
                ? "bg-indigo-600 text-white hover:bg-indigo-700"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            )}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <div className="text-xs text-gray-400 mt-1">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

// Main export - combines button and panel
export default function FloatingChat() {
  return (
    <>
      <ChatPanel />
      <ChatButton />
    </>
  )
}
