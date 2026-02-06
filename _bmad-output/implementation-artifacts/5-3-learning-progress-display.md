# Story 5.3: Learning Progress Display

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want to view my progress on learning objectives for a module,
so that I have a sense of how much I've covered.

## Acceptance Criteria

**AC1:** Given the Progress tab is active
When the panel loads
Then all learning objectives are listed with checked/unchecked status

**AC2:** Given the progress display
When rendered
Then a summary shows "X of Y" completed with a progress bar

**AC3:** Given an objective was just checked off in conversation
When the Progress tab is viewed
Then the newly checked item shows a brief warm glow (3 seconds) before settling to normal checked state

**AC4:** Given the learner is on the conversation screen
When an objective is checked off
Then the ambient progress bar (3px thin line below header) increments in real-time

## Tasks / Subtasks

- [x] Task 1: Warm Glow Animation for Recently Checked Objectives (AC: 3)
  - [x] Extend ObjectiveProgressList to track recentlyCheckedObjectiveIds with timestamps
  - [x] Listen to `objective_checked` SSE event via useLearnerChat hook
  - [x] Add objective_id to recentlyCheckedObjectiveIds when event received
  - [x] Implement auto-removal after 3 seconds using setTimeout
  - [x] Apply conditional CSS class to ObjectiveItem for warm glow styling
  - [x] Use ring animation with warm primary color (ring-2 ring-primary/50)
  - [x] Test animation triggers on SSE event and auto-clears after 3s

- [x] Task 2: Verify Progress Tab Integration in SourcesPanel (AC: 1, 2, 4)
  - [x] Confirm Progress tab renders ObjectiveProgressList (already implemented)
  - [x] Verify useLearnerObjectivesProgress hook fetches progress data
  - [x] Validate checklist display with checked/unchecked status
  - [x] Verify "X of Y" summary and progress bar display
  - [x] Test ambient progress bar increments on objective completion
  - [x] No code changes needed - just verification

- [x] Task 3: Testing & Validation (All ACs)
  - [x] Frontend tests: ObjectiveProgressList warm glow animation (5 cases)
  - [x] Test SSE event listener integration
  - [x] Test auto-removal after 3 seconds
  - [x] Test multiple objectives checked in quick succession
  - [x] Update sprint-status.yaml: story status to "review"

## Dev Notes

### 🎯 Story Overview

This is the **third and final story in Epic 5: Content Browsing & Learning Progress**. It completes the Progress tab implementation in the SourcesPanel by adding a warm glow animation for newly checked objectives.

**Key Context - What Already Exists:**
The learning progress display was substantially implemented in Story 4.4 (Learning Objectives Assessment & Progress Tracking):
- ObjectiveProgressList component (214 lines) - Checklist with completion status
- AmbientProgressBar component (90 lines) - 3px progress bar below header
- useLearnerObjectivesProgress hook - Fetches progress data with auto-refresh
- check_off_objective tool - Backend mechanism for marking objectives complete
- objective_checked SSE event - Real-time notification of completions
- Progress tab in SourcesPanel - Already integrated and rendering

**What Story 5.3 Adds:**
- Warm glow animation for newly checked objectives (AC3)
- Track recentlyCheckedObjectiveIds in ObjectiveProgressList state
- SSE event listener integration for objective_checked events
- Auto-removal of glow after 3 seconds
- Conditional styling with ring animation

**Critical Context:**
- **FR35** (Learners can view their soft progress on learning objectives for a module)
- Builds on Story 4.4 (ObjectiveProgressList, check_off_objective tool, SSE events)
- Builds on Story 5.1 (SourcesPanel tabbed interface, Progress tab)
- Completes Epic 5 - all three tabs (Sources, Artifacts, Progress) now fully functional

### 🏗️ Architecture Patterns (MANDATORY)

**Warm Glow Animation Flow:**
```
AI teacher checks off objective in conversation
  ↓
[Backend] check_off_objective tool creates LearnerObjectiveProgress record
  ↓
[SSE Stream] emits objective_checked event to frontend
  {
    type: 'objective_checked',
    data: {
      objective_id: 'learning_objective:uuid',
      objective_text: 'Understand gradient descent',
      evidence: 'Demonstrated by explaining backpropagation...',
      total_completed: 3,
      total_objectives: 5
    }
  }
  ↓
[useLearnerChat hook] parses SSE event
  ├─ Shows inline toast: "✓ You've demonstrated understanding of [text]"
  ├─ Invalidates TanStack Query cache for learningObjectivesKeys.progressByNotebook
  └─ Triggers useLearnerObjectivesProgress refetch
  ↓
[ObjectiveProgressList component] receives SSE event via custom listener
  ├─ Extracts objective_id from event data
  ├─ Adds to recentlyCheckedObjectiveIds state: Map<string, timestamp>
  ├─ Sets setTimeout to remove after 3000ms
  └─ Re-renders with warm glow applied
  ↓
[ObjectiveItem] conditional rendering:
  ├─ Check if objective.id in recentlyCheckedObjectiveIds
  ├─ Apply warmGlow class if found
  └─ CSS animation: ring-2 ring-primary/50 with pulse
  ↓
After 3 seconds:
  ├─ setTimeout callback fires
  ├─ Remove objective_id from recentlyCheckedObjectiveIds
  └─ Component re-renders, glow removed, normal checked state
```

**SSE Event Listener Integration:**
```
[ObjectiveProgressList] useEffect hook on mount
  ↓
[learner-store or custom event bus] subscribe to 'objective_checked' events
  ↓
Event handler:
  const handleObjectiveChecked = (event: SSEObjectiveCheckedEvent) => {
    const { objective_id } = event.data;
    setRecentlyCheckedObjectiveIds(prev =>
      new Map(prev).set(objective_id, Date.now())
    );

    setTimeout(() => {
      setRecentlyCheckedObjectiveIds(prev => {
        const next = new Map(prev);
        next.delete(objective_id);
        return next;
      });
    }, 3000);
  };
  ↓
Cleanup on unmount: unsubscribe from event bus
```

**Critical Rules:**
- **3-Second Timer**: Warm glow must auto-remove after exactly 3 seconds
- **Multiple Objectives**: Support multiple glowing objectives simultaneously (each with own timer)
- **Graceful Degradation**: If SSE event missed, objective still appears checked (just without glow)
- **Progress Tab Only**: Glow only visible when Progress tab active (ambient bar updates regardless)
- **No Flash on Load**: Don't glow objectives that were completed in previous sessions
- **Component State**: Track in ObjectiveProgressList local state, not global store
- **CSS Animation**: Use existing ring utility pattern from Tailwind, warm primary color

### 📋 Technical Requirements

**Frontend Stack:**
- Existing ObjectiveProgressList component - EXTEND with glow tracking
- Existing useLearnerChat hook - EXTEND to emit custom events
- Existing SourcesPanel with Progress tab - NO CHANGES
- React hooks: useState, useEffect for timer management
- Custom event bus or direct SSE listener integration
- Tailwind CSS for ring animation styling

**No Backend Changes Required:**
- ✅ check_off_objective tool already implemented (Story 4.4)
- ✅ objective_checked SSE event already emitted (Story 4.4)
- ✅ LearnerObjectiveProgress model already exists
- ✅ Progress API endpoint already implemented
- Story 5.3 is pure frontend enhancement

**Component Extension:**

```typescript
// frontend/src/components/learner/ObjectiveProgressList.tsx (EXTEND)

interface ObjectiveProgressListProps {
  notebookId: string
}

function ObjectiveProgressList({ notebookId }: ObjectiveProgressListProps) {
  const { data, isLoading, error } = useLearnerObjectivesProgress(notebookId);

  // NEW: Track recently checked objectives with timestamps
  const [recentlyCheckedObjectiveIds, setRecentlyCheckedObjectiveIds] =
    useState<Map<string, number>>(new Map());

  // NEW: Listen for objective_checked SSE events
  useEffect(() => {
    const handleObjectiveChecked = (event: CustomEvent) => {
      const { objective_id } = event.detail;

      // Add to recently checked map
      setRecentlyCheckedObjectiveIds(prev =>
        new Map(prev).set(objective_id, Date.now())
      );

      // Auto-remove after 3 seconds
      const timerId = setTimeout(() => {
        setRecentlyCheckedObjectiveIds(prev => {
          const next = new Map(prev);
          next.delete(objective_id);
          return next;
        });
      }, 3000);

      return () => clearTimeout(timerId);
    };

    // Subscribe to objective_checked events
    window.addEventListener('objective_checked', handleObjectiveChecked as EventListener);

    return () => {
      window.removeEventListener('objective_checked', handleObjectiveChecked as EventListener);
    };
  }, []);

  return (
    <div className="space-y-4">
      {/* Progress summary - already implemented */}
      <ProgressSummary completed={data.completed_count} total={data.total_count} />

      {/* Objective checklist */}
      <div className="space-y-2">
        {data.objectives.map((objective) => (
          <ObjectiveItem
            key={objective.id}
            objective={objective}
            hasWarmGlow={recentlyCheckedObjectiveIds.has(objective.id)}  // NEW
          />
        ))}
      </div>
    </div>
  );
}
```

**CSS Styling for Warm Glow:**

```tsx
// frontend/src/components/learner/ObjectiveProgressList.tsx

function ObjectiveItem({ objective, hasWarmGlow }: ObjectiveItemProps) {
  const isCompleted = objective.progress_status === 'completed';

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg transition-all duration-150",
        isCompleted && "bg-success/10",
        hasWarmGlow && "ring-2 ring-primary/50 animate-pulse"  // NEW: Warm glow
      )}
    >
      <div className="flex-shrink-0 mt-0.5">
        {isCompleted ? (
          <CheckCircle2 className="w-5 h-5 text-success" />
        ) : (
          <Circle className="w-5 h-5 text-muted-foreground" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn(
          "text-sm font-medium",
          isCompleted ? "text-success" : "text-foreground"
        )}>
          {objective.text}
        </p>
        {isCompleted && objective.progress_evidence && (
          <Tooltip>
            <TooltipTrigger>
              <p className="text-xs text-muted-foreground mt-1">
                {t('progress.evidence')}
              </p>
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs">{objective.progress_evidence}</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
```

**SSE Event Emitter Extension:**

```typescript
// frontend/src/lib/hooks/use-learner-chat.ts (EXTEND)

// When parsing objective_checked SSE event:
if (event.type === 'objective_checked') {
  const data = JSON.parse(event.data);

  // Existing: Show toast notification
  toast.success(t('progress.objectiveCompleted'), {
    description: data.objective_text,
  });

  // Existing: Invalidate TanStack Query cache
  queryClient.invalidateQueries({
    queryKey: learningObjectivesKeys.progressByNotebook(notebookId),
  });

  // NEW: Emit custom event for ObjectiveProgressList
  window.dispatchEvent(new CustomEvent('objective_checked', {
    detail: data
  }));
}
```

### 🎨 UI/UX Requirements (from UX spec)

**Warm Glow Animation (NEW for Story 5.3):**
- **Duration:** Exactly 3 seconds from event trigger
- **Style:** ring-2 ring-primary/50 (2px ring, 50% opacity warm color)
- **Animation:** animate-pulse from Tailwind (gentle pulsing effect)
- **Transition:** 150ms ease for glow appearance/disappearance
- **Multiple Objects:** Each objective has independent timer
- **Visual Hierarchy:** Glow does NOT override checked state styling - adds on top
- **Accessibility:** Does not affect screen reader announcements (toast already announces)

**Existing Progress Tab Layout (Verified):**
- Tabbed interface: Sources | Artifacts | Progress
- Progress tab icon: TrendingUp
- Progress summary at top: "X of Y completed" with Radix Progress bar
- Objectives list: Vertical layout with CheckCircle2/Circle icons
- Checked state: bg-success/10 background, green text, green checkmark
- Unchecked state: Circle icon, muted text
- Tooltip on hover: Shows evidence text for completed objectives
- Empty state: "No Learning Objectives" with friendly message
- All complete state: "Congratulations! You've completed all learning objectives!"

**Animation Timing:**
- 0ms: AI checks off objective, SSE event emitted
- 0-100ms: Toast appears (existing behavior)
- 0-100ms: Warm glow applied to ObjectiveItem
- 100-3000ms: Glow pulses gently
- 3000ms: Glow removed, normal checked state remains
- Ambient bar update: Immediate (no delay)

**Internationalization (i18n):**
- No new i18n keys needed - all strings already exist from Story 4.4
- `progress.objectiveCompleted`: "Objective completed"
- `progress.evidence`: "Evidence"
- `progress.complete`: "complete"
- `progress.completedAt`: "Completed on {date}"

### 🗂️ Data Models & Dependencies

**Existing Models (NO CHANGES):**
- **LearningObjective** (backend): id, notebook_id, text, order, auto_generated
- **LearnerObjectiveProgress** (backend): id, user_id, objective_id, status, completed_via, evidence, completed_at
- **ObjectiveWithProgress** (frontend): Combined objective + progress data

**Existing SSE Event Type:**
```typescript
// frontend/src/lib/types/sse.ts (already exists)

interface ObjectiveCheckedEvent {
  type: 'objective_checked'
  data: {
    objective_id: string
    objective_text: string
    evidence: string
    total_completed: number
    total_objectives: number
  }
}
```

**New Component State (Local):**
```typescript
// frontend/src/components/learner/ObjectiveProgressList.tsx

type RecentlyCheckedMap = Map<string, number>  // objective_id -> timestamp

const [recentlyCheckedObjectiveIds, setRecentlyCheckedObjectiveIds] =
  useState<RecentlyCheckedMap>(new Map());
```

**Existing TanStack Query Hook (NO CHANGES):**
```typescript
// frontend/src/lib/hooks/use-learning-objectives.ts

export function useLearnerObjectivesProgress(notebookId: string | null) {
  return useQuery({
    queryKey: learningObjectivesKeys.progressByNotebook(notebookId),
    queryFn: () => learningObjectivesApi.getLearnerObjectivesProgress(notebookId!),
    enabled: !!notebookId,
    refetchOnWindowFocus: true,
    staleTime: 30 * 1000,  // 30 seconds
  });
}
```

### 📁 File Structure & Naming

**Frontend Files to Modify:**

- `frontend/src/components/learner/ObjectiveProgressList.tsx` - ADD warm glow tracking (~40 lines)
- `frontend/src/lib/hooks/use-learner-chat.ts` - ADD custom event dispatch (~5 lines)

**Frontend Files to Extend Tests:**

- `frontend/src/components/learner/__tests__/ObjectiveProgressList.test.tsx` - ADD 5 test cases for glow

**No New Files Created** - This is a pure enhancement to existing components.

**Directory Structure:**
```
frontend/src/
├── components/learner/
│   ├── ObjectiveProgressList.tsx       # MODIFY - add glow tracking
│   ├── AmbientProgressBar.tsx          # NO CHANGE - already updates on SSE
│   ├── SourcesPanel.tsx                # NO CHANGE - Progress tab already integrated
│   └── __tests__/
│       └── ObjectiveProgressList.test.tsx  # EXTEND - add glow tests
├── lib/
│   ├── hooks/
│   │   ├── use-learning-objectives.ts  # NO CHANGE - already fetches progress
│   │   └── use-learner-chat.ts         # MODIFY - emit custom event
│   ├── api/
│   │   └── learning-objectives.ts      # NO CHANGE
│   ├── types/
│   │   ├── api.ts                      # NO CHANGE
│   │   └── sse.ts                      # NO CHANGE - ObjectiveCheckedEvent already exists
│   └── locales/
│       ├── en-US/index.ts              # NO CHANGE - all keys exist
│       └── fr-FR/index.ts              # NO CHANGE
```

**Backend Files:**
- **NO BACKEND CHANGES** - All backend infrastructure already exists from Story 4.4

### 🧪 Testing Requirements

**Frontend Tests (Vitest/React Testing Library) - 5 new test cases:**

**ObjectiveProgressList Warm Glow Tests:**
```typescript
// components/learner/__tests__/ObjectiveProgressList.test.tsx (EXTEND)

describe('ObjectiveProgressList - Warm Glow Animation', () => {
  it('applies warm glow when objective_checked event fired', async () => {
    render(<ObjectiveProgressList notebookId="notebook:123" />);

    // Dispatch objective_checked event
    const event = new CustomEvent('objective_checked', {
      detail: { objective_id: 'learning_objective:abc123' }
    });
    window.dispatchEvent(event);

    // Verify glow applied
    const objectiveItem = await screen.findByText('Understand gradient descent');
    expect(objectiveItem.closest('div')).toHaveClass('ring-2', 'ring-primary/50');
  });

  it('removes warm glow after 3 seconds', async () => {
    jest.useFakeTimers();
    render(<ObjectiveProgressList notebookId="notebook:123" />);

    window.dispatchEvent(new CustomEvent('objective_checked', {
      detail: { objective_id: 'learning_objective:abc123' }
    }));

    const objectiveItem = screen.getByText('Understand gradient descent');
    expect(objectiveItem.closest('div')).toHaveClass('ring-2');

    // Fast-forward 3 seconds
    jest.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(objectiveItem.closest('div')).not.toHaveClass('ring-2');
    });

    jest.useRealTimers();
  });

  it('supports multiple objectives glowing simultaneously', async () => {
    render(<ObjectiveProgressList notebookId="notebook:123" />);

    // Check off two objectives quickly
    window.dispatchEvent(new CustomEvent('objective_checked', {
      detail: { objective_id: 'learning_objective:obj1' }
    }));
    window.dispatchEvent(new CustomEvent('objective_checked', {
      detail: { objective_id: 'learning_objective:obj2' }
    }));

    const objective1 = screen.getByText('Objective 1');
    const objective2 = screen.getByText('Objective 2');

    expect(objective1.closest('div')).toHaveClass('ring-2');
    expect(objective2.closest('div')).toHaveClass('ring-2');
  });

  it('does not glow objectives that were already completed', () => {
    // Render with already-completed objective
    const { container } = render(<ObjectiveProgressList notebookId="notebook:123" />);

    // Verify no glow on mount (only completed status styling)
    const completedObjective = screen.getByText('Already Completed Objective');
    expect(completedObjective.closest('div')).toHaveClass('bg-success/10');
    expect(completedObjective.closest('div')).not.toHaveClass('ring-2');
  });

  it('cleans up event listeners on unmount', () => {
    const { unmount } = render(<ObjectiveProgressList notebookId="notebook:123" />);

    const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith(
      'objective_checked',
      expect.any(Function)
    );
  });
});
```

**Test Coverage Targets:**
- Frontend: 80%+ for ObjectiveProgressList component
- Focus on: Event listener registration, timer management, CSS class toggling

**Integration Tests (Manual Verification):**
- Check off objective in conversation → Verify toast + glow + ambient bar update
- Switch to Progress tab → Verify glow visible
- Wait 3 seconds → Verify glow disappears, checked state remains
- Check off multiple objectives → Verify independent timers
- Return to module after completion → Verify no glow on previously completed objectives

### 🚫 Anti-Patterns to Avoid (from Memory + Previous Stories)

**From Memory (CRITICAL):**

1. **Global Store Pollution**
   - ❌ Store recentlyCheckedObjectiveIds in learner-store
   - ✅ Keep in ObjectiveProgressList component state (local, transient)

2. **Missing Timer Cleanup**
   - ❌ Don't clear setTimeout on component unmount
   - ✅ Return cleanup function from useEffect

3. **Flash on Page Load**
   - ❌ Glow objectives that were completed in previous sessions
   - ✅ Only glow when objective_checked event received in current session

4. **Multiple Event Listeners**
   - ❌ Register new listener on every re-render
   - ✅ useEffect with empty dependency array for registration

**From Previous Stories:**

5. **Blocking Animation** (Story 4.4 lesson)
   - ❌ Wait for animation to complete before updating state
   - ✅ Glow is purely visual, state updates immediately

6. **No Accessibility Consideration**
   - ❌ Rely only on visual glow for feedback
   - ✅ Toast notification already announces completion (screen reader accessible)

7. **Hard-Coded Timing**
   - ❌ Magic number 3000 scattered in code
   - ✅ Define GLOW_DURATION_MS constant at top of file

8. **Event Listener Memory Leak**
   - ❌ Forget to remove event listener on unmount
   - ✅ Return cleanup function from useEffect

9. **Type Safety Issues**
   - ❌ Use `any` for CustomEvent detail
   - ✅ Define ObjectiveCheckedEventDetail interface

10. **Glow Without Check**
    - ❌ Apply glow even if objective not in current list
    - ✅ Check if objective.id exists before applying hasWarmGlow

### 🔗 Integration with Existing Code

**Builds on Story 4.4 (Learning Objectives Assessment & Progress Tracking):**
- ObjectiveProgressList component structure
- check_off_objective tool in backend
- objective_checked SSE event emission
- useLearnerObjectivesProgress hook
- AmbientProgressBar real-time updates
- Story 5.3 ADDS: Warm glow animation for visual feedback

**Builds on Story 5.1 (Sources Panel with Document Browsing):**
- SourcesPanel tabbed interface (Sources | Artifacts | Progress)
- Progress tab integration point
- Panel rendering patterns
- Story 5.3 ENHANCES: Progress tab content with glow animation

**Builds on Story 5.2 (Artifacts Browsing in Side Panel):**
- Completed Epic 5 tab structure
- All three tabs now fully functional
- Story 5.3 COMPLETES: Epic 5 final story

**Integration Points:**

**Frontend:**
- `ObjectiveProgressList.tsx` - Add warm glow tracking state and SSE listener
- `use-learner-chat.ts` - Extend objective_checked event handler to emit custom event
- `SourcesPanel.tsx` - NO CHANGES (Progress tab already renders ObjectiveProgressList)

**No Breaking Changes:**
- All changes are additive enhancements
- Existing progress display functionality unchanged
- Existing SSE event handling extended (not replaced)
- Existing toast notifications unchanged
- Backward compatible: If glow fails, progress still works normally

### 📊 Data Flow Diagrams

**Warm Glow Animation Flow:**
```
[Conversation] Learner demonstrates understanding
  ↓
[AI Teacher] Invokes check_off_objective tool
  ↓
[Backend] Creates LearnerObjectiveProgress record (status=completed)
  ↓
[SSE Stream] Emits objective_checked event
  ↓
[useLearnerChat hook] Receives SSE event
  ├─ Shows toast: "✓ Objective completed"
  ├─ Invalidates TanStack Query cache
  └─ Dispatches custom window event: 'objective_checked'
  ↓
[ObjectiveProgressList] Event listener fires
  ├─ Extract objective_id from event.detail
  ├─ Add to recentlyCheckedObjectiveIds Map
  ├─ Start 3-second setTimeout
  └─ Component re-renders
  ↓
[ObjectiveItem] Conditional rendering
  ├─ Check if objective.id in recentlyCheckedObjectiveIds
  ├─ If yes: Apply ring-2 ring-primary/50 animate-pulse
  └─ Render with glow
  ↓
[3 seconds later]
  ├─ setTimeout callback executes
  ├─ Remove objective_id from Map
  ├─ Component re-renders
  └─ Glow removed, normal checked state remains
```

**Multiple Objectives Checked in Sequence:**
```
Time: 0ms
  ├─ Objective A checked
  ├─ Add A to Map, start timer A (expires at 3000ms)
  └─ A glows

Time: 1000ms
  ├─ Objective B checked
  ├─ Add B to Map, start timer B (expires at 4000ms)
  └─ A glows, B glows

Time: 3000ms
  ├─ Timer A expires
  ├─ Remove A from Map
  └─ A stops glowing, B still glowing

Time: 4000ms
  ├─ Timer B expires
  ├─ Remove B from Map
  └─ B stops glowing
```

### 🎓 Previous Story Learnings Applied

**From Story 4.4 (Learning Objectives Assessment & Progress Tracking):**
- ObjectiveProgressList component patterns
- SSE event handling for objective_checked
- TanStack Query cache invalidation
- Toast notifications for completion feedback
- **Applied**: Extend SSE handler to emit custom event for glow tracking

**From Story 5.1 (Sources Panel with Document Browsing):**
- Document highlight animation pattern (ring + pulse)
- Timeout management for transient visual effects
- Component local state for temporary UI state
- **Applied**: Same ring animation pattern, local state for glow tracking

**From Story 5.2 (Artifacts Browsing in Side Panel):**
- Accordion behavior with local state
- Lazy loading patterns
- Type-specific rendering
- **Applied**: Local state pattern for warm glow (not global store)

**From Code Review Patterns:**
- Timer cleanup on component unmount
- Type safety for event handlers
- Accessibility considerations (don't rely only on visuals)
- Comprehensive testing (80%+ coverage)
- No unnecessary global state

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Strategy] - Component patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#SSE Streaming] - Event handling

**UX Design Specification:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Warm Glow Animation] - 3-second glow for checked objectives
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Ambient Progress Tracking] - Progress bar design

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3] - Lines 924-948
- [Source: _bmad-output/planning-artifacts/epics.md#FR35] - View learning objectives progress

**Existing Code (Critical for Implementation):**
- [Source: frontend/src/components/learner/ObjectiveProgressList.tsx] - Component to extend
- [Source: frontend/src/lib/hooks/use-learner-chat.ts] - SSE event handler
- [Source: frontend/src/lib/hooks/use-learning-objectives.ts] - Progress data hook
- [Source: frontend/src/lib/types/sse.ts] - ObjectiveCheckedEvent type
- [Source: api/routers/learner_chat.py] - Lines 514-529, SSE emission
- [Source: open_notebook/graphs/tools.py] - check_off_objective tool
- [Source: open_notebook/domain/learner_objective_progress.py] - Progress model

**Previous Stories (Context):**
- [Source: _bmad-output/implementation-artifacts/4-4-learning-objectives-assessment-and-progress-tracking.md] - Foundation
- [Source: _bmad-output/implementation-artifacts/5-1-sources-panel-with-document-browsing.md] - Tab structure
- [Source: _bmad-output/implementation-artifacts/5-2-artifacts-browsing-in-side-panel.md] - Epic 5 pattern

### 🧠 Implementation Strategy & Decision Log

**Key Technical Decisions:**

1. **Custom Event vs. Global Store**
   - Decision: Use browser CustomEvent dispatched from use-learner-chat.ts
   - Rationale: Decoupled architecture, no tight coupling between chat and progress components
   - Alternative rejected: Global store (overkill for transient 3-second state)
   - Alternative rejected: Direct state mutation (violates React patterns)

2. **Timer Management**
   - Decision: Individual setTimeout for each objective with cleanup in useEffect
   - Rationale: Simple, reliable, handles multiple objectives naturally
   - Alternative rejected: Single interval polling (less efficient, complex logic)
   - Alternative rejected: requestAnimationFrame (overkill for simple timer)

3. **Glow Styling Approach**
   - Decision: Tailwind ring utilities (ring-2 ring-primary/50) + animate-pulse
   - Rationale: Consistent with existing highlight patterns, accessible, performant
   - Alternative rejected: Custom keyframe animation (reinventing wheel)
   - Alternative rejected: Box shadow (ring is more subtle and professional)

4. **Event Payload Structure**
   - Decision: Reuse existing ObjectiveCheckedEvent type, no new types needed
   - Rationale: Event already contains all required data (objective_id, text, evidence)
   - No changes to backend event emission needed

5. **Component State Location**
   - Decision: Local state in ObjectiveProgressList, not global learner-store
   - Rationale: Glow is transient (3 seconds), component-scoped, no cross-component needs
   - Reduces complexity, easier to test, no state pollution

6. **Backward Compatibility**
   - Decision: Glow is optional enhancement, no breaking changes
   - Rationale: If event missed or glow fails, progress still displays correctly
   - Graceful degradation: Users still get toast notification + ambient bar update

**Implementation Approach:**

**Phase 1: Event Listener Setup (ObjectiveProgressList)**
```typescript
// Map tracks objective_id -> timestamp of when glow started
const [recentlyCheckedObjectiveIds, setRecentlyCheckedObjectiveIds] =
  useState<Map<string, number>>(new Map());

useEffect(() => {
  const handleObjectiveChecked = (event: CustomEvent) => {
    const { objective_id } = event.detail;

    setRecentlyCheckedObjectiveIds(prev =>
      new Map(prev).set(objective_id, Date.now())
    );

    setTimeout(() => {
      setRecentlyCheckedObjectiveIds(prev => {
        const next = new Map(prev);
        next.delete(objective_id);
        return next;
      });
    }, GLOW_DURATION_MS);
  };

  window.addEventListener('objective_checked', handleObjectiveChecked as EventListener);

  return () => {
    window.removeEventListener('objective_checked', handleObjectiveChecked as EventListener);
  };
}, []);
```

**Phase 2: Custom Event Dispatch (use-learner-chat)**
```typescript
// Existing SSE event handler
if (event.type === 'objective_checked') {
  const data = JSON.parse(event.data);

  // Existing: Toast + cache invalidation
  toast.success(t('progress.objectiveCompleted'));
  queryClient.invalidateQueries({
    queryKey: learningObjectivesKeys.progressByNotebook(notebookId),
  });

  // NEW: Dispatch custom event for glow
  window.dispatchEvent(new CustomEvent('objective_checked', { detail: data }));
}
```

**Phase 3: Conditional Rendering (ObjectiveItem)**
```typescript
<div
  className={cn(
    "flex items-start gap-3 p-3 rounded-lg transition-all duration-150",
    isCompleted && "bg-success/10",
    hasWarmGlow && "ring-2 ring-primary/50 animate-pulse"
  )}
>
```

### Project Structure Notes

**Alignment with Project:**
- Minimal changes to existing codebase (2 files modified)
- Extends existing SSE event handling pattern
- Follows established local state pattern from Story 5.1
- Completes Epic 5 feature set

**No Breaking Changes:**
- All changes are additive enhancements
- Existing progress display unchanged
- Existing SSE handling extended (not replaced)
- Backward compatible: Works with or without glow

**Potential Conflicts:**
- **None** - Story 5.3 is the final story in Epic 5
- No other stories depend on this enhancement
- Glow is isolated to ObjectiveProgressList component

**Design Decisions:**
- 3-second glow duration (UX spec requirement)
- CustomEvent for decoupled communication
- Local state for transient glow tracking
- Ring + pulse animation for visual consistency
- No new i18n keys needed (all strings exist)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - No blocking issues encountered.

### Completion Notes List

**Task 1: Warm Glow Animation for Recently Checked Objectives**
- Extended ObjectiveProgressList component to track `recentlyCheckedObjectiveIds` state (Map<string, number>)
- Implemented SSE event listener for `objective_checked` custom event
- Added auto-removal timer (3 seconds) using setTimeout with proper cleanup in useEffect
- Applied conditional CSS classes: `ring-2 ring-primary/50 animate-pulse` when `hasWarmGlow` is true
- Updated ObjectiveItem to accept `hasWarmGlow` prop
- Modified useLearnerChat hook to dispatch custom window event when objective_checked SSE event received
- All 5 warm glow tests passing (11/11 total tests in ObjectiveProgressList.test.tsx)

**Task 2: Verify Progress Tab Integration**
- Verified Progress tab in SourcesPanel renders ObjectiveProgressList (line 224)
- Confirmed useLearnerObjectivesProgress hook fetches data with auto-refresh (refetchOnWindowFocus: true, staleTime: 30s)
- Validated checklist display with CheckCircle2/Circle icons for checked/unchecked states
- Verified "X of Y" summary and Radix Progress bar display (lines 147-157)
- Confirmed AmbientProgressBar increments on objective completion via TanStack Query cache invalidation
- No code changes required - all functionality already implemented in Story 4.4 and 5.1

**Task 3: Testing & Validation**
- Added 5 comprehensive test cases for warm glow animation:
  1. Applies warm glow when objective_checked event fired
  2. Removes warm glow after 3 seconds
  3. Supports multiple objectives glowing simultaneously
  4. Does not glow objectives that were already completed
  5. Cleans up event listeners on unmount
- All tests passing (11/11 total in ObjectiveProgressList.test.tsx)
- No backend changes required (purely frontend enhancement)

**Technical Implementation:**
- Used Map data structure for efficient O(1) lookup and independent timer management per objective
- Implemented proper event listener cleanup to prevent memory leaks
- Applied Tailwind CSS ring utilities for consistent styling with existing highlight patterns
- Extended SSE event flow: backend emits → useLearnerChat dispatches custom event → ObjectiveProgressList listens
- Maintained separation of concerns: glow state local to component, not in global store

**All Acceptance Criteria Met:**
- ✅ AC1: Progress tab lists all objectives with checked/unchecked status
- ✅ AC2: Summary shows "X of Y" completed with progress bar
- ✅ AC3: Newly checked objectives show 3-second warm glow animation
- ✅ AC4: Ambient progress bar increments in real-time on objective completion

### File List

**Frontend Files Modified:**
- frontend/src/components/learner/ObjectiveProgressList.tsx
- frontend/src/lib/hooks/use-learner-chat.ts
- frontend/src/components/learner/__tests__/ObjectiveProgressList.test.tsx

**Backend Files Modified:**
- None (Story 5.3 is frontend-only)

**Configuration Files Modified:**
- _bmad-output/implementation-artifacts/sprint-status.yaml

