/**
 * Module Publish Flow Component (Story 3.5, Task 7)
 *
 * Orchestrates the publish step with:
 * - ModuleSummaryCard for validation status display
 * - Publish button with loading states
 * - Success confirmation after publish
 * - Back navigation to Configure step
 * - Integration with ModuleCreationStepper
 */

'use client'

import { useEffect, useState } from 'react'
import { Loader2, CheckCircle2 } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { usePublishModule } from '@/lib/hooks/use-notebooks'
import { ModuleSummaryCard } from './ModuleSummaryCard'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface ModulePublishFlowProps {
  notebookId: string
  onSuccess?: () => void
  onBack?: () => void
}

export function ModulePublishFlow({ notebookId, onSuccess, onBack }: ModulePublishFlowProps) {
  const { t } = useTranslation()
  const [publishSuccess, setPublishSuccess] = useState(false)

  // Fetch notebook data to get validation status
  const { data: notebook, isLoading: isLoadingNotebook } = useNotebook(notebookId)

  // Publish mutation
  const publishMutation = usePublishModule(notebookId)

  // Compute validation status from notebook data
  const validation = {
    isValid: (notebook?.source_count ?? 0) >= 1 && (notebook?.objectives_count ?? 0) >= 1,
    sourceCount: notebook?.source_count ?? 0,
    objectiveCount: notebook?.objectives_count ?? 0,
    artifactCount: notebook?.note_count ?? 0,
    hasPrompt: notebook?.has_prompt ?? false,
    errors: [] as Array<{ field: string; message: string }>,
  }

  // Build error list if validation fails
  if (!validation.isValid) {
    if (validation.sourceCount < 1) {
      validation.errors.push({
        field: 'sources',
        message: t.modules.publish.errorNoDocuments,
      })
    }
    if (validation.objectiveCount < 1) {
      validation.errors.push({
        field: 'objectives',
        message: t.modules.publish.errorNoObjectives,
      })
    }
  }

  const canPublish = validation.isValid && !publishMutation.isPending && !publishSuccess

  const handlePublish = async () => {
    try {
      await publishMutation.mutateAsync()
      setPublishSuccess(true)
    } catch (error) {
      // Error handled by mutation hook (toast notification)
      console.error('Publish failed:', error)
    }
  }

  const handleContinue = () => {
    if (onSuccess) {
      onSuccess()
    }
  }

  // Reset success state when notebookId changes
  useEffect(() => {
    setPublishSuccess(false)
  }, [notebookId])

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <ModuleSummaryCard
        validation={validation}
        isLoading={isLoadingNotebook}
      />

      {/* Success Confirmation */}
      {publishSuccess && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription className="font-medium">
            {t.modules.publish.successMessage}
          </AlertDescription>
        </Alert>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack} disabled={publishMutation.isPending}>
          {t.common.back}
        </Button>

        {!publishSuccess ? (
          <Button onClick={handlePublish} disabled={!canPublish}>
            {publishMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {t.modules.publish.publishModule}
          </Button>
        ) : (
          <Button onClick={handleContinue}>
            {t.common.continue}
          </Button>
        )}
      </div>

      {/* Validation Hint */}
      {!validation.isValid && !publishSuccess && (
        <p className="text-sm text-muted-foreground text-center">
          {t.modules.publish.fixErrorsHint}
        </p>
      )}
    </div>
  )
}
