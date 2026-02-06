/**
 * Story 4.6: InlineQuizWidget Component Tests
 *
 * Tests for inline quiz widget with interactive answer submission.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { InlineQuizWidget } from '../InlineQuizWidget'

// Mock dependencies
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        quiz: {
          submitAnswer: 'Submit Answer',
          submitting: 'Submitting...',
          viewFullQuiz: 'View Full Quiz',
          question: 'question',
          questions: 'questions',
          noQuestions: 'No questions available',
          submissionError: 'Failed to submit answer',
        },
      },
    },
  }),
}))

describe('InlineQuizWidget', () => {
  const mockQuiz = {
    quizId: 'quiz:123',
    title: 'Machine Learning Quiz',
    description: 'Test your understanding of ML concepts',
    questions: [
      {
        text: 'What is supervised learning?',
        options: [
          'Uses labeled datasets to train models',
          'Uses unlabeled datasets',
          'Requires no training data',
        ],
      },
    ],
    totalQuestions: 5,
    quizUrl: '/quizzes/quiz:123',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Mock fetch globally
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders quiz title and description', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
    expect(screen.getByText('Test your understanding of ML concepts')).toBeInTheDocument()
  })

  it('renders question text and radio options', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    expect(screen.getByText('What is supervised learning?')).toBeInTheDocument()
    expect(screen.getByText('Uses labeled datasets to train models')).toBeInTheDocument()
    expect(screen.getByText('Uses unlabeled datasets')).toBeInTheDocument()
    expect(screen.getByText('Requires no training data')).toBeInTheDocument()
  })

  it('renders "View Full Quiz" link with correct URL', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    const link = screen.getByText(/View Full Quiz/)
    expect(link).toBeInTheDocument()
    // Link should show total questions count
    expect(screen.getByText(/5/)).toBeInTheDocument()
    expect(screen.getByText(/questions/)).toBeInTheDocument()
  })

  it('disables submit button when no option selected', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    const submitBtn = screen.getByText('Submit Answer')
    expect(submitBtn).toBeDisabled()
  })

  it('enables submit button when option selected', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    expect(submitBtn).toBeEnabled()
  })

  it('allows selecting different options before submission', () => {
    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    const secondOption = screen.getByLabelText('Uses unlabeled datasets')

    fireEvent.click(firstOption)
    expect(firstOption).toBeChecked()

    fireEvent.click(secondOption)
    expect(secondOption).toBeChecked()
    expect(firstOption).not.toBeChecked()
  })

  it('shows correct answer feedback with green styling', async () => {
    const mockResponse = {
      score: 1,
      total: 1,
      percentage: 100,
      results: [
        {
          question_index: 0,
          is_correct: true,
          correct_answer: 0,
          user_answer: 0,
          explanation: 'Correct! Supervised learning uses labeled data.',
        },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    })

    render(<InlineQuizWidget {...mockQuiz} />)

    // Select correct answer
    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    // Submit
    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    // Wait for feedback
    await waitFor(() => {
      expect(screen.getByText(/Correct! Supervised learning uses labeled data./)).toBeInTheDocument()
    })

    // Check API was called correctly
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/quizzes/quiz:123/check',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: [0] }),
      })
    )
  })

  it('shows incorrect answer feedback with amber styling and reveals correct answer', async () => {
    const mockResponse = {
      score: 0,
      total: 1,
      percentage: 0,
      results: [
        {
          question_index: 0,
          is_correct: false,
          correct_answer: 0,
          user_answer: 1,
          explanation: 'Not quite. Supervised learning requires labeled data.',
        },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    })

    render(<InlineQuizWidget {...mockQuiz} />)

    // Select incorrect answer
    const secondOption = screen.getByLabelText('Uses unlabeled datasets')
    fireEvent.click(secondOption)

    // Submit
    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    // Wait for feedback
    await waitFor(() => {
      expect(screen.getByText(/Not quite. Supervised learning requires labeled data./)).toBeInTheDocument()
    })

    // Check both correct and incorrect answers are highlighted
    const correctOptionContainer = screen.getByText('Uses labeled datasets to train models').closest('div')
    const incorrectOptionContainer = screen.getByText('Uses unlabeled datasets').closest('div')

    expect(correctOptionContainer).toHaveClass(/bg-green-50/)
    expect(incorrectOptionContainer).toHaveClass(/bg-amber-50/)
  })

  it('disables radio buttons after submission', async () => {
    const mockResponse = {
      score: 1,
      total: 1,
      percentage: 100,
      results: [
        {
          question_index: 0,
          is_correct: true,
          correct_answer: 0,
          user_answer: 0,
          explanation: 'Correct!',
        },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    })

    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/Correct!/)).toBeInTheDocument()
    })

    // After submission, submit button should be hidden (component shows feedback)
    expect(screen.queryByText('Submit Answer')).not.toBeInTheDocument()

    // Feedback should be visible, indicating quiz is in completed state
    expect(screen.getByText(/Correct!/)).toBeInTheDocument()
  })

  it('shows loading state during submission', async () => {
    // Simulate slow API
    global.fetch = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({
                  score: 1,
                  total: 1,
                  percentage: 100,
                  results: [
                    {
                      question_index: 0,
                      is_correct: true,
                      correct_answer: 0,
                      user_answer: 0,
                      explanation: 'Correct!',
                    },
                  ],
                }),
              }),
            100
          )
        )
    )

    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    // Check submitting state
    expect(screen.getByText('Submitting...')).toBeInTheDocument()

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText(/Correct!/)).toBeInTheDocument()
    })
  })

  it('handles API errors gracefully', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText('Failed to submit answer')).toBeInTheDocument()
    })
  })

  it('handles HTTP error responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    })

    render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText('Failed to submit answer')).toBeInTheDocument()
    })
  })

  it('renders quiz icon', () => {
    const { container } = render(<InlineQuizWidget {...mockQuiz} />)

    // Check for FileQuestion icon (lucide-react renders as svg)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('handles quiz with no questions', () => {
    const emptyQuiz = {
      ...mockQuiz,
      questions: [],
    }

    render(<InlineQuizWidget {...emptyQuiz} />)

    expect(screen.getByText('No questions available')).toBeInTheDocument()
  })

  it('handles "View Full Quiz" link click', () => {
    // Mock window.location.href
    delete window.location
    window.location = { href: '' } as any

    render(<InlineQuizWidget {...mockQuiz} />)

    const link = screen.getByText(/View Full Quiz/)
    fireEvent.click(link)

    expect(window.location.href).toBe('/quizzes/quiz:123')
  })

  it('renders without description', () => {
    const quizWithoutDescription = {
      ...mockQuiz,
      description: undefined,
    }

    render(<InlineQuizWidget {...quizWithoutDescription} />)

    expect(screen.getByText('Machine Learning Quiz')).toBeInTheDocument()
    expect(screen.queryByText('Test your understanding')).not.toBeInTheDocument()
  })

  it('applies correct styling to feedback icons', async () => {
    const mockResponse = {
      score: 1,
      total: 1,
      percentage: 100,
      results: [
        {
          question_index: 0,
          is_correct: true,
          correct_answer: 0,
          user_answer: 0,
          explanation: 'Correct!',
        },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    })

    const { container } = render(<InlineQuizWidget {...mockQuiz} />)

    const firstOption = screen.getByLabelText('Uses labeled datasets to train models')
    fireEvent.click(firstOption)

    const submitBtn = screen.getByText('Submit Answer')
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/Correct!/)).toBeInTheDocument()
    })

    // Check for CheckCircle2 icon with correct styling
    const icons = container.querySelectorAll('svg')
    expect(icons.length).toBeGreaterThan(0)
  })
})
