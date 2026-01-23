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
import { Textarea } from '@/components/ui/textarea'
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
  const [numQuestions, setNumQuestions] = useState<string>('5')
  const [instructions, setInstructions] = useState('')
  const generateQuiz = useGenerateQuiz()

  const handleNumQuestionsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    // Allow empty string for deletion, or valid numbers
    if (value === '' || /^\d+$/.test(value)) {
      setNumQuestions(value)
    }
  }

  const handleNumQuestionsBlur = () => {
    // Ensure we have a valid number on blur
    const num = parseInt(numQuestions)
    if (isNaN(num) || num < 1) {
      setNumQuestions('5')
    } else if (num > 20) {
      setNumQuestions('20')
    } else {
      setNumQuestions(num.toString())
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const num = parseInt(numQuestions) || 5
    const finalNum = Math.max(1, Math.min(20, num))
    
    try {
      await generateQuiz.mutateAsync({
        notebookId,
        request: {
          topic: topic.trim() || undefined,
          num_questions: finalNum,
          instructions: instructions.trim() || undefined,
        },
      })
      setTopic('')
      setNumQuestions('5')
      setInstructions('')
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
              type="text"
              inputMode="numeric"
              min={1}
              max={20}
              value={numQuestions}
              onChange={handleNumQuestionsChange}
              onBlur={handleNumQuestionsBlur}
              placeholder="5"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="instructions">
              {t.artifacts?.quizInstructions || 'Instructions (optional)'}
            </Label>
            <Textarea
              id="instructions"
              placeholder={t.artifacts?.quizInstructionsPlaceholder || 'e.g., Focus on practical examples, avoid theoretical questions'}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={3}
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
