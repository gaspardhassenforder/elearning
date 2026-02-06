'use client'

/**
 * Story 4.1: Learner Document Card
 * Story 4.3: Highlight animation support
 * Story 5.1: Expand/collapse with full content display
 *
 * Collapsible card displaying document metadata in sources panel.
 * Read-only for learners (no edit/delete actions).
 *
 * Story 4.3 additions:
 * - Ref forwarding for scroll-to functionality
 * - Highlight animation (3s glow effect)
 *
 * Story 5.1 additions:
 * - Expandable card showing full document content
 * - Lazy loading content on expand via useSourceContent hook
 * - Loading and error states
 * - Accordion behavior (only one expanded at a time via SourcesPanel)
 */

import { forwardRef } from 'react'
import { FileText, File, ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useSourceContent } from '@/lib/hooks/use-source-content'
import { cn } from '@/lib/utils'

interface DocumentCardProps {
  source: {
    id: string
    title: string | null
    file_type?: string | null
    status?: string
    embedded?: boolean
  }
  isHighlighted?: boolean // Story 4.3: Highlight state
  isExpanded?: boolean // Story 5.1: Expansion state from parent
  onToggleExpand?: () => void // Story 5.1: Callback to toggle expand state
}

export const DocumentCard = forwardRef<HTMLDivElement, DocumentCardProps>(
  ({ source, isHighlighted = false, isExpanded = false, onToggleExpand }, ref) => {
  const { t } = useTranslation()

  // Story 5.1: Fetch content when expanded (lazy loading)
  const {
    data: contentData,
    isLoading: contentLoading,
    error: contentError,
    refetch: retryContent
  } = useSourceContent(isExpanded ? source.id : null)

  const getStatusBadge = () => {
    if (source.status === 'processing') {
      return <Badge variant="secondary">{t.learner.sources.processing}</Badge>
    }
    if (source.status === 'error') {
      return <Badge variant="destructive">{t.learner.sources.error}</Badge>
    }
    if (source.embedded) {
      return <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600">{t.learner.sources.ready}</Badge>
    }
    return null
  }

  const getFileIcon = () => {
    const fileType = source.file_type?.toLowerCase()

    // Map file types to appropriate icons
    if (fileType?.includes('pdf')) {
      return <File className="h-4 w-4 text-red-500" />
    }
    if (fileType?.includes('doc') || fileType?.includes('word')) {
      return <File className="h-4 w-4 text-blue-500" />
    }
    if (fileType?.includes('sheet') || fileType?.includes('excel')) {
      return <File className="h-4 w-4 text-green-500" />
    }
    if (fileType?.includes('text') || fileType?.includes('txt')) {
      return <FileText className="h-4 w-4 text-gray-500" />
    }

    return <FileText className="h-4 w-4 text-muted-foreground" />
  }

  const handleCardClick = () => {
    if (onToggleExpand) {
      onToggleExpand()
    }
  }

  const handleRetry = (e: React.MouseEvent) => {
    e.stopPropagation()
    retryContent()
  }

  // Story 5.1: Brief description for collapsed state
  const getBriefDescription = () => {
    if (contentData?.content) {
      // First 100 characters of content
      const preview = contentData.content.substring(0, 100)
      return preview.length < contentData.content.length ? `${preview}...` : preview
    }
    return null
  }

  return (
    <Card
      ref={ref}
      className={cn(
        "cursor-pointer transition-all",
        !isExpanded && "hover:bg-accent/50",
        source.status === 'processing' && "opacity-60",
        // Story 4.3: Highlight animation
        isHighlighted && "ring-2 ring-primary ring-offset-2 shadow-lg animate-pulse",
        // Story 5.1: Expanded state styling
        isExpanded && "bg-background shadow-md border-primary/20"
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-3">
        {/* Header section - always visible */}
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {getFileIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium line-clamp-2 mb-1">
              {source.title || t.learner.sources.untitled}
            </h3>
            {source.file_type && !isExpanded && (
              <p className="text-xs text-muted-foreground">
                {source.file_type}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {getStatusBadge()}
            {/* Story 5.1: Expand/collapse chevron */}
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>

        {/* Story 5.1: Expanded content section */}
        {isExpanded && (
          <div className="mt-4 border-t pt-4" onClick={(e) => e.stopPropagation()}>
            {contentLoading ? (
              // Loading state
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">
                  {t.learner.sources.loadingContent}
                </span>
              </div>
            ) : contentError ? (
              // Error state
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <AlertCircle className="h-8 w-8 text-destructive mb-2" />
                <p className="text-sm text-muted-foreground mb-3">
                  {t.learner.sources.contentError}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRetry}
                >
                  {t.learner.sources.retry}
                </Button>
              </div>
            ) : contentData ? (
              // Content loaded
              <div className="space-y-3">
                {/* Metadata row */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  {contentData.file_type && (
                    <span>{contentData.file_type}</span>
                  )}
                  <span>
                    {contentData.word_count.toLocaleString()} {t.learner.sources.words}
                  </span>
                </div>

                {/* Content scroll area */}
                <ScrollArea className="max-h-[calc(100vh-300px)]">
                  <div className="text-sm whitespace-pre-wrap leading-relaxed pr-4">
                    {contentData.content || t.learner.sources.noContent}
                  </div>
                </ScrollArea>
              </div>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  )
})

DocumentCard.displayName = 'DocumentCard'
