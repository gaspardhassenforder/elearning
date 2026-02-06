import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CollapsedPanelIndicator } from '../CollapsedPanelIndicator'
import { useLearnerStore } from '@/lib/stores/learner-store'

// Mock the learner store
vi.mock('@/lib/stores/learner-store', () => ({
  useLearnerStore: vi.fn(),
}))

// Mock useTranslation
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        panel: {
          collapsed: 'Show sources',
          newDocuments: '{count} new documents referenced',
        },
      },
    },
  }),
}))

describe('CollapsedPanelIndicator', () => {
  const mockClearBadgeCount = vi.fn()
  const mockGetState = vi.fn(() => ({
    clearBadgeCount: mockClearBadgeCount,
  }))

  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock for useLearnerStore
    ;(useLearnerStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: unknown) => {
      if (typeof selector === 'function') {
        return selector({ pendingBadgeCount: 0 })
      }
      return { pendingBadgeCount: 0 }
    })
    ;(useLearnerStore as unknown as { getState: typeof mockGetState }).getState = mockGetState
  })

  it('renders with FileText icon', () => {
    render(<CollapsedPanelIndicator onExpand={vi.fn()} />)
    // The button should be rendered
    const button = screen.getByRole('button', { name: /show sources/i })
    expect(button).toBeInTheDocument()
  })

  it('calls onExpand when clicked', () => {
    const onExpand = vi.fn()
    render(<CollapsedPanelIndicator onExpand={onExpand} />)

    const button = screen.getByRole('button', { name: /show sources/i })
    fireEvent.click(button)

    expect(onExpand).toHaveBeenCalledTimes(1)
  })

  it('clears badge count when clicked', () => {
    const onExpand = vi.fn()
    render(<CollapsedPanelIndicator onExpand={onExpand} />)

    const button = screen.getByRole('button', { name: /show sources/i })
    fireEvent.click(button)

    expect(mockClearBadgeCount).toHaveBeenCalledTimes(1)
  })

  it('does not show badge when pendingBadgeCount is 0', () => {
    render(<CollapsedPanelIndicator onExpand={vi.fn()} />)
    // Badge should not be visible
    expect(screen.queryByText(/\d+/)).not.toBeInTheDocument()
  })

  it('shows badge when pendingBadgeCount > 0', () => {
    ;(useLearnerStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: unknown) => {
      if (typeof selector === 'function') {
        return selector({ pendingBadgeCount: 3 })
      }
      return { pendingBadgeCount: 3 }
    })

    render(<CollapsedPanelIndicator onExpand={vi.fn()} />)
    // Badge should show count
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<CollapsedPanelIndicator onExpand={vi.fn()} className="custom-class" />)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('has correct accessibility label', () => {
    render(<CollapsedPanelIndicator onExpand={vi.fn()} />)
    const button = screen.getByRole('button', { name: /show sources/i })
    expect(button).toHaveAttribute('aria-label', 'Show sources')
  })
})
