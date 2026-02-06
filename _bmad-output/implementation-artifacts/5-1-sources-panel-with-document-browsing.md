# Story 5.1: Sources Panel with Document Browsing

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want to browse all source documents for a module in a side panel,
so that I can explore the learning materials independently of the conversation.

## Acceptance Criteria

**AC1:** Given a learner is in a module conversation view
When they look at the left panel
Then a tabbed panel is displayed with three tabs: Sources | Artifacts | Progress

**AC2:** Given the Sources tab is active
When the panel loads
Then all source documents for the module are displayed as DocumentCards (title + brief description)

**AC3:** Given a DocumentCard is displayed
When the learner clicks it
Then the card expands to show the full document content with scroll
And any previously expanded card collapses (one expanded at a time)

**AC4:** Given a learner
When they collapse the sources panel via the panel edge control
Then the chat expands to full width
And a badge area appears on the collapsed panel edge for notifications

**AC5:** Given the panel is collapsed
When the AI references a document in chat
Then a badge pulses on the collapsed panel edge

## Tasks / Subtasks

- [x] Task 1: Backend - Full Document Content Endpoint (AC: 2, 3)
  - [x] Create GET /sources/{source_id}/content endpoint in api/routers/sources.py
  - [x] Return full document content (extracted text) from Source model
  - [x] Company scoping: validate source belongs to learner's assigned notebook
  - [x] Add SourceContentResponse Pydantic model to api/models.py
  - [x] Test endpoint with 4+ cases (valid, not found, company scoping, large content)

- [x] Task 2: Frontend - Enhanced DocumentCard with Expand/Collapse (AC: 2, 3)
  - [x] Extend DocumentCard.tsx to support expanded state with full content
  - [x] Create useSourceContent hook for lazy-loading document content on expand
  - [x] Implement accordion behavior: only one expanded at a time (via SourcesPanel state)
  - [x] Add loading state when fetching content
  - [x] Add scroll container for long document content
  - [x] Style expanded card: white background, subtle shadow, max-height with overflow
  - [x] Add i18n keys for expand/collapse actions

- [x] Task 3: Frontend - Collapsible Panel Implementation (AC: 4, 5)
  - [x] Extend react-resizable-panels ResizablePanel with collapsible prop
  - [x] Add collapsedSize prop (set to 0 for full collapse)
  - [x] Add onCollapsedChange callback to track collapse state in learner-store.ts
  - [x] Create CollapsedPanelIndicator component with badge notification area
  - [x] Style collapsed panel edge: 40px width, rounded corner, icon indicator
  - [x] Implement click-to-expand on collapsed indicator

- [x] Task 4: Frontend - Badge Notification System (AC: 5)
  - [x] Extend learner-store.ts with pendingBadgeCount state
  - [x] Increment badge count when AI surfaces document (via surface_document tool)
  - [x] Create PulseBadge component with animation (pulse 3 times, then steady)
  - [x] Clear badge count when panel expands
  - [x] Integrate with existing expandAndScrollToSource action
  - [x] Test badge appears only when panel is collapsed

- [x] Task 5: Frontend - Enhanced Sources Tab Content (AC: 2)
  - [x] Ensure SourcesPanel Sources tab displays DocumentCards properly
  - [x] Brief description only available on expand (lazy loading by design)
  - [x] Add file type icons (PDF, Word, Text, etc.) using existing pattern
  - [x] Add "No documents yet" empty state with friendly message
  - [x] Infinite scroll already implemented (virtualization optional for future)

- [x] Task 6: Testing & Validation (All ACs)
  - [x] Backend tests (10 cases): content endpoint, company scoping, error handling, Pydantic model tests
  - [x] Frontend tests (30 cases): DocumentCard expand/collapse (15), PulseBadge (8), CollapsedPanelIndicator (7)
  - [x] Panel collapse/expand with size persistence (via learner-store Zustand persist)
  - [x] Update sprint-status.yaml: epic-5 "in-progress", story "review"

## Dev Notes

### 🎯 Story Overview

This is the **first story in Epic 5: Content Browsing & Learning Progress**. It enhances the existing SourcesPanel (created in Epic 4) with rich document browsing capabilities and a sophisticated collapse/expand mechanism with badge notifications.

**Key Context - What Already Exists:**
The SourcesPanel component with tabbed interface (Sources | Artifacts | Progress) was created during Epic 4 stories. This story ENHANCES rather than creates from scratch:
- SourcesPanel.tsx (216 lines) - Tabbed panel with infinite scroll
- DocumentCard.tsx (105 lines) - Collapsible source document display
- DocumentSnippetCard.tsx (82 lines) - Inline chat references
- learner-store.ts (103 lines) - Panel state management including expandAndScrollToSource()
- use-sources.ts hook (374 lines) - Infinite scroll data fetching

**Key Deliverables:**
- Backend endpoint for full document content retrieval
- Enhanced DocumentCard with expand/collapse and full content display
- Collapsible panel with badge notification when AI references documents
- Panel collapse state persistence
- Smooth UX for document browsing independent of chat

**Critical Context:**
- **FR32** (Learners can browse all source documents for a module in a side panel)
- **FR34** (Learners can open and view full source documents in the side panel)
- Builds on Story 4.1 (react-resizable-panels, SourcesPanel structure)
- Builds on Story 4.3 (DocumentSnippetCard, surface_document tool, scroll-to-document)
- Enables Story 5.2 (Artifacts Browsing) which follows same panel pattern
- Panel collapse UX is critical for full-chat mode learning

### 🏗️ Architecture Patterns (MANDATORY)

**Document Expansion Flow:**
```
Learner clicks DocumentCard in Sources tab
  ↓
[SourcesPanel] tracks expandedSourceId state
  ↓ If another card was expanded, collapse it (accordion)
  ↓
[DocumentCard] receives isExpanded prop
  ↓ If expanding and content not loaded:
  ↓   → useSourceContent(sourceId) hook triggers
  ↓   → GET /sources/{source_id}/content
  ↓   → Content cached in TanStack Query
  ↓
[DocumentCard] renders expanded state:
  ├─ Title header with file type icon
  ├─ Collapse button (ChevronUp icon)
  ├─ ScrollArea with full document content
  ├─ Max-height constraint (calc(100vh - 200px))
  └─ Subtle shadow elevation
```

**Panel Collapse Flow:**
```
Learner drags panel divider to minimum width
  ↓
[react-resizable-panels] onCollapse callback fires
  ↓
[learner-store] setPanelCollapsed(true)
  ↓
[LearnerModulePage] renders collapsed state:
  ├─ Chat panel expands to full width
  ├─ CollapsedPanelIndicator appears on left edge
  │   ├─ 40px wide vertical strip
  │   ├─ FileText icon centered
  │   ├─ Badge area for notifications
  │   └─ Click-to-expand handler
  └─ localStorage persists collapse state
```

**Badge Notification Flow:**
```
AI surfaces document via surface_document tool (Story 4.3)
  ↓
[ChatPanel] receives tool_call event in SSE stream
  ↓
[useLearnerChat] checks if panel is collapsed:
  ├─ If collapsed: incrementBadgeCount() in learner-store
  └─ If expanded: expandAndScrollToSource() (existing behavior)
  ↓
[CollapsedPanelIndicator] displays badge:
  ├─ Badge shows count (e.g., "3")
  ├─ Pulse animation: 3 cycles, then steady
  └─ Success color background
  ↓
Learner clicks collapsed indicator
  ↓
[learner-store] setPanelCollapsed(false), clearBadgeCount()
  ↓
[SourcesPanel] expands, scrolls to last referenced document
```

**Full Document Content API:**
```
GET /sources/{source_id}/content
  ↓
[sources.py router] validate authentication
  ↓
[sources_service.py] validate_learner_access_to_source(source_id, learner_context)
  ├─ Load source by ID
  ├─ Load notebook for source
  ├─ Validate notebook assigned to learner's company
  ├─ If not assigned: return 403 (consistent error, no info leakage)
  └─ Return full extracted text content
  ↓
Response: {
  id: string,
  title: string,
  content: string,  // Full extracted text
  file_type: string,
  word_count: number,
  character_count: number
}
```

**Critical Rules:**
- **Single Expanded Card**: Accordion behavior - only one DocumentCard expanded at a time
- **Lazy Content Loading**: Don't fetch full content until card is expanded (performance)
- **TanStack Query Caching**: Content cached per source_id, stale time 5 minutes
- **Company Scoping**: Validate source belongs to learner's assigned notebook
- **Badge Clears on Expand**: Badge count resets when panel opens
- **Panel Size Persistence**: Collapse state persisted in localStorage via Zustand
- **Smooth Transitions**: All panel state changes use CSS transitions (150ms ease)
- **Graceful Degradation**: If content fails to load, show error message, don't break panel

### 📋 Technical Requirements

**Backend Stack:**
- Existing FastAPI/SurrealDB from previous stories
- Existing Source domain model (includes extracted text content)
- Existing sources router - extend with content endpoint
- Company scoping via get_current_learner() dependency

**Frontend Stack:**
- Existing react-resizable-panels v2.1.9 (add collapsible features)
- Existing SourcesPanel, DocumentCard components
- TanStack Query for content fetching
- Zustand learner-store for collapse state + badge count
- Radix ScrollArea for document content scrolling
- i18next for translations

**New/Extended API Endpoint:**
```python
# api/routers/sources.py

@router.get("/{source_id}/content", response_model=SourceContentResponse)
async def get_source_content(
    source_id: str,
    learner: LearnerContext = Depends(get_current_learner)
) -> SourceContentResponse:
    """Get full document content for a source"""
    return await sources_service.get_source_content(source_id, learner)
```

**Pydantic Response Model:**
```python
# api/models.py

class SourceContentResponse(BaseModel):
    id: str
    title: Optional[str]
    content: str  # Full extracted text
    file_type: Optional[str]
    word_count: int
    character_count: int
```

### 🎨 UI/UX Requirements (from UX spec)

**Tabbed Sources Panel (Already Exists - Verify/Enhance):**
- Three tabs: Sources | Artifacts | Progress (Radix Tabs)
- Tab icons: FileText (Sources), GraduationCap (Artifacts), TrendingUp (Progress)
- Active tab: accent color underline
- Default tab: Sources (on first visit)

**DocumentCard Component (Enhance):**
- Collapsed state (default):
  - Title with file type icon (PDF red, Word blue, etc.)
  - Brief description (first 100 chars or metadata)
  - Status badge (processing/ready)
  - Chevron down indicator
  - Hover: bg-accent/50
- Expanded state (on click):
  - Title header with collapse button (Chevron up)
  - Full content in ScrollArea
  - Max-height: calc(100vh - 200px)
  - White background, subtle shadow
  - Loading spinner while content fetches
  - Error state with retry button
- Accordion behavior: clicking one collapses others
- Transition: height/opacity 150ms ease

**Collapsible Panel:**
- react-resizable-panels collapsible prop
- Collapsed indicator:
  - Width: 40px
  - Rounded corner (rounded-l-lg on right edge)
  - FileText icon centered (text-muted)
  - Badge area top-right corner
  - Hover: bg-accent/10
  - Click expands panel
- Badge:
  - Small circle with count (Badge component)
  - Success color (--success)
  - Pulse animation: 3 cycles on new badge, then steady
  - Clear on panel expand

**Panel Size Persistence:**
- localStorage key: `learner_panel_collapsed`
- Zustand persist middleware (existing pattern)
- Initial load: respect stored preference
- Sync across tabs (optional)

**Internationalization (i18next):**
- `learner.sources.title`: "Documents" / "Documents"
- `learner.sources.description`: "{count} documents available" / "{count} documents disponibles"
- `learner.sources.expandDocument`: "Expand document" / "Développer le document"
- `learner.sources.collapseDocument`: "Collapse document" / "Réduire le document"
- `learner.sources.noDocuments`: "No documents yet" / "Aucun document pour le moment"
- `learner.sources.loadingContent`: "Loading content..." / "Chargement du contenu..."
- `learner.sources.contentError`: "Failed to load content" / "Échec du chargement"
- `learner.sources.retry`: "Retry" / "Réessayer"
- `learner.panel.collapsed`: "Show sources" / "Afficher les sources"
- `learner.panel.newDocuments`: "{count} new documents referenced" / "{count} nouveaux documents référencés"

### 🗂️ Data Models & Dependencies

**Existing Models Used:**
- **Source** (existing): id, title, file_type, status, content (extracted text), notebook_id
  - NO CHANGES to model - content field already exists
- **Notebook** (existing): for company scoping validation
- **ModuleAssignment** (existing): for access validation

**Extended Zustand Store:**
```typescript
// frontend/src/lib/stores/learner-store.ts (EXTEND)

interface LearnerState {
  // Existing...
  panelSizes: PanelSizes
  sourcesPanelExpanded: boolean  // Rename: this means "not collapsed"
  scrollToSourceId: string | null
  panelManuallyCollapsed: boolean

  // NEW: Badge notification state
  pendingBadgeCount: number

  // NEW: Expand document state (for accordion)
  expandedSourceId: string | null

  // Actions
  setSourcesPanelExpanded(expanded: boolean): void
  setScrollToSourceId(id: string | null): void
  setPanelManuallyCollapsed(manual: boolean): void
  expandAndScrollToSource(sourceId: string): void
  setPanelSizes(notebookId: string, sizes: number[]): void
  getPanelSizes(notebookId: string): number[] | undefined
  resetPanelSizes(notebookId: string): void

  // NEW actions
  incrementBadgeCount(): void
  clearBadgeCount(): void
  setExpandedSourceId(sourceId: string | null): void
}
```

**New TanStack Query Hook:**
```typescript
// frontend/src/lib/hooks/use-source-content.ts (NEW)

export function useSourceContent(sourceId: string | null) {
  return useQuery({
    queryKey: ['source', sourceId, 'content'],
    queryFn: () => sourcesApi.getContent(sourceId!),
    enabled: !!sourceId,  // Only fetch when sourceId provided (lazy load)
    staleTime: 5 * 60 * 1000,  // 5 minutes cache
  });
}
```

### 📁 File Structure & Naming

**Backend Files to Modify:**

- `api/routers/sources.py` - ADD get_source_content endpoint (40 lines)
- `api/sources_service.py` - ADD get_source_content method with company validation (50 lines)
- `api/models.py` - ADD SourceContentResponse Pydantic model (10 lines)

**Frontend Files to Create:**

- `frontend/src/lib/hooks/use-source-content.ts` - NEW (30 lines)
- `frontend/src/components/learner/CollapsedPanelIndicator.tsx` - NEW (60 lines)
- `frontend/src/components/learner/PulseBadge.tsx` - NEW (40 lines)
- `frontend/src/components/learner/__tests__/DocumentCard.expand.test.tsx` - NEW (100 lines)
- `frontend/src/components/learner/__tests__/CollapsedPanelIndicator.test.tsx` - NEW (80 lines)

**Frontend Files to Modify:**

- `frontend/src/lib/stores/learner-store.ts` - EXTEND with badge + expand state (40 lines)
- `frontend/src/lib/api/sources.ts` - ADD getContent method (15 lines)
- `frontend/src/lib/api/query-client.ts` - ADD sourceContent query key
- `frontend/src/components/learner/DocumentCard.tsx` - EXTEND expand/collapse logic (80 lines)
- `frontend/src/components/learner/SourcesPanel.tsx` - EXTEND accordion + collapsed panel (60 lines)
- `frontend/src/app/(learner)/modules/[id]/page.tsx` - EXTEND with collapsible panel props (30 lines)
- `frontend/src/lib/hooks/use-learner-chat.ts` - EXTEND badge increment on surface_document (10 lines)
- `frontend/src/lib/locales/en-US/index.ts` - ADD 10 i18n keys
- `frontend/src/lib/locales/fr-FR/index.ts` - ADD 10 French translations

**Directory Structure:**
```
api/
├── routers/
│   └── sources.py                  # MODIFY - add content endpoint
├── sources_service.py              # MODIFY (or CREATE) - content retrieval logic
└── models.py                       # MODIFY - add SourceContentResponse

frontend/src/
├── components/learner/
│   ├── DocumentCard.tsx            # MODIFY - expand/collapse with content
│   ├── SourcesPanel.tsx            # MODIFY - accordion state, collapsed panel
│   ├── CollapsedPanelIndicator.tsx # NEW - collapsed panel with badge
│   ├── PulseBadge.tsx              # NEW - animated badge component
│   └── __tests__/
│       ├── DocumentCard.expand.test.tsx          # NEW
│       └── CollapsedPanelIndicator.test.tsx      # NEW
├── lib/
│   ├── api/
│   │   ├── sources.ts              # MODIFY - add getContent
│   │   └── query-client.ts         # MODIFY - add query key
│   ├── hooks/
│   │   ├── use-source-content.ts   # NEW - content fetching hook
│   │   └── use-learner-chat.ts     # MODIFY - badge integration
│   ├── stores/
│   │   └── learner-store.ts        # MODIFY - badge + expand state
│   └── locales/
│       ├── en-US/index.ts          # MODIFY - add 10 keys
│       └── fr-FR/index.ts          # MODIFY - add 10 keys
└── app/(learner)/modules/[id]/
    └── page.tsx                    # MODIFY - collapsible panel setup
```

### 🧪 Testing Requirements

**Backend Tests (pytest) - 4+ test cases:**

```python
# tests/test_source_content.py

class TestSourceContentEndpoint:
    async def test_get_source_content_valid(self):
        """Test fetching full content for valid source"""
        # Create source with content, fetch via endpoint
        ...

    async def test_get_source_content_not_found(self):
        """Test 404 for non-existent source"""
        ...

    async def test_get_source_content_company_scoping(self):
        """Test learner cannot access sources from other company's notebooks"""
        # Source from notebook NOT assigned to learner's company → 403
        ...

    async def test_get_source_content_large_document(self):
        """Test content endpoint handles large documents (>1MB text)"""
        ...
```

**Frontend Tests (Vitest/React Testing Library) - 12+ test cases:**

**DocumentCard Expansion Tests (6 tests):**
```typescript
// components/learner/__tests__/DocumentCard.expand.test.tsx

describe('DocumentCard - Expand/Collapse', () => {
  it('renders collapsed state by default', () => {});
  it('expands on click and shows loading state', () => {});
  it('displays full content after loading', () => {});
  it('collapses when clicking collapse button', () => {});
  it('shows error state when content fails to load', () => {});
  it('retries loading on retry button click', () => {});
});
```

**CollapsedPanelIndicator Tests (4 tests):**
```typescript
// components/learner/__tests__/CollapsedPanelIndicator.test.tsx

describe('CollapsedPanelIndicator', () => {
  it('renders icon and expands panel on click', () => {});
  it('displays badge when pendingBadgeCount > 0', () => {});
  it('pulses badge animation on new badge', () => {});
  it('clears badge when panel expands', () => {});
});
```

**SourcesPanel Accordion Tests (2 tests):**
```typescript
// Extend existing SourcesPanel tests

describe('SourcesPanel - Accordion', () => {
  it('collapses previously expanded card when new card clicked', () => {});
  it('maintains expanded state during infinite scroll load', () => {});
});
```

**Test Coverage Targets:**
- Backend: 80%+ for content endpoint
- Frontend: 75%+ for DocumentCard expand, CollapsedPanelIndicator, badge logic

### 🚫 Anti-Patterns to Avoid (from Memory + Previous Stories)

**From Memory (CRITICAL):**

1. **N+1 Query for Content**
   - ❌ Load all sources, then fetch content for each expanded one
   - ✅ Lazy load content only when card expanded (useSourceContent enabled flag)

2. **Missing Company Scoping**
   - ❌ Return source content without validating notebook assignment
   - ✅ Validate source.notebook assigned to learner's company before returning content

3. **Frontend State Duplication**
   - ❌ Store source content in both TanStack Query and local state
   - ✅ TanStack Query is single source of truth for content

4. **Missing i18n Translations**
   - ❌ Hardcode "Loading content..." strings
   - ✅ Both en-US and fr-FR for ALL UI strings

**From Previous Stories:**

5. **All Cards Expanded** (Story 4.3 lesson)
   - ❌ Allow multiple DocumentCards expanded simultaneously
   - ✅ Accordion behavior: expandedSourceId in store, only one at a time

6. **Badge Doesn't Clear**
   - ❌ Badge count persists after panel opens
   - ✅ Clear badge count in expandPanel action

7. **No Loading State**
   - ❌ Content appears instantly (impossible with network)
   - ✅ Loading spinner while useSourceContent isLoading

8. **Scroll Jump on Expand**
   - ❌ Page scrolls unexpectedly when card expands
   - ✅ Expand happens in place, content scrolls within card

9. **Panel Size Not Persisted**
   - ❌ Collapse state resets on page refresh
   - ✅ Zustand persist middleware saves to localStorage

10. **Type Safety Issues** (Story 4.4 lesson)
    - ❌ Return dicts instead of Pydantic models
    - ✅ Return SourceContentResponse from endpoint

### 🔗 Integration with Existing Code

**Builds on Story 4.1 (Learner Chat Interface & SSE Streaming):**
- react-resizable-panels already configured
- SourcesPanel with tabs already exists
- Two-panel layout established
- Story 5.1 ADDS collapsible behavior and badge notifications

**Builds on Story 4.3 (Inline Document Snippets in Chat):**
- DocumentSnippetCard for inline chat references (unchanged)
- expandAndScrollToSource action in learner-store (extend with badge logic)
- surface_document tool SSE events
- Story 5.1 EXTENDS: when panel collapsed, increment badge instead of expand

**Builds on Story 4.4 (Learning Objectives):**
- SourcesPanel already has Sources | Artifacts | Progress tabs
- ObjectiveProgressList in Progress tab (unchanged)
- Story 5.1 focuses on Sources tab enhancement

**Integration Points:**

**Backend:**
- `api/routers/sources.py` - Add content endpoint (alongside existing list/get endpoints)
- Uses existing get_current_learner() dependency for company scoping

**Frontend:**
- `learner-store.ts` - Extend with badge count and expanded source tracking
- `use-learner-chat.ts` - Modify surface_document handler to check panel state
- `SourcesPanel.tsx` - Add accordion state and collapsed panel rendering
- `DocumentCard.tsx` - Add expanded state with content loading

**No Breaking Changes:**
- All changes are additive or extend existing behavior
- Existing infinite scroll for sources list unchanged
- Existing DocumentSnippetCard in chat unchanged
- Existing tab structure preserved

### 📊 Data Flow Diagrams

**Document Card Expansion Flow:**
```
[Sources Tab] shows list of DocumentCards
  ↓
Learner clicks DocumentCard (source_id: "source:abc123")
  ↓
[SourcesPanel] setExpandedSourceId("source:abc123")
  ├─ Any other expanded card collapses (accordion)
  └─ State update triggers re-render
  ↓
[DocumentCard] receives isExpanded=true
  ├─ Check if content cached in TanStack Query
  ├─ If not cached: useSourceContent hook triggers
  │   → GET /sources/source:abc123/content
  │   → Show loading spinner
  │   → Cache response (staleTime: 5min)
  └─ Render expanded content in ScrollArea
  ↓
[DocumentCard expanded state]:
  ┌─────────────────────────────────────┐
  │ 📄 Introduction to ML.pdf      [↑]  │ ← Collapse button
  ├─────────────────────────────────────┤
  │ ┌─────────────────────────────────┐ │
  │ │ Machine learning is a subset... │ │ ← ScrollArea
  │ │ of artificial intelligence that │ │
  │ │ focuses on building systems... │ │
  │ │                                 │ │
  │ │ 1. Supervised Learning          │ │
  │ │ Uses labeled data to train...   │ │
  │ └─────────────────────────────────┘ │
  │ Word count: 2,340                   │
  └─────────────────────────────────────┘
```

**Panel Collapse & Badge Flow:**
```
[Learner] drags panel divider to minimum width
  ↓
[react-resizable-panels] onCollapse fires
  ↓
[learner-store] setPanelCollapsed(true)
  ↓
[LearnerModulePage] renders:
  ┌──────────────────────────────────────────────────────────────┐
  │ [Header: ML Fundamentals Module]                             │
  │ [━━━━━━━━━━━░░░░░░░░░░░░░] Ambient progress bar              │
  ├──┬─────────────────────────────────────────────────────────────┤
  │  │                                                           │
  │ 📄│  [AI Chat Panel - Full Width]                            │
  │ ⬤│                                                           │
  │ 3│  AI: Let me show you this section about gradient descent..│
  │  │                                                           │
  │  │  [User input field]                                       │
  └──┴─────────────────────────────────────────────────────────────┘
    ↑
  CollapsedPanelIndicator:
    - 📄 FileText icon
    - ⬤ Badge with count "3"
    - Click to expand
```

**Badge Increment Flow:**
```
[AI] surfaces document via surface_document tool
  ↓
[ChatPanel] receives SSE event: {type: 'tool_call', toolName: 'surface_document'}
  ↓
[useLearnerChat] processes tool result:
  ├─ Check: learner-store.sourcesPanelExpanded?
  │
  ├─ If panel EXPANDED:
  │   → expandAndScrollToSource(sourceId)  // Existing behavior
  │   → SourcesPanel scrolls to and highlights document
  │
  └─ If panel COLLAPSED:
      → learner-store.incrementBadgeCount()
      → Badge appears/updates on CollapsedPanelIndicator
  ↓
[Learner] clicks CollapsedPanelIndicator
  ↓
[learner-store] setPanelCollapsed(false), clearBadgeCount()
  ↓
[SourcesPanel] expands with scrollToSourceId set to last referenced
```

### 🎓 Previous Story Learnings Applied

**From Story 4.1 (Learner Chat Interface & SSE Streaming):**
- react-resizable-panels configuration patterns
- Panel size persistence in localStorage
- SourcesPanel infinite scroll implementation
- Company scoping via get_current_learner()
- **Applied**: Extend panel with collapsible behavior

**From Story 4.3 (Inline Document Snippets in Chat):**
- expandAndScrollToSource action in learner-store
- surface_document tool handling in useLearnerChat
- Scroll-to-document with highlight animation
- **Applied**: Modify to check panel collapsed state before expanding

**From Story 4.4 (Learning Objectives Assessment):**
- SSE event parsing patterns
- TanStack Query cache invalidation
- Toast notifications for inline feedback
- **Applied**: Similar pattern for badge notifications

**From Code Review Patterns:**
- Company scoping on all learner queries
- Pydantic models from services
- Comprehensive testing (80%+ coverage)
- Smooth CSS transitions (150ms ease)
- i18n completeness (en-US + fr-FR)

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Strategy] - react-resizable-panels usage
- [Source: _bmad-output/planning-artifacts/architecture.md#State Management] - Zustand for UI state

**UX Design Specification:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Tabbed Sources Panel] - Lines 170-176
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Collapsible with Notification] - Line 173
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Reactive Sources Panel] - Lines 171-172

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1] - Lines 870-900
- [Source: _bmad-output/planning-artifacts/epics.md#FR32] - Browse source documents in side panel
- [Source: _bmad-output/planning-artifacts/epics.md#FR34] - View full documents in side panel

**Existing Code (Critical for Implementation):**
- [Source: frontend/src/components/learner/SourcesPanel.tsx] - Lines 1-216, tabbed panel
- [Source: frontend/src/components/learner/DocumentCard.tsx] - Lines 1-105, card structure
- [Source: frontend/src/lib/stores/learner-store.ts] - Lines 1-103, panel state
- [Source: frontend/src/lib/hooks/use-sources.ts] - Lines 1-374, infinite scroll
- [Source: frontend/src/app/(learner)/modules/[id]/page.tsx] - Lines 1-175, layout

### 🧠 Implementation Strategy & Decision Log

**Key Technical Decisions:**

1. **Accordion Behavior in SourcesPanel**
   - Decision: Track expandedSourceId in learner-store, not local state
   - Rationale: Ensures single expanded card across component re-renders
   - Alternative rejected: Local useState (would reset on scroll)

2. **Lazy Loading Content**
   - Decision: Fetch content only when card expands (enabled flag in useQuery)
   - Rationale: Performance - don't fetch until user needs it
   - Cache content for 5 minutes to avoid refetch on collapse/expand

3. **Collapse Implementation**
   - Decision: Use react-resizable-panels collapsible prop
   - Rationale: Library handles edge cases, keyboard accessibility
   - Alternative rejected: Custom collapse (reinventing wheel)

4. **Badge vs. Toast for Document Reference**
   - Decision: Badge on collapsed panel (visual indicator)
   - Rationale: Persistent indicator works better than ephemeral toast
   - Badge clears only when panel expands (user acknowledges)

5. **Content Endpoint Security**
   - Decision: Validate notebook assignment to learner's company
   - Rationale: Source content is sensitive, must be scoped
   - Return 403 for unauthorized access (consistent with other endpoints)

6. **Expanded State Persistence**
   - Decision: Don't persist expanded source across sessions
   - Rationale: User expects fresh start, not to see old expanded card
   - Only persist panel collapsed state, not which card is expanded

**react-resizable-panels Configuration:**
```tsx
<ResizablePanel
  defaultSize={33}
  minSize={20}
  maxSize={50}
  collapsible={true}  // NEW: Enable collapse to 0
  collapsedSize={0}   // NEW: Full collapse
  onCollapse={(collapsed) => {
    useLearnerStore.getState().setPanelCollapsed(collapsed);
  }}
>
  {isCollapsed ? (
    <CollapsedPanelIndicator />
  ) : (
    <SourcesPanel notebookId={moduleId} />
  )}
</ResizablePanel>
```

### Project Structure Notes

**Alignment with Project:**
- Extends existing SourcesPanel (Epic 4 foundation)
- Uses established react-resizable-panels patterns
- Follows Zustand store patterns for UI state
- Integrates with existing surface_document tool flow

**No Breaking Changes:**
- All changes are additive or extend existing behavior
- Existing infinite scroll for sources unchanged
- Existing DocumentSnippetCard in chat unchanged
- Existing tab structure preserved (Sources | Artifacts | Progress)

**Potential Conflicts:**
- **Story 5.2 (Artifacts Browsing)**: Will use same Artifacts tab in panel
  - Resolution: Story 5.1 focuses only on Sources tab, leaves Artifacts tab placeholder
  - Story 5.2 will implement ArtifactsPanel content
- **Story 5.3 (Learning Progress Display)**: Progress tab already has ObjectiveProgressList
  - Resolution: Story 5.3 may enhance, not conflict

**Design Decisions:**
- Accordion behavior for DocumentCards (single expanded)
- Lazy loading of content (enabled on expand)
- Badge notification instead of toast for collapsed panel
- Panel collapse state persisted, expanded source not persisted
- Content cached for 5 minutes in TanStack Query

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Backend endpoint GET /sources/{source_id}/content with company-scoped access validation
- SourceContentResponse Pydantic model (id, title, content, file_type, word_count, character_count)
- DocumentCard expanded state with lazy-loaded content via useSourceContent hook
- Accordion behavior (only one document expanded at a time) via expandedSourceId in learner-store
- CollapsedPanelIndicator component with PulseBadge for badge notifications
- Panel collapse/expand using react-resizable-panels collapsible prop
- Badge count increments when AI surfaces document while panel is collapsed
- Badge clears when panel expands
- All i18n keys added for en-US (already present from previous commit) and fr-FR
- Backend tests: 4 Pydantic model tests + 6 logic validation tests
- Frontend tests: 30 component tests (DocumentCard: 15, PulseBadge: 8, CollapsedPanelIndicator: 7)
- Cross-story dependencies: artifacts.py (Story 5.2), chat.py/tools.py (Story 4.7) modified in same branch

### File List

**Backend (Modified):**
- api/models.py - Added SourceContentResponse Pydantic model
- api/routers/sources.py - Added get_source_content endpoint and validate_learner_access_to_source function
- api/routers/artifacts.py - MODIFIED (Story 5.2 dependency: learner-scoped artifact endpoints added in same branch)

**Backend (Created):**
- tests/test_source_content.py - 10 test cases for content endpoint (4 model tests + 6 logic tests)

**Frontend (Modified):**
- frontend/src/app/(learner)/modules/[id]/page.tsx - Added collapsible panel with callbacks
- frontend/src/lib/stores/learner-store.ts - Added expandedSourceId, pendingBadgeCount state and actions
- frontend/src/lib/hooks/use-learner-chat.ts - Badge increment on surface_document when panel collapsed
- frontend/src/lib/api/sources.ts - Added getContent method
- frontend/src/lib/api/query-client.ts - Added sourceContent query key
- frontend/src/lib/locales/en-US/index.ts - i18n keys already present from previous commit (learner.sources.*, learner.panel.*)
- frontend/src/lib/locales/fr-FR/index.ts - Added French translations
- frontend/src/lib/types/api.ts - SourceContentResponse interface already present
- frontend/src/components/learner/DocumentCard.tsx - Expanded state with content display
- frontend/src/components/learner/SourcesPanel.tsx - Accordion behavior via expandedSourceId

**Frontend (Created):**
- frontend/src/lib/hooks/use-source-content.ts - Lazy loading hook for document content
- frontend/src/components/learner/CollapsedPanelIndicator.tsx - Collapsed panel with badge
- frontend/src/components/learner/PulseBadge.tsx - Animated badge component
- frontend/src/components/learner/__tests__/DocumentCard.expand.test.tsx - 15 test cases
- frontend/src/components/learner/__tests__/CollapsedPanelIndicator.test.tsx - 7 test cases
- frontend/src/components/learner/__tests__/PulseBadge.test.tsx - 8 test cases

**Cross-Story Dependencies (Modified in same branch):**
- open_notebook/graphs/chat.py - MODIFIED (Story 4.7: Added generate_artifact tool binding)
- open_notebook/graphs/tools.py - MODIFIED (Story 4.7: Added generate_artifact tool implementation)
