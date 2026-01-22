'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle, Loader2, RotateCcw } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quizzesApi, QuizCheckRequest } from '@/lib/api/quizzes'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { useTranslation } from '@/lib/hooks/use-translation'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface QuizViewerProps {
  quizId: string
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function QuizViewer({ quizId, notebookId, open, onOpenChange }: QuizViewerProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [selectedAnswers, setSelectedAnswers] = useState<number[]>([])
  const [showResults, setShowResults] = useState(false)
  const [localScore, setLocalScore] = useState<{ score: number; percentage: number } | null>(null)

  const { data: quiz, isLoading, refetch } = useQuery({
    queryKey: QUERY_KEYS.quiz(quizId),
    queryFn: () => quizzesApi.get(quizId),
    enabled: open && !!quizId,
  })

  // When quiz loads, check if it's already completed and show results
  useEffect(() => {
    if (quiz?.completed && quiz.user_answers) {
      setSelectedAnswers(quiz.user_answers)
      setShowResults(true)
      if (quiz.last_score !== undefined) {
        setLocalScore({
          score: quiz.last_score,
          percentage: Math.round((quiz.last_score / quiz.questions.length) * 100),
        })
      }
    }
  }, [quiz])

  const checkMutation = useMutation({
    mutationFn: (request: QuizCheckRequest) => quizzesApi.check(quizId, request),
    onSuccess: (data) => {
      setShowResults(true)
      setLocalScore({ score: data.score, percentage: data.percentage })
      // Refetch to get updated quiz with correct_answer and explanation
      refetch()
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => quizzesApi.reset(quizId),
    onSuccess: () => {
      setSelectedAnswers([])
      setShowResults(false)
      setLocalScore(null)
      // Refetch to get fresh quiz state
      refetch()
    },
  })

  const handleAnswerChange = (questionIndex: number, answerIndex: number) => {
    const newAnswers = [...selectedAnswers]
    newAnswers[questionIndex] = answerIndex
    setSelectedAnswers(newAnswers)
  }

  const handleSubmit = () => {
    if (!quiz || selectedAnswers.filter((a) => a !== undefined).length !== quiz.questions.length) {
      return
    }
    checkMutation.mutate({ answers: selectedAnswers })
  }

  const handleRetake = () => {
    resetMutation.mutate()
  }

  const handleClose = () => {
    onOpenChange(false)
  }

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.quiz || 'Quiz'}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!quiz) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.quiz || 'Quiz'}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            {t.common?.errorLoading || 'Failed to load quiz'}
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  // Determine if we should show results view
  const isShowingResults = showResults || quiz.completed

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="pr-8">{quiz.title}</DialogTitle>
          {quiz.description && (
            <p className="text-sm text-muted-foreground mt-1">{quiz.description}</p>
          )}
        </DialogHeader>

        <div className="flex-1 overflow-y-auto mt-4 min-h-0">
          {!isShowingResults ? (
            // Quiz taking view
            <div className="space-y-6">
              {(!quiz.questions || quiz.questions.length === 0) ? (
                <div className="text-center py-8 text-muted-foreground">
                  {t.artifacts?.noQuestions || 'No questions found in this quiz'}
                </div>
              ) : (
                quiz.questions.map((question, questionIndex) => (
                  <Card key={questionIndex}>
                    <CardHeader>
                      <CardTitle className="text-base">
                        {t.artifacts?.question || 'Question'} {questionIndex + 1}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="font-medium">{question.question}</p>
                      <RadioGroup
                        value={selectedAnswers[questionIndex]?.toString()}
                        onValueChange={(value) =>
                          handleAnswerChange(questionIndex, parseInt(value))
                        }
                      >
                        {question.options.map((option, optionIndex) => (
                          <div key={optionIndex} className="flex items-center space-x-2">
                            <RadioGroupItem
                              value={optionIndex.toString()}
                              id={`q${questionIndex}-o${optionIndex}`}
                            />
                            <Label
                              htmlFor={`q${questionIndex}-o${optionIndex}`}
                              className="flex-1 cursor-pointer"
                            >
                              {option}
                            </Label>
                          </div>
                        ))}
                      </RadioGroup>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          ) : (
            // Results view
            <div className="space-y-6">
              <div className="text-center py-4">
                <h3 className="text-lg font-semibold mb-2">
                  {t.artifacts?.yourScore || 'Your Score'}
                </h3>
                <div className="text-3xl font-bold text-primary">
                  {localScore?.score ?? quiz.last_score ?? 0} / {quiz.questions.length}
                </div>
                <div className="text-lg text-muted-foreground mt-1">
                  {localScore?.percentage ?? (quiz.last_score !== undefined 
                    ? Math.round((quiz.last_score / quiz.questions.length) * 100) 
                    : 0)}%
                </div>
              </div>

              {quiz.questions.map((question, questionIndex) => {
                const userAnswer = selectedAnswers[questionIndex] ?? quiz.user_answers?.[questionIndex]
                const correctAnswer = question.correct_answer
                const isCorrect = userAnswer === correctAnswer

                return (
                  <Card key={questionIndex}>
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base">
                          {t.artifacts?.question || 'Question'} {questionIndex + 1}
                        </CardTitle>
                        {isCorrect ? (
                          <Badge variant="default" className="bg-green-600">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            {t.artifacts?.correct || 'Correct'}
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <XCircle className="h-3 w-3 mr-1" />
                            {t.artifacts?.incorrect || 'Incorrect'}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="font-medium">{question.question}</p>
                      <div className="space-y-2">
                        {question.options.map((option, optionIndex) => {
                          const isSelected = optionIndex === userAnswer
                          const isCorrectOption = optionIndex === correctAnswer
                          
                          let className = 'p-2 rounded border'
                          if (isCorrectOption) {
                            // Always highlight correct answer in green
                            className += ' bg-green-500/20 border-green-500 dark:bg-green-500/30'
                          } else if (isSelected && !isCorrect) {
                            // User selected wrong answer - highlight in red
                            className += ' bg-red-500/20 border-red-500 dark:bg-red-500/30'
                          } else {
                            className += ' border-transparent'
                          }
                          
                          return (
                            <div key={optionIndex} className={className}>
                              <span className="flex items-center gap-2">
                                {isCorrectOption && <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 flex-shrink-0" />}
                                {isSelected && !isCorrect && <XCircle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0" />}
                                {option}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                      {question.explanation && (
                        <div className="mt-3 p-3 bg-muted rounded">
                          <p className="text-sm font-medium mb-1">
                            {t.artifacts?.explanation || 'Explanation'}
                          </p>
                          <p className="text-sm">{question.explanation}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-4 pt-4 border-t flex-shrink-0">
          {!isShowingResults ? (
            <Button
              onClick={handleSubmit}
              disabled={
                !quiz.questions.length ||
                selectedAnswers.filter((a) => a !== undefined).length !== quiz.questions.length ||
                checkMutation.isPending
              }
            >
              {checkMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t.common.processing}
                </>
              ) : (
                t.artifacts?.submit || 'Submit'
              )}
            </Button>
          ) : (
            <>
              <Button 
                variant="outline" 
                onClick={handleRetake}
                disabled={resetMutation.isPending}
              >
                {resetMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RotateCcw className="h-4 w-4 mr-2" />
                )}
                {t.artifacts?.retakeQuiz || 'Retake Quiz'}
              </Button>
              <Button onClick={handleClose}>{t.common.close}</Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
