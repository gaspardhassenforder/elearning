'use client';

/**
 * Quiz Preview Component (Story 3.2, Task 5)
 *
 * Displays quiz questions with answers and explanations.
 */

import { CheckCircle2, XCircle } from 'lucide-react';
import { type QuizPreview } from '@/lib/api/artifacts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface QuizPreviewProps {
  preview: QuizPreview;
}

export function QuizPreview({ preview }: QuizPreviewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{preview.title}</h2>
          <p className="text-muted-foreground mt-1">
            {preview.question_count} {preview.question_count === 1 ? 'question' : 'questions'}
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          Quiz
        </Badge>
      </div>

      {/* Questions */}
      <div className="space-y-6">
        {preview.questions.map((question, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle className="text-lg">
                Question {index + 1}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Question Text */}
              <p className="font-medium">{question.question}</p>

              {/* Choices */}
              <div className="space-y-2">
                {question.choices.map((choice, choiceIndex) => {
                  const isCorrect = choiceIndex === question.correct_answer;

                  return (
                    <div
                      key={choiceIndex}
                      className={cn(
                        'flex items-start gap-3 p-3 rounded-lg border',
                        isCorrect
                          ? 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950'
                          : 'border-border bg-muted/50'
                      )}
                    >
                      <div className="flex-shrink-0 mt-0.5">
                        {isCorrect ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {String.fromCharCode(65 + choiceIndex)}.
                          </span>
                          <span>{choice}</span>
                        </div>
                        {isCorrect && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            Correct Answer
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Explanation */}
              {question.explanation && (
                <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-900">
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                    Explanation
                  </p>
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    {question.explanation}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
