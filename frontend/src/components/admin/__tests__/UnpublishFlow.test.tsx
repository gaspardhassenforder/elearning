/**
 * Frontend tests for Story 3.6 Task 12: Edit button and unpublish flow
 *
 * Tests:
 * - Edit button only visible for published modules
 * - Unpublish confirmation dialog
 * - Unpublish mutation and navigation to edit mode
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UnpublishConfirmDialog } from '../UnpublishConfirmDialog';
import * as useModulesHooks from '@/lib/hooks/use-modules';
import * as moduleCreationStore from '@/lib/stores/module-creation-store';

// Mock the hooks
vi.mock('@/lib/hooks/use-modules', () => ({
  useUnpublishModule: vi.fn(),
}));

vi.mock('@/lib/stores/module-creation-store', () => ({
  useModuleCreationStore: vi.fn(),
}));

vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      modules: {
        unpublishConfirmTitle: 'Unpublish Module?',
        unpublishConfirmDescription: 'This will temporarily hide the module from learners.',
        unpublishLearnerImpactWarning: 'Active learners will lose access until you re-publish.',
      },
      common: {
        cancel: 'Cancel',
        unpublish: 'Unpublish',
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

describe('UnpublishConfirmDialog', () => {
  let queryClient: QueryClient;
  let mockUnpublishMutate: ReturnType<typeof vi.fn>;
  let mockEnterEditMode: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    queryClient = createQueryClient();
    mockUnpublishMutate = vi.fn();
    mockEnterEditMode = vi.fn();

    // Mock useUnpublishModule to return mutation functions
    vi.mocked(useModulesHooks.useUnpublishModule).mockReturnValue({
      mutateAsync: mockUnpublishMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: null,
    } as any);

    // Mock useModuleCreationStore
    vi.mocked(moduleCreationStore.useModuleCreationStore).mockReturnValue({
      enterEditMode: mockEnterEditMode,
      isEditMode: false,
      editingModuleId: null,
      activeStep: 'upload',
      setActiveStep: vi.fn(),
      exitEditMode: vi.fn(),
      reset: vi.fn(),
    } as any);
  });

  it('renders dialog when open', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UnpublishConfirmDialog
          open={true}
          onOpenChange={vi.fn()}
          moduleId="module123"
          moduleName="Test Module"
        />
      </QueryClientProvider>
    );

    expect(screen.getByText('Unpublish Module?')).toBeInTheDocument();
    expect(screen.getByText('This will temporarily hide the module from learners.')).toBeInTheDocument();
    expect(screen.getByText('Active learners will lose access until you re-publish.')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <UnpublishConfirmDialog
          open={false}
          onOpenChange={vi.fn()}
          moduleId="module123"
          moduleName="Test Module"
        />
      </QueryClientProvider>
    );

    expect(screen.queryByText('Unpublish Module?')).not.toBeInTheDocument();
  });

  it('calls unpublish mutation on confirm', async () => {
    mockUnpublishMutate.mockResolvedValueOnce({});

    const onOpenChange = vi.fn();

    render(
      <QueryClientProvider client={queryClient}>
        <UnpublishConfirmDialog
          open={true}
          onOpenChange={onOpenChange}
          moduleId="module123"
          moduleName="Test Module"
        />
      </QueryClientProvider>
    );

    const unpublishButton = screen.getByRole('button', { name: /unpublish/i });
    fireEvent.click(unpublishButton);

    await waitFor(() => {
      expect(mockUnpublishMutate).toHaveBeenCalledWith('module123');
    });

    await waitFor(() => {
      expect(mockEnterEditMode).toHaveBeenCalledWith('module123');
    });

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('closes dialog on cancel', () => {
    const onOpenChange = vi.fn();

    render(
      <QueryClientProvider client={queryClient}>
        <UnpublishConfirmDialog
          open={true}
          onOpenChange={onOpenChange}
          moduleId="module123"
          moduleName="Test Module"
        />
      </QueryClientProvider>
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(mockUnpublishMutate).not.toHaveBeenCalled();
  });

  it('does not call enterEditMode if unpublish fails', async () => {
    mockUnpublishMutate.mockRejectedValueOnce(new Error('Network error'));

    render(
      <QueryClientProvider client={queryClient}>
        <UnpublishConfirmDialog
          open={true}
          onOpenChange={vi.fn()}
          moduleId="module123"
          moduleName="Test Module"
        />
      </QueryClientProvider>
    );

    const unpublishButton = screen.getByRole('button', { name: /unpublish/i });
    fireEvent.click(unpublishButton);

    await waitFor(() => {
      expect(mockUnpublishMutate).toHaveBeenCalledWith('module123');
    });

    // Should not enter edit mode if unpublish failed
    expect(mockEnterEditMode).not.toHaveBeenCalled();
  });
});
