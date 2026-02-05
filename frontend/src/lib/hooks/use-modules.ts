/**
 * TanStack Query hooks for module operations (Story 3.1)
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { modulesApi, Module, ModuleCreate, ModuleUpdate, DocumentStatus } from '@/lib/api/modules';
import { toast } from 'sonner';
import { useTranslation } from './use-translation';

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
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (data: ModuleCreate) => modulesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success(t.modules.moduleCreated);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.loadError);
    },
  });
}

/**
 * Hook to update a module
 */
export function useUpdateModule(id: string) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (data: ModuleUpdate) => modulesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success(t.modules.moduleUpdated);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.loadError);
    },
  });
}

/**
 * Hook to delete a module
 */
export function useDeleteModule() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (id: string) => modulesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success(t.modules.moduleDeleted);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.loadError);
    },
  });
}

/**
 * Hook to upload a document to a module
 */
export function useUploadDocument(moduleId: string) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (file: File) => modulesApi.uploadDocument(moduleId, file),
    onSuccess: () => {
      // Invalidate documents list to show new upload
      queryClient.invalidateQueries({ queryKey: moduleKeys.documents(moduleId) });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.uploadFailed);
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

/**
 * Hook to unpublish a module (Story 3.6, Task 6)
 * Allows admin to edit a published module by reverting it to draft status
 */
export function useUnpublishModule() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (id: string) => modulesApi.unpublish(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.lists() });
      toast.success(t.modules.moduleUnpublished);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.unpublishError);
    },
  });
}

/**
 * Hook to remove a document from a module (Story 3.6, Task 8)
 * Deletes the source relationship in edit mode
 */
export function useRemoveDocument(moduleId: string) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useMutation({
    mutationFn: (sourceId: string) => modulesApi.removeDocument(moduleId, sourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: moduleKeys.documents(moduleId) });
      queryClient.invalidateQueries({ queryKey: moduleKeys.detail(moduleId) });
      toast.success(t.modules.documentRemoved);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t.modules.removeDocumentError);
    },
  });
}
