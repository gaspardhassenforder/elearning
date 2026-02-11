'use client'

/**
 * LearnerHeader - Slim header bar for the learner interface
 *
 * Contains:
 * - App title (left)
 * - Language toggle (right)
 * - Theme toggle (right)
 * - Logout button (right)
 */

import { useRouter } from 'next/navigation'
import { Globe, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useAuthStore } from '@/lib/stores/auth-store'

export function LearnerHeader() {
  const { t, language, setLanguage } = useTranslation()
  const { logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang)
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
          {/* Language toggle */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Globe className="h-4 w-4" />
                <span className="sr-only">{t.common.language}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => handleLanguageChange('en-US')}
                className={language === 'en-US' ? 'bg-accent' : ''}
              >
                {t.common.english}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => handleLanguageChange('fr-FR')}
                className={language === 'fr-FR' ? 'bg-accent' : ''}
              >
                {t.common.french}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Theme toggle */}
          <ThemeToggle iconOnly />

          {/* Logout button */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
            aria-label={t.common.signOut}
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
