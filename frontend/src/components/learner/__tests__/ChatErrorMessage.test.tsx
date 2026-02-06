import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatErrorMessage, parseSSEErrorEvent } from '../ChatErrorMessage'

describe('ChatErrorMessage', () => {
  it('renders error message with amber styling', () => {
    const { container } = render(
      <ChatErrorMessage message="I had trouble processing that." />
    )

    // Message should be visible
    expect(screen.getByText('I had trouble processing that.')).toBeInTheDocument()

    // Should use amber classes (never red)
    const alertDiv = container.querySelector('[role="alert"]')
    expect(alertDiv).toBeInTheDocument()
    expect(alertDiv?.className).toContain('bg-amber-50')
    expect(alertDiv?.className).toContain('border-amber-200')

    // No red classes
    expect(container.innerHTML).not.toMatch(/text-red-|bg-red-|border-red-/)
  })

  it('shows retry button for recoverable errors', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()

    render(
      <ChatErrorMessage
        message="Connection lost"
        recoverable={true}
        onRetry={onRetry}
      />
    )

    const retryButton = screen.getByText('Try Again')
    expect(retryButton).toBeInTheDocument()

    await user.click(retryButton)
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('hides retry button for non-recoverable errors', () => {
    render(
      <ChatErrorMessage
        message="Something went wrong"
        recoverable={false}
        onRetry={vi.fn()}
      />
    )

    expect(screen.queryByText('Try Again')).not.toBeInTheDocument()
  })

  it('has correct ARIA attributes for accessibility', () => {
    const { container } = render(
      <ChatErrorMessage message="Error occurred" />
    )

    const alertDiv = container.querySelector('[role="alert"]')
    expect(alertDiv).toBeInTheDocument()
    expect(alertDiv?.getAttribute('aria-live')).toBe('polite')
  })
})

describe('parseSSEErrorEvent', () => {
  it('returns message from event and recoverability status', () => {
    const event = {
      message: 'I had trouble with that.',
      error_type: 'service_error',
      recoverable: true,
    }

    const result = parseSSEErrorEvent(event, {
      learnerErrors: { chatError: 'Fallback error' },
    })

    expect(result.message).toBe('I had trouble with that.')
    expect(result.recoverable).toBe(true)
  })

  it('falls back to error field when message is missing', () => {
    const event = {
      error: 'Tool failed',
      error_type: 'not_found',
      recoverable: false,
    }

    const result = parseSSEErrorEvent(event, {})

    expect(result.message).toBe('Tool failed')
    expect(result.recoverable).toBe(false)
  })

  it('falls back to generic message when both message and error are missing', () => {
    const event = {
      error_type: 'unknown',
    }

    const result = parseSSEErrorEvent(event, {
      learnerErrors: { chatError: 'I had trouble processing that.' },
    })

    expect(result.message).toBe('I had trouble processing that.')
    expect(result.recoverable).toBe(false)
  })
})
