/**
 * Story 4.4: AmbientProgressBar Component Tests
 *
 * Tests for the thin 3px progress bar displayed below the header.
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AmbientProgressBar } from '../AmbientProgressBar'

// Mock the progress hook
const mockUseLearnerObjectivesProgress = vi.fn()
vi.mock('@/lib/hooks/use-learning-objectives', () => ({
  useLearnerObjectivesProgress: () => mockUseLearnerObjectivesProgress(),
}))

// Mock Progress component with style introspection
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, className, style }: { value: number; className?: string; style?: React.CSSProperties }) => (
    <div
      data-testid="progress-bar"
      data-value={value}
      className={className}
      style={style}
      role="progressbar"
      aria-valuenow={value}
    >
      <div data-testid="progress-indicator" style={{ width: `${value}%` }} />
    </div>
  ),
}))

describe('AmbientProgressBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with correct percentage fill', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 3,
        total_count: 8,
      },
      isLoading: false,
    })

    const { container } = render(<AmbientProgressBar notebookId="notebook:123" />)

    // Progress bar should be present
    const progressBar = screen.getByTestId('progress-bar')
    expect(progressBar).toBeInTheDocument()

    // Value should be 37% (3/8 = 0.375 rounded to 38%)
    expect(progressBar).toHaveAttribute('data-value', '38')

    // Check the h-[3px] class for thin height
    expect(progressBar.className).toContain('h-[3px]')
  })

  it('applies smooth transition style for animations', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 5,
        total_count: 10,
      },
      isLoading: false,
    })

    render(<AmbientProgressBar notebookId="notebook:123" />)

    const progressBar = screen.getByTestId('progress-bar')

    // Check transition style is applied (150ms ease)
    expect(progressBar.style.transition).toBe('width 150ms ease')
  })

  it('hides when no objectives exist', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 0,
        total_count: 0,
      },
      isLoading: false,
    })

    const { container } = render(<AmbientProgressBar notebookId="notebook:123" />)

    // Should return null when total_count is 0
    expect(container.firstChild).toBeNull()
  })

  it('hides when loading', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: null,
      isLoading: true,
    })

    const { container } = render(<AmbientProgressBar notebookId="notebook:123" />)

    // Should return null when loading
    expect(container.firstChild).toBeNull()
  })

  it('hides when no data available', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: null,
      isLoading: false,
    })

    const { container } = render(<AmbientProgressBar notebookId="notebook:123" />)

    // Should return null when no data
    expect(container.firstChild).toBeNull()
  })

  it('applies success color when complete', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 5,
        total_count: 5,
      },
      isLoading: false,
    })

    render(<AmbientProgressBar notebookId="notebook:123" />)

    const progressBar = screen.getByTestId('progress-bar')

    // Check for success color class when complete
    expect(progressBar.className).toContain('bg-green-500')
  })

  it('applies custom className when provided', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 2,
        total_count: 4,
      },
      isLoading: false,
    })

    const { container } = render(
      <AmbientProgressBar notebookId="notebook:123" className="custom-class" />
    )

    // The wrapper div should have the custom class
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.className).toContain('custom-class')
  })
})
