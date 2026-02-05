/**
 * Module Prompts API Client (Story 3.4, Task 6)
 *
 * API functions for managing per-module AI teacher prompts.
 */

import { apiClient } from './client'
import type { ModulePrompt, ModulePromptUpdate } from '@/lib/types/api'

/**
 * Get module prompt for a notebook.
 * Returns null if no prompt configured.
 */
export async function getModulePrompt(notebookId: string): Promise<ModulePrompt | null> {
  const response = await apiClient.get<ModulePrompt | null>(`/api/notebooks/${notebookId}/prompt`)
  return response.data
}

/**
 * Create or update module prompt for a notebook.
 */
export async function updateModulePrompt(
  notebookId: string,
  data: ModulePromptUpdate
): Promise<ModulePrompt> {
  const response = await apiClient.put<ModulePrompt>(`/api/notebooks/${notebookId}/prompt`, data)
  return response.data
}
