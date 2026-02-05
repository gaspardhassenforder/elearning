'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'

/**
 * Learner Layout
 *
 * This layout is for learner-only routes:
 * - /modules, /onboarding, and future learner pages
 *
 * Guards:
 * - If user is not authenticated, redirect to /login (handled by AuthProvider)
 * - If user is authenticated but NOT learner, redirect to /notebooks (admin home)
 * - If learner hasn't completed onboarding, redirect to /onboarding
 */
export default function LearnerLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, user, hasHydrated } = useAuthStore()
  const router = useRouter()
  const pathname = usePathname()
  const [hasCheckedRole, setHasCheckedRole] = useState(false)

  useEffect(() => {
    // Wait for store to hydrate
    if (!hasHydrated) {
      return
    }

    // If not authenticated, AuthProvider will handle redirect to login
    if (!isAuthenticated || !user) {
      setHasCheckedRole(true)
      return
    }

    // Role guard: If user is not learner, redirect to admin home
    if (user.role !== 'learner') {
      router.replace('/notebooks')
      return
    }

    // Onboarding guard: Force incomplete onboarding to /onboarding
    if (!user.onboarding_completed && pathname !== '/onboarding') {
      router.replace('/onboarding')
      return
    }

    // Skip onboarding if already completed
    if (user.onboarding_completed && pathname === '/onboarding') {
      router.replace('/modules')
      return
    }

    setHasCheckedRole(true)
  }, [hasHydrated, isAuthenticated, user, router, pathname])

  // Show loading spinner during initial role check
  if (!hasHydrated || !hasCheckedRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Don't render if not authenticated (AuthProvider handles redirect)
  if (!isAuthenticated || !user) {
    return null
  }

  // Don't render if not learner (redirect in progress)
  if (user.role !== 'learner') {
    return null
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-background">
        {children}
      </div>
    </ErrorBoundary>
  )
}
