'use client'

/**
 * Story 4.6: Inline Audio Player Component
 *
 * Displays podcast player inline in chat with playback controls.
 * Registered as assistant-ui custom message part for surface_podcast tool results.
 *
 * Features:
 * - HTML5 audio element with play/pause controls
 * - Progress bar with time tracking
 * - Playback speed control (1x, 1.25x, 1.5x, 2x)
 * - "View Transcript" link
 * - Loading state for generating podcasts
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Play, Pause, Headphones } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'

interface InlineAudioPlayerProps {
  podcastId: string
  title: string
  audioUrl: string
  durationMinutes: number
  transcriptUrl?: string
  status: string
}

export function InlineAudioPlayer({
  podcastId,
  title,
  audioUrl,
  durationMinutes,
  transcriptUrl,
  status,
}: InlineAudioPlayerProps) {
  const { t } = useTranslation()
  const audioRef = useRef<HTMLAudioElement>(null)
  const seekBarRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(() => {
    // Restore playback speed from localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('podcast-playback-speed')
      return saved ? parseFloat(saved) : 1
    }
    return 1
  })
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(true)
  const [audioError, setAudioError] = useState<string | null>(null)
  const [canPlay, setCanPlay] = useState(false)
  const blobUrlRef = useRef<string | null>(null)
  const fallbackAttemptedRef = useRef(false)
  const [transcript, setTranscript] = useState<string | null>(null)
  const [transcriptLoading, setTranscriptLoading] = useState(false)

  const isReady = status === 'completed'

  // Build transcript URL: use prop if provided, otherwise derive from podcastId
  const effectiveTranscriptUrl = transcriptUrl || (podcastId ? `/api/podcasts/${podcastId}/transcript` : null)

  // Update progress and handle metadata loading
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    // Apply saved playback speed on mount
    audio.playbackRate = playbackSpeed

    const updateTime = () => setCurrentTime(audio.currentTime)
    const updateDuration = () => {
      setDuration(audio.duration)
      setIsLoadingMetadata(false)
    }
    const handleEnded = () => setIsPlaying(false)
    const handleCanPlay = () => {
      setCanPlay(true)
      setIsLoadingMetadata(false)
    }
    const handleError = () => {
      console.error('[InlineAudioPlayer] Audio load error:', audio.error)
      setAudioError(t.learner.podcast.playbackError || 'Unable to play audio')
      setIsLoadingMetadata(false)
    }

    audio.addEventListener('timeupdate', updateTime)
    audio.addEventListener('loadedmetadata', updateDuration)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('canplay', handleCanPlay)
    audio.addEventListener('error', handleError)

    return () => {
      audio.removeEventListener('timeupdate', updateTime)
      audio.removeEventListener('loadedmetadata', updateDuration)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('canplay', handleCanPlay)
      audio.removeEventListener('error', handleError)
    }
  }, [playbackSpeed, t.learner.podcast.playbackError])

  // Fallback: if native audio loading fails, retry once with authenticated fetch
  useEffect(() => {
    if (!audioError || !audioUrl || fallbackAttemptedRef.current) return
    fallbackAttemptedRef.current = true

    let cancelled = false

    const retryWithFetch = async () => {
      try {
        const response = await fetch(audioUrl, { credentials: 'include' })
        if (!response.ok) {
          console.error('[InlineAudioPlayer] Authenticated fetch failed:', response.status)
          return
        }
        const blob = await response.blob()
        if (cancelled) return

        const blobUrl = URL.createObjectURL(blob)
        blobUrlRef.current = blobUrl

        const audio = audioRef.current
        if (audio) {
          audio.src = blobUrl
          audio.load()
          setAudioError(null)
          setCanPlay(false)
          setIsLoadingMetadata(true)
        }
      } catch (err) {
        console.error('[InlineAudioPlayer] Fallback fetch failed:', err)
      }
    }

    retryWithFetch()

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioError, audioUrl])

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current)
      }
    }
  }, [])

  const handlePlayPause = async () => {
    const audio = audioRef.current
    if (!audio) return

    if (audioError) {
      // Retry: reset error and reload
      setAudioError(null)
      setCanPlay(false)
      setIsLoadingMetadata(true)
      audio.load()
      return
    }

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      try {
        await audio.play()
        setIsPlaying(true)
      } catch (err) {
        console.error('[InlineAudioPlayer] Play failed:', err)
        setAudioError(t.learner.podcast.playbackError || 'Unable to play audio')
        setIsPlaying(false)
      }
    }
  }

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current
    const bar = seekBarRef.current
    if (!audio || !bar || !duration) return

    const rect = bar.getBoundingClientRect()
    const fraction = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    audio.currentTime = fraction * duration
    setCurrentTime(audio.currentTime)
  }, [duration])

  const handleSpeedChange = (speed: number) => {
    const audio = audioRef.current
    if (!audio) return

    audio.playbackRate = speed
    setPlaybackSpeed(speed)
    // Persist speed preference to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('podcast-playback-speed', speed.toString())
    }
  }

  // Auto-fetch transcript on mount when URL is available
  useEffect(() => {
    if (!effectiveTranscriptUrl || transcript) return

    let cancelled = false
    setTranscriptLoading(true)

    const fetchTranscript = async () => {
      try {
        const response = await fetch(effectiveTranscriptUrl, { credentials: 'include' })
        if (!response.ok || cancelled) {
          if (!response.ok) console.warn('[InlineAudioPlayer] Transcript fetch failed:', response.status)
          return
        }
        const data = await response.json()
        if (cancelled) return

        const raw = data.transcript
        if (typeof raw === 'string') {
          setTranscript(raw)
        } else if (raw && typeof raw === 'object' && Array.isArray(raw.transcript)) {
          const formatted = raw.transcript
            .map((entry: { speaker?: string; dialogue?: string }) =>
              entry.speaker ? `**${entry.speaker}:** ${entry.dialogue || ''}` : entry.dialogue || ''
            )
            .join('\n\n')
          setTranscript(formatted)
        } else {
          setTranscript(JSON.stringify(raw, null, 2))
        }
      } catch (err) {
        console.error('[InlineAudioPlayer] Failed to fetch transcript:', err)
      } finally {
        if (!cancelled) setTranscriptLoading(false)
      }
    }

    fetchTranscript()
    return () => { cancelled = true }
  }, [effectiveTranscriptUrl, transcript])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0

  if (!isReady) {
    return (
      <Card className="my-2 p-4 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
            <Headphones className="h-4 w-4 text-primary animate-pulse" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-foreground mb-1">{title}</h4>
            <p className="text-xs text-muted-foreground">
              {t.learner.podcast.generating || `Podcast is currently ${status}. Please try again later.`}
            </p>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="my-2 p-4 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700">
      <div className="flex items-start gap-3">
        {/* Podcast icon */}
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <Headphones className="h-4 w-4 text-primary" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Podcast title and duration */}
          <div>
            <h4 className="text-sm font-semibold text-foreground">
              {title}
            </h4>
            {durationMinutes > 0 && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {durationMinutes} {t.learner.podcast.minutes}
              </p>
            )}
          </div>

          {/* HTML5 Audio Element (hidden) */}
          <audio ref={audioRef} src={audioUrl} preload="metadata" />

          {/* Play/Pause Button */}
          <div className="flex items-center gap-2">
            <Button
              onClick={handlePlayPause}
              size="sm"
              variant="outline"
              className="w-20"
              disabled={isLoadingMetadata && !audioError}
            >
              {audioError ? (
                <>
                  <Play className="h-3 w-3 mr-1" />
                  {t.common.retry}
                </>
              ) : isPlaying ? (
                <>
                  <Pause className="h-3 w-3 mr-1" />
                  {t.learner.podcast.pause}
                </>
              ) : (
                <>
                  <Play className="h-3 w-3 mr-1" />
                  {t.learner.podcast.play}
                </>
              )}
            </Button>

            {/* Time display */}
            <span className="text-xs text-muted-foreground">
              {audioError ? (
                <span className="text-orange-600 dark:text-orange-400">{audioError}</span>
              ) : isLoadingMetadata ? (
                <span className="animate-pulse">{t.common.loading}</span>
              ) : (
                `${formatTime(currentTime)} / ${formatTime(duration || durationMinutes * 60)}`
              )}
            </span>
          </div>

          {/* Seek Bar */}
          <div
            ref={seekBarRef}
            onClick={handleSeek}
            className="relative h-3 cursor-pointer group rounded-full border border-warm-neutral-400 dark:border-warm-neutral-500 overflow-hidden"
            role="slider"
            aria-label="Seek"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(progressPercentage)}
          >
            <div className="absolute inset-0 bg-warm-neutral-400/40 dark:bg-warm-neutral-500/40" />
            <div
              className="absolute inset-y-0 left-0 bg-primary transition-[width] duration-100"
              style={{ width: `${progressPercentage}%` }}
            />
            <div
              className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-primary shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ left: `calc(${progressPercentage}% - 8px)` }}
            />
          </div>

          {/* Speed Controls */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {t.learner.podcast.speed}:
            </span>
            {[1, 1.25, 1.5, 2].map((speed) => (
              <button
                key={speed}
                onClick={() => handleSpeedChange(speed)}
                className={cn(
                  'text-xs px-2 py-1 rounded transition-colors',
                  playbackSpeed === speed
                    ? 'bg-primary text-primary-foreground font-medium'
                    : 'bg-warm-neutral-100 dark:bg-warm-neutral-800 text-muted-foreground hover:bg-warm-neutral-200 dark:hover:bg-warm-neutral-700'
                )}
              >
                {speed}x
              </button>
            ))}
          </div>

          {/* Transcript */}
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              {t.learner.podcast.viewTranscript}
            </p>
            <div className="h-48 rounded-md border border-warm-neutral-200 dark:border-warm-neutral-700 bg-white dark:bg-warm-neutral-950 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="p-3">
                  {transcriptLoading ? (
                    <p className="text-xs text-muted-foreground animate-pulse">{t.common.loading}</p>
                  ) : transcript ? (
                    <div className="text-xs text-foreground leading-relaxed prose prose-xs dark:prose-invert max-w-none">
                      <ReactMarkdown>{transcript}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">{t.learner.artifacts.noContent}</p>
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
