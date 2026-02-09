/**
 * NavigationChat Component (Story 6.1)
 *
 * Chat interface for the navigation assistant overlay.
 * Features:
 * - Message history display (user + assistant)
 * - Input composer with send button
 * - Module suggestion cards
 * - Loading and error states
 * - Empty state with greeting
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Loader2, X, Compass } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNavigationHistory, useSendNavigationMessage } from '@/lib/hooks/use-navigation'
import { useNavigationStore } from '@/lib/stores/navigation-store'
import { ModuleSuggestionCard } from './ModuleSuggestionCard'
import { cn } from '@/lib/utils'
import type { NavigationMessage, ModuleSuggestion } from '@/lib/api/navigation'

interface NavigationChatProps {
  currentNotebookId?: string
}

export function NavigationChat({ currentNotebookId }: NavigationChatProps) {
  const { t } = useTranslation()
  const [input, setInput] = useState('')
  const [localMessages, setLocalMessages] = useState<NavigationMessage[]>([])
  const [suggestedModules, setSuggestedModules] = useState<ModuleSuggestion[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { closeNavigator, isLoading } = useNavigationStore()

  // Load navigation history on mount
  const { data: historyData, isLoading: isLoadingHistory } = useNavigationHistory()

  // Send navigation message mutation
  const sendMessageMutation = useSendNavigationMessage(currentNotebookId)

  // Merge history with local messages
  const allMessages = historyData ? [...historyData, ...localMessages] : localMessages

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [allMessages, suggestedModules])

  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message optimistically
    const newUserMessage: NavigationMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    }
    setLocalMessages((prev) => [...prev, newUserMessage])

    try {
      // Send to backend
      const response = await sendMessageMutation.mutateAsync(userMessage)

      // Add assistant response
      const assistantMessage: NavigationMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
      }
      setLocalMessages((prev) => [...prev, assistantMessage])

      // Update suggested modules
      setSuggestedModules(response.suggested_modules || [])
    } catch (error) {
      console.error('Navigation message failed:', error)
      // Error toast is handled by mutation hook
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <Compass className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">{t.learner.navigation.title}</h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={closeNavigator}
          aria-label={t.learner.navigation.close}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : allMessages.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <Compass className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <p className="text-sm font-medium mb-1">{t.learner.navigation.greeting}</p>
            <p className="text-xs text-muted-foreground">{t.learner.navigation.greetingPrompt}</p>
          </div>
        ) : (
          // Message list
          <div className="space-y-4">
            {allMessages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  'flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {/* Suggested Modules */}
            {suggestedModules.length > 0 && (
              <div className="space-y-2 pt-2">
                {suggestedModules.map((suggestion) => (
                  <ModuleSuggestionCard key={suggestion.id} suggestion={suggestion} />
                ))}
              </div>
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-3 py-2 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.learner.navigation.placeholder}
            disabled={isLoading}
            className="resize-none min-h-[44px] max-h-[120px]"
            rows={1}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
