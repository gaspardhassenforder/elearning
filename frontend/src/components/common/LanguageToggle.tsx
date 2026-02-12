'use client'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Languages } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'

interface LanguageToggleProps {
  iconOnly?: boolean
  className?: string
}

export function LanguageToggle({ iconOnly = false, className }: LanguageToggleProps) {
  const { language, setLanguage, t } = useTranslation()

  // Keep the actual language code for proper comparison
  const currentLang = language || 'en-US'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={iconOnly ? "ghost" : "outline"}
          size={iconOnly ? "icon" : "default"}
          className={cn(
            !iconOnly && "w-full justify-start gap-2",
            className
          )}
        >
          <Languages className="h-[1.2rem] w-[1.2rem]" />
          {!iconOnly && <span>{t.common.language}</span>}
          <span className="sr-only">{t.navigation.language}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem 
          onClick={() => setLanguage('en-US')}
          className={currentLang === 'en-US' || currentLang.startsWith('en') ? 'bg-accent' : ''}
        >
          <span>{t.common.english}</span>
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setLanguage('fr-FR')}
          className={currentLang === 'fr-FR' || currentLang.startsWith('fr') ? 'bg-accent' : ''}
        >
          <span>{t.common.french || 'Français'}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
