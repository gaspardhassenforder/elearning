/**
 * Tests for Story 4.5: ModuleSuggestionCard Component
 *
 * Tests module suggestion rendering and navigation on completion.
 */

import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ModuleSuggestionCard } from '../ModuleSuggestionCard'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock useTranslation
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        chat: {
          startModule: 'Start Module',
        },
      },
    },
  }),
}))

describe('ModuleSuggestionCard', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('renders module title and description', () => {
    render(
      <ModuleSuggestionCard
        moduleId="notebook:module1"
        title="Advanced Machine Learning"
        description="Deep learning, neural networks, and transformers"
      />
    )

    // Verify title rendered
    expect(screen.getByText('Advanced Machine Learning')).toBeInTheDocument()

    // Verify description rendered
    expect(screen.getByText('Deep learning, neural networks, and transformers')).toBeInTheDocument()

    // Verify button rendered
    expect(screen.getByText('Start Module')).toBeInTheDocument()
  })

  it('renders without description', () => {
    render(
      <ModuleSuggestionCard
        moduleId="notebook:module2"
        title="MLOps Fundamentals"
      />
    )

    // Verify title rendered
    expect(screen.getByText('MLOps Fundamentals')).toBeInTheDocument()

    // Verify no description text (description is optional)
    expect(screen.queryByText(/production/i)).not.toBeInTheDocument()
  })

  it('navigates to module on "Start" button click', () => {
    render(
      <ModuleSuggestionCard
        moduleId="notebook:test123"
        title="Test Module"
        description="Test description"
      />
    )

    // Click the "Start Module" button
    const startButton = screen.getByText('Start Module')
    fireEvent.click(startButton)

    // Verify navigation was called with correct path
    expect(mockPush).toHaveBeenCalledWith('/modules/notebook:test123')
  })

  it('renders multiple suggestions in list', () => {
    const { container } = render(
      <div className="space-y-2">
        <ModuleSuggestionCard
          moduleId="notebook:module1"
          title="Module 1"
          description="First module"
        />
        <ModuleSuggestionCard
          moduleId="notebook:module2"
          title="Module 2"
          description="Second module"
        />
        <ModuleSuggestionCard
          moduleId="notebook:module3"
          title="Module 3"
          description="Third module"
        />
      </div>
    )

    // Verify all three modules rendered
    expect(screen.getByText('Module 1')).toBeInTheDocument()
    expect(screen.getByText('Module 2')).toBeInTheDocument()
    expect(screen.getByText('Module 3')).toBeInTheDocument()

    // Verify all descriptions rendered
    expect(screen.getByText('First module')).toBeInTheDocument()
    expect(screen.getByText('Second module')).toBeInTheDocument()
    expect(screen.getByText('Third module')).toBeInTheDocument()

    // Verify three "Start Module" buttons
    const startButtons = screen.getAllByText('Start Module')
    expect(startButtons).toHaveLength(3)
  })

  it('applies gradient styling for visual appeal', () => {
    const { container } = render(
      <ModuleSuggestionCard
        moduleId="notebook:styled"
        title="Styled Module"
        description="Visual test"
      />
    )

    // Check that gradient classes are applied (via className check)
    const card = container.querySelector('.bg-gradient-to-r')
    expect(card).toBeInTheDocument()
  })
})
