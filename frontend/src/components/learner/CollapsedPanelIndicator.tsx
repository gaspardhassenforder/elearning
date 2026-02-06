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
import { useLearnerStore } from '@/lib/stores/learner-store'
import { PulseBadge } from './PulseBadge'
import { cn } from '@/lib/utils'

interface CollapsedPanelIndicatorProps {
  onExpand: () => void
  className?: string
}

export function CollapsedPanelIndicator({ onExpand, className }: CollapsedPanelIndicatorProps) {
  const { t } = useTranslation()
  const pendingBadgeCount = useLearnerStore((state) => state.pendingBadgeCount)

  const handleClick = () => {
    // Clear badge count when expanding
    useLearnerStore.getState().clearBadgeCount()
    onExpand()
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={handleClick}
            className={cn(
              "h-full w-10 flex flex-col items-center justify-center gap-2",
              "bg-background border-r hover:bg-accent/10 transition-colors",
              "rounded-r-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
              className
            )}
            aria-label={t.learner.panel.collapsed}
          >
            <FileText className="h-5 w-5 text-muted-foreground" />
            {pendingBadgeCount > 0 && (
              <PulseBadge count={pendingBadgeCount} />
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="right" sideOffset={8}>
          <p>{t.learner.panel.collapsed}</p>
          {pendingBadgeCount > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              {t.learner.panel.newDocuments.replace('{count}', String(pendingBadgeCount))}
            </p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
