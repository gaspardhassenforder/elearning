---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
status: complete
lastStep: 8
completedAt: '2026-02-04'
inputDocuments:
  - "prd.md"
  - "product-brief-open-notebook-2026-02-04.md"
  - "ux-design-specification.md"
  - "prd-validation-report.md"
workflowType: 'architecture'
project_name: 'open-notebook'
user_name: 'Gaspard.hassenforder'
date: '2026-02-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

52 functional requirements across 10 domains:

| Domain | FRs | Architectural Significance |
|--------|-----|---------------------------|
| **Authentication & User Management** | FR1-FR6 | JWT auth, role-based access (Admin/Learner), onboarding questionnaire, company grouping |
| **Module Management (Admin)** | FR7-FR14 | CRUD on modules (1:1 notebook mapping), artifact generation pipeline, learning objectives editor, per-module AI prompt config, admin AI assistant |
| **Module Assignment & Availability** | FR15-FR17 | Company-level assignment, lock/unlock (phased availability), filtered visibility |
| **Learner AI Chat Experience** | FR18-FR31 | Proactive AI teacher, two-layer prompt system, streaming responses, inline document snippets, learning objectives tracking through conversation, async task handling, persistent chat history, fast-track for advanced learners |
| **Learner Content Browsing** | FR32-FR35 | Side panel with sources and artifacts, full document viewer, progress display |
| **Learner Platform Navigation** | FR36-FR38 | Platform-wide AI navigation assistant (separate from module teacher), cross-module search |
| **Learner Voice Input** | FR39-FR41 | Voice recording, transcription, review/edit before send |
| **Error Handling & Observability** | FR42-FR46 | Graceful degradation, structured contextual logging, admin notification, LangSmith integration |
| **Data Privacy & Architecture** | FR47-FR50 | Per-company data isolation, complete user/company deletion, token usage tracking |
| **Learner Transparency & Async** | FR51-FR52 | Details view toggle (function calls, thinking tokens), persistent async task indicators |

**Non-Functional Requirements:**

16 NFRs across 4 domains:

| Domain | NFRs | Key Constraints |
|--------|------|-----------------|
| **Performance** | NFR1-NFR5 | Token streaming, non-blocking function calls, async long-running tasks, responsive side panel, 5-10 concurrent users |
| **Security** | NFR6-NFR10 | Standard auth best practices, per-company isolation, TLS, RBAC on API, session expiry |
| **Scalability** | NFR11-NFR13 | 5-10 concurrent users MVP, no single-user assumptions, growing data volumes |
| **Observability** | NFR14-NFR16 | Structured contextual logs, LangSmith tracing, automatic error notifications |

### UX Architectural Implications

From the UX Design Specification:

- **Two independent frontends** - Learner (fresh, minimalist, chat-first) and Admin (streamlined pipeline). Different design philosophies, effectively two apps sharing a backend. UX spec explicitly states: do NOT base on existing open-notebook UI.
- **assistant-ui library** - Primary component library for learner chat interface. Built on Radix, supports streaming, custom message parts, tool call visualization. Chat is the hero interface.
- **react-resizable-panels** - Split panel layout (sources + chat), drag resize, keyboard accessibility, state persistence.
- **Streaming requirement** - Token-by-token streaming via SSE, compatible with assistant-ui's streaming protocol.
- **Internationalization** - French as primary language for learner interface, minimal EN toggle. `next-intl` for implementation. UI chrome translated, AI messages remain in conversation language.
- **WCAG 2.1 Level AA** - Accessibility target. Keyboard navigation, screen reader support, focus management in chat, reduced motion support.
- **Desktop-only MVP** - No mobile responsive design needed.
- **Design Direction A (Minimal Warmth)** - Flowing text AI messages (no bubbles), subtle user message background, ChatGPT-like minimal chrome. Warm neutral color palette.

### Scale & Complexity Assessment

**Project Complexity: Medium**

- **Primary domain:** Full-stack web application with AI-heavy backend
- **Complexity drivers:** Proactive AI teacher (prompt engineering + two-layer system), real-time streaming, async task management, two independent frontend experiences, brownfield integration
- **Simplifying factors:** Single-instance deployment, simple RBAC (2 roles), company-as-label tenancy, existing codebase provides foundation, 5-10 concurrent users MVP
- **Estimated architectural components:** ~15-20 (auth, 2 frontends, API layer, AI orchestration, streaming, async jobs, database, file processing, embeddings, prompt management, error handling, observability, i18n)

### Brownfield Context

This is a brownfield project building on the existing open-notebook codebase. Understanding what exists vs. what's new is critical:

| Layer | Exists (Reuse) | New (Build) |
|-------|----------------|-------------|
| **Database** | SurrealDB, migrations framework, base models (Notebook, Source, Note) | User model with roles, company grouping, module assignment, learning objectives, token tracking |
| **API** | FastAPI framework, router pattern, CORS, base endpoints | Auth endpoints (JWT), user management, company/assignment APIs, learning objectives API, error notification system |
| **AI Orchestration** | LangGraph workflows (chat, source processing, podcast, transformation), Esperanto multi-provider, ModelManager | Proactive teacher prompt system (two-layer), learning objectives assessment in chat, navigation assistant, admin AI assistant |
| **Content Processing** | content-core (50+ file types), embeddings, vector search, RAG | No changes expected |
| **Artifact Generation** | Quiz generation, podcast creation, summaries, transformations | On-the-fly generation by AI teacher (post-MVP) |
| **Async Jobs** | surreal-commands job queue, command status polling | Persistent visual indicators on frontend, AI conversation continuity during async |
| **Frontend** | Existing Next.js app (to be largely replaced for learner side) | Learner frontend (new, chat-first with assistant-ui), Admin frontend (simplified pipeline), i18n |
| **Observability** | Basic logging | Structured contextual error logging, LangSmith integration, admin notifications, token tracking |

### Technical Constraints & Dependencies

**Hard Constraints (from existing codebase):**
- SurrealDB as database (graph model, vector search, async driver)
- FastAPI as API framework (async-first)
- LangGraph for AI workflows (state machines)
- Esperanto for multi-provider AI abstraction
- Next.js for frontend
- Docker for deployment
- Python 3.11+ backend, TypeScript frontend

**External Dependencies:**
- AI model providers (OpenAI, Anthropic, Google, etc.) via Esperanto
- content-core library for file extraction
- podcast-creator library for audio generation
- LangSmith for LLM observability/tracing
- Browser Speech API or third-party for voice-to-text (FR39-41)

**Infrastructure:**
- Single-instance deployment (Docker Compose)
- SQLite for LangGraph checkpoint storage
- File storage for uploads and generated content

### Cross-Cutting Concerns Identified

1. **Authentication & Authorization** - Touches every API endpoint and both frontends. JWT tokens, role checks, company-scoped data queries.

2. **Company Data Isolation** - Application-level filtering on all learner-facing queries. Every data access must scope by company. GDPR-aware deletion capability.

3. **Streaming Architecture** - Token streaming from AI providers through API to frontend. SSE transport. Must be compatible with assistant-ui on the frontend and LangGraph on the backend.

4. **Error Handling & Resilience** - Structured contextual logging across all layers. Graceful degradation (AI continues conversation when tools fail). Rolling context buffer. Admin notification pipeline.

5. **Token Usage Tracking** - Capture at AI orchestration layer for all LLM calls. Per-company attribution. No UI for MVP but data model must support future reporting.

6. **Async Task Management** - Consistent pattern for long-running operations (podcasts, complex artifacts). Job submission, status polling, completion notification, persistent visual indicators on frontend.

7. **Internationalization** - French primary, English secondary for learner frontend. Translation layer in frontend only. AI conversation language separate from UI language.

8. **Prompt Management** - Two-layer system (global + per-module) for AI teacher. Separate prompts for navigation assistant and admin AI assistant. Prompt versioning consideration for future.

9. **Observability** - LangSmith integration for full AI chain tracing. Structured error logs. Performance monitoring for streaming latency and concurrent users.

## Starter Template Evaluation

### Brownfield Context

This is a brownfield project. No starter template needed - the existing open-notebook codebase provides the foundation. The evaluation focuses on **how to extend** the existing stack.

### Existing Technical Stack (Locked)

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend Framework | Next.js (App Router) | 16.1.1 |
| Frontend Language | TypeScript | 5 |
| UI Primitives | Shadcn/ui + Radix | Latest |
| State Management | Zustand | 5.0.6 |
| Data Fetching | TanStack Query | 5.83.0 |
| Styling | Tailwind CSS | 4 |
| i18n | i18next + react-i18next | 25.7.3 / 16.5.0 |
| Backend Framework | FastAPI | 0.104+ |
| Backend Language | Python | 3.11-3.12 |
| AI Workflows | LangGraph | 1.0.5+ |
| AI Providers | Esperanto | 2.13+ |
| Database | SurrealDB | v2 |
| Deployment | Docker + supervisord | Multi-stage |

### Frontend Strategy Decision

**Decision: Single Next.js App with Route Groups**

Three options evaluated:
- **Option A: Route Groups** (Selected) - Extend existing Next.js app with `(admin)` and `(learner)` route groups
- **Option B: Two Separate Apps** - Rejected: duplicate infrastructure, shared code sync burden, solo developer overhead
- **Option C: Monorepo** - Rejected: excessive build tooling for team size

**Rationale:**
- Solo developer project - minimize infrastructure complexity
- Next.js App Router designed for this pattern via route groups
- Code splitting ensures zero cross-loading between learner and admin
- Shared utilities (API client, auth, i18n, types) stay DRY
- Dynamic imports handle heavy libraries (assistant-ui) per route group
- Existing codebase already uses route groups - natural extension

**Proposed Route Structure:**

```
frontend/src/app/
├── (auth)/login/           # Shared login (existing)
├── (admin)/                # Renamed from (dashboard)
│   ├── layout.tsx          # Admin layout (Shadcn sidebar)
│   ├── notebooks/          # Existing admin routes
│   ├── companies/          # New: company management
│   └── assignments/        # New: module assignment
├── (learner)/              # New route group
│   ├── layout.tsx          # Learner layout (minimal, chat-first)
│   ├── onboarding/         # Questionnaire
│   ├── modules/            # Module selection
│   └── modules/[id]/       # Chat + sources + artifacts
└── layout.tsx              # Root: providers, auth guard, role routing
```

### New Libraries Required

| Library | Purpose | Target |
|---------|---------|--------|
| @assistant-ui/react | AI chat interface (streaming, message parts, tool calls) | Learner chat |
| react-resizable-panels | Split panel layout (sources + chat) | Learner module view |
| jose | JWT token handling (frontend) | Auth upgrade |

### i18n Decision

**Keep i18next** (existing). Already implemented with en-US and fr-FR translations, custom type-safe hook, browser language detection. Switching to next-intl would require rewriting all translations for no benefit.

### Backend Extension Strategy

No new backend framework. Extend FastAPI with:

| Addition | Purpose |
|----------|---------|
| New routers | Auth (JWT), users, companies, assignments, learning objectives |
| New domain models | User, Company, LearningObjective, ModuleAssignment |
| New migrations | SurrealQL for new models and relationships |
| Auth upgrade | Replace PasswordAuthMiddleware with JWT-based auth |
| SSE endpoint | Streaming for assistant-ui compatibility |
| New LangGraph nodes | Proactive teacher behavior, objective tracking in chat graph |

### Initialization Sequence

1. Restructure frontend routes - Rename `(dashboard)` → `(admin)`, create `(learner)` route group
2. Install new frontend dependencies - `assistant-ui`, `react-resizable-panels`, `jose`
3. Create new database migrations - User, Company, Assignment, LearningObjective models
4. Upgrade auth middleware - Password → JWT
5. Extend API routers - New endpoints for user/company/assignment management

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. JWT authentication with python-jose + passlib
2. Role-based access via FastAPI dependency injection
3. New domain models (User, Company, ModuleAssignment, LearningObjective, LearnerObjectiveProgress, ModulePrompt, TokenUsage)
4. Application-level company data isolation on all learner queries
5. SSE streaming for chat (assistant-ui compatible), REST polling for async tasks
6. Two-layer prompt system (global + per-module) with Jinja2 templates

**Important Decisions (Shape Architecture):**
7. Continue AsyncMigrationManager with sequential numbering
8. Structured error handling with rolling context buffer and graceful AI degradation
9. LangSmith for AI tracing, Loguru for app logs, admin webhook notifications

**Deferred Decisions (Post-MVP):**
- WebSocket for real-time notifications (polling sufficient)
- Per-company database isolation (app-level filtering sufficient)
- SSO/OAuth integration (simple JWT for MVP)
- CDN/static asset optimization (small user base)
- Horizontal scaling (vertical sufficient for 5-10 users)
- Prompt versioning (simple text storage for MVP)

### Authentication & Security

**JWT Implementation: python-jose + passlib**

| Aspect | Decision |
|--------|----------|
| Library | python-jose (JWT), passlib with bcrypt (password hashing) |
| Access token | Short-lived (30min), carries user_id, role, company_id |
| Refresh token | Long-lived (7 days), for session continuity |
| Storage | httpOnly cookies (more secure than localStorage) |
| Middleware | Replace existing PasswordAuthMiddleware |

**Role-Based Access Control:**

| Pattern | Implementation |
|---------|---------------|
| User extraction | `get_current_user()` FastAPI dependency |
| Admin gate | `require_admin()` dependency |
| Learner gate | `require_learner()` dependency |
| Company scoping | Automatic on learner routes via middleware |
| Application | Per-router or per-endpoint |

### Data Architecture

**New Domain Models:**

```
User (NEW)
├── id, username, email, password_hash
├── role: admin | learner
├── company_id (for learners)
├── profile: { ai_familiarity, job_type, job_description }
├── onboarding_completed: bool
└── created_at, updated_at

Company (NEW)
├── id, name, slug
├── created_at
└── relationships → assigned modules, member users

ModuleAssignment (NEW - relationship table)
├── company_id → Company
├── notebook_id → Notebook (existing)
├── is_locked: bool
├── assigned_at
└── assigned_by (admin user_id)

LearningObjective (NEW)
├── id, notebook_id → Notebook
├── text: string
├── order: int
├── auto_generated: bool
└── created_at

LearnerObjectiveProgress (NEW - per user per objective)
├── user_id → User
├── objective_id → LearningObjective
├── status: not_started | in_progress | completed
├── completed_via: conversation | quiz
├── completed_at
└── evidence: string (AI's reasoning for checking it off)

ModulePrompt (NEW)
├── notebook_id → Notebook
├── system_prompt: string (per-module AI teacher instructions)
├── updated_at
└── updated_by

TokenUsage (NEW)
├── id, timestamp
├── user_id → User
├── company_id → Company
├── notebook_id → Notebook
├── model_provider, model_name
├── input_tokens, output_tokens
├── operation_type: chat | quiz_gen | podcast_gen | embedding | etc.
└── cost_estimate (optional)
```

**Data Isolation Pattern:**
- All learner-facing queries include `WHERE company_id = $user.company_id`
- Implemented as reusable query builder or FastAPI dependency
- Admin queries have no company filter (see all)

**Migration Strategy:**
- Continue using existing AsyncMigrationManager
- New migrations numbered sequentially after existing 17
- Each new model gets its own migration file

### API & Communication Patterns

**Streaming Architecture: SSE for Chat + REST Polling for Async Tasks**

| Pattern | Use Case | Implementation |
|---------|----------|---------------|
| SSE (Server-Sent Events) | AI chat token streaming | FastAPI `StreamingResponse`, assistant-ui native SSE support |
| REST polling | Async task status (podcasts, artifacts) | Existing `surreal-commands` pattern via `/commands/{id}` |

**assistant-ui Integration:**
- API translates LangGraph streaming output into assistant-ui's expected protocol
- Tool calls (document retrieval, quiz generation) streamed as structured message parts
- Post-MVP: consider WebSockets for real-time task notifications if polling becomes a UX issue

### Prompt Management Architecture

**Two-Layer Prompt System:**

```
Layer 1: Global System Prompt (stored in config/DB)
├── Defines: proactive teaching personality, Socratic method rules,
│            pedagogical discipline, response format, tool usage
├── Updated by: system admin (rare)
└── Applied to: ALL learner chat sessions

Layer 2: Per-Module Prompt (stored per Notebook via ModulePrompt)
├── Defines: topic focus, industry context, tone adjustments,
│            specific teaching strategies, example scenarios
├── Updated by: admin per module
└── Applied to: chat sessions within that specific module

Prompt Assembly (at chat invocation):
final_system_prompt = global_prompt + "\n\n" + module_prompt

Context Injection (dynamic, per turn):
├── Learner profile (role, AI familiarity, job description)
├── Learning objectives (with completion status)
├── Conversation history (from LangGraph checkpoint)
└── Retrieved RAG context (from source documents)
```

**Storage:**
- Global prompt: database config table or environment variable
- Per-module prompt: ModulePrompt record linked to Notebook
- Prompt templates use Jinja2 (existing ai-prompter library) for dynamic variables

### Error Handling & Observability

**Structured Error Handling:**

```
Frontend Error Boundary
├── React ErrorBoundary (existing) for component crashes
├── API error interceptor in axios client
├── Toast notifications for user-facing errors (sonner, existing)
└── AI chat: graceful degradation messages inline

API Error Handling
├── FastAPI exception handlers (global)
├── Structured error response: { error, code, detail, context }
├── Rolling context buffer: last N operations logged per request
├── On error: flush context buffer to structured log
└── Error notification: webhook/email to admin

AI Error Handling
├── LangGraph node-level try/catch
├── Tool call failures: AI continues conversation, reports failure inline
├── Model failures: fallback to cheaper model (existing Esperanto pattern)
└── All AI interactions traced via LangSmith callbacks
```

**LangSmith Integration:**
- LangSmithCallbackHandler added to all graph invocations
- Traces: full conversation chains, RAG retrieval steps, tool calls, token counts
- Per-user/per-company metadata tags for filtering

**Admin Notification (MVP):**
- Structured logs with severity levels + log monitoring
- Webhook to admin (Slack, email, or custom) on ERROR severity

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Hosting | Docker Compose, single VPS | Existing pattern. 5-10 users needs no orchestration. |
| CI/CD | GitHub Actions | Standard. Build, test, push image. |
| Environment config | `.env` files + Docker env vars | Existing pattern. |
| Monitoring | LangSmith (AI) + Loguru (app) | Existing tools, extended. |
| Scaling | Vertical (bigger VPS) for MVP | Horizontal deferred. |
| Backups | SurrealDB data volume snapshots | Simple, automated. |

### Implementation Sequence

1. Database migrations - New models (User, Company, etc.)
2. Auth upgrade - JWT middleware, login/register endpoints
3. Frontend route restructure - `(admin)` + `(learner)` groups
4. Company & assignment API - CRUD endpoints
5. Prompt management - Global + per-module prompt storage
6. Streaming endpoint - SSE compatible with assistant-ui
7. Learner frontend - Chat interface with assistant-ui
8. Error handling - Structured logging, admin notifications
9. LangSmith integration - AI tracing callbacks
10. Token tracking - Usage capture per operation

## Implementation Patterns & Consistency Rules

_Patterns derived from the existing open-notebook codebase. All AI agents must follow these rules._

### Naming Patterns

**Database (SurrealDB):**

| Element | Convention | Examples |
|---------|-----------|----------|
| Table names | `lowercase` singular | `user`, `company`, `learning_objective`, `module_assignment` |
| Edge/relationship tables | `lowercase` descriptive | `assigned_to`, `belongs_to`, `progress_on` |
| Field names | `snake_case` | `company_id`, `password_hash`, `onboarding_completed` |
| Timestamps | `created`, `updated` | Matches existing Notebook/Source pattern |
| Boolean fields | Positive assertion | `is_locked`, `onboarding_completed`, `auto_generated` |
| Migration files | `N.surrealql` / `N_down.surrealql` | `18.surrealql`, `18_down.surrealql` |

**API Endpoints:**

| Element | Convention | Examples |
|---------|-----------|----------|
| Resource paths | Plural nouns | `/users`, `/companies`, `/learning-objectives` |
| Nested resources | Parent/child | `/notebooks/{notebook_id}/objectives` |
| Actions | Verb suffix | `/quizzes/generate`, `/auth/login`, `/auth/refresh` |
| Path parameters | `{resource_id}` | `{user_id}`, `{company_id}`, `{objective_id}` |
| Query parameters | `snake_case` | `?company_id=...`, `?is_locked=false` |
| URL segments | `kebab-case` | `/learning-objectives`, `/module-assignments` |

**Python Backend:**

| Element | Convention | Examples |
|---------|-----------|----------|
| Classes | `PascalCase` | `User`, `Company`, `LearningObjective` |
| Functions | `snake_case` async | `async def get_user()`, `async def assign_module()` |
| Modules | `snake_case` | `user.py`, `company.py`, `learning_objective.py` |
| Router files | `{resource}.py` | `users.py`, `companies.py`, `assignments.py` |
| Service files | `{feature}_service.py` | `user_service.py`, `assignment_service.py` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TOKEN_EXPIRY`, `MAX_OBJECTIVES` |
| Pydantic models | `{Entity}{Purpose}` | `UserCreate`, `UserResponse`, `CompanyUpdate` |
| Exceptions | `{Noun}Error` | `AuthenticationError`, `AuthorizationError` |

**TypeScript Frontend:**

| Element | Convention | Examples |
|---------|-----------|----------|
| Components | `PascalCase.tsx` | `ModuleCard.tsx`, `ChatPanel.tsx` |
| UI primitives | `kebab-case.tsx` (in `ui/`) | `inline-quiz.tsx`, `audio-player.tsx` |
| Hooks | `use-{feature}.ts` | `use-modules.ts`, `use-objectives.ts` |
| API modules | `{resource}.ts` | `users.ts`, `companies.ts`, `objectives.ts` |
| Stores | `{feature}-store.ts` | `auth-store.ts`, `learner-store.ts` |
| Types/Interfaces | `PascalCase` | `ModuleResponse`, `UserProfile` |
| Functions | `camelCase` | `getModules()`, `updateObjective()` |
| i18n keys | `{section}.{key}` | `modules.title`, `chat.placeholder` |

### Structure Patterns

**Backend Layering (mandatory):**

```
Router → Service → Domain → Database

api/routers/{resource}.py       # HTTP layer: parse request, call service, return response
api/{feature}_service.py        # Business logic: orchestration, validation, graph invocation
open_notebook/domain/{model}.py # Domain models: get, save, delete with DB operations
open_notebook/database/         # Repository functions and migrations
```

Routers NEVER access database directly. Services contain business logic. Domain models encapsulate DB operations.

**Frontend Organization:**

```
frontend/src/app/
├── (auth)/                # Shared auth routes
├── (admin)/               # Admin route group with own layout
└── (learner)/             # Learner route group with own layout

frontend/src/components/
├── ui/                    # Radix/Shadcn primitives (shared)
├── common/                # Shared components (both interfaces)
├── admin/                 # Admin-only components
└── learner/               # Learner-only components
```

Learner and admin components NEVER import from each other. Shared code goes in `common/`, `ui/`, or `lib/`.

**Test Organization:**

- Python: `tests/test_{feature}.py` at project root. Class-based with `Test` prefix. `@pytest.mark.asyncio` for async.
- Frontend: Co-located `*.test.ts` files using Vitest.

### Format Patterns

**API Responses:**

- Direct Pydantic model responses (no wrapper object)
- Lists: `List[EntityResponse]`
- Single items: `EntityResponse`
- Errors: `{"detail": "error message"}` via HTTPException
- Status codes: 200 (success), 201 (created), 204 (deleted), 400 (validation), 403 (forbidden), 404 (not found), 500 (server error)

**JSON Field Naming:**

- `snake_case` everywhere (Pydantic default, no camelCase conversion)
- Dates: ISO 8601 strings (`2026-02-04T10:30:00Z`)
- Booleans: `true`/`false`
- Null: explicit `null` (not omitted)

### Communication Patterns

**State Management Rules:**

| State Type | Tool | Location |
|------------|------|----------|
| Server state (API data) | TanStack Query | `lib/hooks/use-{feature}.ts` |
| Auth state | Zustand (persisted) | `lib/stores/auth-store.ts` |
| UI state (modals, toggles) | React `useState` | Component-local |
| Shared UI state | Zustand | `lib/stores/{feature}-store.ts` |

Never duplicate server state in Zustand. TanStack Query is the single source of truth for API data.

**Query Key Convention:**

```typescript
['modules']                          // list
['modules', { companyId }]           // filtered list
['modules', moduleId]                // single item
['modules', moduleId, 'objectives']  // nested resource
```

**Hook Pattern (one hook file per resource):**

```typescript
// lib/hooks/use-modules.ts
export function useModules(companyId?: string) { ... }
export function useModule(moduleId: string) { ... }
export function useCreateModule() { ... }
export function useUpdateModule() { ... }
export function useDeleteModule() { ... }
```

### Process Patterns

**Error Handling Chain:**

- Frontend: TanStack Query `onError` → toast notification (sonner). ErrorBoundary for crashes.
- API: try/catch → `logger.error()` → `HTTPException`. Custom exceptions mapped to HTTP status.
- AI: Node-level try/catch → graceful degradation. Model failure → Esperanto fallback. LangSmith tracing.

Never let exceptions propagate unhandled. Every layer catches and transforms.

**Async Task Pattern:**

1. Frontend: POST to create task → receives `command_id`
2. Frontend: Show persistent AsyncStatusBar component
3. Frontend: Poll `GET /commands/{command_id}` on interval
4. Backend: surreal-commands job queue processes task
5. Frontend: On completion → invalidate query, update indicator
6. AI chat: If triggered from chat, AI acknowledges and continues

**Auth Flow:**

1. `POST /auth/login` → access + refresh tokens in httpOnly cookies
2. API calls: cookies sent automatically
3. 401 → axios interceptor retries with `POST /auth/refresh`
4. Refresh failure → clear auth store, redirect to `/login`
5. Root layout checks role → redirect to `/(admin)` or `/(learner)`

**Company Scoping:**

- FastAPI dependency `get_current_learner()` validates role + extracts `company_id`
- All learner queries filter by `company_id`
- Admin queries have no company filter

### Enforcement Rules

**All AI Agents MUST:**

1. Follow Router → Service → Domain → Database layering
2. Use naming conventions exactly as documented
3. Add Pydantic models to `api/models.py`
4. Add migrations sequentially after current highest number
5. Add i18n keys in BOTH `en-US` and `fr-FR`
6. Use TanStack Query for server state, never Zustand
7. Keep learner and admin components strictly separated
8. Include `logger.error()` before every `HTTPException` raise
9. Use `async def` for all new backend functions
10. Follow `{Entity}{Purpose}` naming for all API models

**Anti-Patterns:**

| Avoid | Do Instead |
|-------|------------|
| Router calling database directly | Router → Service → Domain |
| camelCase in Python | `snake_case` |
| API data in Zustand | TanStack Query hooks |
| Inline SQL in routers | Repository functions |
| Admin importing learner component | Shared code in `common/` |
| Hardcoded UI strings | i18n keys in both locales |
| Sync database operations | `async def` + `await` |
| `except Exception` without logging | `logger.error()` then handle |

## Project Structure & Boundaries

### Complete Project Directory Structure

_Files marked `# NEW` are additions. `# EXTEND` means modifications to existing files. Unmarked files exist unchanged._

```
open-notebook/
├── .github/workflows/ci.yml                    # NEW
├── docker-compose.dev.yml
├── docker-compose.full.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── CLAUDE.md
│
├── api/
│   ├── main.py                                 # EXTEND - new routers, JWT middleware
│   ├── auth.py                                 # REWRITE - JWT auth replacing PasswordAuth
│   ├── models.py                               # EXTEND - new Pydantic models
│   ├── client.py
│   ├── routers/
│   │   ├── auth.py                             # REWRITE - login, register, refresh, me
│   │   ├── chat.py                             # EXTEND - learner chat with teacher prompt
│   │   ├── companies.py                        # NEW
│   │   ├── learning_objectives.py              # NEW
│   │   ├── module_assignments.py               # NEW
│   │   ├── module_prompts.py                   # NEW
│   │   ├── token_usage.py                      # NEW
│   │   ├── users.py                            # NEW
│   │   └── (existing routers unchanged)
│   ├── assignment_service.py                   # NEW
│   ├── company_service.py                      # NEW
│   ├── learning_objectives_service.py          # NEW
│   ├── module_prompt_service.py                # NEW
│   ├── token_usage_service.py                  # NEW
│   ├── user_service.py                         # NEW
│   ├── chat_service.py                         # EXTEND - teacher prompt assembly
│   └── (existing services unchanged)
│
├── open_notebook/
│   ├── exceptions.py                           # EXTEND - auth exceptions
│   ├── domain/
│   │   ├── user.py                             # NEW
│   │   ├── company.py                          # NEW
│   │   ├── module_assignment.py                # NEW
│   │   ├── learning_objective.py               # NEW
│   │   ├── learner_progress.py                 # NEW
│   │   ├── module_prompt.py                    # NEW
│   │   ├── token_usage.py                      # NEW
│   │   └── (existing domain models unchanged)
│   ├── database/migrations/
│   │   ├── 1-17.surrealql                      # Existing
│   │   ├── 18.surrealql                        # NEW - user table
│   │   ├── 19.surrealql                        # NEW - company table
│   │   ├── 20.surrealql                        # NEW - module_assignment
│   │   ├── 21.surrealql                        # NEW - learning_objective
│   │   ├── 22.surrealql                        # NEW - learner_objective_progress
│   │   ├── 23.surrealql                        # NEW - module_prompt
│   │   ├── 24.surrealql                        # NEW - token_usage
│   │   └── (each with corresponding _down.surrealql)
│   ├── graphs/
│   │   ├── chat.py                             # EXTEND - proactive teacher, objectives
│   │   ├── prompt.py                           # EXTEND - two-layer prompt assembly
│   │   ├── tools.py                            # EXTEND - objective check-off tool
│   │   └── (existing graphs unchanged)
│   └── (ai/, utils/, podcasts/ unchanged)
│
├── frontend/src/
│   ├── app/
│   │   ├── layout.tsx                          # MODIFY - role-based routing
│   │   ├── (auth)/login/page.tsx               # MODIFY - role-aware redirect
│   │   ├── (admin)/                            # RENAMED from (dashboard)
│   │   │   ├── layout.tsx
│   │   │   ├── companies/page.tsx              # NEW
│   │   │   ├── companies/[id]/page.tsx         # NEW
│   │   │   ├── assignments/page.tsx            # NEW
│   │   │   └── (existing admin routes)
│   │   └── (learner)/                          # NEW route group
│   │       ├── layout.tsx                      # NEW
│   │       ├── onboarding/page.tsx             # NEW
│   │       ├── modules/page.tsx                # NEW
│   │       ├── modules/[id]/page.tsx           # NEW
│   │       └── profile/page.tsx                # NEW
│   ├── components/
│   │   ├── common/
│   │   │   ├── LanguageToggle.tsx              # NEW
│   │   │   └── AsyncStatusBar.tsx              # NEW
│   │   ├── admin/                              # NEW directory
│   │   │   ├── CompanyCard.tsx                 # NEW
│   │   │   ├── CompanyForm.tsx                 # NEW
│   │   │   ├── AssignmentMatrix.tsx            # NEW
│   │   │   ├── LearningObjectivesEditor.tsx    # NEW
│   │   │   ├── ModulePromptEditor.tsx          # NEW
│   │   │   └── ModulePublishFlow.tsx           # NEW
│   │   ├── learner/                            # NEW directory
│   │   │   ├── ChatPanel.tsx                   # NEW - assistant-ui
│   │   │   ├── SourcesPanel.tsx                # NEW
│   │   │   ├── ArtifactsPanel.tsx              # NEW
│   │   │   ├── ModuleCard.tsx                  # NEW
│   │   │   ├── ObjectiveProgressList.tsx       # NEW
│   │   │   ├── DocumentSnippetCard.tsx         # NEW
│   │   │   ├── InlineQuizWidget.tsx            # NEW
│   │   │   ├── InlineAudioPlayer.tsx           # NEW
│   │   │   ├── VoiceInputButton.tsx            # NEW
│   │   │   ├── NavigationAssistant.tsx         # NEW
│   │   │   ├── DetailsToggle.tsx               # NEW
│   │   │   └── OnboardingQuestionnaire.tsx     # NEW
│   │   ├── layout/
│   │   │   └── LearnerShell.tsx                # NEW
│   │   └── providers/
│   │       └── AuthProvider.tsx                # NEW
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts                       # MODIFY - JWT cookies
│   │   │   ├── auth.ts                         # NEW
│   │   │   ├── users.ts                        # NEW
│   │   │   ├── companies.ts                    # NEW
│   │   │   ├── assignments.ts                  # NEW
│   │   │   ├── learning-objectives.ts          # NEW
│   │   │   └── module-prompts.ts               # NEW
│   │   ├── hooks/
│   │   │   ├── use-auth.ts                     # NEW
│   │   │   ├── use-users.ts                    # NEW
│   │   │   ├── use-companies.ts                # NEW
│   │   │   ├── use-assignments.ts              # NEW
│   │   │   ├── use-learning-objectives.ts      # NEW
│   │   │   ├── use-module-prompts.ts           # NEW
│   │   │   └── use-learner-chat.ts             # NEW
│   │   ├── stores/
│   │   │   ├── auth-store.ts                   # MODIFY - JWT + role
│   │   │   └── learner-store.ts                # NEW
│   │   ├── types/
│   │   │   ├── user.ts                         # NEW
│   │   │   ├── company.ts                      # NEW
│   │   │   └── learner.ts                      # NEW
│   │   └── locales/
│   │       ├── en-US/index.ts                  # EXTEND
│   │       └── fr-FR/index.ts                  # EXTEND
│   └── middleware.ts                           # NEW - role-based route protection
│
├── prompts/                                    # NEW directory
│   ├── global_teacher_prompt.j2                # NEW
│   ├── navigation_assistant_prompt.j2          # NEW
│   └── admin_assistant_prompt.j2               # NEW
│
└── tests/
    ├── test_auth.py                            # NEW
    ├── test_user_service.py                    # NEW
    ├── test_company_service.py                 # NEW
    ├── test_assignment_service.py              # NEW
    ├── test_learning_objectives.py             # NEW
    ├── test_teacher_chat.py                    # NEW
    └── (existing test files unchanged)
```

### Architectural Boundaries

**API Boundaries:**

| Boundary | Endpoints | Auth Requirement |
|----------|-----------|-----------------|
| Public | `/auth/login`, `/auth/register`, `/health` | None |
| Admin-only | `/companies/*`, `/assignments/*`, `/users/*`, `/notebooks/*/prompts`, module CRUD | `require_admin()` |
| Learner-only | `/chat/learner/*`, learner profile, objectives progress | `require_learner()` + company scope |
| Shared (authenticated) | `/notebooks/*` (read), `/sources/*` (read), `/artifacts/*` (read) | `get_current_user()` + role-based filtering |

**Frontend Component Boundaries:**

- `(admin)` route group imports from: `components/admin/`, `components/common/`, `components/ui/`, `lib/*`
- `(learner)` route group imports from: `components/learner/`, `components/common/`, `components/ui/`, `lib/*`
- NEVER cross-import between `admin/` and `learner/` component directories
- Shared logic lives in `lib/` (hooks, API, stores, types)

**Data Boundaries:**

- Admin access: No company filter, full CRUD on all resources
- Learner access: `company_id` filter on ALL queries, read-only on module content
- Chat sessions: Isolated per user via LangGraph thread_id (`user:{user_id}:notebook:{notebook_id}`)
- Deletion cascade: User deletion removes progress, chat sessions, token usage records

### Requirements to Structure Mapping

| FR Domain | Backend | Frontend |
|-----------|---------|----------|
| Auth (FR1-6) | `auth.py`, `users.py` router+service, `user.py`+`company.py` domain, migrations 18-19 | `(auth)/login`, `use-auth.ts`, `auth-store.ts`, `AuthProvider.tsx` |
| Module Mgmt (FR7-14) | Existing notebooks + new `learning_objectives.py`, `module_prompts.py` routers+services, migrations 21,23 | `(admin)/notebooks/`, `LearningObjectivesEditor`, `ModulePromptEditor`, `ModulePublishFlow` |
| Assignment (FR15-17) | `module_assignments.py` router+service, migration 20 | `(admin)/assignments/`, `AssignmentMatrix` |
| AI Chat (FR18-31) | `chat.py` graph (extend), `prompt.py` (extend), `tools.py` (extend), `learner_progress.py` domain, migration 22 | `(learner)/modules/[id]/`, `ChatPanel`, `DocumentSnippetCard`, `InlineQuizWidget`, `DetailsToggle` |
| Content Browse (FR32-35) | Existing source/artifact endpoints | `SourcesPanel`, `ArtifactsPanel`, `ObjectiveProgressList` |
| Navigation (FR36-38) | New nav assistant endpoint + prompt | `NavigationAssistant` |
| Voice Input (FR39-41) | None (browser-side) | `VoiceInputButton` |
| Errors (FR42-46) | `exceptions.py` extend, `main.py` extend, LangSmith | `ErrorBoundary`, `AsyncStatusBar` |
| Privacy (FR47-50) | Company scoping in services, cascade delete, `token_usage.py`, migration 24 | N/A |
| Transparency (FR51-52) | SSE message format with tool calls | `DetailsToggle`, `AsyncStatusBar` |

### Integration Points

**Internal Data Flow:**

```
Learner chat message:
  ChatPanel (assistant-ui) → SSE POST /chat/learner/{notebook_id}
  → chat_service: assemble prompt (global + module + learner profile + objectives)
  → LangGraph chat graph: stream response with tool calls
  → Tools: RAG retrieval, objective check-off, artifact surfacing
  → SSE stream: token chunks + structured tool call parts
  → ChatPanel: render message + inline snippets + progress updates
```

**External Integrations:**

| Service | Integration Point | Protocol |
|---------|------------------|----------|
| AI Providers | `open_notebook/ai/` via Esperanto | HTTPS |
| LangSmith | LangGraph callback handlers | HTTPS |
| Browser Speech API | `VoiceInputButton` component | Browser API |
| Admin notifications | Error handler webhook | HTTPS |

## Architecture Validation Results

### Coherence Validation: PASS

**Decision Compatibility:** All technology choices are compatible. Next.js 16 App Router + route groups is standard for multi-layout apps. assistant-ui works natively with SSE streaming, aligning with FastAPI StreamingResponse + LangGraph. python-jose + passlib is the JWT pattern recommended by FastAPI docs. TanStack Query + Zustand is well-established. i18next already works in the codebase. SurrealDB async driver integrates with FastAPI async-first design. No contradictory decisions found.

**Pattern Consistency:** Naming conventions derived from existing codebase analysis and consistently extended. Backend layering matches existing patterns exactly. Frontend patterns follow established conventions. API response format matches all 23 existing routers.

**Structure Alignment:** Project structure extends naturally from existing layout. New files follow same organizational principles. Route groups leverage built-in Next.js capability already in use. Admin/learner component boundary is clean and enforceable.

### Requirements Coverage Validation: PASS

**Functional Requirements:** All 52 FRs mapped to specific architectural components:

| FR Range | Domain | Status |
|----------|--------|--------|
| FR1-FR6 | Auth & User Management | COVERED - JWT, User/Company models, role dependencies |
| FR7-FR14 | Module Management | COVERED - Existing notebooks + new objectives/prompts/publish |
| FR15-FR17 | Assignment & Availability | COVERED - ModuleAssignment model, company scoping, lock/unlock |
| FR18-FR31 | AI Chat Experience | COVERED - Extended chat graph, two-layer prompts, SSE, assistant-ui |
| FR32-FR35 | Content Browsing | COVERED - SourcesPanel, ArtifactsPanel, ObjectiveProgressList |
| FR36-FR38 | Platform Navigation | COVERED - NavigationAssistant component + prompt |
| FR39-FR41 | Voice Input | COVERED - VoiceInputButton (Browser Speech API) |
| FR42-FR46 | Error Handling & Observability | COVERED - Structured errors, LangSmith, admin webhook |
| FR47-FR50 | Data Privacy | COVERED - Company scoping, cascade delete, token tracking |
| FR51-FR52 | Transparency & Async | COVERED - DetailsToggle, AsyncStatusBar |

**Non-Functional Requirements:** All 16 NFRs covered:
- Performance (NFR1-5): SSE streaming, async patterns, TanStack Query caching
- Security (NFR6-10): JWT + bcrypt, company isolation, RBAC, session expiry
- Scalability (NFR11-13): Async-first, no global state, vertical MVP
- Observability (NFR14-16): Loguru, LangSmith, admin webhook

### Implementation Readiness Validation: PASS

- All critical decisions documented with specific technology choices
- Versions locked to existing codebase (verified via package.json/pyproject.toml)
- Every new file has a specific location in the directory tree
- Every FR maps to specific backend + frontend files
- 10 enforcement rules with anti-pattern examples

### Gap Analysis

**Critical Gaps: None.**

**Important Gaps (not blocking):**
1. assistant-ui SSE protocol adapter - exact message format needs verification during implementation
2. Global teacher prompt content - architecture defines storage/assembly, actual prompt engineering is a product task
3. Migration numbering - verify actual next number from migration directory at implementation time

**Post-MVP Gaps:**
- Prompt versioning for A/B testing
- API rate limiting middleware
- E2E test infrastructure (Playwright)
- Database connection pooling tuning

### Architecture Completeness Checklist

- [x] Project context analyzed (52 FRs, 16 NFRs, 5 user journeys)
- [x] Scale and complexity assessed (Medium, full-stack + AI)
- [x] Technical constraints identified (SurrealDB, FastAPI, LangGraph, Esperanto)
- [x] Cross-cutting concerns mapped (9 concerns)
- [x] Critical decisions documented (10 decisions with rationale)
- [x] Technology stack fully specified (all versions from existing codebase)
- [x] Integration patterns defined (SSE + polling, Router→Service→Domain)
- [x] Naming conventions established (DB, API, Python, TypeScript)
- [x] Structure patterns defined (backend layering, frontend organization)
- [x] Communication patterns specified (TanStack Query, Zustand, hooks)
- [x] Process patterns documented (error handling, auth flow, async tasks)
- [x] Complete directory structure defined (all new + modified files)
- [x] Component boundaries established (admin/learner separation)
- [x] Requirements to structure mapping complete (all 52 FRs)

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**

**Confidence Level: HIGH** - Architecture builds on proven, working codebase. Most infrastructure decisions inherited and battle-tested. New decisions are conventional and well-supported.

**Key Strengths:**
- Brownfield advantage: proven database, API, AI orchestration, deployment
- Minimal new infrastructure: route groups, 3 new libraries, extended patterns
- Clean separation of concerns: admin/learner boundary, backend layering
- All 68 requirements explicitly mapped to architectural components

**Areas for Future Enhancement:**
- WebSocket for real-time task notifications
- Prompt versioning and A/B testing
- Per-company database isolation at scale
- Horizontal scaling infrastructure
- E2E test framework
