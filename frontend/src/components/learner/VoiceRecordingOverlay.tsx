'use client'

/**
 * VoiceRecordingOverlay - Waveform visualization during voice input
 *
 * Shows a floating overlay above the chat input when recording:
 * - Canvas-based waveform animation using Web Audio API AnalyserNode
 * - Recording duration timer
 * - Pulsing red recording indicator
 * - Stop button to end recording
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { MicOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTranslation } from '@/lib/hooks/use-translation'

interface VoiceRecordingOverlayProps {
  analyserNode: AnalyserNode | null
  onStop: () => void
}

export function VoiceRecordingOverlay({ analyserNode, onStop }: VoiceRecordingOverlayProps) {
  const { t } = useTranslation()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>(0)
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef(Date.now())

  // Timer: update every second
  useEffect(() => {
    startTimeRef.current = Date.now()
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Format seconds as mm:ss
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  // Waveform animation
  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { width, height } = canvas
    const centerY = height / 2

    ctx.clearRect(0, 0, width, height)

    if (analyserNode) {
      const bufferLength = analyserNode.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      analyserNode.getByteTimeDomainData(dataArray)

      ctx.lineWidth = 2
      ctx.strokeStyle = 'hsl(0, 72%, 51%)' // red-500
      ctx.beginPath()

      const sliceWidth = width / bufferLength
      let x = 0

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0 // normalize to [0, 2]
        const y = (v * height) / 2

        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
        x += sliceWidth
      }

      ctx.lineTo(width, centerY)
      ctx.stroke()
    } else {
      // Fallback: flat line
      ctx.lineWidth = 2
      ctx.strokeStyle = 'hsl(0, 72%, 51%)'
      ctx.beginPath()
      ctx.moveTo(0, centerY)
      ctx.lineTo(width, centerY)
      ctx.stroke()
    }

    animationRef.current = requestAnimationFrame(draw)
  }, [analyserNode])

  useEffect(() => {
    animationRef.current = requestAnimationFrame(draw)
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [draw])

  // Handle canvas DPI scaling
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.scale(dpr, dpr)
    }
  }, [])

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 mx-4">
      <div className="bg-background border rounded-2xl shadow-lg px-4 py-3 flex items-center gap-3">
        {/* Recording indicator */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs font-medium text-red-500">
            {formatTime(elapsed)}
          </span>
        </div>

        {/* Waveform canvas */}
        <canvas
          ref={canvasRef}
          className="flex-1 h-8"
          style={{ width: '100%', height: '32px' }}
        />

        {/* Stop button */}
        <Button
          type="button"
          variant="destructive"
          size="icon"
          className="flex-shrink-0 h-8 w-8 rounded-full"
          onClick={onStop}
          aria-label={t.learner.chat.voiceInput.stopRecording}
        >
          <MicOff className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
