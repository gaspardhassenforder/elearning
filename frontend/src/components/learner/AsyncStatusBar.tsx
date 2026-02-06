'use client'

/**
 * Story 4.7: Async Status Bar
 *
 * Persistent status bar displayed at bottom of viewport showing async
 * artifact generation progress. Fixed positioning ensures always visible
 * during long-running tasks (podcast/quiz generation).
 *
 * Features:
 * - Fixed bottom viewport positioning (not chat-scrollable)
 * - Status variants: processing, completed, error
 * - Progress bar (if job returns progress data)
 * - Auto-dismiss after 5s on completion
 * - Manual dismiss on error
 * - Accessibility: ARIA live region
 * - Smooth CSS transitions (150ms ease)
 */

import { useEffect, useState } from 'react'
import { CheckCircle2, Loader2, AlertTriangle, X } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/hooks/use-translation'

interface AsyncStatusBarProps {
  jobId: string
  artifactType: 'podcast' | 'quiz' | string
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress?: {
    current?: number
    total?: number
    percentage?: number
  }
  errorMessage?: string
  onComplete?: () => void
  onError?: (error: string) => void
  onDismiss?: () => void
  className?: string
}

export function AsyncStatusBar({
  jobId,
  artifactType,
  status,
  progress,
  errorMessage,
  onComplete,
  onError,
  onDismiss,
  className,
}: AsyncStatusBarProps) {
  const { t } = useTranslation()
  const [dismissed, setDismissed] = useState(false)

  // Auto-dismiss after 5 seconds on completion
  useEffect(() => {
    if (status === 'completed' && !dismissed) {
      const timer = setTimeout(() => {
        setDismissed(true)
        onDismiss?.()
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [status, dismissed, onDismiss])

  // Call completion/error callbacks
  useEffect(() => {
    if (status === 'completed') {
      onComplete?.()
    } else if (status === 'error') {
      onError?.(errorMessage || 'Unknown error')
    }
  }, [status, onComplete, onError, errorMessage])

  // Don't render if dismissed
  if (dismissed) {
    return null
  }

  // Calculate progress percentage
  const progressPercentage = progress?.percentage ??
    (progress?.current && progress?.total
      ? Math.round((progress.current / progress.total) * 100)
      : undefined)

  // Status-specific styling
  const statusStyles = {
    pending: {
      bg: 'bg-blue-50 dark:bg-blue-950',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-900 dark:text-blue-100',
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      label: t.asyncStatus.generatingArtifact.replace('{type}', artifactType),
    },
    processing: {
      bg: 'bg-blue-50 dark:bg-blue-950',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-900 dark:text-blue-100',
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      label: t.asyncStatus.generatingArtifact.replace('{type}', artifactType),
    },
    completed: {
      bg: 'bg-green-50 dark:bg-green-950',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-900 dark:text-green-100',
      icon: <CheckCircle2 className="h-4 w-4" />,
      label: t.asyncStatus.artifactReady.replace('{type}', artifactType),
    },
    error: {
      bg: 'bg-amber-50 dark:bg-amber-950',
      border: 'border-amber-200 dark:border-amber-800',
      text: 'text-amber-900 dark:text-amber-100',
      icon: <AlertTriangle className="h-4 w-4" />,
      label: t.asyncStatus.artifactFailed.replace('{type}', artifactType),
    },
  }

  const currentStyle = statusStyles[status]

  const handleDismiss = () => {
    setDismissed(true)
    onDismiss?.()
  }

  return (
    <div
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50',
        'border-t',
        currentStyle.bg,
        currentStyle.border,
        'transition-all duration-150 ease-in-out',
        className
      )}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Icon + Label */}
          <div className="flex items-center gap-3">
            <div className={currentStyle.text}>
              {currentStyle.icon}
            </div>
            <div className="flex flex-col gap-1">
              <span className={cn('text-sm font-medium', currentStyle.text)}>
                {currentStyle.label}
              </span>
              {/* Error message */}
              {status === 'error' && errorMessage && (
                <span className="text-xs text-amber-700 dark:text-amber-300">
                  {errorMessage}
                </span>
              )}
              {/* Auto-dismiss countdown for completed */}
              {status === 'completed' && (
                <span className="text-xs text-green-600 dark:text-green-400">
                  {t.asyncStatus.autoDismiss}
                </span>
              )}
            </div>
          </div>

          {/* Progress bar (only show if progress data available) */}
          {(status === 'processing' || status === 'pending') && progressPercentage !== undefined && (
            <div className="flex-1 max-w-xs">
              <Progress
                value={progressPercentage}
                className="h-2"
                style={{
                  transition: 'width 150ms ease',
                }}
              />
              <span className="text-xs text-blue-600 dark:text-blue-400 mt-1 block text-right">
                {progressPercentage}%
              </span>
            </div>
          )}

          {/* Dismiss button */}
          {status === 'error' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDismiss}
              className={cn('ml-auto', currentStyle.text)}
              aria-label={t.asyncStatus.dismiss}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
