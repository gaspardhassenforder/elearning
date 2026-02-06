import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DocumentCard } from '../DocumentCard'

// Mock useSourceContent hook
const mockRefetch = vi.fn()
vi.mock('@/lib/hooks/use-source-content', () => ({
  useSourceContent: vi.fn((sourceId: string | null) => {
    if (!sourceId) {
      return { data: null, isLoading: false, error: null, refetch: mockRefetch }
    }
    return {
      data: {
        id: sourceId,
        title: 'Test Document',
        content: 'This is the full document content for testing purposes.',
        file_type: 'application/pdf',
        word_count: 10,
        character_count: 55,
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    }
  }),
}))

// Mock useTranslation
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        sources: {
          untitled: 'Untitled Document',
          processing: 'Processing',
          error: 'Error',
          ready: 'Ready',
          expandDocument: 'Expand document',
          collapseDocument: 'Collapse document',
          loadingContent: 'Loading content...',
          contentError: 'Failed to load content',
          retry: 'Retry',
          words: 'words',
          noContent: 'No content available',
        },
      },
    },
  }),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

const mockSource = {
  id: 'source:123',
  title: 'Test Source',
  file_type: 'application/pdf',
  status: 'completed',
  embedded: true,
}

describe('DocumentCard - Expand/Collapse', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders collapsed state by default', () => {
    render(<DocumentCard source={mockSource} />, { wrapper: createWrapper() })

    expect(screen.getByText('Test Source')).toBeInTheDocument()
    expect(screen.getByText('application/pdf')).toBeInTheDocument()
    // Content should not be visible in collapsed state
    expect(screen.queryByText(/This is the full document content/)).not.toBeInTheDocument()
  })

  it('shows chevron down icon when collapsed', () => {
    const { container } = render(<DocumentCard source={mockSource} />, { wrapper: createWrapper() })

    // ChevronDown should be present (expanded has ChevronUp)
    const chevron = container.querySelector('svg')
    expect(chevron).toBeInTheDocument()
  })

  it('calls onToggleExpand when card is clicked', () => {
    const onToggleExpand = vi.fn()
    render(
      <DocumentCard source={mockSource} onToggleExpand={onToggleExpand} />,
      { wrapper: createWrapper() }
    )

    const card = screen.getByText('Test Source').closest('[class*="cursor-pointer"]')
    expect(card).toBeInTheDocument()
    fireEvent.click(card!)

    expect(onToggleExpand).toHaveBeenCalledTimes(1)
  })

  it('displays full content when expanded', async () => {
    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(screen.getByText('This is the full document content for testing purposes.')).toBeInTheDocument()
    })
  })

  it('shows word count when expanded and content loaded', async () => {
    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(screen.getByText('10 words')).toBeInTheDocument()
    })
  })

  it('shows file type in metadata when expanded', async () => {
    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      // File type should be shown in metadata section
      expect(screen.getByText('application/pdf')).toBeInTheDocument()
    })
  })

  it('applies expanded styling when isExpanded is true', () => {
    const { container } = render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    const card = container.querySelector('[class*="shadow-md"]')
    expect(card).toBeInTheDocument()
  })

  it('applies hover styling only when collapsed', () => {
    const { container, rerender } = render(
      <DocumentCard source={mockSource} isExpanded={false} />,
      { wrapper: createWrapper() }
    )

    const collapsedCard = container.querySelector('[class*="hover:bg-accent"]')
    expect(collapsedCard).toBeInTheDocument()

    rerender(<DocumentCard source={mockSource} isExpanded={true} />)
    const expandedCard = container.querySelector('[class*="hover:bg-accent"]')
    expect(expandedCard).not.toBeInTheDocument()
  })

  it('shows untitled when source has no title', () => {
    const untitledSource = { ...mockSource, title: null }
    render(<DocumentCard source={untitledSource} />, { wrapper: createWrapper() })

    expect(screen.getByText('Untitled Document')).toBeInTheDocument()
  })

  it('shows processing badge when status is processing', () => {
    const processingSource = { ...mockSource, status: 'processing' }
    render(<DocumentCard source={processingSource} />, { wrapper: createWrapper() })

    expect(screen.getByText('Processing')).toBeInTheDocument()
  })

  it('shows ready badge when source is embedded', () => {
    render(<DocumentCard source={mockSource} />, { wrapper: createWrapper() })

    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('applies highlight animation when isHighlighted is true', () => {
    const { container } = render(
      <DocumentCard source={mockSource} isHighlighted={true} />,
      { wrapper: createWrapper() }
    )

    const card = container.querySelector('[class*="ring-2"]')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('animate-pulse')
  })
})

describe('DocumentCard - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows error state when content fails to load', async () => {
    const { useSourceContent } = await import('@/lib/hooks/use-source-content')
    ;(useSourceContent as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
      refetch: mockRefetch,
    })

    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Failed to load content')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('calls refetch when retry button is clicked', async () => {
    const { useSourceContent } = await import('@/lib/hooks/use-source-content')
    ;(useSourceContent as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load'),
      refetch: mockRefetch,
    })

    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    const retryButton = screen.getByRole('button', { name: /retry/i })
    fireEvent.click(retryButton)

    expect(mockRefetch).toHaveBeenCalledTimes(1)
  })

  it('shows loading state when content is loading', async () => {
    const { useSourceContent } = await import('@/lib/hooks/use-source-content')
    ;(useSourceContent as ReturnType<typeof vi.fn>).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: mockRefetch,
    })

    render(
      <DocumentCard source={mockSource} isExpanded={true} />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Loading content...')).toBeInTheDocument()
  })
})
