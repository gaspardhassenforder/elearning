'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/lib/hooks/use-translation';

/**
 * Story 7.1: Learner-specific ErrorBoundary with amber color theme.
 *
 * CRITICAL: Uses warm amber colors, never red, for learner-facing error states.
 * Provides friendly messaging and options to recover or navigate away.
 *
 * IMPORTANT: Refactored to functional component to support i18n (en-US + fr-FR).
 */

interface ErrorFallbackProps {
  error: Error;
  onRetry: () => void;
  onReturnToModules: () => void;
}

/**
 * Amber-styled error fallback UI for LearnerErrorBoundary.
 * Uses i18n for multi-language support (en-US, fr-FR).
 */
function ErrorFallback({ error, onRetry, onReturnToModules }: ErrorFallbackProps) {
  const { t } = useTranslation();

  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-amber-200 dark:border-amber-800">
        <CardHeader className="text-center">
          {/* Amber-themed icon container */}
          <div className="mx-auto w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-4">
            <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
          <CardTitle className="text-amber-900 dark:text-amber-100">
            {t.learnerErrors.componentCrashed}
          </CardTitle>
          <CardDescription className="text-amber-700 dark:text-amber-300">
            {t.learnerErrors.progressSaved}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Development-only error details */}
          {process.env.NODE_ENV === 'development' && error && (
            <details className="text-xs bg-amber-50 dark:bg-amber-900/20 p-3 rounded border border-amber-200 dark:border-amber-800">
              <summary className="cursor-pointer font-medium text-amber-700 dark:text-amber-300">
                {t.common.errorDetails}
              </summary>
              <pre className="mt-2 whitespace-pre-wrap break-all text-amber-800 dark:text-amber-200">
                {error.toString()}
              </pre>
            </details>
          )}

          {/* Action buttons */}
          <Button
            onClick={onRetry}
            className="w-full bg-amber-500 hover:bg-amber-600 text-white"
            variant="default"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            {t.learnerErrors.tryAgain}
          </Button>

          <Button
            onClick={onReturnToModules}
            className="w-full"
            variant="outline"
          >
            <Home className="w-4 h-4 mr-2" />
            {t.learnerErrors.returnToModules}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

interface LearnerErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

interface LearnerErrorBoundaryProps {
  children: React.ReactNode;
  /** Optional callback when retry is clicked */
  onRetry?: () => void;
  /** Optional callback when return to modules is clicked */
  onReturnToModules?: () => void;
}

/**
 * Class-based error boundary wrapper (required by React).
 * Delegates UI rendering to functional ErrorFallback component for i18n support.
 */
export class LearnerErrorBoundary extends React.Component<
  LearnerErrorBoundaryProps,
  LearnerErrorBoundaryState
> {
  constructor(props: LearnerErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): LearnerErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Only log in development to avoid exposing errors in production
    if (process.env.NODE_ENV === 'development') {
      console.error('LearnerErrorBoundary caught error:', error, errorInfo);
    }
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onRetry?.();
  };

  handleReturnToModules = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onReturnToModules?.();
    // If no callback provided, navigate to modules page
    if (!this.props.onReturnToModules) {
      window.location.href = '/modules';
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.resetError}
          onReturnToModules={this.handleReturnToModules}
        />
      );
    }

    return this.props.children;
  }
}

/**
 * Functional wrapper for LearnerErrorBoundary that uses router hooks.
 * Use this when you need router integration for the "Return to Modules" action.
 */
export function LearnerErrorBoundaryWithRouter({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const handleReturnToModules = () => {
    router.push('/modules');
  };

  return (
    <LearnerErrorBoundary onReturnToModules={handleReturnToModules}>
      {children}
    </LearnerErrorBoundary>
  );
}

export default LearnerErrorBoundary;
