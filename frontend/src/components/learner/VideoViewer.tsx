'use client'

import { useEffect, useRef } from 'react'
import { getVideoType, extractYouTubeId } from '@/lib/utils/source-type'

interface VideoViewerProps {
  source: {
    id: string
    asset?: { file_path?: string | null; url?: string | null } | null
  }
  timestampSeconds?: number
  onProgress?: (ratio: number) => void
}

export function VideoViewer({ source, timestampSeconds, onProgress }: VideoViewerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const videoType = getVideoType(source)

  // Seek HTML5 video when timestampSeconds changes
  useEffect(() => {
    if (videoRef.current && timestampSeconds !== undefined) {
      videoRef.current.currentTime = timestampSeconds
    }
  }, [timestampSeconds])

  if (videoType === 'youtube') {
    const youtubeUrl = source.asset?.url ?? ''
    const videoId = extractYouTubeId(youtubeUrl)
    if (!videoId) {
      return (
        <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-4">
          Could not load YouTube video
        </div>
      )
    }
    const startParam = timestampSeconds !== undefined ? `&start=${Math.floor(timestampSeconds)}` : ''
    const embedUrl = `https://www.youtube.com/embed/${videoId}?rel=0${startParam}`
    return (
      /*
        h-full fills the CardContent.
        The iframe uses height:100% so it drives sizing from the actual
        available height (not a viewport estimate), then aspect-ratio
        derives the width. maxWidth:100% prevents horizontal overflow on
        very narrow containers.
      */
      <div className="h-full w-full p-4 flex items-start justify-center overflow-hidden">
        <iframe
          key={`yt-${videoId}-${Math.floor(timestampSeconds ?? 0)}`}
          src={embedUrl}
          title="YouTube video"
          className="rounded block"
          style={{ height: '100%', aspectRatio: '16 / 9', maxWidth: '100%' }}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    )
  }

  if (videoType === 'mp4') {
    // Use the same relative API proxy pattern as PdfViewer (/api/sources/.../file)
    const videoUrl = `/api/sources/${encodeURIComponent(source.id)}/video`
    return (
      <div className="h-full w-full p-4 flex items-start justify-center overflow-hidden">
        <video
          ref={videoRef}
          className="rounded block"
          style={{ height: '100%', aspectRatio: '16 / 9', maxWidth: '100%' }}
          controls
          src={videoUrl}
          onTimeUpdate={() => {
            const v = videoRef.current
            if (v && v.duration > 0 && onProgress) {
              onProgress(v.currentTime / v.duration)
            }
          }}
        >
          Your browser does not support the video tag.
        </video>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-4">
      Unsupported video format
    </div>
  )
}
