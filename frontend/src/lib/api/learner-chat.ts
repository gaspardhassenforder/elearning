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
}

export interface SendLearnerChatMessageRequest {
  message: string
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

/**
 * Parse SSE stream from learner chat response
 *
 * Yields text deltas as they arrive from the stream.
 *
 * @param response - Fetch response with SSE stream
 * @yields Text deltas from SSE events
 */
export async function* parseLearnerChatStream(
  response: Response
): AsyncGenerator<string, void, unknown> {
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
            yield data.delta
          }

          // Handle tool calls (can be extended in future)
          if (eventType === 'tool_call') {
            // Future: Handle tool execution display
            console.log('Tool call:', data)
          }

          // Handle tool results
          if (eventType === 'tool_result') {
            // Future: Display tool results
            console.log('Tool result:', data)
          }

          // Handle message complete
          if (eventType === 'message_complete') {
            console.log('Message complete:', data)
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
