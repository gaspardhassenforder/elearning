'use client'

/**
 * Story 5.2: Artifact Card Component
 *
 * Expandable card displaying artifact metadata in the Artifacts panel.
 * Shows type-specific content when expanded via lazy-loaded preview.
 *
 * Features:
 * - Collapsed: type icon + title + created date + chevron
 * - Expanded: lazy-loaded type-specific content
 *   - Quiz: InlineQuizWidget component
 *   - Podcast: InlineAudioPlayer component
 *   - Summary/Transformation: ScrollArea with text content
 * - Loading spinner during preview fetch
 * - Error state with retry button
 * - Smooth transition animation
 */

import { FileQuestion, Headphones, FileText, ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerArtifactPreview } from '@/lib/hooks/use-artifacts'
import { LearnerArtifactListItem, QuizPreview, PodcastPreview, SummaryPreview, TransformationPreview } from '@/lib/api/artifacts'
import { InlineQuizWidget } from './InlineQuizWidget'
import { InlineAudioPlayer } from './InlineAudioPlayer'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import ReactMarkdown from 'react-markdown'

interface ArtifactCardProps {
  artifact: LearnerArtifactListItem
  isExpanded: boolean
  onToggleExpand: () => void
}

export function ArtifactCard({ artifact, isExpanded, onToggleExpand }: ArtifactCardProps) {
  const { t } = useTranslation()

  // Lazy load preview only when expanded
  const {
    data: previewData,
    isLoading: previewLoading,
    error: previewError,
    refetch: retryPreview
  } = useLearnerArtifactPreview(isExpanded ? artifact.id : null)

  // Get icon based on artifact type
  const getArtifactIcon = () => {
    switch (artifact.artifact_type) {
      case 'quiz':
        return <FileQuestion className="h-4 w-4 text-primary" />
      case 'podcast':
        return <Headphones className="h-4 w-4 text-primary" />
      case 'summary':
      case 'transformation':
        return <FileText className="h-4 w-4 text-muted-foreground" />
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />
    }
  }

  // Get type label
  const getTypeLabel = () => {
    const labels: Record<string, string> = {
      quiz: t.learner?.artifacts?.quiz || 'Quiz',
      podcast: t.learner?.artifacts?.podcast || 'Podcast',
      summary: t.learner?.artifacts?.summary || 'Summary',
      transformation: t.learner?.artifacts?.transformation || 'Transformation',
    }
    return labels[artifact.artifact_type] || artifact.artifact_type
  }

  // Format created date
  const getCreatedLabel = () => {
    try {
      const date = new Date(artifact.created)
      const timeAgo = formatDistanceToNow(date, { addSuffix: true })
      const template = t.learner?.artifacts?.createdAt || 'Created {time}'
      return template.replace('{time}', timeAgo)
    } catch {
      return ''
    }
  }

  const handleCardClick = () => {
    onToggleExpand()
  }

  const handleRetry = (e: React.MouseEvent) => {
    e.stopPropagation()
    retryPreview()
  }

  // Render type-specific expanded content
  const renderExpandedContent = () => {
    if (previewLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">
            {t.learner?.artifacts?.loadingPreview || 'Loading preview...'}
          </span>
        </div>
      )
    }

    if (previewError) {
      return (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <AlertCircle className="h-8 w-8 text-destructive mb-2" />
          <p className="text-sm text-muted-foreground mb-3">
            {t.learner?.artifacts?.previewError || 'Failed to load preview'}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
          >
            {t.learner?.artifacts?.retry || 'Try Again'}
          </Button>
        </div>
      )
    }

    if (!previewData) {
      return null
    }

    // Render based on artifact type
    switch (previewData.artifact_type) {
      case 'quiz':
        return renderQuizContent(previewData as QuizPreview)
      case 'podcast':
        return renderPodcastContent(previewData as PodcastPreview)
      case 'summary':
      case 'transformation':
        return renderTextContent(previewData as SummaryPreview | TransformationPreview)
      default:
        return (
          <p className="text-sm text-muted-foreground">
            {t.learner?.artifacts?.unsupportedType || 'Unsupported artifact type'}
          </p>
        )
    }
  }

  // Quiz content using InlineQuizWidget
  const renderQuizContent = (quiz: QuizPreview) => {
    // Transform quiz preview data to InlineQuizWidget format
    const questions = quiz.questions.map((q) => ({
      text: q.question,
      options: q.choices,
    }))

    return (
      <InlineQuizWidget
        quizId={quiz.id}
        title={quiz.title}
        questions={questions}
        totalQuestions={quiz.question_count}
        // Note: No quizUrl for learner panel - quiz is viewed inline only
      />
    )
  }

  // Podcast content using InlineAudioPlayer
  const renderPodcastContent = (podcast: PodcastPreview) => {
    // Parse duration from "MM:SS" format to minutes
    let durationMinutes = 0
    if (podcast.duration) {
      const parts = podcast.duration.split(':')
      if (parts.length === 2) {
        durationMinutes = parseInt(parts[0]) + parseInt(parts[1]) / 60
      }
    }
    const isGenerating =
      podcast.status === 'generating' || !podcast.audio_url
    const podcastId = podcast.id || artifact.id
    const title = podcast.title || artifact.title

    return (
      <InlineAudioPlayer
        podcastId={podcastId}
        title={title}
        audioUrl={podcast.audio_url || ''}
        durationMinutes={Math.round(durationMinutes)}
        transcriptUrl={podcastId && !isGenerating ? `/api/podcasts/${podcastId}/transcript` : undefined}
        status={isGenerating ? 'generating' : 'completed'}
      />
    )
  }

  // Text content (summary/transformation) in ScrollArea
  const renderTextContent = (content: SummaryPreview | TransformationPreview) => {
    return (
      <div className="space-y-3">
        {/* Metadata row */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>{content.word_count.toLocaleString()} {t.learner?.artifacts?.words || 'words'}</span>
          {'transformation_name' in content && content.transformation_name && (
            <span>{(t.learner?.artifacts?.type || 'Type: {name}').replace('{name}', content.transformation_name)}</span>
          )}
        </div>

        {/* Content scroll area */}
        <ScrollArea className="max-h-[calc(100vh-300px)]">
          <div className="prose prose-sm dark:prose-invert max-w-none pr-4">
            <ReactMarkdown>
              {content.content || (t.learner?.artifacts?.noContent || 'No content available')}
            </ReactMarkdown>
          </div>
        </ScrollArea>
      </div>
    )
  }

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all duration-150 ease-in-out",
        !isExpanded && "hover:bg-accent/50",
        isExpanded && "bg-background shadow-md border-primary/20"
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-3">
        {/* Header section - always visible */}
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">
            {getArtifactIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium line-clamp-1">
              {artifact.title}
            </h3>
            <p className="text-xs text-muted-foreground">
              {getCreatedLabel()}
            </p>
          </div>
          <div className="flex-shrink-0">
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>

        {/* Expanded content section */}
        {isExpanded && (
          <div className="mt-4 border-t pt-4" onClick={(e) => e.stopPropagation()}>
            {renderExpandedContent()}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
