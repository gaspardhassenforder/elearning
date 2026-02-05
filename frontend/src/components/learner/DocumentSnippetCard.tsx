'use client'

/**
 * Story 4.3: Document Snippet Card Component
 *
 * Displays inline document snippets in chat with "Open in sources" link.
 * Registered as assistant-ui custom message part for tool-call results.
 *
 * Features:
 * - Document title, excerpt (max 200 chars with truncation)
 * - "Open in sources" link triggers panel expansion + scroll
 * - Subtle card styling with warm neutral palette
 * - Hover lift effect
 */

import { FileText } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerStore } from '@/lib/stores/learner-store'

interface DocumentSnippetCardProps {
  sourceId: string
  title: string
  excerpt: string
  sourceType?: string
  relevance?: string
}

export function DocumentSnippetCard({
  sourceId,
  title,
  excerpt,
  sourceType = 'document',
  relevance,
}: DocumentSnippetCardProps) {
  const { t } = useTranslation()
  const expandAndScrollToSource = useLearnerStore((state) => state.expandAndScrollToSource)

  const handleOpenInSources = (e: React.MouseEvent) => {
    e.preventDefault()
    expandAndScrollToSource(sourceId)
  }

  // Truncate excerpt to 200 chars if needed (should already be done by backend, but double-check)
  const displayExcerpt = excerpt.length > 200 ? excerpt.slice(0, 197) + '...' : excerpt

  return (
    <Card
      className="my-2 p-3 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700 hover:shadow-md transition-shadow cursor-pointer"
      onClick={handleOpenInSources}
    >
      <div className="flex items-start gap-3">
        {/* Document icon */}
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Document title */}
          <h4 className="text-sm font-semibold text-foreground mb-1 truncate">
            {title}
          </h4>

          {/* Excerpt */}
          <p className="text-xs text-muted-foreground mb-2 line-clamp-3">
            {displayExcerpt}
          </p>

          {/* Open in sources link */}
          <button
            onClick={handleOpenInSources}
            className="text-xs text-primary hover:underline font-medium"
          >
            {t.learner.openInSources || 'Open in sources'} →
          </button>
        </div>
      </div>
    </Card>
  )
}
