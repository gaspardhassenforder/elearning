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

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Play, Pause, Headphones } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'

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
  const router = useRouter()
  const audioRef = useRef<HTMLAudioElement>(null)
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

  const isReady = status === 'completed'

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

    audio.addEventListener('timeupdate', updateTime)
    audio.addEventListener('loadedmetadata', updateDuration)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('timeupdate', updateTime)
      audio.removeEventListener('loadedmetadata', updateDuration)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [playbackSpeed])

  const handlePlayPause = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
      setIsPlaying(false)
    } else {
      audio.play()
      setIsPlaying(true)
    }
  }

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

  const handleViewTranscript = (e: React.MouseEvent) => {
    e.preventDefault()
    if (transcriptUrl) {
      // Use Next.js router for client-side navigation
      router.push(transcriptUrl)
    }
  }

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
            <h4 className="text-sm font-semibold text-foreground mb-1">
              {title}
            </h4>
            <p className="text-xs text-muted-foreground">
              {durationMinutes} {t.learner.podcast.minutes}
            </p>
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
            >
              {isPlaying ? (
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
              {isLoadingMetadata ? (
                <span className="animate-pulse">Loading...</span>
              ) : (
                `${formatTime(currentTime)} / ${formatTime(duration || durationMinutes * 60)}`
              )}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1">
            <Progress value={progressPercentage} className="h-1" />
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

          {/* View Transcript Link */}
          {transcriptUrl && (
            <button
              onClick={handleViewTranscript}
              className="text-xs text-primary hover:underline font-medium"
            >
              {t.learner.podcast.viewTranscript} →
            </button>
          )}
        </div>
      </div>
    </Card>
  )
}
