'use client'

import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { ChevronLeft, LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CollapsibleColumnProps {
  isCollapsed: boolean
  onToggle: () => void
  collapsedIcon: LucideIcon
  collapsedLabel: string
  children: ReactNode
  direction?: 'horizontal' | 'vertical' | 'vertical-in-stack'
}

export function CollapsibleColumn({
  isCollapsed,
  onToggle,
  collapsedIcon: CollapsedIcon,
  collapsedLabel,
  children,
  direction = 'horizontal',
}: CollapsibleColumnProps) {
  if (isCollapsed) {
    // 'vertical-in-stack' = vertical bar (w-12) that's stacked with others vertically
    // 'vertical' = horizontal bar (h-12, w-full) in a vertical stack
    // 'horizontal' = vertical bar (w-12, h-full) in a horizontal layout
    const isVerticalInStack = direction === 'vertical-in-stack'
    const isVertical = direction === 'vertical'
    
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={onToggle}
              className={cn(
                'flex items-center justify-center gap-2',
                'border rounded-lg',
                'bg-card hover:bg-accent/50',
                'transition-all duration-150',
                'cursor-pointer group',
                isVerticalInStack
                  ? 'w-12 h-full min-h-0 flex-col py-6'
                  : isVertical 
                    ? 'h-12 w-full px-4 flex-row' 
                    : 'w-12 h-full min-h-0 flex-col py-6'
              )}
              aria-label={`Expand ${collapsedLabel}`}
            >
              <CollapsedIcon className={cn(
                'text-muted-foreground group-hover:text-foreground transition-colors flex-shrink-0',
                (isVertical && !isVerticalInStack) ? 'h-4 w-4' : 'h-5 w-5'
              )} />
              {(isVertical && !isVerticalInStack) ? (
                <span className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                  {collapsedLabel}
                </span>
              ) : (
                <div
                  className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors whitespace-nowrap"
                  style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', textOrientation: 'mixed' }}
                >
                  {collapsedLabel}
                </div>
              )}
            </button>
          </TooltipTrigger>
          <TooltipContent side={isVerticalInStack || !isVertical ? 'right' : 'bottom'}>
            <p>Expand {collapsedLabel}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <div className={cn(
      'transition-all duration-150',
      direction === 'vertical-in-stack' ? 'w-full h-full min-h-0' :
      direction === 'horizontal' ? 'h-full min-h-0' : 'w-full'
    )}>
      {children}
    </div>
  )
}

// Factory function to create a collapse button for card headers
export function createCollapseButton(onToggle: () => void, label: string) {
  return (
    <div className="hidden lg:block">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation()
                onToggle()
              }}
              className="h-7 w-7 hover:bg-accent"
              aria-label={`Collapse ${label}`}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Collapse {label}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
