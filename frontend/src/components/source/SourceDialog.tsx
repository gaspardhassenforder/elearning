'use client'

import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { SourceDetailContent } from './SourceDetailContent'
import { useTranslation } from '@/lib/hooks/use-translation'

interface SourceDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceId: string | null
}

/**
 * Source Dialog Component
 *
 * Displays source details in a modal dialog.
 * Includes a "Chat with source" button that opens the full source page in a new tab.
 */
export function SourceDialog({ open, onOpenChange, sourceId }: SourceDialogProps) {
  const { t } = useTranslation()
  // Ensure source ID has 'source:' prefix for API calls and routing
  const sourceIdWithPrefix = sourceId
    ? (sourceId.includes(':') ? sourceId : `source:${sourceId}`)
    : null

  const handleChatClick = () => {
    if (sourceIdWithPrefix) {
      window.open(`/sources/${sourceIdWithPrefix}`, '_blank')
      // Modal stays open after opening chat
    }
  }

  const handleClose = () => {
    onOpenChange(false)
  }

  if (!sourceIdWithPrefix) {
    return null
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[75vw] w-[75vw] h-[82vh] max-h-[82vh] flex flex-col p-0">
        {/* Accessibility title (hidden visually but read by screen readers) */}
        <DialogTitle className="sr-only">{t.sources.detailsTitle}</DialogTitle>

        {/* Source detail content — fills dialog, each tab scrolls independently */}
        <div className="flex-1 overflow-hidden min-h-0 flex flex-col">
          <SourceDetailContent
            sourceId={sourceIdWithPrefix}
            showChatButton={true}
            onChatClick={handleChatClick}
            onClose={handleClose}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
