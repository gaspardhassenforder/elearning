import apiClient from './client'
import { getApiUrl } from '@/lib/config'
import {
  PodcastEpisode,
  EpisodeProfile,
  SpeakerProfile,
  SpeakerVoiceConfig,
  PodcastGenerationRequest,
  PodcastGenerationResponse,
} from '@/lib/types/podcasts'

export type UnifiedPodcastProfilePayload = {
  name: string
  description: string
  speakers: SpeakerVoiceConfig[]
  default_briefing: string
  num_segments: number
}

export async function resolvePodcastAssetUrl(path?: string | null): Promise<string | undefined> {
  if (!path) {
    return undefined
  }

  if (/^https?:\/\//i.test(path)) {
    return path
  }

  const base = await getApiUrl()

  if (path.startsWith('/')) {
    return `${base}${path}`
  }

  return `${base}/${path}`
}

interface JobStatusResponse {
  job_id: string
  status: string
  result?: unknown
  error_message?: string | null
  created?: string | null
  updated?: string | null
  progress?: number | null
}

export const podcastsApi = {
  listEpisodes: async () => {
    const response = await apiClient.get<PodcastEpisode[]>('/podcasts/episodes')
    return response.data
  },

  getEpisode: async (episodeId: string) => {
    const response = await apiClient.get<PodcastEpisode>(`/podcasts/episodes/${episodeId}`)
    return response.data
  },

  getJobStatus: async (jobId: string) => {
    // Remove command: prefix if present and URL encode the job ID
    const cleanJobId = jobId.replace(/^command:/, '')
    const encodedJobId = encodeURIComponent(cleanJobId)
    const response = await apiClient.get<JobStatusResponse>(`/podcasts/jobs/${encodedJobId}`)
    return response.data
  },

  deleteEpisode: async (episodeId: string) => {
    await apiClient.delete(`/podcasts/episodes/${episodeId}`)
  },

  listEpisodeProfiles: async () => {
    const response = await apiClient.get<EpisodeProfile[]>('/episode-profiles')
    return response.data
  },

  deleteEpisodeProfile: async (profileId: string) => {
    await apiClient.delete(`/episode-profiles/${profileId}`)
  },

  duplicateEpisodeProfile: async (profileId: string) => {
    const response = await apiClient.post<EpisodeProfile>(
      `/episode-profiles/${profileId}/duplicate`
    )
    return response.data
  },

  createUnifiedEpisodeProfile: async (payload: UnifiedPodcastProfilePayload) => {
    const response = await apiClient.post<EpisodeProfile>(
      '/episode-profiles/unified',
      payload
    )
    return response.data
  },

  updateUnifiedEpisodeProfile: async (
    profileId: string,
    payload: UnifiedPodcastProfilePayload
  ) => {
    const response = await apiClient.put<EpisodeProfile>(
      `/episode-profiles/${profileId}/unified`,
      payload
    )
    return response.data
  },

  getSpeakerProfileByName: async (profileName: string) => {
    const enc = encodeURIComponent(profileName)
    const response = await apiClient.get<SpeakerProfile>(
      `/speaker-profiles/${enc}`
    )
    return response.data
  },

  listSpeakerProfiles: async () => {
    const response = await apiClient.get<SpeakerProfile[]>('/speaker-profiles')
    return response.data
  },

  generatePodcast: async (payload: PodcastGenerationRequest) => {
    const response = await apiClient.post<PodcastGenerationResponse>(
      '/podcasts/generate',
      payload
    )
    return response.data
  },

  cancelJob: async (jobId: string) => {
    // Remove command: prefix if present and URL encode the job ID
    const cleanJobId = jobId.replace(/^command:/, '')
    const encodedJobId = encodeURIComponent(cleanJobId)
    const response = await apiClient.delete<{ success: boolean; message: string }>(
      `/commands/jobs/${encodedJobId}`
    )
    return response.data
  },
}
