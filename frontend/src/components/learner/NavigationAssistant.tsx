/**
 * NavigationAssistant Component (Story 6.1)
 *
 * Platform-wide AI navigation assistant with:
 * - Floating bubble button (bottom-right, always visible)
 * - Dialog overlay with NavigationChat component
 * - Escape key and click-outside to close
 * - Smooth open/close transitions
 *
 * Positioning:
 * - Fixed bottom-right corner (24px from edges)
 * - z-index: 50 (above AsyncStatusBar which is z-40)
 */

'use client'

import { useEffect } from 'react'
import { MessageSquare } from 'lucide-react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useNavigationStore } from '@/lib/stores/navigation-store'
import { NavigationChat } from './NavigationChat'
import { cn } from '@/lib/utils'
import { usePathname } from 'next/navigation'

interface NavigationAssistantProps {
  currentNotebookId?: string
}

export function NavigationAssistant({ currentNotebookId }: NavigationAssistantProps) {
  const { isOpen, openNavigator, closeNavigator } = useNavigationStore()
  const pathname = usePathname()

  // Close overlay when navigating to a new page
  useEffect(() => {
    closeNavigator()
  }, [pathname, closeNavigator])

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeNavigator()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, closeNavigator])

  return (
    <>
      {/* Floating Bubble Button */}
      <Button
        onClick={openNavigator}
        size="icon"
        className={cn(
          'fixed bottom-6 right-6 z-50',
          'h-14 w-14 rounded-full shadow-lg',
          'transition-all duration-200',
          'hover:scale-110 hover:shadow-xl',
          'bg-primary text-primary-foreground'
        )}
        aria-label="Open navigation assistant"
      >
        <MessageSquare className="h-6 w-6" />
      </Button>

      {/* Dialog Overlay */}
      <Dialog open={isOpen} onOpenChange={(open) => !open && closeNavigator()}>
        <DialogContent
          className={cn(
            'fixed bottom-6 right-6',
            'w-[400px] max-w-[calc(100vw-48px)]',
            'h-[600px] max-h-[calc(100vh-48px)]',
            'p-0 gap-0',
            'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
            'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
            'origin-bottom-right'
          )}
          // Override default DialogContent positioning
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            top: 'auto',
            left: 'auto',
            transform: 'none',
          }}
        >
          <NavigationChat currentNotebookId={currentNotebookId} />
        </DialogContent>
      </Dialog>
    </>
  )
}
