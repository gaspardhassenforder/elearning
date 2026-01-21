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

  // For now, we'll need to fetch transformation results
  // Since transformations API doesn't have a direct get-by-id endpoint for results,
  // we'll need to check the artifacts API or create a placeholder
  // For MVP, we'll show a placeholder that can be enhanced later
  const { data: transformationResult, isLoading } = useQuery({
    queryKey: ['transformation', transformationId],
    queryFn: async () => {
      // TODO: Implement actual API call when backend endpoint is available
      // For now, return placeholder data
      return {
        content: 'Transformation result content will be displayed here once the backend endpoint is implemented.',
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
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{t.artifacts?.transformation || 'Transformation'}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{t.artifacts?.transformation || 'Transformation Result'}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex justify-end mb-2">
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

          <ScrollArea className="flex-1">
            <div className="prose max-w-none dark:prose-invert p-4">
              <pre className="whitespace-pre-wrap text-sm bg-muted p-4 rounded">
                {transformationResult?.content || t.artifacts?.noContent || 'No content available'}
              </pre>
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  )
}
