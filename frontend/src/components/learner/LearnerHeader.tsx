'use client'

/**
 * LearnerHeader - Slim header bar for the learner interface
 *
 * Contains:
 * - App title (left)
 * - Language toggle, Theme toggle, Logout button (right)
 */

import { useRouter } from 'next/navigation'
import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { LanguageToggle } from '@/components/common/LanguageToggle'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useAuthStore } from '@/lib/stores/auth-store'

export function LearnerHeader() {
  const { t } = useTranslation()
  const { logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <header className="h-12 flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="h-full flex items-center justify-between px-4">
        {/* Left: App title */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">
            {t.common.appName}
          </span>
        </div>

        {/* Right: Language, Theme, Logout */}
        <div className="flex items-center gap-1">
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
