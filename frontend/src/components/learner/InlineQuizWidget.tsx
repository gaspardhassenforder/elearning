'use client'

/**
 * Story 4.6: Inline Quiz Widget Component
 *
 * Displays interactive multi-question quiz inline in chat.
 * Registered as assistant-ui custom message part for surface_quiz tool results.
 *
 * Features:
 * - Multi-question step-through with Next/Previous navigation
 * - Progress indicator: "Question 2 of 5"
 * - Submit all answers on final question
 * - Results screen with score and per-question correct/incorrect feedback
 * - "View Full Quiz" link for complete quiz experience
 */

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { CheckCircle2, XCircle, FileQuestion, ChevronLeft, ChevronRight } from 'lucide-react'
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

interface QuestionResult {
  question_index: number
  user_answer: number
  correct_answer: number
  is_correct: boolean
  explanation?: string
}

interface QuizResults {
  score: number
  total: number
  percentage: number
  results: QuestionResult[]
}

interface InlineQuizWidgetProps {
  quizId: string
  title: string
  description?: string
  questions: QuizQuestion[]
  totalQuestions: number
  quizUrl?: string
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
  const [currentIndex, setCurrentIndex] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({})
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  if (!questions.length) {
    return (
      <Card className="my-2 p-3 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
        <p className="text-sm text-muted-foreground">{t.learner.quiz.noQuestions}</p>
      </Card>
    )
  }

  const question = questions[currentIndex]
  const isFirst = currentIndex === 0
  const isLast = currentIndex === questions.length - 1
  const allAnswered = questions.every((_, i) => selectedAnswers[i] !== undefined)

  const handleSelectOption = useCallback((value: string) => {
    setSelectedAnswers(prev => ({ ...prev, [currentIndex]: parseInt(value) }))
  }, [currentIndex])

  const handleNext = useCallback(() => {
    if (!isLast) setCurrentIndex(prev => prev + 1)
  }, [isLast])

  const handlePrev = useCallback(() => {
    if (!isFirst) setCurrentIndex(prev => prev - 1)
  }, [isFirst])

  const handleSubmit = async () => {
    if (!allAnswered) return

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      // Build ordered answers array
      const answers = questions.map((_, i) => selectedAnswers[i])

      const response = await fetch(`/api/quizzes/${quizId}/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      })

      if (!response.ok) throw new Error('Failed to score quiz')

      const result: QuizResults = await response.json()
      setQuizResults(result)
    } catch (error) {
      console.error('Quiz submission error:', error)
      setSubmitError(t.learner.quiz.submissionError)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleViewFullQuiz = (e: React.MouseEvent) => {
    e.preventDefault()
    if (quizUrl) router.push(quizUrl)
  }

  const handleRetake = useCallback(() => {
    setQuizResults(null)
    setSelectedAnswers({})
    setCurrentIndex(0)
    setSubmitError(null)
  }, [])

  // Results view
  if (quizResults) {
    return (
      <Card className="my-2 p-4 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700 max-h-[70vh] overflow-y-auto">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
            <FileQuestion className="h-4 w-4 text-primary" />
          </div>

          <div className="flex-1 min-w-0 space-y-3">
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-1">{title}</h4>
              <p className="text-sm font-medium text-foreground">
                {t.learner.quiz.score
                  .replace('{score}', String(quizResults.score))
                  .replace('{total}', String(quizResults.total))}
              </p>
            </div>

            {/* Per-question results */}
            <div className="space-y-2">
              {quizResults.results.map((result, i) => (
                <div
                  key={i}
                  className={cn(
                    'p-2 rounded-md text-sm border',
                    result.is_correct
                      ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800'
                      : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                  )}
                >
                  <div className="flex items-start gap-2">
                    {result.is_correct ? (
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5 text-green-600 dark:text-green-400" />
                    ) : (
                      <XCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-red-500 dark:text-red-400" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-foreground">
                        Q{i + 1}: {questions[i]?.text}
                      </p>
                      {!result.is_correct && (
                        <p className="mt-1 text-sm text-muted-foreground">
                          {t.learner.quiz.correct}: {questions[i]?.options[result.correct_answer]}
                        </p>
                      )}
                      {result.explanation && (
                        <p className="mt-1 text-sm text-muted-foreground">
                          {result.explanation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Actions: Retake + View Full Quiz */}
            <div className="flex items-center gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetake}
              >
                {t.learner.quiz.tryAgain}
              </Button>
              {quizUrl && (
                <button
                  onClick={handleViewFullQuiz}
                  className="text-xs text-primary hover:underline font-medium"
                >
                  {t.learner.quiz.viewFullQuiz} →
                </button>
              )}
            </div>
          </div>
        </div>
      </Card>
    )
  }

  // Question view (step-through)
  return (
    <Card className="my-2 p-4 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
      <div className="flex items-start gap-3">
        {/* Quiz icon */}
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <FileQuestion className="h-4 w-4 text-primary" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Quiz title + progress */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-1">
              {title}
            </h4>
            {description && currentIndex === 0 && (
              <p className="text-xs text-muted-foreground mb-1">
                {description}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {t.learner.quiz.questionOf
                .replace('{current}', String(currentIndex + 1))
                .replace('{total}', String(questions.length))}
            </p>
          </div>

          {/* Progress dots */}
          <div className="flex gap-1">
            {questions.map((_, i) => (
              <div
                key={i}
                className={cn(
                  'h-1.5 flex-1 rounded-full transition-colors',
                  i === currentIndex
                    ? 'bg-primary'
                    : selectedAnswers[i] !== undefined
                    ? 'bg-primary/40'
                    : 'bg-warm-neutral-200 dark:bg-warm-neutral-700'
                )}
              />
            ))}
          </div>

          {/* Question */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">
              {question.text}
            </p>

            {/* Options */}
            <RadioGroup
              value={selectedAnswers[currentIndex]?.toString() ?? ''}
              onValueChange={handleSelectOption}
            >
              <div className="space-y-2">
                {question.options.map((option, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-2 p-2 rounded-md transition-colors hover:bg-warm-neutral-100 dark:hover:bg-warm-neutral-800"
                  >
                    <RadioGroupItem
                      value={index.toString()}
                      id={`q${currentIndex}-option-${index}`}
                    />
                    <Label
                      htmlFor={`q${currentIndex}-option-${index}`}
                      className="flex-1 text-sm cursor-pointer"
                    >
                      {option}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </div>

          {/* Submit error */}
          {submitError && (
            <p className="text-sm text-amber-600 dark:text-amber-400">{submitError}</p>
          )}

          {/* Navigation + Submit */}
          <div className="flex items-center justify-between pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handlePrev}
              disabled={isFirst}
              className="gap-1"
            >
              <ChevronLeft className="h-4 w-4" />
              {t.learner.quiz.previous}
            </Button>

            <div className="flex items-center gap-2">
              {isLast ? (
                <Button
                  onClick={handleSubmit}
                  disabled={!allAnswered || isSubmitting}
                  size="sm"
                  className="bg-primary hover:bg-primary/90"
                >
                  {isSubmitting ? t.learner.quiz.submitting : t.learner.quiz.submitQuiz}
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNext}
                  className="gap-1"
                >
                  {t.learner.quiz.next}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
