/**
 * Story 4.1: Learner Chat Hook
 *
 * Manages learner chat state and SSE streaming.
 * Uses TanStack Query for server state caching.
 */

import { useState, useCallback } from 'react'
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
      // Add user message immediately (optimistic update)
      const userMessage: LearnerChatMessage = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

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
      setMessages((prev) => [...prev, assistantMessage])

      try {
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
      } catch (streamError) {
        console.error('Stream error:', streamError)
        throw streamError
      } finally {
        setIsStreaming(false)
      }

      return assistantContent
    },
    onError: (error) => {
      // Remove failed messages on error
      setMessages((prev) => prev.slice(0, -2)) // Remove user + assistant messages
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

  return {
    messages,
    isLoading: isLoading || isStreaming,
    isStreaming,
    error: error as Error | null,
    sendMessage,
    clearMessages,
  }
}
