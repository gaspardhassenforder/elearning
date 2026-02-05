/**
 * Story 4.3: DocumentSnippetCard Component Tests
 *
 * Tests for inline document snippet cards in chat.
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DocumentSnippetCard } from '../DocumentSnippetCard'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        openInSources: 'Open in sources',
        documentSnippet: 'Document Snippet',
        referencedDocument: 'Referenced Document',
      },
    },
  }),
}))

vi.mock('@/lib/stores/learner-store', () => ({
  useLearnerStore: vi.fn(),
}))

describe('DocumentSnippetCard', () => {
  const mockExpandAndScrollToSource = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    const { useLearnerStore } = require('@/lib/stores/learner-store')
    useLearnerStore.mockReturnValue(mockExpandAndScrollToSource)
  })

  it('renders title, excerpt, and link correctly', () => {
    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Machine Learning Fundamentals"
        excerpt="Supervised learning uses labeled data to train models."
        sourceType="pdf"
      />
    )

    expect(screen.getByText('Machine Learning Fundamentals')).toBeInTheDocument()
    expect(screen.getByText(/Supervised learning uses labeled data/)).toBeInTheDocument()
    expect(screen.getByText(/Open in sources/)).toBeInTheDocument()
  })

  it('truncates excerpts longer than 200 characters', () => {
    const longExcerpt = 'A'.repeat(250)
    const expectedTruncated = 'A'.repeat(197) + '...'

    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Long Document"
        excerpt={longExcerpt}
      />
    )

    const excerptElement = screen.getByText(expectedTruncated)
    expect(excerptElement).toBeInTheDocument()
    expect(excerptElement.textContent?.length).toBeLessThanOrEqual(200)
  })

  it('does not truncate excerpts of exactly 200 characters', () => {
    const exactExcerpt = 'B'.repeat(200)

    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Exact Length Document"
        excerpt={exactExcerpt}
      />
    )

    expect(screen.getByText(exactExcerpt)).toBeInTheDocument()
  })

  it('calls expandAndScrollToSource when clicking the card', () => {
    render(
      <DocumentSnippetCard
        sourceId="source:456"
        title="Clickable Document"
        excerpt="Click me!"
      />
    )

    const card = screen.getByText('Clickable Document').closest('.p-3')
    expect(card).toBeInTheDocument()

    if (card) {
      fireEvent.click(card)
      expect(mockExpandAndScrollToSource).toHaveBeenCalledWith('source:456')
      expect(mockExpandAndScrollToSource).toHaveBeenCalledTimes(1)
    }
  })

  it('calls expandAndScrollToSource when clicking the link button', () => {
    render(
      <DocumentSnippetCard
        sourceId="source:789"
        title="Link Test"
        excerpt="Test excerpt"
      />
    )

    const link = screen.getByText(/Open in sources/)
    fireEvent.click(link)

    expect(mockExpandAndScrollToSource).toHaveBeenCalledWith('source:789')
    expect(mockExpandAndScrollToSource).toHaveBeenCalledTimes(1)
  })

  it('displays document icon', () => {
    const { container } = render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Icon Test"
        excerpt="Test excerpt"
      />
    )

    // Check for FileText icon (lucide-react renders as svg)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('applies hover styles', () => {
    const { container } = render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Hover Test"
        excerpt="Test excerpt"
      />
    )

    const card = container.querySelector('.hover\\:shadow-md')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('cursor-pointer')
  })

  it('renders with optional relevance reason', () => {
    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Relevant Document"
        excerpt="Important content"
        relevance="Explains the core concept you asked about"
      />
    )

    // Component doesn't display relevance in UI (it's metadata for context)
    // Just verify it doesn't crash
    expect(screen.getByText('Relevant Document')).toBeInTheDocument()
  })

  it('handles short excerpts without truncation', () => {
    const shortExcerpt = 'Short text'

    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Short Document"
        excerpt={shortExcerpt}
      />
    )

    expect(screen.getByText(shortExcerpt)).toBeInTheDocument()
    expect(screen.getByText(shortExcerpt).textContent).toBe(shortExcerpt)
  })

  it('prevents default event when clicking link', () => {
    render(
      <DocumentSnippetCard
        sourceId="source:123"
        title="Event Test"
        excerpt="Test excerpt"
      />
    )

    const link = screen.getByText(/Open in sources/)
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true })
    const preventDefaultSpy = vi.spyOn(clickEvent, 'preventDefault')

    link.dispatchEvent(clickEvent)

    expect(preventDefaultSpy).toHaveBeenCalled()
  })
})
