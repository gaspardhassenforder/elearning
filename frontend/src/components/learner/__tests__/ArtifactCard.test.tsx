/**
 * Story 5.2: ArtifactCard Component Tests
 *
 * Tests for expandable artifact card with type-specific content rendering.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ArtifactCard } from '../ArtifactCard'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        artifacts: {
          quiz: 'Quiz',
          podcast: 'Podcast',
          summary: 'Summary',
          transformation: 'Transformation',
          createdAt: 'Created {time}',
          loadingPreview: 'Loading preview...',
          previewError: 'Failed to load preview',
          retry: 'Try Again',
        },
      },
    },
  }),
}))

// Mock the useLearnerArtifactPreview hook
const mockUseLearnerArtifactPreview = vi.fn()
vi.mock('@/lib/hooks/use-artifacts', () => ({
  useLearnerArtifactPreview: (artifactId: string | null) => mockUseLearnerArtifactPreview(artifactId),
}))

// Mock child components
vi.mock('../InlineQuizWidget', () => ({
  InlineQuizWidget: ({ quizId, title }: any) => (
    <div data-testid="inline-quiz-widget">
      <span>Quiz: {title}</span>
      <span>ID: {quizId}</span>
    </div>
  ),
}))

vi.mock('../InlineAudioPlayer', () => ({
  InlineAudioPlayer: ({ podcastId, title }: any) => (
    <div data-testid="inline-audio-player">
      <span>Podcast: {title}</span>
      <span>ID: {podcastId}</span>
    </div>
  ),
}))

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: () => '2 days ago',
}))

describe('ArtifactCard', () => {
  let queryClient: QueryClient

  const mockQuizArtifact = {
    id: 'artifact:quiz1',
    artifact_type: 'quiz' as const,
    title: 'Machine Learning Quiz',
    created: '2024-01-15T10:00:00Z',
  }

  const mockPodcastArtifact = {
    id: 'artifact:podcast1',
    artifact_type: 'podcast' as const,
    title: 'Introduction to Python',
    created: '2024-01-16T10:00:00Z',
  }

  const mockSummaryArtifact = {
    id: 'artifact:summary1',
    artifact_type: 'summary' as const,
    title: 'Chapter Summary',
    created: '2024-01-17T10:00:00Z',
  }

  const mockTransformationArtifact = {
    id: 'artifact:transform1',
    artifact_type: 'transformation' as const,
    title: 'Code Analysis',
    created: '2024-01-18T10:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })

    // Default mock: not loading, no data
    mockUseLearnerArtifactPreview.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  afterEach(() => {
    queryClient.clear()
  })

  const renderComponent = (
    artifact = mockQuizArtifact,
    isExpanded = false,
    onToggleExpand = vi.fn()
  ) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ArtifactCard
          artifact={artifact}
          isExpanded={isExpanded}
          onToggleExpand={onToggleExpand}
        />
      </QueryClientProvider>
    )
  }

  describe('Collapsed State', () => {
    it('renders artifact title', () => {
      renderComponent(mockQuizArtifact)
      expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
    })

    it('renders created date', () => {
      renderComponent(mockQuizArtifact)
      expect(screen.getByText(/Created 2 days ago/)).toBeInTheDocument()
    })

    it('renders chevron down icon when collapsed', () => {
      const { container } = renderComponent(mockQuizArtifact, false)
      // ChevronDown should be present (lucide-react renders as svg)
      const svgs = container.querySelectorAll('svg')
      expect(svgs.length).toBeGreaterThan(0)
    })

    it('calls onToggleExpand when card is clicked', () => {
      const onToggleExpand = vi.fn()
      renderComponent(mockQuizArtifact, false, onToggleExpand)

      const card = screen.getByText('Machine Learning Quiz').closest('[class*="cursor-pointer"]')
      fireEvent.click(card!)

      expect(onToggleExpand).toHaveBeenCalledTimes(1)
    })
  })

  describe('Type-Specific Icons', () => {
    it('renders quiz icon for quiz artifacts', () => {
      const { container } = renderComponent(mockQuizArtifact)
      // FileQuestion icon should be present
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('renders podcast icon for podcast artifacts', () => {
      const { container } = renderComponent(mockPodcastArtifact)
      // Headphones icon should be present
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('renders summary icon for summary artifacts', () => {
      const { container } = renderComponent(mockSummaryArtifact)
      // FileText icon should be present
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('renders transformation icon for transformation artifacts', () => {
      const { container } = renderComponent(mockTransformationArtifact)
      // FileText icon should be present
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })

  describe('Expanded State', () => {
    it('shows loading spinner when preview is loading', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockQuizArtifact, true)

      expect(screen.getByText('Loading preview...')).toBeInTheDocument()
    })

    it('shows error state with retry button on error', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Network error'),
        refetch: vi.fn(),
      })

      renderComponent(mockQuizArtifact, true)

      expect(screen.getByText('Failed to load preview')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })

    it('calls refetch when retry button is clicked', () => {
      const refetchMock = vi.fn()
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Network error'),
        refetch: refetchMock,
      })

      renderComponent(mockQuizArtifact, true)

      const retryButton = screen.getByText('Try Again')
      fireEvent.click(retryButton)

      expect(refetchMock).toHaveBeenCalledTimes(1)
    })

    it('does not propagate click from retry button to card', () => {
      const onToggleExpand = vi.fn()
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Network error'),
        refetch: vi.fn(),
      })

      renderComponent(mockQuizArtifact, true, onToggleExpand)

      const retryButton = screen.getByText('Try Again')
      fireEvent.click(retryButton)

      // Card click handler should not be called
      expect(onToggleExpand).not.toHaveBeenCalled()
    })
  })

  describe('Quiz Content Rendering', () => {
    it('renders InlineQuizWidget when quiz preview is loaded', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'quiz:123',
          artifact_type: 'quiz',
          title: 'ML Quiz',
          question_count: 5,
          questions: [
            {
              question: 'What is ML?',
              choices: ['A', 'B', 'C'],
            },
          ],
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockQuizArtifact, true)

      expect(screen.getByTestId('inline-quiz-widget')).toBeInTheDocument()
      expect(screen.getByText(/Quiz: ML Quiz/)).toBeInTheDocument()
    })
  })

  describe('Podcast Content Rendering', () => {
    it('renders InlineAudioPlayer when podcast preview is loaded', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'podcast:123',
          artifact_type: 'podcast',
          title: 'Python Podcast',
          duration: '05:30',
          audio_url: '/audio/podcast.mp3',
          transcript: null,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockPodcastArtifact, true)

      expect(screen.getByTestId('inline-audio-player')).toBeInTheDocument()
      expect(screen.getByText(/Podcast: Python Podcast/)).toBeInTheDocument()
    })

    it('handles podcast without audio_url (still generating)', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'podcast:123',
          artifact_type: 'podcast',
          title: 'Python Podcast',
          duration: null,
          audio_url: null,
          transcript: null,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockPodcastArtifact, true)

      expect(screen.getByTestId('inline-audio-player')).toBeInTheDocument()
    })
  })

  describe('Summary Content Rendering', () => {
    it('renders text content for summary preview', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'summary:123',
          artifact_type: 'summary',
          title: 'Chapter Summary',
          content: 'This is the summary content text.',
          word_count: 150,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockSummaryArtifact, true)

      expect(screen.getByText('This is the summary content text.')).toBeInTheDocument()
      expect(screen.getByText(/150 words/)).toBeInTheDocument()
    })
  })

  describe('Transformation Content Rendering', () => {
    it('renders text content for transformation preview', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'transform:123',
          artifact_type: 'transformation',
          title: 'Code Analysis',
          content: 'Analysis result text.',
          word_count: 200,
          transformation_name: 'Code Review',
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockTransformationArtifact, true)

      expect(screen.getByText('Analysis result text.')).toBeInTheDocument()
      expect(screen.getByText(/200 words/)).toBeInTheDocument()
      expect(screen.getByText(/Type: Code Review/)).toBeInTheDocument()
    })
  })

  describe('Lazy Loading', () => {
    it('does not fetch preview when collapsed', () => {
      renderComponent(mockQuizArtifact, false)

      // Hook should be called with null when not expanded
      expect(mockUseLearnerArtifactPreview).toHaveBeenCalledWith(null)
    })

    it('fetches preview when expanded', () => {
      renderComponent(mockQuizArtifact, true)

      // Hook should be called with artifact ID when expanded
      expect(mockUseLearnerArtifactPreview).toHaveBeenCalledWith('artifact:quiz1')
    })
  })

  describe('Styling', () => {
    it('applies hover styling when collapsed', () => {
      const { container } = renderComponent(mockQuizArtifact, false)

      const card = container.querySelector('[class*="hover:bg-accent"]')
      expect(card).toBeInTheDocument()
    })

    it('applies expanded styling when expanded', () => {
      const { container } = renderComponent(mockQuizArtifact, true)

      const card = container.querySelector('[class*="shadow-md"]')
      expect(card).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty content gracefully', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'summary:123',
          artifact_type: 'summary',
          title: 'Empty Summary',
          content: '',
          word_count: 0,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      renderComponent(mockSummaryArtifact, true)

      expect(screen.getByText('No content available')).toBeInTheDocument()
    })

    it('handles invalid date gracefully', () => {
      const artifactWithBadDate = {
        ...mockQuizArtifact,
        created: 'invalid-date',
      }

      // Should not throw
      renderComponent(artifactWithBadDate, false)

      // Title should still render
      expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
    })

    it('handles unknown artifact type', () => {
      mockUseLearnerArtifactPreview.mockReturnValue({
        data: {
          id: 'unknown:123',
          artifact_type: 'unknown',
          title: 'Unknown Type',
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      })

      const unknownArtifact = {
        id: 'artifact:unknown1',
        artifact_type: 'unknown' as any,
        title: 'Unknown Artifact',
        created: '2024-01-15T10:00:00Z',
      }

      renderComponent(unknownArtifact, true)

      expect(screen.getByText('Unsupported artifact type')).toBeInTheDocument()
    })
  })
})
