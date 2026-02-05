# Story 3.3: Learning Objectives Configuration

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **admin**,
I want to review and edit auto-generated learning objectives for a module,
So that the AI teacher has clear goals to guide learner conversations toward.

## Acceptance Criteria

**Given** an admin enters the Configure step
**When** the module has source documents
**Then** learning objectives are auto-generated from content analysis and displayed as an editable checklist

**Given** the objectives checklist is displayed
**When** the admin edits, removes, rewords, or reorders an objective
**Then** the changes are saved to the LearningObjective records

**Given** the admin wants to add a new objective
**When** they click "Add Objective" and enter text
**Then** a new LearningObjective is created with `auto_generated: false`

**Given** no objectives exist
**When** the admin cannot proceed
**Then** a validation message indicates at least one objective is required

## Tasks / Subtasks

- [x] Task 1: Database Schema & Domain Model (AC: All)
  - [x] Create Migration 23 for learning_objective table (UPDATED: using 23, not 22)
  - [x] Create LearningObjective domain model extending ObjectModel
  - [x] Add get_for_notebook() class method for ordered retrieval
  - [x] Add reorder_objectives() helper for drag-and-drop
  - [ ] Write unit tests for domain model (PENDING)

- [x] Task 2: Auto-Generation Workflow (AC: 1)
  - [x] Create LangGraph workflow in learning_objectives_generation.py
  - [x] Implement 3-node workflow: analyze → generate → save
  - [x] Create Jinja2 prompt template for objective generation
  - [x] Use PydanticOutputParser for structured LLM output
  - [x] Generate 3-5 measurable objectives from source content

- [x] Task 3: Backend API Endpoints (AC: 1, 2, 3, 4)
  - [x] Create learning_objectives router with 6 endpoints
  - [x] GET /notebooks/{id}/learning-objectives - List objectives (ordered)
  - [x] POST /notebooks/{id}/learning-objectives/generate - Auto-generate
  - [x] POST /notebooks/{id}/learning-objectives - Create manual objective
  - [x] PUT /notebooks/{id}/learning-objectives/{obj_id} - Update text
  - [x] DELETE /notebooks/{id}/learning-objectives/{obj_id} - Delete
  - [x] POST /notebooks/{id}/learning-objectives/reorder - Reorder via drag-drop
  - [x] Add Pydantic request/response models to api/models.py
  - [x] Register router in api/main.py

- [x] Task 4: Frontend - Learning Objectives Editor Component (AC: 2, 3, 4)
  - [x] Create LearningObjectivesEditor component with drag-drop
  - [x] Install @hello-pangea/dnd for reordering (modern fork of react-beautiful-dnd)
  - [x] Add Generate button (calls auto-generation endpoint)
  - [x] Editable inline text inputs for each objective
  - [x] Add/delete objective buttons
  - [x] Visual indicator for auto-generated vs manual objectives
  - [x] Validation warning when 0 objectives exist

- [ ] Task 5: Frontend - API & Hooks Integration (AC: All)
  - [ ] Create learning-objectives.ts API client
  - [ ] Create use-learning-objectives.ts TanStack Query hooks
  - [ ] Implement optimistic updates for drag-and-drop reordering
  - [ ] Add toast notifications for all mutations
  - [ ] Add i18n keys for objectives UI (en-US + fr-FR)

- [ ] Task 6: Pipeline Integration (AC: 4)
  - [ ] Integrate LearningObjectivesEditor into Configure step
  - [ ] Add step validation (≥1 objective required)
  - [ ] Enable Next button only when validation passes
  - [ ] Update ModuleCreationStepper progress tracking

- [ ] Task 7: Testing (All ACs)
  - [ ] Unit tests for LearningObjective domain model
  - [ ] Unit tests for objectives generation workflow
  - [ ] Integration tests for all API endpoints
  - [ ] Frontend component tests for editor
  - [ ] E2E test for full auto-generate → edit → save flow

## Dev Notes

### 🎯 Story Overview

This is the **third story in Epic 3: Module Creation & Publishing Pipeline**. It implements AI-powered learning objectives generation with full CRUD operations and drag-and-drop reordering for the admin module creation workflow.

**Key Integration Points:**
- Extends Story 3.1 and 3.2's module creation pipeline (step 3 of 5-step flow)
- Creates new LearningObjective domain model with database migration
- Implements LangGraph workflow for AI-powered objective generation
- Provides full admin CRUD interface with drag-and-drop reordering
- Sets foundation for Epic 4 learner progress tracking (LearnerObjectiveProgress)
- Validates pipeline progression (≥1 objective required before publishing)

### 🏗️ Architecture Patterns (MANDATORY)

**Three-Layer Backend Pattern:**
```
Router (api/routers/learning_objectives.py)
  ↓ validates request, applies auth
Domain Model (LearningObjective)
  ↓ business logic, persistence
Database (SurrealDB via repository.py)
```

**Critical Rules:**
- Routers NEVER call database directly
- LearningObjective extends ObjectModel base class
- All functions are `async def` with `await`
- Return Pydantic models from endpoints (never raw dicts)
- Log before raising HTTPException: `logger.error()` then `raise HTTPException`
- Use `Depends(require_admin)` for admin-only endpoints

**Frontend Architecture:**
- TanStack Query for ALL server state (objectives list, generation status)
- Zustand ONLY for UI state (expanded objectives, editing state)
- Optimistic updates for drag-and-drop (instant feedback)
- Query keys: hierarchical `['modules', id, 'objectives']`
- Never duplicate API data in Zustand

### 📋 Technical Requirements

**Backend Stack:**
- FastAPI 0.104+ with async endpoints
- Python 3.11+ with type hints
- LangGraph for objective generation workflow
- Esperanto library for AI model provisioning
- SurrealDB async driver for persistence
- Pydantic v2 for request/response validation
- Loguru for structured logging
- ai_prompter with Jinja2 templates

**Frontend Stack:**
- Next.js 16 (App Router) with React 19
- TypeScript 5 with strict mode
- TanStack Query 5.83.0 for server state
- react-beautiful-dnd for drag-and-drop reordering
- Shadcn/ui components (Card, Input, Button)
- Tailwind CSS for styling
- i18next for internationalization (BOTH en-US and fr-FR required)

**Learning Objective Characteristics:**

| Field | Type | Purpose | Default |
|-------|------|---------|---------|
| **notebook_id** | record<notebook> | Links objective to module | Required |
| **text** | string | Objective description (measurable) | Required |
| **order** | int | Display order (drag-drop) | 0 |
| **auto_generated** | bool | AI vs manual creation | false |
| **created** | datetime | Creation timestamp | time::now() |
| **updated** | datetime | Last update timestamp | time::now() |

### 🔒 Security & Permissions

**Admin-Only Operations:**
- List objectives: `require_admin()` dependency
- Generate objectives: `require_admin()` dependency
- Create/update/delete objectives: `require_admin()` dependency
- Reorder objectives: `require_admin()` dependency

**Learner Operations (Epic 4, not this story):**
- Learners view objectives in Progress tab (Story 5.3)
- AI teacher checks off objectives during chat (Story 4.4)
- LearnerObjectiveProgress tracks per-user completion (Migration 23)

**Authentication:**
- JWT tokens in httpOnly cookies (existing auth.py)
- No additional auth changes needed
- All endpoints protected by dependencies

### 🗂️ Database Schema

**Migration 22: learning_objective Table (NEW)**

```sql
-- migrations/22_learning_objective.surql
DEFINE TABLE learning_objective SCHEMAFULL;

DEFINE FIELD notebook_id ON learning_objective TYPE record<notebook>;
DEFINE FIELD text ON learning_objective TYPE string;
DEFINE FIELD order ON learning_objective TYPE int DEFAULT 0;
DEFINE FIELD auto_generated ON learning_objective TYPE bool DEFAULT false;
DEFINE FIELD created ON learning_objective TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON learning_objective TYPE datetime DEFAULT time::now();

-- Index for efficient retrieval by notebook
DEFINE INDEX idx_notebook_objectives ON learning_objective FIELDS notebook_id, order;
```

**Rollback Migration:**
```sql
-- migrations/22_learning_objective_down.surql
REMOVE TABLE learning_objective;
```

**CRITICAL NOTE:** Migration 21 is already used for `published` field on notebooks. This story uses Migration 22.

**Migration Strategy:**
- **NEW MIGRATION REQUIRED** for this story (Migration 22)
- LearningObjective table with 6 fields
- Index on (notebook_id, order) for efficient ordered queries
- No changes to existing tables

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `migrations/22_learning_objective.surql` - Create learning_objective table
- `migrations/22_learning_objective_down.surql` - Rollback migration
- `open_notebook/domain/learning_objective.py` - Domain model
- `open_notebook/graphs/learning_objectives_generation.py` - LangGraph workflow
- `prompts/learning_objectives/generate.jinja` - AI prompt template
- `api/routers/learning_objectives.py` - API endpoints (6 routes)
- `tests/test_learning_objective_domain.py` - Domain model unit tests
- `tests/test_objectives_generation.py` - Workflow unit tests
- `tests/test_learning_objectives_api.py` - API integration tests

**MODIFY (extend existing):**
- `api/models.py` - Add LearningObjective Pydantic models (5 models)
- `api/main.py` - Register learning_objectives router

**Frontend Files to Create:**

**NEW:**
- `frontend/src/components/admin/LearningObjectivesEditor.tsx` - Main editor component
- `frontend/src/lib/api/learning-objectives.ts` - API client (6 functions)
- `frontend/src/lib/hooks/use-learning-objectives.ts` - TanStack Query hooks (6 hooks)

**MODIFY:**
- `frontend/src/app/(dashboard)/modules/[id]/page.tsx` - Integrate editor in Configure step
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add validation logic
- `frontend/src/lib/types/api.ts` - Add LearningObjective types
- `frontend/package.json` - Add react-beautiful-dnd dependency
- `frontend/src/lib/locales/en-US/index.ts` - Add learningObjectives.* keys (20+ keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Add French translations (MANDATORY)

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

### 🔄 Auto-Generation Workflow Pattern (CRITICAL)

**3-Node LangGraph Workflow:**

```python
# Workflow stages:
# 1. analyze_sources → Extract content summary from notebook sources
# 2. generate_objectives → LLM generates 3-5 measurable objectives
# 3. save_objectives → Save to database with auto_generated=true

async def analyze_sources(state: ObjectiveGenerationState) -> dict:
    """Build summary from notebook sources for LLM context."""
    notebook = await Notebook.get(state["notebook_id"])
    sources = await notebook.get_sources()

    # Build concise summary (titles + excerpts)
    summary_parts = []
    for source in sources[:10]:  # Limit to first 10
        summary_parts.append(f"- {source.title}: {source.full_text[:200]}...")

    return {
        "sources_summary": "\n".join(summary_parts),
        "status": "generating"
    }

async def generate_objectives(state: ObjectiveGenerationState) -> dict:
    """Generate objectives using LLM with structured output."""
    parser = PydanticOutputParser(pydantic_object=GeneratedObjectives)

    prompter = Prompter(
        prompt_template="learning_objectives/generate.jinja",
        parser=parser
    )
    system_prompt = prompter.render(data={
        "sources_summary": state["sources_summary"],
        "num_objectives": state.get("num_objectives", 4)
    })

    model = await provision_langchain_model(
        content=system_prompt,
        structured=dict(type="json")
    )

    ai_message = await model.ainvoke(system_prompt)
    result = parser.parse(clean_thinking_content(str(ai_message.content)))

    objectives_list = [
        {"text": obj, "order": idx, "auto_generated": True}
        for idx, obj in enumerate(result.objectives)
    ]

    return {
        "generated_objectives": objectives_list,
        "status": "saving"
    }

async def save_objectives(state: ObjectiveGenerationState) -> dict:
    """Save objectives to database."""
    objective_ids = []

    for obj_data in state["generated_objectives"]:
        objective = LearningObjective(
            notebook_id=state["notebook_id"],
            text=obj_data["text"],
            order=obj_data["order"],
            auto_generated=True
        )
        await objective.save()
        objective_ids.append(objective.id)

    return {
        "objective_ids": objective_ids,
        "status": "completed"
    }
```

**Prompt Template Strategy:**
```jinja
You are an expert instructional designer. Based on the following educational content, generate {{ num_objectives }} clear, measurable learning objectives.

# Content Summary
{{ sources_summary }}

# Instructions
Generate objectives that:
1. Are specific and measurable (use action verbs: explain, analyze, apply, compare)
2. Represent key concepts learners should master
3. Are achievable through guided AI conversation
4. Progress from foundational to advanced
5. Avoid generic objectives like "understand the material"

Format as JSON matching this schema:
{{ parser.get_format_instructions() }}
```

**Generation Trigger:**
- Admin enters Configure step in pipeline
- Frontend checks if objectives exist via GET endpoint
- If none exist, shows "Generate" button
- Button calls POST /notebooks/{id}/learning-objectives/generate
- Workflow runs (30-60s), generates 3-5 objectives
- Frontend displays generated objectives in editable list

### 🧪 Testing Requirements

**Backend Tests (pytest):**
- `tests/test_learning_objective_domain.py`
  - Test LearningObjective model creation and validation
  - Test get_for_notebook() ordered retrieval
  - Test reorder_objectives() bulk update
  - Test RecordID coercion in validators
  - Test empty text validation (should raise InvalidInputError)

- `tests/test_objectives_generation.py`
  - Test workflow with valid sources (generates 3-5 objectives)
  - Test workflow with empty sources (returns error)
  - Test workflow with LLM failure (error handling)
  - Test structured output parsing
  - Test save_objectives() database writes

- `tests/test_learning_objectives_api.py`
  - Test GET /objectives returns ordered list
  - Test POST /generate creates objectives (first time only)
  - Test POST /generate fails if objectives already exist
  - Test POST / creates manual objective (auto_generated=false)
  - Test PUT /{id} updates text
  - Test DELETE /{id} removes objective
  - Test POST /reorder updates order field
  - Test admin-only auth (403 for non-admin)

**Frontend Tests:**
- Component tests for LearningObjectivesEditor
- Mock drag-and-drop interactions
- Test optimistic updates for reordering
- Mock API responses with MSW

**Test Coverage Targets:**
- Backend: 80%+ line coverage
- Frontend: 70%+ line coverage for critical paths

### 🚫 Anti-Patterns to Avoid

**From Previous Code Reviews (Stories 3.1 & 3.2):**

1. **Migration Number Collision (CRITICAL)**
   - ❌ Using Migration 21 (already used for `published` field)
   - ✅ Use Migration 22 for learning_objective table

2. **N+1 Query Problem (CRITICAL)**
   - ❌ Fetching objectives in a loop
   - ✅ Use get_for_notebook() with ORDER BY in single query

3. **Domain Model Pattern**
   - ❌ Not extending ObjectModel base class
   - ✅ Inherit from ObjectModel for auto-save/delete/get methods

4. **RecordID Coercion**
   - ❌ Storing notebook_id as plain string
   - ✅ Use field_validator to ensure RecordID format: "notebook:{id}"

5. **Service Return Types**
   - ❌ Returning raw dicts from services
   - ✅ Always return Pydantic models for type safety

6. **Error Status Checking**
   - ❌ Frontend: `if (error)` without checking status
   - ✅ Frontend: `if (error?.response?.status === 400)` to distinguish errors

7. **i18n Completeness**
   - ❌ Only adding en-US translations
   - ✅ ALWAYS add BOTH en-US and fr-FR for every UI string

8. **State Management**
   - ❌ Duplicating API data in Zustand store
   - ✅ Use TanStack Query for server state, Zustand only for UI state

9. **Optimistic Updates**
   - ❌ No feedback during drag-and-drop (feels laggy)
   - ✅ Use onMutate for instant UI update, onError for rollback

10. **Missing Logging**
    - ❌ Raising HTTPException without logging
    - ✅ Always `logger.error()` before raising exception

11. **Validation Timing**
    - ❌ Only validating on form submit
    - ✅ Also validate in stepper Next button (disable if <1 objective)

12. **Empty Checklist UX**
    - ❌ No guidance when objectives list is empty
    - ✅ Show "Generate" button and helpful empty state message

### 🔗 Integration with Existing Code

**Follows Patterns From:**

From `open_notebook/domain/module_assignment.py`:
- RecordID coercion in field_validator
- Class method for filtered retrieval (get_for_notebook)
- Compound WHERE clauses (notebook_id + order)

From `open_notebook/graphs/quiz_generation.py`:
- 3+ node LangGraph workflow pattern
- PydanticOutputParser for structured LLM output
- provision_langchain_model() for AI calls
- State machine with status field

From `api/routers/module_assignments.py`:
- Admin-only CRUD endpoints
- require_admin() dependency on all routes
- List + Create + Update + Delete pattern

From `frontend/src/components/admin/DocumentUploader.tsx`:
- Status indicators during async operations
- Empty state with call-to-action button
- Error handling with inline messages

**New Dependencies:**

Frontend:
- `react-beautiful-dnd` - Drag-and-drop library (add to package.json)
- No backend dependencies needed (all exist)

**Reuse These Existing Components:**

From Shadcn/ui:
- Card - Objective list items
- Input - Editable text fields
- Button - Add/delete/generate actions
- Loader2 - Loading spinners

From existing hooks:
- useTranslation() - i18n access
- useMutation/useQuery - TanStack Query wrappers

### 📊 Data Flow Diagrams

**Auto-Generation Flow:**
```
Admin (Browser)
  ↓ Enters Configure step
Frontend (LearningObjectivesEditor)
  ↓ GET /api/notebooks/{id}/learning-objectives
Backend
  ↓ Returns empty list []
Frontend
  ↓ Shows "Generate" button
Admin
  ↓ Clicks "Generate Objectives"
Frontend
  ↓ POST /api/notebooks/{id}/learning-objectives/generate
Backend Router
  ↓ Depends(require_admin)
  ↓ Verifies notebook exists
  ↓ Checks no objectives already exist (400 if exist)
  ↓ Invokes objectives_generation_graph.ainvoke()
LangGraph Workflow
  ↓ Node 1: analyze_sources (extract summary)
  ↓ Node 2: generate_objectives (LLM call with structured output)
  ↓ Node 3: save_objectives (create LearningObjective records)
  ↓ Returns { status: "completed", objective_ids: [...] }
Backend
  ↓ Returns BatchGenerationResponse
Frontend
  ↓ Invalidates ['modules', id, 'objectives'] query
  ↓ Refetches objectives list
  ↓ Displays 3-5 generated objectives
  ↓ Shows toast: "Learning objectives generated"
```

**CRUD Operations Flow:**
```
Admin (Browser)
  ↓ Views objectives checklist
  ↓ Actions:

1. **Edit Objective Text:**
   ↓ Types in inline Input field
   ↓ onChange triggers debounced mutation
   ↓ PUT /api/notebooks/{id}/learning-objectives/{obj_id}
   ↓ Backend updates text field
   ↓ Query invalidated, list refetches

2. **Add Manual Objective:**
   ↓ Types in bottom Input field
   ↓ Clicks "Add" button
   ↓ POST /api/notebooks/{id}/learning-objectives { text }
   ↓ Backend creates with auto_generated=false, order=max+1
   ↓ Query invalidated, new objective appears

3. **Delete Objective:**
   ↓ Clicks trash icon
   ↓ Confirm dialog: "Are you sure?"
   ↓ DELETE /api/notebooks/{id}/learning-objectives/{obj_id}
   ↓ Backend deletes record
   ↓ Query invalidated, objective removed

4. **Reorder via Drag-Drop:**
   ↓ Drags objective to new position
   ↓ onDragEnd calculates new order
   ↓ Optimistic update (instant UI feedback)
   ↓ POST /api/notebooks/{id}/learning-objectives/reorder
   ↓ Backend updates order field for all objectives
   ↓ Query invalidated for consistency
   ↓ If error, rollback to previous order
```

**Pipeline Validation Flow:**
```
Admin (Browser)
  ↓ On Configure step
  ↓ ModuleCreationStepper checks validation
Stepper Component
  ↓ Queries objectives count via TanStack Query
  ↓ Checks: objectives.length >= 1

If FALSE (no objectives):
  ↓ Next button is DISABLED
  ↓ Shows warning: "At least one learning objective is required"

If TRUE (≥1 objective):
  ↓ Next button is ENABLED
  ↓ Admin can advance to next step (AI Teacher Prompt - Story 3.4)
```

### 🔍 Code Review Checklist

Before marking this story as "done", verify:

**Backend:**
- [ ] Migration 22 created (NOT 21) with learning_objective table
- [ ] LearningObjective extends ObjectModel base class
- [ ] RecordID coercion in field_validator for notebook_id
- [ ] get_for_notebook() returns ordered list (ORDER BY order ASC)
- [ ] All endpoints have `Depends(require_admin)` dependency
- [ ] All endpoints have `response_model=SomeResponse` typing
- [ ] All exceptions logged with `logger.error()` before raising
- [ ] Generation workflow follows quiz_generation.py pattern
- [ ] PydanticOutputParser used for structured LLM output
- [ ] Prompt template in prompts/learning_objectives/generate.jinja
- [ ] No N+1 queries (single query with ORDER BY)
- [ ] Router registered in api/main.py

**Frontend:**
- [ ] react-beautiful-dnd added to package.json
- [ ] TanStack Query for ALL objectives data (no Zustand duplication)
- [ ] Query keys follow hierarchy: `['modules', id, 'objectives']`
- [ ] Optimistic updates for drag-and-drop (onMutate + onError)
- [ ] Mutations invalidate correct query keys
- [ ] Error handling checks `error?.response?.status`
- [ ] Loading states with Loader2 spinners
- [ ] Empty state with "Generate" button when 0 objectives
- [ ] Validation warning when <1 objective
- [ ] NO hardcoded strings (all via i18n)
- [ ] BOTH en-US and fr-FR translations added (20+ keys)

**Pipeline Integration:**
- [ ] LearningObjectivesEditor integrated in Configure step
- [ ] ModuleCreationStepper validates ≥1 objective before Next
- [ ] Next button disabled when validation fails
- [ ] Step can be revisited for editing after advancing

**Testing:**
- [ ] Backend: 20+ tests covering domain + workflow + API
- [ ] Frontend: Component tests for editor + drag-drop
- [ ] Integration test for full flow (generate + edit + reorder)

**Documentation:**
- [ ] Dev Agent Record filled with agent model, files, notes
- [ ] This checklist completed in story file

### 🎓 Learning from Previous Stories

**From Story 3.1 (Module Creation):**
- ModuleCreationStepper pattern with 5 steps
- Step validation before enabling Next button
- Empty state with call-to-action (Generate button)
- Admin-only CRUD operations with require_admin()
- i18n completeness (en-US + fr-FR mandatory)

**From Story 3.2 (Artifact Generation):**
- LangGraph workflow pattern (3 nodes: analyze → generate → save)
- PydanticOutputParser for structured LLM output
- ai_prompter with Jinja2 templates in prompts/ folder
- provision_langchain_model() for smart AI provisioning
- Status tracking in workflow state
- Error isolation (return status + error, don't throw)

**Apply these learnings:**
- Auto-generation uses LangGraph (like quiz, not async job like podcast)
- Validation blocks pipeline progression (like document upload requirement)
- Drag-and-drop uses optimistic updates (instant feedback)
- Empty state encourages action ("Generate" button prominent)
- Admin remains in control (can edit AI-generated objectives)

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Domain Models]
- [Source: _bmad-output/planning-artifacts/architecture.md#LangGraph Workflows]
- [Source: _bmad-output/planning-artifacts/architecture.md#Database Migrations]
- [Source: _bmad-output/planning-artifacts/architecture.md#ObjectModel Base Class]

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Module Creation & Publishing Pipeline]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3: Learning Objectives Configuration]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Context for Learner Usage]

**UX Design:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Pipeline Step 3 Configure]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Editable Checklist Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Drag-Drop Interactions]

**Existing Code Patterns:**
- [Source: open_notebook/domain/module_assignment.py] - RecordID coercion, compound keys
- [Source: open_notebook/graphs/quiz_generation.py] - LangGraph workflow pattern
- [Source: api/routers/module_assignments.py] - Admin CRUD endpoints
- [Source: frontend/src/components/admin/DocumentUploader.tsx] - Empty state + generation pattern

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md] - Stepper validation, admin patterns
- [Source: _bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md] - LangGraph generation, structured output

**Configuration:**
- [Source: CONFIGURATION.md#LangGraph Settings]
- [Source: CONFIGURATION.md#AI Model Configuration]
- [Source: CONFIGURATION.md#Database Migrations]

### Project Structure Notes

**Alignment with Project:**
- Continues (dashboard) route group for admin pages (consistent with Stories 3.1-3.2)
- Follows established domain/service/router layering (mandatory)
- Adds Migration 22 for new learning_objective table
- Extends ObjectModel base class pattern (like Company, ModuleAssignment)
- Integrates with Story 3.1's ModuleCreationStepper (step 3 of 5)

**Potential Conflicts:**
- Migration 21 already used for `published` field - use Migration 22 ✓
- No conflicts detected with existing code
- Clean separation from learner features (Epic 4)

**Design Decisions:**
- Auto-generation triggers on Configure step entry (not pre-generated)
- Drag-and-drop for reordering (better UX than up/down buttons)
- Inline text editing (no separate edit modal)
- Validation at stepper level (Next button disabled if <1 objective)
- Optimistic updates for smooth drag-and-drop experience

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Context Analysis Completed

**Architecture Analysis:**
- Analyzed complete architecture document for ObjectModel base class pattern
- Extracted LangGraph workflow patterns (quiz_generation.py as template)
- Identified database migration requirements (Migration 22 for learning_objective)
- Documented AI provisioning via Esperanto library
- Verified domain model patterns (RecordID coercion, class methods)

**Epic & Story Analysis:**
- Extracted Story 3.3 acceptance criteria from epics.md
- Identified CRUD operations needed (list, generate, create, update, delete, reorder)
- Documented auto-generation trigger point (Configure step entry)
- Mapped validation requirements (≥1 objective before Next)
- Confirmed position in 5-step pipeline (step 3: Configure)

**Database Schema Analysis:**
- Discovered Migration 21 already used for `published` field
- Designed Migration 22 for learning_objective table (6 fields + index)
- Defined relationships (notebook_id as foreign key to notebook table)
- Planned order field for drag-and-drop reordering
- Confirmed auto_generated flag for AI vs manual distinction

**LangGraph Workflow Design:**
- Analyzed quiz_generation.py workflow as template
- Designed 3-node workflow: analyze_sources → generate_objectives → save_objectives
- Created prompt template strategy (Jinja2 with PydanticOutputParser)
- Documented structured output schema (GeneratedObjectives model)
- Confirmed synchronous execution (30-60s, not async job)

**Frontend UX Analysis:**
- Researched drag-and-drop library options (react-beautiful-dnd selected)
- Designed LearningObjectivesEditor component architecture
- Planned inline editing pattern (no separate edit modal)
- Documented optimistic update strategy for smooth UX
- Identified validation integration with ModuleCreationStepper

**Previous Story Analysis:**
- Analyzed Story 3.1 patterns (stepper validation, admin CRUD)
- Analyzed Story 3.2 patterns (LangGraph workflows, structured output)
- Extracted code review learnings (N+1 prevention, RecordID coercion, i18n)
- Found admin UI patterns (empty state with Generate button)
- Confirmed TanStack Query + Zustand separation

### Debug Log

**Session 1: Story Context Research & Analysis (2026-02-05)**

(Previous session notes preserved above)

**Session 2: Backend Implementation (2026-02-05)**

**Migration Number Correction:**
1. User provided critical note: Use Migration 23, NOT 22
2. Migration 22 reserved for LearnerObjectiveProgress (Epic 4)
3. Current migrations: 21 is latest (published field on notebooks)
4. Created Migration 23 for learning_objective table
5. Updated async_migrate.py to register Migration 23

**Task 1: Database Schema & Domain Model**
1. Created `open_notebook/database/migrations/23.surrealql`:
   - SCHEMAFULL table with 6 fields (notebook_id, text, order, auto_generated, created, updated)
   - Index on (notebook_id, order) for efficient ordered retrieval
   - No unique constraint (multiple objectives per notebook needed)
2. Created `open_notebook/database/migrations/23_down.surrealql` for rollback
3. Registered migrations in AsyncMigrationManager (both up and down)
4. Created `open_notebook/domain/learning_objective.py`:
   - Extended ObjectModel base class
   - RecordID coercion in field_validator for notebook_id
   - Text validation (non-empty) in field_validator
   - get_for_notebook() class method with ORDER BY order ASC
   - reorder_objectives() bulk update method
   - delete_by_id() class method
   - count_for_notebook() helper method
   - needs_embedding() returns False (not searchable)
5. Tested imports: ✓ LearningObjective imports successfully

**Task 2: Auto-Generation Workflow**
1. Created `open_notebook/graphs/learning_objectives_generation.py`:
   - ObjectiveGenerationState TypedDict for workflow state
   - GeneratedObjectives Pydantic model for structured LLM output
   - analyze_sources() node: Builds summary from first 10 sources
   - generate_objectives() node: LLM call with PydanticOutputParser
   - save_objectives() node: Persist LearningObjective records
   - Linear workflow: analyze → generate → save → END
2. Created `prompts/learning_objectives/generate.jinja`:
   - Instructional design expert persona
   - Bloom's Taxonomy action verbs guidance
   - Examples of good vs bad objectives
   - Measurable, conversation-achievable objectives
   - Parser format instructions injection
3. Workflow uses provision_langchain_model() with structured output
4. Error handling at each node (returns error dict, no exceptions)
5. Tested imports: ✓ Learning objectives graph imports successfully

**Task 3: Backend API Endpoints**
1. Added 5 Pydantic models to `api/models.py`:
   - LearningObjectiveCreate (text, order)
   - LearningObjectiveUpdate (text optional)
   - LearningObjectiveResponse (full objective with timestamps)
   - LearningObjectiveReorder (list of {id, order} dicts)
   - BatchGenerationResponse (status, objective_ids, error)
2. Created `api/routers/learning_objectives.py`:
   - 6 endpoints with admin-only dependency
   - GET /notebooks/{id}/learning-objectives - List (ordered)
   - POST /notebooks/{id}/learning-objectives/generate - Auto-generate
   - POST /notebooks/{id}/learning-objectives - Create manual
   - PUT /notebooks/{id}/learning-objectives/{obj_id} - Update text
   - DELETE /notebooks/{id}/learning-objectives/{obj_id} - Delete
   - POST /notebooks/{id}/learning-objectives/reorder - Reorder
   - HTTPException handling for 400, 404, 500 errors
   - Admin user dependency injection
3. Created `api/learning_objectives_service.py`:
   - list_objectives(): Fetches ordered list
   - generate_objectives(): Invokes LangGraph workflow
   - create_objective(): Manual creation with auto order calculation
   - update_objective(): Text updates only
   - delete_objective(): Deletion with existence check
   - reorder_objectives(): Bulk update via domain method
   - All methods log operations and handle exceptions
   - Generate checks for existing objectives (idempotent guard)
4. Registered router in `api/main.py`:
   - Added to imports
   - Registered with /api prefix and learning-objectives tag
5. Tested imports: ✓ Learning objectives router imports successfully

**Session 3: Frontend Implementation - Task 4 (2026-02-05)**

**Task 4: Frontend Editor Component**
1. Installed `@hello-pangea/dnd@16.6.1` (modern maintained fork of react-beautiful-dnd):
   - Better TypeScript support
   - Active maintenance (react-beautiful-dnd is deprecated)
   - Drop-in replacement with same API
2. Added TypeScript types to `frontend/src/lib/types/api.ts`:
   - LearningObjectiveResponse (6 fields)
   - CreateLearningObjectiveRequest
   - UpdateLearningObjectiveRequest
   - ReorderLearningObjectivesRequest (array of {id, order})
   - BatchGenerationResponse
3. Created `frontend/src/lib/api/learning-objectives.ts`:
   - listLearningObjectives() - GET ordered list
   - generateLearningObjectives() - POST trigger workflow
   - createLearningObjective() - POST manual objective
   - updateLearningObjective() - PUT text update
   - deleteLearningObjective() - DELETE objective
   - reorderLearningObjectives() - POST bulk reorder
4. Created `frontend/src/lib/hooks/use-learning-objectives.ts`:
   - Query factory: learningObjectivesKeys (hierarchical cache keys)
   - useLearningObjectives() - List query with auto-refetch
   - useGenerateLearningObjectives() - Mutation with toast feedback
   - useCreateLearningObjective() - Mutation with cache invalidation
   - useUpdateLearningObjective() - Mutation with toast
   - useDeleteLearningObjective() - Mutation with confirmation
   - useReorderLearningObjectives() - **Optimistic updates** for instant drag feedback
5. Created `frontend/src/components/admin/LearningObjectivesEditor.tsx`:
   - DragDropContext with @hello-pangea/dnd
   - Droppable list with visual drag feedback
   - Draggable items with grip handle
   - Inline text editing (click to edit, save on blur/Enter)
   - Empty state with prominent "Generate" button
   - AI-generated badge (Sparkles icon)
   - Delete confirmation AlertDialog
   - Add manual objective input at bottom
   - Validation warning when 0 objectives
   - Loading states with Loader2 spinners
   - Error handling with Alert component
6. Added i18n translations (20 keys):
   - `frontend/src/lib/locales/en-US/index.ts` - English strings
   - `frontend/src/lib/locales/fr-FR/index.ts` - French translations
   - Keys: learningObjectives.title, emptyTitle, generateButton, etc.
7. Integrated into `frontend/src/app/(dashboard)/modules/[id]/page.tsx`:
   - Added LearningObjectivesEditor import
   - Added useLearningObjectives() hook for validation
   - Updated canProceed logic (≥1 objective required for Configure step)
   - Rendered in activeStep === 'configure' block
   - Card wrapper with title and description
8. Linting fixes:
   - Removed unused useDebounce import (save on blur/Enter instead)
   - Clean lint results for LearningObjectivesEditor.tsx
9. Tested TypeScript compilation: ✓ All types resolve correctly

**Session 2: Backend Implementation - Tasks 1-3 (2026-02-05)**

**Story Identification:**
1. Parsed user request for Story 3.3
2. Located in sprint-status.yaml: status = "backlog"
3. Extracted from epics.md: Epic 3, Story 3
4. Confirmed as third story in Module Creation Pipeline

**Architecture Discovery:**
1. Loaded complete epics.md (Story 3.3 lines 527-552)
2. Launched Explore agent (abd7a76) to analyze architecture + PRD + UX docs
3. Agent discovered Migration 21 collision (already used for `published`)
4. Corrected to Migration 22 for learning_objective table
5. Extracted ObjectModel base class pattern from existing domain models

**Technical Analysis:**
1. LearningObjective domain model design (6 fields, RecordID coercion)
2. LangGraph workflow design (3 nodes, synchronous execution)
3. API endpoints design (6 routes for full CRUD + reorder)
4. Frontend drag-and-drop pattern (react-beautiful-dnd library)
5. Optimistic updates strategy for instant feedback

**Code Pattern Extraction:**
1. RecordID coercion from module_assignment.py
2. LangGraph workflow from quiz_generation.py
3. Admin CRUD endpoints from module_assignments.py
4. Empty state + generation from DocumentUploader.tsx
5. Stepper validation from ModuleCreationStepper.tsx

**Prompt Template Design:**
1. Created Jinja2 template for objective generation
2. Designed structured output schema (GeneratedObjectives)
3. Specified action verb requirements (explain, analyze, apply)
4. Confirmed measurable objective criteria
5. PydanticOutputParser integration for reliable parsing

**Story File Creation:**
1. Initialized story file with header and acceptance criteria
2. Created 7 tasks with detailed subtasks
3. Wrote comprehensive Dev Notes (30+ pages):
   - Architecture patterns with Migration 22 schema
   - LangGraph workflow design with code examples
   - CRUD API endpoints (6 routes)
   - Frontend drag-and-drop component design
   - Optimistic update patterns
   - Data flow diagrams (3 flows)
   - Code review checklist (30+ items)
   - Learning from Stories 3.1 and 3.2
   - Complete references to source documents

### Completion Notes

**Story 3.3 Context Analysis COMPLETE:**
- ✅ All acceptance criteria extracted and detailed
- ✅ Comprehensive task breakdown (7 tasks with subtasks)
- ✅ Complete technical requirements for backend and frontend
- ✅ Database schema (Migration 22) with rollback
- ✅ LearningObjective domain model extending ObjectModel
- ✅ LangGraph workflow (3 nodes: analyze → generate → save)
- ✅ CRUD API endpoints (6 routes) with Pydantic models
- ✅ Frontend drag-and-drop editor with optimistic updates
- ✅ Prompt template design with structured output
- ✅ Pipeline validation integration (≥1 objective required)
- ✅ Testing requirements documented
- ✅ Code review checklist for developer guidance
- ✅ Learning from previous stories applied

**Critical Implementation Guidance Provided:**
- Migration 22 for learning_objective table (NOT 21)
- LearningObjective extends ObjectModel base class
- RecordID coercion in field_validator for notebook_id
- 3-node LangGraph workflow (synchronous, 30-60s)
- PydanticOutputParser for structured LLM output
- Jinja2 prompt template with action verb requirements
- Full CRUD API (6 endpoints) with admin-only auth
- react-beautiful-dnd for drag-and-drop reordering
- Optimistic updates with onMutate + onError rollback
- Pipeline validation in ModuleCreationStepper
- i18n keys in both en-US and fr-FR (20+ keys)

**All Context Sources Analyzed:**
✅ Architecture document (ObjectModel, LangGraph, migrations, domain patterns)
✅ PRD document (learning objectives requirements, admin workflow)
✅ UX design specification (Configure step, drag-drop, validation)
✅ Epics file (Story 3.3 acceptance criteria, technical requirements)
✅ Story 3.1 file (stepper patterns, validation, admin CRUD)
✅ Story 3.2 file (LangGraph workflows, structured output, generation patterns)
✅ Existing codebase (module_assignment.py, quiz_generation.py, module_assignments.py)

**Developer Has Everything Needed:**
- Clear acceptance criteria with Given/When/Then format
- Detailed task breakdown with file-level guidance
- Database migration schema with rollback
- Domain model code with validators
- LangGraph workflow code with prompt template
- Complete API endpoint implementations
- Frontend component with drag-and-drop
- Optimistic update patterns for smooth UX
- Testing requirements and coverage targets
- Anti-patterns to avoid (migration collision, N+1 queries, etc.)
- Integration with existing pipeline stepper

**Story Status:** Tasks 1-4 Complete (Backend + Frontend Editor Done)

**Task 4 (Frontend Editor) Implementation Summary:**
- ✅ Installed @hello-pangea/dnd for drag-and-drop reordering
- ✅ Created comprehensive TypeScript types for API integration
- ✅ Built full API client with 6 endpoint functions
- ✅ Implemented TanStack Query hooks with optimistic updates
- ✅ Created LearningObjectivesEditor component with:
  - Drag-and-drop reordering with visual feedback
  - Inline text editing (click to edit, save on blur/Enter)
  - Auto-generation button with loading states
  - Empty state with prominent "Generate" CTA
  - AI-generated vs manual visual indicators
  - Delete confirmation dialog
  - Add manual objective input
  - Validation warning when 0 objectives
- ✅ Added complete i18n support (en-US + fr-FR, 20 keys each)
- ✅ Integrated into module pipeline Configure step
- ✅ Pipeline validation: Next button disabled when <1 objective
- ✅ Clean TypeScript compilation with no linting errors

**Next Steps:**
- Task 5: Frontend API & Hooks Integration (ALREADY DONE in Task 4)
- Task 6: Pipeline Integration (ALREADY DONE in Task 4)
- Task 7: Testing (Unit, integration, E2E tests needed)

### File List

**Backend Files to Create:**
- `migrations/22_learning_objective.surql` - Create learning_objective table schema
- `migrations/22_learning_objective_down.surql` - Rollback migration
- `open_notebook/domain/learning_objective.py` - LearningObjective domain model
- `open_notebook/graphs/learning_objectives_generation.py` - 3-node LangGraph workflow
- `prompts/learning_objectives/generate.jinja` - AI prompt template for generation
- `api/routers/learning_objectives.py` - 6 API endpoints (CRUD + generate + reorder)
- `tests/test_learning_objective_domain.py` - Domain model unit tests
- `tests/test_objectives_generation.py` - Workflow unit tests
- `tests/test_learning_objectives_api.py` - API integration tests

**Backend Files to Modify:**
- `api/models.py` - Add 5 Pydantic models (Create, Update, Response, Reorder, BatchGeneration)
- `api/main.py` - Register learning_objectives router

**Frontend Files to Create:**
- `frontend/src/components/admin/LearningObjectivesEditor.tsx` - Drag-drop editor component
- `frontend/src/lib/api/learning-objectives.ts` - API client (6 functions)
- `frontend/src/lib/hooks/use-learning-objectives.ts` - TanStack Query hooks (6 hooks)

**Frontend Files to Modify:**
- `frontend/src/app/(dashboard)/modules/[id]/page.tsx` - Integrate editor in Configure step
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add validation (≥1 objective required)
- `frontend/src/lib/types/api.ts` - Add LearningObjective interface
- `frontend/package.json` - Add react-beautiful-dnd dependency
- `frontend/src/lib/locales/en-US/index.ts` - Add learningObjectives.* keys (20+ keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Add French translations (MANDATORY)

**Story File:**
- `_bmad-output/implementation-artifacts/3-3-learning-objectives-configuration.md` - Comprehensive story documentation

**Task 4 Frontend Files (NEW):**
- `frontend/src/lib/types/api.ts` - Added LearningObjective types (5 interfaces)
- `frontend/src/lib/api/learning-objectives.ts` - API client (6 functions)
- `frontend/src/lib/hooks/use-learning-objectives.ts` - TanStack Query hooks (6 hooks)
- `frontend/src/components/admin/LearningObjectivesEditor.tsx` - Drag-drop editor component
- `frontend/src/lib/locales/en-US/index.ts` - Added learningObjectives section (20 keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Added French translations (20 keys)
- `frontend/src/app/(dashboard)/modules/[id]/page.tsx` - Integrated editor in Configure step
- `frontend/package.json` - Added @hello-pangea/dnd dependency

**Analysis Sources Referenced:**
- `_bmad-output/planning-artifacts/epics.md` - Epic 3 and Story 3.3 requirements
- `_bmad-output/planning-artifacts/architecture.md` - ObjectModel pattern, migrations, LangGraph
- `_bmad-output/planning-artifacts/ux-design-specification.md` - Configure step UX, drag-drop
- `_bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md` - Stepper patterns
- `_bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md` - Generation workflows
- `open_notebook/domain/module_assignment.py` - RecordID coercion pattern
- `open_notebook/graphs/quiz_generation.py` - LangGraph workflow template
- `api/routers/module_assignments.py` - Admin CRUD endpoint patterns
- `frontend/src/components/admin/DocumentUploader.tsx` - Empty state + generation UI
