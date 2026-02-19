/**
 * System Prompt API Client
 *
 * Admin-only API functions for viewing and editing the global AI teacher system prompt.
 */

import { apiClient } from './client'

export const systemPromptApi = {
  get: () => apiClient.get<{ content: string }>('/system-prompt'),
  update: (content: string) => apiClient.put<{ content: string }>('/system-prompt', { content }),
}
