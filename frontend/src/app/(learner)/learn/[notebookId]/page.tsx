'use client'

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { useNotebookChat } from '@/lib/hooks/useNotebookChat'
import { useSources } from '@/lib/hooks/use-sources'
import { useArtifacts, useDeleteArtifact } from '@/lib/hooks/use-artifacts'
import { useLearnerModule } from '@/lib/hooks/use-learner-modules'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useIsDesktop } from '@/lib/hooks/use-media-query'
import { useModalManager } from '@/lib/hooks/use-modal-manager'
import { useToast } from '@/lib/hooks/use-toast'
import { cn } from '@/lib/utils'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChatPanel } from '@/components/source/ChatPanel'
import { SourceCard } from '@/components/sources/SourceCard'
import { QuizCard } from '@/components/artifacts/QuizCard'
import { PodcastCard } from '@/components/artifacts/PodcastCard'
import { TransformationCard } from '@/components/artifacts/TransformationCard'
import { GenerateQuizDialog } from '@/components/artifacts/GenerateQuizDialog'
import { GeneratePodcastDialog } from '@/components/podcasts/GeneratePodcastDialog'
import {
  ArrowLeft,
  BookOpen,
  FileText,
  MessageSquare,
  GraduationCap,
  Plus,
  ChevronDown,
  Headphones,
  Loader2,
} from 'lucide-react'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

/**
 * Learner Learning Interface
 *
 * 3-column layout for learners to engage with notebook content:
 * - Left: Document Reader (sources list, read-only)
 * - Middle: AI Chat Guide (interactive tutor)
 * - Right: Artifacts Panel (quizzes, podcasts)
 */
export default function LearnerLearnPage() {
  const { t } = useTranslation()
  const params = useParams()
  const router = useRouter()
  const isDesktop = useIsDesktop()
  const { openModal } = useModalManager()
  const { toast } = useToast()

  const notebookId = params?.notebookId ? decodeURIComponent(params.notebookId as string) : ''

  // Direct URL protection (Task 13): Validate learner access
  const { error: accessError, isLoading: accessLoading } = useLearnerModule(notebookId)

  // Redirect if access denied (403/404 only, not network errors)
  useEffect(() => {
    if (accessError) {
      // Check if it's an access denial (403/404) vs network error
      const errorStatus = (accessError as any)?.response?.status
      if (errorStatus === 403 || errorStatus === 404) {
        toast({
          title: t.common.error,
          description: t.assignments.notAccessible,
          variant: 'destructive',
        })
        router.push('/learner/modules')
      } else {
        // Network or other errors - show generic error
        toast({
          title: t.common.error,
          description: t.common.unknownError,
          variant: 'destructive',
        })
      }
    }
  }, [accessError, router, toast, t])

  // Fetch notebook data
  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const {
    sources,
    isLoading: sourcesLoading,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useNotebookSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)

  // Mobile tab state
  const [mobileActiveTab, setMobileActiveTab] = useState<'documents' | 'chat' | 'artifacts'>('documents')

  // Context selection state for chat
  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  // Initialize default selections when sources/notes load
  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections(prev => {
        const newSourceSelections = { ...prev.sources }
        sources.forEach(source => {
          if (!(source.id in newSourceSelections)) {
            newSourceSelections[source.id] = source.insights_count > 0 ? 'insights' : 'full'
          }
        })
        return { ...prev, sources: newSourceSelections }
      })
    }
  }, [sources])

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections(prev => {
        const newNoteSelections = { ...prev.notes }
        notes.forEach(note => {
          if (!(note.id in newNoteSelections)) {
            newNoteSelections[note.id] = 'full'
          }
        })
        return { ...prev, notes: newNoteSelections }
      })
    }
  }, [notes])

  const handleContextModeChange = (itemId: string, mode: ContextMode, type: 'source' | 'note') => {
    setContextSelections(prev => ({
      ...prev,
      [type === 'source' ? 'sources' : 'notes']: {
        ...(type === 'source' ? prev.sources : prev.notes),
        [itemId]: mode
      }
    }))
  }

  const handleSourceClick = (sourceId: string) => {
    openModal('source', sourceId)
  }

  // Show loading while validating access or loading notebook
  if (accessLoading || notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!notebook) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">{t.notebooks.notFound}</h1>
        <p className="text-muted-foreground">{t.notebooks.notFoundDesc}</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push('/modules')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t.common.back}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/modules')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t.common.back}
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold line-clamp-1">{notebook.name}</h1>
                {notebook.description && (
                  <p className="text-sm text-muted-foreground line-clamp-1">{notebook.description}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 p-4">
        {/* Mobile: Tabbed interface */}
        {!isDesktop && (
          <>
            <div className="lg:hidden mb-4">
              <Tabs value={mobileActiveTab} onValueChange={(value) => setMobileActiveTab(value as 'documents' | 'chat' | 'artifacts')}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="documents" className="gap-2">
                    <FileText className="h-4 w-4" />
                    {t.navigation.documents}
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="gap-2">
                    <MessageSquare className="h-4 w-4" />
                    {t.common.chat}
                  </TabsTrigger>
                  <TabsTrigger value="artifacts" className="gap-2">
                    <GraduationCap className="h-4 w-4" />
                    {t.artifacts.title}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <div className="flex-1 overflow-hidden lg:hidden h-[calc(100vh-200px)]">
              {mobileActiveTab === 'documents' && (
                <LearnerDocumentsColumn
                  sources={sources}
                  isLoading={sourcesLoading}
                  contextSelections={contextSelections.sources}
                  onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                  onSourceClick={handleSourceClick}
                  hasNextPage={hasNextPage}
                  isFetchingNextPage={isFetchingNextPage}
                  fetchNextPage={fetchNextPage}
                />
              )}
              {mobileActiveTab === 'chat' && (
                <LearnerChatColumn
                  notebookId={notebookId}
                  contextSelections={contextSelections}
                  sources={sources || []}
                  notes={notes || []}
                  sourcesLoading={sourcesLoading}
                  notesLoading={notesLoading}
                />
              )}
              {mobileActiveTab === 'artifacts' && (
                <LearnerArtifactsPanel notebookId={notebookId} />
              )}
            </div>
          </>
        )}

        {/* Desktop: 3-column layout */}
        <div className="hidden lg:flex h-full gap-4">
          {/* Left Column: Documents */}
          <div className="w-1/4 min-w-[280px] h-full">
            <LearnerDocumentsColumn
              sources={sources}
              isLoading={sourcesLoading}
              contextSelections={contextSelections.sources}
              onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
              onSourceClick={handleSourceClick}
              hasNextPage={hasNextPage}
              isFetchingNextPage={isFetchingNextPage}
              fetchNextPage={fetchNextPage}
            />
          </div>

          {/* Middle Column: Chat */}
          <div className="flex-1 min-w-[400px] h-full">
            <LearnerChatColumn
              notebookId={notebookId}
              contextSelections={contextSelections}
              sources={sources || []}
              notes={notes || []}
              sourcesLoading={sourcesLoading}
              notesLoading={notesLoading}
            />
          </div>

          {/* Right Column: Artifacts */}
          <div className="w-1/4 min-w-[280px] h-full">
            <LearnerArtifactsPanel notebookId={notebookId} />
          </div>
        </div>
      </div>
    </div>
  )
}

// Learner Documents Column (Read-only)
interface LearnerDocumentsColumnProps {
  sources?: { id: string; title: string | null; insights_count: number; embedded: boolean; status?: string }[]
  isLoading: boolean
  contextSelections: Record<string, ContextMode>
  onContextModeChange: (sourceId: string, mode: ContextMode) => void
  onSourceClick: (sourceId: string) => void
  hasNextPage?: boolean
  isFetchingNextPage?: boolean
  fetchNextPage?: () => void
}

function LearnerDocumentsColumn({
  sources,
  isLoading,
  contextSelections,
  onContextModeChange,
  onSourceClick,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
}: LearnerDocumentsColumnProps) {
  const { t } = useTranslation()
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current
    if (!container || !hasNextPage || isFetchingNextPage || !fetchNextPage) return
    const { scrollTop, scrollHeight, clientHeight } = container
    if (scrollHeight - scrollTop - clientHeight < 200) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {t.navigation.documents}
        </CardTitle>
        <CardDescription>{t.modules.sources.replace('{count}', String(sources?.length || 0))}</CardDescription>
      </CardHeader>
      <CardContent ref={scrollContainerRef} className="flex-1 overflow-y-auto min-h-0">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : !sources || sources.length === 0 ? (
          <EmptyState
            icon={FileText}
            title={t.sources.noSourcesYet}
            description={t.sources.allSourcesDescShort}
          />
        ) : (
          <div className="space-y-3">
            {sources.map((source) => (
              <SourceCard
                key={source.id}
                source={source as any}
                onClick={onSourceClick}
                contextMode={contextSelections[source.id]}
                onContextModeChange={(mode) => onContextModeChange(source.id, mode)}
              />
            ))}
            {isFetchingNextPage && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Learner Chat Column
interface LearnerChatColumnProps {
  notebookId: string
  contextSelections: ContextSelections
  sources: any[]
  notes: any[]
  sourcesLoading: boolean
  notesLoading: boolean
}

function LearnerChatColumn({
  notebookId,
  contextSelections,
  sources,
  notes,
  sourcesLoading,
  notesLoading,
}: LearnerChatColumnProps) {
  const { t } = useTranslation()

  const chat = useNotebookChat({
    notebookId,
    sources,
    notes,
    contextSelections
  })

  const contextStats = useMemo(() => {
    let sourcesInsights = 0
    let sourcesFull = 0
    let notesCount = 0

    sources.forEach(source => {
      const mode = contextSelections.sources[source.id]
      if (mode === 'insights') sourcesInsights++
      else if (mode === 'full') sourcesFull++
    })

    notes.forEach(note => {
      const mode = contextSelections.notes[note.id]
      if (mode === 'full') notesCount++
    })

    return {
      sourcesInsights,
      sourcesFull,
      notesCount,
      tokenCount: chat.tokenCount,
      charCount: chat.charCount
    }
  }, [sources, notes, contextSelections, chat.tokenCount, chat.charCount])

  if (sourcesLoading || notesLoading) {
    return (
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </CardContent>
      </Card>
    )
  }

  return (
    <ChatPanel
      title={t.chat.chatWithNotebook}
      contextType="notebook"
      messages={chat.messages}
      isStreaming={chat.isSending}
      contextIndicators={null}
      onSendMessage={(message, modelOverride) => chat.sendMessage(message, modelOverride)}
      modelOverride={chat.currentSession?.model_override ?? chat.pendingModelOverride ?? undefined}
      onModelChange={(model) => chat.setModelOverride(model ?? null)}
      sessions={chat.sessions}
      currentSessionId={chat.currentSessionId}
      onCreateSession={(title) => chat.createSession(title)}
      onSelectSession={chat.switchSession}
      onUpdateSession={(sessionId, title) => chat.updateSession(sessionId, { title })}
      onDeleteSession={chat.deleteSession}
      loadingSessions={chat.loadingSessions}
      notebookContextStats={contextStats}
      notebookId={notebookId}
    />
  )
}

// Learner Artifacts Panel
interface LearnerArtifactsPanelProps {
  notebookId: string
}

function LearnerArtifactsPanel({ notebookId }: LearnerArtifactsPanelProps) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'all' | 'quiz' | 'podcast'>('all')
  const [showQuizDialog, setShowQuizDialog] = useState(false)
  const [showPodcastDialog, setShowPodcastDialog] = useState(false)

  const { data: artifacts, isLoading } = useArtifacts(notebookId)
  const deleteArtifact = useDeleteArtifact()

  const filteredArtifacts = useMemo(() => {
    if (!artifacts) return []
    if (activeTab === 'all') return artifacts.filter(a => a.artifact_type === 'quiz' || a.artifact_type === 'podcast')
    return artifacts.filter((artifact) => artifact.artifact_type === activeTab)
  }, [artifacts, activeTab])

  const handleDelete = async (artifactId: string) => {
    await deleteArtifact.mutateAsync(artifactId)
  }

  if (isLoading) {
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
        <CardHeader className="pb-3 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              {t.artifacts.title}
            </CardTitle>
            <DropdownMenu modal={false}>
              <DropdownMenuTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  {t.artifacts.generate}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onSelect={() => setTimeout(() => setShowQuizDialog(true), 0)}>
                  <FileText className="h-4 w-4 mr-2" />
                  {t.artifacts.generateQuiz}
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setTimeout(() => setShowPodcastDialog(true), 0)}>
                  <Headphones className="h-4 w-4 mr-2" />
                  {t.artifacts.generatePodcast}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-hidden p-0">
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)} className="h-full flex flex-col">
            <div className="px-4 pt-2 border-b">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="all">{t.artifacts.all}</TabsTrigger>
                <TabsTrigger value="quiz">{t.artifacts.quizzes}</TabsTrigger>
                <TabsTrigger value="podcast">{t.artifacts.podcasts}</TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {filteredArtifacts && filteredArtifacts.length > 0 ? (
                <div className="space-y-3">
                  {filteredArtifacts.map((artifact) => {
                    switch (artifact.artifact_type) {
                      case 'quiz':
                        return (
                          <QuizCard
                            key={artifact.id}
                            artifact={artifact}
                            onDelete={handleDelete}
                            notebookId={notebookId}
                          />
                        )
                      case 'podcast':
                        return (
                          <PodcastCard
                            key={artifact.id}
                            artifact={artifact}
                            onDelete={handleDelete}
                            notebookId={notebookId}
                          />
                        )
                      default:
                        return null
                    }
                  })}
                </div>
              ) : (
                <EmptyState
                  icon={GraduationCap}
                  title={t.artifacts.noArtifacts}
                  description={t.artifacts.noArtifactsDescription}
                />
              )}
            </div>
          </Tabs>
        </CardContent>
      </Card>

      {showQuizDialog && (
        <GenerateQuizDialog
          notebookId={notebookId}
          open={showQuizDialog}
          onOpenChange={setShowQuizDialog}
        />
      )}

      {showPodcastDialog && (
        <GeneratePodcastDialog
          open={showPodcastDialog}
          onOpenChange={setShowPodcastDialog}
          notebookId={notebookId}
        />
      )}
    </>
  )
}
