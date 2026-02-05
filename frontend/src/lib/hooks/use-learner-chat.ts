/**
 * Story 4.1: Learner Chat Hook
 * Story 4.2: Proactive Greeting Support
 *
 * Manages learner chat state and SSE streaming.
 * Uses TanStack Query for server state caching.
 * Story 4.2: Automatically requests proactive greeting on first load.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { sendLearnerChatMessage, parseLearnerChatStream, LearnerChatMessage } from '../api/learner-chat'
import { useToast } from './use-toast'

interface UseLearnerChatResult {
  messages: LearnerChatMessage[]
  isLoading: boolean
  isStreaming: boolean
  error: Error | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  greetingRequested: boolean  // Story 4.2: Track if greeting was requested
}

/**
 * Hook for learner chat with SSE streaming
 *
 * @param notebookId - Notebook/module ID
 * @returns Chat state and actions
 */
export function useLearnerChat(notebookId: string): UseLearnerChatResult {
  const { toast } = useToast()
  const [messages, setMessages] = useState<LearnerChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  // For now, we don't persist chat history (Story 4.8 will add this)
  // This query is a placeholder for future chat history loading
  const { isLoading, error } = useQuery({
    queryKey: ['learner', 'modules', notebookId, 'chat'],
    queryFn: async () => {
      // Story 4.8 will implement persistent chat history
      // For now, return empty array
      return []
    },
    enabled: !!notebookId,
  })

  // Send message mutation with SSE streaming
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      // Track message indices for cleanup on error
      let userMessageIndex = -1
      let assistantMessageIndex = -1

      try {
        // Add user message immediately (optimistic update)
        const userMessage: LearnerChatMessage = {
          role: 'user',
          content,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => {
          userMessageIndex = prev.length
          return [...prev, userMessage]
        })

        // Start streaming assistant response
        setIsStreaming(true)
        const response = await sendLearnerChatMessage(notebookId, { message: content })

        // Parse SSE stream and accumulate response
        let assistantContent = ''
        const assistantMessage: LearnerChatMessage = {
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
        }

        // Add empty assistant message that will be updated as stream arrives
        setMessages((prev) => {
          assistantMessageIndex = prev.length
          return [...prev, assistantMessage]
        })

        // Stream parsing with error handling
        for await (const delta of parseLearnerChatStream(response)) {
          assistantContent += delta

          // Update assistant message with accumulated content
          setMessages((prev) => {
            const updated = [...prev]
            const lastMessage = updated[updated.length - 1]
            if (lastMessage && lastMessage.role === 'assistant') {
              lastMessage.content = assistantContent
            }
            return updated
          })
        }

        return assistantContent
      } catch (streamError) {
        console.error('Stream error:', streamError)
        // Cleanup will happen in onError
        throw streamError
      } finally {
        setIsStreaming(false)
      }
    },
    onError: (error) => {
      // Remove failed messages on error
      // This handles both: request failures AND streaming failures
      setMessages((prev) => {
        // Remove the optimistic user message + partial/empty assistant message
        // Check last 2 messages to ensure they're from this failed request
        if (prev.length >= 2) {
          const lastTwo = prev.slice(-2)
          const isUserThenAssistant =
            lastTwo[0]?.role === 'user' &&
            lastTwo[1]?.role === 'assistant'

          if (isUserThenAssistant) {
            return prev.slice(0, -2)
          }
        }
        // Fallback: if structure is unexpected, just remove last message
        return prev.slice(0, -1)
      })
      setIsStreaming(false)

      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send message',
        variant: 'destructive',
      })
    },
  })

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return
      await sendMessageMutation.mutateAsync(content)
    },
    [sendMessageMutation, isStreaming]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  // Story 4.2: Request proactive greeting on first load
  const [greetingRequested, setGreetingRequested] = useState(false)
  const greetingRequestedRef = useRef(false)

  useEffect(() => {
    // Only request greeting once, when messages are empty and not already requested
    if (messages.length === 0 && !greetingRequestedRef.current && !isLoading && !error) {
      greetingRequestedRef.current = true
      setGreetingRequested(true)

      // Request greeting-only message
      const requestGreeting = async () => {
        try {
          setIsStreaming(true)
          const response = await sendLearnerChatMessage(notebookId, {
            message: '',
            request_greeting_only: true,
          })

          // Parse SSE stream and accumulate greeting
          let greetingContent = ''
          const greetingMessage: LearnerChatMessage = {
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
          }

          // Add empty assistant message that will be updated as stream arrives
          setMessages([greetingMessage])

          // Stream parsing
          for await (const delta of parseLearnerChatStream(response)) {
            greetingContent += delta

            // Update greeting message with accumulated content
            setMessages((prev) => {
              const updated = [...prev]
              const lastMessage = updated[updated.length - 1]
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.content = greetingContent
              }
              return updated
            })
          }
        } catch (err) {
          console.error('Failed to fetch greeting:', err)
          // If greeting fails, just show empty state (UI will handle)
          setMessages([])
        } finally {
          setIsStreaming(false)
        }
      }

      requestGreeting()
    }
  }, [messages.length, notebookId, isLoading, error])

  return {
    messages,
    isLoading: isLoading || isStreaming,
    isStreaming,
    error: error as Error | null,
    sendMessage,
    clearMessages,
    greetingRequested,
  }
}
