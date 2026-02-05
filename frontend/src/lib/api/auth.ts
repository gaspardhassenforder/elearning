import apiClient from './client'
import { OnboardingSubmit, OnboardingResponse } from '@/lib/types/api'

export const authApi = {
  submitOnboarding: async (data: OnboardingSubmit) => {
    const response = await apiClient.put<OnboardingResponse>('/auth/me/onboarding', data)
    return response.data
  },
}
