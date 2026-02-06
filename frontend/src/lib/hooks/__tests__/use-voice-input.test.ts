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

  it('should handle multiple start calls gracefully', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
    })

    // Try to start again while already listening
    act(() => {
      result.current.startListening()
    })

    // Should remain listening without error
    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
      expect(result.current.error).toBeNull()
    })
  })

  it('should expose clearTranscript function', () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate result
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'Test message', confidence: 0.9 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    expect(result.current.transcript).toContain('Test message')

    // Clear transcript
    act(() => {
      result.current.clearTranscript()
    })

    expect(result.current.transcript).toBe('')
  })

  it('should handle interim results correctly without duplication', async () => {
    const { result } = renderHook(() => useVoiceInput())

    act(() => {
      result.current.startListening()
    })

    // Simulate interim result
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'hello', confidence: 0.7 },
              isFinal: false,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toBe('hello')
    })

    // Simulate updated interim result (should replace, not accumulate)
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'hello world', confidence: 0.8 },
              isFinal: false,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toBe('hello world')
      // Should NOT be 'hellohello world'
    })

    // Simulate final result
    if (currentRecognitionInstance?.onresult) {
      act(() => {
        currentRecognitionInstance!.onresult!({
          results: [
            {
              0: { transcript: 'hello world', confidence: 0.95 },
              isFinal: true,
              length: 1,
            },
          ],
          resultIndex: 0,
        } as any)
      })
    }

    await waitFor(() => {
      expect(result.current.transcript).toBe('hello world ')
    })
  })

  it('should set isRequestingPermission when starting', async () => {
    const { result } = renderHook(() => useVoiceInput())

    expect(result.current.isRequestingPermission).toBe(false)

    // Note: In our mock, start() immediately calls onstart, so we can't test
    // the intermediate requesting state. In real usage, there would be a delay
    // while browser shows permission prompt.
    act(() => {
      result.current.startListening()
    })

    // After recognition starts, requesting flag should be cleared
    await waitFor(() => {
      expect(result.current.isListening).toBe(true)
      expect(result.current.isRequestingPermission).toBe(false)
    })
  })
})
