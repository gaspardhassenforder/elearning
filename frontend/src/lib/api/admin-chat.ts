/**
 * Admin Chat API Client (Story 3.7, Task 3)
 *
 * API functions for admin assistant chat.
 */

import { apiClient } from './client';

export interface AdminChatRequest {
  message: string;
  notebook_id: string;
  model_override?: string;
}

export interface AdminChatResponse {
  message: string;
  context_used: {
    module_title: string;
    documents_count: number;
    objectives_count: number;
    has_module_prompt: boolean;
  };
}

export const adminChatApi = {
  /**
   * Send message to admin assistant.
   */
  async sendMessage(
    message: string,
    notebookId: string,
    modelOverride?: string
  ): Promise<AdminChatResponse> {
    const response = await apiClient.post<AdminChatResponse>('/admin/chat', {
      message,
      notebook_id: notebookId,
      model_override: modelOverride
    });
    return response.data;
  }
};
