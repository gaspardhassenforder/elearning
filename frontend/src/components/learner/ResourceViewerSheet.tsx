'use client'

/**
 * ResourceViewerSheet Component
 *
 * Radix Sheet (slide-over from right) for viewing:
 * - Source content: loads full text/markdown via useSourceContent
 * - Artifact content: quiz interaction, podcast playback, summary/transformation text
 *
 * Controlled by learner-store viewerSheet state.
 * ~50% viewport width on desktop, 100% on mobile.
 */

import { useState, useEffect, useRef } from 'react'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useSourceContent } from '@/lib/hooks/use-source-content'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useLearnerArtifactPreview } from '@/lib/hooks/use-artifacts'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { sourcesApi } from '@/lib/api/sources'
import { InlineQuizWidget } from './InlineQuizWidget'
import { InlineAudioPlayer } from './InlineAudioPlayer'
import { AlertCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

function ArtifactErrorFallback() {
  return (
    <div className="text-sm text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded p-4">
      Failed to load content
    </div>
  )
}

interface ResourceViewerSheetProps {
  notebookId: string
}

export function ResourceViewerSheet({ notebookId }: ResourceViewerSheetProps) {
  const { t } = useTranslation()
  const viewerSheet = useLearnerStore((state) => state.viewerSheet)
  const closeViewerSheet = useLearnerStore((state) => state.closeViewerSheet)

  const isOpen = viewerSheet !== null

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && closeViewerSheet()}>
      <SheetContent
        side="right"
        className="w-full sm:w-[50vw] sm:max-w-[50vw] p-0 flex flex-col"
      >
        {viewerSheet?.type === 'source' && (
          <SourceViewer
            notebookId={notebookId}
            sourceId={viewerSheet.id}
            searchText={viewerSheet.searchText}
            t={t}
          />
        )}
        {viewerSheet?.type === 'artifact' && (
          <ArtifactViewer
            artifactId={viewerSheet.id}
            t={t}
          />
        )}
      </SheetContent>
    </Sheet>
  )
}

// Source content viewer
function SourceViewer({
  notebookId,
  sourceId,
  searchText,
  t,
}: {
  notebookId: string
  sourceId: string
  searchText?: string
  t: Record<string, unknown>
}) {
  const { sources } = useNotebookSources(notebookId)
  const source = sources?.find((s) => s.id === sourceId)
  const { data: content, isLoading, error, refetch } = useSourceContent(sourceId)

  const tSources = (t.learner as Record<string, unknown>)?.sources as Record<string, string>

  const isPdf = content?.file_type === 'PDF'
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [fileLoading, setFileLoading] = useState(false)

  useEffect(() => {
    if (!isPdf || !sourceId) return

    let cancelled = false
    const loadPdf = async () => {
      setFileLoading(true)
      try {
        const response = await sourcesApi.downloadLearnerFile(sourceId)
        if (cancelled) return
        const arrayBuffer = await response.data.arrayBuffer()
        const typedBlob = new Blob([arrayBuffer], { type: 'application/pdf' })
        setBlobUrl(URL.createObjectURL(typedBlob))
      } catch {
        // Fall back to text display
      } finally {
        if (!cancelled) setFileLoading(false)
      }
    }
    void loadPdf()
    return () => {
      cancelled = true
    }
  }, [isPdf, sourceId])

  // Cleanup blob URL on unmount or sourceId change
  useEffect(() => {
    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
  }, [blobUrl])

  return (
    <>
      <SheetHeader className="px-6 py-4 border-b flex-shrink-0">
        <SheetTitle className="line-clamp-2">
          {source?.title || tSources?.untitled || 'Document'}
        </SheetTitle>
        {content?.word_count && (
          <SheetDescription>
            {content.word_count.toLocaleString()} {tSources?.words || 'words'}
            {content.file_type && ` · ${content.file_type}`}
          </SheetDescription>
        )}
      </SheetHeader>
      {isPdf && (fileLoading || blobUrl) ? (
        <div className="flex-1 min-h-0">
          {fileLoading ? (
            <div className="flex items-center justify-center h-full">
              <LoadingSpinner />
            </div>
          ) : blobUrl ? (
            <iframe
              src={searchText ? `${blobUrl}#search=${encodeURIComponent(searchText.slice(0, 80))}` : blobUrl}
              title={source?.title || 'PDF'}
              className="w-full h-full border-0"
            />
          ) : null}
        </div>
      ) : (
        <ScrollArea className="flex-1 px-6 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <AlertCircle className="h-8 w-8 text-amber-500" />
              <p className="text-sm text-muted-foreground">
                {tSources?.contentError || 'Failed to load content'}
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                {tSources?.retry || 'Retry'}
              </Button>
            </div>
          ) : content?.content ? (
            <TextContentWithHighlight content={content.content} searchText={searchText} />
          ) : (
            <p className="text-sm text-muted-foreground text-center py-12">
              {tSources?.noContent || 'No content available'}
            </p>
          )}
        </ScrollArea>
      )}
    </>
  )
}

// Text content with search highlight
function TextContentWithHighlight({
  content,
  searchText,
}: {
  content: string
  searchText?: string
}) {
  const highlightRef = useRef<HTMLElement>(null)

  // Scroll to first highlighted match after render
  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [searchText, content])

  if (!searchText) {
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
          {content}
        </pre>
      </div>
    )
  }

  // Find and highlight the first occurrence of searchText (case-insensitive)
  const lowerContent = content.toLowerCase()
  const lowerSearch = searchText.toLowerCase().slice(0, 100) // Use first 100 chars for matching
  const matchIndex = lowerContent.indexOf(lowerSearch)

  if (matchIndex === -1) {
    // No match found - render plain
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
          {content}
        </pre>
      </div>
    )
  }

  const before = content.slice(0, matchIndex)
  const match = content.slice(matchIndex, matchIndex + lowerSearch.length)
  const after = content.slice(matchIndex + lowerSearch.length)

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
        {before}
        <mark ref={highlightRef} className="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">
          {match}
        </mark>
        {after}
      </pre>
    </div>
  )
}

// Artifact content viewer
function ArtifactViewer({
  artifactId,
  t,
}: {
  artifactId: string
  t: Record<string, unknown>
}) {
  const { data: preview, isLoading, error, refetch } = useLearnerArtifactPreview(artifactId)

  const tArtifacts = (t.learner as Record<string, unknown>)?.artifacts as Record<string, string>

  if (isLoading) {
    return (
      <>
        <SheetHeader className="px-6 py-4 border-b flex-shrink-0">
          <SheetTitle>{tArtifacts?.loadingPreview || 'Loading...'}</SheetTitle>
        </SheetHeader>
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </>
    )
  }

  if (error || !preview) {
    return (
      <>
        <SheetHeader className="px-6 py-4 border-b flex-shrink-0">
          <SheetTitle>{tArtifacts?.previewError || 'Error'}</SheetTitle>
        </SheetHeader>
        <div className="flex-1 flex flex-col items-center justify-center gap-3 px-6">
          <AlertCircle className="h-8 w-8 text-amber-500" />
          <p className="text-sm text-muted-foreground">
            {tArtifacts?.previewError || 'Failed to load preview'}
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            {tArtifacts?.retry || 'Retry'}
          </Button>
        </div>
      </>
    )
  }

  return (
    <>
      <SheetHeader className="px-6 py-4 border-b flex-shrink-0">
        <SheetTitle className="line-clamp-2">
          {preview.title}
        </SheetTitle>
        <SheetDescription>
          {tArtifacts?.[preview.artifact_type] || preview.artifact_type}
        </SheetDescription>
      </SheetHeader>
      <ScrollArea className="flex-1 px-6 py-4">
        <ErrorBoundary fallback={ArtifactErrorFallback}>
          {preview.artifact_type === 'quiz' && (
            <InlineQuizWidget
              quizId={preview.id}
              title={preview.title}
              description=""
              questions={(preview.questions || []).map((q) => ({
                text: q.question,
                options: q.options,
              }))}
              totalQuestions={preview.question_count || preview.questions?.length || 0}
              quizUrl=""
            />
          )}

          {preview.artifact_type === 'podcast' && (
            <InlineAudioPlayer
              podcastId={preview.id}
              title={preview.title}
              audioUrl={preview.audio_url || ''}
              durationMinutes={0}
              transcriptUrl={`/api/podcasts/${preview.id}/transcript`}
              status={preview.audio_url ? 'completed' : 'generating'}
            />
          )}

          {(preview.artifact_type === 'summary' || preview.artifact_type === 'transformation') && (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>
                {preview.content || tArtifacts?.noContent || 'No content available'}
              </ReactMarkdown>
            </div>
          )}
        </ErrorBoundary>
      </ScrollArea>
    </>
  )
}
