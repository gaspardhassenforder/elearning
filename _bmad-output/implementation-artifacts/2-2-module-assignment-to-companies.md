# Story 2.2: Module Assignment to Companies

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **admin**,
I want to assign modules to specific companies,
So that learners in those companies can access the learning content.

## Acceptance Criteria

1. **Given** an admin is logged in **When** they assign a module (notebook) to a company **Then** a ModuleAssignment record is created linking the notebook_id to the company_id

2. **Given** an admin assigns a module that is not yet published **When** the assignment is created **Then** a warning is displayed: "This module is not published yet. Learners will see it once published." **And** the assignment is created successfully (unpublished modules can be pre-assigned)

3. **Given** an admin **When** they view the assignment interface **Then** they see a matrix of modules and companies with assignment status, with unpublished modules visually distinguished

4. **Given** an admin **When** they remove a module assignment from a company **Then** the ModuleAssignment record is deleted **And** learners in that company can no longer see the module

## Tasks / Subtasks

- [x] Task 1: Verify dependencies are complete (AC: all)
  - [x] 1.1: Verify Story 2.1 complete — Company model with get_assignment_count() exists
  - [x] 1.2: Verify require_admin() FastAPI dependency exists
  - [x] 1.3: Verify Company domain model and companies router exist
  - [x] 1.4: If dependencies incomplete, document gaps and defer to prerequisite stories

- [x] Task 2: Create ModuleAssignment database migration (AC: #1)
  - [x] 2.1: Create `open_notebook/database/migrations/20.surrealql` with module_assignment table
  - [x] 2.2: Fields: id, company_id (record<company>), notebook_id (record<notebook>), is_locked (bool default false), assigned_at (datetime), assigned_by (record<user>)
  - [x] 2.3: Add unique index on (company_id, notebook_id) to prevent duplicate assignments
  - [x] 2.4: Create `open_notebook/database/migrations/20_down.surrealql` rollback

- [x] Task 3: Create ModuleAssignment domain model (AC: #1, #4)
  - [x] 3.1: Create `open_notebook/domain/module_assignment.py`
  - [x] 3.2: Inherit from ObjectModel with table_name = "module_assignment"
  - [x] 3.3: Fields: company_id (str), notebook_id (str), is_locked (bool = False), assigned_at (str), assigned_by (Optional[str])
  - [x] 3.4: Add class methods: `get_by_company()`, `get_by_notebook()`, `get_by_company_and_notebook()`
  - [x] 3.5: Add class method `delete_assignment(company_id, notebook_id)` for removing assignments
  - [x] 3.6: Override `needs_embedding()` to return False (not searchable)

- [x] Task 4: Create assignment_service.py (AC: #1, #2, #3, #4)
  - [x] 4.1: Create `api/assignment_service.py`
  - [x] 4.2: `async def assign_module(company_id, notebook_id, assigned_by)` — create assignment, return warning if notebook not published
  - [x] 4.3: `async def unassign_module(company_id, notebook_id)` — delete assignment
  - [x] 4.4: `async def list_assignments()` — return all assignments with company and notebook details
  - [x] 4.5: `async def get_assignment_matrix()` — return matrix of (company, notebook, is_assigned, is_locked, is_published)
  - [x] 4.6: `async def toggle_assignment(company_id, notebook_id, assigned_by)` — create if not exists, delete if exists
  - [x] 4.7: Check notebook.published status for warning (not blocking)
  - [x] 4.8: Logger for all operations, HTTPException for errors

- [x] Task 5: Create module_assignments router (AC: #1, #2, #3, #4)
  - [x] 5.1: Create `api/routers/module_assignments.py`
  - [x] 5.2: POST `/api/module-assignments` — assign module to company (body: {company_id, notebook_id})
  - [x] 5.3: DELETE `/api/module-assignments/{assignment_id}` — remove specific assignment
  - [x] 5.4: DELETE `/api/module-assignments/company/{company_id}/notebook/{notebook_id}` — remove by compound key
  - [x] 5.5: GET `/api/module-assignments` — list all assignments
  - [x] 5.6: GET `/api/module-assignments/matrix` — get assignment matrix for UI
  - [x] 5.7: POST `/api/module-assignments/toggle` — toggle assignment (create/delete)
  - [x] 5.8: All endpoints require `require_admin()` dependency
  - [x] 5.9: Register router in `api/main.py`

- [x] Task 6: Add Pydantic models for assignments (AC: all)
  - [x] 6.1: Add to `api/models.py`: `ModuleAssignmentCreate`, `ModuleAssignmentResponse`, `AssignmentToggleRequest`, `AssignmentMatrixResponse`
  - [x] 6.2: AssignmentMatrixResponse includes: companies list, notebooks list, assignments as {company_id: {notebook_id: {is_assigned, is_locked}}}
  - [x] 6.3: ModuleAssignmentResponse includes warning field for unpublished module message

- [x] Task 7: Add notebook published field check (AC: #2, #3)
  - [x] 7.1: Check if Notebook model has `published` field (may need to add if not exists)
  - [x] 7.2: If not exists, add `published: bool = False` field to Notebook model
  - [x] 7.3: Update assignment_service to check notebook.published for warning message

- [x] Task 8: Create admin assignments page (AC: #1, #2, #3, #4)
  - [x] 8.1: Create `frontend/src/app/(dashboard)/assignments/page.tsx`
  - [x] 8.2: Display AssignmentMatrix component
  - [x] 8.3: Show warning toast when assigning unpublished module
  - [x] 8.4: Handle loading and error states

- [x] Task 9: Create AssignmentMatrix component (AC: #1, #2, #3, #4)
  - [x] 9.1: Create `frontend/src/components/admin/AssignmentMatrix.tsx`
  - [x] 9.2: Matrix grid: rows = companies, columns = modules (notebooks)
  - [x] 9.3: Each cell: checkbox for assigned/unassigned state
  - [x] 9.4: Unpublished modules: column header with muted text and "Draft" badge
  - [x] 9.5: On checkbox change: call toggleAssignment mutation
  - [x] 9.6: Show inline warning when assigning unpublished module
  - [x] 9.7: Use Shadcn Table component with sticky headers
  - [x] 9.8: Handle empty state: "No companies" or "No modules" messages

- [x] Task 10: Create frontend hooks for assignments (AC: all)
  - [x] 10.1: Create `frontend/src/lib/hooks/use-assignments.ts`
  - [x] 10.2: `useAssignmentMatrix()` — TanStack Query for matrix data
  - [x] 10.3: `useToggleAssignment()` — mutation with optimistic update
  - [x] 10.4: `useAssignments()` — list all assignments
  - [x] 10.5: Query key: `['assignments', 'matrix']`
  - [x] 10.6: Invalidate companies query on assignment change (affects assignment_count)

- [x] Task 11: Create frontend API module for assignments (AC: all)
  - [x] 11.1: Create `frontend/src/lib/api/assignments.ts`
  - [x] 11.2: `assignmentsApi.getMatrix()` → GET /api/module-assignments/matrix
  - [x] 11.3: `assignmentsApi.list()` → GET /api/module-assignments
  - [x] 11.4: `assignmentsApi.toggle(companyId, notebookId)` → POST /api/module-assignments/toggle
  - [x] 11.5: `assignmentsApi.assign(companyId, notebookId)` → POST /api/module-assignments
  - [x] 11.6: `assignmentsApi.unassign(companyId, notebookId)` → DELETE /api/module-assignments/company/{company_id}/notebook/{notebook_id}

- [x] Task 12: Add assignment types to frontend (AC: all)
  - [x] 12.1: Add to `frontend/src/lib/types/api.ts`: `ModuleAssignmentResponse`, `AssignmentMatrixResponse`, `AssignmentToggleRequest`
  - [x] 12.2: Ensure types match backend Pydantic models exactly

- [x] Task 13: Add i18n keys for assignments (AC: all)
  - [x] 13.1: Add `assignments` section to `frontend/src/lib/locales/en-US/index.ts`
  - [x] 13.2: Keys: title, assignModule, unassignModule, assigned, unassigned, unpublishedWarning, noCompanies, noModules, assignmentCreated, assignmentRemoved, companies, modules, published, draft, toggleAssignment
  - [x] 13.3: Add same keys with French translations to `frontend/src/lib/locales/fr-FR/index.ts`

- [x] Task 14: Add assignments link to admin sidebar (AC: all)
  - [x] 14.1: Add "Assignments" navigation item to admin sidebar
  - [x] 14.2: Use Link2 or LayoutGrid icon from lucide-react
  - [x] 14.3: Route to `/assignments`

- [x] Task 15: Write backend tests (AC: all)
  - [x] 15.1: Create `tests/test_assignment_service.py`
  - [x] 15.2: Test assign_module — happy path, creates ModuleAssignment record
  - [x] 15.3: Test assign_module — unpublished notebook returns warning message
  - [x] 15.4: Test assign_module — duplicate assignment returns existing (idempotent)
  - [x] 15.5: Test unassign_module — removes assignment record
  - [x] 15.6: Test unassign_module — nonexistent assignment returns 404
  - [x] 15.7: Test get_assignment_matrix — returns correct structure with companies, notebooks, assignments
  - [x] 15.8: Test toggle_assignment — creates when not exists, deletes when exists

- [x] Task 16: Integration test for company deletion with assignments (AC: #4)
  - [x] 16.1: Verify company_service.delete_company() now correctly blocks when assignments exist
  - [x] 16.2: Test from Story 2.1 should pass with real module_assignment table

## Dev Notes

### Architecture Decisions

- **ModuleAssignment is a separate domain model**, not a relationship table. This allows for additional metadata (is_locked, assigned_at, assigned_by) beyond a simple graph edge.
- **Toggle endpoint for UI efficiency**: The matrix UI benefits from a single toggle endpoint rather than separate assign/unassign calls.
- **Unpublished modules can be pre-assigned**: Consultants prepare assignments before publishing. Warning is informational, not blocking.
- **Backend layering MANDATORY:** Router → assignment_service → ModuleAssignment domain → Database

### Critical Implementation Details

**ModuleAssignment Domain Model:**
```python
from typing import ClassVar, Optional
from open_notebook.domain.base import ObjectModel
from open_notebook.database.repository import repo_query

class ModuleAssignment(ObjectModel):
    table_name: ClassVar[str] = "module_assignment"

    company_id: str
    notebook_id: str
    is_locked: bool = False
    assigned_at: Optional[str] = None
    assigned_by: Optional[str] = None

    def needs_embedding(self) -> bool:
        return False  # Not searchable

    @classmethod
    async def get_by_company(cls, company_id: str) -> list["ModuleAssignment"]:
        result = await repo_query(
            "SELECT * FROM module_assignment WHERE company_id = $company_id",
            {"company_id": company_id}
        )
        return [cls(**item) for item in result]

    @classmethod
    async def get_by_notebook(cls, notebook_id: str) -> list["ModuleAssignment"]:
        result = await repo_query(
            "SELECT * FROM module_assignment WHERE notebook_id = $notebook_id",
            {"notebook_id": notebook_id}
        )
        return [cls(**item) for item in result]

    @classmethod
    async def get_by_company_and_notebook(
        cls, company_id: str, notebook_id: str
    ) -> Optional["ModuleAssignment"]:
        result = await repo_query(
            "SELECT * FROM module_assignment WHERE company_id = $company_id AND notebook_id = $notebook_id LIMIT 1",
            {"company_id": company_id, "notebook_id": notebook_id}
        )
        return cls(**result[0]) if result else None

    @classmethod
    async def delete_assignment(cls, company_id: str, notebook_id: str) -> bool:
        result = await repo_query(
            "DELETE FROM module_assignment WHERE company_id = $company_id AND notebook_id = $notebook_id",
            {"company_id": company_id, "notebook_id": notebook_id}
        )
        return True
```

**Migration 20.surrealql:**
```sql
-- Migration 20: Create module_assignment table
DEFINE TABLE module_assignment SCHEMAFULL;

DEFINE FIELD company_id ON module_assignment TYPE record<company>;
DEFINE FIELD notebook_id ON module_assignment TYPE record<notebook>;
DEFINE FIELD is_locked ON module_assignment TYPE bool DEFAULT false;
DEFINE FIELD assigned_at ON module_assignment TYPE datetime DEFAULT time::now();
DEFINE FIELD assigned_by ON module_assignment TYPE option<record<user>>;
DEFINE FIELD created ON module_assignment TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON module_assignment TYPE datetime DEFAULT time::now();

-- Unique constraint: one assignment per company-notebook pair
DEFINE INDEX unique_company_notebook ON module_assignment FIELDS company_id, notebook_id UNIQUE;
```

**assignment_service.py key functions:**
```python
from typing import Optional
from datetime import datetime
from loguru import logger
from fastapi import HTTPException

from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.company import Company
from api.models import ModuleAssignmentResponse, AssignmentMatrixResponse

async def assign_module(
    company_id: str,
    notebook_id: str,
    assigned_by: Optional[str] = None
) -> ModuleAssignmentResponse:
    """Assign a module to a company."""
    logger.info(f"Assigning notebook {notebook_id} to company {company_id}")

    # Check company exists
    company = await Company.get(company_id)
    if not company:
        logger.error(f"Company not found: {company_id}")
        raise HTTPException(status_code=404, detail="Company not found")

    # Check notebook exists
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        logger.error(f"Notebook not found: {notebook_id}")
        raise HTTPException(status_code=404, detail="Module not found")

    # Check if already assigned (idempotent)
    existing = await ModuleAssignment.get_by_company_and_notebook(company_id, notebook_id)
    if existing:
        logger.info(f"Assignment already exists: {existing.id}")
        return _to_response(existing, notebook)

    # Create assignment
    assignment = ModuleAssignment(
        company_id=company_id,
        notebook_id=notebook_id,
        is_locked=False,
        assigned_at=datetime.utcnow().isoformat(),
        assigned_by=assigned_by
    )
    await assignment.save()
    logger.info(f"Created assignment: {assignment.id}")

    return _to_response(assignment, notebook)

def _to_response(assignment: ModuleAssignment, notebook: Notebook) -> ModuleAssignmentResponse:
    """Convert assignment to response with optional warning."""
    warning = None
    is_published = getattr(notebook, 'published', True)  # Default True if field doesn't exist
    if not is_published:
        warning = "This module is not published yet. Learners will see it once published."

    return ModuleAssignmentResponse(
        id=str(assignment.id),
        company_id=assignment.company_id,
        notebook_id=assignment.notebook_id,
        is_locked=assignment.is_locked,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
        warning=warning
    )

async def toggle_assignment(
    company_id: str,
    notebook_id: str,
    assigned_by: Optional[str] = None
) -> dict:
    """Toggle assignment: create if not exists, delete if exists."""
    existing = await ModuleAssignment.get_by_company_and_notebook(company_id, notebook_id)

    if existing:
        # Delete existing assignment
        await ModuleAssignment.delete_assignment(company_id, notebook_id)
        logger.info(f"Removed assignment for company {company_id} notebook {notebook_id}")
        return {"action": "unassigned", "company_id": company_id, "notebook_id": notebook_id}
    else:
        # Create new assignment
        response = await assign_module(company_id, notebook_id, assigned_by)
        return {"action": "assigned", "assignment": response}
```

**Pydantic Models:**
```python
class ModuleAssignmentCreate(BaseModel):
    company_id: str
    notebook_id: str

class ModuleAssignmentResponse(BaseModel):
    id: str
    company_id: str
    notebook_id: str
    is_locked: bool = False
    assigned_at: Optional[str] = None
    assigned_by: Optional[str] = None
    warning: Optional[str] = None  # Unpublished module warning

class AssignmentToggleRequest(BaseModel):
    company_id: str
    notebook_id: str

class AssignmentMatrixCell(BaseModel):
    is_assigned: bool
    is_locked: bool = False
    assignment_id: Optional[str] = None

class CompanySummary(BaseModel):
    id: str
    name: str
    slug: str

class NotebookSummary(BaseModel):
    id: str
    name: str
    published: bool = True

class AssignmentMatrixResponse(BaseModel):
    companies: List[CompanySummary]
    notebooks: List[NotebookSummary]
    assignments: Dict[str, Dict[str, AssignmentMatrixCell]]  # {company_id: {notebook_id: cell}}
```

**AssignmentMatrix Component Structure:**
```tsx
interface AssignmentMatrixProps {}

export function AssignmentMatrix({}: AssignmentMatrixProps) {
  const { t } = useTranslation()
  const { data: matrix, isLoading } = useAssignmentMatrix()
  const toggleMutation = useToggleAssignment()

  if (isLoading) return <Skeleton className="h-96 w-full" />

  if (!matrix?.companies.length) {
    return <EmptyState message={t.assignments.noCompanies} />
  }

  if (!matrix?.notebooks.length) {
    return <EmptyState message={t.assignments.noModules} />
  }

  const handleToggle = async (companyId: string, notebookId: string, notebook: NotebookSummary) => {
    const cell = matrix.assignments[companyId]?.[notebookId]
    const wasAssigned = cell?.is_assigned ?? false

    // Show warning for unpublished modules when assigning
    if (!wasAssigned && !notebook.published) {
      toast.warning(t.assignments.unpublishedWarning)
    }

    await toggleMutation.mutateAsync({ companyId, notebookId })
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="sticky left-0 bg-background">{t.assignments.companies}</TableHead>
          {matrix.notebooks.map(notebook => (
            <TableHead key={notebook.id} className="text-center">
              <div className="flex flex-col items-center gap-1">
                <span className={notebook.published ? '' : 'text-muted-foreground'}>
                  {notebook.name}
                </span>
                {!notebook.published && (
                  <Badge variant="secondary" className="text-xs">
                    {t.assignments.draft}
                  </Badge>
                )}
              </div>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {matrix.companies.map(company => (
          <TableRow key={company.id}>
            <TableCell className="sticky left-0 bg-background font-medium">
              {company.name}
            </TableCell>
            {matrix.notebooks.map(notebook => {
              const cell = matrix.assignments[company.id]?.[notebook.id]
              const isAssigned = cell?.is_assigned ?? false

              return (
                <TableCell key={notebook.id} className="text-center">
                  <Checkbox
                    checked={isAssigned}
                    onCheckedChange={() => handleToggle(company.id, notebook.id, notebook)}
                    disabled={toggleMutation.isPending}
                  />
                </TableCell>
              )
            })}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

**i18n Keys:**
```typescript
// en-US
assignments: {
  title: 'Module Assignments',
  assignModule: 'Assign Module',
  unassignModule: 'Remove Assignment',
  assigned: 'Assigned',
  unassigned: 'Not Assigned',
  unpublishedWarning: 'This module is not published yet. Learners will see it once published.',
  noCompanies: 'No companies created yet. Create a company first.',
  noModules: 'No modules created yet. Create a notebook first.',
  assignmentCreated: 'Module assigned successfully',
  assignmentRemoved: 'Assignment removed',
  companies: 'Companies',
  modules: 'Modules',
  published: 'Published',
  draft: 'Draft',
  toggleAssignment: 'Toggle assignment',
}

// fr-FR
assignments: {
  title: 'Affectations des modules',
  assignModule: 'Affecter un module',
  unassignModule: 'Retirer l\'affectation',
  assigned: 'Affecté',
  unassigned: 'Non affecté',
  unpublishedWarning: 'Ce module n\'est pas encore publié. Les apprenants le verront une fois publié.',
  noCompanies: 'Aucune entreprise créée. Créez d\'abord une entreprise.',
  noModules: 'Aucun module créé. Créez d\'abord un notebook.',
  assignmentCreated: 'Module affecté avec succès',
  assignmentRemoved: 'Affectation retirée',
  companies: 'Entreprises',
  modules: 'Modules',
  published: 'Publié',
  draft: 'Brouillon',
  toggleAssignment: 'Basculer l\'affectation',
}
```

### Existing Code Patterns to Follow

**Domain Model Pattern** (from `open_notebook/domain/company.py`):
- Inherit from ObjectModel
- Use ClassVar for table_name
- All methods are `async def`
- Use repo_query for custom queries
- Logger for all operations

**Service Pattern** (from `api/company_service.py`):
- Services contain business logic
- Call domain models, not database directly
- Logger.info for operations, logger.error before HTTPException
- Return Pydantic response models

**Router Pattern** (from `api/routers/companies.py`):
- FastAPI APIRouter with prefix and tags
- Dependency injection for auth
- Call service functions
- Document endpoints with docstrings

**Frontend Hook Pattern** (from `frontend/src/lib/hooks/use-companies.ts`):
- useQuery for GET operations with query keys
- useMutation with onSuccess invalidation
- Toast notifications on success/error
- Query keys follow `['resource', 'subresource']` pattern

### Dependencies on Other Stories

**MUST be complete before starting this story:**
- **Story 2.1 (Company Management)** — Company model with get_assignment_count() method (already implemented, queries module_assignment table)

**This story enables:**
- **Story 2.3 (Module Lock/Unlock & Learner Visibility)** — Will use ModuleAssignment with is_locked field
- **Epic 4 stories** — Learner module selection will query ModuleAssignment

### What This Story CREATES

**Backend (NEW files):**
- `open_notebook/database/migrations/20.surrealql` — module_assignment table
- `open_notebook/database/migrations/20_down.surrealql` — rollback
- `open_notebook/domain/module_assignment.py` — ModuleAssignment domain model
- `api/assignment_service.py` — Assignment business logic
- `api/routers/module_assignments.py` — Assignment API endpoints
- `tests/test_assignment_service.py` — Backend tests

**Frontend (NEW files):**
- `frontend/src/app/(dashboard)/assignments/page.tsx` — Assignments page
- `frontend/src/components/admin/AssignmentMatrix.tsx` — Matrix component
- `frontend/src/lib/hooks/use-assignments.ts` — TanStack Query hooks
- `frontend/src/lib/api/assignments.ts` — API module

**EXTEND (modify existing files):**
- `api/models.py` — Add assignment Pydantic models
- `api/main.py` — Register module_assignments router
- `frontend/src/lib/types/api.ts` — Add assignment types
- `frontend/src/lib/locales/en-US/index.ts` — Add assignments section
- `frontend/src/lib/locales/fr-FR/index.ts` — Add assignments section (French)
- Dashboard layout sidebar — Add Assignments navigation link

### API Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/module-assignments` | `require_admin()` | Create assignment |
| GET | `/api/module-assignments` | `require_admin()` | List all assignments |
| GET | `/api/module-assignments/matrix` | `require_admin()` | Get matrix for UI |
| POST | `/api/module-assignments/toggle` | `require_admin()` | Toggle assignment |
| DELETE | `/api/module-assignments/company/{company_id}/notebook/{notebook_id}` | `require_admin()` | Remove by compound key |

### Previous Story Intelligence (from Story 2.1)

Key learnings from Story 2.1 implementation:
- Company model already has `get_assignment_count()` that queries `module_assignment` table (returns 0 until this story creates the table)
- CompanyResponse already includes `assignment_count` field
- delete_company() already checks assignment count before allowing deletion
- Frontend companies page already shows assignment_count badge
- i18n pattern established for both en-US and fr-FR

**Integration point:** Once this story creates the module_assignment table, Story 2.1's existing code will automatically start returning real assignment counts.

### Anti-Patterns to Avoid

| DO NOT | DO INSTEAD |
|--------|-----------|
| Use SurrealDB graph edges for assignments | Use dedicated module_assignment table with metadata |
| Block assignment of unpublished modules | Allow with warning message |
| Call database directly from router | Router → assignment_service → ModuleAssignment domain |
| Hardcode strings in UI | Use i18n keys in both en-US and fr-FR |
| Put matrix data in Zustand | Use TanStack Query for server state |
| Create separate assign/unassign endpoints only | Include toggle endpoint for matrix UI efficiency |
| Forget to invalidate companies query | Invalidate on assignment change (affects assignment_count) |
| Silent error handling | `logger.error()` then raise HTTPException |

### Project Structure Notes

- Backend: Router → Service → Domain → Database layering mandatory
- Frontend: `(dashboard)/` route group for admin pages
- Components: `components/admin/` for admin-only components
- i18n: keys in BOTH `en-US` and `fr-FR` locales
- Tests: backend `tests/test_*.py`

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — ModuleAssignment model definition]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Company Management & Module Assignment]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2: Module Assignment to Companies]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Side — Pipeline UX]
- [Source: _bmad-output/implementation-artifacts/2-1-company-management.md — Previous story with assignment_count prep]
- [Source: open_notebook/domain/company.py — Company model with get_assignment_count()]
- [Source: open_notebook/domain/base.py — ObjectModel base class]
- [Source: api/routers/companies.py — Router pattern example]
- [Source: api/company_service.py — Service pattern example]
- [Source: frontend/src/lib/hooks/use-companies.ts — TanStack Query hook pattern]
- [Source: frontend/src/lib/locales/en-US/index.ts — i18n key pattern]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- All 16 tasks completed successfully
- Backend tests: 11 tests in test_assignment_service.py, all passing
- Company deletion tests: 15 tests in test_company_service.py, all passing (includes assignment blocking)
- Fixed datetime.utcnow() deprecation warning in assignment_service.py
- Matrix UI displays companies × notebooks with toggle checkboxes
- Draft badges shown for unpublished modules
- i18n keys added for both en-US and fr-FR locales
- Navigation link added to admin sidebar with LayoutGrid icon

**Code Review Fixes Applied:**
- ✅ Fixed published field default value inconsistency (migration default=false, service layer now matches)
- ✅ Added error handling try/catch in AssignmentMatrix toggle mutation
- ✅ Added validation in toggle_assignment to verify company/notebook exist before processing
- ✅ Updated API docstrings for better OpenAPI documentation (all 5 endpoints)
- ✅ Added per-checkbox loading spinner in AssignmentMatrix (shows which assignment is processing)
- ✅ Fixed test_toggle_assignment_deletes_when_exists to mock Company/Notebook validation
- ✅ All 26 tests passing after fixes

**Note on Git Status:**
Many modified files shown in git status (api/auth.py, 20+ routers, frontend layouts) are from Story 2.1 (User/Company Management) and remain uncommitted. This story (2.2) only adds/modifies the files listed in the File List section below.

### File List

**NEW Backend Files:**
- open_notebook/database/migrations/20.surrealql
- open_notebook/database/migrations/20_down.surrealql
- open_notebook/database/migrations/21.surrealql
- open_notebook/database/migrations/21_down.surrealql
- open_notebook/domain/module_assignment.py
- api/assignment_service.py
- api/routers/module_assignments.py
- tests/test_assignment_service.py

**NEW Frontend Files:**
- frontend/src/app/(dashboard)/assignments/page.tsx
- frontend/src/components/admin/AssignmentMatrix.tsx
- frontend/src/lib/hooks/use-assignments.ts
- frontend/src/lib/api/assignments.ts

**MODIFIED Files:**
- open_notebook/database/async_migrate.py (added migrations 20, 21)
- open_notebook/domain/notebook.py (added published field)
- api/models.py (added assignment Pydantic models)
- api/main.py (registered module_assignments router)
- frontend/src/lib/types/api.ts (added assignment types)
- frontend/src/lib/api/query-client.ts (added assignment query keys)
- frontend/src/lib/locales/en-US/index.ts (added assignments section)
- frontend/src/lib/locales/fr-FR/index.ts (added assignments section)
- frontend/src/components/layout/AppSidebar.tsx (added Assignments nav item)
