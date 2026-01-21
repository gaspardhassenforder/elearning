'use client'

import { useState, useRef, useEffect, ReactNode } from 'react'
import { GripVertical } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResizablePanelProps {
  children: ReactNode
  defaultSize?: number // percentage (0-100)
  minSize?: number // percentage
  maxSize?: number // percentage
  onResize?: (size: number) => void
  direction?: 'horizontal' | 'vertical'
  className?: string
}

export function ResizablePanel({
  children,
  defaultSize = 33,
  minSize = 10,
  maxSize = 90,
  onResize,
  direction = 'horizontal',
  className,
}: ResizablePanelProps) {
  const [size, setSize] = useState(defaultSize)
  const [isResizing, setIsResizing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const startPosRef = useRef<number>(0)
  const startSizeRef = useRef<number>(0)

  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return

      const containerRect = containerRef.current.getBoundingClientRect()
      const isHorizontal = direction === 'horizontal'
      const pos = isHorizontal ? e.clientX : e.clientY
      const containerSize = isHorizontal ? containerRect.width : containerRect.height
      const relativePos = pos - (isHorizontal ? containerRect.left : containerRect.top)
      const newSize = ((relativePos - startPosRef.current) / containerSize) * 100 + startSizeRef.current

      const clampedSize = Math.max(minSize, Math.min(maxSize, newSize))
      setSize(clampedSize)
      onResize?.(clampedSize)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, direction, minSize, maxSize, onResize])

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect()
      const isHorizontal = direction === 'horizontal'
      const pos = isHorizontal ? e.clientX : e.clientY
      const containerPos = isHorizontal ? containerRect.left : containerRect.top
      startPosRef.current = pos - containerPos
      startSizeRef.current = size
    }
  }

  const sizeStyle = direction === 'horizontal' 
    ? { width: `${size}%` }
    : { height: `${size}%` }

  return (
    <div
      ref={containerRef}
      className={cn('relative', className)}
      style={sizeStyle}
    >
      {children}
    </div>
  )
}

interface ResizableHandleProps {
  onMouseDown: (e: React.MouseEvent) => void
  direction?: 'horizontal' | 'vertical'
  className?: string
}

export function ResizableHandle({
  onMouseDown,
  direction = 'horizontal',
  className,
}: ResizableHandleProps) {
  const isHorizontal = direction === 'horizontal'

  return (
    <div
      onMouseDown={onMouseDown}
      className={cn(
        'absolute z-10 bg-border hover:bg-primary/50 transition-colors cursor-col-resize',
        isHorizontal
          ? 'top-0 right-0 w-1 h-full cursor-col-resize'
          : 'left-0 bottom-0 h-1 w-full cursor-row-resize',
        'group',
        className
      )}
      style={
        isHorizontal
          ? { right: '-3px', width: '6px' }
          : { bottom: '-3px', height: '6px' }
      }
    >
      <div
        className={cn(
          'absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity',
          isHorizontal ? 'flex-col' : 'flex-row'
        )}
      >
        <GripVertical
          className={cn(
            'text-muted-foreground',
            isHorizontal ? 'rotate-90' : ''
          )}
          size={12}
        />
      </div>
    </div>
  )
}
