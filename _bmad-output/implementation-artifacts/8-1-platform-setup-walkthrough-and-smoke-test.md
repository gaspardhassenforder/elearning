# Story 8.1: Platform Setup Walkthrough & Smoke Test

Status: ready-for-dev

## Story

As a **new platform operator/developer**,
I want a complete, tested walkthrough to set up and use the Open Notebook platform from scratch,
So that I can verify all features work end-to-end and have a reference guide for onboarding new team members.

## Acceptance Criteria

1. **Given** a developer clones the repository for the first time
   **When** they follow the setup steps
   **Then** all services (SurrealDB, API, Worker, Frontend) start without errors

2. **Given** the platform is running with JWT_SECRET_KEY configured
   **When** the API starts for the first time
   **Then** a default admin user (`admin`/`changeme`) is auto-created
   **And** database migrations (1-26) run successfully

3. **Given** an admin is logged in
   **When** they complete the admin workflow (create company, create module, upload docs, configure, publish, assign)
   **Then** each step succeeds and the module is visible to a learner

4. **Given** a learner is logged in
   **When** they complete the learner workflow (onboarding, module selection, AI chat, browse sources/artifacts, progress tracking)
   **Then** all features function correctly

5. **Given** the walkthrough is documented
   **When** a new developer reads it
   **Then** they can reproduce the entire setup and feature verification independently

## Tasks / Subtasks

### Phase 1: Environment Setup (AC: #1, #2)

- [ ] **Task 1: Prerequisites & Environment Configuration** (AC: #1)
  - [ ] 1.1 Verify prerequisites (Python 3.11+, Node 18+, Docker, uv)
  - [ ] 1.2 Copy `.env.example` to `.env`
  - [ ] 1.3 Set `JWT_SECRET_KEY` (generate with `openssl rand -base64 32`)
  - [ ] 1.4 Set at least one AI provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.)
  - [ ] 1.5 Verify SurrealDB config defaults (`SURREAL_URL`, `SURREAL_USER`, `SURREAL_PASSWORD`)

- [ ] **Task 2: Start All Services** (AC: #1, #2)
  - [ ] 2.1 Start SurrealDB: `make database` (verify port 8000)
  - [ ] 2.2 Start API: `make api` (verify migrations run, admin seeded, port 5055)
  - [ ] 2.3 Start Worker: `make worker` (background job processing)
  - [ ] 2.4 Start Frontend: `cd frontend && npm install && npm run dev` (port 3000)
  - [ ] 2.5 Verify health: `curl http://localhost:5055/health`
  - [ ] 2.6 Verify API docs: browse `http://localhost:5055/docs`

- [ ] **Task 3: Seed Test Data** (AC: #2)
  - [ ] 3.1 Run `uv run python scripts/seed_test_accounts.py`
  - [ ] 3.2 Verify output: admin user, learner user, Acme Corp company, Welcome Module
  - [ ] 3.3 Credentials: `admin`/`changeme`, `learner`/`learner123`

### Phase 2: Admin Workflow Walkthrough (AC: #3)

- [ ] **Task 4: Admin Login & Dashboard** (AC: #3)
  - [ ] 4.1 Navigate to `http://localhost:3000`
  - [ ] 4.2 Log in as `admin`/`changeme`
  - [ ] 4.3 Verify redirect to admin dashboard
  - [ ] 4.4 Verify admin navigation sidebar items

- [ ] **Task 5: Company Management** (AC: #3)
  - [ ] 5.1 Navigate to Companies section
  - [ ] 5.2 Verify "Acme Corp" exists (from seed)
  - [ ] 5.3 Create a new company (e.g., "Test Corp", slug: "test-corp")
  - [ ] 5.4 Verify company appears in list

- [ ] **Task 6: Create a Learner Account** (AC: #3)
  - [ ] 6.1 Navigate to Users section
  - [ ] 6.2 Create a new learner (`testlearner`/password, assigned to "Test Corp")
  - [ ] 6.3 Verify learner appears in user list with company

- [ ] **Task 7: Module Creation Pipeline** (AC: #3)
  - [ ] 7.1 Navigate to Modules section, click "Create Module"
  - [ ] 7.2 **Upload Step**: Upload 1-2 test documents (PDF, text, or URL)
  - [ ] 7.3 Wait for content processing to complete
  - [ ] 7.4 **Generate Step**: Generate artifacts (quizzes, summaries)
  - [ ] 7.5 Preview generated artifacts
  - [ ] 7.6 **Configure Step**: Review/edit learning objectives
  - [ ] 7.7 **Configure Step**: Write/edit AI teacher prompt
  - [ ] 7.8 **Publish Step**: Review summary and publish module
  - [ ] 7.9 Verify "Published" badge appears

- [ ] **Task 8: Module Assignment** (AC: #3)
  - [ ] 8.1 Navigate to Assignments section
  - [ ] 8.2 Assign the published module to "Acme Corp"
  - [ ] 8.3 Verify assignment appears in matrix
  - [ ] 8.4 Toggle lock/unlock on assignment

### Phase 3: Learner Workflow Walkthrough (AC: #4)

- [ ] **Task 9: Learner Login & Onboarding** (AC: #4)
  - [ ] 9.1 Log out of admin account
  - [ ] 9.2 Log in as `learner`/`learner123`
  - [ ] 9.3 Verify redirect to learner interface
  - [ ] 9.4 Complete onboarding questionnaire (if first login)
  - [ ] 9.5 Verify redirect to module selection after onboarding

- [ ] **Task 10: Module Selection & Access** (AC: #4)
  - [ ] 10.1 Verify module selection screen shows assigned modules
  - [ ] 10.2 Verify locked modules appear with lock icon and 60% opacity
  - [ ] 10.3 Click an unlocked module to enter conversation view

- [ ] **Task 11: AI Chat Experience** (AC: #4)
  - [ ] 11.1 Verify two-panel layout (sources panel + chat panel)
  - [ ] 11.2 Verify AI sends a personalized greeting automatically
  - [ ] 11.3 Send a message and verify SSE streaming response
  - [ ] 11.4 Verify AI uses Socratic method (hints, not direct answers)
  - [ ] 11.5 Verify inline document snippets appear when AI references sources
  - [ ] 11.6 Click "Open in sources" link and verify panel scrolls to document
  - [ ] 11.7 Verify voice input button is present (if browser supports Speech API)

- [ ] **Task 12: Content Browsing** (AC: #4)
  - [ ] 12.1 Click Sources tab - verify source documents listed
  - [ ] 12.2 Click a document card - verify it expands with content
  - [ ] 12.3 Click Artifacts tab - verify artifacts listed (quizzes, podcasts)
  - [ ] 12.4 Click Progress tab - verify learning objectives with checkboxes

- [ ] **Task 13: Learning Progress & Artifacts** (AC: #4)
  - [ ] 13.1 Continue conversation until AI checks off a learning objective
  - [ ] 13.2 Verify ambient progress bar increments
  - [ ] 13.3 Verify objective appears checked in Progress tab
  - [ ] 13.4 Test inline quiz widget if AI surfaces one
  - [ ] 13.5 Test inline audio player if AI surfaces a podcast

- [ ] **Task 14: Persistent Chat & Navigation** (AC: #4)
  - [ ] 14.1 Leave the module and return - verify chat history loads
  - [ ] 14.2 Verify AI sends re-engagement message
  - [ ] 14.3 Test navigation assistant bubble (bottom-right corner)

### Phase 4: Documentation & Bug Reporting (AC: #5)

- [ ] **Task 15: Document Findings** (AC: #5)
  - [ ] 15.1 Record any issues/bugs encountered during walkthrough
  - [ ] 15.2 Note any unclear UX or missing error messages
  - [ ] 15.3 Document any setup steps that were confusing or missing
  - [ ] 15.4 Create follow-up stories for any blocking issues found

## Dev Notes

### Critical Setup Information

#### JWT Authentication (REQUIRED)
```bash
# Generate a secure JWT secret
openssl rand -base64 32

# Add to .env
JWT_SECRET_KEY=<your-generated-secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30    # Optional, default 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7       # Optional, default 7
```

**Without `JWT_SECRET_KEY` set, login will NOT work.** The system falls back to legacy `OPEN_NOTEBOOK_PASSWORD` mode which doesn't support user accounts.

#### Auto-Seeded Admin User
The API automatically creates an admin user on first startup if:
- `JWT_SECRET_KEY` is set
- No users exist in the database

Default credentials: `admin` / `changeme` (override with `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` env vars).

[Source: api/main.py:65-92 `seed_admin_user()`]

#### Seed Script for Test Data
```bash
uv run python scripts/seed_test_accounts.py
```
Creates:
- Company: "Acme Corp" (slug: "acme")
- Admin: `admin` / `changeme`
- Learner: `learner` / `learner123` (assigned to Acme Corp, onboarding pre-completed)
- Module: "Welcome Module" (published, assigned to Acme Corp)

[Source: scripts/seed_test_accounts.py]

#### Service Ports
| Service | Port | URL |
|---------|------|-----|
| SurrealDB | 8000 | ws://localhost:8000/rpc |
| FastAPI API | 5055 | http://localhost:5055 |
| API Docs | 5055 | http://localhost:5055/docs |
| Frontend | 3000 | http://localhost:3000 |

#### Startup Order (Critical)
1. SurrealDB first (3s wait)
2. API second (runs 26 migrations on first start)
3. Worker third (processes async jobs)
4. Frontend last

Use `make start-all` to handle this automatically.

### Known Issues & Workarounds

#### SurrealDB Record Type Mismatch (Fixed in this PR)
- **Issue**: `connection.insert()` requires proper `RecordID` objects for record reference fields (`record<company>`, `record<notebook>`, etc.), but domain models pass plain strings
- **Affected Models**: User (`company_id`), ModuleAssignment (`company_id`, `notebook_id`, `assigned_by`)
- **Fix**: Added `_prepare_save_data()` overrides in User and ModuleAssignment to convert string IDs to RecordIDs
- **Root Cause**: `parse_record_ids()` converts RecordIDs to strings on READ, but no inverse conversion existed for INSERT (UPDATE via SurrealQL auto-coerces)

[Source: open_notebook/domain/user.py, open_notebook/domain/module_assignment.py]

### Architecture & File References

#### Authentication Flow
- JWT auth: `api/auth.py` (token creation/verification, password hashing)
- Auth endpoints: `api/routers/auth.py` (login, register, refresh, logout, /me)
- User service: `api/user_service.py` (registration, admin user creation)
- Frontend auth: `frontend/src/components/providers/AuthProvider.tsx`

#### Database Migrations (26 total)
- User table: Migration 18 (`open_notebook/database/migrations/18.surrealql`)
- Company table: Migration 19
- ModuleAssignment: Migration 20
- LearningObjective: Migration 21
- LearnerObjectiveProgress: Migration 22
- ModulePrompt: Migration 24
- TokenUsage: Migration 26

#### Admin Interface
- Route group: `frontend/src/app/(dashboard)/admin/`
- Module pipeline: Upload → Generate → Configure → Publish
- Company management, user management, module assignment

#### Learner Interface
- Route group: `frontend/src/app/(learner)/`
- Module selection: `(learner)/modules/`
- Conversation view: Two-panel layout (sources + chat)
- Onboarding: `(learner)/onboarding/`

### Project Structure Notes

- Frontend uses route groups: `(dashboard)` for admin, `(learner)` for learner
- API layering: Router → Service → Domain → Database (mandatory pattern)
- All learner queries include company_id filter for data isolation
- AI chat uses two-layer prompt: global system prompt + per-module prompt
- Background jobs (podcasts, quizzes) processed by surreal-commands-worker

### References

- [Source: api/main.py - API startup, lifespan, router registration]
- [Source: api/auth.py - JWT configuration, password hashing]
- [Source: api/routers/auth.py - Auth endpoints]
- [Source: scripts/seed_test_accounts.py - Test data seeding]
- [Source: open_notebook/database/migrations/ - Schema definitions]
- [Source: CONFIGURATION.md - Environment variables reference]
- [Source: Makefile - Service management commands]
- [Source: frontend/src/app/(learner)/ - Learner UI routes]
- [Source: frontend/src/app/(dashboard)/admin/ - Admin UI routes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Seed script `company_id` type mismatch: SurrealDB INSERT requires RecordID, not string
- Seed script `assigned_at` type mismatch: SurrealDB INSERT requires datetime, not ISO string

### Completion Notes List

- Story created as Epic 8, Story 8.1 (new epic: Platform Setup, Testing & Documentation)
- Fixed critical bug: User and ModuleAssignment `_prepare_save_data()` now convert string record references to RecordID objects for SurrealDB INSERT compatibility
- Seed script now works end-to-end: admin, learner, company, and module all created successfully
- This story is primarily a manual QA/walkthrough story - the "dev" work is the walkthrough itself plus documenting findings

### File List

- `open_notebook/domain/user.py` - Added `_prepare_save_data()` override for company_id RecordID conversion
- `open_notebook/domain/module_assignment.py` - Added `_prepare_save_data()` override for record reference fields
- `_bmad-output/implementation-artifacts/8-1-platform-setup-walkthrough-and-smoke-test.md` - This story file
