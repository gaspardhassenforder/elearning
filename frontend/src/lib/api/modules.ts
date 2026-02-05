/**
 * API client for module/notebook operations (Story 3.1)
 */

import { apiClient } from './client';

export interface Module {
  id: string;
  name: string;
  description: string;
  archived: boolean;
  published: boolean;
  created: string;
  updated: string;
  source_count: number;
  note_count: number;
}

export interface ModuleCreate {
  name: string;
  description: string;
}

export interface ModuleUpdate {
  name?: string;
  description?: string;
  archived?: boolean;
}

export interface DocumentUpload {
  id: string;
  title: string;
  status: string;
  command_id?: string;
}

export interface DocumentStatus {
  id: string;
  title: string;
  status: string;
  command_id?: string;
  error_message?: string;
  created?: string;
  updated?: string;
}

/**
 * Modules API client
 */
export const modulesApi = {
  /**
   * Get all modules (notebooks)
   */
  async list(): Promise<Module[]> {
    const response = await apiClient.get<Module[]>('/notebooks');
    return response.data;
  },

  /**
   * Get a single module by ID
   */
  async get(id: string): Promise<Module> {
    const response = await apiClient.get<Module>(`/notebooks/${id}`);
    return response.data;
  },

  /**
   * Create a new module
   */
  async create(data: ModuleCreate): Promise<Module> {
    const response = await apiClient.post<Module>('/notebooks', data);
    return response.data;
  },

  /**
   * Update an existing module
   */
  async update(id: string, data: ModuleUpdate): Promise<Module> {
    const response = await apiClient.put<Module>(`/notebooks/${id}`, data);
    return response.data;
  },

  /**
   * Delete a module
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/notebooks/${id}`);
  },

  /**
   * Upload a document to a module
   */
  async uploadDocument(moduleId: string, file: File): Promise<DocumentUpload> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentUpload>(
      `/notebooks/${moduleId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * List documents in a module with their processing status
   */
  async listDocuments(moduleId: string): Promise<DocumentStatus[]> {
    const response = await apiClient.get<DocumentStatus[]>(
      `/notebooks/${moduleId}/documents`
    );
    return response.data;
  },
};
