'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerGenerateQuiz } from '@/lib/hooks/use-learner-artifacts'
import { LearnerSourceSelector } from './LearnerSourceSelector'
import { ClipboardList } from 'lucide-react'

interface LearnerQuizDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
}

export function LearnerQuizDialog({
  open,
  onOpenChange,
  notebookId,
}: LearnerQuizDialogProps) {
  const { t } = useTranslation()
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [topic, setTopic] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)

  const generateMutation = useLearnerGenerateQuiz(notebookId)

  const canSubmit = !generateMutation.isPending

  const handleSubmit = () => {
    if (!canSubmit) return
    generateMutation.mutate(
      {
        source_ids: selectedSourceIds.length > 0 ? selectedSourceIds : undefined,
        topic: topic.trim() || undefined,
        num_questions: numQuestions,
      },
      {
        onSuccess: () => {
          setSelectedSourceIds([])
          setTopic('')
          setNumQuestions(5)
          onOpenChange(false)
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5" />
            {t.learner?.createArtifact?.quiz || 'Generate Quiz'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Source Selection */}
          <LearnerSourceSelector
            notebookId={notebookId}
            selectedSourceIds={selectedSourceIds}
            onSelectionChange={setSelectedSourceIds}
          />

          {/* Topic */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.topic || 'Topic'}</Label>
            <Textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={t.learner?.createArtifact?.topicPlaceholder || 'What should the quiz focus on? (optional)'}
              rows={2}
            />
          </div>

          {/* Number of questions */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.numQuestions || 'Number of questions'}</Label>
            <Input
              type="number"
              min={1}
              max={10}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Math.min(10, Math.max(1, parseInt(e.target.value) || 5)))}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common?.cancel || 'Cancel'}
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {generateMutation.isPending ? (
              <>
                <LoadingSpinner />
                <span className="ml-2">{t.learner?.createArtifact?.generating || 'Generating...'}</span>
              </>
            ) : (
              t.learner?.createArtifact?.generate || 'Generate'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
