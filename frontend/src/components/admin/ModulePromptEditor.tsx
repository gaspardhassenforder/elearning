/**
 * Module Prompt Editor Component (Story 3.4, Task 5)
 *
 * Editor for per-module AI teacher prompt customization with:
 * - Default template pre-population
 * - Multi-line textarea input
 * - Info box explaining two-layer prompt system
 * - Auto-save on navigation
 * - Character count display
 * - Optional configuration (can be left empty)
 */

'use client'

import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useModulePrompt, useUpdateModulePrompt } from '@/lib/hooks/use-module-prompts'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

interface ModulePromptEditorProps {
  moduleId: string
  onNext?: () => void
  onBack?: () => void
}

export function ModulePromptEditor({ moduleId, onNext, onBack }: ModulePromptEditorProps) {
  const { t } = useTranslation()

  // Query and mutation
  const { data: promptData, isLoading, error } = useModulePrompt(moduleId)
  const updateMutation = useUpdateModulePrompt(moduleId)

  // Local state
  const [promptText, setPromptText] = useState('')
  const [hasChanges, setHasChanges] = useState(false)

  // Initialize prompt text from API or default template
  useEffect(() => {
    if (promptData) {
      // Existing prompt - load it
      setPromptText(promptData.system_prompt || '')
    } else if (!isLoading && !promptData) {
      // No existing prompt - leave empty (placeholder guides the admin)
      setPromptText('')
    }
  }, [promptData, isLoading])

  // Track changes
  const handleTextChange = (value: string) => {
    setPromptText(value)
    setHasChanges(true)
  }

  // Auto-save on navigation
  const handleSave = async () => {
    if (!hasChanges) {
      return true // No changes to save
    }

    try {
      await updateMutation.mutateAsync({
        system_prompt: promptText.trim() || null, // Empty string becomes null
      })
      setHasChanges(false)
      return true
    } catch (error) {
      console.error('Failed to save prompt:', error)
      return false
    }
  }

  const handleNext = async () => {
    const saved = await handleSave()
    if (saved && onNext) {
      onNext()
    }
  }

  const handleBack = async () => {
    const saved = await handleSave()
    if (saved && onBack) {
      onBack()
    }
  }

  // Character count
  const charCount = promptText.length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">{t.modulePrompt.loading}</span>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          {t.modulePrompt.errorLoading}: {(error as any)?.response?.data?.detail || (error as Error).message}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* Prompt Editor Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t.modulePrompt.title}</CardTitle>
          <CardDescription>{t.modulePrompt.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Textarea */}
          <div className="space-y-2">
            <Textarea
              value={promptText}
              onChange={(e) => handleTextChange(e.target.value)}
              placeholder={t.modulePrompt.placeholder}
              className="min-h-[400px] font-mono text-sm"
              disabled={updateMutation.isPending}
            />
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {t.modulePrompt.charactersLabel}: {charCount.toLocaleString()}
              </span>
              {hasChanges && (
                <span className="text-amber-600">
                  {t.modulePrompt.unsavedChanges}
                </span>
              )}
            </div>
          </div>

          {/* Help Text */}
          <Alert>
            <AlertDescription className="text-sm">
              <p className="font-semibold mb-2">{t.modulePrompt.helpTitle}</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>{t.modulePrompt.helpVariables}</li>
                <li>{t.modulePrompt.helpJinja}</li>
                <li>{t.modulePrompt.helpEmpty}</li>
              </ul>
            </AlertDescription>
          </Alert>

          {/* Error Display */}
          {updateMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                {t.modulePrompt.errorSaving}:{' '}
                {(updateMutation.error as any)?.response?.data?.detail || (updateMutation.error as Error).message}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons — hidden when no callbacks provided (standalone mode) */}
      {(onBack || onNext) ? (
        <div className="flex items-center justify-between">
          {onBack ? (
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={updateMutation.isPending}
            >
              {t.common.back}
            </Button>
          ) : <div />}
          {onNext && (
            <Button
              onClick={handleNext}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t.common.saving}
                </>
              ) : (
                t.common.next
              )}
            </Button>
          )}
        </div>
      ) : hasChanges && (
        <div className="flex justify-end">
          <Button
            onClick={handleSave}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.common.saving}
              </>
            ) : (
              t.common.save
            )}
          </Button>
        </div>
      )}
    </div>
  )
}
