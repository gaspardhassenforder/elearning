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
import { Info, Loader2 } from 'lucide-react'
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

const DEFAULT_TEMPLATE = `# Module-Specific Teaching Focus

Focus this module on [TOPIC/INDUSTRY - e.g., "AI applications in logistics"].
The learners are [ROLE/AUDIENCE - e.g., "supply chain managers"].

## Teaching Approach
[Describe desired teaching style - e.g., "Keep explanations concrete with real-world examples"]

## Emphasis Areas
- [Area 1 - e.g., "Warehouse automation"]
- [Area 2 - e.g., "Predictive shipping optimization"]
- [Area 3 - e.g., "Inventory forecasting"]

## Specific Examples to Reference
When appropriate, reference these real-world applications:
- [Example 1 - e.g., "Amazon's fulfillment center automation"]
- [Example 2 - e.g., "DHL's predictive shipping"]

## Tone & Language
[Describe desired tone - e.g., "Professional but approachable, avoid overly technical jargon"]

---

**Available Template Variables:**
- \`learner_profile.role\` - Learner's job role
- \`learner_profile.ai_familiarity\` - AI experience level
- \`objectives\` - List of learning objectives with status
- \`context\` - Available source documents

**Example Usage:**
\`\`\`
{% if learner_profile.ai_familiarity == "beginner" %}
Avoid technical AI terminology unless explaining it.
{% endif %}
\`\`\`
`

export function ModulePromptEditor({ moduleId, onNext, onBack }: ModulePromptEditorProps) {
  const { t } = useTranslation()

  // Query and mutation
  const { data: promptData, isLoading, error } = useModulePrompt(moduleId)
  const updateMutation = useUpdateModulePrompt(moduleId)

  // Local state
  const [promptText, setPromptText] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const [showInfoBox, setShowInfoBox] = useState(true)

  // Initialize prompt text from API or default template
  useEffect(() => {
    if (promptData) {
      // Existing prompt - load it
      setPromptText(promptData.system_prompt || '')
    } else if (!isLoading && !promptData) {
      // No existing prompt - pre-populate with default template
      setPromptText(DEFAULT_TEMPLATE)
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
      {/* Info Box */}
      {showInfoBox && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-semibold">{t.modulePrompt.infoTitle}</p>
              <p className="text-sm">{t.modulePrompt.infoDescription}</p>
              <ul className="text-sm list-disc list-inside space-y-1 ml-2">
                <li>{t.modulePrompt.infoGlobal}</li>
                <li>{t.modulePrompt.infoModule}</li>
              </ul>
              <p className="text-sm text-muted-foreground mt-2">{t.modulePrompt.infoOptional}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowInfoBox(false)}
                className="mt-2"
              >
                {t.common.dismiss}
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

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

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={updateMutation.isPending}
        >
          {t.common.back}
        </Button>
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
      </div>
    </div>
  )
}
