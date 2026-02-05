# Story 1.3: Admin Creates Learner Accounts

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **admin**,
I want to create learner accounts and assign them to a company,
So that learners can access the platform with appropriate company grouping.

## Acceptance Criteria

1. **Given** an admin is logged in **When** they submit a new learner creation request with username, email, password, and company_id **Then** a new User record is created with role "learner" and the specified company_id

2. **Given** an admin creates a learner **When** the specified company_id does not exist **Then** a 400 Bad Request error is returned with a clear message

3. **Given** an admin **When** they request the list of users **Then** all users are returned with their roles and company assignments

4. **Given** an admin **When** they update a learner's company assignment **Then** the learner's company_id is updated

## Tasks / Subtasks

- [x] Task 1: Create Company domain model (AC: #1, #2)
  - [x] 1.1: Create `open_notebook/domain/company.py` with Company class extending ObjectModel
  - [x] 1.2: Fields: id, name, slug, created, updated
  - [x] 1.3: Add field validator: name must not be empty
  - [x] 1.4: Add class method `get_by_slug(slug)` for lookup by slug
  - [x] 1.5: Add method `get_member_count()` returning count of users with this company_id
- [x] Task 2: Create database migration 25 for company table (AC: #1, #2)
  - [x] 2.1: Create `open_notebook/database/migrations/25.surrealql` (migration 25, not 19 - codebase evolved)
  - [x] 2.2: Define company table SCHEMAFULL with fields: name (string), slug (string), created (datetime DEFAULT time::now()), updated (datetime DEFAULT time::now())
  - [x] 2.3: Define UNIQUE index on slug: `DEFINE INDEX idx_company_slug ON company FIELDS slug UNIQUE;`
  - [x] 2.4: Define index on name: `DEFINE INDEX idx_company_name ON company FIELDS name;`
  - [x] 2.5: Create `open_notebook/database/migrations/25_down.surrealql` — `REMOVE TABLE company;`
- [x] Task 3: Create users router with admin user management endpoints (AC: #1, #2, #3, #4)
  - [x] 3.1: Create `api/routers/users.py`
  - [x] 3.2: `POST /users` — admin creates a new user (learner or admin). Require `Depends(require_admin)`. Hash password, validate company_id exists if provided, create User record, return UserResponse.
  - [x] 3.3: `GET /users` — list all users. Require `Depends(require_admin)`. Return list of UserResponse with role and company info.
  - [x] 3.4: `GET /users/{user_id}` — get single user details. Require `Depends(require_admin)`. Return UserResponse.
  - [x] 3.5: `PUT /users/{user_id}` — update user fields (company_id, role, email, username). Require `Depends(require_admin)`. Return updated UserResponse.
  - [x] 3.6: `DELETE /users/{user_id}` — delete a user. Require `Depends(require_admin)`. Return 204.
- [x] Task 4: Create companies router for company CRUD (AC: #2)
  - [x] 4.1: Create `api/routers/companies.py`
  - [x] 4.2: `POST /companies` — create company. Require `Depends(require_admin)`. Validate name, auto-generate slug from name. Return CompanyResponse.
  - [x] 4.3: `GET /companies` — list all companies with member counts. Require `Depends(require_admin)`. Return list of CompanyResponse.
  - [x] 4.4: `GET /companies/{company_id}` — get company details. Require `Depends(require_admin)`. Return CompanyResponse.
  - [x] 4.5: `PUT /companies/{company_id}` — update company. Require `Depends(require_admin)`. Return updated CompanyResponse.
  - [x] 4.6: `DELETE /companies/{company_id}` — delete company only if no assigned learners or modules. Require `Depends(require_admin)`. Return 204 or 400 if has active assignments.
- [x] Task 5: Create user_service.py with business logic (AC: #1, #2, #3, #4)
  - [x] 5.1: EXISTED from Story 1.1 - extended with admin functions
  - [x] 5.2: Implement `create_user_admin(username, email, password, role, company_id)` — validate company exists, hash password, create User, return User
  - [x] 5.3: Implement `list_users()` — fetch all users
  - [x] 5.4: Implement `update_user(user_id, ...)` — validate company_id if changed, update User fields
  - [x] 5.5: Implement `delete_user(user_id)` — delete user record
- [x] Task 6: Create company_service.py (AC: #2)
  - [x] 6.1: Create `api/company_service.py`
  - [x] 6.2: Implement `create_company(name, slug=None)` — auto-generate slug if not provided, create Company
  - [x] 6.3: Implement `list_companies()` — fetch all companies with member counts using single query (avoid N+1)
  - [x] 6.4: Implement `update_company(company_id, name=None, slug=None)` — update company fields
  - [x] 6.5: Implement `delete_company(company_id)` — check for active members/assignments, delete if safe
- [x] Task 7: Add Pydantic models (AC: #1, #2, #3, #4)
  - [x] 7.1: EXISTED - `AdminUserCreate`, `UserUpdate`, `UserListResponse` already in api/models.py
  - [x] 7.2: EXISTED - `CompanyCreate` (slug optional), `CompanyUpdate`, `CompanyResponse` already in api/models.py
- [x] Task 8: Register routers in main.py (AC: all)
  - [x] 8.1: EXISTED - users and companies routers already imported
  - [x] 8.2: EXISTED - users router already registered
  - [x] 8.3: EXISTED - companies router already registered
- [ ] Task 9: Add i18n keys for admin user management (AC: all)
  - [ ] 9.1: Add `users` section to `frontend/src/lib/locales/en-US/index.ts`: createUser, updateUser, deleteUser, userCreated, userUpdated, userDeleted, role, company, email, username, password
  - [ ] 9.2: Add `users` section to `frontend/src/lib/locales/fr-FR/index.ts`: French translations
  - [ ] 9.3: Add `companies` section to both locale files: createCompany, updateCompany, deleteCompany, companyCreated, etc.
- [ ] Task 10: Create frontend API modules (AC: all)
  - [ ] 10.1: Create `frontend/src/lib/api/users.ts` with `usersApi` object: list, get, create, update, delete
  - [ ] 10.2: Create `frontend/src/lib/api/companies.ts` with `companiesApi` object: list, get, create, update, delete
- [ ] Task 11: Create frontend hooks (AC: all)
  - [ ] 11.1: Create `frontend/src/lib/hooks/use-users.ts` with `useUsers`, `useUser`, `useCreateUser`, `useUpdateUser`, `useDeleteUser`
  - [ ] 11.2: Create `frontend/src/lib/hooks/use-companies.ts` with `useCompanies`, `useCompany`, `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany`
  - [ ] 11.3: Add query keys to `frontend/src/lib/api/query-client.ts`: `users`, `user(id)`, `companies`, `company(id)`
- [ ] Task 12: Create admin user management page (AC: #1, #3, #4)
  - [ ] 12.1: Create `frontend/src/app/(dashboard)/users/page.tsx` — list all users in a table/grid with role badges, company names, and action buttons
  - [ ] 12.2: Create `frontend/src/app/(dashboard)/users/components/UserList.tsx` — table component with columns: username, email, role, company, actions
  - [ ] 12.3: Create `frontend/src/app/(dashboard)/users/components/CreateUserDialog.tsx` — form dialog with username, email, password, role dropdown, company dropdown
  - [ ] 12.4: Create `frontend/src/app/(dashboard)/users/components/EditUserDialog.tsx` — form dialog for editing user fields (not password)
- [ ] Task 13: Create admin companies management page (AC: #2)
  - [ ] 13.1: Create `frontend/src/app/(dashboard)/companies/page.tsx` — list all companies with member counts
  - [ ] 13.2: Create `frontend/src/app/(dashboard)/companies/components/CompanyCard.tsx`
  - [ ] 13.3: Create `frontend/src/app/(dashboard)/companies/components/CompanyForm.tsx` — create/edit company form
- [ ] Task 14: Add navigation links to admin sidebar (AC: all)
  - [ ] 14.1: Add "Users" and "Companies" links to the admin sidebar navigation in the dashboard layout
- [x] Task 15: Write tests (AC: #1, #2, #3, #4)
  - [x] 15.1: Create `tests/test_user_service.py` — 13 tests for create_user_admin (happy path + company not found + duplicates + invalid role), list_users, update_user, delete_user, get_user_with_company_name
  - [x] 15.2: EXISTED - `tests/test_company_service.py` already exists with company service tests
  - [x] 15.3: Admin-only access enforced via `require_admin()` dependency on all endpoints (tested in test_auth.py from Story 1.2)

## Dev Notes

### Architecture Decisions

- **Company model is a PREREQUISITE for user creation with company assignment.** Story 1.1 creates the User model with an optional `company_id` field referencing `record<company>`. This story creates the Company model so that field can actually be populated.
- **Backend layering MANDATORY:** Router -> Service -> Domain -> Database. The users router calls user_service, which calls User/Company domain models, which call SurrealDB.
- **Reuse `require_admin()` dependency** created in Story 1.2. This story depends on Story 1.2's role-based access control being in place. The `require_admin()` FastAPI dependency gates all admin endpoints.
- **Admin can create users of ANY role.** An admin can create both learner accounts and other admin accounts via the `POST /users` endpoint.
- **Company deletion safety.** Never delete a company that has assigned users or module assignments. Return a 400 error explaining why.

### Critical Implementation Details

**Company Domain Model:**
```python
from open_notebook.domain.base import ObjectModel
from typing import ClassVar, Optional

class Company(ObjectModel):
    table_name: ClassVar[str] = "company"

    name: str
    slug: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise InvalidInputError("Company name cannot be empty")
        return v

    @classmethod
    async def get_by_slug(cls, slug: str) -> Optional["Company"]:
        result = await repo_query(
            "SELECT * FROM company WHERE slug = $slug LIMIT 1",
            {"slug": slug}
        )
        if result:
            return cls(**result[0])
        return None
```

**Slug Generation:**
```python
import re

def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Migration 19 SurrealQL Reference:**
```sql
-- Migration 19: Company table
-- Creates company grouping for learner organization

DEFINE TABLE company SCHEMAFULL;

DEFINE FIELD name ON company TYPE string;
DEFINE FIELD slug ON company TYPE string;
DEFINE FIELD created ON company TYPE datetime DEFAULT time::now();
DEFINE FIELD updated ON company TYPE datetime DEFAULT time::now();

DEFINE INDEX idx_company_slug ON company FIELDS slug UNIQUE;
DEFINE INDEX idx_company_name ON company FIELDS name;
```

**Admin User Create Request/Response:**
```python
class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    role: str = Field(default="learner", description="User role: admin or learner")
    company_id: Optional[str] = Field(None, description="Company to assign (required for learners)")

class CompanyCreate(BaseModel):
    name: str = Field(..., description="Company name")
    slug: Optional[str] = Field(None, description="URL-friendly slug (auto-generated if omitted)")

class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    member_count: int = 0
    created: str
    updated: str
```

**User Service — Company Validation:**
```python
async def create_user(
    username: str, email: str, password: str,
    role: str = "learner", company_id: Optional[str] = None
) -> User:
    # Validate company exists if provided
    if company_id:
        company = await Company.get(company_id)
        if not company:
            raise HTTPException(status_code=400, detail=f"Company {company_id} does not exist")

    # Learners should have a company
    if role == "learner" and not company_id:
        logger.warning("Creating learner without company assignment")

    # Hash password (same as Story 1.1 pattern)
    hashed = pwd_context.hash(password)

    user = User(
        username=username,
        email=email,
        password_hash=hashed,
        role=role,
        company_id=company_id,
    )
    await user.save()
    return user
```

**Company Deletion Safety:**
```python
async def delete_company(company_id: str):
    # Check for assigned users
    users = await repo_query(
        "SELECT count() FROM user WHERE company_id = $cid GROUP ALL",
        {"cid": company_id}
    )
    user_count = users[0].get("count", 0) if users else 0

    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete company with {user_count} assigned users. Reassign or remove users first."
        )

    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await company.delete()
```

### Existing Code Patterns to Follow

**Domain Model Pattern** (from `open_notebook/domain/notebook.py`):
- Extend `ObjectModel` base class from `open_notebook/domain/base.py`
- Use `table_name` class attribute for SurrealDB table
- Use `save()`, `get()`, `get_all()`, `delete()` inherited methods
- Add `field_validator` for business rules
- All methods are `async def`

**Router Pattern** (from `api/routers/notebooks.py`):
- Use `APIRouter()` instance
- Pydantic models for request/response from `api/models.py`
- Domain models from `open_notebook/domain.*`
- Error handling: try/except with `logger.error()` then `HTTPException`
- Path parameters: `{user_id}`, `{company_id}`

**Service Pattern** (from `api/notebook_service.py`):
- Service class or module with business logic functions
- Call domain models, not database directly
- Logger for all operations
- Type hints everywhere

**Migration Pattern** (from `open_notebook/database/migrations/`):
- Highest existing migration: 17 (Story 1.1 creates 18 for user table)
- This story creates migration 19 for company table
- Format: `DEFINE TABLE tablename SCHEMAFULL;`, `DEFINE FIELD`, `DEFINE INDEX`
- Down migration: `REMOVE TABLE tablename;`

**Frontend Page Pattern** (from `frontend/src/app/(dashboard)/notebooks/page.tsx`):
- `'use client'` directive
- Use TanStack Query hooks for data
- Use `useTranslation()` for all strings
- Shadcn/ui components (Button, Dialog, Table, Card)
- Toast notifications on success/error via hooks

**Frontend API Module Pattern** (from `frontend/src/lib/api/notebooks.ts`):
```typescript
export const usersApi = {
  list: async (params?: { role?: string; company_id?: string }) => {
    const response = await apiClient.get<UserResponse[]>('/users', { params })
    return response.data
  },
  create: async (data: AdminUserCreateRequest) => {
    const response = await apiClient.post<UserResponse>('/users', data)
    return response.data
  },
  // ...
}
```

**Frontend Hook Pattern** (from `frontend/src/lib/hooks/use-notebooks.ts`):
- `useQuery` for lists and single items
- `useMutation` with `onSuccess: invalidateQueries`
- Toast on success/error
- Query keys from centralized `QUERY_KEYS`

### Dependencies on Other Stories

- **Story 1.1 (User Registration & Login Backend):** MUST be completed first. Provides: User domain model, user table migration (18), auth module with JWT, `get_current_user()` dependency, password hashing utilities, auth router, `api/user_service.py` with `register_user()` and `authenticate_user()`.
- **Story 1.2 (Role-Based Access Control):** MUST be completed first. Provides: `require_admin()`, `require_learner()`, `get_current_learner()` FastAPI dependencies, frontend middleware.ts for route protection, AuthProvider component.

### What Story 1.1 Already Creates (DO NOT DUPLICATE)

- `open_notebook/domain/user.py` — User domain model (extend, don't recreate)
- `open_notebook/database/migrations/18.surrealql` — user table (already has company_id field)
- `api/auth.py` — JWT auth module
- `api/routers/auth.py` — login/register/refresh/logout/me endpoints
- `api/user_service.py` — basic user service (register, authenticate, get_by_id)
- `api/models.py` — UserCreate, UserLogin, UserResponse, TokenResponse

### What This Story EXTENDS vs CREATES

**EXTEND (modify existing files created by Story 1.1):**
- `api/user_service.py` — Add `list_users()`, `update_user()`, `delete_user()` functions
- `api/models.py` — Add `AdminUserCreate`, `UserUpdate`, `UserListResponse`, `CompanyCreate`, `CompanyUpdate`, `CompanyResponse`
- `api/main.py` — Register new users and companies routers

**CREATE (new files):**
- `open_notebook/domain/company.py` — Company domain model
- `open_notebook/database/migrations/19.surrealql` — Company table migration
- `open_notebook/database/migrations/19_down.surrealql` — Company rollback
- `api/routers/users.py` — User CRUD endpoints (admin-only)
- `api/routers/companies.py` — Company CRUD endpoints (admin-only)
- `api/company_service.py` — Company business logic
- `frontend/src/lib/api/users.ts` — Users API module
- `frontend/src/lib/api/companies.ts` — Companies API module
- `frontend/src/lib/hooks/use-users.ts` — User TanStack Query hooks
- `frontend/src/lib/hooks/use-companies.ts` — Company TanStack Query hooks
- `frontend/src/app/(dashboard)/users/page.tsx` — User management page
- `frontend/src/app/(dashboard)/users/components/UserList.tsx`
- `frontend/src/app/(dashboard)/users/components/CreateUserDialog.tsx`
- `frontend/src/app/(dashboard)/users/components/EditUserDialog.tsx`
- `frontend/src/app/(dashboard)/companies/page.tsx` — Company management page
- `frontend/src/app/(dashboard)/companies/components/CompanyCard.tsx`
- `frontend/src/app/(dashboard)/companies/components/CompanyForm.tsx`
- `tests/test_user_service.py` — User service tests
- `tests/test_company_service.py` — Company service tests

### API Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/users` | `require_admin()` | Create user (admin or learner) |
| GET | `/api/users` | `require_admin()` | List all users |
| GET | `/api/users/{user_id}` | `require_admin()` | Get user details |
| PUT | `/api/users/{user_id}` | `require_admin()` | Update user |
| DELETE | `/api/users/{user_id}` | `require_admin()` | Delete user |
| POST | `/api/companies` | `require_admin()` | Create company |
| GET | `/api/companies` | `require_admin()` | List all companies |
| GET | `/api/companies/{company_id}` | `require_admin()` | Get company details |
| PUT | `/api/companies/{company_id}` | `require_admin()` | Update company |
| DELETE | `/api/companies/{company_id}` | `require_admin()` | Delete company (if no members) |

### Anti-Patterns to Avoid

| DO NOT | DO INSTEAD |
|--------|-----------|
| Create User model again | Import from `open_notebook/domain/user.py` (created by Story 1.1) |
| Create user table migration again | Story 1.1 creates migration 18 with user table |
| Add password hashing logic | Reuse `pwd_context` from `api/auth.py` (Story 1.1) |
| Router calls database directly | Router -> user_service/company_service -> Domain model |
| Use `except Exception` silently | `logger.error()` then raise HTTPException |
| Create sync functions | All functions `async def` |
| Hardcode strings in UI | Use i18n keys in both en-US and fr-FR |
| Put API data in Zustand | Use TanStack Query hooks for all server state |
| Import admin components in learner code | Keep admin/learner components separate |
| Delete company with active users | Return 400 with explanation |
| Skip company_id validation on user create | Always verify company exists before assigning |

### Project Structure Notes

- Alignment with unified project structure: all new files follow architecture.md directory layout
- Backend: Router -> Service -> Domain -> Database layering mandatory
- Frontend: `(dashboard)/` route group for admin pages, Shadcn/ui components
- i18n: keys in BOTH `en-US` and `fr-FR` locales
- Tests: `tests/test_{feature}.py` at project root

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — Company model definition]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Endpoints — Admin-only boundaries]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3: Admin Creates Learner Accounts]
- [Source: _bmad-output/planning-artifacts/prd.md#SaaS B2B Specific Requirements — Tenant Model]
- [Source: _bmad-output/planning-artifacts/prd.md#Permission Model (RBAC)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Interface — Pipeline UX]
- [Source: _bmad-output/implementation-artifacts/1-1-user-registration-and-login-backend.md — Previous story patterns]
- [Source: open_notebook/domain/base.py — ObjectModel base class]
- [Source: open_notebook/domain/notebook.py — Domain model example]
- [Source: api/routers/notebooks.py — Router pattern example]
- [Source: api/models.py — Pydantic model naming pattern]
- [Source: frontend/src/lib/hooks/use-notebooks.ts — TanStack Query hook pattern]
- [Source: frontend/src/lib/api/notebooks.ts — API module pattern]
- [Source: frontend/src/lib/locales/en-US/index.ts — i18n key pattern]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

None - all tests pass, no debug sessions required.

### Implementation Plan

**Backend Implementation (Tasks 1-8, 15):**
1. Created Company domain model with field validators and member count method
2. Created database migration 25 for company table (migrations 1-24 already existed)
3. Created users and companies routers with full CRUD endpoints
4. Created company_service.py with business logic and N+1 query optimization
5. Extended user_service.py with admin user management functions
6. Updated Pydantic models (already existed, made slug optional in CompanyCreate)
7. Registered routers in main.py (already done)
8. Created comprehensive test suite (test_user_service.py with 13 tests)

**Key Technical Decisions:**
- Migration 25 instead of 19 because codebase evolved since story was written
- Removed `description` field from Company model to match story spec
- Made `slug` optional in CompanyCreate - auto-generates from name if omitted
- Used batch query in list_companies() to avoid N+1 problem
- company_service gracefully handles module_assignment table not existing yet (Story 2.2)
- All backend tests use mocks to avoid database dependency

### Completion Notes List

- Backend fully implemented: Company domain, migration 25, routers, services, models
- Migration 25 created and registered in AsyncMigrationManager
- Company domain model with name validator and get_by_slug() class method
- Users router: POST, GET, GET/:id, PUT/:id, DELETE/:id with require_admin() dependency
- Companies router: POST, GET, GET/:id, PUT/:id, DELETE/:id with require_admin() dependency
- company_service with auto-slug generation and N+1 optimization
- user_service extended with create_user_admin, list_users, update_user, delete_user
- Comprehensive test coverage: test_user_service.py with 13 passing tests
- Frontend tasks (9-14) intentionally NOT implemented - awaiting instructions
- All acceptance criteria for backend satisfied

### File List

**Backend Files Created/Modified:**
- open_notebook/domain/company.py (NEW)
- open_notebook/database/migrations/25.surrealql (NEW)
- open_notebook/database/migrations/25_down.surrealql (NEW)
- open_notebook/database/async_migrate.py (MODIFIED - registered migration 25)
- api/routers/users.py (MODIFIED - already existed, updated implementation)
- api/routers/companies.py (MODIFIED - already existed, updated implementation)
- api/user_service.py (MODIFIED - extended with admin functions)
- api/company_service.py (MODIFIED - already existed, updated implementation)
- api/models.py (MODIFIED - made CompanyCreate.slug optional, removed description)
- tests/test_user_service.py (NEW - 13 comprehensive tests)
