'use client'

/**
 * InlineVideoPlayer
 *
 * Embeds a video player directly in chat when the AI surfaces a video source.
 * Auto-expanded (required viewing). Shows "I've watched this" confirmation button
 * after 90% of the video has been watched.
 *
 * - YouTube: uses YouTube IFrame Player API (YT.Player) for progress tracking
 * - MP4: uses VideoViewer with onProgress callback
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { ChevronDown, ChevronUp, Video, CheckCircle2 } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { VideoViewer } from './VideoViewer'
import { getVideoType, extractYouTubeId } from '@/lib/utils/source-type'
import { cn } from '@/lib/utils'

interface InlineVideoPlayerProps {
  sourceId: string
  title: string
  assetUrl?: string | null
  assetFilePath?: string | null
  timestampSeconds?: number
  relevance?: string
  onConfirm: (message: string) => void
}

// Module-level singletons for YT API loading
let ytApiLoaded = false
let ytApiReady = false
const ytReadyCallbacks: Array<() => void> = []

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const w = typeof window !== 'undefined' ? (window as any) : null

function ensureYTApiLoaded(onReady: () => void) {
  if (ytApiReady && w?.YT) {
    onReady()
    return
  }
  ytReadyCallbacks.push(onReady)
  if (!ytApiLoaded) {
    ytApiLoaded = true
    const script = document.createElement('script')
    script.src = 'https://www.youtube.com/iframe_api'
    document.head.appendChild(script)
    const prev = w?.onYouTubeIframeAPIReady as (() => void) | undefined
    if (w) {
      w.onYouTubeIframeAPIReady = () => {
        prev?.()
        ytApiReady = true
        ytReadyCallbacks.forEach((cb) => cb())
        ytReadyCallbacks.length = 0
      }
    }
  }
}

export function InlineVideoPlayer({
  sourceId,
  title,
  assetUrl,
  assetFilePath,
  timestampSeconds,
  relevance,
  onConfirm,
}: InlineVideoPlayerProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [watchedEnough, setWatchedEnough] = useState(false)
  const [confirmed, setConfirmed] = useState(false)

  const syntheticSource = {
    id: sourceId,
    asset: { url: assetUrl ?? null, file_path: assetFilePath ?? null },
  }
  const videoType = getVideoType(syntheticSource)

  // YouTube player tracking
  const ytWrapperRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ytPlayerRef = useRef<any>(null)
  const ytIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const watchedEnoughRef = useRef(false)

  // Setup YouTube IFrame Player when expanded
  useEffect(() => {
    if (!isExpanded || videoType !== 'youtube' || !ytWrapperRef.current) return
    if (ytPlayerRef.current) return

    const videoId = extractYouTubeId(assetUrl ?? '')
    if (!videoId) return

    const wrapper = ytWrapperRef.current
    // Create inner div for YT.Player to replace (keeps React's wrapper div clean)
    const innerDiv = document.createElement('div')
    innerDiv.style.width = '100%'
    innerDiv.style.height = '100%'
    wrapper.appendChild(innerDiv)

    ensureYTApiLoaded(() => {
      if (!wrapper.parentNode) return // component unmounted before API ready
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const YT = w?.YT as any
      ytPlayerRef.current = new YT.Player(innerDiv, {
        videoId,
        width: '100%',
        height: '100%',
        playerVars: {
          start: timestampSeconds ? Math.floor(timestampSeconds) : 0,
          rel: 0,
        },
        events: {
          onReady: () => {
            ytIntervalRef.current = setInterval(() => {
              const player = ytPlayerRef.current
              if (!player) return
              const currentTime = player.getCurrentTime?.() ?? 0
              const duration = player.getDuration?.() ?? 0
              if (duration > 0 && currentTime / duration >= 0.9 && !watchedEnoughRef.current) {
                watchedEnoughRef.current = true
                setWatchedEnough(true)
                if (ytIntervalRef.current) {
                  clearInterval(ytIntervalRef.current)
                  ytIntervalRef.current = null
                }
              }
            }, 500)
          },
        },
      })
    })

    return () => {
      if (ytIntervalRef.current) {
        clearInterval(ytIntervalRef.current)
        ytIntervalRef.current = null
      }
      if (ytPlayerRef.current) {
        ytPlayerRef.current.destroy?.()
        ytPlayerRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isExpanded, videoType])

  // MP4 progress callback — stable reference via ref guard
  const handleMp4Progress = useCallback((ratio: number) => {
    if (ratio >= 0.9 && !watchedEnoughRef.current) {
      watchedEnoughRef.current = true
      setWatchedEnough(true)
    }
  }, [])

  const handleConfirm = () => {
    setConfirmed(true)
    onConfirm("I've watched the video")
  }

  return (
    <Card className="my-2 bg-warm-neutral-50 dark:bg-warm-neutral-900 border-warm-neutral-200 dark:border-warm-neutral-700 overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-warm-neutral-100 dark:hover:bg-warm-neutral-800 transition-colors"
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center">
          <Video className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-foreground truncate">{title}</h4>
          {relevance && (
            <p className="text-xs text-muted-foreground mt-0.5 truncate">{relevance}</p>
          )}
        </div>
        {confirmed && (
          <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium flex-shrink-0">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Done
          </div>
        )}
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        )}
      </button>

      {/* Player body */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          <div className="aspect-video w-full rounded overflow-hidden bg-black">
            {videoType === 'youtube' ? (
              <div ref={ytWrapperRef} className="w-full h-full" />
            ) : (
              <div className="h-full">
                <VideoViewer
                  source={syntheticSource}
                  timestampSeconds={timestampSeconds}
                  onProgress={handleMp4Progress}
                />
              </div>
            )}
          </div>

          {/* Confirmation button — appears at 90% */}
          {watchedEnough && !confirmed && (
            <Button
              onClick={handleConfirm}
              className={cn(
                'w-full gap-2 bg-green-600 hover:bg-green-700 text-white',
                'animate-pulse'
              )}
            >
              <CheckCircle2 className="h-4 w-4" />
              I&apos;ve watched this
            </Button>
          )}
        </div>
      )}
    </Card>
  )
}
