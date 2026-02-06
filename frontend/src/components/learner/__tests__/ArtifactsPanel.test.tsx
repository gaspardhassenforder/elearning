/**
 * Story 5.2: ArtifactsPanel Component Tests
 *
 * Tests for the artifacts panel with list display and accordion behavior.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ArtifactsPanel } from '../ArtifactsPanel'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        artifacts: {
          noArtifacts: 'No artifacts yet',
          noArtifactsDesc: 'Your AI teacher may generate quizzes and summaries as you learn.',
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

// Mock the useNotebookArtifacts hook
const mockUseNotebookArtifacts = vi.fn()
vi.mock('@/lib/hooks/use-artifacts', () => ({
  useNotebookArtifacts: () => mockUseNotebookArtifacts(),
  useLearnerArtifactPreview: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}))

// Mock ArtifactCard to simplify testing
vi.mock('../ArtifactCard', () => ({
  ArtifactCard: ({ artifact, isExpanded, onToggleExpand }: any) => (
    <div
      data-testid={`artifact-card-${artifact.id}`}
      data-expanded={isExpanded}
      onClick={onToggleExpand}
    >
      <span>{artifact.title}</span>
      <span>{artifact.artifact_type}</span>
    </div>
  ),
}))

describe('ArtifactsPanel', () => {
  let queryClient: QueryClient

  const mockArtifacts = [
    {
      id: 'artifact:quiz1',
      artifact_type: 'quiz' as const,
      title: 'Machine Learning Quiz',
      created: '2024-01-15T10:00:00Z',
    },
    {
      id: 'artifact:podcast1',
      artifact_type: 'podcast' as const,
      title: 'Introduction to Python',
      created: '2024-01-16T10:00:00Z',
    },
    {
      id: 'artifact:summary1',
      artifact_type: 'summary' as const,
      title: 'Chapter Summary',
      created: '2024-01-17T10:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
  })

  afterEach(() => {
    queryClient.clear()
  })

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ArtifactsPanel notebookId="notebook:123" />
      </QueryClientProvider>
    )
  }

  describe('Loading State', () => {
    it('shows loading spinner while fetching artifacts', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      })

      renderComponent()

      // LoadingSpinner has data-testid="loading-spinner"
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows empty state when no artifacts exist', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByText('No artifacts yet')).toBeInTheDocument()
      expect(screen.getByText('Your AI teacher may generate quizzes and summaries as you learn.')).toBeInTheDocument()
    })

    it('shows empty state when data is undefined', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByText('No artifacts yet')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('shows empty state on error (treated as empty for simplicity)', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
      })

      renderComponent()

      expect(screen.getByText('No artifacts yet')).toBeInTheDocument()
    })
  })

  describe('Artifacts List', () => {
    it('renders all artifacts when data is loaded', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByTestId('artifact-card-artifact:quiz1')).toBeInTheDocument()
      expect(screen.getByTestId('artifact-card-artifact:podcast1')).toBeInTheDocument()
      expect(screen.getByTestId('artifact-card-artifact:summary1')).toBeInTheDocument()
    })

    it('displays artifact titles', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
      expect(screen.getByText('Introduction to Python')).toBeInTheDocument()
      expect(screen.getByText('Chapter Summary')).toBeInTheDocument()
    })

    it('displays artifact types', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByText('quiz')).toBeInTheDocument()
      expect(screen.getByText('podcast')).toBeInTheDocument()
      expect(screen.getByText('summary')).toBeInTheDocument()
    })
  })

  describe('Accordion Behavior', () => {
    it('starts with no artifact expanded', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      // All cards should have isExpanded=false
      const quizCard = screen.getByTestId('artifact-card-artifact:quiz1')
      const podcastCard = screen.getByTestId('artifact-card-artifact:podcast1')
      const summaryCard = screen.getByTestId('artifact-card-artifact:summary1')

      expect(quizCard).toHaveAttribute('data-expanded', 'false')
      expect(podcastCard).toHaveAttribute('data-expanded', 'false')
      expect(summaryCard).toHaveAttribute('data-expanded', 'false')
    })

    it('expands artifact when clicked', async () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      const quizCard = screen.getByTestId('artifact-card-artifact:quiz1')
      fireEvent.click(quizCard)

      await waitFor(() => {
        expect(quizCard).toHaveAttribute('data-expanded', 'true')
      })
    })

    it('only one artifact can be expanded at a time', async () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      const quizCard = screen.getByTestId('artifact-card-artifact:quiz1')
      const podcastCard = screen.getByTestId('artifact-card-artifact:podcast1')

      // Expand quiz
      fireEvent.click(quizCard)
      await waitFor(() => {
        expect(quizCard).toHaveAttribute('data-expanded', 'true')
      })

      // Expand podcast - should collapse quiz
      fireEvent.click(podcastCard)
      await waitFor(() => {
        expect(podcastCard).toHaveAttribute('data-expanded', 'true')
        expect(quizCard).toHaveAttribute('data-expanded', 'false')
      })
    })

    it('collapses artifact when clicking the same one twice', async () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: mockArtifacts,
        isLoading: false,
        error: null,
      })

      renderComponent()

      const quizCard = screen.getByTestId('artifact-card-artifact:quiz1')

      // Expand
      fireEvent.click(quizCard)
      await waitFor(() => {
        expect(quizCard).toHaveAttribute('data-expanded', 'true')
      })

      // Collapse
      fireEvent.click(quizCard)
      await waitFor(() => {
        expect(quizCard).toHaveAttribute('data-expanded', 'false')
      })
    })
  })

  describe('Single Artifact', () => {
    it('handles single artifact in list', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: [mockArtifacts[0]],
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByTestId('artifact-card-artifact:quiz1')).toBeInTheDocument()
      expect(screen.queryByTestId('artifact-card-artifact:podcast1')).not.toBeInTheDocument()
    })
  })

  describe('Different Artifact Types', () => {
    it('renders transformation type artifacts', () => {
      mockUseNotebookArtifacts.mockReturnValue({
        data: [
          {
            id: 'artifact:transform1',
            artifact_type: 'transformation' as const,
            title: 'Code Analysis',
            created: '2024-01-18T10:00:00Z',
          },
        ],
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByTestId('artifact-card-artifact:transform1')).toBeInTheDocument()
      expect(screen.getByText('Code Analysis')).toBeInTheDocument()
      expect(screen.getByText('transformation')).toBeInTheDocument()
    })
  })
})
