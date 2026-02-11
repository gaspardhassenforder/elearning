'use client'

/**
 * Story 5.1: Collapsed Panel Indicator
 *
 * Vertical strip shown when the sources panel is collapsed.
 * Features:
 * - FileText icon indicating sources panel
 * - PulseBadge showing count of new document references
 * - Click-to-expand functionality
 * - Tooltip with expand hint
 */

import { FileText } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'

interface CollapsedPanelIndicatorProps {
  onExpand: () => void
  className?: string
}

/**
 * @deprecated This component is no longer used in the ChatGPT-like interface.
 * Kept for backward compatibility. The ResourceSidebar replaces panel collapse behavior.
 */
export function CollapsedPanelIndicator({ onExpand, className }: CollapsedPanelIndicatorProps) {
  const { t } = useTranslation()

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={onExpand}
            className={cn(
              "h-full w-10 flex flex-col items-center justify-center gap-2",
              "bg-background border-r hover:bg-accent/10 transition-colors",
              "rounded-r-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
              className
            )}
            aria-label={t.learner.panel.collapsed}
          >
            <FileText className="h-5 w-5 text-muted-foreground" />
          </button>
        </TooltipTrigger>
        <TooltipContent side="right" sideOffset={8}>
          <p>{t.learner.panel.collapsed}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
