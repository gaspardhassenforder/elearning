'use client'

import { useEffect, useMemo, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Download, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { podcastsApi } from '@/lib/api/podcasts'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { resolvePodcastAssetUrl } from '@/lib/api/podcasts'
import { useTranslation } from '@/lib/hooks/use-translation'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
interface PodcastPlayerProps {
  podcastId: string
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

type OutlineSegment = {
  name?: string
  description?: string
  size?: string
}

type OutlineData = {
  segments?: OutlineSegment[]
}

type TranscriptEntry = {
  speaker?: string
  dialogue?: string
}

type TranscriptData = {
  transcript?: TranscriptEntry[]
}

function extractOutlineSegments(outline: unknown): OutlineSegment[] {
  if (outline && typeof outline === 'object' && 'segments' in outline) {
    const data = outline as OutlineData
    if (Array.isArray(data.segments)) {
      return data.segments
    }
  }
  return []
}

function extractTranscriptEntries(transcript: unknown): TranscriptEntry[] {
  if (transcript && typeof transcript === 'object' && 'transcript' in transcript) {
    const data = transcript as TranscriptData
    if (Array.isArray(data.transcript)) {
      return data.transcript
    }
  }
  return []
}

export function PodcastPlayer({ podcastId, notebookId, open, onOpenChange }: PodcastPlayerProps) {
  const { t } = useTranslation()
  const [audioSrc, setAudioSrc] = useState<string | undefined>()
  const [audioError, setAudioError] = useState<string | null>(null)

  // Fetch podcast episode - note: we need to get it from the episodes list
  // For now, we'll fetch all episodes and find the one matching podcastId
  const { data: episodes, isLoading } = useQuery({
    queryKey: QUERY_KEYS.podcastEpisodes,
    queryFn: () => podcastsApi.listEpisodes(),
    enabled: open,
  })

  const episode = useMemo(() => {
    return episodes?.find((ep) => ep.id === podcastId)
  }, [episodes, podcastId])

  const outlineSegments = useMemo(() => extractOutlineSegments(episode?.outline), [episode?.outline])
  const transcriptEntries = useMemo(() => extractTranscriptEntries(episode?.transcript), [episode?.transcript])

  useEffect(() => {
    if (!episode) return

    let revokeUrl: string | undefined
    setAudioError(null)

    const loadProtectedAudio = async () => {
      const directAudioUrl = await resolvePodcastAssetUrl(episode.audio_url ?? episode.audio_file)

      if (!directAudioUrl || !episode.audio_url) {
        setAudioSrc(directAudioUrl)
        return
      }

      try {
        let token: string | undefined
        if (typeof window !== 'undefined') {
          const raw = window.localStorage.getItem('auth-storage')
          if (raw) {
            try {
              const parsed = JSON.parse(raw)
              token = parsed?.state?.token
            } catch (error) {
              console.error('Failed to parse auth storage', error)
            }
          }
        }

        const headers: HeadersInit = {}
        if (token) {
          headers.Authorization = `Bearer ${token}`
        }

        const response = await fetch(directAudioUrl, { headers })
        if (!response.ok) {
          throw new Error(`Audio request failed with status ${response.status}`)
        }

        const blob = await response.blob()
        revokeUrl = URL.createObjectURL(blob)
        setAudioSrc(revokeUrl)
      } catch (error) {
        console.error('Unable to load podcast audio', error)
        setAudioError(t.podcasts.audioUnavailable)
        setAudioSrc(undefined)
      }
    }

    void loadProtectedAudio()

    return () => {
      if (revokeUrl) {
        URL.revokeObjectURL(revokeUrl)
      }
    }
  }, [episode, t])

  const handleDownload = async () => {
    if (!episode || !audioSrc) return

    try {
      const response = await fetch(audioSrc)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${episode.name || 'podcast'}.mp3`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download podcast', error)
    }
  }

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{t.artifacts.podcast}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!episode) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{t.artifacts.podcast}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <p className="text-muted-foreground">
              {t.podcasts.episodeNotFound}
            </p>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{episode.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 overflow-hidden flex flex-col flex-1 min-h-0">
          {audioSrc ? (
            <div className="space-y-2">
              <audio controls preload="none" src={audioSrc} className="w-full" />
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                className="w-full"
              >
                <Download className="h-4 w-4 mr-2" />
                {t.common.download}
              </Button>
            </div>
          ) : audioError ? (
            <p className="text-sm text-destructive">{audioError}</p>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}

          <Tabs defaultValue="summary" className="flex-1 flex flex-col min-h-0">
            <TabsList>
              <TabsTrigger value="summary">
                {t.podcasts.summaryTab}
              </TabsTrigger>
              {transcriptEntries.length > 0 && (
                <TabsTrigger value="transcript">
                  {t.podcasts.transcriptTab}
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="summary" className="flex-1 overflow-y-auto mt-4">
              <ScrollArea className="h-full">
                <div className="space-y-4 pr-4">
                  {outlineSegments.length > 0 ? (
                    outlineSegments.map((segment, index) => (
                      <div key={index} className="space-y-2">
                        {segment.name && (
                          <h4 className="font-semibold">{segment.name}</h4>
                        )}
                        {segment.description && (
                          <p className="text-sm text-muted-foreground">{segment.description}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      {t.podcasts.noSummary}
                    </p>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            {transcriptEntries.length > 0 && (
              <TabsContent value="transcript" className="flex-1 overflow-y-auto mt-4">
                <ScrollArea className="h-full">
                  <div className="space-y-4 pr-4">
                    {transcriptEntries.map((entry, index) => (
                      <div key={index} className="space-y-1">
                        {entry.speaker && (
                          <p className="font-semibold text-sm">{entry.speaker}</p>
                        )}
                        {entry.dialogue && (
                          <p className="text-sm text-muted-foreground">{entry.dialogue}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
            )}
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  )
}
