import apiClient from './client'

export interface ArtifactResponse {
  id: string
  artifact_type: 'quiz' | 'podcast' | 'transformation' | 'note'
  artifact_id: string
  title: string
  created: string
}

export const artifactsApi = {
  list: async (notebookId: string, type?: string) => {
    const params = type ? { artifact_type: type } : {}
    const response = await apiClient.get<ArtifactResponse[]>(
      `/notebooks/${notebookId}/artifacts`,
      { params }
    )
    return response.data
  },
  
  delete: async (artifactId: string) => {
    await apiClient.delete(`/artifacts/${artifactId}`)
  }
}
