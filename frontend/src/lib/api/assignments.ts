import { apiClient } from './client'
import {
  AssignmentMatrixResponse,
  AssignmentToggleResponse,
  ModuleAssignmentResponse,
} from '@/lib/types/api'

export const assignmentsApi = {
  /**
   * Get all module assignments
   */
  list: async (): Promise<ModuleAssignmentResponse[]> => {
    const response = await apiClient.get('/module-assignments')
    return response.data
  },

  /**
   * Get assignment matrix for admin UI
   */
  getMatrix: async (): Promise<AssignmentMatrixResponse> => {
    const response = await apiClient.get('/module-assignments/matrix')
    return response.data
  },

  /**
   * Assign a module to a company
   */
  assign: async (
    companyId: string,
    notebookId: string
  ): Promise<ModuleAssignmentResponse> => {
    const response = await apiClient.post('/module-assignments', {
      company_id: companyId,
      notebook_id: notebookId,
    })
    return response.data
  },

  /**
   * Unassign a module from a company
   */
  unassign: async (companyId: string, notebookId: string): Promise<void> => {
    await apiClient.delete(
      `/module-assignments/company/${companyId}/notebook/${notebookId}`
    )
  },

  /**
   * Toggle assignment (create if not exists, delete if exists)
   */
  toggle: async (
    companyId: string,
    notebookId: string
  ): Promise<AssignmentToggleResponse> => {
    const response = await apiClient.post('/module-assignments/toggle', {
      company_id: companyId,
      notebook_id: notebookId,
    })
    return response.data
  },

  /**
   * Toggle lock status on a module assignment (admin only)
   */
  toggleLock: async (
    companyId: string,
    notebookId: string,
    isLocked: boolean
  ): Promise<ModuleAssignmentResponse> => {
    const response = await apiClient.put(
      `/module-assignments/company/${companyId}/notebook/${notebookId}/lock`,
      { is_locked: isLocked }
    )
    return response.data
  },
}
