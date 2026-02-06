/**
 * Story 4.4: ObjectiveProgressList Component Tests
 *
 * Tests for learning objectives progress display in the Progress tab.
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ObjectiveProgressList } from '../ObjectiveProgressList'
import type { ObjectiveWithProgress } from '@/lib/types/api'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        progress: {
          title: 'Learning Objectives',
          complete: 'complete',
          completedAt: 'Completed on {date}',
          evidence: 'Evidence',
          loadError: 'Failed to load objectives',
          loadErrorDesc: 'Please try again later',
          noObjectives: 'No objectives yet',
          noObjectivesDesc: 'This module has no learning objectives defined',
          allComplete: 'All objectives completed! 🎓',
        },
      },
    },
  }),
}))

// Mock the progress hook
const mockUseLearnerObjectivesProgress = vi.fn()
vi.mock('@/lib/hooks/use-learning-objectives', () => ({
  useLearnerObjectivesProgress: () => mockUseLearnerObjectivesProgress(),
}))

// Mock TooltipProvider to avoid Radix DOM issues in tests
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div data-testid="tooltip-content">{children}</div>,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock ScrollArea
vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={className} data-testid="scroll-area">{children}</div>
  ),
}))

// Mock EmptyState
vi.mock('@/components/common/EmptyState', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) => (
    <div data-testid="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  ),
}))

// Mock LoadingSpinner
vi.mock('@/components/common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}))

// Mock Progress component
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, className }: { value: number; className?: string }) => (
    <div
      data-testid="progress-bar"
      data-value={value}
      className={className}
      role="progressbar"
      aria-valuenow={value}
    />
  ),
}))

describe('ObjectiveProgressList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders objectives with mixed completion states', () => {
    const objectives: ObjectiveWithProgress[] = [
      {
        id: 'lo:1',
        notebook_id: 'notebook:123',
        text: 'Understand supervised learning',
        order: 1,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T10:00:00Z',
        progress_evidence: 'Correctly explained labeled data concept',
      },
      {
        id: 'lo:2',
        notebook_id: 'notebook:123',
        text: 'Explain overfitting',
        order: 2,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T11:00:00Z',
        progress_evidence: 'Demonstrated understanding of bias-variance tradeoff',
      },
      {
        id: 'lo:3',
        notebook_id: 'notebook:123',
        text: 'Describe gradient descent',
        order: 3,
        auto_generated: false,
        progress_status: null,
        progress_completed_at: null,
        progress_evidence: null,
      },
    ]

    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives,
        completed_count: 2,
        total_count: 3,
      },
      isLoading: false,
      error: null,
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    // Check objectives are rendered
    expect(screen.getByText('Understand supervised learning')).toBeInTheDocument()
    expect(screen.getByText('Explain overfitting')).toBeInTheDocument()
    expect(screen.getByText('Describe gradient descent')).toBeInTheDocument()

    // Check count display
    expect(screen.getByText('2/3')).toBeInTheDocument()
  })

  it('calculates and displays completion percentage', () => {
    const objectives: ObjectiveWithProgress[] = [
      {
        id: 'lo:1',
        notebook_id: 'notebook:123',
        text: 'Objective 1',
        order: 1,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T10:00:00Z',
        progress_evidence: 'Evidence 1',
      },
      {
        id: 'lo:2',
        notebook_id: 'notebook:123',
        text: 'Objective 2',
        order: 2,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T11:00:00Z',
        progress_evidence: 'Evidence 2',
      },
      {
        id: 'lo:3',
        notebook_id: 'notebook:123',
        text: 'Objective 3',
        order: 3,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T12:00:00Z',
        progress_evidence: 'Evidence 3',
      },
      ...Array.from({ length: 5 }, (_, i) => ({
        id: `lo:${i + 4}`,
        notebook_id: 'notebook:123',
        text: `Objective ${i + 4}`,
        order: i + 4,
        auto_generated: false,
        progress_status: null,
        progress_completed_at: null,
        progress_evidence: null,
      })),
    ]

    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives,
        completed_count: 3,
        total_count: 8,
      },
      isLoading: false,
      error: null,
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    // Check percentage is displayed (3/8 = 37.5% rounded to 38%)
    expect(screen.getByText('38% complete')).toBeInTheDocument()

    // Check progress bar value
    const progressBar = screen.getByTestId('progress-bar')
    expect(progressBar).toHaveAttribute('data-value', '38')
  })

  it('shows empty state when no objectives', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives: [],
        completed_count: 0,
        total_count: 0,
      },
      isLoading: false,
      error: null,
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    // Check empty state is shown
    const emptyState = screen.getByTestId('empty-state')
    expect(emptyState).toBeInTheDocument()
    expect(screen.getByText('No objectives yet')).toBeInTheDocument()
  })

  it('shows complete state when all objectives done', () => {
    const objectives: ObjectiveWithProgress[] = [
      {
        id: 'lo:1',
        notebook_id: 'notebook:123',
        text: 'Objective 1',
        order: 1,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T10:00:00Z',
        progress_evidence: 'Evidence 1',
      },
      {
        id: 'lo:2',
        notebook_id: 'notebook:123',
        text: 'Objective 2',
        order: 2,
        auto_generated: false,
        progress_status: 'completed',
        progress_completed_at: '2024-01-15T11:00:00Z',
        progress_evidence: 'Evidence 2',
      },
    ]

    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: {
        objectives,
        completed_count: 2,
        total_count: 2,
      },
      isLoading: false,
      error: null,
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    // Check 100% completion
    expect(screen.getByText('100% complete')).toBeInTheDocument()

    // Check completion message is shown
    expect(screen.getByText('All objectives completed! 🎓')).toBeInTheDocument()
  })

  it('shows loading state while fetching data', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('shows error state when fetch fails', () => {
    mockUseLearnerObjectivesProgress.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Network error'),
    })

    render(<ObjectiveProgressList notebookId="notebook:123" />)

    expect(screen.getByText('Failed to load objectives')).toBeInTheDocument()
  })

  // Story 5.3: Warm Glow Animation Tests
  describe('Warm Glow Animation', () => {
    it('applies warm glow when objective_checked event fired', async () => {
      const objectives: ObjectiveWithProgress[] = [
        {
          id: 'learning_objective:abc123',
          notebook_id: 'notebook:123',
          text: 'Understand gradient descent',
          order: 1,
          auto_generated: false,
          progress_status: 'completed',
          progress_completed_at: '2024-01-15T10:00:00Z',
          progress_evidence: 'Demonstrated understanding',
        },
      ]

      mockUseLearnerObjectivesProgress.mockReturnValue({
        data: {
          objectives,
          completed_count: 1,
          total_count: 1,
        },
        isLoading: false,
        error: null,
      })

      const { container } = render(<ObjectiveProgressList notebookId="notebook:123" />)

      // Dispatch objective_checked event
      const event = new CustomEvent('objective_checked', {
        detail: { objective_id: 'learning_objective:abc123' }
      })
      window.dispatchEvent(event)

      // Wait for React to process state updates
      await vi.waitFor(() => {
        // Find the container div with the styling (parent of text)
        const textElement = screen.getByText('Understand gradient descent')
        const containerDiv = textElement.closest('.flex.items-start.gap-3')
        expect(containerDiv).toHaveClass('ring-2')
        expect(containerDiv).toHaveClass('ring-primary/50')
        expect(containerDiv).toHaveClass('animate-pulse')
      })
    })

    it('removes warm glow after 3 seconds', async () => {
      vi.useFakeTimers()

      const objectives: ObjectiveWithProgress[] = [
        {
          id: 'learning_objective:abc123',
          notebook_id: 'notebook:123',
          text: 'Understand gradient descent',
          order: 1,
          auto_generated: false,
          progress_status: 'completed',
          progress_completed_at: '2024-01-15T10:00:00Z',
          progress_evidence: 'Demonstrated understanding',
        },
      ]

      mockUseLearnerObjectivesProgress.mockReturnValue({
        data: {
          objectives,
          completed_count: 1,
          total_count: 1,
        },
        isLoading: false,
        error: null,
      })

      render(<ObjectiveProgressList notebookId="notebook:123" />)

      // Dispatch event
      window.dispatchEvent(new CustomEvent('objective_checked', {
        detail: { objective_id: 'learning_objective:abc123' }
      }))

      // Wait for glow to be applied
      await vi.waitFor(() => {
        const textElement = screen.getByText('Understand gradient descent')
        const containerDiv = textElement.closest('.flex.items-start.gap-3')
        expect(containerDiv).toHaveClass('ring-2')
      })

      // Fast-forward 3 seconds
      vi.advanceTimersByTime(3000)

      // Wait for React to process state updates and glow to be removed
      await vi.waitFor(() => {
        const textElement = screen.getByText('Understand gradient descent')
        const containerDiv = textElement.closest('.flex.items-start.gap-3')
        expect(containerDiv).not.toHaveClass('ring-2')
      })

      vi.useRealTimers()
    })

    it('supports multiple objectives glowing simultaneously', async () => {
      const objectives: ObjectiveWithProgress[] = [
        {
          id: 'learning_objective:obj1',
          notebook_id: 'notebook:123',
          text: 'Objective 1',
          order: 1,
          auto_generated: false,
          progress_status: 'completed',
          progress_completed_at: '2024-01-15T10:00:00Z',
          progress_evidence: 'Evidence 1',
        },
        {
          id: 'learning_objective:obj2',
          notebook_id: 'notebook:123',
          text: 'Objective 2',
          order: 2,
          auto_generated: false,
          progress_status: 'completed',
          progress_completed_at: '2024-01-15T11:00:00Z',
          progress_evidence: 'Evidence 2',
        },
      ]

      mockUseLearnerObjectivesProgress.mockReturnValue({
        data: {
          objectives,
          completed_count: 2,
          total_count: 2,
        },
        isLoading: false,
        error: null,
      })

      render(<ObjectiveProgressList notebookId="notebook:123" />)

      // Check off two objectives quickly
      window.dispatchEvent(new CustomEvent('objective_checked', {
        detail: { objective_id: 'learning_objective:obj1' }
      }))
      window.dispatchEvent(new CustomEvent('objective_checked', {
        detail: { objective_id: 'learning_objective:obj2' }
      }))

      // Wait for both glows to be applied
      await vi.waitFor(() => {
        const objective1 = screen.getByText('Objective 1').closest('.flex.items-start.gap-3')
        const objective2 = screen.getByText('Objective 2').closest('.flex.items-start.gap-3')
        expect(objective1).toHaveClass('ring-2')
        expect(objective2).toHaveClass('ring-2')
      })
    })

    it('does not glow objectives that were already completed', () => {
      const objectives: ObjectiveWithProgress[] = [
        {
          id: 'learning_objective:old',
          notebook_id: 'notebook:123',
          text: 'Already Completed Objective',
          order: 1,
          auto_generated: false,
          progress_status: 'completed',
          progress_completed_at: '2024-01-10T10:00:00Z',
          progress_evidence: 'Old evidence',
        },
      ]

      mockUseLearnerObjectivesProgress.mockReturnValue({
        data: {
          objectives,
          completed_count: 1,
          total_count: 1,
        },
        isLoading: false,
        error: null,
      })

      render(<ObjectiveProgressList notebookId="notebook:123" />)

      // Verify no glow on mount (only completed status styling)
      const completedObjective = screen.getByText('Already Completed Objective').closest('.flex.items-start.gap-3')
      expect(completedObjective).toHaveClass('bg-green-50')
      expect(completedObjective).not.toHaveClass('ring-2')
    })

    it('cleans up event listeners on unmount', () => {
      mockUseLearnerObjectivesProgress.mockReturnValue({
        data: {
          objectives: [],
          completed_count: 0,
          total_count: 0,
        },
        isLoading: false,
        error: null,
      })

      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
      const { unmount } = render(<ObjectiveProgressList notebookId="notebook:123" />)

      unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'objective_checked',
        expect.any(Function)
      )

      removeEventListenerSpy.mockRestore()
    })
  })
})
