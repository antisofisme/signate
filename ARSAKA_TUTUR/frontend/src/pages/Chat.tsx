import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Trash2, PlusCircle } from 'lucide-react'
import { Button, Input, Card } from '@/components/ui'
import { useChatStore } from '@/lib/store'
import { chatStream } from '@/lib/api'
import { cn, formatRelativeTime } from '@/lib/utils'
import { toast } from 'sonner'

export function Chat() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const {
    sessionId,
    messages,
    isLoading,
    addMessage,
    updateLastMessage,
    clearMessages,
    setLoading,
    setSessionId,
  } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message
    addMessage({ role: 'user', content: userMessage })

    // Add empty assistant message for streaming
    addMessage({ role: 'assistant', content: '', isStreaming: true })

    try {
      let fullResponse = ''

      for await (const chunk of chatStream({
        message: userMessage,
        session_id: sessionId || undefined,
        use_rag: true,
        stream: true,
      })) {
        fullResponse += chunk
        updateLastMessage(fullResponse)
      }

      // Extract session_id from response if new session
      if (!sessionId) {
        // The API should return session info, but for now we'll let it be handled by the next message
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateLastMessage('Sorry, there was an error processing your message. Please try again.')
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleNewChat = () => {
    clearMessages()
    setSessionId(null)
    toast.success('Started new chat session')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Chat</h1>
          <p className="text-gray-500">
            {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : 'New conversation'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleNewChat}>
            <PlusCircle className="h-4 w-4 mr-2" />
            New Chat
          </Button>
          {messages.length > 0 && (
            <Button variant="ghost" onClick={clearMessages}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <Card className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
              <Send className="h-12 w-12 mb-4 opacity-50" />
              <h3 className="text-lg font-medium">Start a conversation</h3>
              <p className="text-sm">Type a message below to begin chatting with ATLAS AI</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] rounded-lg px-4 py-3',
                    message.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  <p className="whitespace-pre-wrap break-words">
                    {message.content}
                    {message.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
                    )}
                  </p>
                  <p
                    className={cn(
                      'text-xs mt-2',
                      message.role === 'user' ? 'text-white/70' : 'text-gray-500'
                    )}
                  >
                    {formatRelativeTime(message.timestamp)}
                  </p>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
