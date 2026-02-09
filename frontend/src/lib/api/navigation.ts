/**
 * Navigation Assistant API Client (Story 6.1)
 *
 * API methods for the platform-wide navigation assistant.
 * Provides navigation chat and history fetching.
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface ModuleSuggestion {
  id: string;
  title: string;
  description: string;
  relevance_score?: number;
}

export interface NavigationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface NavigationChatRequest {
  message: string;
  current_notebook_id?: string;
}

export interface NavigationChatResponse {
  message: string;
  suggested_modules: ModuleSuggestion[];
}

// ============================================================================
// API Methods
// ============================================================================

/**
 * Send a message to the navigation assistant.
 *
 * @param message - The user's navigation query
 * @param currentNotebookId - Optional current notebook ID for context-aware search
 * @returns Navigation response with assistant message and suggested modules
 */
export async function sendNavigationMessage(
  message: string,
  currentNotebookId?: string
): Promise<NavigationChatResponse> {
  const response = await apiClient.post<NavigationChatResponse>(
    '/learner/navigation/chat',
    {
      message,
      current_notebook_id: currentNotebookId,
    } as NavigationChatRequest
  );
  return response.data;
}

/**
 * Get navigation conversation history.
 *
 * Returns last 10 navigation messages for continuity.
 *
 * @returns List of navigation messages (user and assistant)
 */
export async function getNavigationHistory(): Promise<NavigationMessage[]> {
  const response = await apiClient.get<NavigationMessage[]>(
    '/learner/navigation/history'
  );
  return response.data;
}
