# Story 3.2: Artifact Generation and Preview

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **admin**,
I want to generate artifacts (quizzes, podcasts, summaries, transformations) for a module,
So that learners have rich learning materials alongside the source documents.

## Acceptance Criteria

**Given** an admin is in the Generate step with uploaded documents
**When** they click "Generate Artifacts"
**Then** the system generates quizzes, podcasts, summaries using existing artifact generation workflows
**And** each artifact shows a spinner during generation and a preview button when complete

**Given** an artifact has been generated
**When** the admin clicks "Preview"
**Then** the artifact content is displayed for review

**Given** an admin reviews a generated artifact
**When** they want to regenerate it
**Then** they can click "Regenerate" to create a new version

**Given** all desired artifacts are generated
**When** the admin clicks "Next"
**Then** the pipeline advances to the Configure step

## Tasks / Subtasks

- [x] Task 1: Backend - Batch Artifact Generation Endpoint (AC: 1)
  - [x] Create POST `/api/notebooks/{notebook_id}/generate-artifacts` endpoint
  - [x] Orchestrate parallel generation (quizzes, summaries, transformations sync; podcasts async)
  - [x] Return batch generation status with command_ids for async jobs
  - [x] Use existing LangGraph workflows (quiz, transformation, podcast)

- [x] Task 2: Backend - Artifact Preview Endpoints (AC: 2)
  - [x] Extend GET `/api/artifacts/{artifact_id}` for all types
  - [x] Add type-specific formatting for preview display
  - [x] Include metadata (word count, duration, question count)
  - [x] Return structured preview data per artifact type

- [x] Task 3: Backend - Artifact Regeneration Endpoint (AC: 3)
  - [x] Create POST `/api/artifacts/{artifact_id}/regenerate` endpoint
  - [x] Delete old artifact and create new with same parameters
  - [x] Support partial regeneration (single artifact type)
  - [x] Return new artifact with processing status

- [x] Task 4: Frontend - Artifact Generation UI (AC: 1)
  - [x] Create ArtifactGenerationPanel component
  - [x] Add "Generate All" button with confirmation
  - [x] Show generation status per artifact type with progress indicators
  - [x] Display errors inline with retry option
  - [x] Integrate AsyncStatusBar for podcast generation

- [x] Task 5: Frontend - Artifact Preview Components (AC: 2)
  - [x] Create QuizPreview component (MCQ questions display)
  - [x] Create PodcastPreview component (audio player + transcript)
  - [x] Create SummaryPreview component (markdown renderer)
  - [x] Create TransformationPreview component (side-by-side comparison)
  - [x] Add preview modal/drawer with type-specific rendering

- [x] Task 6: Frontend - Pipeline Integration (AC: 4)
  - [x] Update ModuleCreationStepper for Generate step
  - [x] Add step validation (at least one artifact generated)
  - [x] Enable Next button when artifacts complete
  - [x] Add i18n keys for generation UI (en-US + fr-FR)

- [ ] Task 7: Testing (All ACs)
  - [ ] Unit tests for batch generation orchestration
  - [ ] Unit tests for preview endpoint logic
  - [ ] Integration test for full generation → preview → regenerate flow
  - [ ] Frontend component tests for artifact panels

## Dev Notes

### 🎯 Story Overview

This is the **second story in Epic 3: Module Creation & Publishing Pipeline**. It implements AI-powered artifact generation (quizzes, podcasts, summaries, transformations) with status tracking and preview functionality for the admin module creation workflow.

**Key Integration Points:**
- Extends Story 3.1's module creation pipeline (step 2 of 5-step flow)
- Reuses existing LangGraph workflows (quiz_generation.py, transformation.py, podcast via surreal-commands)
- Integrates with existing Artifact model for unified artifact tracking
- Follows async job pattern for long-running podcast generation
- Admin remains in control with preview and regenerate capabilities

### 🏗️ Architecture Patterns (MANDATORY)

**Three-Layer Backend Pattern:**
```
Router (api/routers/notebooks.py)
  ↓ validates request, applies auth
Service (api/artifact_generation_service.py)
  ↓ orchestrates LangGraph workflows
Domain Models (Quiz, Podcast, Transformation, Artifact)
  ↓ persistence operations
Database (SurrealDB via repository.py)
```

**Critical Rules:**
- Routers NEVER call database directly
- Services orchestrate multiple workflows in parallel
- All functions are `async def` with `await`
- Return Pydantic models from endpoints (never raw dicts)
- Log before raising HTTPException: `logger.error()` then `raise HTTPException`
- Use `Depends(require_admin)` for admin-only endpoints

**Frontend Architecture:**
- TanStack Query for ALL server state (artifacts, generation status, preview data)
- Zustand ONLY for UI state (active step, expanded previews, modal state)
- Never duplicate API data in Zustand
- Query keys: hierarchical `['modules', id, 'artifacts']`, `['artifacts', id, 'preview']`
- Polling for async jobs: conditional refetchInterval (2s when processing)

### 📋 Technical Requirements

**Backend Stack:**
- FastAPI 0.104+ with async endpoints
- Python 3.11+ with type hints
- LangGraph for workflow orchestration (quiz, transformation)
- Esperanto library for AI model provisioning
- surreal-commands for async podcast generation
- SurrealDB async driver for persistence
- Pydantic v2 for request/response validation
- Loguru for structured logging

**Frontend Stack:**
- Next.js 16 (App Router) with React 19
- TypeScript 5 with strict mode
- TanStack Query 5.83.0 for server state
- Zustand 5.0.6 for UI state only
- Shadcn/ui components (Card, Dialog, Button, Progress, Tabs)
- Tailwind CSS for styling
- React Markdown for summary/transformation display
- i18next for internationalization (BOTH en-US and fr-FR required)

**Artifact Types & Characteristics:**

| Type | Generation Method | Duration | Preview Requirements | Storage |
|------|-------------------|----------|----------------------|---------|
| **Quiz** | LangGraph sync workflow | 30-60s | MCQ questions with answers | Quiz + QuizQuestion models |
| **Podcast** | Async job (surreal-commands) | 2-5min | Audio player + transcript | Podcast model + audio file |
| **Summary** | LangGraph transformation | 10-30s | Markdown text display | Insight on Source |
| **Transformation** | LangGraph transformation | 10-30s | Markdown text display | Insight on Source |

### 🔒 Security & Permissions

**Admin-Only Operations:**
- Generate artifacts: `require_admin()` dependency
- Preview artifacts: `require_admin()` dependency
- Regenerate artifacts: `require_admin()` dependency
- Delete artifacts: `require_admin()` dependency

**Learner Operations (Not in this story, but relevant):**
- Learners will use artifacts via chat interface (Epic 4)
- Artifacts visible to learners only after module is published (Story 3.5)
- Learner access controlled via `get_current_learner()` dependency

**Authentication:**
- JWT tokens in httpOnly cookies (existing auth.py)
- No additional auth changes needed
- All endpoints protected by dependencies

### 🗂️ Database Schema

**Artifact Table (ALREADY EXISTS):**
```sql
-- No migration needed - existing Artifact model handles all types
-- Fields: artifact_id, artifact_type, notebook_id, title, created_at
-- Links generated artifacts to notebooks
```

**Quiz Table (ALREADY EXISTS):**
```sql
-- Quiz model with QuizQuestion relationships
-- Fields: id, notebook_id, source_id, title, questions[]
```

**Podcast Table (ALREADY EXISTS):**
```sql
-- Podcast model
-- Fields: id, notebook_id, title, audio_path, transcript
```

**Source Table (ALREADY EXISTS - for insights):**
```sql
-- Source.insights field stores summaries and transformations
-- No separate table for summaries/transformations
```

**Migration Strategy:**
- **NO NEW MIGRATION NEEDED** for this story
- Reuse existing Artifact, Quiz, Podcast models
- Insights stored as JSONB in Source.insights field
- Artifact model tracks all generated items centrally

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `api/artifact_generation_service.py` - Orchestrates batch artifact generation
- `api/models.py` - Add BatchGenerationRequest, BatchGenerationResponse, ArtifactPreviewResponse models

**MODIFY (extend existing):**
- `api/routers/notebooks.py` - Add `/notebooks/{id}/generate-artifacts` endpoint
- `api/routers/artifacts.py` - Extend for preview and regeneration
- `api/quiz_service.py` - Add batch generation support (if needed)
- `api/podcast_service.py` - Add batch job submission
- `api/transformations_service.py` - Add batch transformation support

**Frontend Files to Create:**

**NEW:**
- `frontend/src/components/admin/ArtifactGenerationPanel.tsx` - Main generation UI
- `frontend/src/components/admin/artifacts/QuizPreview.tsx` - Quiz display
- `frontend/src/components/admin/artifacts/PodcastPreview.tsx` - Audio player + transcript
- `frontend/src/components/admin/artifacts/SummaryPreview.tsx` - Markdown renderer
- `frontend/src/components/admin/artifacts/TransformationPreview.tsx` - Side-by-side view
- `frontend/src/components/admin/artifacts/ArtifactPreviewModal.tsx` - Modal wrapper
- `frontend/src/components/admin/AsyncStatusBar.tsx` - Persistent status indicator
- `frontend/src/lib/api/artifacts.ts` - API client methods for artifacts
- `frontend/src/lib/hooks/use-artifacts.ts` - TanStack Query hooks

**MODIFY:**
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add Generate step UI
- `frontend/src/app/(dashboard)/modules/[id]/page.tsx` - Integrate generation panel
- `frontend/src/lib/types/api.ts` - Add Artifact, Preview types
- `frontend/src/lib/locales/en-US/index.ts` - Add artifacts.* keys
- `frontend/src/lib/locales/fr-FR/index.ts` - Add artifacts.* keys (MANDATORY)

**Naming Conventions:**
- Python modules: `snake_case.py`
- Python classes: `PascalCase`
- Python functions: `async def snake_case()`
- TypeScript files: `kebab-case.ts` or `PascalCase.tsx` for components
- TypeScript interfaces: `PascalCase`
- TypeScript functions: `camelCase`
- Database tables: `lowercase` singular
- Database fields: `snake_case`
- API endpoints: `/api/resource-name` (kebab-case, plural)
- i18n keys: `section.key` (dot notation, lowercase)

### 🔄 Batch Generation Orchestration Pattern (CRITICAL)

**Parallel Generation with Async Handling:**

```python
async def generate_all_artifacts(notebook_id: str) -> BatchGenerationResponse:
    """
    Orchestrate parallel artifact generation:
    - Quiz: sync workflow (30-60s)
    - Summary: sync transformation (10-30s)
    - Custom transformations: sync (10-30s each)
    - Podcast: async job (2-5min, fire-and-forget)
    """

    # Get notebook sources
    sources = await get_notebook_sources(notebook_id)

    # Parallel sync operations (use asyncio.gather)
    quiz_task = generate_quiz(notebook_id, sources)
    summary_task = generate_summary(notebook_id, sources)
    transformation_tasks = [generate_transformation(s) for s in sources[:3]]

    results = await asyncio.gather(
        quiz_task,
        summary_task,
        *transformation_tasks,
        return_exceptions=True  # Don't fail entire batch if one fails
    )

    # Fire-and-forget podcast job
    podcast_command_id = await submit_podcast_job(notebook_id)

    # Return batch status
    return BatchGenerationResponse(
        quiz_status="completed" if results[0] else "error",
        summary_status="completed" if results[1] else "error",
        transformations_status="completed" if all(results[2:]) else "partial",
        podcast_status="processing",
        podcast_command_id=podcast_command_id,
        errors=[str(e) for e in results if isinstance(e, Exception)]
    )
```

**Frontend Polling Strategy:**
```typescript
// Poll batch status until all complete
const { data: artifacts } = useQuery({
  queryKey: ['modules', moduleId, 'artifacts'],
  queryFn: () => artifactsApi.listArtifacts(moduleId),
  refetchInterval: (data) => {
    const hasProcessing = data?.some(artifact =>
      artifact.status === 'processing' || artifact.command_id
    )
    return hasProcessing ? 2000 : false  // Poll every 2s if processing
  },
})

// Separate AsyncStatusBar for podcast
const { data: podcastStatus } = useQuery({
  queryKey: ['commands', podcastCommandId],
  queryFn: () => commandsApi.getStatus(podcastCommandId),
  enabled: !!podcastCommandId,
  refetchInterval: (data) => {
    return data?.status === 'running' ? 2000 : false
  }
})
```

### 🧪 Testing Requirements

**Backend Tests (pytest):**
- `tests/test_artifact_generation_service.py`
  - Test batch generation success (all artifacts)
  - Test partial failure (one artifact fails, others succeed)
  - Test async podcast job submission
  - Test error isolation (quiz failure doesn't block summary)
  - Test empty sources edge case

- `tests/test_artifact_preview.py`
  - Test preview endpoint for each artifact type
  - Test preview formatting (metadata extraction)
  - Test preview for non-existent artifact (404)
  - Test regeneration logic (delete old, create new)

**Frontend Tests:**
- Component tests for ArtifactGenerationPanel
- Component tests for each preview component
- Integration test for generate → poll → preview flow
- Mock API responses with MSW

**Test Coverage Targets:**
- Backend: 80%+ line coverage
- Frontend: 70%+ line coverage for critical paths

### 🚫 Anti-Patterns to Avoid

**From Previous Code Reviews (Epic 2 & Story 3.1):**

1. **Infinite Render Loop (CRITICAL)**
   - ❌ Calling functions directly in component body
   - ✅ Wrap side effects in useEffect with proper dependencies

2. **N+1 Query Problem (CRITICAL)**
   - ❌ Fetching artifacts in a loop
   - ✅ Use JOIN or array aggregation: `array::len(notebook.artifacts)` in SELECT

3. **Service Return Types**
   - ❌ Returning raw dicts from services
   - ✅ Always return Pydantic models for type safety

4. **Error Status Checking**
   - ❌ Frontend: `if (error)` without checking status
   - ✅ Frontend: `if (error?.response?.status === 403)` to distinguish 403 vs 404

5. **i18n Completeness**
   - ❌ Only adding en-US translations
   - ✅ ALWAYS add BOTH en-US and fr-FR for every UI string

6. **State Management**
   - ❌ Duplicating API data in Zustand store
   - ✅ Use TanStack Query for server state, Zustand only for UI state

7. **Hardcoded Strings**
   - ❌ `<Button>Generate Artifacts</Button>`
   - ✅ `<Button>{t('artifacts.generateAll')}</Button>`

8. **Missing Logging**
   - ❌ Raising HTTPException without logging
   - ✅ Always `logger.error()` before raising exception

9. **Blocking on Async**
   - ❌ Waiting for all artifacts before returning response
   - ✅ Fire-and-forget pattern for slow operations (podcasts)

10. **Cascading Failures**
    - ❌ One artifact failure breaks entire batch
    - ✅ Error isolation - use `asyncio.gather(return_exceptions=True)`

### 🔗 Integration with Existing Code

**Reuse These Existing Workflows:**

From `open_notebook/graphs/quiz_generation.py`:
- `generate_quiz_workflow()` - Full 5-step quiz generation
- Returns Quiz model with QuizQuestion list
- Auto-saves to database via StateDict

From `open_notebook/graphs/transformation.py`:
- `run_transformation()` - Single-node transformation
- Uses ai_prompter with Jinja2 templates
- Auto-saves insights to source

From `api/podcast_service.py`:
- `submit_podcast_job()` - Async job submission
- Returns command_id for polling
- Uses surreal-commands queue

From `open_notebook/domain/artifact.py`:
- `Artifact.create_for_artifact()` - Factory method
- Links artifact to notebook centrally
- Tracks all artifact types uniformly

**Extend These Existing Endpoints:**

`api/routers/artifacts.py` already has:
- GET `/artifacts` - List all artifacts (add filtering by notebook_id)
- GET `/artifacts/{id}` - Get single artifact (add preview formatting)
- DELETE `/artifacts/{id}` - Delete artifact (reuse for regeneration)

**New Endpoints to Add:**
- POST `/notebooks/{notebook_id}/generate-artifacts` - Batch generation
- POST `/artifacts/{artifact_id}/regenerate` - Regenerate single artifact
- GET `/artifacts/{artifact_id}/preview` - Get formatted preview data

### 📊 Data Flow Diagrams

**Batch Artifact Generation Flow:**
```
Admin (Browser)
  ↓ Clicks "Generate Artifacts"
  ↓ Confirmation dialog
Frontend (ArtifactGenerationPanel)
  ↓ POST /api/notebooks/{id}/generate-artifacts
Backend Router
  ↓ Depends(require_admin)
  ↓ Validates notebook exists
  ↓ Calls artifact_generation_service.generate_all_artifacts()
Service
  ↓ Parallel: asyncio.gather(quiz, summary, transformations)
  ↓ Async: submit_podcast_job()
  ↓ Returns BatchGenerationResponse
Frontend
  ↓ Shows progress indicators per artifact type
  ↓ AsyncStatusBar for podcast
  ↓ Polls ['modules', id, 'artifacts'] every 2s
Backend (async workflows)
  ↓ LangGraph generates quiz, summary, transformations
  ↓ surreal-commands processes podcast
  ↓ Updates Artifact.status on completion
Frontend
  ↓ Detects completion in poll
  ↓ Shows preview buttons ✓
  ↓ Stops polling when all complete
```

**Preview Flow:**
```
Admin (Browser)
  ↓ Clicks "Preview" button on artifact
Frontend (ArtifactPreviewModal)
  ↓ GET /api/artifacts/{id}/preview
Backend Router
  ↓ Depends(require_admin)
  ↓ Fetches artifact by ID
  ↓ Formats preview data per type:
      • Quiz → questions with correct answers marked
      • Podcast → audio URL + transcript
      • Summary → markdown content
      • Transformation → before/after comparison
  ↓ Returns ArtifactPreviewResponse
Frontend
  ↓ Renders type-specific preview component
  ↓ QuizPreview / PodcastPreview / SummaryPreview / TransformationPreview
Admin
  ↓ Reviews content
  ↓ Clicks "Regenerate" OR "Close"
```

**Regeneration Flow:**
```
Admin (Browser)
  ↓ Clicks "Regenerate" in preview modal
Frontend
  ↓ POST /api/artifacts/{id}/regenerate
Backend Router
  ↓ Depends(require_admin)
  ↓ Fetches artifact metadata (type, notebook_id, parameters)
  ↓ Deletes old artifact and Artifact tracker
  ↓ Re-invokes appropriate generation workflow
  ↓ Returns new artifact with "processing" status
Frontend
  ↓ Closes preview modal
  ↓ Shows spinner on regenerating artifact
  ↓ Resumes polling
  ↓ Preview button reappears when complete
```

### 🔍 Code Review Checklist

Before marking this story as "done", verify:

**Backend:**
- [ ] All endpoints have `Depends(require_admin)` dependency
- [ ] All endpoints have `response_model=SomeResponse` typing
- [ ] All exceptions logged with `logger.error()` before raising
- [ ] No direct database calls in routers (use domain models)
- [ ] Batch generation uses `asyncio.gather(return_exceptions=True)`
- [ ] Async podcast jobs fire-and-forget (don't block response)
- [ ] Error isolation - one failure doesn't cascade
- [ ] All functions are `async def` with `await`
- [ ] Preview formatting handles all artifact types
- [ ] Regeneration deletes old artifact before creating new

**Frontend:**
- [ ] TanStack Query for ALL API data (no Zustand duplication)
- [ ] Query keys follow hierarchy: `['modules', id, 'artifacts']`
- [ ] Mutations invalidate correct query keys
- [ ] Error handling checks `error?.response?.status`
- [ ] Loading states with Skeleton components
- [ ] Empty states with EmptyState component
- [ ] NO hardcoded strings (all via i18n)
- [ ] BOTH en-US and fr-FR translations added
- [ ] AsyncStatusBar for podcast generation
- [ ] Polling conditional (stops when complete)
- [ ] No infinite render loops (useEffect wrapping)

**Testing:**
- [ ] Backend: 15+ tests covering happy path + partial failures
- [ ] Frontend: Component tests for all preview components
- [ ] Integration test for full flow (generate + preview + regenerate)

**Documentation:**
- [ ] Dev Agent Record filled with agent model, files, notes
- [ ] This checklist completed in story file

### 🎓 Learning from Story 3.1

**Key patterns established in Story 3.1:**

**From Task 1-3 (Backend Implementation):**
- Async endpoint pattern: save → submit job → return command_id
- Fire-and-forget for long operations (document processing)
- Status polling via separate endpoint (GET /documents)
- Error tracking via command status (no schema changes)

**From Task 4-6 (Frontend Implementation):**
- Module creation stepper with 5 steps
- Document uploader with drag-and-drop
- Polling with conditional refetchInterval (2s when processing)
- Status indicators per item (uploading → processing → completed)
- Inline error display with retry button

**Apply these learnings:**
- Batch generation parallels document upload pattern
- Per-artifact status tracking (like per-document tracking)
- AsyncStatusBar for podcasts (similar to upload progress)
- Preview button appears when artifact.status === "completed"
- Regeneration reuses same workflow as initial generation

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend Layering]
- [Source: _bmad-output/planning-artifacts/architecture.md#LangGraph Workflows]
- [Source: _bmad-output/planning-artifacts/architecture.md#Async Job Processing]
- [Source: _bmad-output/planning-artifacts/architecture.md#Admin Pipeline UX]

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Module Creation & Publishing Pipeline]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2: Artifact Generation & Preview]

**PRD Requirements:**
- [Source: _bmad-output/planning-artifacts/prd.md#FR9: Artifact Generation]
- [Source: _bmad-output/planning-artifacts/prd.md#Admin Workflow]

**UX Design:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Pipeline Step 2]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Async Status Indicators]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Preview UI Patterns]

**Existing Code Patterns:**
- [Source: open_notebook/graphs/quiz_generation.py] - Quiz generation workflow
- [Source: open_notebook/graphs/transformation.py] - Transformation workflow
- [Source: api/podcast_service.py] - Async podcast job submission
- [Source: api/routers/artifacts.py lines 20-60] - Artifact listing and retrieval
- [Source: open_notebook/domain/artifact.py] - Artifact model and factory
- [Source: api/artifact_generation_service.py] - Batch generation orchestration (if exists)

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md] - Pipeline patterns, async jobs, polling
- [Source: _bmad-output/implementation-artifacts/2-3-module-lock-unlock-and-learner-visibility.md] - Code review fixes, N+1 prevention

**Configuration:**
- [Source: CONFIGURATION.md#LangGraph Settings]
- [Source: CONFIGURATION.md#AI Model Configuration]
- [Source: CONFIGURATION.md#Async Job Queue Settings]

### Project Structure Notes

**Alignment with Project:**
- Continues (dashboard) route group for admin pages (consistent with Story 3.1)
- Follows established domain/service/router layering (mandatory)
- Reuses existing LangGraph workflows (quiz, transformation, podcast)
- Extends Artifact model for centralized tracking (no new tables)
- Integrates with Story 3.1's ModuleCreationStepper (step 2 of 5)

**Potential Conflicts:**
- None detected - this story extends Story 3.1's pipeline cleanly
- Artifact generation already exists per-artifact, we're adding batch orchestration
- Preview functionality is new but follows existing patterns

**Design Decisions:**
- Batch generation uses parallel async execution (asyncio.gather)
- Podcast remains async via surreal-commands (fire-and-forget)
- Preview modal uses Shadcn Dialog with type-specific content
- Regeneration creates new artifact (doesn't modify existing)
- No new database migrations needed (reuse existing models)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Context Analysis Completed

**Architecture Analysis:**
- Analyzed complete architecture document for backend layering patterns (Router → Service → Domain)
- Extracted LangGraph workflow patterns (quiz_generation.py, transformation.py)
- Identified async job patterns for podcast generation via surreal-commands
- Documented AI model provisioning via Esperanto library
- Verified artifact storage patterns (Quiz, Podcast, Transformation, Artifact models)

**Epic & Story Analysis:**
- Extracted Story 3.2 acceptance criteria from epics.md
- Identified 4 artifact types: Quiz, Podcast, Summary, Transformation
- Documented generation methods and duration for each type
- Mapped preview requirements per artifact type
- Confirmed position in 5-step pipeline (step 2: Generate)

**UX Design Analysis:**
- Extracted admin pipeline UX patterns (Upload → Generate → Configure → Publish)
- Documented Generate step requirements (batch generation with status indicators)
- Identified AsyncStatusBar pattern for long-running tasks
- Documented preview UI requirements (type-specific preview components)
- Confirmed error isolation pattern (one failure doesn't cascade)

**Previous Story Analysis (Story 3.1):**
- Analyzed complete 3-1-module-creation-and-document-upload.md
- Extracted async upload pattern (fire-and-forget with polling)
- Identified status tracking pattern (per-item status indicators)
- Documented ModuleCreationStepper integration (5-step flow)
- Found code review learnings: infinite render loops, i18n completeness, polling patterns

**Git Intelligence:**
- Reviewed last 5 commits for Story 3.1 patterns
- Identified document upload async pattern
- Found frontend API infrastructure patterns (TanStack Query hooks)
- Confirmed admin UI component patterns (Card grids, dialogs, steppers)

**Codebase Pattern Analysis:**
- Explored existing artifact generation workflows:
  - `open_notebook/graphs/quiz_generation.py` - 5-step quiz workflow
  - `open_notebook/graphs/transformation.py` - Single-node transformation
  - `api/podcast_service.py` - Async podcast job submission
- Identified reusable domain models: Artifact, Quiz, Podcast, Source
- Documented existing artifact endpoints in `api/routers/artifacts.py`
- Found batch execution patterns (asyncio.gather with error isolation)

### Debug Log

**Session 1: Story Context Research & Analysis (2026-02-05)**

**Story Identification:**
1. Parsed user input: "Story 3.2: Artifact Generation and Preview"
2. Located in sprint-status.yaml: status = "backlog"
3. Extracted from epics.md: Epic 3, Story 2
4. Confirmed as second story in Module Creation Pipeline

**Artifact Discovery:**
1. Loaded sprint-status.yaml - confirmed Story 3.1 status = "done"
2. Loaded epics.md (1217 lines) - extracted all Epic 3 stories
3. Loaded Story 3.1 file - analyzed implementation patterns
4. Identified 4 artifact types with different generation methods

**Technical Analysis:**
1. Launched Explore agent (a477264) to analyze architecture/PRD/UX docs
2. Agent loaded 3 complete documents:
   - architecture.md (backend layering, LangGraph workflows, async patterns)
   - prd.md (FR9 requirements, admin workflow)
   - ux-design-specification.md (Generate step UI, preview patterns)
3. Comprehensive context returned in 12 sections

**Pattern Extraction:**
1. Quiz generation: LangGraph 5-step workflow (30-60s sync)
2. Transformation: LangGraph single-node (10-30s sync)
3. Podcast: Async job via surreal-commands (2-5min fire-and-forget)
4. Summary: Stored as insights on Source model
5. Batch orchestration: asyncio.gather with error isolation

**Code Review Learnings Applied:**
1. Infinite render loop prevention (useEffect wrapping)
2. N+1 query prevention (JOIN with aggregates)
3. i18n completeness (both en-US and fr-FR)
4. Service return types (Pydantic models, not dicts)
5. Error status checking (error?.response?.status)
6. State management (TanStack Query for server data)
7. Logging before exceptions (logger.error() then raise)
8. Async pattern (fire-and-forget for slow operations)

**Story File Creation:**
1. Initialized story file with header and acceptance criteria
2. Created 7 tasks with detailed subtasks (Backend 1-3, Frontend 4-6, Testing 7)
3. Wrote comprehensive Dev Notes (25+ pages):
   - Architecture patterns with code examples
   - Technical requirements per stack
   - Artifact types comparison table
   - Security & permissions guidelines
   - Database schema analysis (no migration needed)
   - File structure (10+ files to create/modify)
   - Batch orchestration pattern with asyncio.gather
   - Data flow diagrams (3 flows: generation, preview, regeneration)
   - Code review checklist (30+ items)
   - Learning from Story 3.1
   - Complete references to source documents

### Completion Notes

**Story 3.2 Context Analysis COMPLETE:**
- ✅ All acceptance criteria extracted and detailed
- ✅ Comprehensive task breakdown (7 tasks with subtasks)
- ✅ Complete technical requirements for backend and frontend
- ✅ Artifact types documented with generation methods and durations
- ✅ Security and permission guidelines provided
- ✅ Database schema analysis (no migration required)
- ✅ File structure with all files to create/modify
- ✅ Batch orchestration pattern with code examples (asyncio.gather)
- ✅ Data flow diagrams for all workflows
- ✅ Testing requirements and anti-patterns documented
- ✅ Integration points with existing code identified
- ✅ Code review checklist for developer guidance
- ✅ Learning from Story 3.1 patterns applied

**Critical Implementation Guidance Provided:**
- Batch generation with parallel async execution (asyncio.gather)
- Fire-and-forget pattern for podcast generation (surreal-commands)
- Error isolation pattern (return_exceptions=True)
- Per-artifact status tracking with preview buttons
- Type-specific preview components (Quiz, Podcast, Summary, Transformation)
- Polling pattern with conditional refetchInterval
- AsyncStatusBar for long-running operations
- Regeneration workflow (delete old, create new)
- No new database migrations needed (reuse existing models)

**All Context Sources Analyzed:**
✅ Architecture document (backend layering, LangGraph, async patterns)
✅ PRD document (FR9 requirements, admin workflow)
✅ UX design specification (Generate step UI, preview patterns, async indicators)
✅ Epics file (Story 3.2 acceptance criteria, technical requirements)
✅ Story 3.1 file (pipeline patterns, async jobs, polling, code review learnings)
✅ Git commits (last 5 commits for Story 3.1 implementation patterns)
✅ Existing codebase (quiz_generation.py, transformation.py, podcast_service.py, artifacts.py)

**Developer Has Everything Needed:**
- Clear acceptance criteria with Given/When/Then format
- Detailed task breakdown with file-level guidance
- Comprehensive architecture and pattern documentation
- Code examples for critical patterns (batch generation, polling, preview)
- Anti-patterns to avoid based on Story 3.1 code review
- Complete file list with create/modify actions
- Testing requirements and coverage targets
- Integration with Story 3.1's pipeline stepper

**Story Status:** IN PROGRESS (Tasks 1-6 Complete, Task 7 Pending)

**Implementation Progress (2026-02-05):**
- ✅ Task 1: Backend - Batch Artifact Generation Endpoint (COMPLETE)
  - Created `api/artifact_generation_service.py` with async batch orchestration
  - Added POST `/api/notebooks/{notebook_id}/generate-artifacts` endpoint
  - Implements parallel generation with asyncio.gather and error isolation
  - Quiz, Summary generation (sync 30-60s each)
  - Podcast generation (async fire-and-forget via surreal-commands)
  - 12/12 tests passing in test_artifact_generation_service.py

- ✅ Task 2: Backend - Artifact Preview Endpoints (COMPLETE)
  - Extended `api/artifacts_service.py` with type-specific preview logic
  - Added GET `/api/artifacts/{artifact_id}/preview` endpoint
  - Supports all 4 artifact types: quiz, podcast, summary, transformation
  - Includes metadata: word_count, duration, question_count
  - 5/5 tests passing in test_artifact_preview.py

- ✅ Task 3: Backend - Artifact Regeneration Endpoint (COMPLETE)
  - Added regenerate_artifact() function in artifacts_service.py
  - Added POST `/api/artifacts/{artifact_id}/regenerate` endpoint
  - Deletes old artifact and creates new with same parameters
  - Supports partial regeneration per artifact type
  - 7/7 tests passing in test_artifact_regeneration.py

**Backend Implementation Complete (24/24 tests passing)**

- ✅ Task 4: Frontend - Artifact Generation UI (COMPLETE)
  - Created ArtifactGenerationPanel component with batch generation controls
  - Added "Generate All" button with confirmation dialog
  - Implemented per-artifact status tracking (quiz, podcast, summary)
  - Added polling with conditional 2s refetch when artifacts are processing
  - Integrated AsyncStatusBar for long-running podcast generation
  - Error handling with inline error display and retry functionality

- ✅ Task 5: Frontend - Artifact Preview Components (COMPLETE)
  - Created QuizPreview component with MCQ questions and correct answer highlighting
  - Created PodcastPreview component with audio player and transcript display
  - Created SummaryPreview component with markdown rendering
  - Created TransformationPreview component for before/after comparisons
  - Created ArtifactPreviewModal with type-specific rendering
  - Added regeneration functionality with confirmation dialog
  - All components integrated with i18n (en-US and fr-FR)

- ✅ Task 6: Frontend - Pipeline Integration (COMPLETE)
  - Integrated ArtifactGenerationPanel with module page
  - Added conditional rendering based on activeStep === 'generate'
  - Implemented step validation requiring at least one completed artifact
  - Made Next button conditional on artifact completion status
  - Wired automatic step advancement via onComplete callback
  - Updated ModuleCreationStepper to accept canProceed prop

**Frontend Implementation Complete (13 files created/modified)**

**Next Steps:**
- Task 7: Additional Integration Tests (frontend component tests)

### File List

**Backend Files to Create:**
- `api/artifact_generation_service.py` - Batch artifact generation orchestration
- `tests/test_artifact_generation_service.py` - Unit tests for batch generation
- `tests/test_artifact_preview.py` - Unit tests for preview and regeneration

**Backend Files to Modify:**
- `api/models.py` - Add BatchGenerationRequest, BatchGenerationResponse, ArtifactPreviewResponse models
- `api/routers/notebooks.py` - Add POST /notebooks/{id}/generate-artifacts endpoint
- `api/routers/artifacts.py` - Extend for preview and regeneration endpoints
- `api/quiz_service.py` - Add batch generation support (if needed)
- `api/podcast_service.py` - Add batch job submission method
- `api/transformations_service.py` - Add batch transformation support

**Frontend Files to Create:**
- `frontend/src/components/admin/ArtifactGenerationPanel.tsx` - Main generation UI component
- `frontend/src/components/admin/artifacts/QuizPreview.tsx` - Quiz preview display
- `frontend/src/components/admin/artifacts/PodcastPreview.tsx` - Audio player + transcript
- `frontend/src/components/admin/artifacts/SummaryPreview.tsx` - Markdown renderer
- `frontend/src/components/admin/artifacts/TransformationPreview.tsx` - Side-by-side comparison
- `frontend/src/components/admin/artifacts/ArtifactPreviewModal.tsx` - Modal wrapper for previews
- `frontend/src/components/admin/AsyncStatusBar.tsx` - Persistent status indicator for async tasks
- `frontend/src/lib/api/artifacts.ts` - Artifacts API client methods
- `frontend/src/lib/hooks/use-artifacts.ts` - TanStack Query hooks for artifacts

**Frontend Files to Modify:**
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add Generate step UI integration
- `frontend/src/app/(dashboard)/modules/[id]/page.tsx` - Integrate ArtifactGenerationPanel
- `frontend/src/lib/types/api.ts` - Add Artifact, Preview, BatchGeneration types
- `frontend/src/lib/locales/en-US/index.ts` - Add artifacts.* translation keys (40+ keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Add French translations for all artifact keys (MANDATORY)

**Story File:**
- `_bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md` - Comprehensive story documentation

**Analysis Sources Referenced:**
- `_bmad-output/planning-artifacts/epics.md` - Epic 3 and Story 3.2 requirements
- `_bmad-output/planning-artifacts/architecture.md` - Technical architecture and patterns
- `_bmad-output/planning-artifacts/prd.md` - FR9 artifact generation requirements
- `_bmad-output/planning-artifacts/ux-design-specification.md` - Admin pipeline UX design
- `_bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md` - Pipeline patterns and learnings
- `open_notebook/graphs/quiz_generation.py` - Quiz generation workflow
- `open_notebook/graphs/transformation.py` - Transformation workflow
- `api/podcast_service.py` - Async podcast job submission
- `api/routers/artifacts.py` - Existing artifact endpoints
- `open_notebook/domain/artifact.py` - Artifact domain model

