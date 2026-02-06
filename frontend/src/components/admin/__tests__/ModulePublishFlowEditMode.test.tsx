/**
 * Frontend tests for Story 3.6 Task 12: ModulePublishFlow in edit mode
 *
 * Tests:
 * - Shows "Publish Changes" button in edit mode vs "Publish Module" in create mode
 * - Shows different success message in edit mode
 * - Validation still applies in edit mode
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ModulePublishFlow } from '../ModulePublishFlow';
import * as useNotebooksHooks from '@/lib/hooks/use-notebooks';

// Mock the hooks
vi.mock('@/lib/hooks/use-notebooks', () => ({
  useNotebook: vi.fn(),
  usePublishModule: vi.fn(),
}));

vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      modules: {
        publish: {
          summary: 'Module Summary',
          documents: 'Documents',
          objectives: 'Learning Objectives',
          required: 'Required',
          readyToPublish: 'Ready to publish!',
          publishModule: 'Publish Module',
          publishChanges: 'Publish Changes',
          successMessage: 'Module has been published and is now visible to learners.',
          successMessageEdit: 'Module updated and published',
          errorNoDocuments: 'At least 1 document is required',
          errorNoObjectives: 'At least 1 learning objective is required',
          fixErrorsHint: 'Fix the errors above before publishing',
        },
      },
      common: {
        back: 'Back',
        continue: 'Continue',
      },
    },
  }),
}));

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

describe('ModulePublishFlow - Edit Mode', () => {
  let queryClient: QueryClient;
  let mockPublishMutate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    queryClient = createQueryClient();
    mockPublishMutate = vi.fn();

    vi.mocked(useNotebooksHooks.usePublishModule).mockReturnValue({
      mutateAsync: mockPublishMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: null,
    } as any);
  });

  it('shows "Publish Module" button in create mode', () => {
    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 2,
        objectives_count: 3,
        note_count: 1,
        has_prompt: true,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={false}
          onSuccess={vi.fn()}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    expect(screen.getByRole('button', { name: /publish module/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /publish changes/i })).not.toBeInTheDocument();
  });

  it('shows "Publish Changes" button in edit mode', () => {
    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 2,
        objectives_count: 3,
        note_count: 1,
        has_prompt: true,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={true}
          onSuccess={vi.fn()}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    expect(screen.getByRole('button', { name: /publish changes/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^publish module$/i })).not.toBeInTheDocument();
  });

  it('shows standard success message in create mode', async () => {
    mockPublishMutate.mockResolvedValueOnce({});

    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 2,
        objectives_count: 3,
        note_count: 1,
        has_prompt: true,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={false}
          onSuccess={vi.fn()}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    const publishButton = screen.getByRole('button', { name: /publish module/i });
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(screen.getByText(/module has been published and is now visible to learners/i)).toBeInTheDocument();
    });
  });

  it('shows edit success message in edit mode', async () => {
    mockPublishMutate.mockResolvedValueOnce({});

    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 2,
        objectives_count: 3,
        note_count: 1,
        has_prompt: true,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={true}
          onSuccess={vi.fn()}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    const publishButton = screen.getByRole('button', { name: /publish changes/i });
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(screen.getByText(/module updated and published/i)).toBeInTheDocument();
    });
  });

  it('validates module in edit mode same as create mode', () => {
    // Module with insufficient sources
    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 0,  // No sources
        objectives_count: 3,
        note_count: 0,
        has_prompt: false,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={true}
          onSuccess={vi.fn()}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    // Button should be disabled due to validation
    const publishButton = screen.getByRole('button', { name: /publish changes/i });
    expect(publishButton).toBeDisabled();

    // Should show error message
    expect(screen.getByText(/at least 1 document is required/i)).toBeInTheDocument();
  });

  it('calls onSuccess callback after successful publish in edit mode', async () => {
    mockPublishMutate.mockResolvedValueOnce({});
    const onSuccess = vi.fn();

    vi.mocked(useNotebooksHooks.useNotebook).mockReturnValue({
      data: {
        id: 'module123',
        name: 'Test Module',
        published: false,
        source_count: 2,
        objectives_count: 3,
        note_count: 1,
        has_prompt: true,
      },
      isLoading: false,
      error: null,
    } as any);

    render(
      <QueryClientProvider client={queryClient}>
        <ModulePublishFlow
          notebookId="module123"
          isEditMode={true}
          onSuccess={onSuccess}
          onBack={vi.fn()}
        />
      </QueryClientProvider>
    );

    const publishButton = screen.getByRole('button', { name: /publish changes/i });
    fireEvent.click(publishButton);

    await waitFor(() => {
      expect(screen.getByText(/module updated and published/i)).toBeInTheDocument();
    });

    // Click Continue button to trigger onSuccess
    const continueButton = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(continueButton);

    expect(onSuccess).toHaveBeenCalled();
  });
});
