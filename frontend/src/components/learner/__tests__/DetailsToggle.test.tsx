/**
 * Story 7.8: DetailsToggle Component Tests
 *
 * Tests toggle button behavior, styling, accessibility, and i18n.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DetailsToggle } from '../DetailsToggle'
import type { LearnerChatMessage } from '@/lib/api/learner-chat'

// Mock useTranslation hook
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        details: {
          show: 'Show message details',
          hide: 'Hide message details',
        },
      },
    },
    language: 'en-US',
    setLanguage: vi.fn(),
  }),
}))

describe('DetailsToggle', () => {
  const mockMessage: LearnerChatMessage = {
    role: 'assistant',
    content: 'Test message',
    toolCalls: [
      {
        id: 'call_1',
        toolName: 'surface_document',
        args: { source_id: 'doc_1' },
        result: { source_id: 'doc_1', title: 'Test Doc' },
      },
    ],
  }

  const mockOnToggle = vi.fn()

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders toggle button with correct icon when collapsed', () => {
    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={false}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button', { name: /show message details/i })
    expect(button).toBeInTheDocument()

    // ChevronDown icon should be present
    const chevronDown = button.querySelector('svg')
    expect(chevronDown).toBeInTheDocument()
  })

  it('renders toggle button with correct icon when expanded', () => {
    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={true}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button', { name: /hide message details/i })
    expect(button).toBeInTheDocument()

    // ChevronUp icon should be present
    const chevronUp = button.querySelector('svg')
    expect(chevronUp).toBeInTheDocument()
  })

  it('calls onToggle callback when clicked', async () => {
    const user = userEvent.setup()

    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={false}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button')
    await user.click(button)

    expect(mockOnToggle).toHaveBeenCalledTimes(1)
  })

  it('shows correct aria-label for accessibility (collapsed)', () => {
    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={false}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Show message details')
  })

  it('shows correct aria-label for accessibility (expanded)', () => {
    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={true}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Hide message details')
  })

  it('applies subtle styling (ghost variant, small size)', () => {
    render(
      <DetailsToggle
        message={mockMessage}
        isExpanded={false}
        onToggle={mockOnToggle}
      />
    )

    const button = screen.getByRole('button')

    // Check for subtle styling attributes and text styles
    // Shadcn/ui Button uses CSS classes for variants, check for text styling
    expect(button.className).toContain('text-xs')
    expect(button.className).toContain('text-muted-foreground')
    expect(button.className).toContain('h-8')
  })
})
