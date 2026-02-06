import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LearnerErrorBoundary, LearnerErrorBoundaryWithRouter } from '../LearnerErrorBoundary'

// Component that throws on render
function ThrowingComponent({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test render error')
  }
  return <div data-testid="child-content">Working content</div>
}

// Suppress console.error for expected error boundary catches
const originalConsoleError = console.error
beforeEach(() => {
  console.error = vi.fn()
})

afterEach(() => {
  console.error = originalConsoleError
})

describe('LearnerErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    render(
      <LearnerErrorBoundary>
        <div data-testid="child">Hello</div>
      </LearnerErrorBoundary>
    )

    expect(screen.getByTestId('child')).toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders fallback UI when child component throws', () => {
    render(
      <LearnerErrorBoundary>
        <ThrowingComponent />
      </LearnerErrorBoundary>
    )

    // Should show the friendly error message
    expect(screen.getByText('Something unexpected happened')).toBeInTheDocument()
    expect(screen.getByText("Don't worry, your progress is saved.")).toBeInTheDocument()
  })

  it('uses amber color scheme in fallback UI (never red)', () => {
    const { container } = render(
      <LearnerErrorBoundary>
        <ThrowingComponent />
      </LearnerErrorBoundary>
    )

    // Check amber classes are used on the card border
    const card = container.querySelector('.border-amber-200')
    expect(card).toBeInTheDocument()

    // Check amber icon container
    const iconContainer = container.querySelector('.bg-amber-100')
    expect(iconContainer).toBeInTheDocument()

    // Check amber text on title
    const title = container.querySelector('.text-amber-900')
    expect(title).toBeInTheDocument()

    // Ensure no red classes are present
    const html = container.innerHTML
    expect(html).not.toMatch(/text-red-|bg-red-|border-red-/)
  })

  it('provides retry and return to modules options', async () => {
    const user = userEvent.setup()
    const onReturnToModules = vi.fn()

    render(
      <LearnerErrorBoundary onReturnToModules={onReturnToModules}>
        <ThrowingComponent />
      </LearnerErrorBoundary>
    )

    // Find buttons
    const tryAgainButton = screen.getByText('Try Again')
    const returnButton = screen.getByText('Return to Modules')
    expect(tryAgainButton).toBeInTheDocument()
    expect(returnButton).toBeInTheDocument()

    // Click return to modules
    await user.click(returnButton)
    expect(onReturnToModules).toHaveBeenCalled()
  })

  it('resets error state when retry button is clicked', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()

    render(
      <LearnerErrorBoundary onRetry={onRetry}>
        <ThrowingComponent />
      </LearnerErrorBoundary>
    )

    // Should be in error state
    expect(screen.getByText('Something unexpected happened')).toBeInTheDocument()

    // Click try again - resets error state
    await user.click(screen.getByText('Try Again'))
    expect(onRetry).toHaveBeenCalled()
  })

  it('hides error details in non-development environments', () => {
    // In vitest, NODE_ENV is 'test' (not 'development')
    // The component only shows <details> when NODE_ENV === 'development'
    const { container } = render(
      <LearnerErrorBoundary>
        <ThrowingComponent />
      </LearnerErrorBoundary>
    )

    // Error details should NOT be shown in test/production environments
    const details = container.querySelector('details')
    expect(details).not.toBeInTheDocument()

    // But the fallback UI should still be visible without technical info
    expect(screen.getByText('Something unexpected happened')).toBeInTheDocument()
    expect(screen.queryByText('Test render error')).not.toBeInTheDocument()
  })
})

describe('LearnerErrorBoundaryWithRouter', () => {
  it('renders children when no error occurs', () => {
    render(
      <LearnerErrorBoundaryWithRouter>
        <div data-testid="child">Working</div>
      </LearnerErrorBoundaryWithRouter>
    )

    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})
