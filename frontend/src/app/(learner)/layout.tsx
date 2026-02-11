'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { LearnerErrorBoundaryWithRouter } from '@/components/learner/LearnerErrorBoundary'
import { LearnerHeader } from '@/components/learner/LearnerHeader'

/**
 * Learner Layout
 *
 * Minimal layout for the ChatGPT-like learner interface.
 * Guards: auth, role check, onboarding.
 * No NavigationAssistant - navigation is handled by the module page header.
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
    if (!hasHydrated) return

    if (!isAuthenticated || !user) {
      setHasCheckedRole(true)
      return
    }

    if (user.role !== 'learner') {
      setHasCheckedRole(true)
      router.replace('/notebooks')
      return
    }

    if (!user.onboarding_completed && pathname !== '/onboarding') {
      setHasCheckedRole(true)
      router.replace('/onboarding')
      return
    }

    if (user.onboarding_completed && pathname === '/onboarding') {
      setHasCheckedRole(true)
      router.replace('/modules')
      return
    }

    setHasCheckedRole(true)
  }, [hasHydrated, isAuthenticated, user, router, pathname])

  if (!hasHydrated || !hasCheckedRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (user.role !== 'learner') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <LearnerErrorBoundaryWithRouter>
      <div className="min-h-screen bg-background flex flex-col">
        <LearnerHeader />
        <div className="flex-1 min-h-0">
          {children}
        </div>
      </div>
    </LearnerErrorBoundaryWithRouter>
  )
}
