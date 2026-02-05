# Story 3.7: Admin AI Chatbot Assistant

Status: ready-for-dev

## Story

As an **admin**,
I want to interact with an AI chatbot assistant within the admin interface,
So that I can get help with module creation, prompt writing, and content decisions.

## Acceptance Criteria

**Given** an admin is in the module creation pipeline
**When** they open the AI assistant
**Then** a chat interface appears with context about the current module

**Given** the admin asks the assistant a question
**When** the assistant responds
**Then** responses are relevant to module creation (help with prompts, objectives, content strategy)

**Given** the admin assistant
**When** it provides suggestions
**Then** suggestions are grounded in the module's uploaded documents

## Tasks / Subtasks

- [x] Task 1: Admin Assistant Prompt Template (AC: 2, 3)
  - [x] Create admin_assistant_prompt.j2 in prompts/ directory
  - [x] Define assistant personality (helpful, practical, concise)
  - [x] Add module context injection (documents, objectives, current prompt)
  - [x] Include guidance areas (prompt writing, learning objectives, content strategy)
  - [x] Document available template variables

- [x] Task 2: Backend API Endpoint (AC: 1, 2)
  - [x] Create admin_chat router or extend existing chat router
  - [x] POST /admin/chat endpoint for admin assistant
  - [x] Inject current module context into prompt
  - [x] Use existing LangGraph chat workflow with custom prompt
  - [x] Ensure admin-only access with require_admin() dependency

- [ ] Task 3: Frontend - Admin Chat UI Component (AC: 1, 2)
  - [ ] Create AdminAssistantChat.tsx component
  - [ ] Use assistant-ui for chat interface (consistent with learner)
  - [ ] Add floating button/panel trigger in admin layout
  - [ ] Pass current module ID to API for context
  - [ ] Handle streaming responses via SSE
  - [ ] Add loading and error states

- [ ] Task 4: Context Assembly Logic (AC: 3)
  - [ ] Load current module's documents
  - [ ] Load current module's learning objectives
  - [ ] Load current module's prompt (if exists)
  - [ ] Format context for admin assistant prompt
  - [ ] Ensure RAG searches module documents

- [ ] Task 5: Pipeline Integration (AC: 1)
  - [ ] Add admin assistant button to module pipeline layout
  - [ ] Make assistant available across all pipeline steps
  - [ ] Ensure assistant has context of current step
  - [ ] Add keyboard shortcut (optional)

- [ ] Task 6: Testing (All ACs)
  - [ ] Integration tests for admin chat endpoint
  - [ ] Frontend component tests for chat UI
  - [ ] E2E test for assistant conversation flow
  - [ ] Verify context injection accuracy

## Dev Notes

### 🎯 Story Overview

This is the **seventh and final story in Epic 3: Module Creation & Publishing Pipeline**. It implements an **AI chatbot assistant** to help admins with module creation, prompt writing, and content decisions.

**Key Integration Points:**
- Reuses existing LangGraph chat workflow with custom prompt
- Extends admin interface with assistant-ui chat component
- Provides module-specific context (documents, objectives, prompt)
- Grounded in module's source documents via RAG
- Available throughout module creation pipeline

**Critical Context:**
- **FR14** (Admin AI chatbot assistant): Help with module creation
- Admin assistant is **distinct** from learner AI teacher (different personality, purpose)
- Admin assistant focuses on **helping admins**, not teaching learners
- Responses must be **practical, concise, and actionable**
- Assistant should suggest improvements to prompts, objectives, content strategy

### 🏗️ Architecture Patterns (MANDATORY)

**Backend Pattern:**
```
Admin Chat Router (api/routers/admin_chat.py)
  ↓ validates admin access, injects module context
Service Layer (reuse existing chat_service or create admin_chat_service)
  ↓ assembles admin assistant prompt with module context
LangGraph Chat Workflow (existing open_notebook/graphs/chat.py)
  ↓ invokes with admin_assistant_prompt
AI Provider (via Esperanto)
  ↓ generates response, streams tokens
```

**Critical Rules:**
- Admin assistant uses **separate prompt** from learner AI teacher
- Context includes current module's documents, objectives, and prompt
- RAG searches scoped to current module's documents
- All admin chat endpoints use `Depends(require_admin)` dependency
- Responses stream via SSE (same as learner chat)

**Frontend Architecture:**
- assistant-ui for chat interface (consistent with learner)
- AdminAssistantChat component as floating panel or sidebar
- TanStack Query for SSE streaming
- Context passed via query params (notebook_id)

### 📋 Technical Requirements

**Backend Stack:**
- FastAPI with async endpoints
- Existing LangGraph chat workflow (reuse)
- Jinja2 for admin prompt template
- SurrealDB for RAG context retrieval
- Esperanto for AI provider abstraction

**Frontend Stack:**
- Next.js 16 with React 19
- TypeScript 5 with strict mode
- assistant-ui for chat interface (existing)
- TanStack Query for SSE streaming (existing)
- Shadcn/ui components (Button, Card, Sheet for panel)
- i18next for internationalization (admin is en-US only)

**Admin Assistant Prompt Characteristics:**

| Aspect | Design |
|--------|--------|
| **Personality** | Helpful colleague, practical, concise, actionable |
| **Purpose** | Assist with module creation, not teaching learners |
| **Scope** | Prompt writing, learning objectives, content strategy |
| **Grounding** | Module's uploaded documents via RAG |
| **Tone** | Professional, supportive, clear |

### 🔒 Security & Permissions

**Admin-Only Access:**
- All admin chat endpoints use `require_admin()` dependency
- Learners cannot access admin assistant
- Admin assistant cannot access learner-specific data

**Authentication:**
- JWT tokens in httpOnly cookies (existing auth.py)
- No additional auth changes needed

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `prompts/admin_assistant_prompt.j2` - Admin assistant Jinja2 template
- `api/routers/admin_chat.py` - Admin chat endpoint (or extend existing chat router)
- `api/admin_chat_service.py` - Context assembly logic (optional, can be in router)

**MODIFY (if needed):**
- `api/main.py` - Register admin_chat router if separate

**Frontend Files to Create:**

**NEW:**
- `frontend/src/components/admin/AdminAssistantChat.tsx` - Chat UI component
- `frontend/src/lib/api/admin-chat.ts` - API client for admin chat
- `frontend/src/lib/hooks/use-admin-chat.ts` - TanStack Query hook for SSE streaming

**MODIFY:**
- `frontend/src/app/(admin)/layout.tsx` - Add assistant button to admin layout
- `frontend/src/lib/locales/en-US/index.ts` - Add adminAssistant.* keys

**Naming Conventions:**
- Python modules: `snake_case.py`
- Python functions: `async def snake_case()`
- TypeScript files: `kebab-case.ts` or `PascalCase.tsx` for components
- API endpoints: `/admin/chat`
- i18n keys: `adminAssistant.key`

### 🎨 Admin Assistant Prompt Design

**Admin Assistant Prompt Template Structure:**

```jinja
You are an AI assistant helping administrators create educational modules.

YOUR ROLE:
- Provide practical guidance on module creation
- Help write effective learning objectives
- Suggest improvements to AI teacher prompts
- Advise on content organization and strategy
- Answer questions about module configuration

CURRENT MODULE CONTEXT:
{% if module_title %}
Module: {{ module_title }}
{% endif %}

{% if documents %}
Uploaded Documents ({{ documents|length }}):
{% for doc in documents %}
- {{ doc.title }}
{% endfor %}
{% endif %}

{% if objectives %}
Learning Objectives ({{ objectives|length }}):
{% for obj in objectives %}
- {{ obj.text }}
{% endfor %}
{% endif %}

{% if module_prompt %}
Current AI Teacher Prompt:
{{ module_prompt }}
{% endif %}

GUIDELINES:
- Keep responses concise and actionable
- Reference the module's documents when making suggestions
- Provide specific examples for prompt improvements
- Focus on practical next steps for the admin
- Avoid teaching learner content - focus on admin tasks

When suggesting prompt improvements, explain the pedagogical reasoning.
When suggesting objectives, ensure they are measurable and aligned with content.
When advising on content, consider the learner audience and module goals.
```

**Context Variables Available:**
| Variable | Source | Example |
|----------|--------|---------|
| `module_title` | Notebook.title | "AI in Logistics" |
| `documents` | Source records for notebook | [{"title": "Intro to AI", ...}] |
| `objectives` | LearningObjective records | [{"text": "Understand AI basics", ...}] |
| `module_prompt` | ModulePrompt.system_prompt | "Focus on supply chain..." |

### 🔄 Admin Chat Flow

**Admin Conversation Flow:**
```
Admin (Browser)
  ↓ Clicks assistant button in admin interface
Frontend (AdminAssistantChat)
  ↓ Opens chat panel with assistant-ui
  ↓ Admin types question: "How should I structure the learning objectives?"
  ↓ POST /admin/chat { message, notebook_id }
Backend API (admin_chat router)
  ↓ Depends(require_admin) validates admin access
  ↓ Loads module context (documents, objectives, prompt)
  ↓ Assembles admin_assistant_prompt with context
  ↓ Invokes LangGraph chat workflow with custom prompt
LangGraph Chat Workflow
  ↓ RAG retrieves relevant document snippets
  ↓ LLM generates response based on prompt + context
  ↓ Streams response tokens via SSE
Frontend
  ↓ assistant-ui displays streaming response
  ↓ Admin reads advice and applies to module
```

### 🧪 Testing Requirements

**Backend Tests (pytest):**
- `tests/test_admin_chat_api.py`
  - Test POST /admin/chat with valid admin token
  - Test POST /admin/chat with learner token (403)
  - Test context assembly includes documents, objectives, prompt
  - Test SSE streaming response format
  - Test RAG search scoped to current module

**Frontend Tests:**
- Component tests for AdminAssistantChat
- Test chat panel open/close
- Test message submission
- Test streaming response rendering
- Mock SSE responses with MSW

**Test Coverage Targets:**
- Backend: 80%+ line coverage
- Frontend: 70%+ component coverage

### 🚫 Anti-Patterns to Avoid

1. **Prompt Confusion**
   - ❌ Using learner AI teacher prompt for admin assistant
   - ✅ Create separate admin_assistant_prompt.j2

2. **Context Scope**
   - ❌ Admin assistant accessing all notebooks
   - ✅ Context scoped to current module only

3. **Access Control**
   - ❌ Learners accessing admin assistant
   - ✅ Strict `require_admin()` dependency on all endpoints

4. **UI Duplication**
   - ❌ Reimplementing chat interface from scratch
   - ✅ Reuse assistant-ui (same as learner chat)

5. **Workflow Duplication**
   - ❌ Creating new LangGraph workflow for admin
   - ✅ Reuse existing chat.py with different prompt

### 🔗 Integration with Existing Code

**Reuse These Existing Components:**

From Story 4.1 (Learner Chat):
- assistant-ui chat interface components
- SSE streaming endpoint pattern
- TanStack Query hooks for streaming

From existing LangGraph:
- `open_notebook/graphs/chat.py` - Chat workflow
- RAG retrieval nodes
- Token streaming implementation

From existing API:
- `api/routers/chat.py` patterns (if extending)
- `require_admin()` dependency
- SSE response helpers

**New Dependencies:**
- None - all libraries already exist

### 📊 Data Flow Diagrams

**Context Assembly Flow:**
```
Backend receives POST /admin/chat
  ↓ Extract notebook_id from request
  ↓ Load Notebook record (title, description)
  ↓ Load Source records WHERE notebook_id = $id
  ↓ Load LearningObjective records WHERE notebook_id = $id
  ↓ Load ModulePrompt record WHERE notebook_id = $id
  ↓ Format context dict:
  {
    module_title: "...",
    documents: [{title, type, status}, ...],
    objectives: [{text, order}, ...],
    module_prompt: "..." or None
  }
  ↓ Render admin_assistant_prompt.j2 with context
  ↓ Pass rendered prompt to LangGraph chat workflow
  ↓ Return streaming response
```

**UI Integration Flow:**
```
Admin Layout (admin/layout.tsx)
  ↓ Renders AdminAssistantChat component (bottom-right or sidebar)
AdminAssistantChat Component
  ↓ Gets current notebook_id from URL or context
  ↓ Renders assistant-ui Thread component
  ↓ On message send:
  │   ├─ Calls POST /admin/chat with notebook_id
  │   ├─ Streams response via SSE
  │   └─ Displays in chat interface
  ↓ Admin reads response and applies advice
```

### 🔍 Code Review Checklist

Before marking this story as "done", verify:

**Backend:**
- [ ] admin_assistant_prompt.j2 created with module context variables
- [ ] Admin chat endpoint created (separate or extended)
- [ ] Endpoint has `Depends(require_admin)` dependency
- [ ] Context assembly loads documents, objectives, prompt
- [ ] RAG search scoped to current module's documents
- [ ] SSE streaming response format
- [ ] Router registered in api/main.py (if separate)

**Frontend:**
- [ ] AdminAssistantChat component created
- [ ] Uses assistant-ui for chat interface
- [ ] Passes notebook_id to API endpoint
- [ ] Handles SSE streaming responses
- [ ] Button/trigger in admin layout
- [ ] Available across all pipeline steps
- [ ] Loading and error states
- [ ] i18n keys added (en-US only for admin)

**Prompt:**
- [ ] Admin assistant personality defined
- [ ] Context variables documented
- [ ] Grounding in module documents
- [ ] Practical, concise, actionable tone
- [ ] Distinct from learner AI teacher

**Testing:**
- [ ] Backend: Admin-only access enforced (403 for learners)
- [ ] Backend: Context assembly includes all module data
- [ ] Backend: SSE streaming works correctly
- [ ] Frontend: Chat panel opens/closes correctly
- [ ] Frontend: Messages send and receive correctly
- [ ] E2E: Full conversation flow works

**Documentation:**
- [ ] Dev Agent Record filled with agent model, files, notes
- [ ] This checklist completed in story file

### 🎓 Learning from Previous Stories

**From Story 4.1 (Learner Chat Interface):**
- assistant-ui integration for chat UI
- SSE streaming endpoint pattern
- TanStack Query hooks for streaming
- Loading and error state handling

**From Story 3.4 (AI Teacher Prompt Configuration):**
- Jinja2 prompt templates with context variables
- Prompt assembly logic pattern
- Context injection (dynamic data)

**From Story 3.3 (Learning Objectives Configuration):**
- Admin-only CRUD operations
- require_admin() dependency pattern
- Frontend component integration in pipeline

**Apply these learnings:**
- Reuse assistant-ui (don't reinvent chat interface)
- Reuse LangGraph chat workflow (different prompt)
- Separate admin assistant prompt from learner teacher
- Inject module context dynamically
- Admin-only access enforcement

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Admin AI Assistant]
- [Source: _bmad-output/planning-artifacts/architecture.md#Prompt Management Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#LangGraph Workflows]

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Module Creation & Publishing Pipeline]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7: Admin AI Chatbot Assistant]
- [Source: _bmad-output/planning-artifacts/epics.md#FR14: Admin AI chatbot assistant]

**UX Design:**
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Admin Assistant UI]

**Existing Code Patterns:**
- [Source: open_notebook/graphs/chat.py] - LangGraph chat workflow
- [Source: api/routers/chat.py] - Chat endpoint patterns
- [Source: frontend/src/components/learner/ChatPanel.tsx] - assistant-ui usage

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/4-1-learner-chat-interface-and-sse-streaming.md] - assistant-ui, SSE
- [Source: _bmad-output/implementation-artifacts/3-4-ai-teacher-prompt-configuration.md] - Prompt templates

### Project Structure Notes

**Alignment with Project:**
- Continues (admin) route group for admin features
- Reuses existing LangGraph chat workflow
- Adds admin_assistant_prompt.j2 to prompts/ directory
- AdminAssistantChat component in admin components
- No new database models needed

**Potential Conflicts:**
- None - admin assistant is isolated from learner features
- Distinct prompt prevents confusion with learner AI teacher
- Context scoped to current module

**Design Decisions:**
- Admin assistant prompt stored in file (not database)
- Reuse existing chat workflow with custom prompt
- assistant-ui for consistency with learner chat
- Context injected dynamically (not stored)
- Available across all pipeline steps (not step-specific)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Implementation proceeded smoothly with RED-GREEN-REFACTOR TDD approach

### Completion Notes List

**Tasks 1-2 Complete (Backend)**:
- ✅ Task 1: Admin Assistant Prompt Template
  - Created `prompts/admin_assistant_prompt.jinja` with module context injection
  - Defined helpful, practical, concise personality distinct from learner AI teacher
  - Template supports: module_title, documents, objectives, module_prompt variables
  - All 6 prompt tests passing

- ✅ Task 2: Backend API Endpoint
  - Created `api/routers/admin_chat.py` with POST /admin/chat endpoint
  - Implemented `assemble_admin_context()` function to load notebook, sources, objectives, prompt
  - Integrated with existing LangGraph chat workflow using custom admin_assistant_prompt
  - Admin-only access enforced via `Depends(require_admin)` dependency
  - Router registered in `api/main.py` under /api prefix with "admin-chat" tag
  - All 5 API tests passing (access control + context assembly)

**Remaining Tasks (Frontend)**:
- Task 3: Frontend - Admin Chat UI Component (AdminAssistantChat.tsx)
- Task 4: Context Assembly Logic (already done in backend, may need RAG scoping)
- Task 5: Pipeline Integration (add button to admin layout)
- Task 6: Testing (E2E + component tests)

### File List

**NEW:**
- `prompts/admin_assistant_prompt.jinja` - Admin assistant Jinja2 template
- `api/routers/admin_chat.py` - Admin chat endpoint with context assembly
- `tests/test_admin_assistant_prompt.py` - Prompt template tests (6 tests)
- `tests/test_admin_chat_api.py` - API endpoint tests (5 tests)

**MODIFIED:**
- `api/main.py` - Registered admin_chat router
