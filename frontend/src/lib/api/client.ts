import axios, { AxiosResponse } from 'axios'
import { getApiUrl } from '@/lib/config'

/**
 * API client with runtime-configurable base URL and cookie-based authentication.
 *
 * Authentication:
 * - Uses httpOnly cookies (set by /auth/login endpoint)
 * - withCredentials: true ensures cookies are sent with every request
 * - No manual token handling - browser manages cookies automatically
 *
 * Timeout:
 * - 10 minutes (600000ms) to accommodate slow LLM operations
 * - (transformations, insights generation, chat) especially on slower hardware
 */
export const apiClient = axios.create({
  timeout: 600000, // 600 seconds = 10 minutes
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // CRITICAL: enables httpOnly cookie handling
})

// Request interceptor to add base URL
apiClient.interceptors.request.use(async (config) => {
  // Set the base URL dynamically from runtime config
  if (!config.baseURL) {
    const apiUrl = await getApiUrl()
    config.baseURL = `${apiUrl}/api`
  }

  // Handle FormData vs JSON content types
  if (config.data instanceof FormData) {
    // Remove any Content-Type header to let browser set multipart boundary
    delete config.headers['Content-Type']
  } else if (config.method && ['post', 'put', 'patch'].includes(config.method.toLowerCase())) {
    config.headers['Content-Type'] = 'application/json'
  }

  return config
})

// Track if we're currently refreshing the token to avoid infinite loops
let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Skip refresh for auth endpoints themselves
      const isAuthEndpoint =
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/register') ||
        originalRequest.url?.includes('/auth/refresh')

      if (isAuthEndpoint) {
        return Promise.reject(error)
      }

      originalRequest._retry = true

      // If already refreshing, wait for that to complete
      if (isRefreshing && refreshPromise) {
        try {
          const refreshed = await refreshPromise
          if (refreshed) {
            return apiClient(originalRequest)
          }
        } catch {
          // Refresh failed, redirect to login
        }
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }

      // Start refresh process
      isRefreshing = true
      refreshPromise = (async () => {
        try {
          const apiUrl = await getApiUrl()
          const refreshResponse = await fetch(`${apiUrl}/api/auth/refresh`, {
            method: 'POST',
            credentials: 'include',
          })

          if (refreshResponse.ok) {
            return true
          }
          return false
        } catch {
          return false
        } finally {
          isRefreshing = false
          refreshPromise = null
        }
      })()

      try {
        const refreshed = await refreshPromise
        if (refreshed) {
          // Retry original request with new token (cookie already set)
          return apiClient(originalRequest)
        }
      } catch {
        // Refresh failed
      }

      // Refresh failed - clear state and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth-storage')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // Story 7.1: Log common error status codes at debug level (calling code handles UI feedback)
    // IMPORTANT: We log errors here but DO NOT show toasts.
    // Why? Different consumers need different error UX:
    // - Some endpoints show inline error messages (ChatErrorMessage)
    // - Some use toast notifications (learnerToast.error)
    // - Some display error states in components (loading/error UI)
    // Letting calling code decide ensures consistent, context-appropriate error handling.
    if (error.response?.status === 403) {
      console.debug('[API] Access denied:', error.config?.url)
    } else if (error.response?.status === 404) {
      console.debug('[API] Not found:', error.config?.url)
    } else if (error.response?.status && error.response.status >= 500) {
      console.debug('[API] Server error:', error.response.status, error.config?.url)
    }

    // Handle network errors (no response from server)
    if (!error.response && error.code) {
      console.debug('[API] Network error:', error.code, error.config?.url)
    }

    // Always propagate - calling code decides on UI feedback (toast, inline message, etc.)
    // This pattern prevents duplicate toasts and allows for context-specific error handling.
    return Promise.reject(error)
  }
)

export default apiClient
