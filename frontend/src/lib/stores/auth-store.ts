import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { getApiUrl } from '@/lib/config'

/**
 * User object returned from /auth/me endpoint
 */
export interface AuthUser {
  id: string
  username: string
  role: 'admin' | 'learner'
  company_id: string | null
  email: string
  onboarding_completed: boolean
}

interface AuthState {
  isAuthenticated: boolean
  user: AuthUser | null
  isLoading: boolean
  error: string | null
  lastAuthCheck: number | null
  isCheckingAuth: boolean
  hasHydrated: boolean
  authRequired: boolean | null
  setHasHydrated: (state: boolean) => void
  checkAuthRequired: () => Promise<boolean>
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  checkAuth: () => Promise<boolean>
  fetchCurrentUser: () => Promise<AuthUser | null>
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      isLoading: false,
      error: null,
      lastAuthCheck: null,
      isCheckingAuth: false,
      hasHydrated: false,
      authRequired: null,

      setHasHydrated: (state: boolean) => {
        set({ hasHydrated: state })
      },

      checkAuthRequired: async () => {
        try {
          const apiUrl = await getApiUrl()
          const response = await fetch(`${apiUrl}/api/auth/status`, {
            cache: 'no-store',
            credentials: 'include',
          })

          if (!response.ok) {
            throw new Error(`Auth status check failed: ${response.status}`)
          }

          const data = await response.json()
          const required = data.auth_enabled || false
          set({ authRequired: required })

          // If auth is not required, mark as authenticated with a default admin user
          if (!required) {
            set({
              isAuthenticated: true,
              user: {
                id: 'anonymous',
                username: 'anonymous',
                role: 'admin',
                company_id: null,
                email: 'anonymous@localhost',
                onboarding_completed: true,
              },
            })
          }

          return required
        } catch (error) {
          console.error('Failed to check auth status:', error)

          if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
            set({
              error: 'Unable to connect to server. Please check if the API is running.',
              authRequired: null,
            })
          } else {
            set({ authRequired: true })
          }

          throw error
        }
      },

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const apiUrl = await getApiUrl()

          // Call the new JWT login endpoint
          const response = await fetch(`${apiUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include', // CRITICAL: sends and receives httpOnly cookies
            body: JSON.stringify({ username, password }),
          })

          if (response.ok) {
            // Fetch user data from /auth/me
            const user = await get().fetchCurrentUser()

            if (user) {
              set({
                isAuthenticated: true,
                user,
                isLoading: false,
                lastAuthCheck: Date.now(),
                error: null,
              })
              return true
            } else {
              set({
                error: 'Failed to fetch user profile',
                isLoading: false,
                isAuthenticated: false,
                user: null,
              })
              return false
            }
          } else {
            let errorMessage = 'Authentication failed'
            try {
              const errorData = await response.json()
              errorMessage = errorData.detail || errorMessage
            } catch {
              if (response.status === 401) {
                errorMessage = 'Invalid username or password. Please try again.'
              } else if (response.status === 403) {
                errorMessage = 'Access denied. Please check your credentials.'
              } else if (response.status >= 500) {
                errorMessage = 'Server error. Please try again later.'
              } else {
                errorMessage = `Authentication failed (${response.status})`
              }
            }

            set({
              error: errorMessage,
              isLoading: false,
              isAuthenticated: false,
              user: null,
            })
            return false
          }
        } catch (error) {
          console.error('Network error during auth:', error)
          let errorMessage = 'Authentication failed'

          if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to server. Please check if the API is running.'
          } else if (error instanceof Error) {
            errorMessage = `Network error: ${error.message}`
          } else {
            errorMessage = 'An unexpected error occurred during authentication'
          }

          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
          })
          return false
        }
      },

      logout: async () => {
        try {
          const apiUrl = await getApiUrl()

          // Call logout endpoint to clear httpOnly cookies
          await fetch(`${apiUrl}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include',
          })
        } catch (error) {
          console.error('Logout API error:', error)
          // Continue with local logout even if API call fails
        }

        set({
          isAuthenticated: false,
          user: null,
          error: null,
          lastAuthCheck: null,
        })
      },

      fetchCurrentUser: async () => {
        try {
          const apiUrl = await getApiUrl()

          const response = await fetch(`${apiUrl}/api/auth/me`, {
            method: 'GET',
            credentials: 'include', // Sends httpOnly cookies
          })

          if (response.ok) {
            const userData = await response.json()
            const user: AuthUser = {
              id: userData.id,
              username: userData.username,
              role: userData.role,
              company_id: userData.company_id,
              email: userData.email,
              onboarding_completed: userData.onboarding_completed,
            }
            return user
          }

          return null
        } catch (error) {
          console.error('Error fetching current user:', error)
          return null
        }
      },

      checkAuth: async () => {
        const state = get()
        const { lastAuthCheck, isCheckingAuth, isAuthenticated } = state

        // If already checking, return current auth state
        if (isCheckingAuth) {
          return isAuthenticated
        }

        // If we checked recently (within 30 seconds) and are authenticated, skip
        const now = Date.now()
        if (isAuthenticated && lastAuthCheck && now - lastAuthCheck < 30000) {
          return true
        }

        set({ isCheckingAuth: true })

        try {
          const user = await get().fetchCurrentUser()

          if (user) {
            set({
              isAuthenticated: true,
              user,
              lastAuthCheck: now,
              isCheckingAuth: false,
            })
            return true
          } else {
            set({
              isAuthenticated: false,
              user: null,
              lastAuthCheck: null,
              isCheckingAuth: false,
            })
            return false
          }
        } catch (error) {
          console.error('checkAuth error:', error)
          set({
            isAuthenticated: false,
            user: null,
            lastAuthCheck: null,
            isCheckingAuth: false,
          })
          return false
        }
      },

      clearAuth: () => {
        set({
          isAuthenticated: false,
          user: null,
          error: null,
          lastAuthCheck: null,
        })
      },
    }),
    {
      name: 'auth-storage',
      // Note: We do NOT persist user object since it's fetched from /auth/me on each load
      // Only persist isAuthenticated as a hint (actual validation happens via cookie)
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)
