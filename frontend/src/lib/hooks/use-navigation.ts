/**
 * Navigation Assistant Hooks (Story 6.1)
 *
 * TanStack Query hooks for navigation assistant API endpoints.
 * Provides navigation chat mutations and history queries.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useTranslation } from '../locales/use-translation';
import {
  sendNavigationMessage,
  getNavigationHistory,
  type NavigationChatResponse,
  type NavigationMessage,
} from '../api/navigation';
import { useNavigationStore } from '../stores/navigation-store';

// ============================================================================
// Query Keys
// ============================================================================

export const navigationKeys = {
  all: ['navigation'] as const,
  history: () => [...navigationKeys.all, 'history'] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook to send a message to the navigation assistant.
 *
 * Handles loading state, error handling, and toast notifications.
 *
 * @param currentNotebookId - Optional current notebook ID for context-aware search
 * @returns Mutation object with sendMessage function
 */
export function useSendNavigationMessage(currentNotebookId?: string) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { setLoading } = useNavigationStore();

  return useMutation<NavigationChatResponse, Error, string>({
    mutationFn: async (message: string) => {
      setLoading(true);
      try {
        return await sendNavigationMessage(message, currentNotebookId);
      } finally {
        setLoading(false);
      }
    },
    onSuccess: () => {
      // Invalidate history to refetch with new messages
      queryClient.invalidateQueries({ queryKey: navigationKeys.history() });
    },
    onError: (error) => {
      console.error('Navigation chat error:', error);
      toast.error(t.learner.navigation.searchFailed);
    },
  });
}

/**
 * Hook to fetch navigation conversation history.
 *
 * Returns last 10 navigation messages for continuity.
 * Cached for 1 minute to reduce API calls.
 *
 * @returns Query object with navigation message history
 */
export function useNavigationHistory() {
  return useQuery<NavigationMessage[], Error>({
    queryKey: navigationKeys.history(),
    queryFn: getNavigationHistory,
    staleTime: 60 * 1000, // 1 minute
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    retry: 1, // Only retry once on failure
  });
}
