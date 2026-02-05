import apiClient from './client'

export interface ArtifactResponse {
  id: string
  artifact_type: 'quiz' | 'podcast' | 'summary' | 'transformation'
  artifact_id: string
  title: string
  created: string
}

// Batch generation types (Story 3.2)
export interface ArtifactGenerationResult {
  status: 'pending' | 'processing' | 'completed' | 'error'
  id?: string
  error?: string
}

export interface BatchGenerationResponse {
  notebook_id: string
  quiz: ArtifactGenerationResult
  summary: ArtifactGenerationResult
  transformations: {
    status: string
    ids: string[]
    errors: string[]
  }
  podcast: {
    status: string
    command_id?: string
    artifact_ids: string[]
    error?: string
  }
}

// Preview types (Story 3.2)
export interface QuizQuestion {
  question: string
  choices: string[]
  correct_answer: number
  explanation?: string
}

export interface QuizPreview {
  artifact_type: 'quiz'
  id: string
  title: string
  question_count: number
  questions: QuizQuestion[]
}

export interface PodcastPreview {
  artifact_type: 'podcast'
  id: string
  title: string
  duration?: string
  audio_url?: string
  transcript?: string
}

export interface SummaryPreview {
  artifact_type: 'summary'
  id: string
  title: string
  word_count: number
  content: string
}

export interface TransformationPreview {
  artifact_type: 'transformation'
  id: string
  title: string
  word_count: number
  content: string
  transformation_name?: string
}

export type ArtifactPreview = QuizPreview | PodcastPreview | SummaryPreview | TransformationPreview

// Regeneration types (Story 3.2)
export interface RegenerateResponse {
  artifact_id: string
  artifact_type: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  new_artifact_id?: string
  command_id?: string
  error?: string
}

export const artifactsApi = {
  /**
   * List all artifacts for a notebook
   */
  list: async (notebookId: string, type?: string) => {
    const params = type ? { artifact_type: type } : {}
    const response = await apiClient.get<ArtifactResponse[]>(
      `/notebooks/${notebookId}/artifacts`,
      { params }
    )
    return response.data
  },

  /**
   * Generate all artifacts for a notebook (Story 3.2, Task 1)
   */
  generateAll: async (notebookId: string): Promise<BatchGenerationResponse> => {
    const response = await apiClient.post<BatchGenerationResponse>(
      `/notebooks/${notebookId}/generate-artifacts`
    )
    return response.data
  },

  /**
   * Get artifact preview with type-specific data (Story 3.2, Task 2)
   */
  getPreview: async (artifactId: string): Promise<ArtifactPreview> => {
    const response = await apiClient.get<ArtifactPreview>(
      `/artifacts/${artifactId}/preview`
    )
    return response.data
  },

  /**
   * Regenerate an artifact (Story 3.2, Task 3)
   */
  regenerate: async (artifactId: string): Promise<RegenerateResponse> => {
    const response = await apiClient.post<RegenerateResponse>(
      `/artifacts/${artifactId}/regenerate`
    )
    return response.data
  },

  /**
   * Delete an artifact
   */
  delete: async (artifactId: string) => {
    await apiClient.delete(`/artifacts/${artifactId}`)
  }
}
