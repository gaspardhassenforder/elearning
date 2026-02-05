import apiClient from './client'
import { CompanyResponse, CreateCompanyRequest, UpdateCompanyRequest } from '@/lib/types/api'

export const companiesApi = {
  list: async () => {
    const response = await apiClient.get<CompanyResponse[]>('/companies')
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<CompanyResponse>(`/companies/${id}`)
    return response.data
  },

  create: async (data: CreateCompanyRequest) => {
    const response = await apiClient.post<CompanyResponse>('/companies', data)
    return response.data
  },

  update: async (id: string, data: UpdateCompanyRequest) => {
    const response = await apiClient.put<CompanyResponse>(`/companies/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/companies/${id}`)
  }
}
