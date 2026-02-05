import { apiClient } from './client'
import { LearnerModule } from '@/lib/types/api'

export const learnerModulesApi = {
  /**
   * Get all modules visible to the authenticated learner
   * (assigned to learner's company, unlocked only)
   */
  list: async (): Promise<LearnerModule[]> => {
    const response = await apiClient.get('/learner/modules')
    return response.data
  },

  /**
   * Validate learner access to a specific module
   * (for direct URL navigation protection)
   */
  get: async (notebookId: string): Promise<LearnerModule> => {
    const response = await apiClient.get(`/learner/modules/${notebookId}`)
    return response.data
  },
}
