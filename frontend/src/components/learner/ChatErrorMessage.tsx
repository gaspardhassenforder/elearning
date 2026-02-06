'use client';

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/lib/hooks/use-translation';

/**
 * Story 7.1: Inline chat error message with amber styling.
 *
 * CRITICAL: Uses warm amber colors, never red, for learner-facing error states.
 * Shows a user-friendly error message inline in the chat conversation.
 */

interface ChatErrorMessageProps {
  /** Error message to display (should be translated) */
  message: string;
  /** Whether the error is recoverable (shows retry button) */
  recoverable?: boolean;
  /** Callback when retry button is clicked */
  onRetry?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Inline error message component for chat conversations.
 * Uses amber color scheme to match learner error styling.
 */
export function ChatErrorMessage({
  message,
  recoverable = false,
  onRetry,
  className = '',
}: ChatErrorMessageProps) {
  const { t } = useTranslation();

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 ${className}`}
      role="alert"
      aria-live="polite"
    >
      {/* Amber-themed icon */}
      <div className="flex-shrink-0 mt-0.5">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
      </div>

      {/* Message content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-amber-800 dark:text-amber-200">
          {message}
        </p>

        {/* Retry button for recoverable errors */}
        {recoverable && onRetry && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRetry}
            className="mt-2 h-7 px-2 text-amber-700 hover:text-amber-900 hover:bg-amber-100 dark:text-amber-300 dark:hover:text-amber-100 dark:hover:bg-amber-800/50"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            {t?.learnerErrors?.tryAgain || 'Try Again'}
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Props for SSE error events from the backend.
 */
export interface SSEErrorEvent {
  error?: string;
  error_type?: string;
  recoverable?: boolean;
  message?: string;
}

/**
 * Parses an SSE error event and returns props for ChatErrorMessage.
 *
 * @param event - The SSE error event data
 * @param t - Translation object
 * @returns Props for ChatErrorMessage component
 */
export function parseSSEErrorEvent(
  event: SSEErrorEvent,
  t: Record<string, unknown>
): { message: string; recoverable: boolean } {
  // Use the message field if available, otherwise use a generic message
  const message = event.message || event.error ||
    (t?.learnerErrors as Record<string, string>)?.chatError ||
    'I had trouble processing that. Let me try again.';

  // Default to not recoverable unless explicitly marked
  const recoverable = event.recoverable ?? false;

  return {
    message,
    recoverable,
  };
}

export default ChatErrorMessage;
