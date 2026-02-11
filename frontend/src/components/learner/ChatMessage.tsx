'use client'

/**
 * ChatMessage Component
 *
 * Renders a single chat message with ChatGPT-inspired styling:
 * - Assistant messages: left-aligned with avatar, no background, full-width
 * - User messages: right-aligned, subtle background bubble
 * - Supports tool call rendering (document snippets, quizzes, podcasts)
 * - Streaming cursor on last assistant message
 * - Details toggle for transparency
 */

import { useState } from 'react'
import { MessageSquare } from 'lucide-react'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { DocumentSnippetCard } from './DocumentSnippetCard'
import { ModuleSuggestionCard } from './ModuleSuggestionCard'
import { InlineQuizWidget } from './InlineQuizWidget'
import { InlineAudioPlayer } from './InlineAudioPlayer'
import { ChatErrorMessage } from './ChatErrorMessage'
import { DetailsToggle } from './DetailsToggle'
import { ToolCallDetails } from './ToolCallDetails'
import { useLearnerStore } from '@/lib/stores/learner-store'
import type { LearnerChatMessage } from '@/lib/api/learner-chat'
import type { SuggestedModule } from '@/lib/types/api'

interface ChatMessageProps {
  message: LearnerChatMessage
  index: number
  isLastAssistant: boolean
  isStreaming: boolean
  t: Record<string, unknown>
}

function QuizErrorFallback() {
  return (
    <div className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
      Failed to load quiz. Please try again later.
    </div>
  )
}

function PodcastErrorFallback() {
  return (
    <div className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
      Failed to load podcast player. Please try again later.
    </div>
  )
}

export function ChatMessage({ message, index, isLastAssistant, isStreaming, t }: ChatMessageProps) {
  const [detailsExpanded, setDetailsExpanded] = useState(false)
  const openViewerSheet = useLearnerStore((state) => state.openViewerSheet)

  const tLearner = t.learner as Record<string, unknown>
  const tChat = tLearner?.chat as Record<string, string>
  const tLearnerErrors = t.learnerErrors as Record<string, string>

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-accent/30 rounded-2xl px-4 py-3">
          <p className="text-base leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

  // Assistant message
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
        <MessageSquare className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-base leading-relaxed text-foreground/90">
          {message.content}
          {isLastAssistant && isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse" />
          )}
        </p>

        {/* Tool call artifacts */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-3 space-y-2">
            {/* Document snippets */}
            {message.toolCalls
              .filter((tc) => tc.toolName === 'surface_document' && tc.result && !tc.result.error)
              .map((tc, tcIndex) => (
                <DocumentSnippetCard
                  key={`doc-${index}-${tcIndex}`}
                  sourceId={tc.result!.source_id as string}
                  title={tc.result!.title as string}
                  excerpt={tc.result!.excerpt as string}
                  sourceType={tc.result!.source_type as string}
                  relevance={tc.result!.relevance as string}
                />
              ))}

            {/* Inline quiz widgets */}
            {message.toolCalls
              .filter((tc) => tc.toolName === 'surface_quiz' && tc.result && !tc.result.error)
              .map((tc, tcIndex) => (
                <ErrorBoundary key={`quiz-boundary-${index}-${tcIndex}`} fallback={QuizErrorFallback}>
                  <InlineQuizWidget
                    key={`quiz-${index}-${tcIndex}`}
                    quizId={tc.result!.quiz_id as string}
                    title={tc.result!.title as string}
                    description={tc.result!.description as string}
                    questions={(tc.result!.questions || []) as Array<{ text: string; options: string[] }>}
                    totalQuestions={(tc.result!.total_questions || 0) as number}
                    quizUrl={tc.result!.quiz_url as string}
                  />
                </ErrorBoundary>
              ))}

            {/* Inline podcast players */}
            {message.toolCalls
              .filter((tc) => tc.toolName === 'surface_podcast' && tc.result && !tc.result.error)
              .map((tc, tcIndex) => (
                <ErrorBoundary key={`podcast-boundary-${index}-${tcIndex}`} fallback={PodcastErrorFallback}>
                  <InlineAudioPlayer
                    key={`podcast-${index}-${tcIndex}`}
                    podcastId={tc.result!.podcast_id as string}
                    title={tc.result!.title as string}
                    audioUrl={tc.result!.audio_url as string}
                    durationMinutes={tc.result!.duration_minutes as number}
                    transcriptUrl={tc.result!.transcript_url as string}
                    status={tc.result!.status as string}
                  />
                </ErrorBoundary>
              ))}

            {/* Module suggestions on completion */}
            {message.toolCalls
              .filter((tc) =>
                tc.toolName === 'check_off_objective' &&
                tc.result &&
                tc.result.all_complete === true &&
                tc.result.suggested_modules &&
                (tc.result.suggested_modules as SuggestedModule[]).length > 0
              )
              .map((tc, tcIndex) => (
                <div key={`suggestions-${index}-${tcIndex}`} className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">
                    {tChat?.suggestedModules || 'Suggested Modules'}
                  </p>
                  {(tc.result!.suggested_modules as SuggestedModule[]).map((module: SuggestedModule, modIndex: number) => (
                    <ModuleSuggestionCard
                      key={`module-${index}-${tcIndex}-${modIndex}`}
                      suggestion={{ id: module.id, title: module.title, description: module.description }}
                    />
                  ))}
                </div>
              ))}

            {/* Error messages for failed tool calls */}
            {message.toolCalls
              .filter((tc) => tc.result?.error)
              .map((tc, tcIndex) => (
                <ChatErrorMessage
                  key={`error-${index}-${tcIndex}`}
                  message={tc.result!.error as string}
                  recoverable={(tc.result!.recoverable ?? false) as boolean}
                  className="text-xs"
                />
              ))}
          </div>
        )}

        {/* SSE error events */}
        {message.sseError && (
          <div className="mt-2">
            <ChatErrorMessage
              message={message.sseError.message || message.sseError.error || tLearnerErrors?.chatError || 'Something went wrong'}
              recoverable={message.sseError.recoverable ?? false}
              className="text-xs"
            />
          </div>
        )}

        {/* Details toggle */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2">
            <DetailsToggle
              message={message}
              isExpanded={detailsExpanded}
              onToggle={() => setDetailsExpanded(!detailsExpanded)}
            />
            {detailsExpanded && (
              <ToolCallDetails
                toolCalls={message.toolCalls}
                messageContent={message.content}
                onSourceSelect={(sourceId) => {
                  openViewerSheet({ type: 'source', id: sourceId })
                }}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
