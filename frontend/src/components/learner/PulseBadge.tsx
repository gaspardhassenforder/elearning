'use client'

/**
 * Story 5.1: Pulse Badge Component
 *
 * Animated badge that pulses when count changes, then becomes steady.
 * Used on the collapsed panel indicator to show referenced documents.
 */

import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface PulseBadgeProps {
  count: number
  className?: string
}

export function PulseBadge({ count, className }: PulseBadgeProps) {
  const [isPulsing, setIsPulsing] = useState(false)
  const [prevCount, setPrevCount] = useState(count)

  // Trigger pulse animation when count increases
  useEffect(() => {
    if (count > prevCount) {
      setIsPulsing(true)
      // Stop pulsing after 3 cycles (approximately 2.1 seconds)
      const timer = setTimeout(() => {
        setIsPulsing(false)
      }, 2100)
      return () => clearTimeout(timer)
    }
    setPrevCount(count)
  }, [count, prevCount])

  if (count <= 0) {
    return null
  }

  return (
    <Badge
      variant="default"
      className={cn(
        "min-w-[1.25rem] h-5 flex items-center justify-center text-xs font-medium",
        "bg-emerald-500 hover:bg-emerald-600 text-white border-0",
        isPulsing && "animate-pulse",
        className
      )}
    >
      {count > 99 ? '99+' : count}
    </Badge>
  )
}
