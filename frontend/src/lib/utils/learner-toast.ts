/**
 * Story 7.1: Learner-specific toast notifications with amber color theme.
 *
 * CRITICAL: Learner-facing error toasts use warm amber colors, never red.
 * This aligns with UX spec requirements for learner-facing error states.
 */

import { toast } from 'sonner';

/**
 * Amber color palette for learner error states (from UX Design Spec).
 */
const AMBER_COLORS = {
  background: '#FEF3C7', // amber-100
  border: '#F59E0B', // amber-500
  text: '#B45309', // amber-700
  icon: '#D97706', // amber-600
};

/**
 * Learner-specific toast wrapper with amber styling for errors.
 *
 * Usage:
 * ```
 * import { learnerToast } from '@/lib/utils/learner-toast';
 * learnerToast.error(t.learnerErrors.generic);
 * learnerToast.success('Great job!');
 * ```
 */
export const learnerToast = {
  /**
   * Show an error toast with warm amber styling (never red).
   *
   * Story 7.1: ARIA Accessibility Implementation
   * - sonner automatically adds role="status" to toast elements
   * - sonner automatically adds aria-live="polite" for screen reader announcements
   * - Toast messages are announced without interrupting user's current task
   * - Tested with: NVDA (Windows), JAWS (Windows), VoiceOver (macOS/iOS)
   *
   * @param message - User-friendly error message (should be translated)
   * @param options - Additional toast options
   */
  error: (message: string, options?: { duration?: number; description?: string }) => {
    toast.error(message, {
      duration: options?.duration ?? 5000,
      description: options?.description,
      style: {
        backgroundColor: AMBER_COLORS.background,
        borderColor: AMBER_COLORS.border,
        borderWidth: '1px',
        borderStyle: 'solid',
        color: AMBER_COLORS.text,
      },
      className: 'learner-toast-error',
      // Accessibility: sonner handles ARIA roles/labels automatically
      // role="status", aria-live="polite", aria-atomic="true" are set by library
    });
  },

  /**
   * Show a success toast (uses default green styling).
   * @param message - Success message
   * @param options - Additional toast options
   */
  success: (message: string, options?: { duration?: number; description?: string }) => {
    toast.success(message, {
      duration: options?.duration ?? 3000,
      description: options?.description,
    });
  },

  /**
   * Show an info toast (uses default styling).
   * @param message - Info message
   * @param options - Additional toast options
   */
  info: (message: string, options?: { duration?: number; description?: string }) => {
    toast(message, {
      duration: options?.duration ?? 4000,
      description: options?.description,
    });
  },

  /**
   * Show a warning toast with amber styling.
   * @param message - Warning message
   * @param options - Additional toast options
   */
  warning: (message: string, options?: { duration?: number; description?: string }) => {
    toast.warning(message, {
      duration: options?.duration ?? 5000,
      description: options?.description,
      style: {
        backgroundColor: AMBER_COLORS.background,
        borderColor: AMBER_COLORS.border,
        borderWidth: '1px',
        borderStyle: 'solid',
        color: AMBER_COLORS.text,
      },
      className: 'learner-toast-warning',
    });
  },
};
