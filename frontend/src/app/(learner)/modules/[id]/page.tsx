'use client'

/**
 * Module Conversation Page - ChatGPT-like Layout
 *
 * Clean, spacious layout:
 * - Minimal header (48px): hamburger (mobile) + module name + back button
 * - Fixed 280px sidebar: sources, artifacts, progress
 * - Chat area: fills remaining space, ChatGPT-style messages
 * - Resource viewer sheet: slides from right when sidebar item clicked
 *
 * Mobile: sidebar hidden by default, hamburger toggles overlay.
 */

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, BookOpen, Menu, X } from 'lucide-react'
import { AxiosError } from 'axios'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useToast } from '@/lib/hooks/use-toast'
import { useLearnerModule } from '@/lib/hooks/use-learner-modules'
import { useLearnerStore } from '@/lib/stores/learner-store'
import { ResourceSidebar } from '@/components/learner/ResourceSidebar'
import { ResourceViewerSheet } from '@/components/learner/ResourceViewerSheet'
import { ChatPanel } from '@/components/learner/ChatPanel'

export default function ModuleConversationPage() {
  const { t } = useTranslation()
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()

  const moduleId = params?.id ? decodeURIComponent(params.id as string) : ''

  // Sidebar state
  const sidebarOpen = useLearnerStore((state) => state.sidebarOpen)
  const setSidebarOpen = useLearnerStore((state) => state.setSidebarOpen)
  const toggleSidebar = useLearnerStore((state) => state.toggleSidebar)

  // Validate learner access
  const { data: module, error: accessError, isLoading: accessLoading } = useLearnerModule(moduleId)

  // Redirect if access denied
  useEffect(() => {
    if (accessError) {
      const isAxiosError = accessError instanceof AxiosError
      const errorStatus = isAxiosError ? accessError.response?.status : undefined

      if (errorStatus === 403 || errorStatus === 404) {
        toast({
          title: t.common.error,
          description: t.learner.moduleNotAccessible,
          variant: 'destructive',
        })
        router.push('/modules')
      } else {
        toast({
          title: t.common.error,
          description: t.common.unknownError,
          variant: 'destructive',
        })
      }
    }
  }, [accessError, router, toast, t])

  // Loading state
  if (accessLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // Module not found
  if (!module) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">{t.learner.moduleNotFound}</h1>
        <p className="text-muted-foreground">{t.learner.moduleNotFoundDesc}</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push('/modules')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t.common.back}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Minimal Header (48px) */}
      <header className="flex-shrink-0 h-12 border-b bg-background flex items-center px-4 gap-3">
        {/* Mobile: hamburger toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden h-8 w-8"
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </Button>

        {/* Back button */}
        <Button
          variant="ghost"
          size="sm"
          className="hidden md:flex h-8 text-muted-foreground hover:text-foreground"
          onClick={() => router.push('/modules')}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          {t.common.back}
        </Button>

        {/* Module name */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <BookOpen className="h-4 w-4 text-primary flex-shrink-0" />
          <h1 className="text-sm font-medium truncate">{module.name}</h1>
        </div>
      </header>

      {/* Main Content: Sidebar + Chat */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Sidebar - fixed 280px on desktop, overlay on mobile */}
        <aside
          className={`
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            absolute md:relative z-30 md:z-0
            w-[280px] flex-shrink-0
            h-full bg-background border-r
            transition-transform duration-200 ease-in-out
            ${sidebarOpen ? '' : 'md:hidden'}
          `}
        >
          <ResourceSidebar notebookId={moduleId} />
        </aside>

        {/* Mobile sidebar overlay backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/20 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Chat Area - fills remaining space */}
        <main className="flex-1 min-w-0">
          <ChatPanel notebookId={moduleId} />
        </main>
      </div>

      {/* Resource Viewer Sheet */}
      <ResourceViewerSheet notebookId={moduleId} />
    </div>
  )
}
