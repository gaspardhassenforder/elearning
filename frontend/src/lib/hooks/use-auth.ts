'use client'

import { useAuthStore, AuthUser } from '@/lib/stores/auth-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function useAuth() {
  const router = useRouter()
  const {
    isAuthenticated,
    isLoading,
    user,
    login: storeLogin,
    logout: storeLogout,
    checkAuth,
    checkAuthRequired,
    error,
    hasHydrated,
    authRequired
  } = useAuthStore()

  useEffect(() => {
    // Only check auth after the store has hydrated from localStorage
    if (hasHydrated) {
      // First check if auth is required
      if (authRequired === null) {
        checkAuthRequired().then((required) => {
          // If auth is required, check if we have valid credentials
          if (required) {
            checkAuth()
          }
        })
      } else if (authRequired) {
        // Auth is required, check credentials
        checkAuth()
      }
      // If authRequired === false, we're already authenticated (set in checkAuthRequired)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated, authRequired])

  /**
   * Login with username and password.
   * On success, redirects based on user role:
   * - admin → /notebooks
   * - learner → /modules
   */
  const handleLogin = async (username: string, password: string) => {
    const success = await storeLogin(username, password)
    if (success) {
      // Check if there's a stored redirect path
      const redirectPath = sessionStorage.getItem('redirectAfterLogin')

      // Determine default path based on role
      const currentUser = useAuthStore.getState().user
      const defaultPath = currentUser?.role === 'admin' ? '/notebooks' : '/modules'

      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin')
        router.push(redirectPath)
      } else {
        router.push(defaultPath)
      }
    }
    return success
  }

  /**
   * Logout and redirect to login page.
   */
  const handleLogout = async () => {
    await storeLogout()
    router.push('/login')
  }

  return {
    isAuthenticated,
    isLoading: isLoading || !hasHydrated, // Treat lack of hydration as loading
    user,
    error,
    login: handleLogin,
    logout: handleLogout
  }
}
