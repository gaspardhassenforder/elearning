'use client';

/**
 * Admin Assistant Chat Component (Story 3.7, Task 3)
 *
 * Provides AI assistance for module creation, prompt writing, and content decisions.
 * Reuses ChatPanel component for consistent UI with learner chat.
 * Available across all pipeline steps via floating button.
 */

import { useState } from 'react';
import { Bot, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ChatPanel } from '@/components/source/ChatPanel';
import { useAdminChat } from '@/lib/hooks/use-admin-chat';
import { useTranslation } from '@/lib/hooks/use-translation';
import { toast } from 'sonner';

interface AdminAssistantChatProps {
  moduleId: string;
}

export function AdminAssistantChat({ moduleId }: AdminAssistantChatProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const {
    messages,
    isStreaming,
    sendMessage,
    modelOverride,
    setModelOverride,
    error
  } = useAdminChat(moduleId);

  // Handle errors
  if (error) {
    toast.error(t.common.error);
  }

  const handleSendMessage = async (message: string, override?: string) => {
    try {
      await sendMessage(message, override);
    } catch (err) {
      toast.error(t.chat.sendError);
    }
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-shadow z-40"
        size="icon"
        title={t.adminAssistant.title}
      >
        <Bot className="h-6 w-6" />
      </Button>

      {/* Chat Panel (Sheet) */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="right" className="w-full sm:max-w-2xl p-0 flex flex-col">
          <SheetHeader className="px-6 py-4 border-b flex-shrink-0">
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                {t.adminAssistant.title}
              </SheetTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {t.adminAssistant.subtitle}
            </p>
          </SheetHeader>

          <div className="flex-1 min-h-0 p-4">
            <ChatPanel
              messages={messages}
              isStreaming={isStreaming}
              contextIndicators={null}
              onSendMessage={handleSendMessage}
              modelOverride={modelOverride}
              onModelChange={setModelOverride}
              title={t.adminAssistant.chatTitle}
              contextType="notebook"
            />
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
