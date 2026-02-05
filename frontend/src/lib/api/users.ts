import apiClient from './client'
import { UserListResponse, CreateUserRequest, UpdateUserRequest } from '@/lib/types/api'

export const usersApi = {
  list: async () => {
    const response = await apiClient.get<UserListResponse[]>('/users')
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<UserListResponse>(`/users/${id}`)
    return response.data
  },

  create: async (data: CreateUserRequest) => {
    const response = await apiClient.post<UserListResponse>('/users', data)
    return response.data
  },

  update: async (id: string, data: UpdateUserRequest) => {
    const response = await apiClient.put<UserListResponse>(`/users/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    await apiClient.delete(`/users/${id}`)
  }
}
