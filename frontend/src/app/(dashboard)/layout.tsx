'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useVersionCheck } from '@/lib/hooks/use-version-check'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { ModalProvider } from '@/components/providers/ModalProvider'
import { CreateDialogsProvider } from '@/lib/hooks/use-create-dialogs'
import { CommandPalette } from '@/components/common/CommandPalette'

/**
 * Dashboard (Admin) Layout
 *
 * This layout is for admin-only routes:
 * - /notebooks, /sources, /search, /models, /settings, /advanced, /podcasts, /transformations
 *
 * Role Guard:
 * - If user is not authenticated, redirect to /login (handled by AuthProvider)
 * - If user is authenticated but NOT admin, redirect to /modules (learner home)
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, user, hasHydrated } = useAuthStore()
  const router = useRouter()
  const [hasCheckedRole, setHasCheckedRole] = useState(false)

  // Check for version updates once per session
  useVersionCheck()

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

    // Role guard: If user is not admin, redirect to learner home
    if (user.role !== 'admin') {
      setHasCheckedRole(true)
      router.replace('/modules')
      return
    }

    setHasCheckedRole(true)
  }, [hasHydrated, isAuthenticated, user, router])

  // Show loading spinner during initial role check
  if (!hasHydrated || !hasCheckedRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Don't render main content if not authenticated (AuthProvider handles redirect)
  // Show loading instead of null to avoid a black/blank screen
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Don't render main content if not admin (redirect in progress)
  if (user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <CreateDialogsProvider>
        {children}
        <ModalProvider />
        <CommandPalette />
      </CreateDialogsProvider>
    </ErrorBoundary>
  )
}
