'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from '@/lib/hooks/use-translation'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/lib/hooks/use-toast'
import { notesApi } from '@/lib/api/notes'

interface TransformationViewerProps {
  transformationId: string
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TransformationViewer({
  transformationId,
  notebookId,
  open,
  onOpenChange,
}: TransformationViewerProps) {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [copied, setCopied] = useState(false)

  // Fetch the note content - transformationId is actually the note_id
  const { data: transformationResult, isLoading, error } = useQuery({
    queryKey: ['note', transformationId],
    queryFn: async () => {
      const note = await notesApi.get(transformationId)
      return {
        title: note.title,
        content: note.content || '',
      }
    },
    enabled: open && !!transformationId,
  })

  const handleCopy = async () => {
    if (!transformationResult?.content) return

    try {
      await navigator.clipboard.writeText(transformationResult.content)
      setCopied(true)
      toast({
        title: t.common.success,
        description: t.common.copyToClipboard || 'Copied to clipboard',
      })
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy to clipboard', error)
      toast({
        title: t.common.error,
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.transformation || 'Transformation'}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (error) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.transformation || 'Transformation'}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            {t.common.errorLoading || 'Failed to load transformation result'}
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[90vw] max-w-2xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="pr-8">{transformationResult?.title || t.artifacts?.transformation || 'Transformation Result'}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <div className="flex justify-end mb-2 flex-shrink-0">
            <Button variant="outline" size="sm" onClick={handleCopy}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  {t.common.copied || 'Copied'}
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  {t.common.copyToClipboard || 'Copy'}
                </>
              )}
            </Button>
          </div>

          <ScrollArea className="flex-1 min-h-0">
            <div className="prose prose-sm max-w-none dark:prose-invert px-1">
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {transformationResult?.content || t.artifacts?.noContent || 'No content available'}
              </div>
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  )
}
