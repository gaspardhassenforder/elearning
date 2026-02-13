/**
 * Story 4.1: Learner Chat Hook
 * Story 4.2: Proactive Greeting Support
 * Story 4.3: Reactive Document Scroll After Streaming
 *
 * Manages learner chat state and SSE streaming.
 * Uses TanStack Query for server state caching.
 * Story 4.2: Automatically requests proactive greeting on first load.
 * Story 4.3: Triggers scroll to referenced documents after streaming completes.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sendLearnerChatMessage, parseLearnerChatStream, LearnerChatMessage, ToolCall, ObjectiveCheckedData, SSEErrorData } from '../api/learner-chat'
import { useToast } from './use-toast'
import { learnerToast } from '../utils/learner-toast'
import { useLearnerStore } from '../stores/learner-store'
import { learningObjectivesKeys } from './use-learning-objectives'
import { useTranslation } from './use-translation'

interface UseLearnerChatResult {
  messages: LearnerChatMessage[]
  isLoading: boolean
  isStreaming: boolean
  error: Error | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => Promise<void>
  editLastMessage: (newContent: string) => Promise<void>
  greetingRequested: boolean  // Story 4.2: Track if greeting was requested
  lastObjectiveChecked: ObjectiveCheckedData | null  // Story 4.4: Last checked objective for inline confirmation
}

/**
 * Hook for learner chat with SSE streaming
 *
 * @param notebookId - Notebook/module ID
 * @returns Chat state and actions
 */
export function useLearnerChat(notebookId: string): UseLearnerChatResult {
  const { toast } = useToast()
  const { language } = useTranslation()
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<LearnerChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  // Story 4.4: Track last checked objective for inline confirmation
  const [lastObjectiveChecked, setLastObjectiveChecked] = useState<ObjectiveCheckedData | null>(null)

  // Story 4.3: Access scroll actions from store
  // Story 4.7: Access job tracking actions from store
  // Individual selectors to avoid infinite re-renders from object creation
  const setScrollToSourceId = useLearnerStore((state) => state.setScrollToSourceId)
  const setActiveJob = useLearnerStore((state) => state.setActiveJob)
  const openViewerSheet = useLearnerStore((state) => state.openViewerSheet)

  // Story 4.8: Chat history is now loaded via useChatHistory hook (see ChatPanel.tsx)
  // This hook manages message state and streaming, not history loading
  const { isLoading, error } = useQuery({
    queryKey: ['learner', 'modules', notebookId, 'chat'],
    queryFn: async () => {
      // Empty query - actual history loaded by useChatHistory in ChatPanel
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
        const response = await sendLearnerChatMessage(notebookId, { message: content, language })

        // Parse SSE stream and accumulate response
        // Story 4.3: Also track tool calls for reactive scroll
        let assistantContent = ''
        const toolCalls: ToolCall[] = []
        const toolCallsMap = new Map<string, ToolCall>()

        const assistantMessage: LearnerChatMessage = {
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          toolCalls: [],
        }

        // Add empty assistant message that will be updated as stream arrives
        setMessages((prev) => {
          assistantMessageIndex = prev.length
          return [...prev, assistantMessage]
        })

        // Stream parsing with error handling
        for await (const event of parseLearnerChatStream(response)) {
          // Story 4.3: Handle different event types
          if (event.type === 'text' && event.delta) {
            assistantContent += event.delta

            // Update assistant message with accumulated content
            setMessages((prev) => {
              const updated = [...prev]
              const lastMessage = updated[updated.length - 1]
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.content = assistantContent
              }
              return updated
            })
          } else if (event.type === 'tool_call' && event.toolCall) {
            // Track tool call
            toolCallsMap.set(event.toolCall.id, event.toolCall)
          } else if (event.type === 'tool_result' && event.toolResult) {
            // Merge result into tool call
            const toolCall = toolCallsMap.get(event.toolResult.id)
            if (toolCall) {
              // Unwrap 'output' wrapper if present (backward compatibility)
              const rawResult = event.toolResult.result
              toolCall.result = rawResult?.output && typeof rawResult.output === 'object' && !Array.isArray(rawResult.output)
                ? rawResult.output
                : rawResult

              // Story 4.7: Detect async artifact generation (tool result with job_id)
              if (
                toolCall.toolName === 'generate_artifact' &&
                toolCall.result?.job_id &&
                toolCall.result?.artifact_type
              ) {
                // Store active job in learner store to trigger AsyncStatusBar
                setActiveJob({
                  jobId: toolCall.result.job_id,
                  artifactType: toolCall.result.artifact_type,
                  notebookId,
                })
              }
            }
          } else if (event.type === 'objective_checked' && event.objectiveChecked) {
            // Story 4.4: Objective was checked off - update progress
            const objectiveData = event.objectiveChecked
            setLastObjectiveChecked(objectiveData)

            // Invalidate progress query to trigger refetch
            queryClient.invalidateQueries({
              queryKey: learningObjectivesKeys.progressByNotebook(notebookId),
            })

            // Show toast notification for completed objective
            toast({
              title: objectiveData.all_complete
                ? '🎉 All objectives complete!'
                : '✓ Objective completed',
              description: objectiveData.objective_text,
              duration: 5000,
            })

            // Story 5.3: Emit custom event for ObjectiveProgressList warm glow
            window.dispatchEvent(new CustomEvent('objective_checked', {
              detail: objectiveData
            }))
          } else if (event.type === 'error' && event.errorData) {
            // Story 7.1: Handle SSE error events - attach to current assistant message
            setMessages((prev) => {
              const updated = [...prev]
              const lastMessage = updated[updated.length - 1]
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.sseError = event.errorData
              }
              return updated
            })
          } else if (event.type === 'message_complete') {
            // Story 4.3: Message streaming complete - trigger reactive scroll
            const completedToolCalls = Array.from(toolCallsMap.values())

            // Attach tool calls to message
            setMessages((prev) => {
              const updated = [...prev]
              const lastMessage = updated[updated.length - 1]
              if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.toolCalls = completedToolCalls
              }
              return updated
            })

            // Extract document references from surface_document tool calls
            const documentRefs = completedToolCalls
              .filter((tc) => tc.toolName === 'surface_document' && tc.result?.source_id)
              .map((tc) => tc.result!.source_id as string)

            // Open viewer sheet for first referenced document
            if (documentRefs.length > 0) {
              const firstDocId = documentRefs[0]
              setScrollToSourceId(firstDocId)
            }
          }
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

      // Story 7.1: Use amber-styled learner toast (never red)
      learnerToast.error(
        error instanceof Error ? error.message : 'Failed to send message'
      )
    },
  })

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return
      await sendMessageMutation.mutateAsync(content)
    },
    [sendMessageMutation, isStreaming]
  )

  const clearMessages = useCallback(async () => {
    setMessages([])
    greetingRequestedRef.current = false  // Allow greeting to fire again
    setGreetingRequested(false)
    try {
      const { resetLearnerChat } = await import('../api/learner-chat')
      await resetLearnerChat(notebookId)
      // Invalidate history cache so next load sees empty state
      queryClient.invalidateQueries({ queryKey: ['learner-chat-history', notebookId] })
    } catch (err) {
      console.error('Failed to reset chat:', err)
    }
  }, [notebookId, queryClient])

  const editLastMessage = useCallback(
    async (newContent: string) => {
      if (!newContent.trim() || isStreaming) return
      // Find the last user message index
      const lastUserIndex = messages.reduce(
        (lastIdx, msg, idx) => (msg.role === 'user' ? idx : lastIdx),
        -1
      )
      if (lastUserIndex === -1) return
      // Truncate messages up to (but not including) the last user message
      setMessages((prev) => prev.slice(0, lastUserIndex))
      // Send the edited content as a new message
      await sendMessageMutation.mutateAsync(newContent)
    },
    [sendMessageMutation, isStreaming, messages]
  )

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
            language,
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
          for await (const event of parseLearnerChatStream(response)) {
            if (event.type === 'text' && event.delta) {
              greetingContent += event.delta

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
          }
        } catch (err) {
          console.error('Failed to fetch greeting:', err)
          // If greeting fails, show empty state and notify user
          setMessages([])

          toast({
            title: 'Could not generate greeting',
            description: 'You can still start the conversation by sending a message.',
            variant: 'default',  // Non-destructive - not critical failure
          })
        } finally {
          setIsStreaming(false)
        }
      }

      requestGreeting()
    }
  }, [messages.length, notebookId, isLoading, error])

  return {
    messages,
    isLoading,
    isStreaming,
    error: error as Error | null,
    sendMessage,
    clearMessages,
    editLastMessage,
    greetingRequested,
    lastObjectiveChecked,  // Story 4.4: Expose for inline confirmation
  }
}

/**
 * Hook for loading chat history
 *
 * Story 4.8: Loads previous conversation messages for persistent chat.
 * Used to initialize Thread component with historical messages on page load.
 *
 * @param notebookId - Notebook/module ID
 * @returns Query result with chat history
 */
export function useChatHistory(notebookId: string) {
  return useQuery({
    queryKey: ['learner-chat-history', notebookId],
    queryFn: async () => {
      const { getChatHistory } = await import('../api/learner-chat')
      return getChatHistory(notebookId)
    },
    staleTime: 1000 * 60 * 5, // 5 minutes - history doesn't change frequently
    retry: 1, // Retry once on failure
  })
}
