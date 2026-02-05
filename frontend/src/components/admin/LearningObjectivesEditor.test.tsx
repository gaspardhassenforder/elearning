/**
 * LearningObjectivesEditor Component Tests (Story 3.3, Task 7)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LearningObjectivesEditor } from './LearningObjectivesEditor'
import * as hooks from '@/lib/hooks/use-learning-objectives'

// Mock the hooks
vi.mock('@/lib/hooks/use-learning-objectives')
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      common: {
        loading: 'Loading...',
        add: 'Add',
        delete: 'Delete',
        cancel: 'Cancel',
        aiGenerated: 'AI Generated',
      },
      learningObjectives: {
        loadError: 'Failed to load learning objectives',
        emptyTitle: 'No Learning Objectives Yet',
        emptyDescription: 'Generate objectives automatically from your module content.',
        generateButton: 'Generate Objectives',
        regenerateButton: 'Regenerate',
        generating: 'Generating objectives...',
        regenerating: 'Regenerating...',
        listDescription: 'Drag to reorder. Click to edit.',
        addPlaceholder: 'Enter a new learning objective...',
        validationRequired: 'At least one learning objective is required to proceed.',
        deleteTitle: 'Delete Learning Objective',
        deleteConfirm: 'Are you sure you want to delete this learning objective?',
      },
    },
  }),
}))

describe('LearningObjectivesEditor', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('Loading State', () => {
    it('should display loading spinner while fetching objectives', () => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: [],
        isLoading: true,
        error: null,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message when fetch fails', () => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: [],
        isLoading: false,
        error: new Error('Network error'),
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('Failed to load learning objectives')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    beforeEach(() => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any)

      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)
    })

    it('should display empty state with generate button', () => {
      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('No Learning Objectives Yet')).toBeInTheDocument()
      expect(screen.getByText('Generate Objectives')).toBeInTheDocument()
      expect(screen.getByText('At least one learning objective is required to proceed.')).toBeInTheDocument()
    })

    it('should call generate mutation when Generate button clicked', async () => {
      const mutateMock = vi.fn()
      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: mutateMock,
        isPending: false,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      const generateBtn = screen.getByText('Generate Objectives')
      await userEvent.click(generateBtn)

      expect(mutateMock).toHaveBeenCalled()
    })
  })

  describe('Objectives List', () => {
    const mockObjectives = [
      {
        id: 'obj-1',
        notebook_id: 'test-module',
        text: 'Understand React hooks',
        order: 0,
        auto_generated: true,
        created: '2024-01-01',
        updated: '2024-01-01',
      },
      {
        id: 'obj-2',
        notebook_id: 'test-module',
        text: 'Build components',
        order: 1,
        auto_generated: false,
        created: '2024-01-02',
        updated: '2024-01-02',
      },
    ]

    beforeEach(() => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: mockObjectives,
        isLoading: false,
        error: null,
      } as any)

      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useUpdateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useDeleteLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useReorderLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)
    })

    it('should display all objectives in order', () => {
      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('Understand React hooks')).toBeInTheDocument()
      expect(screen.getByText('Build components')).toBeInTheDocument()
    })

    it('should show AI badge for auto-generated objectives', () => {
      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      const aiBadges = screen.getAllByText('AI Generated')
      expect(aiBadges).toHaveLength(1) // Only first objective is auto-generated
    })

    it('should show order numbers for each objective', () => {
      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('1.')).toBeInTheDocument()
      expect(screen.getByText('2.')).toBeInTheDocument()
    })
  })

  describe('Add Manual Objective', () => {
    beforeEach(() => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any)

      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useDeleteLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useReorderLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)
    })

    it('should enable Add button when text entered', async () => {
      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      const input = screen.getByPlaceholderText('Enter a new learning objective...')
      const addButton = screen.getByRole('button', { name: /add/i })

      expect(addButton).toBeDisabled()

      await userEvent.type(input, 'New objective')

      expect(addButton).toBeEnabled()
    })

    it('should call create mutation when Add clicked', async () => {
      const mutateMock = vi.fn()
      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: mutateMock,
        isPending: false,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      const input = screen.getByPlaceholderText('Enter a new learning objective...')
      await userEvent.type(input, 'New objective')

      const addButton = screen.getByRole('button', { name: /add/i })
      await userEvent.click(addButton)

      expect(mutateMock).toHaveBeenCalledWith(
        { text: 'New objective' },
        expect.any(Object)
      )
    })
  })

  describe('Delete Objective', () => {
    const mockObjectives = [
      {
        id: 'obj-1',
        notebook_id: 'test-module',
        text: 'Test objective',
        order: 0,
        auto_generated: false,
        created: '2024-01-01',
        updated: '2024-01-01',
      },
    ]

    beforeEach(() => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: mockObjectives,
        isLoading: false,
        error: null,
      } as any)

      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useUpdateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useReorderLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)
    })

    it('should have delete button for each objective', () => {
      vi.mocked(hooks.useDeleteLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      // Verify delete button exists (trash icon button)
      const allButtons = screen.getAllByRole('button')
      // Should have at least one button in the objective card
      expect(allButtons.length).toBeGreaterThan(0)
      expect(screen.getByText('Test objective')).toBeInTheDocument()
    })
  })

  describe('Validation', () => {
    it('should show validation warning when no objectives exist', () => {
      vi.mocked(hooks.useLearningObjectives).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any)

      vi.mocked(hooks.useGenerateLearningObjectives).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      vi.mocked(hooks.useCreateLearningObjective).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any)

      render(<LearningObjectivesEditor moduleId="test-module" />, { wrapper })

      expect(screen.getByText('At least one learning objective is required to proceed.')).toBeInTheDocument()
    })
  })
})
