'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

// TypeScript declarations for Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: 'no-speech' | 'aborted' | 'audio-capture' | 'network' | 'not-allowed' | 'service-not-allowed' | 'bad-grammar' | 'language-not-supported'
  message: string
}

interface SpeechRecognitionResultList {
  length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionResult {
  isFinal: boolean
  length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  start(): void
  stop(): void
  abort(): void
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null
  onend: ((this: SpeechRecognition, ev: Event) => any) | null
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null
}

interface SpeechRecognitionConstructor {
  new(): SpeechRecognition
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

interface UseVoiceInputReturn {
  isListening: boolean
  isSupported: boolean
  transcript: string
  isRequestingPermission: boolean
  startListening: () => void
  stopListening: () => void
  clearTranscript: () => void
  error: string | null
  analyserNode: AnalyserNode | null
}

export function useVoiceInput(language?: string): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [isRequestingPermission, setIsRequestingPermission] = useState(false)
  const [finalTranscript, setFinalTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null)

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)

  // Determine effective language for STT
  const effectiveLang = language || navigator.language || 'en-US'

  // Cleanup Web Audio resources
  const cleanupAudio = useCallback(() => {
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }
    setAnalyserNode(null)
  }, [])

  // Initialize Speech Recognition on mount or language change
  useEffect(() => {
    if (typeof window === 'undefined') return

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognitionAPI) {
      setIsSupported(false)
      return
    }

    setIsSupported(true)
    const recognition = new SpeechRecognitionAPI()

    // Configuration
    recognition.continuous = true  // Keep recording until user stops
    recognition.interimResults = true  // Real-time feedback
    recognition.maxAlternatives = 1
    recognition.lang = effectiveLang  // Use app language for STT

    // Event handlers
    recognition.onstart = () => {
      setIsListening(true)
      setIsRequestingPermission(false)
      setError(null)
    }

    recognition.onend = () => {
      setIsListening(false)
      setIsRequestingPermission(false)
      cleanupAudio()
    }

    recognition.onerror = (event) => {
      setIsListening(false)
      setIsRequestingPermission(false)
      cleanupAudio()

      // Map error codes to user-friendly messages
      switch (event.error) {
        case 'not-allowed':
        case 'service-not-allowed':
          setError('microphone-permission-denied')
          break
        case 'no-speech':
          setError('no-speech-detected')
          break
        case 'network':
          setError('network-error')
          break
        case 'audio-capture':
          setError('no-microphone')
          break
        default:
          setError('unknown-error')
      }
    }

    recognition.onresult = (event) => {
      let newFinal = ''
      let newInterim = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcriptText = result[0].transcript

        if (result.isFinal) {
          newFinal += transcriptText + ' '
        } else {
          newInterim += transcriptText
        }
      }

      // Update state correctly: accumulate finals, replace interim
      if (newFinal) {
        setFinalTranscript(prev => prev + newFinal)
        setInterimTranscript('')  // Clear interim when final arrives
      } else if (newInterim) {
        setInterimTranscript(newInterim)  // Replace interim, don't accumulate
      }
    }

    recognitionRef.current = recognition

    // Cleanup on unmount or language change
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
      cleanupAudio()
    }
  }, [effectiveLang, cleanupAudio])

  // Start Web Audio API for waveform visualization
  const startAudioAnalyser = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream

      const audioContext = new AudioContext()
      audioContextRef.current = audioContext

      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      analyser.smoothingTimeConstant = 0.8
      source.connect(analyser)

      setAnalyserNode(analyser)
    } catch {
      // Audio analyser is optional - voice input still works without it
    }
  }, [])

  const startListening = useCallback(() => {
    if (!recognitionRef.current || !isSupported || isListening || isRequestingPermission) return

    try {
      setError(null)
      setFinalTranscript('')  // Clear previous transcript
      setInterimTranscript('')
      setIsRequestingPermission(true)

      // Start audio analyser for waveform (fire-and-forget)
      startAudioAnalyser()

      recognitionRef.current.start()
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to start speech recognition:', err)
      }
      setError('failed-to-start')
      setIsRequestingPermission(false)
      cleanupAudio()
    }
  }, [isSupported, isListening, isRequestingPermission, startAudioAnalyser, cleanupAudio])

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return

    try {
      recognitionRef.current.stop()
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to stop speech recognition:', err)
      }
    }
    cleanupAudio()
  }, [cleanupAudio])

  const clearTranscript = useCallback(() => {
    setFinalTranscript('')
    setInterimTranscript('')
    setError(null)
  }, [])

  // Combine final and interim for return value
  const transcript = finalTranscript + interimTranscript

  return {
    isListening,
    isSupported,
    transcript,
    isRequestingPermission,
    startListening,
    stopListening,
    clearTranscript,
    error,
    analyserNode,
  }
}
