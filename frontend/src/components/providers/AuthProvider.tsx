'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/stores/auth-store'
import { Loader2 } from 'lucide-react'

interface AuthProviderProps {
  children: React.ReactNode
}

/**
 * AuthProvider handles authentication state initialization and role-based routing.
 *
 * On mount:
 * 1. Calls GET /auth/me to validate token and get user data
 * 2. Stores user data in auth-store (id, role, company_id, username)
 * 3. If validation fails (401), clears auth state and redirects to /login
 *
 * Role-based redirect:
 * - At root `/`, admin users → /notebooks, learner users → /modules
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter()
  const pathname = usePathname()
  const {
    user,
    isAuthenticated,
    fetchCurrentUser,
    clearAuth,
    hasHydrated,
  } = useAuthStore()

  const [isInitializing, setIsInitializing] = useState(true)

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      // Wait for Zustand to hydrate from localStorage
      if (!hasHydrated) {
        return
      }

      // Skip auth check on login/register pages
      if (pathname === '/login' || pathname === '/register') {
        setIsInitializing(false)
        return
      }

      // Already have user (e.g. just logged in): don't block on /auth/me again
      const state = useAuthStore.getState()
      if (state.isAuthenticated && state.user) {
        setIsInitializing(false)
        return
      }

      try {
        const currentUser = await fetchCurrentUser()

        if (!currentUser) {
          clearAuth()
          router.replace('/login')
          return
        }

        // Store the user so layouts (dashboard/learner) have it after refresh
        useAuthStore.setState({
          user: currentUser,
          isAuthenticated: true,
          lastAuthCheck: Date.now(),
        })
      } catch (error) {
        console.error('Auth initialization error:', error)
        clearAuth()
        router.replace('/login')
      } finally {
        // Always stop loading so we never block the UI (redirect will happen if auth failed)
        setIsInitializing(false)
      }
    }

    initAuth()
  }, [hasHydrated, pathname, fetchCurrentUser, clearAuth, router])

  // Handle role-based redirect after auth is resolved
  useEffect(() => {
    if (isInitializing || !isAuthenticated || !user) {
      return
    }

    // Only redirect at root path
    if (pathname === '/') {
      const targetPath = user.role === 'admin' ? '/notebooks' : '/modules'
      router.replace(targetPath)
    }
  }, [isInitializing, isAuthenticated, user, pathname, router])

  // Show loading spinner while initializing auth
  if (isInitializing && pathname !== '/login' && pathname !== '/register') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
