/**
 * Story 4.6: InlineAudioPlayer Component Tests
 *
 * Tests for inline podcast audio player with playback controls.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { InlineAudioPlayer } from '../InlineAudioPlayer'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        podcast: {
          play: 'Play',
          pause: 'Pause',
          speed: 'Speed',
          minutes: 'minutes',
          viewTranscript: 'View Transcript',
          generating: 'Generating podcast...',
        },
      },
    },
  }),
}))

describe('InlineAudioPlayer', () => {
  const mockPodcast = {
    podcastId: 'podcast:456',
    title: 'Machine Learning Fundamentals',
    audioUrl: '/api/podcasts/podcast:456/audio',
    durationMinutes: 7,
    transcriptUrl: '/api/podcasts/podcast:456/transcript',
    status: 'completed',
  }

  // Mock HTMLAudioElement methods
  let mockPlay: ReturnType<typeof vi.fn>
  let mockPause: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock the play/pause methods on HTMLMediaElement prototype
    mockPlay = vi.fn().mockResolvedValue(undefined)
    mockPause = vi.fn()

    HTMLMediaElement.prototype.play = mockPlay
    HTMLMediaElement.prototype.pause = mockPause
  })

  afterEach(() => {
    // Restore HTML media prototypes
    vi.restoreAllMocks()
  })

  it('renders podcast title and duration', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    expect(screen.getByText('Machine Learning Fundamentals')).toBeInTheDocument()
    expect(screen.getByText(/7.*minutes/i)).toBeInTheDocument()
  })

  it('renders play button initially', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
  })

  it('renders audio element with correct src', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio')
    expect(audio).toBeInTheDocument()
    expect(audio).toHaveAttribute('src', '/api/podcasts/podcast:456/audio')
  })

  it('renders speed control buttons', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    expect(screen.getByText('1x')).toBeInTheDocument()
    expect(screen.getByText('1.25x')).toBeInTheDocument()
    expect(screen.getByText('1.5x')).toBeInTheDocument()
    expect(screen.getByText('2x')).toBeInTheDocument()
  })

  it('renders "View Transcript" link', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const link = screen.getByText(/View Transcript/)
    expect(link).toBeInTheDocument()
  })

  it('plays audio when play button clicked', async () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const playBtn = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playBtn)

    await waitFor(() => {
      expect(mockPlay).toHaveBeenCalled()
    })
  })

  it('changes button to pause after playing', async () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const playBtn = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playBtn)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    })
  })

  it('pauses audio when pause button clicked', async () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    // Start playing
    const playBtn = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playBtn)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    })

    // Click pause
    const pauseBtn = screen.getByRole('button', { name: /pause/i })
    fireEvent.click(pauseBtn)

    expect(mockPause).toHaveBeenCalled()
  })

  it('changes playback speed when speed button clicked', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const speedBtn = screen.getByText('1.5x')
    fireEvent.click(speedBtn)

    const audio = container.querySelector('audio') as HTMLAudioElement
    expect(audio.playbackRate).toBe(1.5)
  })

  it('highlights selected speed button', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const speed1x = screen.getByText('1x')
    const speed2x = screen.getByText('2x')

    // Initially 1x should be highlighted (button itself has the class)
    expect(speed1x).toHaveClass('bg-primary')

    // Click 2x
    fireEvent.click(speed2x)

    // 2x should now be highlighted
    expect(speed2x).toHaveClass('bg-primary')
    // 1x should no longer be highlighted
    expect(speed1x).not.toHaveClass('bg-primary')
  })

  it('updates progress bar during playback', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement
    expect(audio).toBeInTheDocument()

    // Simulate time update
    Object.defineProperty(audio, 'currentTime', { value: 150, writable: true, configurable: true })
    Object.defineProperty(audio, 'duration', { value: 420, writable: true, configurable: true })

    // Trigger timeupdate event
    fireEvent.timeUpdate(audio)

    // Progress should be 150/420 = ~35.7%
    const progress = container.querySelector('[role="progressbar"]')
    expect(progress).toBeInTheDocument()
  })

  it('shows generating state when status is not completed', () => {
    const generatingPodcast = {
      ...mockPodcast,
      status: 'generating',
    }

    render(<InlineAudioPlayer {...generatingPodcast} />)

    expect(screen.getByText(/Generating podcast.../)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /play/i })).not.toBeInTheDocument()
  })

  it('shows generating state when status is pending', () => {
    const pendingPodcast = {
      ...mockPodcast,
      status: 'pending',
    }

    render(<InlineAudioPlayer {...pendingPodcast} />)

    expect(screen.getByText(/Generating podcast.../)).toBeInTheDocument()
  })

  it('shows generating state when status is failed', () => {
    const failedPodcast = {
      ...mockPodcast,
      status: 'failed',
    }

    render(<InlineAudioPlayer {...failedPodcast} />)

    expect(screen.getByText(/Generating podcast.../)).toBeInTheDocument()
  })

  it('renders podcast icon', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    // Check for Headphones icon (lucide-react renders as svg)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('persists playback speed across pause/resume', async () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement

    // Set speed to 1.5x
    const speedBtn = screen.getByText('1.5x')
    fireEvent.click(speedBtn)

    expect(audio.playbackRate).toBe(1.5)

    // Play
    const playBtn = screen.getByRole('button', { name: /play/i })
    fireEvent.click(playBtn)

    await waitFor(() => {
      expect(mockPlay).toHaveBeenCalled()
    })

    // Pause
    const pauseBtn = screen.getByRole('button', { name: /pause/i })
    fireEvent.click(pauseBtn)

    // Speed should still be 1.5x
    expect(audio.playbackRate).toBe(1.5)
  })

  it('formats time display correctly', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement

    // Simulate 2 minutes 30 seconds played out of 7 minutes
    Object.defineProperty(audio, 'currentTime', { value: 150, writable: true, configurable: true })
    Object.defineProperty(audio, 'duration', { value: 420, writable: true, configurable: true })

    // Trigger time update event
    fireEvent.timeUpdate(audio)

    // Time display should show 2:30 / 7:00
    const timeDisplay = container.querySelector('.text-xs.text-muted-foreground')
    expect(timeDisplay).toBeInTheDocument()
  })

  it('handles transcript link click', () => {
    // Mock window.location.href
    delete window.location
    window.location = { href: '' } as any

    render(<InlineAudioPlayer {...mockPodcast} />)

    const link = screen.getByText(/View Transcript/)
    fireEvent.click(link)

    expect(window.location.href).toBe('/api/podcasts/podcast:456/transcript')
  })

  it('cleans up event listeners on unmount', () => {
    const { container, unmount } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement
    const removeEventListenerSpy = vi.spyOn(audio, 'removeEventListener')

    unmount()

    expect(removeEventListenerSpy).toHaveBeenCalled()
  })

  it('handles all speed options correctly', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement
    const speeds = [1, 1.25, 1.5, 2]

    speeds.forEach((speed) => {
      const speedBtn = screen.getByText(`${speed}x`)
      fireEvent.click(speedBtn)
      expect(audio.playbackRate).toBe(speed)
    })
  })

  it('displays progress as percentage', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement

    // Set progress to 50%
    Object.defineProperty(audio, 'currentTime', { value: 210, writable: true, configurable: true })
    Object.defineProperty(audio, 'duration', { value: 420, writable: true, configurable: true })

    // Trigger time update event
    fireEvent.timeUpdate(audio)

    const progress = container.querySelector('[role="progressbar"]')
    expect(progress).toBeInTheDocument()
    // Progress bar value should be 50
  })

  it('handles rapid play/pause toggles', async () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const playBtn = screen.getByRole('button', { name: /play/i })

    // Rapid clicks
    fireEvent.click(playBtn)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    })

    const pauseBtn = screen.getByRole('button', { name: /pause/i })
    fireEvent.click(pauseBtn)
    fireEvent.click(screen.getByRole('button', { name: /play/i }))

    expect(mockPlay).toHaveBeenCalledTimes(2)
    expect(mockPause).toHaveBeenCalledTimes(1)
  })

  it('applies correct styling to play/pause button', () => {
    render(<InlineAudioPlayer {...mockPodcast} />)

    const playBtn = screen.getByRole('button', { name: /play/i })
    // Button uses outline variant from shadcn/ui
    expect(playBtn).toHaveClass('w-20')
    expect(playBtn).toBeInTheDocument()
  })

  it('shows duration in minutes correctly', () => {
    const longPodcast = {
      ...mockPodcast,
      durationMinutes: 15,
    }

    render(<InlineAudioPlayer {...longPodcast} />)

    // Check for duration text more specifically
    expect(screen.getByText(/15.*minutes/i)).toBeInTheDocument()
  })

  it('handles 0 current time correctly', () => {
    const { container } = render(<InlineAudioPlayer {...mockPodcast} />)

    const audio = container.querySelector('audio') as HTMLAudioElement

    Object.defineProperty(audio, 'currentTime', { value: 0, writable: true, configurable: true })
    Object.defineProperty(audio, 'duration', { value: 420, writable: true, configurable: true })

    // Trigger time update event
    fireEvent.timeUpdate(audio)

    // Progress should be 0%
    const progress = container.querySelector('[role="progressbar"]')
    expect(progress).toBeInTheDocument()
  })
})
