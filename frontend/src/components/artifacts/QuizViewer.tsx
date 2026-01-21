'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
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
  const [selectedAnswers, setSelectedAnswers] = useState<number[]>([])
  const [showResults, setShowResults] = useState(false)

  const { data: quiz, isLoading } = useQuery({
    queryKey: QUERY_KEYS.quiz(quizId),
    queryFn: () => quizzesApi.get(quizId),
    enabled: open && !!quizId,
  })

  const checkMutation = useMutation({
    mutationFn: (request: QuizCheckRequest) => quizzesApi.check(quizId, request),
    onSuccess: () => {
      setShowResults(true)
    },
  })

  const handleAnswerChange = (questionIndex: number, answerIndex: number) => {
    const newAnswers = [...selectedAnswers]
    newAnswers[questionIndex] = answerIndex
    setSelectedAnswers(newAnswers)
  }

  const handleSubmit = () => {
    if (!quiz || selectedAnswers.length !== quiz.questions.length) {
      return
    }
    checkMutation.mutate({ answers: selectedAnswers })
  }

  const handleClose = () => {
    setShowResults(false)
    setSelectedAnswers([])
    onOpenChange(false)
  }

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.quiz || 'Quiz'}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!quiz) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{quiz.title}</DialogTitle>
          {quiz.description && (
            <p className="text-sm text-muted-foreground mt-1">{quiz.description}</p>
          )}
        </DialogHeader>

        <div className="flex-1 overflow-y-auto mt-4">
          {!showResults ? (
            <div className="space-y-6">
              {quiz.questions.map((question, questionIndex) => (
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
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center py-4">
                <h3 className="text-lg font-semibold mb-2">
                  {t.artifacts?.yourScore || 'Your Score'}
                </h3>
                <div className="text-3xl font-bold text-primary">
                  {checkMutation.data?.score || 0} / {quiz.questions.length}
                </div>
                <div className="text-lg text-muted-foreground mt-1">
                  {checkMutation.data?.percentage || 0}%
                </div>
              </div>

              {quiz.questions.map((question, questionIndex) => {
                const result = checkMutation.data?.results.find(
                  (r) => r.question_index === questionIndex
                )
                const isCorrect = result?.correct ?? false
                const selectedAnswer = selectedAnswers[questionIndex]

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
                        {question.options.map((option, optionIndex) => (
                          <div
                            key={optionIndex}
                            className={`p-2 rounded ${
                              optionIndex === selectedAnswer
                                ? isCorrect
                                  ? 'bg-green-50 border border-green-200'
                                  : 'bg-red-50 border border-red-200'
                                : ''
                            }`}
                          >
                            {option}
                          </div>
                        ))}
                      </div>
                      {result?.explanation && (
                        <div className="mt-3 p-3 bg-muted rounded">
                          <p className="text-sm font-medium mb-1">
                            {t.artifacts?.explanation || 'Explanation'}
                          </p>
                          <p className="text-sm">{result.explanation}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
          {!showResults ? (
            <Button
              onClick={handleSubmit}
              disabled={
                selectedAnswers.length !== quiz.questions.length || checkMutation.isPending
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
            <Button onClick={handleClose}>{t.common.close}</Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
