/**
 * Module Summary Card Component (Story 3.5, Task 6)
 *
 * Displays module validation status with:
 * - Document count (required: >= 1)
 * - Learning objective count (required: >= 1)
 * - Artifact count (optional, informational)
 * - Prompt status (optional, informational)
 * - Inline validation errors
 */

'use client'

import { AlertCircle, CheckCircle2, FileText, Target, Wand2, MessageSquare } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

interface ValidationError {
  field: string
  message: string
}

interface ValidationStatus {
  isValid: boolean
  sourceCount: number
  objectiveCount: number
  artifactCount?: number
  hasPrompt?: boolean
  errors?: ValidationError[]
}

interface ModuleSummaryCardProps {
  notebookId: string
  validation: ValidationStatus
  isLoading?: boolean
}

export function ModuleSummaryCard({ validation, isLoading }: ModuleSummaryCardProps) {
  const { t } = useTranslation()

  const summaryItems = [
    {
      label: t.modules.publish.documents,
      count: validation.sourceCount,
      icon: FileText,
      status: validation.sourceCount >= 1 ? 'valid' : 'invalid',
      required: true,
    },
    {
      label: t.modules.publish.objectives,
      count: validation.objectiveCount,
      icon: Target,
      status: validation.objectiveCount >= 1 ? 'valid' : 'invalid',
      required: true,
    },
    {
      label: t.modules.publish.artifacts,
      count: validation.artifactCount ?? 0,
      icon: Wand2,
      status: 'info',
      required: false,
    },
    {
      label: t.modules.publish.prompt,
      count: validation.hasPrompt ? 1 : 0,
      icon: MessageSquare,
      status: validation.hasPrompt ? 'configured' : 'not-configured',
      required: false,
    },
  ]

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t.modules.publish.summary}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-sm text-muted-foreground">{t.common.loading}</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t.modules.publish.summary}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Items */}
        <div className="grid grid-cols-2 gap-4">
          {summaryItems.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.label} className="flex items-center gap-3">
                <Icon
                  className={cn(
                    'h-5 w-5',
                    item.status === 'valid' && 'text-green-600',
                    item.status === 'invalid' && 'text-red-600',
                    item.status === 'info' && 'text-blue-600',
                    item.status === 'configured' && 'text-green-600',
                    item.status === 'not-configured' && 'text-gray-400'
                  )}
                />
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.count}{' '}
                    {item.required && item.count < 1 && (
                      <span className="text-red-600">({t.modules.publish.required})</span>
                    )}
                    {!item.required && item.status === 'not-configured' && (
                      <span className="text-gray-500">({t.modules.publish.optional})</span>
                    )}
                  </p>
                </div>
                {item.status === 'valid' && (
                  <CheckCircle2 className="ml-auto h-5 w-5 text-green-600" />
                )}
                {item.status === 'invalid' && (
                  <AlertCircle className="ml-auto h-5 w-5 text-red-600" />
                )}
              </div>
            )
          })}
        </div>

        {/* Validation Errors */}
        {validation.errors && validation.errors.length > 0 && (
          <div className="space-y-2">
            {validation.errors.map((error) => (
              <Alert variant="destructive" key={error.field}>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle className="capitalize">{error.field}</AlertTitle>
                <AlertDescription>{error.message}</AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {/* Success Message */}
        {validation.isValid && (
          <Alert>
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>{t.modules.publish.readyToPublish}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
