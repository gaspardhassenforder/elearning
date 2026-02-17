'use client'

/**
 * Module Conversation Page - ChatGPT-like Layout
 *
 * Clean, spacious layout:
 * - Header is handled by LearnerHeader (via currentModule store state)
 * - Fixed 280px sidebar: sources, artifacts, progress
 * - Chat area: fills remaining space, ChatGPT-style messages
 * - Resource viewer sheet: slides from right when sidebar item clicked
 *
 * Mobile: sidebar hidden by default, hamburger toggles overlay.
 */

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
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
import { LearnerActionButtons } from '@/components/learner/LearnerActionButtons'

export default function ModuleConversationPage() {
  const { t } = useTranslation()
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()

  const moduleId = params?.id ? decodeURIComponent(params.id as string) : ''

  // Sidebar state
  const sidebarOpen = useLearnerStore((state) => state.sidebarOpen)
  const setSidebarOpen = useLearnerStore((state) => state.setSidebarOpen)

  // Set current module in store for the unified header
  const setCurrentModule = useLearnerStore((state) => state.setCurrentModule)

  // Validate learner access
  const { data: module, error: accessError, isLoading: accessLoading } = useLearnerModule(moduleId)

  // Sync module info to store for header display
  useEffect(() => {
    if (module) {
      setCurrentModule({ id: moduleId, name: module.name })
    }
    return () => {
      setCurrentModule(null)
    }
  }, [module, moduleId, setCurrentModule])

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
      <div className="h-full flex items-center justify-center">
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
    <div className="flex flex-1 min-h-0 h-full relative">
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
      <main className="flex-1 min-w-0 h-full relative">
        <ChatPanel notebookId={moduleId} />
        <LearnerActionButtons notebookId={moduleId} />
      </main>

      {/* Resource Viewer Sheet */}
      <ResourceViewerSheet notebookId={moduleId} />
    </div>
  )
}
