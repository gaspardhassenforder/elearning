'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useGenerateQuiz } from '@/lib/hooks/use-artifacts'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Loader2 } from 'lucide-react'

interface GenerateQuizDialogProps {
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GenerateQuizDialog({ notebookId, open, onOpenChange }: GenerateQuizDialogProps) {
  const { t } = useTranslation()
  const [topic, setTopic] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const generateQuiz = useGenerateQuiz()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await generateQuiz.mutateAsync({
        notebookId,
        request: {
          topic: topic.trim() || undefined,
          num_questions: numQuestions,
        },
      })
      setTopic('')
      setNumQuestions(5)
      onOpenChange(false)
    } catch (error) {
      // Error is handled by the mutation hook
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.artifacts?.generateQuiz || 'Generate Quiz'}</DialogTitle>
          <DialogDescription>
            {t.artifacts?.generateQuizDesc || 'Create a quiz from your notebook sources'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">{t.artifacts?.quizTopic || 'Topic (optional)'}</Label>
            <Input
              id="topic"
              placeholder={t.artifacts?.quizTopicPlaceholder || 'e.g., JavaScript arrays'}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="numQuestions">
              {t.artifacts?.numQuestions || 'Number of Questions'}
            </Label>
            <Input
              id="numQuestions"
              type="number"
              min={1}
              max={20}
              value={numQuestions}
              onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={generateQuiz.isPending}
            >
              {t.common.cancel}
            </Button>
            <Button type="submit" disabled={generateQuiz.isPending}>
              {generateQuiz.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t.artifacts?.generating || 'Generating...'}
                </>
              ) : (
                t.artifacts?.generateQuiz || 'Generate Quiz'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
