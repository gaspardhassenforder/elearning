/**
 * Story 4.7: AsyncStatusBar Component Tests
 *
 * Tests for async artifact generation status bar with fixed viewport positioning.
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { AsyncStatusBar } from '../AsyncStatusBar'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      asyncStatus: {
        generatingArtifact: 'Generating {type}...',
        artifactReady: '{type} ready!',
        artifactReadyDescription: 'You can find it in the Artifacts panel',
        artifactFailed: 'Failed to generate {type}',
        autoDismiss: 'Auto-dismiss in 5s',
        dismiss: 'Dismiss',
      },
    },
  }),
}))

vi.mock('@/lib/utils', () => ({
  cn: (...classes: any[]) => classes.filter(Boolean).join(' '),
}))

describe('AsyncStatusBar', () => {
  const mockProps = {
    jobId: 'command:test123',
    artifactType: 'podcast',
    onComplete: vi.fn(),
    onError: vi.fn(),
    onDismiss: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('Status Rendering', () => {
    it('renders processing status with spinner', () => {
      render(<AsyncStatusBar {...mockProps} status="processing" />)

      expect(screen.getByText(/Generating podcast/i)).toBeInTheDocument()
      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
      expect(screen.getByRole('status')).toHaveAttribute('aria-atomic', 'true')
    })

    it('renders completed status with checkmark', () => {
      render(<AsyncStatusBar {...mockProps} status="completed" />)

      expect(screen.getByText(/podcast ready/i)).toBeInTheDocument()
      expect(screen.getByText(/Auto-dismiss in 5s/i)).toBeInTheDocument()
    })

    it('renders error status with dismiss button', () => {
      render(
        <AsyncStatusBar
          {...mockProps}
          status="error"
          errorMessage="TTS service failed: timeout"
        />
      )

      expect(screen.getByText(/Failed to generate podcast/i)).toBeInTheDocument()
      expect(screen.getByText(/TTS service failed: timeout/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
    })

    it('renders pending status with spinner', () => {
      render(<AsyncStatusBar {...mockProps} status="pending" />)

      expect(screen.getByText(/Generating podcast/i)).toBeInTheDocument()
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('Progress Bar', () => {
    it('shows progress bar if progress data available', () => {
      render(
        <AsyncStatusBar
          {...mockProps}
          status="processing"
          progress={{ current: 40, total: 100, percentage: 40 }}
        />
      )

      expect(screen.getByText('40%')).toBeInTheDocument()
    })

    it('calculates percentage from current/total', () => {
      render(
        <AsyncStatusBar
          {...mockProps}
          status="processing"
          progress={{ current: 75, total: 100 }}
        />
      )

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('does not show progress bar if no progress data', () => {
      const { container } = render(<AsyncStatusBar {...mockProps} status="processing" />)

      // Progress bar should not be present
      expect(container.querySelector('[role="progressbar"]')).not.toBeInTheDocument()
    })

    it('does not show progress bar for completed status', () => {
      const { container } = render(
        <AsyncStatusBar
          {...mockProps}
          status="completed"
          progress={{ percentage: 100 }}
        />
      )

      // Progress bar should not be present for completed status
      expect(container.querySelector('[role="progressbar"]')).not.toBeInTheDocument()
    })
  })

  describe('Auto-Dismiss Behavior', () => {
    it('auto-dismisses after 5 seconds on completion', () => {
      render(<AsyncStatusBar {...mockProps} status="completed" />)

      expect(mockProps.onDismiss).not.toHaveBeenCalled()

      // Fast-forward time by 4.9 seconds (just before dismiss)
      act(() => {
        vi.advanceTimersByTime(4900)
      })

      // Should not have been called yet
      expect(mockProps.onDismiss).not.toHaveBeenCalled()

      // Fast-forward past 5 seconds
      act(() => {
        vi.advanceTimersByTime(200)
      })

      // Now should be called
      expect(mockProps.onDismiss).toHaveBeenCalledTimes(1)
    })

    it('does not auto-dismiss on error', () => {
      render(<AsyncStatusBar {...mockProps} status="error" />)

      // Fast-forward time
      act(() => {
        vi.advanceTimersByTime(10000)
      })

      expect(mockProps.onDismiss).not.toHaveBeenCalled()
    })

    it('does not auto-dismiss on processing', () => {
      render(<AsyncStatusBar {...mockProps} status="processing" />)

      act(() => {
        vi.advanceTimersByTime(10000)
      })

      expect(mockProps.onDismiss).not.toHaveBeenCalled()
    })

    it('clears timer when status changes before auto-dismiss', () => {
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="completed" />)

      // Fast-forward 2 seconds (before 5s auto-dismiss)
      act(() => {
        vi.advanceTimersByTime(2000)
      })

      // Change status to error (should cancel auto-dismiss)
      rerender(<AsyncStatusBar {...mockProps} status="error" />)

      // Fast-forward another 5 seconds
      act(() => {
        vi.advanceTimersByTime(5000)
      })

      // onDismiss should not have been called (timer was cleared)
      expect(mockProps.onDismiss).not.toHaveBeenCalled()
    })
  })

  describe('Manual Dismiss', () => {
    it('dismisses when dismiss button clicked (error status)', () => {
      render(<AsyncStatusBar {...mockProps} status="error" />)

      const dismissButton = screen.getByRole('button', { name: /dismiss/i })
      fireEvent.click(dismissButton)

      expect(mockProps.onDismiss).toHaveBeenCalledTimes(1)
    })

    it('hides status bar after dismiss', () => {
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="error" />)

      const dismissButton = screen.getByRole('button', { name: /dismiss/i })
      fireEvent.click(dismissButton)

      // Simulate parent clearing the activeJob (which would unmount the component)
      rerender(<></>)

      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
  })

  describe('Callback Invocation', () => {
    it('calls onComplete callback when status becomes completed', () => {
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="processing" />)

      expect(mockProps.onComplete).not.toHaveBeenCalled()

      rerender(<AsyncStatusBar {...mockProps} status="completed" />)

      expect(mockProps.onComplete).toHaveBeenCalledTimes(1)
    })

    it('calls onError callback when status becomes error', () => {
      const errorMessage = 'TTS service failed'
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="processing" />)

      expect(mockProps.onError).not.toHaveBeenCalled()

      rerender(
        <AsyncStatusBar {...mockProps} status="error" errorMessage={errorMessage} />
      )

      expect(mockProps.onError).toHaveBeenCalledTimes(1)
      expect(mockProps.onError).toHaveBeenCalledWith(errorMessage)
    })

    it('does not call callbacks multiple times for same status', () => {
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="completed" />)

      expect(mockProps.onComplete).toHaveBeenCalledTimes(1)

      // Re-render with same status
      rerender(<AsyncStatusBar {...mockProps} status="completed" />)

      // Callback should not be called again
      expect(mockProps.onComplete).toHaveBeenCalledTimes(1)
    })
  })

  describe('Artifact Type Support', () => {
    it('renders podcast artifact type correctly', () => {
      render(<AsyncStatusBar {...mockProps} artifactType="podcast" status="processing" />)

      expect(screen.getByText(/Generating podcast/i)).toBeInTheDocument()
    })

    it('renders quiz artifact type correctly', () => {
      render(<AsyncStatusBar {...mockProps} artifactType="quiz" status="processing" />)

      expect(screen.getByText(/Generating quiz/i)).toBeInTheDocument()
    })

    it('renders custom artifact type correctly', () => {
      render(
        <AsyncStatusBar {...mockProps} artifactType="summary" status="completed" />
      )

      expect(screen.getByText(/summary ready/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has correct ARIA attributes for screen readers', () => {
      render(<AsyncStatusBar {...mockProps} status="processing" />)

      const statusBar = screen.getByRole('status')
      expect(statusBar).toHaveAttribute('aria-live', 'polite')
      expect(statusBar).toHaveAttribute('aria-atomic', 'true')
    })

    it('dismiss button has accessible label', () => {
      render(<AsyncStatusBar {...mockProps} status="error" />)

      const dismissButton = screen.getByRole('button', { name: /dismiss/i })
      expect(dismissButton).toHaveAttribute('aria-label')
    })
  })

  describe('Fixed Viewport Positioning', () => {
    it('has fixed bottom positioning CSS classes', () => {
      const { container } = render(<AsyncStatusBar {...mockProps} status="processing" />)

      const statusBar = container.firstChild as HTMLElement
      expect(statusBar.className).toContain('fixed')
      expect(statusBar.className).toContain('bottom-0')
      expect(statusBar.className).toContain('z-50')
    })
  })

  describe('Visual States', () => {
    it('applies correct color scheme for processing', () => {
      const { container } = render(<AsyncStatusBar {...mockProps} status="processing" />)

      const statusBar = container.firstChild as HTMLElement
      // Should have blue colors
      expect(statusBar.className).toContain('blue')
    })

    it('applies correct color scheme for completed', () => {
      const { container } = render(<AsyncStatusBar {...mockProps} status="completed" />)

      const statusBar = container.firstChild as HTMLElement
      // Should have green colors
      expect(statusBar.className).toContain('green')
    })

    it('applies correct color scheme for error', () => {
      const { container } = render(<AsyncStatusBar {...mockProps} status="error" />)

      const statusBar = container.firstChild as HTMLElement
      // Should have amber colors (warm, not red - per UX spec)
      expect(statusBar.className).toContain('amber')
    })
  })

  describe('Edge Cases', () => {
    it('handles undefined error message gracefully', () => {
      render(<AsyncStatusBar {...mockProps} status="error" errorMessage={undefined} />)

      expect(screen.getByText(/Failed to generate podcast/i)).toBeInTheDocument()
      // Should not crash, error message just not displayed
    })

    it('handles missing progress percentage gracefully', () => {
      const { container } = render(
        <AsyncStatusBar {...mockProps} status="processing" progress={{}} />
      )

      // Should render without progress bar
      expect(container.querySelector('[role="progressbar"]')).not.toBeInTheDocument()
    })

    it('handles rapid status changes', () => {
      const { rerender } = render(<AsyncStatusBar {...mockProps} status="pending" />)

      rerender(<AsyncStatusBar {...mockProps} status="processing" />)
      rerender(<AsyncStatusBar {...mockProps} status="completed" />)

      expect(mockProps.onComplete).toHaveBeenCalledTimes(1)
    })
  })
})
