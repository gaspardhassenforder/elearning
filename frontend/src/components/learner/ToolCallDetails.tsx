/**
 * Story 7.8: Tool Call Details Component
 *
 * Displays tool calls made during AI message generation.
 * Shows inputs, outputs, and clickable source links.
 */

import { useState } from 'react'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { useTranslation } from '@/lib/hooks/use-translation'
import type { ToolCall } from '@/lib/api/learner-chat'

interface ToolCallDetailsProps {
  toolCalls: ToolCall[]
  messageContent?: string
  onSourceSelect?: (sourceId: string) => void
}

export function ToolCallDetails({
  toolCalls,
  messageContent,
  onSourceSelect,
}: ToolCallDetailsProps) {
  const { t } = useTranslation()

  if (!toolCalls || toolCalls.length === 0) {
    return null
  }

  return (
    <div className="mt-3 space-y-2">
      {/* Reasoning steps (if message content provided) */}
      {messageContent && (
        <div className="text-xs text-muted-foreground border-l-2 border-border pl-3 py-1">
          <p className="font-medium mb-1">{t.learner.details.reasoning}</p>
          <p className="leading-relaxed opacity-80">{messageContent}</p>
        </div>
      )}

      {/* Tool calls accordion */}
      <Accordion type="single" collapsible className="w-full">
        {toolCalls.map((toolCall, index) => (
          <AccordionItem key={toolCall.id} value={toolCall.id}>
            <AccordionTrigger className="text-xs font-mono text-left">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">#{index + 1}</span>
                <span className="font-semibold">{toolCall.toolName}</span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                {/* Inputs */}
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    {t.learner.details.inputs}
                  </p>
                  <pre className="text-xs bg-muted/50 rounded p-2 overflow-x-auto">
                    <code role="code">{JSON.stringify(toolCall.args, null, 2)}</code>
                  </pre>
                </div>

                {/* Outputs */}
                {toolCall.result && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      {t.learner.details.outputs}
                    </p>
                    <pre className="text-xs bg-muted/50 rounded p-2 overflow-x-auto">
                      <code role="code">{JSON.stringify(toolCall.result, null, 2)}</code>
                    </pre>
                  </div>
                )}

                {/* Source links (for surface_document tool) */}
                {toolCall.toolName === 'surface_document' &&
                  toolCall.result &&
                  !toolCall.result.error &&
                  'source_id' in toolCall.result && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-1">
                        {t.learner.details.sources}
                      </p>
                      <button
                        onClick={() => onSourceSelect?.(toolCall.result.source_id)}
                        className="text-xs text-primary hover:underline cursor-pointer transition-colors"
                      >
                        {toolCall.result.title || toolCall.result.source_id}
                      </button>
                    </div>
                  )}

                {/* Pending state indicator */}
                {!toolCall.result && (
                  <div className="text-xs text-muted-foreground italic">
                    {t.learner.details.pending}
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}
