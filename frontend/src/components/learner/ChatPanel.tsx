'use client'

/**
 * Story 4.1: Learner Chat Panel with assistant-ui
 * Story 4.2: Proactive AI Teacher Greeting
 * Story 4.3: Document Snippet Rendering
 * Story 4.8: Persistent Chat History
 *
 * Features:
 * - SSE streaming with token-by-token rendering
 * - assistant-ui Thread component integration
 * - Proactive AI greeting (personalized on first load)
 * - Flowing AI messages, subtle user backgrounds
 * - Streaming cursor during generation
 * - Document snippet cards inline (Story 4.3)
 * - Persistent chat history loading (Story 4.8)
 */

import { useEffect, useState, useRef } from 'react'
import { MessageSquare, ArrowDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerChat, useChatHistory } from '@/lib/hooks/use-learner-chat'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { DocumentSnippetCard } from './DocumentSnippetCard'
import { ModuleSuggestionCard } from './ModuleSuggestionCard'
import { InlineQuizWidget } from './InlineQuizWidget'
import { InlineAudioPlayer } from './InlineAudioPlayer'
import { AsyncStatusBar } from './AsyncStatusBar'
import { useJobStatus } from '@/lib/hooks/use-job-status'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { useToast } from '@/lib/hooks/use-toast'
import type { SuggestedModule } from '@/lib/types/api'

interface ChatPanelProps {
  notebookId: string
}

export function ChatPanel({ notebookId }: ChatPanelProps) {
  const { t } = useTranslation()
  const { toast } = useToast()
  const [mounted, setMounted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Story 4.7: Access active job state from store
  const { activeJob, setActiveJob, clearActiveJob } = useLearnerStore((state) => ({
    activeJob: state.activeJob,
    setActiveJob: state.setActiveJob,
    clearActiveJob: state.clearActiveJob,
  }))

  // Wait for client-side mounting (assistant-ui uses browser APIs)
  useEffect(() => {
    setMounted(true)
  }, [])

  // Story 4.8: Load chat history
  const {
    data: historyData,
    isLoading: isLoadingHistory,
    error: historyError,
  } = useChatHistory(notebookId)

  const {
    isLoading,
    isStreaming,
    error,
    sendMessage,
    messages,
  } = useLearnerChat(notebookId)

  // Story 4.8: Merge history with current messages (history first, then new messages)
  const allMessages = historyLoaded && historyData?.messages
    ? [...historyData.messages, ...messages]
    : messages

  // Story 4.8: Track when history finishes loading
  useEffect(() => {
    if (!isLoadingHistory && historyData && !historyLoaded) {
      setHistoryLoaded(true)
    }
  }, [isLoadingHistory, historyData, historyLoaded])

  // Story 4.8: Auto-scroll to bottom after history loads
  useEffect(() => {
    if (historyLoaded && allMessages.length > 0) {
      // Delay scroll slightly to ensure messages are rendered
      const timer = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [historyLoaded, allMessages.length])

  // Story 4.8: Detect user manual scroll
  const handleScroll = () => {
    const container = messagesContainerRef.current
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight

    // Consider "at bottom" if within 50px
    const isAtBottom = distanceFromBottom < 50

    setIsUserScrolledUp(!isAtBottom)
    setShowScrollButton(!isAtBottom)
  }

  // Story 4.8: Scroll to bottom function
  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
    setIsUserScrolledUp(false)
    setShowScrollButton(false)
  }

  // Auto-scroll to bottom when messages change or streaming updates
  // Only if user hasn't manually scrolled up
  useEffect(() => {
    if (!isUserScrolledUp) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isStreaming, isUserScrolledUp])

  // Story 4.7: Poll job status when active job exists
  const { status, progress, error: jobError } = useJobStatus(
    activeJob?.jobId || null,
    {
      notebookId,
      onComplete: () => {
        toast({
          title: t.asyncStatus.artifactReady.replace('{type}', activeJob?.artifactType || 'artifact'),
          description: t.asyncStatus.artifactReadyDescription,
        })
      },
      onError: (errorMsg) => {
        toast({
          title: t.asyncStatus.artifactFailed.replace('{type}', activeJob?.artifactType || 'artifact'),
          description: errorMsg,
          variant: 'destructive',
        })
      },
    }
  )

  if (!mounted) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0 border-b">
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          {t.learner.chat.title}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        {isLoading || isLoadingHistory ? (
          <div className="flex items-center justify-center h-full" data-testid="history-loading-skeleton">
            <LoadingSpinner size="lg" />
          </div>
        ) : error || historyError ? (
          <div className="flex items-center justify-center h-full p-6 text-center">
            <div>
              <p className="text-sm text-muted-foreground mb-2">{t.learner.chat.error}</p>
              <p className="text-xs text-muted-foreground">{t.learner.chat.errorDesc}</p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col relative">
            {/* Chat Messages Area */}
            <div
              ref={messagesContainerRef}
              onScroll={handleScroll}
              className="flex-1 overflow-y-auto p-4 space-y-4"
            >
              {allMessages.length === 0 && isStreaming ? (
                // Story 4.2: Show loading indicator while fetching greeting
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-4 w-4 text-primary animate-pulse" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {t.learner.chat.greetingLoading || 'Preparing your personalized greeting...'}
                    </p>
                  </div>
                </div>
              ) : allMessages.length === 0 ? (
                // Fallback empty state (shouldn't normally be seen due to auto greeting request)
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="text-sm leading-relaxed">
                      {t.learner.chat.greeting}
                    </p>
                  </div>
                </div>
              ) : (
                allMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex items-start gap-3 ${
                      message.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <MessageSquare className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`flex-1 max-w-[85%] ${
                        message.role === 'user'
                          ? 'bg-accent/50 rounded-lg p-3'
                          : ''
                      }`}
                    >
                      <p className={`text-sm leading-relaxed ${
                        message.role === 'assistant' ? 'text-foreground/90' : ''
                      }`}>
                        {message.content}
                        {/* Show streaming cursor on last assistant message during streaming */}
                        {message.role === 'assistant' &&
                         index === allMessages.length - 1 &&
                         isStreaming && (
                          <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse" />
                        )}
                      </p>

                      {/* Story 4.3, 4.6: Render artifact cards for tool calls */}
                      {message.role === 'assistant' && message.toolCalls && message.toolCalls.length > 0 && (
                        <div className="mt-2 space-y-2">
                          {/* Successful document snippets */}
                          {message.toolCalls
                            .filter((tc) => tc.toolName === 'surface_document' && tc.result && !tc.result.error)
                            .map((tc, tcIndex) => (
                              <DocumentSnippetCard
                                key={`${index}-${tcIndex}`}
                                sourceId={tc.result!.source_id}
                                title={tc.result!.title}
                                excerpt={tc.result!.excerpt}
                                sourceType={tc.result!.source_type}
                                relevance={tc.result!.relevance}
                              />
                            ))}

                          {/* Story 4.6: Inline quiz widgets */}
                          {message.toolCalls
                            .filter((tc) => tc.toolName === 'surface_quiz' && tc.result && !tc.result.error)
                            .map((tc, tcIndex) => (
                              <ErrorBoundary key={`quiz-boundary-${index}-${tcIndex}`} fallback={
                                <div className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
                                  Failed to load quiz. Please try again later.
                                </div>
                              }>
                                <InlineQuizWidget
                                  key={`quiz-${index}-${tcIndex}`}
                                  quizId={tc.result!.quiz_id}
                                  title={tc.result!.title}
                                  description={tc.result!.description}
                                  questions={tc.result!.questions || []}
                                  totalQuestions={tc.result!.total_questions || 0}
                                  quizUrl={tc.result!.quiz_url}
                                />
                              </ErrorBoundary>
                            ))}

                          {/* Story 4.6: Inline podcast players */}
                          {message.toolCalls
                            .filter((tc) => tc.toolName === 'surface_podcast' && tc.result && !tc.result.error)
                            .map((tc, tcIndex) => (
                              <ErrorBoundary key={`podcast-boundary-${index}-${tcIndex}`} fallback={
                                <div className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
                                  Failed to load podcast player. Please try again later.
                                </div>
                              }>
                                <InlineAudioPlayer
                                  key={`podcast-${index}-${tcIndex}`}
                                  podcastId={tc.result!.podcast_id}
                                  title={tc.result!.title}
                                  audioUrl={tc.result!.audio_url}
                                  durationMinutes={tc.result!.duration_minutes}
                                  transcriptUrl={tc.result!.transcript_url}
                                  status={tc.result!.status}
                                />
                              </ErrorBoundary>
                            ))}

                          {/* Story 4.5: Module suggestions on completion */}
                          {message.toolCalls
                            .filter((tc) =>
                              tc.toolName === 'check_off_objective' &&
                              tc.result &&
                              tc.result.all_complete === true &&
                              tc.result.suggested_modules &&
                              tc.result.suggested_modules.length > 0
                            )
                            .map((tc, tcIndex) => (
                              <div key={`suggestions-${index}-${tcIndex}`} className="space-y-2">
                                <p className="text-xs font-medium text-muted-foreground">
                                  {t.learner.chat.suggestedModules}
                                </p>
                                {tc.result!.suggested_modules.map((module: SuggestedModule, modIndex: number) => (
                                  <ModuleSuggestionCard
                                    key={`module-${index}-${tcIndex}-${modIndex}`}
                                    moduleId={module.id}
                                    title={module.title}
                                    description={module.description}
                                  />
                                ))}
                              </div>
                            ))}

                          {/* Error messages for failed tool calls */}
                          {message.toolCalls
                            .filter((tc) => tc.result?.error)
                            .map((tc, tcIndex) => (
                              <div
                                key={`error-${index}-${tcIndex}`}
                                className="text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded px-2 py-1"
                              >
                                ⚠️ {tc.result!.error}
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {/* Scroll anchor for auto-scroll */}
              <div ref={messagesEndRef} />
            </div>

            {/* Story 4.8: Scroll to bottom button */}
            {showScrollButton && (
              <div className="absolute bottom-20 right-6 z-10">
                <Button
                  size="sm"
                  variant="secondary"
                  className="rounded-full shadow-lg"
                  onClick={() => scrollToBottom(true)}
                  aria-label="Scroll to bottom"
                >
                  <ArrowDown className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Message Input Area */}
            <div className="flex-shrink-0 border-t p-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const input = e.currentTarget.elements.namedItem('message') as HTMLInputElement
                  if (input.value.trim()) {
                    sendMessage(input.value)
                    input.value = ''
                  }
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  name="message"
                  placeholder={t.learner.chat.placeholder}
                  className="flex-1 px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  autoComplete="off"
                />
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {t.learner.chat.send}
                </button>
              </form>
            </div>
          </div>
        )}
      </CardContent>
    </Card>

      {/* Story 4.7: Async Status Bar - Fixed bottom viewport */}
      {activeJob && (
        <AsyncStatusBar
          jobId={activeJob.jobId}
          artifactType={activeJob.artifactType}
          status={status || 'pending'}
          progress={progress}
          errorMessage={jobError}
          onDismiss={clearActiveJob}
        />
      )}
    </>
  )
}
