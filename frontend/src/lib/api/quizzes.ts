import apiClient from './client'

export interface QuizQuestion {
  question: string
  options: string[]
  correct_answer: number
  explanation?: string
  source_reference?: string
}

export interface Quiz {
  id: string
  title: string
  description: string
  questions: QuizQuestion[]
  num_questions: number
  created: string
  created_by: string
  // Persistence fields
  completed: boolean
  user_answers?: number[]
  last_score?: number
}

export interface QuizGenerateRequest {
  topic?: string
  num_questions?: number
  source_ids?: string[]
  instructions?: string
}

export interface QuizCheckRequest {
  answers: number[]
}

export interface QuizCheckResult {
  score: number
  total: number
  percentage: number
  results: Array<{
    question_index: number
    user_answer: number
    correct_answer: number
    is_correct: boolean
    explanation?: string
  }>
}

export const quizzesApi = {
  generate: async (notebookId: string, request: QuizGenerateRequest) => {
    const response = await apiClient.post<Quiz>(
      `/notebooks/${notebookId}/quizzes/generate`,
      request
    )
    return response.data
  },
  
  list: async (notebookId: string) => {
    const response = await apiClient.get<Array<Omit<Quiz, 'questions'>>>(
      `/notebooks/${notebookId}/quizzes`
    )
    return response.data
  },
  
  get: async (quizId: string) => {
    const response = await apiClient.get<Quiz>(`/quizzes/${quizId}`)
    return response.data
  },
  
  check: async (quizId: string, request: QuizCheckRequest) => {
    const response = await apiClient.post<QuizCheckResult>(
      `/quizzes/${quizId}/check`,
      request
    )
    return response.data
  },
  
  delete: async (quizId: string) => {
    await apiClient.delete(`/quizzes/${quizId}`)
  },
  
  reset: async (quizId: string) => {
    const response = await apiClient.post<{ status: string; quiz_id: string }>(
      `/quizzes/${quizId}/reset`
    )
    return response.data
  }
}
