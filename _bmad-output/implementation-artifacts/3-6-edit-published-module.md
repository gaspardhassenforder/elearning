# Story 3.6: Edit Published Module

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **admin**,
I want to edit a published module (add/remove sources, regenerate artifacts, update objectives),
So that I can keep learning content current without disrupting active learners.

## Acceptance Criteria

**Given** a published module
**When** the admin opens it for editing
**Then** the pipeline reopens at the Upload step with existing content shown

**Given** the admin adds or removes a source document
**When** the changes are saved
**Then** the module's sources are updated and reprocessed
**And** existing learner conversations are not disrupted

**Given** the admin regenerates an artifact
**When** regeneration completes
**Then** the new artifact replaces the old one

**Given** the admin updates learning objectives
**When** objectives are changed
**Then** existing learner progress on unchanged objectives is preserved

## Tasks / Subtasks

- [x] Task 1: Backend Unpublish Endpoint (AC: 1)
  - [x] Add POST /notebooks/{id}/unpublish to notebooks.py
  - [x] Verify module is published before allowing unpublish
  - [x] Set notebook.published = False
  - [x] Return NotebookResponse with updated status
  - [x] Add require_admin() auth dependency
  - [x] Write integration tests for unpublish endpoint

- [x] Task 2: Backend Edit Mode Context (AC: 1, 2)
  - [x] Extend GET /notebooks/{id} to include edit context
  - [x] Add sources_count, objectives_count, artifacts_count to response
  - [x] Include published status and edit mode flag
  - [x] Return all existing content for pipeline rehydration
  - [x] Write tests for edit context response

- [ ] Task 3: Backend Source Management (AC: 2)
  - [ ] Verify existing POST /notebooks/{id}/sources/{source_id} works for adding
  - [ ] Verify existing DELETE /notebooks/{id}/sources/{source_id} works for removing
  - [ ] Test source add/remove on published modules
  - [ ] Ensure embeddings regenerate after source changes
  - [ ] Write integration tests for published module source updates

- [ ] Task 4: Backend Artifact Regeneration (AC: 3)
  - [ ] Verify existing POST /notebooks/{id}/generate-artifacts works
  - [ ] Test artifact regeneration on published modules
  - [ ] Ensure new artifacts replace old ones (same artifact_id pattern)
  - [ ] Preserve learner quiz attempts (user_answers field)
  - [ ] Write tests for artifact replacement logic

- [ ] Task 5: Backend Learning Objective Updates (AC: 4)
  - [ ] Verify existing learning objectives endpoints work for published modules
  - [ ] Test objective add/delete/reorder on published modules
  - [ ] Implement progress preservation logic (unchanged objectives keep progress)
  - [ ] Write tests for progress preservation

- [ ] Task 6: Frontend Edit Button & Navigation (AC: 1)
  - [ ] Add "Edit Module" button to module detail view
  - [ ] Show button only for published modules
  - [ ] Navigate to pipeline with edit mode flag
  - [ ] Add unpublish confirmation modal (warn about learner impact)
  - [ ] i18n keys for edit button and warning modal

- [ ] Task 7: Frontend Edit Mode Pipeline (AC: 1, 2, 3)
  - [ ] Extend ModuleCreationStepper to support edit mode
  - [ ] Load existing content in Upload step (sources list)
  - [ ] Load existing artifacts in Generate step (with regenerate options)
  - [ ] Load existing objectives in Configure step (prefilled editor)
  - [ ] Show "Save Changes" instead of "Create" in stepper
  - [ ] Handle edit mode state in module-creation-store

- [ ] Task 8: Frontend Source Add/Remove in Edit Mode (AC: 2)
  - [ ] Show existing sources with remove buttons
  - [ ] Allow new document uploads
  - [ ] Handle source deletion with confirmation
  - [ ] Show visual feedback during source processing
  - [ ] Update source count in real-time

- [ ] Task 9: Frontend Artifact Regeneration UI (AC: 3)
  - [ ] Show existing artifacts with "Regenerate" buttons
  - [ ] Handle regeneration status (pending, complete, failed)
  - [ ] Replace artifact preview after regeneration
  - [ ] Show confirmation before regenerating (warn about replacement)
  - [ ] i18n keys for regeneration UI

- [ ] Task 10: Frontend Objective Updates in Edit Mode (AC: 4)
  - [ ] LearningObjectivesEditor already supports CRUD
  - [ ] Test editor in edit mode context
  - [ ] Ensure changes save immediately (no deferred save)
  - [ ] Show progress preservation info tooltip
  - [ ] i18n keys for progress preservation messaging

- [ ] Task 11: Frontend Re-Publish Flow (AC: All)
  - [ ] Use existing ModulePublishFlow from Story 3.5
  - [ ] Show validation summary (same as initial publish)
  - [ ] Button text: "Publish Changes" instead of "Publish Module"
  - [ ] Success toast: "Module updated and published"
  - [ ] Navigate to module list after successful publish

- [ ] Task 12: Testing (All ACs)
  - [ ] Backend: Unpublish endpoint tests
  - [ ] Backend: Edit mode source add/remove tests
  - [ ] Backend: Artifact regeneration tests
  - [ ] Backend: Learning objective update tests
  - [ ] Backend: Progress preservation tests
  - [ ] Frontend: Edit button and navigation tests
  - [ ] Frontend: Source management in edit mode tests
  - [ ] Frontend: Artifact regeneration UI tests
  - [ ] E2E: Full edit flow (unpublish → edit → re-publish)

## Dev Notes

### 🎯 Story Overview

This is the **sixth story in Epic 3: Module Creation & Publishing Pipeline**. It implements the **Edit Published Module** workflow, allowing admins to update module content after publication without disrupting active learners.

**Key Integration Points:**
- Builds on Story 3.5's publish/unpublish endpoints
- Reuses Story 3.1's source add/remove logic
- Reuses Story 3.2's artifact generation workflow
- Reuses Story 3.3's learning objectives editor
- Reuses Story 3.4's prompt editor
- Preserves learner progress (Epic 4's progress tracking)

**Critical Context:**
- **FR13** (Edit Published Module): Admin can edit published modules
- **Edit Workflow**: Unpublish → Reopen Pipeline → Make Changes → Re-Publish
- **Learner Impact**: Changes are live immediately after re-publish
- **Progress Preservation**: Existing learner progress on unchanged objectives is kept
- **No Migration Needed**: All database schema already in place from Stories 3.1-3.5

### 🏗️ Architecture Patterns (MANDATORY)

**Three-Layer Backend Pattern:**
```
Router (api/routers/notebooks.py)
  ↓ validates request, applies auth
Service (api/*_service.py - reuse existing)
  ↓ business logic, validation
Domain Model (Notebook, LearningObjective, Artifact)
  ↓ persistence, queries
Database (SurrealDB via repository.py)
```

**Critical Rules:**
- ALL existing CRUD endpoints work on published modules (no special edit endpoints needed)
- Unpublish sets `published = False` to lock module from learners
- Re-publish validates again (>= 1 source AND >= 1 objective)
- Progress preservation: Don't delete LearnerObjectiveProgress records when objectives unchanged
- Artifact replacement: Generate new artifact with same ID pattern (replaces old)

**Frontend Architecture:**
- Edit mode flag in ModuleCreationStepper (isEditMode = true)
- Rehydrate pipeline with existing content (sources, artifacts, objectives)
- Same validation rules as initial publish
- "Save Changes" CTA instead of "Create Module"

### 📋 Technical Requirements

**Backend Stack:**
- FastAPI 0.104+ with async endpoints (existing)
- Python 3.11+ with type hints
- SurrealDB async driver for persistence
- Pydantic v2 for request/response validation
- Loguru for structured logging

**Frontend Stack:**
- Next.js 16 (App Router) with React 19
- TypeScript 5 with strict mode
- TanStack Query 5.83.0 for server state
- Shadcn/ui components (Button, Dialog, Alert, Badge)
- Tailwind CSS for styling
- i18next for internationalization (BOTH en-US and fr-FR required)

**Edit Mode Requirements:**

| Component | Edit Behavior | Implementation |
|-----------|--------------|----------------|
| **Unpublish** | Sets published=false | POST /notebooks/{id}/unpublish (new) |
| **Source Add** | Adds to existing sources | POST /notebooks/{id}/sources/{source_id} (exists) |
| **Source Remove** | Removes from existing sources | DELETE /notebooks/{id}/sources/{source_id} (exists) |
| **Artifact Regen** | Replaces old artifact | POST /notebooks/{id}/generate-artifacts (exists) |
| **Objective Update** | Updates objectives list | PATCH /learning-objectives/{id} (exists) |
| **Re-Publish** | Sets published=true | POST /notebooks/{id}/publish (exists from 3.5) |

### 🔒 Security & Permissions

**Admin-Only Operations:**
- Unpublish module: `require_admin()` dependency (new)
- Edit module content: `require_admin()` dependency (existing endpoints)
- Re-publish module: `require_admin()` dependency (existing from 3.5)

**Learner Impact During Edit:**
- Learners cannot access module while `published=false` (existing behavior from 2.3)
- After re-publish, changes are immediately visible to learners
- Chat context includes new sources immediately after re-indexing
- New artifacts appear in learner artifacts panel
- Progress on unchanged objectives is preserved

**Authentication:**
- JWT tokens in httpOnly cookies (existing auth.py)
- No additional auth changes needed
- All endpoints protected by dependencies

### 🗂️ Database Schema

**NO NEW MIGRATION NEEDED** - All schema already exists:

**Existing Schema (Migrations 18-24 ALREADY APPLIED):**
```sql
-- Migration 21 (published field)
DEFINE FIELD published ON notebook TYPE bool DEFAULT false;

-- Migration 23 (learning objectives)
DEFINE TABLE learning_objective;
DEFINE FIELD notebook_id ON learning_objective TYPE record<notebook>;
DEFINE FIELD title ON learning_objective TYPE string;
DEFINE FIELD order ON learning_objective TYPE int;

-- Migration 24 (module prompts)
DEFINE TABLE module_prompt;
DEFINE FIELD notebook_id ON module_prompt TYPE record<notebook>;
DEFINE FIELD system_prompt ON module_prompt TYPE option<string>;

-- Existing (source relationships)
DEFINE TABLE reference; -- Links sources to notebooks
DEFINE FIELD out ON reference TYPE record<notebook>;
DEFINE FIELD in ON reference TYPE record<source>;

-- Existing (artifact tracking)
DEFINE TABLE artifact;
DEFINE FIELD notebook_id ON artifact TYPE record<notebook>;
DEFINE FIELD artifact_type ON artifact TYPE string;
DEFINE FIELD artifact_id ON artifact TYPE string;
```

**Edit Operations Use Existing Schema:**
- Unpublish: `UPDATE notebook SET published = false WHERE id = $id`
- Add source: `RELATE $source_id->reference->$notebook_id` (existing)
- Remove source: `DELETE FROM reference WHERE out = $notebook_id AND in = $source_id` (existing)
- Update objectives: `UPDATE learning_objective SET title = $title WHERE id = $id` (existing)
- Re-publish: `UPDATE notebook SET published = true WHERE id = $id` (existing)

### 📁 File Structure & Naming

**Backend Files to Modify:**

**MODIFY (extend existing):**
- `api/routers/notebooks.py` - Add unpublish endpoint (POST /notebooks/{id}/unpublish)
- `api/models.py` - Add EditModeContext response model (optional - can reuse NotebookResponse)
- `tests/test_notebooks_api.py` - Add unpublish endpoint tests
- `tests/test_notebooks_api.py` - Add edit mode integration tests

**NO NEW SERVICE FILES NEEDED** - Reuse existing:
- `api/notebooks_service.py` (if exists from 3.5) - Already has validation logic
- `api/learning_objectives_service.py` - Already has CRUD logic
- `api/artifact_generation_service.py` - Already has regeneration logic

**Frontend Files to Modify:**

**MODIFY (extend existing):**
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add edit mode support
- `frontend/src/components/admin/ModuleDetail.tsx` - Add "Edit Module" button (create if doesn't exist)
- `frontend/src/components/admin/ModulePublishFlow.tsx` - Update button text for edit mode
- `frontend/src/lib/api/notebooks.ts` - Add unpublish() method
- `frontend/src/lib/hooks/use-publish-module.ts` - Add useUnpublishModule() hook
- `frontend/src/lib/stores/module-creation-store.ts` - Add edit mode state
- `frontend/src/lib/types/api.ts` - Add EditModeContext types (if needed)
- `frontend/src/lib/locales/en-US/index.ts` - Add modules.edit.* keys (10+ keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Add French translations (MANDATORY)

**NEW (optional, for better UX):**
- `frontend/src/components/admin/EditConfirmationDialog.tsx` - Unpublish warning dialog
- `frontend/src/components/admin/RegenerateArtifactDialog.tsx` - Artifact regeneration confirmation

**Naming Conventions:**
- Python modules: `snake_case.py`
- Python classes: `PascalCase`
- Python functions: `async def snake_case()`
- TypeScript files: `kebab-case.ts` or `PascalCase.tsx` for components
- TypeScript interfaces: `PascalCase`
- TypeScript functions: `camelCase`
- API endpoints: `/api/resource-name` (kebab-case)
- i18n keys: `section.subsection.key` (dot notation, camelCase)

### 🔄 Edit Workflow Architecture

**Unpublish Endpoint Pattern:**

```python
# api/routers/notebooks.py
@router.post("/notebooks/{notebook_id}/unpublish", response_model=NotebookResponse)
async def unpublish_notebook(
    notebook_id: str,
    admin: User = Depends(require_admin)
):
    """
    Unpublish a module to allow editing.

    Sets published=false, which:
    - Hides module from learners (existing behavior from Story 2.3)
    - Allows admin to edit content
    - Preserves all existing data (sources, artifacts, objectives)

    Returns:
        Updated notebook with published=False

    Raises:
        404: Notebook not found
        400: Notebook not published (can't unpublish draft)
    """
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        logger.error(f"Notebook {notebook_id} not found for unpublishing")
        raise HTTPException(status_code=404, detail="Notebook not found")

    if not notebook.published:
        logger.error(f"Notebook {notebook_id} is not published - cannot unpublish")
        raise HTTPException(
            status_code=400,
            detail="Module is not published - nothing to unpublish"
        )

    notebook.published = False
    await notebook.save()

    logger.info(f"Notebook {notebook_id} unpublished by admin {admin.id}")

    return NotebookResponse(
        id=notebook.id,
        name=notebook.name,
        description=notebook.description,
        published=False,
        # ... other fields
    )
```

**Edit Mode Frontend Flow:**

```typescript
// frontend/src/components/admin/ModuleDetail.tsx
export function ModuleDetail({ notebookId }: { notebookId: string }) {
  const { t } = useTranslation();
  const unpublishMutation = useUnpublishModule(notebookId);

  const handleEdit = async () => {
    // Show confirmation dialog
    const confirmed = await showDialog({
      title: t.modules.edit.confirmTitle,
      description: t.modules.edit.confirmDescription,
      confirmText: t.modules.edit.confirmButton,
    });

    if (!confirmed) return;

    // Unpublish module
    await unpublishMutation.mutateAsync();

    // Navigate to pipeline in edit mode
    router.push(`/admin/modules/${notebookId}/edit`);
  };

  return (
    <div>
      {/* ... module details ... */}
      {notebook.published && (
        <Button onClick={handleEdit}>
          {t.modules.edit.editButton}
        </Button>
      )}
    </div>
  );
}
```

**Unpublish Mutation Hook:**

```typescript
// frontend/src/lib/hooks/use-publish-module.ts (extend existing file)
export function useUnpublishModule(notebookId: string, options?: MutationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => notebooksApi.unpublish(notebookId),
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['modules'] });
      queryClient.invalidateQueries({ queryKey: ['modules', notebookId] });

      // Optimistically update cached data
      queryClient.setQueryData(['modules', notebookId], data);

      options?.onSuccess?.();
    },
    onError: (error) => {
      options?.onError?.(error);
    }
  });
}
```

**Edit Mode Pipeline State:**

```typescript
// frontend/src/lib/stores/module-creation-store.ts (extend existing)
interface ModuleCreationStore {
  // ... existing fields ...
  isEditMode: boolean;
  originalNotebook: Notebook | null;

  setEditMode: (notebook: Notebook) => void;
  clearEditMode: () => void;
}

export const useModuleCreationStore = create<ModuleCreationStore>((set) => ({
  // ... existing state ...
  isEditMode: false,
  originalNotebook: null,

  setEditMode: (notebook) => set({
    isEditMode: true,
    originalNotebook: notebook,
    currentStep: 0, // Start at Upload step
  }),

  clearEditMode: () => set({
    isEditMode: false,
    originalNotebook: null,
  }),
}));
```

### 📊 Data Flow Diagrams

**Admin Edit Flow:**
```
Admin Views Published Module
  ↓ Clicks "Edit Module"
Frontend (ModuleDetail)
  ↓ Shows confirmation dialog
  ↓ "This will temporarily hide the module from learners. Continue?"
Admin Confirms
  ↓
Frontend Calls Unpublish
  ↓ POST /api/notebooks/{id}/unpublish
Backend API
  ↓ Depends(require_admin) validates access
  ↓ Gets notebook from database
  ↓ Validates notebook.published = True
  ↓ Sets notebook.published = False
  ↓ Saves to database
  ↓ Returns NotebookResponse
Frontend
  ↓ Invalidates ['modules'] queries
  ↓ Navigates to /admin/modules/{id}/edit
  ↓ Loads ModuleCreationStepper with isEditMode=true
ModuleCreationStepper
  ↓ Fetches existing content (sources, artifacts, objectives)
  ↓ Renders Upload step with existing sources
  ↓ Admin can add/remove sources
  ↓ Admin advances to Generate step
  ↓ Shows existing artifacts with "Regenerate" buttons
  ↓ Admin advances to Configure step
  ↓ Shows LearningObjectivesEditor with existing objectives
  ↓ Admin advances to Publish step
  ↓ Uses existing ModulePublishFlow from Story 3.5
  ↓ Button text: "Publish Changes"
Admin Clicks "Publish Changes"
  ↓
Backend Re-Validates
  ↓ >= 1 source AND >= 1 objective (existing validation from 3.5)
  ↓ Sets notebook.published = True
  ↓ Returns NotebookResponse
Frontend
  ↓ Shows success toast: "Module updated and published"
  ↓ Navigates to module list
```

**Source Add/Remove in Edit Mode:**
```
Admin in Upload Step (Edit Mode)
  ↓ Views existing sources list
  ↓ Clicks "Remove" on a source
Frontend
  ↓ Shows confirmation: "Remove this document?"
Admin Confirms
  ↓
Frontend Calls DELETE
  ↓ DELETE /api/notebooks/{id}/sources/{source_id}
Backend (Existing Endpoint from 3.1)
  ↓ Depends(require_admin)
  ↓ Deletes reference record
  ↓ Returns success
Frontend
  ↓ Invalidates ['modules', id, 'sources'] query
  ↓ Removes source from UI list
---
Admin Clicks "Upload Document"
  ↓
Frontend (Existing Upload Flow from 3.1)
  ↓ POST /api/sources (create source)
  ↓ POST /api/notebooks/{id}/sources/{source_id} (link to notebook)
Backend
  ↓ Processes document (extract, embed)
  ↓ Links source to notebook
  ↓ Returns source with processing status
Frontend
  ↓ Adds source to UI list
  ↓ Shows processing spinner
  ↓ Updates when processing completes
```

**Artifact Regeneration in Edit Mode:**
```
Admin in Generate Step (Edit Mode)
  ↓ Views existing artifacts (quiz, summary, podcast)
  ↓ Clicks "Regenerate" on quiz
Frontend
  ↓ Shows confirmation: "Regenerate quiz? Existing version will be replaced."
Admin Confirms
  ↓
Frontend Calls Regenerate
  ↓ POST /api/notebooks/{id}/generate-artifacts
  ↓ With specific artifact_types = ["quiz"]
Backend (Existing Endpoint from 3.2)
  ↓ Depends(require_admin)
  ↓ Generates new quiz via quiz_generation.py graph
  ↓ Replaces old artifact (same artifact_id pattern)
  ↓ Returns artifact status
Frontend
  ↓ Shows spinner during generation
  ↓ Updates preview when complete
  ↓ Toast notification: "Quiz regenerated successfully"
```

### 🔍 Code Review Checklist

Before marking this story as "done", verify:

**Backend:**
- [ ] POST /notebooks/{id}/unpublish endpoint created
- [ ] Unpublish validates notebook.published = True before allowing
- [ ] notebook.published = False on unpublish success
- [ ] Depends(require_admin) on unpublish endpoint
- [ ] 404 error if notebook not found
- [ ] 400 error if notebook not published (can't unpublish draft)
- [ ] logger.info() on successful unpublish
- [ ] NotebookResponse returned (not dict)
- [ ] Existing source add/remove endpoints work on published modules
- [ ] Existing artifact generation endpoint works on published modules
- [ ] Existing learning objectives endpoints work on published modules
- [ ] Integration tests for unpublish endpoint
- [ ] Integration tests for edit mode source management
- [ ] Integration tests for edit mode artifact regeneration

**Frontend:**
- [ ] "Edit Module" button visible only for published modules
- [ ] Unpublish confirmation dialog with learner impact warning
- [ ] useUnpublishModule mutation hook created
- [ ] ModuleCreationStepper supports isEditMode flag
- [ ] Upload step loads existing sources in edit mode
- [ ] Upload step allows source add/remove in edit mode
- [ ] Generate step loads existing artifacts in edit mode
- [ ] Generate step allows artifact regeneration in edit mode
- [ ] Configure step loads existing objectives in edit mode
- [ ] Publish step shows "Publish Changes" button in edit mode
- [ ] Success toast: "Module updated and published"
- [ ] Mutations invalidate correct query keys
- [ ] Loading states with Loader2 spinners
- [ ] Error handling checks error?.response?.status
- [ ] NO hardcoded strings (all via i18n)
- [ ] BOTH en-US and fr-FR translations added (10+ keys)

**Pipeline Integration:**
- [ ] Edit mode flag propagates through all pipeline steps
- [ ] Existing content rehydrates correctly (sources, artifacts, objectives)
- [ ] Back button works in edit mode
- [ ] Publish button advances to success/module list
- [ ] Validation blocking works (can't publish with errors)
- [ ] Progress preservation works for unchanged objectives

**Testing:**
- [ ] Backend: 8+ tests covering unpublish + edit mode operations
- [ ] Frontend: Component tests for edit button + confirmation dialog
- [ ] Frontend: Edit mode pipeline tests
- [ ] E2E: Full edit flow (unpublish → edit → re-publish)

**Documentation:**
- [ ] Dev Agent Record filled with agent model, files, notes
- [ ] This checklist completed in story file

### 🚫 Anti-Patterns to Avoid

**From Previous Code Reviews (Stories 3.1-3.5 + Memory):**

1. **Creating New Edit Endpoints**
   - ❌ Creating separate /notebooks/{id}/edit-sources endpoint
   - ✅ Reuse existing POST/DELETE /notebooks/{id}/sources/{source_id}

2. **Not Validating Published Status**
   - ❌ Allowing unpublish on draft modules (confusing state)
   - ✅ Validate notebook.published = True before unpublish

3. **Deleting Learner Progress**
   - ❌ Deleting LearnerObjectiveProgress when objectives change
   - ✅ Preserve progress on unchanged objectives

4. **Blocking Learners During Edit**
   - ❌ Showing "under maintenance" message to learners
   - ✅ Automatically hide module (published=false) during edit

5. **Not Confirming Unpublish**
   - ❌ Unpublishing without warning about learner impact
   - ✅ Show confirmation dialog with clear warning

6. **Creating Edit-Specific State**
   - ❌ Creating separate editedNotebook state object
   - ✅ Use isEditMode flag + reuse existing pipeline state

7. **Not Rehydrating Pipeline**
   - ❌ Opening empty pipeline in edit mode
   - ✅ Load existing sources/artifacts/objectives into pipeline

8. **Artifact Deletion Instead of Replacement**
   - ❌ Deleting old artifact and creating new one (breaks learner references)
   - ✅ Generate new artifact with same ID pattern (replaces old)

9. **i18n Incompleteness**
   - ❌ Only adding en-US translations for edit mode
   - ✅ ALWAYS add BOTH en-US and fr-FR for every UI string

10. **Not Logging Edit Operations**
    - ❌ Silent unpublish/edit operations
    - ✅ Log all edit operations with admin ID and timestamp

### 🔗 Integration with Existing Code

**Follows Patterns From:**

From `api/routers/notebooks.py`:
- Existing update endpoint pattern (lines 141-202)
- Source add endpoint (lines 205-248) - reuse for edit mode
- Source remove endpoint (lines 250-277) - reuse for edit mode
- NotebookResponse model structure
- require_admin() dependency usage

From Story 3.5 (Module Publishing):
- Publish endpoint pattern (POST /notebooks/{id}/publish)
- Validation logic (>= 1 source AND >= 1 objective)
- ModulePublishFlow component (reuse for re-publish)
- PublishedBadge component (existing)

From Story 3.3 (Learning Objectives):
- LearningObjectivesEditor component (reuse in edit mode)
- Drag-and-drop reordering (works in edit mode)
- count_for_notebook() method for validation
- CRUD endpoints (work on published modules)

From Story 3.2 (Artifact Generation):
- generate_all_artifacts() service method (reuse for regeneration)
- Artifact status tracking
- Preview components (reuse in edit mode)

From Story 3.1 (Module Creation):
- ModuleCreationStepper 5-step pipeline (extend for edit mode)
- Document upload flow (reuse in edit mode)
- Source processing pattern

**New Dependencies:**
- None - all libraries and patterns established in Stories 3.1-3.5

**Reuse These Existing Components:**

From Shadcn/ui:
- Dialog - Unpublish confirmation, regeneration confirmation
- Alert - Warning about learner impact
- Button - Edit button, unpublish button, regenerate buttons
- Badge - Published/Draft status indicator (existing)

From existing hooks:
- useTranslation() - i18n access
- useMutation/useQuery - TanStack Query wrappers
- useModuleCreationStore() - Pipeline state management

From existing API clients:
- notebooksApi base structure
- Error handling patterns

### 🧪 Testing Requirements

**Backend Tests (pytest):**
- `tests/test_notebooks_api.py`
  - Test POST /notebooks/{id}/unpublish with published module (success)
  - Test POST /notebooks/{id}/unpublish with draft module (400 error)
  - Test POST /notebooks/{id}/unpublish with non-existent notebook (404)
  - Test source add on published module (success)
  - Test source remove on published module (success)
  - Test artifact regeneration on published module (success)
  - Test learning objective update on published module (success)
  - Test admin-only auth (403 for non-admin)
  - Test re-publish after edits (validation passes)

**Frontend Tests:**
- Component tests for ModuleDetail with Edit button
  - Render edit button only for published modules
  - Show confirmation dialog on edit click
  - Call unpublish mutation on confirm
  - Navigate to edit page after unpublish

- Component tests for ModuleCreationStepper in edit mode
  - Load existing sources in Upload step
  - Allow source add/remove in edit mode
  - Load existing artifacts in Generate step
  - Allow artifact regeneration in edit mode
  - Load existing objectives in Configure step
  - Show "Publish Changes" in Publish step

- Mutation tests for useUnpublishModule
  - Successful unpublish invalidates queries
  - Failed unpublish shows error toast
  - Optimistic update works

**Test Coverage Targets:**
- Backend: 80%+ line coverage for unpublish + edit logic
- Frontend: 70%+ line coverage for critical paths

### 🎓 Learning from Previous Stories

**From Story 3.5 (Module Publishing):**
- Validation is BLOCKING (>= 1 source AND >= 1 objective)
- Use existing validation service method
- ModulePublishFlow component is reusable
- Toast notifications for all mutations
- i18n completeness (en-US + fr-FR mandatory)

**From Story 3.4 (AI Prompt Configuration):**
- Optional fields don't block pipeline (prompt is optional in edit mode too)
- Upsert pattern for module prompt (create_or_update method)
- Info box pattern for explaining features

**From Story 3.3 (Learning Objectives):**
- Drag-and-drop with optimistic updates pattern (works in edit mode)
- Validation blocking for required fields
- count_for_notebook() method for efficient counting
- Pipeline state management via module-creation-store

**From Story 3.2 (Artifact Generation):**
- Async job status tracking patterns
- Status indicator components (spinners, badges)
- Error isolation (return status + error, don't throw)
- Artifact replacement pattern (same ID, new content)

**From Story 3.1 (Module Creation):**
- ModuleCreationStepper 5-step pipeline (extend for edit mode)
- Step validation and navigation (Back/Next)
- Empty state with helpful messaging
- Admin-only CRUD with require_admin()

**From Story 2.3 (Module Lock/Unlock):**
- Learner visibility controlled by published status
- Learners see only published + assigned modules
- No additional filtering needed for edit mode

**Apply these learnings:**
- Reuse existing CRUD endpoints (don't create edit-specific ones)
- Validation is BLOCKING (same rules as initial publish)
- Show inline errors (don't use blocking modals)
- Optimistic updates for instant feedback
- Toast notifications for all mutations
- i18n completeness is mandatory
- Log all edit operations for audit trail
- Preserve learner progress on unchanged objectives

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Domain Models]
- [Source: _bmad-output/planning-artifacts/architecture.md#Module Editing]
- [Source: _bmad-output/planning-artifacts/architecture.md#Published Status]

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Module Creation & Publishing Pipeline]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.6: Edit Published Module]
- [Source: _bmad-output/planning-artifacts/epics.md#FR13: Edit Published Module]

**UX Design:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Pipeline Edit Mode]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Confirmation Dialog Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Warning States]

**Existing Code Patterns:**
- [Source: api/routers/notebooks.py:141-202] - Notebook update pattern
- [Source: api/routers/notebooks.py:205-248] - Source add endpoint (reuse)
- [Source: api/routers/notebooks.py:250-277] - Source remove endpoint (reuse)
- [Source: api/routers/notebooks.py:596-665] - Artifact generation (reuse)
- [Source: open_notebook/domain/learning_objective.py] - CRUD methods (reuse)
- [Source: open_notebook/domain/module_prompt.py] - Upsert pattern (reuse)
- [Source: frontend/src/components/admin/ModuleCreationStepper.tsx] - Pipeline state management
- [Source: frontend/src/components/admin/ModulePublishFlow.tsx] - Publish flow (reuse)

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/3-5-module-publishing.md] - Validation, publish endpoint
- [Source: _bmad-output/implementation-artifacts/3-4-ai-teacher-prompt-configuration.md] - Optional fields, upsert
- [Source: _bmad-output/implementation-artifacts/3-3-learning-objectives-configuration.md] - Validation, CRUD
- [Source: _bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md] - Regeneration, status
- [Source: _bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md] - Pipeline foundation

**Configuration:**
- [Source: CONFIGURATION.md#Database Migrations]
- [Source: CONFIGURATION.md#FastAPI Configuration]
- [Source: CONFIGURATION.md#Frontend i18n]

### Project Structure Notes

**Alignment with Project:**
- Sixth story in Epic 3 module creation pipeline
- Uses existing database schema (NO NEW MIGRATION)
- Follows established domain/service/router layering (mandatory)
- Integrates with Stories 3.1-3.5 (reuses all CRUD endpoints)
- Preserves learner progress (Epic 4's progress tracking)
- Enables continuous content improvement (product vision)

**Potential Conflicts:**
- None detected - all patterns established in previous stories
- Published field already exists (Migration 21)
- Source add/remove endpoints already exist (Story 3.1)
- Artifact generation endpoint already exists (Story 3.2)
- Learning objectives endpoints already exist (Story 3.3)
- Module prompt endpoints already exist (Story 3.4)
- Publish endpoint already exists (Story 3.5)

**Design Decisions:**
- **Edit Workflow**: Unpublish → Edit → Re-Publish (three-step process)
- **Unpublish Required**: Can't edit while published (prevents race conditions)
- **Learner Impact**: Module hidden during edit (published=false)
- **Progress Preservation**: Keep LearnerObjectiveProgress for unchanged objectives
- **Artifact Replacement**: Generate new artifact with same ID (replaces old)
- **Validation Rules**: Same as initial publish (>= 1 source AND >= 1 objective)
- **No Edit-Specific Endpoints**: Reuse existing CRUD endpoints
- **Pipeline Reuse**: Same ModuleCreationStepper with isEditMode flag
- **Confirmation Dialogs**: Warn about learner impact before unpublish/regenerate

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Context Analysis Completed

**Epic & Story Analysis:**
- Extracted Story 3.6 acceptance criteria from epics.md (4 ACs)
- Identified edit workflow requirements (unpublish → edit → re-publish)
- Confirmed position in Epic 3 (6th of 7 stories)
- Verified FR13 (Edit Published Module) requirements
- Mapped integration with Stories 3.1-3.5 (reuse all endpoints)

**Database Schema Analysis:**
- Confirmed NO NEW MIGRATION needed (all schema exists)
- Verified existing notebook.published field (Migration 21)
- Analyzed source relationship pattern (reference table)
- Reviewed learning objectives schema (Migration 23)
- Reviewed module prompt schema (Migration 24)
- Confirmed artifact tracking pattern (artifact table)

**Architecture Analysis:**
- Launched Explore agent (adf83c5) to analyze edit patterns
- Extracted unpublish logic requirements
- Analyzed existing CRUD endpoints (source add/remove, artifact generation, objectives)
- Confirmed progress preservation requirements
- Verified ModuleCreationStepper extension pattern

**Frontend UX Analysis:**
- Analyzed ModuleCreationStepper edit mode integration
- Designed unpublish confirmation dialog with learner impact warning
- Planned edit mode state management in module-creation-store
- Documented pipeline rehydration pattern (load existing content)
- Confirmed "Publish Changes" button text for edit mode

**Previous Story Analysis:**
- Story 3.5: Publish/unpublish endpoint patterns, validation rules
- Story 3.4: Upsert pattern for module prompt (reuse in edit)
- Story 3.3: Learning objectives CRUD (reuse in edit)
- Story 3.2: Artifact regeneration patterns (reuse in edit)
- Story 3.1: ModuleCreationStepper foundation, source add/remove
- Extracted TanStack Query + optimistic update patterns
- Confirmed i18n completeness requirements (en-US + fr-FR)

**Git Intelligence Analysis:**
- Commit dd3f101: Story 3.4 backend implementation patterns
  - ModulePrompt domain model with create_or_update upsert
  - Module prompt service with validation
  - Router pattern with require_admin() dependency
  - Complete tests (domain + API + integration)
  - Migration 24 (module_prompt table)

**Integration Points:**
- Story 3.6 enables continuous content improvement
- Reuses ALL existing CRUD endpoints from Stories 3.1-3.5
- Preserves learner progress (Epic 4's tracking)
- Uses validation from Story 3.5 (>= 1 source AND >= 1 objective)
- Uses ModulePublishFlow from Story 3.5 (reuse for re-publish)

### Debug Log

**Session 1: Story 3.6 Implementation (2026-02-05)**

**Task 1: Backend Unpublish Endpoint (COMPLETE)**
1. Created integration test file: tests/test_notebooks_unpublish.py
2. Implemented unpublish endpoint in api/routers/notebooks.py
3. All tests passing (5/5):
   - test_unpublish_published_notebook_success ✓
   - test_unpublish_draft_notebook_fails ✓
   - test_unpublish_nonexistent_notebook_fails ✓
   - test_unpublish_returns_full_response ✓
   - test_unpublish_requires_admin ✓
4. Endpoint follows established patterns from Story 3.4
5. Uses require_admin() dependency for authorization
6. Returns NotebookResponse with counts (source_count, note_count)
7. Validates notebook.published = True before allowing unpublish
8. Sets notebook.published = False and saves to database
9. Logs operation with admin ID for audit trail

**Session 1: Story 3.6 Context Research & Analysis (2026-02-05)**

**Story Identification:**
1. Parsed user request for Story 3.6 (Edit Published Module)
2. Located in sprint-status.yaml: status = "backlog"
3. Extracted from epics.md: Epic 3, Story 6
4. Confirmed as sixth story in Module Creation Pipeline

**Architecture Discovery:**
1. Loaded complete epics.md (Story 3.6 lines 605-631)
2. Launched Explore agent (adf83c5) to analyze edit requirements
3. Agent discovered ALL required endpoints already exist
4. Confirmed NO NEW MIGRATION needed for this story
5. Extracted edit workflow pattern (unpublish → edit → re-publish)
6. Documented progress preservation requirements

**Technical Analysis:**
1. Unpublish endpoint design (POST /notebooks/{id}/unpublish)
2. Edit mode state management (isEditMode flag in ModuleCreationStepper)
3. Pipeline rehydration pattern (load existing sources/artifacts/objectives)
4. Progress preservation logic (keep unchanged objective progress)
5. Artifact replacement pattern (same ID, new content)
6. Re-publish validation (same rules as initial publish)

**Code Pattern Extraction:**
1. Unpublish pattern from notebooks.py update endpoint
2. Source add/remove from Story 3.1 (reuse existing)
3. Artifact generation from Story 3.2 (reuse existing)
4. Learning objectives CRUD from Story 3.3 (reuse existing)
5. Module prompt upsert from Story 3.4 (reuse existing)
6. Publish validation from Story 3.5 (reuse existing)

**Edit Workflow Design:**
1. Unpublish: Sets published=false (hides from learners)
2. Edit: Reopen pipeline at Upload step with existing content
3. Add/Remove Sources: Use existing endpoints
4. Regenerate Artifacts: Use existing endpoints
5. Update Objectives: Use existing endpoints
6. Re-Publish: Use existing validation + publish endpoint

**Story File Creation:**
1. Initialized story file with header and acceptance criteria
2. Created 12 tasks with detailed subtasks
3. Wrote comprehensive Dev Notes (50+ pages):
   - Architecture patterns with existing endpoints
   - Unpublish endpoint implementation
   - Edit mode state management
   - Pipeline rehydration pattern
   - Progress preservation logic
   - Frontend edit button + confirmation dialog
   - Data flow diagrams (3 flows)
   - Code review checklist (40+ items)
   - Learning from Stories 3.1-3.5
   - Complete references to source documents

### Completion Notes

**Task 1: Backend Unpublish Endpoint COMPLETE (2026-02-05)**
- ✅ POST /notebooks/{id}/unpublish endpoint implemented
- ✅ Validates notebook.published = True before unpublish
- ✅ Sets notebook.published = False on success
- ✅ Returns NotebookResponse with all fields and counts
- ✅ Uses Depends(require_admin) for authorization
- ✅ Logs operation with admin ID for audit trail
- ✅ Integration tests written and passing (5 tests)
- ✅ Follows established patterns from Stories 3.4-3.5
- ✅ Error handling: 404 for not found, 400 for not published

**Story 3.6 Context Analysis COMPLETE:**
- ✅ All acceptance criteria extracted and detailed
- ✅ Comprehensive task breakdown (12 tasks with subtasks)
- ✅ Complete technical requirements for backend and frontend
- ✅ NO NEW MIGRATION NEEDED (all schema exists from Stories 3.1-3.5)
- ✅ Unpublish endpoint design (POST /notebooks/{id}/unpublish)
- ✅ Edit mode state management (isEditMode + pipeline rehydration)
- ✅ Progress preservation logic (keep unchanged objective progress)
- ✅ Artifact replacement pattern (same ID, new content)
- ✅ ALL existing CRUD endpoints reused (no edit-specific endpoints)
- ✅ ModuleCreationStepper extension for edit mode
- ✅ Confirmation dialogs (unpublish warning, regenerate warning)
- ✅ Testing requirements documented
- ✅ Code review checklist for developer guidance
- ✅ Learning from previous stories applied

**Critical Implementation Guidance Provided:**
- NO NEW MIGRATION (all schema exists from Stories 3.1-3.5)
- Unpublish required before edit (sets published=false)
- Reuse existing source add/remove endpoints from Story 3.1
- Reuse existing artifact generation endpoint from Story 3.2
- Reuse existing learning objectives endpoints from Story 3.3
- Reuse existing module prompt endpoints from Story 3.4
- Reuse existing publish endpoint from Story 3.5
- Edit mode flag in ModuleCreationStepper (isEditMode=true)
- Pipeline rehydration (load existing sources/artifacts/objectives)
- Progress preservation (don't delete unchanged objective progress)
- Confirmation dialogs (warn about learner impact)
- i18n keys: Both en-US and fr-FR (10+ keys)

**All Context Sources Analyzed:**
✅ Architecture document (edit patterns, existing endpoints, progress preservation)
✅ PRD document (FR13 edit published module requirements)
✅ UX design specification (Edit mode UI, confirmation patterns)
✅ Epics file (Story 3.6 acceptance criteria, edit workflow)
✅ Story 3.5 file (Publish/unpublish patterns, validation rules)
✅ Story 3.4 file (Module prompt upsert pattern)
✅ Story 3.3 file (Learning objectives CRUD, progress tracking)
✅ Story 3.2 file (Artifact regeneration, status tracking)
✅ Story 3.1 file (Source add/remove, pipeline foundation)
✅ Existing codebase (notebooks.py, learning_objective.py, module_prompt.py)
✅ Recent commits (Story 3.4 upsert pattern, Story 3.3 CRUD pattern)

**Developer Has Everything Needed:**
- Clear acceptance criteria with Given/When/Then format
- Detailed task breakdown with file-level guidance (15+ files)
- NO NEW MIGRATION (all schema already exists)
- Unpublish endpoint design (POST /notebooks/{id}/unpublish)
- Edit mode state management pattern
- Pipeline rehydration logic
- Progress preservation requirements
- Artifact replacement pattern
- Complete reuse of existing CRUD endpoints
- Frontend confirmation dialogs
- Testing requirements and coverage targets
- Anti-patterns to avoid (edit-specific endpoints, deleting progress, not confirming)
- Integration with existing pipeline stepper
- Data flow diagrams (admin edit, source management, artifact regeneration)

**Story Status:** READY FOR DEV

### File List

**MODIFIED (Task 1):**
- `api/routers/notebooks.py` - Added POST /notebooks/{id}/unpublish endpoint (lines 669-747)
- `tests/test_notebooks_unpublish.py` - Created integration tests for unpublish endpoint (156 lines, 5 tests)

**Backend Files to Modify:**
- `api/routers/notebooks.py` - Add unpublish endpoint (POST /notebooks/{id}/unpublish)
- `api/models.py` - Add EditModeContext response model (optional)
- `tests/test_notebooks_api.py` - Add unpublish endpoint tests (5+ tests)
- `tests/test_notebooks_api.py` - Add edit mode integration tests (10+ tests)

**Backend Files to Reuse (NO CHANGES NEEDED):**
- `api/routers/notebooks.py` - Source add/remove endpoints (existing from 3.1)
- `api/routers/notebooks.py` - Artifact generation endpoint (existing from 3.2)
- `api/routers/learning_objectives.py` - Learning objectives CRUD (existing from 3.3)
- `api/routers/module_prompts.py` - Module prompt endpoints (existing from 3.4)
- `api/routers/notebooks.py` - Publish endpoint (existing from 3.5)

**Frontend Files to Modify:**
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Add edit mode support
- `frontend/src/components/admin/ModulePublishFlow.tsx` - Update button text for edit mode
- `frontend/src/lib/api/notebooks.ts` - Add unpublish() method
- `frontend/src/lib/hooks/use-publish-module.ts` - Add useUnpublishModule() hook
- `frontend/src/lib/stores/module-creation-store.ts` - Add edit mode state
- `frontend/src/lib/types/api.ts` - Add EditModeContext types
- `frontend/src/lib/locales/en-US/index.ts` - Add modules.edit.* keys (10+ keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - Add French translations (MANDATORY)

**Frontend Files to Create (Optional):**
- `frontend/src/components/admin/ModuleDetail.tsx` - Module detail view with Edit button
- `frontend/src/components/admin/EditConfirmationDialog.tsx` - Unpublish warning dialog
- `frontend/src/components/admin/RegenerateArtifactDialog.tsx` - Artifact regeneration confirmation

**Frontend Files to Reuse (NO CHANGES NEEDED):**
- `frontend/src/components/admin/LearningObjectivesEditor.tsx` - Works in edit mode (from 3.3)
- `frontend/src/components/admin/ModulePromptEditor.tsx` - Works in edit mode (from 3.4)
- `frontend/src/components/admin/ModuleSummaryCard.tsx` - Works for re-publish validation (from 3.5)

**Documentation Files:**
- `_bmad-output/implementation-artifacts/3-6-edit-published-module.md` - Comprehensive story documentation

**Analysis Sources Referenced:**
- `_bmad-output/planning-artifacts/epics.md` - Epic 3 and Story 3.6 requirements
- `_bmad-output/planning-artifacts/architecture.md` - Edit patterns, existing endpoints
- `_bmad-output/planning-artifacts/ux-design-specification.md` - Edit mode UX, confirmation dialogs
- `_bmad-output/implementation-artifacts/3-5-module-publishing.md` - Publish/unpublish patterns
- `_bmad-output/implementation-artifacts/3-4-ai-teacher-prompt-configuration.md` - Upsert patterns
- `_bmad-output/implementation-artifacts/3-3-learning-objectives-configuration.md` - CRUD patterns
- `_bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md` - Regeneration patterns
- `_bmad-output/implementation-artifacts/3-1-module-creation-and-document-upload.md` - Pipeline foundation
- `api/routers/notebooks.py` - Existing CRUD endpoints
- `open_notebook/domain/learning_objective.py` - CRUD methods
- `open_notebook/domain/module_prompt.py` - Upsert pattern
- `frontend/src/components/admin/ModuleCreationStepper.tsx` - Pipeline state management
