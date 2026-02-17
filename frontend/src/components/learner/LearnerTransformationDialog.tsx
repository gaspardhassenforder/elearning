'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerExecuteTransformation } from '@/lib/hooks/use-learner-artifacts'
import { transformationsApi } from '@/lib/api/transformations'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { LearnerSourceSelector } from './LearnerSourceSelector'
import { Sparkles } from 'lucide-react'
import type { Transformation } from '@/lib/types/transformations'

interface LearnerTransformationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  notebookId: string
}

export function LearnerTransformationDialog({
  open,
  onOpenChange,
  notebookId,
}: LearnerTransformationDialogProps) {
  const { t } = useTranslation()
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [selectedTransformationId, setSelectedTransformationId] = useState<string>('')
  const [instructions, setInstructions] = useState('')

  const { data: transformations, isLoading: transformationsLoading } = useQuery<Transformation[]>({
    queryKey: QUERY_KEYS.transformations,
    queryFn: transformationsApi.list,
    enabled: open,
  })

  const executeMutation = useLearnerExecuteTransformation(notebookId)

  const canSubmit =
    selectedSourceIds.length > 0 &&
    selectedTransformationId &&
    !executeMutation.isPending

  const handleSubmit = () => {
    if (!canSubmit) return
    executeMutation.mutate(
      {
        transformation_id: selectedTransformationId,
        source_ids: selectedSourceIds,
        instructions: instructions.trim() || undefined,
      },
      {
        onSuccess: () => {
          setSelectedSourceIds([])
          setSelectedTransformationId('')
          setInstructions('')
          onOpenChange(false)
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {t.learner?.createArtifact?.transform || 'Transform'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Source Selection */}
          <LearnerSourceSelector
            notebookId={notebookId}
            selectedSourceIds={selectedSourceIds}
            onSelectionChange={setSelectedSourceIds}
          />

          {/* Transformation Picker */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.pickTransformation || 'Choose a transformation'}</Label>
            {transformationsLoading ? (
              <div className="flex items-center justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : !transformations || transformations.length === 0 ? (
              <p className="text-sm text-muted-foreground py-2">{t.learner?.createArtifact?.noTransformationsAvailable || 'No transformations available'}</p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {transformations.map((tx) => (
                  <button
                    key={tx.id}
                    type="button"
                    onClick={() => setSelectedTransformationId(tx.id)}
                    className={`rounded-xl border p-3 text-left transition-all hover:border-primary/50 ${
                      selectedTransformationId === tx.id
                        ? 'border-primary ring-2 ring-primary/20 bg-primary/5'
                        : 'border-border'
                    }`}
                  >
                    <div className="font-medium text-sm">{tx.title}</div>
                    {tx.description && (
                      <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {tx.description}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Additional Instructions */}
          <div className="space-y-2">
            <Label>{t.learner?.createArtifact?.instructions || 'Instructions'}</Label>
            <Textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder={t.learner?.createArtifact?.instructionsPlaceholder || 'Optional: additional instructions...'}
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.common?.cancel || 'Cancel'}
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {executeMutation.isPending ? (
              <>
                <LoadingSpinner />
                <span className="ml-2">{t.learner?.createArtifact?.generating || 'Generating...'}</span>
              </>
            ) : (
              t.learner?.createArtifact?.execute || 'Execute'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
