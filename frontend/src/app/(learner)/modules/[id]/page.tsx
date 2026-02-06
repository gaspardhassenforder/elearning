'use client'

/**
 * Story 4.1: Learner Chat Interface & SSE Streaming
 *
 * Two-panel layout for learner module conversation:
 * - Left panel (1/3): Sources with tabs (Sources, Artifacts, Progress)
 * - Right panel (2/3): AI Chat with assistant-ui streaming
 *
 * Features:
 * - Resizable panels with localStorage persistence
 * - Company-scoped access control
 * - SSE streaming with token-by-token rendering
 * - Proactive AI teacher greeting
 */

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from 'react-resizable-panels'
import { ArrowLeft, BookOpen } from 'lucide-react'
import { AxiosError } from 'axios'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useToast } from '@/lib/hooks/use-toast'
import { useLearnerModule } from '@/lib/hooks/use-learner-modules'
import { SourcesPanel } from '@/components/learner/SourcesPanel'
import { ChatPanel } from '@/components/learner/ChatPanel'
import { AmbientProgressBar } from '@/components/learner/AmbientProgressBar'

export default function ModuleConversationPage() {
  const { t } = useTranslation()
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()

  const moduleId = params?.id ? decodeURIComponent(params.id as string) : ''

  // Restore panel sizes from localStorage
  const getStoredPanelSizes = (): number[] => {
    if (typeof window === 'undefined') return [33, 67]
    try {
      const stored = localStorage.getItem(`learner_panel_sizes_${moduleId}`)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length === 2) {
          return parsed
        }
      }
    } catch (e) {
      console.warn('Failed to parse stored panel sizes:', e)
    }
    return [33, 67] // Default sizes
  }

  const [panelSizes] = useState(getStoredPanelSizes)

  // Validate learner access to this module
  const { data: module, error: accessError, isLoading: accessLoading } = useLearnerModule(moduleId)

  // Redirect if access denied (403/404 only, not network errors)
  useEffect(() => {
    if (accessError) {
      // Check if it's an access denial (403/404) vs network error
      const isAxiosError = accessError instanceof AxiosError
      const errorStatus = isAxiosError ? accessError.response?.status : undefined

      if (errorStatus === 403 || errorStatus === 404) {
        toast({
          title: t.common.error,
          description: t.learner.moduleNotAccessible,
          variant: 'destructive',
        })
        router.push('/learner/modules')
      } else {
        // Network or other errors - show generic error
        toast({
          title: t.common.error,
          description: t.common.unknownError,
          variant: 'destructive',
        })
      }
    }
  }, [accessError, router, toast, t])

  // Show loading while validating access
  if (accessLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!module) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">{t.learner.moduleNotFound}</h1>
        <p className="text-muted-foreground">{t.learner.moduleNotFoundDesc}</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push('/learner/modules')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t.common.back}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => router.push('/learner/modules')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t.common.back}
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <BookOpen className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold line-clamp-1">{module.name}</h1>
                {module.description && (
                  <p className="text-sm text-muted-foreground line-clamp-1">{module.description}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Story 4.4: Ambient Progress Bar - thin indicator below header */}
      <AmbientProgressBar notebookId={moduleId} />

      {/* Two-Panel Layout with Resizable Divider */}
      <div className="flex-1 min-h-0">
        <ResizablePanelGroup
          direction="horizontal"
          className="h-full"
          onLayout={(sizes) => {
            // Persist panel sizes to localStorage
            localStorage.setItem(
              `learner_panel_sizes_${moduleId}`,
              JSON.stringify(sizes)
            )
          }}
        >
          {/* Left Panel: Sources (1/3 default, restored from localStorage) */}
          <ResizablePanel
            defaultSize={panelSizes[0]}
            minSize={20}
            maxSize={50}
            className="p-4"
          >
            <SourcesPanel notebookId={moduleId} />
          </ResizablePanel>

          {/* Resizable Divider */}
          <ResizableHandle withHandle className="bg-border hover:bg-primary/20 transition-colors" />

          {/* Right Panel: Chat (2/3 default, restored from localStorage) */}
          <ResizablePanel
            defaultSize={panelSizes[1]}
            minSize={50}
            className="p-4"
          >
            <ChatPanel notebookId={moduleId} />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}
