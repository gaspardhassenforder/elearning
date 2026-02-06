/**
 * Learning Objectives API Client (Story 3.3, Task 5)
 *
 * API functions for CRUD operations on learning objectives with drag-and-drop reordering.
 */

import { apiClient } from './client'
import type {
  LearningObjectiveResponse,
  CreateLearningObjectiveRequest,
  UpdateLearningObjectiveRequest,
  ReorderLearningObjectivesRequest,
  BatchGenerationResponse,
  LearnerObjectivesProgressResponse,
} from '@/lib/types/api'

/**
 * List all learning objectives for a notebook (ordered by order field)
 */
export async function listLearningObjectives(
  notebookId: string
): Promise<LearningObjectiveResponse[]> {
  const response = await apiClient.get<LearningObjectiveResponse[]>(
    `/api/notebooks/${notebookId}/learning-objectives`
  )
  return response.data
}

/**
 * Auto-generate learning objectives from notebook content
 * Triggers LangGraph workflow to analyze sources and generate 3-5 objectives
 */
export async function generateLearningObjectives(
  notebookId: string
): Promise<BatchGenerationResponse> {
  const response = await apiClient.post<BatchGenerationResponse>(
    `/api/notebooks/${notebookId}/learning-objectives/generate`
  )
  return response.data
}

/**
 * Create a manual learning objective
 */
export async function createLearningObjective(
  notebookId: string,
  data: CreateLearningObjectiveRequest
): Promise<LearningObjectiveResponse> {
  const response = await apiClient.post<LearningObjectiveResponse>(
    `/api/notebooks/${notebookId}/learning-objectives`,
    data
  )
  return response.data
}

/**
 * Update learning objective text
 */
export async function updateLearningObjective(
  notebookId: string,
  objectiveId: string,
  data: UpdateLearningObjectiveRequest
): Promise<LearningObjectiveResponse> {
  const response = await apiClient.put<LearningObjectiveResponse>(
    `/api/notebooks/${notebookId}/learning-objectives/${objectiveId}`,
    data
  )
  return response.data
}

/**
 * Delete a learning objective
 */
export async function deleteLearningObjective(
  notebookId: string,
  objectiveId: string
): Promise<void> {
  await apiClient.delete(
    `/api/notebooks/${notebookId}/learning-objectives/${objectiveId}`
  )
}

/**
 * Reorder learning objectives (bulk update)
 * Used after drag-and-drop to update order field for all affected objectives
 */
export async function reorderLearningObjectives(
  notebookId: string,
  data: ReorderLearningObjectivesRequest
): Promise<void> {
  await apiClient.post(
    `/api/notebooks/${notebookId}/learning-objectives/reorder`,
    data
  )
}

/**
 * Get learning objectives with learner progress (Story 4.4)
 * Returns objectives with completion status for the authenticated learner
 */
export async function getLearnerObjectivesProgress(
  notebookId: string
): Promise<LearnerObjectivesProgressResponse> {
  const response = await apiClient.get<LearnerObjectivesProgressResponse>(
    `/api/notebooks/${notebookId}/learning-objectives/progress`
  )
  return response.data
}
