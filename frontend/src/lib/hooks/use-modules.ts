/**
 * TanStack Query hooks for module operations (Story 3.1)
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { modulesApi, Module, ModuleCreate, ModuleUpdate, DocumentStatus } from '@/lib/api/modules';
import { toast } from 'sonner';

/**
 * Query keys for modules
 */
export const moduleKeys = {
  all: ['modules'] as const,
  lists: () => [...moduleKeys.all, 'list'] as const,
  list: (filters?: any) => [...moduleKeys.lists(), filters] as const,
  details: () => [...moduleKeys.all, 'detail'] as const,
  detail: (id: string) => [...moduleKeys.details(), id] as const,
  documents: (id: string) => [...moduleKeys.detail(id), 'documents'] as const,
};

/**
 * Hook to fetch all modules
 */
export function useModules() {
  return useQuery({
    queryKey: moduleKeys.lists(),
    queryFn: () => modulesApi.list(),
  });
}

/**
 * Hook to fetch a single module
 */
export function useModule(id: string) {
  return useQuery({
    queryKey: moduleKeys.detail(id),
    queryFn: () => modulesApi.get(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a module
 */
export function useCreateModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ModuleCreate) => modulesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success('Module created successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create module');
    },
  });
}

/**
 * Hook to update a module
 */
export function useUpdateModule(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ModuleUpdate) => modulesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success('Module updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update module');
    },
  });
}

/**
 * Hook to delete a module
 */
export function useDeleteModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => modulesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success('Module deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete module');
    },
  });
}

/**
 * Hook to upload a document to a module
 */
export function useUploadDocument(moduleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => modulesApi.uploadDocument(moduleId, file),
    onSuccess: () => {
      // Invalidate documents list to show new upload
      queryClient.invalidateQueries({ queryKey: moduleKeys.documents(moduleId) });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to upload document');
    },
  });
}

/**
 * Hook to list documents in a module with polling for processing status
 */
export function useModuleDocuments(moduleId: string, options?: { pollingInterval?: number }) {
  return useQuery({
    queryKey: moduleKeys.documents(moduleId),
    queryFn: () => modulesApi.listDocuments(moduleId),
    enabled: !!moduleId,
    // Poll every 2 seconds if any document is processing
    refetchInterval: (data) => {
      const hasProcessing = data?.some((doc: DocumentStatus) => doc.status === 'processing');
      return hasProcessing ? (options?.pollingInterval ?? 2000) : false;
    },
  });
}
