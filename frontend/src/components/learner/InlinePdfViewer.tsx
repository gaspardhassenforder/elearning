'use client'

/**
 * InlinePdfViewer
 *
 * Embeds a PDF viewer inline in chat when the AI surfaces a PDF source.
 * Collapsed by default (PDFs need vertical space). Shows "I've read this"
 * confirmation button whenever the PDF is expanded.
 *
 * - Collapsed: shows PDF icon + title + optional page badge + relevance
 * - Expanded: renders PdfViewer (height-fixed, jumps to page) + "I've read this" button
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText, CheckCircle2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PdfViewer } from './PdfViewer'

interface InlinePdfViewerProps {
  sourceId: string
  title: string
  pageNumber?: number
  searchText?: string
  relevance?: string
  onConfirm: (message: string) => void
}

export function InlinePdfViewer({
  sourceId,
  title,
  pageNumber,
  searchText,
  relevance,
  onConfirm,
}: InlinePdfViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [confirmed, setConfirmed] = useState(false)

  const handleConfirm = () => {
    setConfirmed(true)
    setIsExpanded(false)
    onConfirm("I've read the document")
  }

  return (
    <Card className="my-2 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700 overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-warm-neutral-100 dark:hover:bg-warm-neutral-800 transition-colors"
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-foreground truncate">{title}</h4>
            {pageNumber && (
              <span className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
                p.{pageNumber}
              </span>
            )}
          </div>
          {relevance && (
            <p className="text-xs text-muted-foreground mt-0.5 truncate">{relevance}</p>
          )}
        </div>
        {confirmed && (
          <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium flex-shrink-0">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Done
          </div>
        )}
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        )}
      </button>

      {/* PDF body — only renders iframe when expanded */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          <div className="h-[480px] w-full rounded overflow-hidden border border-warm-neutral-200 dark:border-warm-neutral-700">
            <PdfViewer
              sourceId={sourceId}
              pageNumber={pageNumber}
              searchText={searchText}
            />
          </div>

          {/* Confirmation button — always visible when expanded */}
          {!confirmed && (
            <Button
              onClick={handleConfirm}
              variant="outline"
              className="w-full gap-2 border-green-500 text-green-700 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-950/30"
            >
              <CheckCircle2 className="h-4 w-4" />
              I&apos;ve read this
            </Button>
          )}
        </div>
      )}
    </Card>
  )
}
