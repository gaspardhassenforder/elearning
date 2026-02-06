import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useVoiceInput } from '../use-voice-input'

// Track the current instance for testing
let currentRecognitionInstance: MockSpeechRecognition | null = null

// Mock SpeechRecognition
class MockSpeechRecognition {
  continuous = false
  interimResults = false
  lang = ''
  maxAlternatives = 1
  onstart: ((event: Event) => void) | null = null
  onend: ((event: Event) => void) | null = null
  onerror: ((event: any) => void) | null = null
  onresult: ((event: any) => void) | null = null

  constructor() {
    currentRecognitionInstance = this
  }

  start() {
    if (this.onstart) {
      this.onstart(new Event('start'))
    }
  }

  stop() {
    if (this.onend) {
      this.onend(new Event('end'))
    }
  }

  abort() {
    if (this.onend) {
      this.onend(new Event('end'))
    }
  }
}

describe('useVoiceInput', () => {
  beforeEach(() => {
    // Mock window.SpeechRecognition
    vi.stubGlobal('SpeechRecognition', MockSpeechRecognition)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should detect Speech API support', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(true)
  })

  it('should detect when Speech API is not supported', () => {
    vi.unstubAllGlobals()
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(false)
  })

  it('should start listening when startListening is called', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
    })
  })

  it('should stop listening when stopListening is called', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
    })

    act(() => {
      result.current.stopListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(false)
    })
  })

  it('should set error on permission denied', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate permission denied error using the current instance
    if (currentRecognitionInstance?.onerror) {
      act(() => {
        currentRecognitionInstance!.onerror!({
          error: 'not-allowed',
          message: 'Permission denied',
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.error).toBe('microphone-permission-denied')
    })
  })

  it('should update transcript on speech result', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate speech recognition result using the current instance
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'Hello world', confidence: 0.9 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toContain('Hello world')
    })
  })

  it('should clear transcript on new recording start', async () => {
    const { result } = renderHook(() => useVoiceInput())

    // Set initial transcript
    act(() => {
      result.current.startListening()
    })

    // Simulate result using the current instance
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'First message', confidence: 0.9 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toContain('First message')
    })

    // Stop and start again
    act(() => {
      result.current.stopListening()
    })

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.transcript).toBe('')
    })
  })

  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() => useVoiceInput())
    const abortSpy = vi.spyOn(MockSpeechRecognition.prototype, 'abort')

    unmount()

    expect(abortSpy).toHaveBeenCalled()
  })

  it('should handle network error', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    if (currentRecognitionInstance?.onerror) {
      act(() => {
        currentRecognitionInstance!.onerror!({
          error: 'network',
          message: 'Network error',
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.error).toBe('network-error')
    })
  })

  it('should handle no-speech error', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    if (currentRecognitionInstance?.onerror) {
      act(() => {
        currentRecognitionInstance!.onerror!({
          error: 'no-speech',
          message: 'No speech detected',
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.error).toBe('no-speech-detected')
    })
  })

  it('should handle audio-capture error', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    if (currentRecognitionInstance?.onerror) {
      act(() => {
        currentRecognitionInstance!.onerror!({
          error: 'audio-capture',
          message: 'No microphone',
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.error).toBe('no-microphone')
    })
  })
})
