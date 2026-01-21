'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useTranslation } from '@/lib/hooks/use-translation'
import { GraduationCap, Plus, ChevronDown, FileText, Headphones, Sparkles } from 'lucide-react'
import { useArtifacts, useDeleteArtifact } from '@/lib/hooks/use-artifacts'
import { CollapsibleColumn, createCollapseButton } from '@/components/notebooks/CollapsibleColumn'
import { useNotebookColumnsStore } from '@/lib/stores/notebook-columns-store'
import { QuizCard } from '@/components/artifacts/QuizCard'
import { PodcastCard } from '@/components/artifacts/PodcastCard'
import { TransformationCard } from '@/components/artifacts/TransformationCard'
import { GenerateQuizDialog } from '@/components/artifacts/GenerateQuizDialog'
import { GeneratePodcastDialog } from '@/components/podcasts/GeneratePodcastDialog'

interface ArtifactsPanelProps {
  notebookId: string
  className?: string
}

export function ArtifactsPanel({ notebookId, className }: ArtifactsPanelProps) {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'all' | 'quiz' | 'podcast' | 'transformation'>('all')
  const [showQuizDialog, setShowQuizDialog] = useState(false)
  const [showPodcastDialog, setShowPodcastDialog] = useState(false)

  const { data: artifacts, isLoading, error } = useArtifacts(notebookId)
  const deleteArtifact = useDeleteArtifact()

  // Collapsible column state
  const { artifactsCollapsed, toggleArtifacts } = useNotebookColumnsStore()
  const collapseButton = useMemo(
    () => createCollapseButton(toggleArtifacts, t.artifacts?.title || 'Artifacts'),
    [toggleArtifacts, t.artifacts?.title]
  )

  // Filter artifacts by type
  const filteredArtifacts = useMemo(() => {
    if (!artifacts) return []
    if (activeTab === 'all') return artifacts
    return artifacts.filter((artifact) => artifact.artifact_type === activeTab)
  }, [artifacts, activeTab])

  const handleDelete = async (artifactId: string) => {
    await deleteArtifact.mutateAsync(artifactId)
  }

  if (isLoading) {
    return (
      <CollapsibleColumn
        isCollapsed={artifactsCollapsed}
        onToggle={toggleArtifacts}
        collapsedIcon={GraduationCap}
        collapsedLabel={t.artifacts?.title || 'Artifacts'}
        direction="vertical-in-stack"
      >
        <Card className={className}>
          <CardContent className="flex-1 flex items-center justify-center h-full">
            <LoadingSpinner size="lg" />
          </CardContent>
        </Card>
      </CollapsibleColumn>
    )
  }

  if (error) {
    return (
      <CollapsibleColumn
        isCollapsed={artifactsCollapsed}
        onToggle={toggleArtifacts}
        collapsedIcon={GraduationCap}
        collapsedLabel={t.artifacts?.title || 'Artifacts'}
        direction="vertical-in-stack"
      >
        <Card className={className}>
          <CardContent className="flex-1 flex items-center justify-center h-full">
            <p className="text-muted-foreground">{t.common.errorLoading}</p>
          </CardContent>
        </Card>
      </CollapsibleColumn>
    )
  }

  return (
    <>
      <CollapsibleColumn
        isCollapsed={artifactsCollapsed}
        onToggle={toggleArtifacts}
        collapsedIcon={GraduationCap}
        collapsedLabel={t.artifacts?.title || 'Artifacts'}
        direction="vertical-in-stack"
      >
        <Card className={`${className} h-full flex flex-col flex-1 overflow-hidden`}>
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-center justify-between gap-2">
              <CardTitle className="text-lg">{t.artifacts?.title || 'Artifacts'}</CardTitle>
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      {t.artifacts?.generate || 'Generate'}
                      <ChevronDown className="h-4 w-4 ml-2" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setShowQuizDialog(true)}>
                      <FileText className="h-4 w-4 mr-2" />
                      {t.artifacts?.generateQuiz || 'Generate Quiz'}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setShowPodcastDialog(true)}>
                      <Headphones className="h-4 w-4 mr-2" />
                      {t.artifacts?.generatePodcast || 'Generate Podcast'}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                {collapseButton}
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-hidden p-0">
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as typeof activeTab)} className="h-full flex flex-col">
              <div className="px-4 pt-2 border-b">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="all">{t.artifacts?.all || 'All'}</TabsTrigger>
                  <TabsTrigger value="quiz">{t.artifacts?.quizzes || 'Quizzes'}</TabsTrigger>
                  <TabsTrigger value="podcast">{t.artifacts?.podcasts || 'Podcasts'}</TabsTrigger>
                  <TabsTrigger value="transformation">{t.artifacts?.transformations || 'Transformations'}</TabsTrigger>
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
                        case 'transformation':
                          return (
                            <TransformationCard
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
                    title={t.artifacts?.noArtifacts || 'No artifacts yet'}
                    description={t.artifacts?.noArtifactsDescription || 'Generate a quiz or podcast to get started'}
                  />
                )}
              </div>
            </Tabs>
          </CardContent>
        </Card>
      </CollapsibleColumn>

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
        />
      )}
    </>
  )
}
