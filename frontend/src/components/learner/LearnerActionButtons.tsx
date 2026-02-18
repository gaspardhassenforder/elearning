'use client'

import { useState, useEffect, useMemo } from 'react'
import { Headphones, ClipboardList, Sparkles, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { useJobStatus } from '@/lib/hooks/use-job-status'
import { cn } from '@/lib/utils'
import { LearnerPodcastDialog } from './LearnerPodcastDialog'
import { LearnerQuizDialog } from './LearnerQuizDialog'
import { LearnerTransformationDialog } from './LearnerTransformationDialog'

interface LearnerActionButtonsProps {
  notebookId: string
}

/**
 * Compute weighted overall progress from phase + phase percentage.
 *
 * Phase weights give smooth overall progress across the pipeline:
 *   starting:   0%
 *   outline:    0–15%
 *   transcript: 15–65%  (longest phase)
 *   audio:      65–90%
 *   combining:  90–100%
 */
function computeOverallProgress(phase?: string, phasePct?: number): number {
  const weights: Record<string, { start: number; end: number }> = {
    starting:   { start: 0,  end: 0 },
    outline:    { start: 0,  end: 15 },
    transcript: { start: 15, end: 65 },
    audio:      { start: 65, end: 90 },
    combining:  { start: 90, end: 100 },
  }
  if (!phase || phase === 'starting') return 0
  const range = weights[phase]
  if (!range) return 0
  const pct = phasePct ?? 0
  return Math.round(range.start + (range.end - range.start) * (pct / 100))
}

export function LearnerActionButtons({ notebookId }: LearnerActionButtonsProps) {
  const { t } = useTranslation()
  const [podcastOpen, setPodcastOpen] = useState(false)
  const [quizOpen, setQuizOpen] = useState(false)
  const [transformOpen, setTransformOpen] = useState(false)

  // Podcast progress tracking
  const activeJob = useLearnerStore((s) => s.activeJob)
  const clearActiveJob = useLearnerStore((s) => s.clearActiveJob)
  const isPodcastActive = activeJob?.artifactType === 'podcast'
  const podcastJobId = isPodcastActive ? activeJob.jobId : null

  // Shares TanStack Query cache with ChatPanel (same query key)
  const { status, progress } = useJobStatus(podcastJobId)

  const phase = progress?.phase
  const phasePct = progress?.percentage
  const overallPct = useMemo(
    () => computeOverallProgress(phase, phasePct),
    [phase, phasePct]
  )

  // Completion flash state
  const [showComplete, setShowComplete] = useState(false)

  useEffect(() => {
    if (isPodcastActive && status === 'completed') {
      setShowComplete(true)
      const timer = setTimeout(() => {
        setShowComplete(false)
        clearActiveJob()
      }, 2000)
      return () => clearTimeout(timer)
    } else if (isPodcastActive && status === 'error') {
      clearActiveJob()
    } else {
      setShowComplete(false)
    }
  }, [isPodcastActive, status, clearActiveJob])

  // Phase label from i18n (trivial computation, no memo needed)
  const phases = t.asyncStatus?.phases as Record<string, string> | undefined
  const phaseLabel = showComplete
    ? (t.asyncStatus?.podcastComplete as string) || 'Podcast ready!'
    : !phase
      ? phases?.starting || 'Starting...'
      : phases?.[phase] || phase

  // Whether to show active podcast state (in-progress or brief completion flash)
  // status is undefined before first poll response, so treat it as in-progress
  const isJobInProgress = status === undefined || status === 'pending' || status === 'processing'
  const showPodcastProgress = isPodcastActive && (isJobInProgress || showComplete)

  return (
    <>
      {/* Floating action buttons - right edge, vertically centered */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10 flex flex-col gap-2">
        {/* Podcast button — transforms into progress bar when active */}
        {showPodcastProgress ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  "relative overflow-hidden rounded-full border shadow-sm px-3 py-2 text-sm",
                  "inline-flex items-center justify-center gap-1.5",
                  "bg-background/80 backdrop-blur cursor-default select-none",
                  "h-[34px]" // Match Button size="sm" height
                )}
                onClick={(e) => e.preventDefault()}
              >
                {/* Fill overlay */}
                <div
                  className={cn(
                    "absolute inset-0 origin-left transition-all duration-500 ease-out",
                    showComplete
                      ? "bg-green-300/50 dark:bg-green-600/40"
                      : "bg-sky-300/50 dark:bg-sky-600/40"
                  )}
                  style={{ width: `${showComplete ? 100 : overallPct}%` }}
                />
                {/* Content above fill */}
                <span className="relative z-10 flex items-center gap-1.5">
                  {showComplete ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Headphones className="h-4 w-4 animate-pulse" />
                  )}
                  <span className="hidden md:inline text-xs font-medium">
                    {phaseLabel}
                  </span>
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="left">
              <div className="flex flex-col gap-0.5">
                <span className="font-medium">{phaseLabel}</span>
                {progress?.current != null && progress?.total != null && progress.total > 0 && (
                  <span className="text-[10px] opacity-80">
                    {progress.current} / {progress.total}
                  </span>
                )}
                <span className="text-[10px] opacity-80">{overallPct}%</span>
              </div>
            </TooltipContent>
          </Tooltip>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="rounded-full bg-background/80 backdrop-blur border shadow-sm px-3 py-2 text-sm"
            onClick={() => setPodcastOpen(true)}
          >
            <Headphones className="h-4 w-4" />
            <span className="hidden md:inline ml-1.5">
              {t.learner?.createArtifact?.podcast || 'Podcast'}
            </span>
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          className="rounded-full bg-background/80 backdrop-blur border shadow-sm px-3 py-2 text-sm"
          onClick={() => setQuizOpen(true)}
        >
          <ClipboardList className="h-4 w-4" />
          <span className="hidden md:inline ml-1.5">
            {t.learner?.createArtifact?.quiz || 'Quiz'}
          </span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          className="rounded-full bg-background/80 backdrop-blur border shadow-sm px-3 py-2 text-sm"
          onClick={() => setTransformOpen(true)}
        >
          <Sparkles className="h-4 w-4" />
          <span className="hidden md:inline ml-1.5">
            {t.learner?.createArtifact?.transform || 'Transform'}
          </span>
        </Button>
      </div>

      {/* Dialogs */}
      <LearnerPodcastDialog
        open={podcastOpen}
        onOpenChange={setPodcastOpen}
        notebookId={notebookId}
      />
      <LearnerQuizDialog
        open={quizOpen}
        onOpenChange={setQuizOpen}
        notebookId={notebookId}
      />
      <LearnerTransformationDialog
        open={transformOpen}
        onOpenChange={setTransformOpen}
        notebookId={notebookId}
      />
    </>
  )
}
