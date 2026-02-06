import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ChatPanel } from '../ChatPanel'

// Mock translation hook
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        chat: {
          title: 'AI Teacher',
          placeholder: 'Ask a question...',
          send: 'Send',
          loadingHistory: 'Loading conversation history...',
          voiceInput: {
            startRecording: 'Start voice input',
            stopRecording: 'Stop recording',
            microphoneError: 'Microphone access denied',
            microphoneErrorDesc: 'Please allow microphone access in your browser settings to use voice input.',
            noSpeech: 'No speech detected',
            noSpeechDesc: 'Please speak clearly into your microphone and try again.',
            networkError: 'Network error',
            networkErrorDesc: 'Voice recognition requires an internet connection.',
            noMicrophone: 'No microphone found',
            noMicrophoneDesc: 'Please connect a microphone to use voice input.',
            error: 'Voice input error',
            errorDesc: 'Something went wrong with voice input.',
          },
        },
      },
    },
    language: 'en-US',
    setLanguage: vi.fn(),
  }),
}))

// Mock learner chat hook
vi.mock('@/lib/hooks/use-learner-chat', () => ({
  useLearnerChat: vi.fn(() => ({
    isLoading: false,
    isStreaming: false,
    error: null,
    sendMessage: vi.fn(),
    messages: [],
  })),
  useChatHistory: vi.fn(() => ({
    data: { messages: [] },
    isLoading: false,
    error: null,
  })),
}))

// Mock learner store
vi.mock('@/lib/stores/learner-store', () => ({
  useLearnerStore: vi.fn(() => ({
    activeJob: null,
    setActiveJob: vi.fn(),
    clearActiveJob: vi.fn(),
  })),
}))

// Mock job status hook
vi.mock('@/lib/hooks/use-job-status', () => ({
  useJobStatus: vi.fn(() => ({
    status: null,
    progress: 0,
    error: null,
  })),
}))

// Mock toast hook - create mock outside to track calls
const mockToastFn = vi.fn()
vi.mock('@/lib/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToastFn,
  }),
}))

// Mock voice input hook - will be modified per test
vi.mock('@/lib/hooks/use-voice-input', () => ({
  useVoiceInput: vi.fn(() => ({
    isListening: false,
    isSupported: true,
    transcript: '',
    startListening: vi.fn(),
    stopListening: vi.fn(),
    error: null,
  })),
}))

describe('ChatPanel Voice Input Integration', () => {
  let queryClient: QueryClient

  beforeEach(async () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()

    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn()

    // Reset mock to default state
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })
  })

  it('should render microphone button when voice input is supported', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Start voice input')
    expect(micButton).toBeInTheDocument()
  })

  it('should not render microphone button when voice input is not supported', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: false,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    expect(screen.queryByLabelText('Start voice input')).not.toBeInTheDocument()
  })

  it('should call startListening when microphone button is clicked', async () => {
    const mockStartListening = vi.fn()
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: mockStartListening,
      stopListening: vi.fn(),
      error: null,
    })

    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Start voice input')
    await user.click(micButton)

    expect(mockStartListening).toHaveBeenCalled()
  })

  it('should show recording state with pulsing icon', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Stop recording')
    expect(micButton).toBeInTheDocument()
    expect(micButton).toHaveClass('animate-pulse')
  })

  it('should call stopListening when recording and button clicked', async () => {
    const mockStopListening = vi.fn()
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: mockStopListening,
      error: null,
    })

    const user = userEvent.setup()

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Stop recording')
    await user.click(micButton)

    expect(mockStopListening).toHaveBeenCalled()
  })

  it('should populate input field with transcript', async () => {
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    // Update mock to return transcript
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: 'Hello from voice input',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    // Force re-render with new transcript
    rerender(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement
    await waitFor(() => {
      expect(input.value).toBe('Hello from voice input')
    })
  })

  it('should show toast on microphone permission denied error', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: 'microphone-permission-denied',
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalledWith({
        title: 'Microphone access denied',
        description: 'Please allow microphone access in your browser settings to use voice input.',
        variant: 'destructive',
      })
    })
  })

  it('should show toast on network error', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: 'network-error',
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalledWith({
        title: 'Network error',
        description: 'Voice recognition requires an internet connection.',
        variant: 'destructive',
      })
    })
  })

  it('should show toast on no speech detected error', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: 'no-speech-detected',
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalledWith({
        title: 'No speech detected',
        description: 'Please speak clearly into your microphone and try again.',
        variant: 'destructive',
      })
    })
  })

  it('should show toast on no microphone error', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: 'no-microphone',
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalledWith({
        title: 'No microphone found',
        description: 'Please connect a microphone to use voice input.',
        variant: 'destructive',
      })
    })
  })

  it('should show generic error toast for unknown errors', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: false,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: 'failed-to-start',
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(mockToastFn).toHaveBeenCalledWith({
        title: 'Voice input error',
        description: 'Something went wrong with voice input.',
        variant: 'destructive',
      })
    })
  })

  it('should have proper accessibility attributes on microphone button', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Start voice input')
    expect(micButton).toHaveAttribute('aria-label', 'Start voice input')
    expect(micButton).toHaveAttribute('type', 'button')
  })

  it('should change aria-label when recording', async () => {
    const { useVoiceInput } = await import('@/lib/hooks/use-voice-input')
    vi.mocked(useVoiceInput).mockReturnValue({
      isListening: true,
      isSupported: true,
      transcript: '',
      startListening: vi.fn(),
      stopListening: vi.fn(),
      error: null,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <ChatPanel notebookId="test-notebook" />
      </QueryClientProvider>
    )

    const micButton = screen.getByLabelText('Stop recording')
    expect(micButton).toHaveAttribute('aria-label', 'Stop recording')
  })
})
