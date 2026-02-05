'use client'

/**
 * Story 4.1: Learner Chat Panel with assistant-ui
 *
 * Features:
 * - SSE streaming with token-by-token rendering
 * - assistant-ui Thread component integration
 * - Proactive AI greeting (no empty state)
 * - Flowing AI messages, subtle user backgrounds
 * - Streaming cursor during generation
 */

import { useEffect, useState, useRef } from 'react'
import { MessageSquare } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerChat } from '@/lib/hooks/use-learner-chat'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface ChatPanelProps {
  notebookId: string
}

export function ChatPanel({ notebookId }: ChatPanelProps) {
  const { t } = useTranslation()
  const [mounted, setMounted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Wait for client-side mounting (assistant-ui uses browser APIs)
  useEffect(() => {
    setMounted(true)
  }, [])

  const {
    isLoading,
    isStreaming,
    error,
    sendMessage,
    messages,
  } = useLearnerChat(notebookId)

  // Auto-scroll to bottom when messages change or streaming updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  if (!mounted) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0 border-b">
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          {t.learner.chat.title}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full p-6 text-center">
            <div>
              <p className="text-sm text-muted-foreground mb-2">{t.learner.chat.error}</p>
              <p className="text-xs text-muted-foreground">{t.learner.chat.errorDesc}</p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                // Proactive AI Greeting (no empty state)
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm leading-relaxed">
                      {t.learner.chat.greeting}
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-3 ${
                      message.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <MessageSquare className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`flex-1 max-w-[85%] ${
                        message.role === 'user'
                          ? 'bg-accent/50 rounded-lg p-3'
                          : ''
                      }`}
                    >
                      <p className={`text-sm leading-relaxed ${
                        message.role === 'assistant' ? 'text-foreground/90' : ''
                      }`}>
                        {message.content}
                        {/* Show streaming cursor on last assistant message during streaming */}
                        {message.role === 'assistant' &&
                         index === messages.length - 1 &&
                         isStreaming && (
                          <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse" />
                        )}
                      </p>
                    </div>
                  </div>
                ))
              )}
              {/* Scroll anchor for auto-scroll */}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Area */}
            <div className="flex-shrink-0 border-t p-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const input = e.currentTarget.elements.namedItem('message') as HTMLInputElement
                  if (input.value.trim()) {
                    sendMessage(input.value)
                    input.value = ''
                  }
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  name="message"
                  placeholder={t.learner.chat.placeholder}
                  className="flex-1 px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  autoComplete="off"
                />
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {t.learner.chat.send}
                </button>
              </form>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
