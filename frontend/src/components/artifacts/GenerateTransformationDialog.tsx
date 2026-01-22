'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTransformations } from '@/lib/hooks/use-transformations'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useToast } from '@/lib/hooks/use-toast'
import { Loader2 } from 'lucide-react'
import apiClient from '@/lib/api/client'
import { useQueryClient } from '@tanstack/react-query'
import { QUERY_KEYS } from '@/lib/api/query-client'

interface GenerateTransformationDialogProps {
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function GenerateTransformationDialog({
  notebookId,
  open,
  onOpenChange,
}: GenerateTransformationDialogProps) {
  const { t } = useTranslation()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const { data: transformations, isLoading: transformationsLoading } = useTransformations()
  const [selectedTransformationId, setSelectedTransformationId] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)

  // Reset selection when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setSelectedTransformationId('')
    }
  }, [open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTransformationId) return

    setIsGenerating(true)
    try {
      await apiClient.post(`/notebooks/${notebookId}/transformations/generate`, {
        transformation_id: selectedTransformationId,
      })
      
      // Invalidate artifacts queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
      
      toast({
        title: t.common.success,
        description: t.artifacts?.transformationGenerated || 'Transformation generated successfully',
      })
      
      setSelectedTransformationId('')
      onOpenChange(false)
    } catch (error: any) {
      toast({
        title: t.common.error,
        description: error?.response?.data?.detail || t.common.error,
        variant: 'destructive',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const selectedTransformation = transformations?.find(
    (t) => t.id === selectedTransformationId
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t.artifacts?.generateTransformation || 'Generate Transformation'}
          </DialogTitle>
          <DialogDescription>
            {t.artifacts?.generateTransformationDesc ||
              'Apply a transformation to your notebook content and save it as an artifact'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="transformation">
              {t.transformations?.title || 'Transformation'} *
            </Label>
            {transformationsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t.common?.loading || 'Loading...'}
              </div>
            ) : (
              <Select
                value={selectedTransformationId}
                onValueChange={setSelectedTransformationId}
              >
                <SelectTrigger id="transformation">
                  <SelectValue
                    placeholder={
                      t.transformations?.selectToStart || 'Select a transformation'
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {transformations && transformations.length > 0 ? (
                    transformations.map((transformation) => (
                      <SelectItem key={transformation.id} value={transformation.id}>
                        {transformation.title || transformation.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled>
                      {t.transformations?.noTransformations || 'No transformations available'}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            )}
            {selectedTransformation?.description && (
              <p className="text-sm text-muted-foreground">
                {selectedTransformation.description}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isGenerating}
            >
              {t.common.cancel}
            </Button>
            <Button
              type="submit"
              disabled={!selectedTransformationId || isGenerating || transformationsLoading}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t.artifacts?.generating || 'Generating...'}
                </>
              ) : (
                t.artifacts?.generateTransformation || 'Generate'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
