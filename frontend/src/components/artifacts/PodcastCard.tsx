'use client'

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArtifactResponse } from '@/lib/api/artifacts'
import { podcastsApi } from '@/lib/api/podcasts'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Headphones, Trash2, Play, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { getDateLocale } from '@/lib/utils/date-locale'
import { useTranslation } from '@/lib/hooks/use-translation'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { PodcastPlayer } from './PodcastPlayer'
import { ACTIVE_EPISODE_STATUSES } from '@/lib/types/podcasts'
import { useToast } from '@/lib/hooks/use-toast'
import { QUERY_KEYS } from '@/lib/api/query-client'

interface PodcastCardProps {
  artifact: ArtifactResponse
  onDelete: (artifactId: string) => void
  notebookId: string
}

export function PodcastCard({ artifact, onDelete, notebookId }: PodcastCardProps) {
  const { t, language } = useTranslation()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [showPodcastPlayer, setShowPodcastPlayer] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)

  // Check if this is a job ID (command:xxx) or episode ID (episode:xxx)
  const isJobId = artifact.artifact_id.startsWith('command:')
  
  // Extract the actual job ID (remove command: prefix if present)
  const jobId = isJobId ? artifact.artifact_id.replace(/^command:/, '') : null
  
  // Fetch episode data to check status
  const { data: episode, isLoading: episodeLoading } = useQuery({
    queryKey: ['podcast-episode', artifact.artifact_id],
    queryFn: () => podcastsApi.getEpisode(artifact.artifact_id),
    enabled: !isJobId, // Only fetch if it's a real episode ID
    staleTime: 10_000,
    retry: false,
  })

  // Fetch job status if it's a job ID
  const { data: jobStatus } = useQuery({
    queryKey: ['podcast-job', jobId],
    queryFn: () => podcastsApi.getJobStatus(jobId!),
    enabled: isJobId && !!jobId,
    refetchInterval: isJobId && !!jobId ? 5000 : false, // Poll every 5s if generating
    staleTime: 2000,
  })

  // Determine if podcast is still generating
  const isGenerating = isJobId || 
    (episode?.job_status && ACTIVE_EPISODE_STATUSES.includes(episode.job_status))
  
  const jobFailed = jobStatus?.status === 'failed' || jobStatus?.status === 'error'

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (isGenerating && isJobId && jobId) {
      // Cancel the job first, then delete the artifact
      setIsCancelling(true)
      try {
        await podcastsApi.cancelJob(jobId)
        toast({
          title: t.podcasts.generationCancelled,
          description: t.podcasts.generationCancelledDesc,
        })
      } catch (error) {
        console.error('Failed to cancel job:', error)
        toast({
          title: t.common.error,
          description: t.podcasts.cancelFailed,
          variant: 'destructive',
        })
        // Continue with deletion even if cancel fails
      } finally {
        setIsCancelling(false)
      }
    }
    
    // Delete the artifact (this may fail for job IDs, but that's okay - we'll refresh anyway)
    try {
      await onDelete(artifact.id)
    } catch (error) {
      console.error('Failed to delete artifact:', error)
      // If delete fails (e.g., backend error with job IDs), still refresh to remove from UI
    }
    
    setDeleteDialogOpen(false)
    
    // Always refresh artifacts list to ensure UI is up to date
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.artifacts(notebookId) })
  }

  const handleCardClick = () => {
    if (!isGenerating && !episodeLoading) {
      setShowPodcastPlayer(true)
    }
  }

  return (
    <>
      <Card 
        className={`transition-colors ${isGenerating ? 'opacity-75' : 'cursor-pointer hover:bg-accent/50'}`}
        onClick={handleCardClick}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className="mt-1">
                {isGenerating ? (
                  <Loader2 className="h-5 w-5 text-primary animate-spin" />
                ) : (
                  <Headphones className="h-5 w-5 text-primary" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm truncate">{artifact.title}</h4>
                  {isGenerating ? (
                    <Badge variant="outline" className="text-xs bg-amber-100 text-amber-800 border-amber-200">
                      {t.podcasts.processingLabel}
                    </Badge>
                  ) : jobFailed ? (
                    <Badge variant="outline" className="text-xs bg-red-100 text-red-800 border-red-200">
                      {t.podcasts.failedLabel}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="text-xs">
                      {t.artifacts.podcast}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {isGenerating 
                    ? t.podcasts.generatingDescription
                    : formatDistanceToNow(new Date(artifact.created), {
                        addSuffix: true,
                        locale: getDateLocale(language)
                      })
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {!isGenerating && !jobFailed && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowPodcastPlayer(true)
                  }}
                  className="h-8"
                  disabled={episodeLoading}
                >
                  <Play className="h-4 w-4 mr-1" />
                  {t.artifacts.playPodcast}
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={handleDeleteClick}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {showPodcastPlayer && !isGenerating && (
        <PodcastPlayer
          podcastId={artifact.artifact_id}
          notebookId={notebookId}
          open={showPodcastPlayer}
          onOpenChange={setShowPodcastPlayer}
        />
      )}

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={
          isGenerating 
            ? t.podcasts.cancelGeneration
            : t.artifacts.deleteArtifact
        }
        description={
          isGenerating
            ? t.podcasts.cancelGenerationConfirm
            : t.artifacts.deleteConfirm
        }
        confirmText={
          isGenerating 
            ? t.podcasts.cancelAndDelete
            : t.common.delete
        }
        onConfirm={handleDeleteConfirm}
        confirmVariant="destructive"
        isLoading={isCancelling}
      />
    </>
  )
}
