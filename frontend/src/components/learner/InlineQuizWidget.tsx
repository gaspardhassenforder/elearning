'use client'

/**
 * Story 4.6: Inline Quiz Widget Component
 *
 * Displays interactive quiz preview inline in chat with answer submission.
 * Registered as assistant-ui custom message part for surface_quiz tool results.
 *
 * Features:
 * - First question preview with radio button options
 * - Submit answer with instant feedback
 * - Green feedback for correct, amber for incorrect
 * - Explanation text after submission
 * - "View Full Quiz" link for complete quiz experience
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { CheckCircle2, XCircle, FileQuestion } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'

interface QuizQuestion {
  text: string
  options: string[]
  // Note: correct_answer is NOT included (kept server-side for security)
}

interface QuizFeedback {
  isCorrect: boolean
  correctAnswer: number
  userAnswer: number
  explanation?: string
}

interface InlineQuizWidgetProps {
  quizId: string
  title: string
  description?: string
  questions: QuizQuestion[]
  totalQuestions: number
  quizUrl: string
}

export function InlineQuizWidget({
  quizId,
  title,
  description,
  questions,
  totalQuestions,
  quizUrl,
}: InlineQuizWidgetProps) {
  const { t } = useTranslation()
  const router = useRouter()
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<QuizFeedback | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Get first question (only one shown in inline preview)
  const question = questions[0]

  if (!question) {
    return (
      <Card className="my-2 p-3 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
        <p className="text-sm text-muted-foreground">{t.learner.quiz.noQuestions}</p>
      </Card>
    )
  }

  const handleSubmit = async () => {
    if (selectedOption === null) return

    setIsSubmitting(true)

    try {
      // Call quiz scoring API
      const response = await fetch(`/api/quizzes/${quizId}/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: [selectedOption] }),
      })

      if (!response.ok) throw new Error('Failed to score quiz')

      const result = await response.json()
      const questionResult = result.results[0]

      setFeedback({
        isCorrect: questionResult.is_correct,
        correctAnswer: questionResult.correct_answer,
        userAnswer: questionResult.user_answer,
        explanation: questionResult.explanation,
      })
    } catch (error) {
      console.error('Quiz submission error:', error)
      // Show error feedback
      setFeedback({
        isCorrect: false,
        correctAnswer: 0,
        userAnswer: selectedOption,
        explanation: t.learner.quiz.submissionError,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleViewFullQuiz = (e: React.MouseEvent) => {
    e.preventDefault()
    // Use Next.js router for client-side navigation
    router.push(quizUrl)
  }

  return (
    <Card className="my-2 p-4 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
      <div className="flex items-start gap-3">
        {/* Quiz icon */}
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <FileQuestion className="h-4 w-4 text-primary" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Quiz title */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-1">
              {title}
            </h4>
            {description && (
              <p className="text-xs text-muted-foreground">
                {description}
              </p>
            )}
          </div>

          {/* Question */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">
              {question.text}
            </p>

            {/* Options */}
            <RadioGroup
              value={selectedOption?.toString()}
              onValueChange={(value) => setSelectedOption(parseInt(value))}
              disabled={feedback !== null}
            >
              <div className="space-y-2">
                {question.options.map((option, index) => {
                  const isUserAnswer = feedback && feedback.userAnswer === index
                  const isCorrectAnswer = feedback && feedback.correctAnswer === index
                  const showCorrect = isCorrectAnswer
                  const showIncorrect = isUserAnswer && !feedback.isCorrect

                  return (
                    <div
                      key={index}
                      className={cn(
                        'flex items-center space-x-2 p-2 rounded-md transition-colors',
                        showCorrect && 'bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800',
                        showIncorrect && 'bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800',
                        !feedback && 'hover:bg-warm-neutral-100 dark:hover:bg-warm-neutral-800'
                      )}
                    >
                      {feedback ? (
                        // Show result icons after submission
                        <div className="flex-shrink-0 w-4 h-4">
                          {showCorrect && (
                            <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                          )}
                          {showIncorrect && (
                            <XCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                          )}
                        </div>
                      ) : (
                        // Show radio buttons before submission
                        <RadioGroupItem value={index.toString()} id={`option-${index}`} />
                      )}
                      <Label
                        htmlFor={`option-${index}`}
                        className={cn(
                          'flex-1 text-sm cursor-pointer',
                          showCorrect && 'font-medium text-green-700 dark:text-green-300',
                          showIncorrect && 'text-amber-700 dark:text-amber-300',
                          feedback && !showCorrect && !showIncorrect && 'text-muted-foreground'
                        )}
                      >
                        {option}
                      </Label>
                    </div>
                  )
                })}
              </div>
            </RadioGroup>
          </div>

          {/* Feedback explanation */}
          {feedback && feedback.explanation && (
            <div
              className={cn(
                'p-3 rounded-md text-sm',
                feedback.isCorrect
                  ? 'bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800'
                  : 'bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
              )}
            >
              <div className="flex items-start gap-2">
                {feedback.isCorrect ? (
                  <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                )}
                <p className="flex-1">{feedback.explanation}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            {!feedback ? (
              <Button
                onClick={handleSubmit}
                disabled={selectedOption === null || isSubmitting}
                size="sm"
                className="bg-primary hover:bg-primary/90"
              >
                {isSubmitting ? t.learner.quiz.submitting : t.learner.quiz.submitAnswer}
              </Button>
            ) : null}

            <button
              onClick={handleViewFullQuiz}
              className="text-xs text-primary hover:underline font-medium"
            >
              {t.learner.quiz.viewFullQuiz} ({totalQuestions} {totalQuestions === 1 ? t.learner.quiz.question : t.learner.quiz.questions}) →
            </button>
          </div>
        </div>
      </div>
    </Card>
  )
}
