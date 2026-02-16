'use client'

import { useState } from 'react'
import { Headphones, ClipboardList, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'
import { LearnerPodcastDialog } from './LearnerPodcastDialog'
import { LearnerQuizDialog } from './LearnerQuizDialog'
import { LearnerTransformationDialog } from './LearnerTransformationDialog'

interface LearnerActionButtonsProps {
  notebookId: string
}

export function LearnerActionButtons({ notebookId }: LearnerActionButtonsProps) {
  const { t } = useTranslation()
  const [podcastOpen, setPodcastOpen] = useState(false)
  const [quizOpen, setQuizOpen] = useState(false)
  const [transformOpen, setTransformOpen] = useState(false)

  return (
    <>
      {/* Floating action buttons - right edge, vertically centered */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10 flex flex-col gap-2">
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
