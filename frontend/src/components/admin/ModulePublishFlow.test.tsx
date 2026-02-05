/**
 * Tests for ModulePublishFlow Component (Story 3.5, Code Review Fix MEDIUM-2)
 *
 * Covers validation logic to ensure frontend and backend validation stay in sync:
 * - Error display when source_count = 0
 * - Error display when objectives_count = 0
 * - Publish button disabled when validation fails
 * - Publish button enabled when validation passes
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ModulePublishFlow } from './ModulePublishFlow'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock hooks
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      common: { back: 'Back', continue: 'Continue', loading: 'Loading...' },
      modules: {
        publish: {
          summary: 'Module Summary',
          documents: 'Documents',
          objectives: 'Learning Objectives',
          artifacts: 'Artifacts',
          prompt: 'AI Prompt',
          required: 'Required',
          optional: 'Optional',
          readyToPublish: 'Ready to publish!',
          publishModule: 'Publish Module',
          success: 'Published successfully',
          successMessage: 'Module has been published',
          errorNoDocuments: 'At least 1 document is required',
          errorNoObjectives: 'At least 1 learning objective is required',
          fixErrorsHint: 'Fix the errors above before publishing',
        },
      },
    },
  }),
}))

vi.mock('@/lib/hooks/use-notebooks', () => ({
  useNotebook: vi.fn(),
  usePublishModule: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
}))

describe('ModulePublishFlow Validation Logic', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('shows error when source_count = 0', async () => {
    const { useNotebook } = await import('@/lib/hooks/use-notebooks')
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: 'notebook:1',
        name: 'Test',
        description: 'Test',
        archived: false,
        published: false,
        created: '2024-01-01',
        updated: '2024-01-01',
        source_count: 0, // Invalid
        note_count: 0,
        objectives_count: 1, // Valid
        has_prompt: false,
      },
      isLoading: false,
    } as any)

    render(<ModulePublishFlow notebookId="notebook:1" />, { wrapper })

    expect(screen.getByText('At least 1 document is required')).toBeInTheDocument()
  })

  it('shows error when objectives_count = 0', async () => {
    const { useNotebook } = await import('@/lib/hooks/use-notebooks')
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: 'notebook:1',
        name: 'Test',
        description: 'Test',
        archived: false,
        published: false,
        created: '2024-01-01',
        updated: '2024-01-01',
        source_count: 1, // Valid
        note_count: 0,
        objectives_count: 0, // Invalid
        has_prompt: false,
      },
      isLoading: false,
    } as any)

    render(<ModulePublishFlow notebookId="notebook:1" />, { wrapper })

    expect(screen.getByText('At least 1 learning objective is required')).toBeInTheDocument()
  })

  it('disables publish button when validation fails', async () => {
    const { useNotebook } = await import('@/lib/hooks/use-notebooks')
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: 'notebook:1',
        name: 'Test',
        description: 'Test',
        archived: false,
        published: false,
        created: '2024-01-01',
        updated: '2024-01-01',
        source_count: 0, // Invalid
        note_count: 0,
        objectives_count: 0, // Invalid
        has_prompt: false,
      },
      isLoading: false,
    } as any)

    render(<ModulePublishFlow notebookId="notebook:1" />, { wrapper })

    const publishButton = screen.getByRole('button', { name: 'Publish Module' })
    expect(publishButton).toBeDisabled()
  })

  it('enables publish button when validation passes', async () => {
    const { useNotebook } = await import('@/lib/hooks/use-notebooks')
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: 'notebook:1',
        name: 'Test',
        description: 'Test',
        archived: false,
        published: false,
        created: '2024-01-01',
        updated: '2024-01-01',
        source_count: 1, // Valid
        note_count: 0,
        objectives_count: 1, // Valid
        has_prompt: true,
      },
      isLoading: false,
    } as any)

    render(<ModulePublishFlow notebookId="notebook:1" />, { wrapper })

    const publishButton = screen.getByRole('button', { name: 'Publish Module' })
    expect(publishButton).not.toBeDisabled()
  })

  it('shows both errors when both validations fail', async () => {
    const { useNotebook } = await import('@/lib/hooks/use-notebooks')
    vi.mocked(useNotebook).mockReturnValue({
      data: {
        id: 'notebook:1',
        name: 'Test',
        description: 'Test',
        archived: false,
        published: false,
        created: '2024-01-01',
        updated: '2024-01-01',
        source_count: 0, // Invalid
        note_count: 0,
        objectives_count: 0, // Invalid
        has_prompt: false,
      },
      isLoading: false,
    } as any)

    render(<ModulePublishFlow notebookId="notebook:1" />, { wrapper })

    expect(screen.getByText('At least 1 document is required')).toBeInTheDocument()
    expect(screen.getByText('At least 1 learning objective is required')).toBeInTheDocument()
  })
})
