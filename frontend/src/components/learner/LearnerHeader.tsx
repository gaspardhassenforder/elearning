'use client'

/**
 * LearnerHeader - Unified header bar for the learner interface
 *
 * Contains:
 * - Left: Back button + module name (when inside a module), or nothing
 * - Left (mobile): Hamburger toggle for sidebar
 * - Right: Language toggle, Theme toggle, Logout button
 */

import { useRouter } from 'next/navigation'
import { LogOut, ArrowLeft, BookOpen, Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { LanguageToggle } from '@/components/common/LanguageToggle'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useAuthStore } from '@/lib/stores/auth-store'
import { useLearnerStore } from '@/lib/stores/learner-store'

export function LearnerHeader() {
  const { t } = useTranslation()
  const { logout } = useAuthStore()
  const router = useRouter()

  const currentModule = useLearnerStore((state) => state.currentModule)
  const sidebarOpen = useLearnerStore((state) => state.sidebarOpen)
  const toggleSidebar = useLearnerStore((state) => state.toggleSidebar)

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <header className="h-12 flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="h-full flex items-center justify-between px-4">
        {/* Left: Module context or empty */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {currentModule ? (
            <>
              {/* Mobile: hamburger toggle */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden h-8 w-8 flex-shrink-0"
                onClick={toggleSidebar}
                aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
              >
                {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </Button>

              {/* Back button (desktop) */}
              <Button
                variant="ghost"
                size="sm"
                className="hidden md:flex h-8 text-muted-foreground hover:text-foreground flex-shrink-0"
                onClick={() => router.push('/modules')}
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                {t.common.back}
              </Button>

              {/* Module name */}
              <BookOpen className="h-4 w-4 text-primary flex-shrink-0" />
              <span className="text-sm font-medium truncate">{currentModule.name}</span>
            </>
          ) : null}
        </div>

        {/* Right: Language, Theme, Logout */}
        <div className="flex items-center gap-1 flex-shrink-0">
          <LanguageToggle iconOnly />
          <ThemeToggle iconOnly />

          <Separator orientation="vertical" className="mx-1 h-5" />

          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
            aria-label={t.common.signOut}
          >
            <LogOut className="h-4 w-4" />
            <span className="text-xs">{t.common.signOut}</span>
          </Button>
        </div>
      </div>
    </header>
  )
}
