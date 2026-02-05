/**
 * Admin Chat Hook (Story 3.7, Task 3)
 *
 * Manages admin assistant chat state and API communication.
 * Reuses similar patterns from useNotebookChat but simpler (single request/response).
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { adminChatApi } from '@/lib/api/admin-chat';
import type { SourceChatMessage } from '@/lib/types/api';

export function useAdminChat(moduleId: string) {
  const [messages, setMessages] = useState<SourceChatMessage[]>([]);
  const [modelOverride, setModelOverride] = useState<string | undefined>(undefined);

  const sendMessageMutation = useMutation({
    mutationFn: async ({ message, override }: { message: string; override?: string }) => {
      return adminChatApi.sendMessage(message, moduleId, override);
    },
    onMutate: ({ message }) => {
      // Optimistic update: Add user message immediately
      const userMessage: SourceChatMessage = {
        id: `temp-${Date.now()}`,
        type: 'human',
        content: message,
        timestamp: new Date().toISOString()
      };
      setMessages((prev) => [...prev, userMessage]);
    },
    onSuccess: (response) => {
      // Add AI response
      const aiMessage: SourceChatMessage = {
        id: `ai-${Date.now()}`,
        type: 'ai',
        content: response.message,
        timestamp: new Date().toISOString()
      };
      setMessages((prev) => [...prev, aiMessage]);
    },
    onError: (error, { message }) => {
      // Remove optimistic user message on error
      setMessages((prev) => prev.filter((msg) => msg.content !== message));
      throw error;
    }
  });

  const sendMessage = async (message: string, override?: string) => {
    await sendMessageMutation.mutateAsync({ message, override: override || modelOverride });
  };

  return {
    messages,
    isStreaming: sendMessageMutation.isPending,
    sendMessage,
    modelOverride,
    setModelOverride,
    error: sendMessageMutation.error
  };
}
