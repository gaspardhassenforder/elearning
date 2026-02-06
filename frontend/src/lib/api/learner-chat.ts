/**
 * Story 4.1: Learner Chat API Client
 *
 * Handles SSE streaming connection to backend learner chat endpoint.
 */

import { apiClient } from './client'

export interface LearnerChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  toolCalls?: ToolCall[]  // Story 4.3: Track tool calls for document snippets
}

// Story 4.3: Tool call tracking
export interface ToolCall {
  id: string
  toolName: string
  args: Record<string, any>
  result?: Record<string, any>
}

export interface SendLearnerChatMessageRequest {
  message: string
  request_greeting_only?: boolean  // Story 4.2: Request proactive greeting without processing message
}

/**
 * Send a message to the learner chat and receive SSE stream
 *
 * Note: This returns a fetch Response object for SSE streaming.
 * The caller is responsible for parsing the SSE events.
 *
 * @param notebookId - Notebook/module ID
 * @param request - Message request
 * @returns Fetch Response with SSE stream
 */
export async function sendLearnerChatMessage(
  notebookId: string,
  request: SendLearnerChatMessageRequest
): Promise<Response> {
  // Use fetch directly for SSE (axios doesn't support streaming well)
  const baseURL = apiClient.defaults.baseURL || '/api'
  const token = localStorage.getItem('auth-storage')
  let accessToken = ''

  if (token) {
    try {
      const authData = JSON.parse(token)
      accessToken = authData.state?.token || ''
    } catch (e) {
      console.error('Failed to parse auth token:', e)
    }
  }

  const response = await fetch(`${baseURL}/chat/learner/${notebookId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    },
    body: JSON.stringify(request),
    credentials: 'include', // Send cookies for JWT auth
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Chat request failed: ${response.status} ${error}`)
  }

  return response
}

// Story 4.4: Objective checked event data
export interface ObjectiveCheckedData {
  objective_id: string
  objective_text: string
  evidence: string
  total_completed: number
  total_objectives: number
  all_complete: boolean
}

// Story 4.8: Chat history response types
export interface ChatHistoryMessage {
  id: string
  role: 'assistant' | 'user'
  content: string
  createdAt: string  // ISO 8601 timestamp
}

export interface ChatHistoryResponse {
  messages: ChatHistoryMessage[]
  thread_id: string
  has_more: boolean
}

// Story 4.3: Extended stream event for tracking tool calls
// Story 4.4: Added objective_checked event type
export interface StreamEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'message_complete' | 'objective_checked'
  delta?: string
  toolCall?: ToolCall
  toolResult?: { id: string; result: Record<string, any> }
  objectiveChecked?: ObjectiveCheckedData  // Story 4.4
}

/**
 * Parse SSE stream from learner chat response
 *
 * Story 4.3: Extended to yield StreamEvent objects including tool calls
 *
 * @param response - Fetch response with SSE stream
 * @yields Stream events (text deltas, tool calls, message complete)
 */
export async function* parseLearnerChatStream(
  response: Response
): AsyncGenerator<StreamEvent, void, unknown> {
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('Response body is not readable')
  }

  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')

      // Keep the last incomplete chunk in buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim()) continue

        // Parse SSE format: "event: text\ndata: {...}"
        const eventMatch = line.match(/^event:\s*(\w+)\s*$/m)
        const dataMatch = line.match(/^data:\s*(.+)$/m)

        if (!dataMatch) continue

        const eventType = eventMatch?.[1] || 'text'
        const dataStr = dataMatch[1]

        try {
          const data = JSON.parse(dataStr)

          // Yield text deltas
          if (eventType === 'text' && data.delta) {
            yield { type: 'text', delta: data.delta }
          }

          // Story 4.3: Yield tool calls
          if (eventType === 'tool_call') {
            yield {
              type: 'tool_call',
              toolCall: {
                id: data.id,
                toolName: data.toolName,
                args: data.args,
              },
            }
          }

          // Story 4.3: Yield tool results
          if (eventType === 'tool_result') {
            yield {
              type: 'tool_result',
              toolResult: {
                id: data.id,
                result: data.result,
              },
            }
          }

          // Story 4.3: Yield message complete event
          if (eventType === 'message_complete') {
            yield { type: 'message_complete' }
          }

          // Story 4.4: Yield objective checked event
          if (eventType === 'objective_checked') {
            yield {
              type: 'objective_checked',
              objectiveChecked: {
                objective_id: data.objective_id,
                objective_text: data.objective_text,
                evidence: data.evidence,
                total_completed: data.total_completed,
                total_objectives: data.total_objectives,
                all_complete: data.all_complete,
              },
            }
          }

          // Handle errors
          if (eventType === 'error') {
            throw new Error(data.detail || 'Stream error occurred')
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e, dataStr)
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * Get chat history for a notebook
 *
 * Story 4.8: Load previous conversation history for persistent chat.
 * Returns messages from the learner's conversation thread with this module.
 *
 * Story 4.8 Task 9: Supports pagination for long conversations (50+ messages).
 *
 * @param notebookId - Notebook/module ID
 * @param options - Pagination options (limit, offset)
 * @returns Chat history response with messages array and has_more flag
 */
export async function getChatHistory(
  notebookId: string,
  options?: { limit?: number; offset?: number }
): Promise<ChatHistoryResponse> {
  const params = new URLSearchParams()
  if (options?.limit !== undefined) params.append('limit', options.limit.toString())
  if (options?.offset !== undefined) params.append('offset', options.offset.toString())

  const queryString = params.toString()
  const url = queryString
    ? `/chat/learner/${notebookId}/history?${queryString}`
    : `/chat/learner/${notebookId}/history`

  const response = await apiClient.get<ChatHistoryResponse>(url)
  return response.data
}
