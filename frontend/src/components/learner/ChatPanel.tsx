'use client'

/**
 * ChatPanel - ChatGPT-inspired Design
 *
 * Features:
 * - No Card wrapper - fills available space directly
 * - Larger text (text-base), generous padding
 * - Max-width container (48rem) centered for messages
 * - ChatGPT-like rounded input bar at bottom
 * - SSE streaming with token-by-token rendering
 * - Proactive AI greeting
 * - Persistent chat history
 * - Voice input integration
 * - Async job tracking
 */

import { useEffect, useState, useRef, useMemo } from 'react'
import { MessageSquare, ArrowDown, Mic, MicOff, Send, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { VoiceRecordingOverlay } from './VoiceRecordingOverlay'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useLearnerChat, useChatHistory } from '@/lib/hooks/use-learner-chat'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ChatMessage } from './ChatMessage'
import { AsyncStatusBar } from './AsyncStatusBar'
import { useJobStatus } from '@/lib/hooks/use-job-status'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { useToast } from '@/lib/hooks/use-toast'
import { learnerToast } from '@/lib/utils/learner-toast'
import { useVoiceInput } from '@/lib/hooks/use-voice-input'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useLessonSteps, useLessonStepsProgress } from '@/lib/hooks/use-lesson-plan'
import type { LessonStepResponse } from '@/lib/api/lesson-plan'
import type { LearnerChatMessage } from '@/lib/api/learner-chat'

const CHAT_CACHE_MAX = 50

function chatCacheKey(notebookId: string) {
  return `chat-cache-v1-${notebookId}`
}

function readChatCache(notebookId: string): LearnerChatMessage[] {
  try {
    const raw = localStorage.getItem(chatCacheKey(notebookId))
    return raw ? (JSON.parse(raw) as LearnerChatMessage[]) : []
  } catch {
    return []
  }
}

function writeChatCache(notebookId: string, msgs: LearnerChatMessage[]) {
  try {
    localStorage.setItem(chatCacheKey(notebookId), JSON.stringify(msgs.slice(-CHAT_CACHE_MAX)))
  } catch {}
}

function deleteChatCache(notebookId: string) {
  try {
    localStorage.removeItem(chatCacheKey(notebookId))
  } catch {}
}

interface ChatPanelProps {
  notebookId: string
}

export function ChatPanel({ notebookId }: ChatPanelProps) {
  const { t, language } = useTranslation()
  const { toast } = useToast()
  const [mounted, setMounted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [showScrollButton, setShowScrollButton] = useState(false)

  // Access active job state from store (individual selectors to avoid infinite re-renders)
  const activeJob = useLearnerStore((state) => state.activeJob)
  const setActiveJob = useLearnerStore((state) => state.setActiveJob)
  const clearActiveJob = useLearnerStore((state) => state.clearActiveJob)

  // Chat cache — read synchronously from localStorage at mount time.
  // Using useState initializer (not Zustand) avoids hydration timing issues on page refresh.
  const [cachedMessages, setCachedMessages] = useState<LearnerChatMessage[]>(() =>
    typeof window !== 'undefined' ? readChatCache(notebookId) : []
  )

  useEffect(() => {
    setMounted(true)
  }, [])

  // Load chat history
  const {
    data: historyData,
    isLoading: isLoadingHistory,
    isFetching: isHistoryFetching,
    error: historyError,
  } = useChatHistory(notebookId)

  // Derive history state for greeting guard (must be computed before useLearnerChat)
  // Also treat a populated cache as existing history to prevent re-greeting
  const hasExistingHistory = !!(historyData?.messages?.length) || cachedMessages.length > 0

  const {
    isLoading,
    isStreaming,
    quickRepliesReady,
    error,
    sendMessage,
    messages,
    clearMessages,
    editLastMessage,
    injectSurfaceQuiz,
  } = useLearnerChat(notebookId, isLoadingHistory, hasExistingHistory, isHistoryFetching)

  // Lesson step progress
  const { data: stepProgress } = useLessonStepsProgress(notebookId)
  const { data: lessonSteps } = useLessonSteps(notebookId)

  // Derive the current (first incomplete required) lesson step
  const currentStep = useMemo<LessonStepResponse | null>(() => {
    if (!lessonSteps || !stepProgress) return null
    const completedIds = new Set(stepProgress.completed_step_ids)
    return lessonSteps.find((s) => s.required && !completedIds.has(s.id)) ?? null
  }, [lessonSteps, stepProgress])

  // Build source title map for reference display (source:id -> title)
  const { sources: notebookSources } = useNotebookSources(notebookId)
  const sourceTitleMap = useMemo(() => {
    const map = new Map<string, string>()
    if (notebookSources) {
      for (const source of notebookSources) {
        if (source.id && source.title) {
          map.set(source.id, source.title)
        }
      }
    }
    return map
  }, [notebookSources])

  // Compute contextual quick replies for the current lesson step
  const quickReplies = useMemo<string[]>(() => {
    const chat = t.learner?.chat as Record<string, unknown>
    const qrKeys = chat?.quickReplies as Record<string, string> | undefined
    if (!qrKeys) return []
    if (!currentStep) {
      return [qrKeys.tellMeMore, qrKeys.whatsNext, qrKeys.haveQuestion]
    }
    switch (currentStep.step_type) {
      case 'watch':
        return [qrKeys.watchedVideo, qrKeys.needMoreContext, qrKeys.haveQuestion]
      case 'read':
        return [qrKeys.readIt, qrKeys.canYouSummarize, qrKeys.haveQuestion]
      case 'discuss':
        return [qrKeys.understood, qrKeys.explainDifferently, qrKeys.showExample]
      case 'quiz':
        return [qrKeys.completedQuiz, qrKeys.haveQuestion]
      default:
        return [qrKeys.tellMeMore, qrKeys.whatsNext, qrKeys.haveQuestion]
    }
  }, [currentStep, t])

  // Voice input
  const {
    isListening,
    isSupported,
    transcript,
    isRequestingPermission,
    startListening,
    stopListening,
    clearTranscript,
    error: voiceError,
    analyserNode,
  } = useVoiceInput(language)

  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [userHasEdited, setUserHasEdited] = useState(false)
  const textBeforeRecordingRef = useRef('')

  // Strip empty paragraphs (e.g. "[]" from ReAct tool-call messages merged by backend)
  function cleanMessageContent(content: string): string {
    return content
      .split('\n\n')
      .filter(part => part.trim() !== '[]' && part.trim() !== '')
      .join('\n\n')
  }

  // Merge history/cache with current messages, preserving toolCalls.
  // Cache is only written on unmount (never mid-session), so cachedMessages and messages
  // never overlap: messages resets to [] on every mount via useLearnerChat's notebookId effect.
  const allMessages = useMemo(() => {
    const clean = (msgs: typeof messages) =>
      msgs.map(m => ({ ...m, content: cleanMessageContent(m.content) }))

    if (cachedMessages.length > 0) {
      // Cache has previous-session messages (with toolCalls). Append any new session messages.
      return clean(messages.length > 0 ? [...cachedMessages, ...messages] : cachedMessages)
    }
    // No cache: normal flow (first visit or after explicit reset)
    const base = historyLoaded && historyData?.messages
      ? [...historyData.messages, ...messages]
      : messages
    return clean(base)
  }, [cachedMessages, messages, historyLoaded, historyData])

  // Memoized: avoids scanning allMessages on every SSE-delta re-render
  const hasUserMessage = useMemo(() => allMessages.some((m) => m.role === 'user'), [allMessages])

  // Track when history finishes loading
  useEffect(() => {
    if (!isLoadingHistory && historyData && !historyLoaded) {
      setHistoryLoaded(true)
    }
  }, [isLoadingHistory, historyData, historyLoaded])

  // Ref to track latest allMessages without triggering effects
  const allMessagesRef = useRef(allMessages)
  allMessagesRef.current = allMessages

  // Save to localStorage when stream completes (toolCalls fully attached at that point).
  // This ensures the cache is written even if the user refreshes before navigating away.
  const prevIsStreamingRef = useRef(false)
  useEffect(() => {
    if (prevIsStreamingRef.current && !isStreaming && allMessages.length > 0) {
      writeChatCache(notebookId, allMessages)
    }
    prevIsStreamingRef.current = isStreaming
  }, [isStreaming, notebookId, allMessages])

  // Also save on unmount so navigating away captures the very latest state.
  useEffect(() => {
    return () => {
      if (allMessagesRef.current.length > 0) {
        writeChatCache(notebookId, allMessagesRef.current)
      }
    }
  }, [notebookId])

  // Auto-scroll to bottom after history loads
  useEffect(() => {
    if (historyLoaded && allMessages.length > 0) {
      const timer = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [historyLoaded, allMessages.length])

  // Detect user manual scroll
  const handleScroll = () => {
    const container = messagesContainerRef.current
    if (!container) return
    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    const isAtBottom = distanceFromBottom < 50
    setIsUserScrolledUp(!isAtBottom)
    setShowScrollButton(!isAtBottom)
  }

  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
    setIsUserScrolledUp(false)
    setShowScrollButton(false)
  }

  // Auto-scroll when messages change (unless user scrolled up)
  useEffect(() => {
    if (!isUserScrolledUp) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isStreaming, isUserScrolledUp])

  // Set input to pre-recording text + current transcript
  useEffect(() => {
    if (transcript && inputRef.current && !userHasEdited) {
      const prefix = textBeforeRecordingRef.current
      const separator = prefix && !prefix.endsWith(' ') ? ' ' : ''
      inputRef.current.value = prefix + separator + transcript
    }
  }, [transcript, userHasEdited])

  // Capture existing text when recording starts
  useEffect(() => {
    if (isListening) {
      setUserHasEdited(false)
      textBeforeRecordingRef.current = inputRef.current?.value || ''
    }
  }, [isListening])

  // Voice input error toasts
  useEffect(() => {
    if (voiceError) {
      let title = ''
      let description = ''
      switch (voiceError) {
        case 'microphone-permission-denied':
          title = t.learner.chat.voiceInput.microphoneError
          description = t.learner.chat.voiceInput.microphoneErrorDesc
          break
        case 'no-speech-detected':
          title = t.learner.chat.voiceInput.noSpeech
          description = t.learner.chat.voiceInput.noSpeechDesc
          break
        case 'network-error':
          title = t.learner.chat.voiceInput.networkError
          description = t.learner.chat.voiceInput.networkErrorDesc
          break
        case 'no-microphone':
          title = t.learner.chat.voiceInput.noMicrophone
          description = t.learner.chat.voiceInput.noMicrophoneDesc
          break
        default:
          title = t.learner.chat.voiceInput.error
          description = t.learner.chat.voiceInput.errorDesc
      }
      learnerToast.error(title, { description })
    }
  }, [voiceError, t])

  // Poll job status
  const { status, progress, error: jobError } = useJobStatus(
    activeJob?.jobId || null,
    {
      notebookId,
      onComplete: (result) => {
        toast({
          title: t.asyncStatus.artifactReady.replace('{type}', activeJob?.artifactType || 'artifact'),
          description: t.asyncStatus.artifactReadyDescription,
        })
        // Inject quiz inline when quiz generation completes
        if (activeJob?.artifactType === 'quiz' && result?.quiz_id) {
          injectSurfaceQuiz(result as Record<string, unknown>)
        }
      },
      onError: (errorMsg) => {
        learnerToast.error(
          t.asyncStatus.artifactFailed.replace('{type}', activeJob?.artifactType || 'artifact'),
          { description: errorMsg }
        )
      },
    }
  )

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const textarea = inputRef.current
    if (textarea && textarea.value.trim()) {
      sendMessage(textarea.value)
      textarea.value = ''
      clearTranscript()
      setUserHasEdited(false)
      // Reset textarea height
      textarea.style.height = 'auto'
    }
  }

  // Handle Enter key (submit) vs Shift+Enter (newline)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  const handleTextareaInput = () => {
    const textarea = inputRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
      if (!userHasEdited) setUserHasEdited(true)
    }
  }

  if (!mounted) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <>
      <div className="h-full flex flex-col">
        {/* Loading or error state */}
        {(isLoading || isLoadingHistory) ? (
          <div className="flex-1 flex items-center justify-center" data-testid="history-loading-skeleton">
            <LoadingSpinner size="lg" />
          </div>
        ) : (error || historyError) ? (
          <div className="flex-1 flex items-center justify-center p-6 text-center">
            <div>
              <p className="text-base text-muted-foreground mb-2">{t.learner.chat.error}</p>
              <p className="text-sm text-muted-foreground">{t.learner.chat.errorDesc}</p>
            </div>
          </div>
        ) : (
          <>

            {/* Messages Area */}
            <div
              ref={messagesContainerRef}
              onScroll={handleScroll}
              className="flex-1 overflow-y-auto relative"
            >
              {/* New conversation button */}
              {allMessages.length > 0 && !isStreaming && (
                <div className="sticky top-2 z-10 flex justify-end px-4">
                  <Button
                    size="icon"
                    variant="outline"
                    className="rounded-full shadow-sm h-7 w-7"
                    onClick={() => {
                      clearMessages()
                      deleteChatCache(notebookId)
                      setCachedMessages([])
                      setHistoryLoaded(false)
                    }}
                    aria-label={t.learner.chat.newConversation}
                    title={t.learner.chat.newConversation}
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </Button>
                </div>
              )}
              <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
                {allMessages.length === 0 && isStreaming ? (
                  // Greeting loading state
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <MessageSquare className="h-4 w-4 text-primary animate-pulse" />
                    </div>
                    <div className="flex-1">
                      <p className="text-base leading-relaxed text-muted-foreground">
                        {t.learner.chat.greetingLoading || 'Preparing your personalized greeting...'}
                      </p>
                    </div>
                  </div>
                ) : allMessages.length === 0 ? (
                  // Empty state
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <MessageSquare className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="text-base leading-relaxed">
                        {t.learner.chat.greeting}
                      </p>
                    </div>
                  </div>
                ) : (
                  allMessages.map((message, index) => {
                    // Determine if this is the last user message (for edit)
                    const lastUserIndex = allMessages.reduce(
                      (lastIdx: number, msg: { role: string }, idx: number) =>
                        msg.role === 'user' ? idx : lastIdx,
                      -1
                    )
                    const isEditableMsg =
                      message.role === 'user' &&
                      index === lastUserIndex &&
                      !isStreaming

                    return (
                      <ChatMessage
                        key={index}
                        message={message}
                        index={index}
                        isLastAssistant={
                          message.role === 'assistant' &&
                          index === allMessages.length - 1
                        }
                        isStreaming={isStreaming}
                        t={t}
                        isEditable={isEditableMsg}
                        onEdit={isEditableMsg ? editLastMessage : undefined}
                        sourceTitleMap={sourceTitleMap}
                        onConfirm={sendMessage}
                        notebookId={notebookId}
                      />
                    )
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Scroll to bottom button */}
              {showScrollButton && (
                <div className="sticky bottom-4 flex justify-center z-10">
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
            </div>

            {/* Input Area - ChatGPT style */}
            <div className="flex-shrink-0 border-t bg-background">
              <div className="max-w-3xl mx-auto px-4 py-3 relative">
                {/* Voice recording overlay */}
                {isListening && (
                  <VoiceRecordingOverlay
                    analyserNode={analyserNode}
                    onStop={stopListening}
                  />
                )}
                {/* Dynamic quick replies — shown after each AI message (or before first user message) */}
                {!isStreaming && quickRepliesReady && (allMessages.length === 0 || allMessages[allMessages.length - 1]?.role === 'assistant') && (() => {
                  let replies: string[]
                  if (!hasUserMessage) {
                    replies = [
                      t.learner.chat.suggestions.whatAbout as string,
                      t.learner.chat.suggestions.summarize as string,
                      t.learner.chat.suggestions.focusFirst as string,
                    ]
                  } else {
                    // LLM-generated replies if available, fall back to step-based
                    const lastMsg = allMessages[allMessages.length - 1] as { quickReplies?: string[] }
                    replies = lastMsg?.quickReplies?.length ? lastMsg.quickReplies : quickReplies
                  }
                  const filtered = replies.filter(Boolean)
                  if (!filtered.length) return null
                  return (
                    <div className="flex flex-wrap justify-center gap-2 mb-3">
                      {filtered.map((reply: string) => (
                        <button
                          key={reply}
                          type="button"
                          onClick={() => sendMessage(reply)}
                          className="text-sm px-3 py-1.5 rounded-full border bg-background hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground"
                        >
                          {reply}
                        </button>
                      ))}
                    </div>
                  )
                })()}
                <form
                  onSubmit={handleSubmit}
                  className="relative flex items-end gap-2 rounded-2xl border bg-background px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all"
                >
                  {/* Voice input button */}
                  {isSupported && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={isListening ? stopListening : startListening}
                      disabled={isRequestingPermission}
                      aria-label={isListening ? t.learner.chat.voiceInput.stopRecording : t.learner.chat.voiceInput.startRecording}
                      className={`flex-shrink-0 h-8 w-8 ${
                        isListening || isRequestingPermission
                          ? 'text-red-500 animate-pulse'
                          : 'text-muted-foreground animate-breathe'
                      }`}
                    >
                      {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                    </Button>
                  )}

                  {isListening && (
                    <span className="sr-only" role="status" aria-live="polite">
                      {t.learner.chat.voiceInput.listening}
                    </span>
                  )}

                  <textarea
                    ref={inputRef}
                    name="message"
                    placeholder={t.learner.chat.placeholder}
                    className="flex-1 resize-none bg-transparent text-base leading-relaxed focus:outline-none py-1 min-h-[28px] max-h-[150px]"
                    autoComplete="off"
                    rows={1}
                    onInput={handleTextareaInput}
                    onKeyDown={handleKeyDown}
                  />

                  <Button
                    type="submit"
                    size="icon"
                    variant="ghost"
                    className="flex-shrink-0 h-8 w-8 text-primary hover:text-primary/80"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Async Status Bar */}
      {activeJob && activeJob.artifactType !== 'podcast' && (
        <AsyncStatusBar
          jobId={activeJob.jobId}
          artifactType={activeJob.artifactType}
          status={status || 'pending'}
          progress={progress ?? undefined}
          errorMessage={jobError ?? undefined}
          onDismiss={clearActiveJob}
        />
      )}
    </>
  )
}
