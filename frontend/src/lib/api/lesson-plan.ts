/**
 * Lesson Plan API Client
 *
 * API functions for lesson step management (admin) and learner progress tracking.
 */

import { apiClient } from './client'

export interface LessonStepResponse {
  id: string
  notebook_id: string
  title: string
  step_type: 'watch' | 'read' | 'quiz' | 'discuss'
  source_id: string | null
  source_title: string | null
  discussion_prompt: string | null
  order: number
  required: boolean
  auto_generated: boolean
  created: string | null
  updated: string | null
}

export interface LessonStepUpdate {
  title?: string
  step_type?: 'watch' | 'read' | 'quiz' | 'discuss'
  source_id?: string | null
  discussion_prompt?: string | null
  order?: number
  required?: boolean
}

export interface LessonPlanGenerationResponse {
  status: 'completed' | 'failed'
  step_ids: string[] | null
  error: string | null
}

export interface LearnerStepProgressResponse {
  completed_step_ids: string[]
  total_steps: number
  completed_count: number
}

/**
 * Generate a lesson plan for a notebook using AI (admin only)
 */
export async function generateLessonPlan(
  notebookId: string
): Promise<LessonPlanGenerationResponse> {
  const response = await apiClient.post<LessonPlanGenerationResponse>(
    `/notebooks/${notebookId}/lesson-steps/generate`
  )
  return response.data
}

/**
 * List all lesson steps for a notebook, ordered by step order
 */
export async function listLessonSteps(
  notebookId: string
): Promise<LessonStepResponse[]> {
  const response = await apiClient.get<LessonStepResponse[]>(
    `/notebooks/${notebookId}/lesson-steps`
  )
  return response.data
}

/**
 * Update a lesson step (admin only)
 */
export async function updateLessonStep(
  stepId: string,
  data: LessonStepUpdate
): Promise<LessonStepResponse> {
  const response = await apiClient.put<LessonStepResponse>(
    `/lesson-steps/${stepId}`,
    data
  )
  return response.data
}

/**
 * Delete a lesson step (admin only)
 */
export async function deleteLessonStep(stepId: string): Promise<void> {
  await apiClient.delete(`/lesson-steps/${stepId}`)
}

/**
 * Reorder lesson steps (admin only)
 * Sends bulk order update: [{id, order}, ...]
 */
export async function reorderLessonSteps(
  notebookId: string,
  steps: { id: string; order: number }[]
): Promise<void> {
  await apiClient.post(`/notebooks/${notebookId}/lesson-steps/reorder`, {
    steps,
  })
}

/**
 * Mark a lesson step as complete (learner only)
 */
export async function completeLessonStep(stepId: string): Promise<void> {
  await apiClient.post(`/lesson-steps/${stepId}/complete`)
}

/**
 * Get learner step progress for a notebook
 */
export async function getLessonStepsProgress(
  notebookId: string
): Promise<LearnerStepProgressResponse> {
  const response = await apiClient.get<LearnerStepProgressResponse>(
    `/notebooks/${notebookId}/lesson-steps/progress`
  )
  return response.data
}
