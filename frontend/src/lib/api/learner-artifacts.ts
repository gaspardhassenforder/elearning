import apiClient from './client'

// Request types
export interface LearnerPodcastRequest {
  episode_profile: string
  episode_name: string
  source_ids: string[]
  instructions?: string
}

export interface LearnerQuizRequest {
  source_ids?: string[]
  topic?: string
  num_questions?: number
}

export interface LearnerTransformationRequest {
  transformation_id: string
  source_ids: string[]
  instructions?: string
}

// Response types
export interface LearnerPodcastResponse {
  job_id: string
  status: string
  artifact_id?: string
}

export interface LearnerTransformationResponse {
  artifact_id: string
  title: string
  content_preview: string
}

export const learnerArtifactsApi = {
  generatePodcast: async (notebookId: string, request: LearnerPodcastRequest): Promise<LearnerPodcastResponse> => {
    const response = await apiClient.post<LearnerPodcastResponse>(
      `/learner/notebooks/${notebookId}/podcasts/generate`,
      request
    )
    return response.data
  },

  generateQuiz: async (notebookId: string, request: LearnerQuizRequest) => {
    const response = await apiClient.post(
      `/learner/notebooks/${notebookId}/quizzes/generate`,
      request
    )
    return response.data
  },

  executeTransformation: async (notebookId: string, request: LearnerTransformationRequest): Promise<LearnerTransformationResponse> => {
    const response = await apiClient.post<LearnerTransformationResponse>(
      `/learner/notebooks/${notebookId}/transformations/execute`,
      request
    )
    return response.data
  },
}
