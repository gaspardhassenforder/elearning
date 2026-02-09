/**
 * Story 7.8: ToolCallDetails Component Tests
 *
 * Tests tool call accordion rendering, JSON formatting, and source links.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToolCallDetails } from '../ToolCallDetails'
import type { ToolCall } from '@/lib/api/learner-chat'

// Mock useTranslation hook
vi.mock('@/lib/hooks/use-translation', () => ({
  useTranslation: () => ({
    t: {
      learner: {
        details: {
          toolCall: 'Tool Call',
          inputs: 'Inputs',
          outputs: 'Outputs',
          sources: 'Sources',
          reasoning: 'Thinking Process',
          executionOrder: 'Execution Order',
        },
      },
    },
    language: 'en-US',
    setLanguage: vi.fn(),
  }),
}))

describe('ToolCallDetails', () => {
  const mockToolCalls: ToolCall[] = [
    {
      id: 'call_1',
      toolName: 'surface_document',
      args: { source_id: 'doc_1', query: 'test query' },
      result: {
        source_id: 'doc_1',
        title: 'Test Document',
        excerpt: 'Test excerpt',
        relevance: 'Highly relevant',
      },
    },
    {
      id: 'call_2',
      toolName: 'check_off_objective',
      args: { objective_id: 'obj_1', evidence_text: 'Student demonstrated understanding' },
      result: {
        success: true,
        objective_id: 'obj_1',
        total_completed: 3,
        total_objectives: 5,
      },
    },
  ]

  it('renders tool call accordion for each tool call', () => {
    render(<ToolCallDetails toolCalls={mockToolCalls} />)

    // Accordion triggers should show tool names
    expect(screen.getByText(/surface_document/i)).toBeInTheDocument()
    expect(screen.getByText(/check_off_objective/i)).toBeInTheDocument()
  })

  it('displays tool name as accordion trigger', () => {
    render(<ToolCallDetails toolCalls={mockToolCalls} />)

    // The tool name is in a span, but the parent button is the trigger
    const trigger = screen.getByText(/surface_document/i)
    expect(trigger).toBeInTheDocument()
    // Verify it's within an accordion trigger button
    const button = trigger.closest('button')
    expect(button).toBeInTheDocument()
  })

  it('shows formatted JSON for inputs and outputs', async () => {
    const user = userEvent.setup()

    render(<ToolCallDetails toolCalls={mockToolCalls} />)

    // Expand first accordion item
    const trigger = screen.getByText(/surface_document/i)
    await user.click(trigger)

    // Check for formatted JSON in code blocks
    const codeBlocks = screen.getAllByRole('code')
    expect(codeBlocks.length).toBeGreaterThan(0)

    // Check that JSON content is present (use getAllByText for multiple occurrences)
    const sourceIdMatches = screen.getAllByText(/"source_id"/i)
    expect(sourceIdMatches.length).toBeGreaterThan(0)
    const queryMatches = screen.getAllByText(/"query"/i)
    expect(queryMatches.length).toBeGreaterThan(0)
  })

  it('extracts and renders clickable source links from surface_document tool calls', async () => {
    const user = userEvent.setup()
    const mockOnSourceSelect = vi.fn()

    render(
      <ToolCallDetails
        toolCalls={mockToolCalls}
        onSourceSelect={mockOnSourceSelect}
      />
    )

    // Expand first accordion item
    const trigger = screen.getByText(/surface_document/i)
    await user.click(trigger)

    // Should show source link - find the button specifically (not the JSON content)
    const sourceLink = screen.getByRole('button', { name: /Test Document/i })
    expect(sourceLink).toBeInTheDocument()

    // Click source link
    await user.click(sourceLink)
    expect(mockOnSourceSelect).toHaveBeenCalledWith('doc_1')
  })

  it('handles empty tool calls array gracefully', () => {
    render(<ToolCallDetails toolCalls={[]} />)

    // Should render nothing or empty state
    expect(screen.queryByText(/Tool Call/i)).not.toBeInTheDocument()
  })

  it('handles tool calls without results (pending state)', () => {
    const pendingToolCall: ToolCall = {
      id: 'call_pending',
      toolName: 'generate_artifact',
      args: { artifact_type: 'quiz', topic: 'React' },
      // No result field
    }

    render(<ToolCallDetails toolCalls={[pendingToolCall]} />)

    // Should still render the tool call
    expect(screen.getByText(/generate_artifact/i)).toBeInTheDocument()
  })

  it('calls onSourceSelect callback when source link clicked', async () => {
    const user = userEvent.setup()
    const mockOnSourceSelect = vi.fn()

    const toolCallsWithSource: ToolCall[] = [
      {
        id: 'call_1',
        toolName: 'surface_document',
        args: { source_id: 'doc_123' },
        result: {
          source_id: 'doc_123',
          title: 'Clickable Document',
          excerpt: 'Test',
        },
      },
    ]

    render(
      <ToolCallDetails
        toolCalls={toolCallsWithSource}
        onSourceSelect={mockOnSourceSelect}
      />
    )

    // Expand accordion
    const trigger = screen.getByText(/surface_document/i)
    await user.click(trigger)

    // Click source link - find the button specifically (not the JSON content)
    const sourceLink = screen.getByRole('button', { name: /Clickable Document/i })
    await user.click(sourceLink)

    expect(mockOnSourceSelect).toHaveBeenCalledWith('doc_123')
    expect(mockOnSourceSelect).toHaveBeenCalledTimes(1)
  })
})
