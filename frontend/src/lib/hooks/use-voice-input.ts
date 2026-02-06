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
  startListening: () => void
  stopListening: () => void
  error: string | null
}

export function useVoiceInput(): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // Initialize Speech Recognition on mount
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
    recognition.continuous = false  // Single utterance mode
    recognition.interimResults = true  // Real-time feedback
    recognition.maxAlternatives = 1
    recognition.lang = navigator.language || 'en-US'  // User's browser language

    // Event handlers
    recognition.onstart = () => {
      setIsListening(true)
      setError(null)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.onerror = (event) => {
      setIsListening(false)

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
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcriptText = result[0].transcript

        if (result.isFinal) {
          finalTranscript += transcriptText + ' '
        } else {
          interimTranscript += transcriptText
        }
      }

      // Update state with final or interim transcript
      if (finalTranscript) {
        setTranscript(prev => prev + finalTranscript)
      } else if (interimTranscript) {
        // Show interim results for real-time feedback
        setTranscript(prev => prev + interimTranscript)
      }
    }

    recognitionRef.current = recognition

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [])

  const startListening = useCallback(() => {
    if (!recognitionRef.current || !isSupported) return

    try {
      setError(null)
      setTranscript('')  // Clear previous transcript
      recognitionRef.current.start()
    } catch (err) {
      console.error('Failed to start speech recognition:', err)
      setError('failed-to-start')
    }
  }, [isSupported])

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return

    try {
      recognitionRef.current.stop()
    } catch (err) {
      console.error('Failed to stop speech recognition:', err)
    }
  }, [])

  return {
    isListening,
    isSupported,
    transcript,
    startListening,
    stopListening,
    error,
  }
}
