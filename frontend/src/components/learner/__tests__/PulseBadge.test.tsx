import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { PulseBadge } from '../PulseBadge'

describe('PulseBadge', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns null when count is 0', () => {
    const { container } = render(<PulseBadge count={0} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when count is negative', () => {
    const { container } = render(<PulseBadge count={-1} />)
    expect(container.firstChild).toBeNull()
  })

  it('displays count when positive', () => {
    render(<PulseBadge count={3} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('displays 99+ when count exceeds 99', () => {
    render(<PulseBadge count={100} />)
    expect(screen.getByText('99+')).toBeInTheDocument()
  })

  it('applies pulse animation when count increases', () => {
    const { rerender } = render(<PulseBadge count={1} />)
    const badge = screen.getByText('1')

    // Initially no pulse (since it's the first render)
    expect(badge).not.toHaveClass('animate-pulse')

    // Increase count
    rerender(<PulseBadge count={2} />)

    // Should have pulse animation
    expect(screen.getByText('2')).toHaveClass('animate-pulse')
  })

  it('stops pulsing after timeout', () => {
    const { rerender } = render(<PulseBadge count={1} />)

    // Increase count to trigger pulse
    rerender(<PulseBadge count={2} />)
    const badge = screen.getByText('2')
    expect(badge).toHaveClass('animate-pulse')

    // Advance time past pulse duration (2100ms)
    act(() => {
      vi.advanceTimersByTime(2100)
    })

    // Should no longer have pulse animation
    expect(badge).not.toHaveClass('animate-pulse')
  })

  it('applies custom className', () => {
    render(<PulseBadge count={5} className="custom-class" />)
    const badge = screen.getByText('5')
    expect(badge).toHaveClass('custom-class')
  })

  it('has success color styling', () => {
    render(<PulseBadge count={1} />)
    const badge = screen.getByText('1')
    expect(badge).toHaveClass('bg-emerald-500')
  })
})
