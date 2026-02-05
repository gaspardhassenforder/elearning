---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: complete
inputDocuments:
  - "prd.md"
  - "architecture.md"
  - "ux-design-specification.md"
---

# open-notebook - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for open-notebook, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Authentication & User Management**
- FR1: Learners can create an account and log into the platform
- FR2: Admins can log into the platform with a shared admin account
- FR3: The system distinguishes between Admin and Learner roles and restricts access accordingly
- FR4: Learners complete an onboarding questionnaire on first login (AI familiarity, job type)
- FR5: Admins can create and manage company groups
- FR6: Admins can create learner accounts and assign them to a company

**Module Management (Admin)**
- FR7: Admins can create a new module (1:1 mapped to a notebook)
- FR8: Admins can upload documents and resources into a module
- FR9: Admins can generate artifacts within a module (quizzes, podcasts, summaries, transformations)
- FR10: Admins can review and edit the auto-generated learning objectives checklist for a module
- FR11: Admins can write and edit a per-module prompt for the AI teacher
- FR12: Admins can publish a module, making it available for assignment
- FR13: Admins can edit a published module (add/remove sources, regenerate artifacts, update learning objectives)
- FR14: Admins can interact with an AI chatbot assistant within the admin interface for help with module creation

**Module Assignment & Availability**
- FR15: Admins can assign modules to specific companies
- FR16: Admins can lock or unlock modules per company (phased availability for pre/post-workshop)
- FR17: Learners can only see and access modules assigned to their company that are unlocked

**Learner AI Chat Experience**
- FR18: Learners can engage in conversation with a proactive AI teacher within a module
- FR19: The AI teacher proactively leads the learning conversation toward module learning objectives
- FR20: The AI teacher adapts its teaching approach based on the learner's responses and demonstrated level
- FR21: The AI teacher surfaces relevant document snippets inline within the chat conversation
- FR22: Learners can click an inline snippet to open the full source document in the side panel
- FR23: The AI teacher suggests and surfaces artifacts (quizzes, podcasts, summaries) during conversation
- FR24: The AI teacher uses Socratic methods - guiding and hinting rather than providing direct answers
- FR25: The AI teacher grounds all responses in the module's source documents and does not hallucinate
- FR26: The AI teacher assesses learner comprehension through natural conversation and checks off learning objectives
- FR27: The AI teacher generates quizzes to validate remaining learning objectives when natural assessment is insufficient
- FR28: The AI teacher fast-tracks advanced learners by rapidly confirming comprehension and completing learning objectives
- FR29: The AI teacher handles long-running tasks asynchronously - acknowledges the task, continues the conversation, notifies when complete
- FR30: The AI teacher's behavior is governed by a two-layer prompt system: global system prompt (pedagogical personality) plus per-module prompt (consultant customization)
- FR31: Learners can resume a previous conversation when returning to a module (persistent chat history)

**Learner Content Browsing**
- FR32: Learners can browse all source documents for a module in a side panel
- FR33: Learners can browse all artifacts for a module in a side panel
- FR34: Learners can open and view full source documents in the side panel
- FR35: Learners can view their soft progress on learning objectives for a module

**Learner Platform Navigation**
- FR36: Learners can access a platform-wide AI navigation assistant from any screen (bottom-right bubble)
- FR37: The navigation assistant helps learners find the right module or locate specific information across assigned modules
- FR38: The navigation assistant directs learners to relevant modules or content - it does not teach or answer learning questions directly

**Learner Voice Input**
- FR39: Learners can initiate voice recording within the chat interface via a dedicated button
- FR40: The system automatically transcribes the voice recording into text when recording stops
- FR41: Learners can review and edit the transcribed text before sending it to the AI teacher

**Error Handling & Observability**
- FR42: The system handles errors in any artifact generation gracefully without breaking the user's experience
- FR43: The system displays a user-friendly error message when a feature fails and the AI teacher continues the conversation
- FR44: The system captures structured contextual error logs (rolling context buffer flushed on error) for all failures
- FR45: The system automatically notifies the system administrator when errors occur
- FR46: The system integrates with LLM monitoring/tracing (LangSmith or equivalent) to capture full AI conversation chains, RAG retrieval steps, and function calls

**Data Privacy & Architecture**
- FR47: Learner data (conversations, progress, quiz results) is isolated per company at the application level
- FR48: The system supports complete deletion of all data for a specific user
- FR49: The system supports complete deletion of all data for a specific company
- FR50: The system tracks AI token usage at a level that supports future spending visibility per company

**Learner Transparency & Async Feedback**
- FR51: Learners can toggle a "details" view showing the AI's function calls and thinking tokens for each conversation step
- FR52: When a long-running task starts asynchronously, the system displays a persistent visual indicator (progress bar or status badge) showing task status, updated upon completion

### NonFunctional Requirements

**Performance**
- NFR1: AI teacher responses stream tokens as generated, providing immediate visual feedback
- NFR2: Function calls (RAG retrieval, artifact surfacing, quiz generation) execute without blocking the streaming response where possible
- NFR3: Long-running tasks (podcast generation, complex artifact creation) handled asynchronously with persistent visual indicator; AI continues conversation; indicator updates on completion or failure
- NFR4: Side panel content (document loading, artifact browsing) loads without perceptible delay under normal conditions
- NFR5: Platform remains responsive during concurrent AI conversations (5-10 simultaneous users)

**Security**
- NFR6: Authentication follows standard security best practices (hashed passwords, secure session management, HTTPS)
- NFR7: Learner data isolated per company at the application level - no cross-company data leakage
- NFR8: All data in transit encrypted (TLS/HTTPS)
- NFR9: API endpoints enforce role-based access control (admin vs. learner)
- NFR10: Session tokens expire after a reasonable inactivity period

**Scalability**
- NFR11: Architecture supports 5-10 concurrent users for MVP without performance degradation
- NFR12: No patterns that prevent scaling beyond MVP levels (no single-user assumptions, no blocking global state)
- NFR13: Database queries and AI operations handle growing data volumes without architectural changes

**Observability**
- NFR14: All errors captured with structured contextual logs (rolling context buffer) sufficient for system administrator diagnosis
- NFR15: LLM interactions traced end-to-end via LangSmith or equivalent, including function calls and retrieval steps
- NFR16: Error notifications reach system administrator automatically without requiring log review

### Additional Requirements

**From Architecture Document:**

- Brownfield project - no starter template. Existing open-notebook codebase provides the foundation.
- JWT authentication with python-jose + passlib (replacing existing PasswordAuthMiddleware)
- Access tokens: short-lived (30min) in httpOnly cookies; Refresh tokens: long-lived (7 days)
- Role-based access via FastAPI dependency injection: `get_current_user()`, `require_admin()`, `require_learner()`
- Single Next.js app with route groups: `(admin)` (renamed from `(dashboard)`) and `(learner)` (new)
- New frontend libraries required: @assistant-ui/react, react-resizable-panels, jose
- Keep existing i18next (not switch to next-intl)
- SSE streaming for AI chat (assistant-ui compatible) + REST polling for async tasks
- Two-layer prompt system: global system prompt + per-module prompt assembled via Jinja2 templates
- 7 new database models: User, Company, ModuleAssignment, LearningObjective, LearnerObjectiveProgress, ModulePrompt, TokenUsage
- 7 new database migrations (numbered 18-24), continuing AsyncMigrationManager pattern
- Backend layering: Router → Service → Domain → Database (mandatory)
- All learner queries must include company_id filter for data isolation
- LangSmith integration via callback handlers on all graph invocations
- Admin notification via webhook (Slack, email, or custom) on ERROR severity
- Chat thread isolation per user via LangGraph thread_id: `user:{user_id}:notebook:{notebook_id}`
- Deletion cascade: User deletion removes progress, chat sessions, token usage records
- Docker Compose single-instance deployment
- CI/CD via GitHub Actions

**From UX Design Specification:**

- Two independent frontend experiences: learner (fresh, minimalist, chat-first) and admin (streamlined pipeline). Do NOT base on existing open-notebook UI.
- Learner interface: assistant-ui library for chat, react-resizable-panels for split layout (1/3 sources + 2/3 chat)
- Admin interface: stays on Shadcn/ui with simplified pipeline UX (Upload → Generate → Configure → Publish → Assign)
- Design Direction A (Minimal Warmth): flowing text AI messages (no bubbles), subtle user message background, ChatGPT-like minimal chrome
- Warm neutral color palette with CSS custom properties
- Inter font for learner interface, system fonts for admin
- Desktop-only MVP (no mobile responsive). Below 768px shows friendly "use desktop" message.
- WCAG 2.1 Level AA accessibility target: keyboard navigation, screen reader support, focus management, reduced motion support
- Minimum 44x44px touch targets for all interactive elements
- AI initiates conversation immediately (no empty state) with personalized greeting from questionnaire data
- Reactive sources panel: scrolls to and highlights referenced documents after AI message stream completes
- Tabbed sources panel: Sources | Artifacts | Progress tabs
- Collapsible sources panel with badge notification when collapsed and AI surfaces content
- Ambient progress tracking: thin 3px progress bar below header, subtle objective check-off in chat
- Inline rich content in chat: DocumentSnippetCard, InlineQuizWidget, InlineAudioPlayer as assistant-ui custom message parts
- AsyncStatusBar: persistent bottom viewport bar for background task status
- Module selection screen: vertical list with white cards, hover shadow, progress indicator
- No gamification, no badges, no celebration animations - professional calm tone
- Error states use warm amber color, never red for learner-facing states
- All transitions: 150ms ease
- Learner has exactly 3 screens: Login, Module Selection, Conversation (two-panel)
- Onboarding questionnaire on first login: 3-4 questions, conversational tone
- Internationalization: French primary, English secondary for learner interface via i18next

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 | Learner account creation and login |
| FR2 | Epic 1 | Admin login with shared account |
| FR3 | Epic 1 | Role distinction and access restriction |
| FR4 | Epic 1 | Learner onboarding questionnaire |
| FR5 | Epic 2 | Admin company group management |
| FR6 | Epic 1 | Admin creates learner accounts, assigns to company |
| FR7 | Epic 3 | Module creation (1:1 notebook) |
| FR8 | Epic 3 | Document upload into module |
| FR9 | Epic 3 | Artifact generation |
| FR10 | Epic 3 | Learning objectives editor |
| FR11 | Epic 3 | Per-module AI teacher prompt |
| FR12 | Epic 3 | Module publishing |
| FR13 | Epic 3 | Edit published module |
| FR14 | Epic 3 | Admin AI chatbot assistant |
| FR15 | Epic 2 | Module-to-company assignment |
| FR16 | Epic 2 | Module lock/unlock per company |
| FR17 | Epic 2 | Learner filtered module visibility |
| FR18 | Epic 4 | Proactive AI teacher conversation |
| FR19 | Epic 4 | AI leads toward learning objectives |
| FR20 | Epic 4 | AI adapts to learner level |
| FR21 | Epic 4 | Inline document snippets |
| FR22 | Epic 4 | Click snippet to open full doc |
| FR23 | Epic 4 | AI surfaces artifacts in conversation |
| FR24 | Epic 4 | Socratic method teaching |
| FR25 | Epic 4 | Grounded responses, no hallucination |
| FR26 | Epic 4 | Comprehension assessment via conversation |
| FR27 | Epic 4 | Quiz generation for remaining objectives |
| FR28 | Epic 4 | Fast-track advanced learners |
| FR29 | Epic 4 | Async task handling in chat |
| FR30 | Epic 4 | Two-layer prompt system |
| FR31 | Epic 4 | Persistent chat history |
| FR32 | Epic 5 | Browse source documents in side panel |
| FR33 | Epic 5 | Browse artifacts in side panel |
| FR34 | Epic 5 | View full documents in side panel |
| FR35 | Epic 5 | View learning objectives progress |
| FR36 | Epic 6 | Platform-wide navigation assistant |
| FR37 | Epic 6 | Cross-module search via assistant |
| FR38 | Epic 6 | Navigation assistant directs, doesn't teach |
| FR39 | Epic 6 | Voice recording in chat |
| FR40 | Epic 6 | Voice-to-text transcription |
| FR41 | Epic 6 | Review/edit transcription before send |
| FR42 | Epic 7 | Graceful error handling |
| FR43 | Epic 7 | User-friendly error messages |
| FR44 | Epic 7 | Structured contextual error logs |
| FR45 | Epic 7 | Admin error notifications |
| FR46 | Epic 7 | LangSmith LLM tracing |
| FR47 | Epic 7 | Per-company data isolation |
| FR48 | Epic 7 | User data deletion |
| FR49 | Epic 7 | Company data deletion |
| FR50 | Epic 7 | Token usage tracking |
| FR51 | Epic 7 | Details view (function calls, thinking) |
| FR52 | Epic 7 | Persistent async task indicators |

## Epic List

### Epic 1: Authentication & User Identity
Users can register, log in, and be routed to the correct experience (admin or learner). Learners complete an onboarding questionnaire that personalizes their AI interactions.
**FRs covered:** FR1, FR2, FR3, FR4, FR6
**NFRs addressed:** NFR6, NFR7, NFR8, NFR9, NFR10

### Epic 2: Company Management & Module Assignment
Admins can create companies, assign modules to them, and control phased availability (lock/unlock). Learners see only their assigned, unlocked modules.
**FRs covered:** FR5, FR15, FR16, FR17

### Epic 3: Module Creation & Publishing Pipeline
Admins can create modules, upload documents, generate artifacts, configure learning objectives and AI teacher prompts, publish modules, and get AI assistance during creation.
**FRs covered:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14

### Epic 4: Learner AI Chat Experience
Learners engage with a proactive AI teacher that leads conversations, surfaces documents inline, adapts to learner level, assesses comprehension, generates quizzes, handles async tasks, and maintains persistent chat history — all governed by the two-layer prompt system.
**FRs covered:** FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31
**NFRs addressed:** NFR1, NFR2, NFR3, NFR5

### Epic 5: Content Browsing & Learning Progress
Learners can browse source documents and artifacts in a side panel, view full documents, and track their soft progress on learning objectives.
**FRs covered:** FR32, FR33, FR34, FR35
**NFRs addressed:** NFR4

### Epic 6: Platform Navigation & Voice Input
Learners can access a platform-wide AI navigation assistant and use voice-to-text input for the chat interface.
**FRs covered:** FR36, FR37, FR38, FR39, FR40, FR41

### Epic 7: Error Handling, Observability & Data Privacy
The system handles errors gracefully, captures structured logs, notifies admins, integrates LLM tracing, isolates data per company, supports user/company deletion, and tracks token usage.
**FRs covered:** FR42, FR43, FR44, FR45, FR46, FR47, FR48, FR49, FR50, FR51, FR52
**NFRs addressed:** NFR11, NFR12, NFR13, NFR14, NFR15, NFR16

## Epic 1: Authentication & User Identity

Users can register, log in, and be routed to the correct experience (admin or learner). Learners complete an onboarding questionnaire that personalizes their AI interactions.

### Story 1.1: User Registration & Login (Backend)

As a **user (admin or learner)**,
I want to register an account and log in with my credentials,
So that I can securely access the platform.

**Acceptance Criteria:**

**Given** a visitor has no account
**When** they submit a registration request with username, email, and password
**Then** a new User record is created with a hashed password (bcrypt via passlib)
**And** the user is assigned a default role of "learner"

**Given** a registered user
**When** they submit valid credentials to `/auth/login`
**Then** an access token (30min, JWT) and refresh token (7 days) are set as httpOnly cookies
**And** the response includes the user's id, role, and company_id

**Given** a user with an expired access token
**When** they call `/auth/refresh` with a valid refresh token
**Then** a new access token is issued

**Given** any API request with an invalid or missing token
**When** the request reaches a protected endpoint
**Then** a 401 Unauthorized response is returned

*Creates: User domain model, user table migration (18), auth router, auth service, JWT middleware replacing PasswordAuthMiddleware*

### Story 1.2: Role-Based Access Control & Route Protection

As a **platform operator**,
I want the system to distinguish between Admin and Learner roles and restrict access accordingly,
So that each role only sees their authorized interface.

**Acceptance Criteria:**

**Given** a logged-in user with role "admin"
**When** they access the platform
**Then** they are routed to the `(admin)` route group

**Given** a logged-in user with role "learner"
**When** they access the platform
**Then** they are routed to the `(learner)` route group

**Given** a learner
**When** they attempt to access an admin-only API endpoint
**Then** a 403 Forbidden response is returned

**Given** an admin
**When** they attempt to access a learner-only API endpoint
**Then** a 403 Forbidden response is returned

**Given** an unauthenticated user
**When** they access any non-public route
**Then** they are redirected to `/login`

**Given** a learner makes any API request
**When** the request reaches a learner-scoped endpoint
**Then** all database queries are automatically scoped to the learner's company via the `get_current_learner()` dependency (extracts company_id from the authenticated user)

*Creates: `require_admin()`, `require_learner()`, and `get_current_learner()` (with company_id extraction) FastAPI dependencies, frontend middleware.ts for route protection, AuthProvider component, role-based redirect in root layout. The `get_current_learner()` dependency ensures per-company data isolation on all learner endpoints from the start.*

### Story 1.3: Admin Creates Learner Accounts

As an **admin**,
I want to create learner accounts and assign them to a company,
So that learners can access the platform with appropriate company grouping.

**Acceptance Criteria:**

**Given** an admin is logged in
**When** they submit a new learner creation request with username, email, password, and company_id
**Then** a new User record is created with role "learner" and the specified company_id

**Given** an admin creates a learner
**When** the specified company_id does not exist
**Then** a 400 Bad Request error is returned with a clear message

**Given** an admin
**When** they request the list of users
**Then** all users are returned with their roles and company assignments

**Given** an admin
**When** they update a learner's company assignment
**Then** the learner's company_id is updated

*Creates: Company domain model, company table migration (19), users router, user_service, admin user management endpoints*

### Story 1.4: Learner Onboarding Questionnaire

As a **learner**,
I want to complete a short onboarding questionnaire on first login,
So that the AI teacher can personalize my learning experience.

**Acceptance Criteria:**

**Given** a learner logs in for the first time (`onboarding_completed` is false)
**When** they are redirected to the platform
**Then** they see the onboarding questionnaire screen before accessing modules

**Given** the onboarding questionnaire is displayed
**When** the learner answers the questions (AI familiarity, job type, job description)
**Then** their profile is updated with the responses and `onboarding_completed` is set to true

**Given** a learner has completed onboarding
**When** they log in again
**Then** they skip the questionnaire and go directly to module selection

**Given** a learner is on the questionnaire
**When** they submit answers
**Then** the questionnaire has a conversational, friendly tone (3-4 questions, not a form)

*Creates: Onboarding page in `(learner)/onboarding/`, OnboardingQuestionnaire component, profile update API endpoint, i18n keys (FR + EN)*

## Epic 2: Company Management & Module Assignment

Admins can create companies, assign modules to them, and control phased availability (lock/unlock). Learners see only their assigned, unlocked modules.

### Story 2.1: Company Management

As an **admin**,
I want to create and manage company groups,
So that I can organize client learners by organization.

**Acceptance Criteria:**

**Given** an admin is logged in
**When** they create a new company with name and slug
**Then** a Company record is created and returned with its id

**Given** an admin
**When** they view the companies list
**Then** all companies are displayed with name, slug, and count of assigned learners

**Given** an admin
**When** they update a company's name
**Then** the company record is updated

**Given** an admin
**When** they delete a company with no assigned learners or modules
**Then** the company is removed

**Given** an admin
**When** they attempt to delete a company with assigned learners or modules
**Then** a 400 error is returned explaining the company has active assignments

*Creates: companies router, company_service, admin companies page, CompanyCard and CompanyForm components*

### Story 2.2: Module Assignment to Companies

As an **admin**,
I want to assign modules to specific companies,
So that learners in those companies can access the learning content.

**Acceptance Criteria:**

**Given** an admin is logged in
**When** they assign a module (notebook) to a company
**Then** a ModuleAssignment record is created linking the notebook_id to the company_id

**Given** an admin assigns a module that is not yet published
**When** the assignment is created
**Then** a warning is displayed: "This module is not published yet. Learners will see it once published."
**And** the assignment is created successfully (unpublished modules can be pre-assigned)

**Given** an admin
**When** they view the assignment interface
**Then** they see a matrix of modules and companies with assignment status, with unpublished modules visually distinguished

**Given** an admin
**When** they remove a module assignment from a company
**Then** the ModuleAssignment record is deleted
**And** learners in that company can no longer see the module

*Creates: ModuleAssignment domain model, module_assignment migration (20), module_assignments router, assignment_service, AssignmentMatrix component, admin assignments page*

### Story 2.3: Module Lock/Unlock & Learner Visibility

As an **admin**,
I want to lock or unlock modules per company for phased availability,
So that learners access content at the right time in the consulting engagement.

**Acceptance Criteria:**

**Given** an admin views a module assignment
**When** they toggle the lock/unlock state
**Then** the ModuleAssignment `is_locked` field is updated

**Given** a learner logs in
**When** they view the module selection screen
**Then** they see only modules assigned to their company that are published

**Given** a learner views the module selection screen
**When** a module is assigned but locked
**Then** the module appears with a lock icon, 60% opacity, and is not clickable

**Given** a learner views the module selection screen
**When** a module is assigned and unlocked
**Then** the module card is clickable with title, description, and progress indicator

**Given** a learner
**When** they attempt to access a module not assigned to their company via direct URL
**Then** a 403 Forbidden response is returned

*Creates: Learner module selection page in `(learner)/modules/`, ModuleCard component, company-scoped module query endpoint, i18n keys (FR + EN)*

## Epic 3: Module Creation & Publishing Pipeline

Admins can create modules, upload documents, generate artifacts, configure learning objectives and AI teacher prompts, publish modules, and get AI assistance during creation.

### Story 3.1: Module Creation & Document Upload

As an **admin**,
I want to create a new module and upload documents into it,
So that I can build a learning module from my source materials.

**Acceptance Criteria:**

**Given** an admin is logged in
**When** they click "Create Module" and provide a title and description
**Then** a new Notebook record is created (1:1 module-to-notebook mapping)

**Given** an admin is in the Upload step of the pipeline
**When** they drag-and-drop or select files
**Then** the files are uploaded and processed asynchronously (content extraction + embedding via existing source processing)
**And** document cards appear as each file completes processing

**Given** an admin uploads multiple documents
**When** one document fails processing
**Then** an inline error is shown for the failed document while others continue processing

**Given** an admin has uploaded documents
**When** they click "Next"
**Then** the pipeline advances to the Generate step

*Extends: Existing notebook and source creation endpoints. Creates: Admin module pipeline page with horizontal stepper, Upload step UI*

### Story 3.2: Artifact Generation & Preview

As an **admin**,
I want to generate artifacts (quizzes, podcasts, summaries, transformations) for a module,
So that learners have rich learning materials alongside the source documents.

**Acceptance Criteria:**

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

*Extends: Existing quiz, podcast, summary, transformation generation endpoints. Creates: Generate step UI with per-artifact status indicators and preview*

### Story 3.3: Learning Objectives Configuration

As an **admin**,
I want to review and edit auto-generated learning objectives for a module,
So that the AI teacher has clear goals to guide learner conversations toward.

**Acceptance Criteria:**

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

*Creates: LearningObjective domain model, learning_objective migration (21), learning_objectives router, learning_objectives_service, LearningObjectivesEditor component*

### Story 3.4: AI Teacher Prompt Configuration

As an **admin**,
I want to write a per-module prompt for the AI teacher,
So that the AI's teaching behavior is tailored to the module's topic, industry, and tone.

**Acceptance Criteria:**

**Given** an admin is in the Configure step
**When** they view the prompt editor
**Then** a default template prompt is pre-populated as a starting point

**Given** the admin edits the prompt
**When** they save
**Then** a ModulePrompt record is created or updated for this module

**Given** the admin leaves the prompt empty
**When** they proceed
**Then** the global system prompt alone governs the AI teacher (per-module prompt is optional)

**Given** the admin has configured objectives and prompt
**When** they click "Next"
**Then** the pipeline advances to the Publish step

*Creates: ModulePrompt domain model, module_prompt migration (23), module_prompts router, module_prompt_service, ModulePromptEditor component*

### Story 3.5: Module Publishing

As an **admin**,
I want to publish a module,
So that it becomes available for assignment to companies.

**Acceptance Criteria:**

**Given** an admin is in the Publish step
**When** they see the module summary
**Then** it displays: document count, artifact count, objective count, prompt status

**Given** the admin clicks "Publish"
**When** validation passes (at least one document, at least one objective)
**Then** the module is marked as published and a confirmation is shown

**Given** the admin clicks "Publish"
**When** validation fails (missing documents or objectives)
**Then** inline errors indicate what's missing and the module is not published

**Given** a module is published
**When** the admin views the module list
**Then** the module shows a "Published" status badge

*Creates: Module publish endpoint (sets published flag on notebook), ModulePublishFlow component with summary view, publish validation logic*

### Story 3.6: Edit Published Module

As an **admin**,
I want to edit a published module (add/remove sources, regenerate artifacts, update objectives),
So that I can keep learning content current without disrupting active learners.

**Acceptance Criteria:**

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

*Extends: Existing source and artifact management endpoints. Creates: Edit mode for the pipeline, progress preservation logic*

### Story 3.7: Admin AI Chatbot Assistant

As an **admin**,
I want to interact with an AI chatbot assistant within the admin interface,
So that I can get help with module creation, prompt writing, and content decisions.

**Acceptance Criteria:**

**Given** an admin is in the module creation pipeline
**When** they open the AI assistant
**Then** a chat interface appears with context about the current module

**Given** the admin asks the assistant a question
**When** the assistant responds
**Then** responses are relevant to module creation (help with prompts, objectives, content strategy)

**Given** the admin assistant
**When** it provides suggestions
**Then** suggestions are grounded in the module's uploaded documents

*Extends: Existing admin chat functionality. Creates: Admin assistant prompt template (`admin_assistant_prompt.j2`), assistant context injection with current module data*

## Epic 4: Learner AI Chat Experience

Learners engage with a proactive AI teacher that leads conversations, surfaces documents inline, adapts to learner level, assesses comprehension, generates quizzes, handles async tasks, and maintains persistent chat history — all governed by the two-layer prompt system.

### Story 4.1: Learner Chat Interface & SSE Streaming

As a **learner**,
I want to engage in a streaming conversation with the AI teacher within a module,
So that I experience responsive, real-time interaction.

**Acceptance Criteria:**

**Given** a learner clicks an unlocked module from the selection screen
**When** the module page loads
**Then** a two-panel layout renders: sources panel (1/3 left) + chat panel (2/3 right) using react-resizable-panels

**Given** the chat panel is displayed
**When** the learner types a message and sends it
**Then** the message is sent via POST to the SSE chat endpoint
**And** the AI response streams token-by-token via SSE, rendered by assistant-ui Thread

**Given** the AI is generating a response
**When** tokens are streaming
**Then** a streaming cursor is visible at the end of the response

**Given** the learner resizes the panel divider
**When** they release the divider
**Then** the new position is persisted to localStorage

*Creates: Learner module page `(learner)/modules/[id]/page.tsx`, ChatPanel component with assistant-ui, SSE streaming endpoint in chat router, LearnerShell layout, react-resizable-panels setup*

### Story 4.2: Two-Layer Prompt System & Proactive AI Teacher

As a **learner**,
I want the AI teacher to proactively lead my learning conversation toward module objectives,
So that I'm guided through the material rather than left to figure it out alone.

**Acceptance Criteria:**

**Given** a learner opens a module for the first time
**When** the chat loads
**Then** the AI sends a personalized greeting referencing the learner's role and job context (from questionnaire data)
**And** the AI proactively introduces the first topic

**Given** the AI teacher responds
**When** assembling the system prompt
**Then** the prompt combines: global system prompt + per-module prompt + learner profile + learning objectives with status + RAG context

**Given** the AI teacher is conversing
**When** the learner demonstrates understanding of a topic
**Then** the AI naturally moves to the next objective topic

**Given** the AI teacher is conversing
**When** the learner asks a direct question
**Then** the AI uses Socratic methods — guiding and hinting rather than providing direct answers

**Given** the AI teacher responds
**When** making claims about module content
**Then** all responses are grounded in the module's source documents

*Creates: Global teacher prompt template (`global_teacher_prompt.j2`), prompt assembly logic in chat graph, learner profile injection, objectives injection, extended chat.py LangGraph nodes*

### Story 4.3: Inline Document Snippets in Chat

As a **learner**,
I want the AI teacher to surface relevant document snippets inline within the chat,
So that I can see source material in context without leaving the conversation.

**Acceptance Criteria:**

**Given** the AI references a source document during conversation
**When** the response is rendered
**Then** a DocumentSnippetCard appears inline showing: document title, excerpt text, and "Open in sources" link

**Given** a DocumentSnippetCard is displayed
**When** the learner clicks "Open in sources"
**Then** the sources panel scrolls to and highlights the referenced document
**And** if the sources panel is collapsed, it expands first

**Given** the AI message stream completes
**When** a document was referenced
**Then** the sources panel reactively scrolls to the referenced document after streaming finishes (not during)

*Creates: DocumentSnippetCard custom message part for assistant-ui, document surfacing tool in chat graph, reactive panel scroll logic via learner-store.ts*

### Story 4.4: Learning Objectives Assessment & Progress Tracking

As a **learner**,
I want the AI teacher to assess my comprehension through natural conversation and check off learning objectives,
So that my progress is tracked without formal testing.

**Acceptance Criteria:**

**Given** the AI determines a learner has demonstrated understanding of an objective
**When** the AI checks off the objective
**Then** a subtle inline confirmation appears in chat: "You've demonstrated understanding of [objective]" in success color
**And** the ambient progress bar below the header increments
**And** a LearnerObjectiveProgress record is created with status "completed" and evidence text

**Given** a learner returns to a module
**When** the conversation resumes
**Then** the AI has context on which objectives are already completed and focuses on remaining ones

**Given** all objectives are completed
**When** the AI confirms completion
**Then** a calm message appears: "You've covered all the objectives for this module"
**And** the module shows "Complete" on the module selection screen

*Creates: LearnerObjectiveProgress domain model, learner_progress migration (22), objective check-off tool for LangGraph, ObjectiveProgressList component, ambient progress bar (Radix Progress)*

### Story 4.5: Adaptive Teaching & Fast-Track for Advanced Learners

As an **advanced learner**,
I want the AI teacher to adapt its approach and fast-track me through content I already know,
So that my time is respected and I'm not forced through material unnecessarily.

**Acceptance Criteria:**

**Given** a learner's questionnaire indicates high AI familiarity
**When** the AI greets them
**Then** the greeting acknowledges their expertise and proposes a rapid assessment

**Given** the AI is assessing an advanced learner
**When** the learner demonstrates understanding of multiple related objectives in one response
**Then** the AI checks off multiple objectives at once

**Given** an advanced learner completes all objectives rapidly
**When** the module is marked complete
**Then** the AI suggests upcoming modules: "Post-workshop modules will go deeper"

**Given** a learner of any level
**When** the AI detects a knowledge gap
**Then** it shifts to deeper teaching on that specific topic before continuing

*Extends: Chat graph prompt logic for adaptive behavior. No new models — uses existing LearnerObjectiveProgress and prompt assembly*

### Story 4.6: AI Surfaces Artifacts in Conversation

As a **learner**,
I want the AI teacher to suggest and surface artifacts (quizzes, podcasts, summaries) during conversation,
So that I can engage with varied learning materials in context.

**Acceptance Criteria:**

**Given** the AI determines a quiz would help validate understanding
**When** it triggers quiz surfacing
**Then** an InlineQuizWidget renders in the chat with question, options, and submit button

**Given** the learner submits a quiz answer
**When** the answer is correct
**Then** the correct option is highlighted in success color with an explanation

**Given** the learner submits a quiz answer
**When** the answer is incorrect
**Then** the selected option shows amber, the correct option is revealed, and an explanation is shown

**Given** the AI references a podcast
**When** the podcast is surfaced
**Then** an InlineAudioPlayer renders in chat with play/pause, progress bar, and speed control

*Creates: InlineQuizWidget custom message part, InlineAudioPlayer custom message part, artifact surfacing tools in chat graph*

### Story 4.7: Async Task Handling in Chat

As a **learner**,
I want the AI teacher to handle long-running tasks asynchronously,
So that my conversation isn't blocked while waiting for artifact generation.

**Acceptance Criteria:**

**Given** the AI triggers a long-running task (e.g., podcast generation)
**When** the task starts
**Then** the AI acknowledges: "I'm generating that for you. Let's continue while it's processing."
**And** an AsyncStatusBar appears at the bottom of the viewport showing task status

**Given** an async task is running
**When** the conversation continues
**Then** the chat is not blocked — the learner and AI continue normally

**Given** an async task completes
**When** the status bar updates to "Ready"
**Then** the AI notifies inline: "Your podcast is ready" and the status bar auto-dismisses after 5 seconds

**Given** an async task fails
**When** the error is detected
**Then** the status bar shows amber "Failed" with a dismiss button
**And** the AI says: "I had trouble generating that. Let me walk you through it instead."

*Creates: AsyncStatusBar component, async task tracking in learner-store.ts, chat graph integration with surreal-commands job status*

### Story 4.8: Persistent Chat History

As a **learner**,
I want to resume my previous conversation when returning to a module,
So that I don't lose context and can continue learning where I left off.

**Acceptance Criteria:**

**Given** a learner has had a previous conversation in a module
**When** they return to the module
**Then** the chat history loads with all previous messages scrolled to the end

**Given** a learner returns to a module
**When** the history is loaded
**Then** the AI sends a re-engagement message: "Welcome back. Last time we were discussing..."

**Given** conversation history exists
**When** loading the chat
**Then** the thread_id `user:{user_id}:notebook:{notebook_id}` ensures isolation per user per module

*Extends: Existing LangGraph checkpoint storage (SQLite). Creates: Chat history loading endpoint, assistant-ui thread initialization with existing history, re-engagement prompt logic*

## Epic 5: Content Browsing & Learning Progress

Learners can browse source documents and artifacts in a side panel, view full documents, and track their soft progress on learning objectives.

### Story 5.1: Sources Panel with Document Browsing

As a **learner**,
I want to browse all source documents for a module in a side panel,
So that I can explore the learning materials independently of the conversation.

**Acceptance Criteria:**

**Given** a learner is in a module conversation view
**When** they look at the left panel
**Then** a tabbed panel is displayed with three tabs: Sources | Artifacts | Progress

**Given** the Sources tab is active
**When** the panel loads
**Then** all source documents for the module are displayed as DocumentCards (title + brief description)

**Given** a DocumentCard is displayed
**When** the learner clicks it
**Then** the card expands to show the full document content with scroll
**And** any previously expanded card collapses (one expanded at a time)

**Given** a learner
**When** they collapse the sources panel via the panel edge control
**Then** the chat expands to full width
**And** a badge area appears on the collapsed panel edge for notifications

**Given** the panel is collapsed
**When** the AI references a document in chat
**Then** a badge pulses on the collapsed panel edge

*Creates: SourcesPanel component, DocumentCard component, Radix Tabs setup for sources panel, collapse/expand logic with badge in learner-store.ts, i18n keys (FR + EN)*

### Story 5.2: Artifacts Browsing in Side Panel

As a **learner**,
I want to browse all artifacts for a module in the side panel,
So that I can access quizzes, podcasts, and summaries at any time.

**Acceptance Criteria:**

**Given** the Artifacts tab is active
**When** the panel loads
**Then** all artifacts for the module are listed (quizzes, podcasts, summaries, transformations) with type icon and title

**Given** an artifact is listed
**When** the learner clicks it
**Then** the artifact opens inline in the panel (quiz renders as interactive widget, podcast as audio player, summary as text)

**Given** no artifacts exist for the module
**When** the Artifacts tab is viewed
**Then** a calm message displays: "No artifacts yet. Your AI teacher may generate quizzes and summaries as you learn."

*Creates: ArtifactsPanel component, artifact list endpoint scoped to learner's company, artifact type rendering logic*

### Story 5.3: Learning Progress Display

As a **learner**,
I want to view my progress on learning objectives for a module,
So that I have a sense of how much I've covered.

**Acceptance Criteria:**

**Given** the Progress tab is active
**When** the panel loads
**Then** all learning objectives are listed with checked/unchecked status

**Given** the progress display
**When** rendered
**Then** a summary shows "X of Y" completed with a progress bar

**Given** an objective was just checked off in conversation
**When** the Progress tab is viewed
**Then** the newly checked item shows a brief warm glow (3 seconds) before settling to normal checked state

**Given** the learner is on the conversation screen
**When** an objective is checked off
**Then** the ambient progress bar (3px thin line below header) increments in real-time

*Extends: ObjectiveProgressList component (created in Epic 4). Creates: Progress tab content integration, progress data fetching hook (`use-learning-objectives.ts`)*

## Epic 6: Platform Navigation & Voice Input

Learners can access a platform-wide AI navigation assistant and use voice-to-text input for the chat interface.

### Story 6.1: Platform-Wide AI Navigation Assistant

As a **learner**,
I want to access a platform-wide AI navigation assistant from any screen,
So that I can find the right module or locate specific information across my assigned modules.

**Acceptance Criteria:**

**Given** a learner is on any learner screen (module selection or conversation)
**When** they see the bottom-right corner
**Then** a floating bubble icon is visible for the navigation assistant

**Given** the learner clicks the navigation bubble
**When** the assistant opens
**Then** a small chat overlay appears with a conversational interface

**Given** the learner asks "Where can I learn about AI in logistics?"
**When** the assistant responds
**Then** it searches across the learner's assigned modules and directs them to the relevant module or content

**Given** the learner asks a learning question (e.g., "What is machine learning?")
**When** the assistant responds
**Then** it redirects the learner to the appropriate module's AI teacher rather than answering the question itself

**Given** the assistant is open
**When** the learner clicks outside or presses Escape
**Then** the overlay closes

*Creates: NavigationAssistant component, navigation assistant prompt template (`navigation_assistant_prompt.j2`), navigation assistant API endpoint, cross-module search query scoped to learner's company*

### Story 6.2: Voice-to-Text Input

As a **learner**,
I want to use voice input in the chat interface,
So that I can interact with the AI teacher by speaking instead of typing.

**Acceptance Criteria:**

**Given** a learner is in the chat interface
**When** they see the input bar
**Then** a microphone button is visible on the left side of the composer

**Given** the learner clicks the microphone button
**When** recording starts
**Then** a visual recording indicator appears in the input bar (pulsing dot or waveform)
**And** the browser requests microphone permission if not already granted

**Given** the learner is recording
**When** they click the stop button or the microphone button again
**Then** recording stops and the audio is transcribed to text automatically

**Given** transcription is complete
**When** the text appears in the input field
**Then** the learner can review and edit the transcribed text before sending

**Given** the learner is satisfied with the transcription
**When** they click Send or press Enter
**Then** the message is sent to the AI teacher as normal text

**Given** the browser does not support the Speech API or permission is denied
**When** the learner clicks the microphone button
**Then** a friendly message indicates voice input is unavailable

*Creates: VoiceInputButton component, Browser Speech API integration (SpeechRecognition / webkitSpeechRecognition), composer extension for voice state*

## Epic 7: Error Handling, Observability & Data Privacy

The system handles errors gracefully, captures structured logs, notifies admins, integrates LLM tracing, isolates data per company, supports user/company deletion, and tracks token usage.

### Story 7.1: Graceful Error Handling & User-Friendly Messages

As a **learner**,
I want errors to be handled gracefully without breaking my experience,
So that I can continue learning even when something goes wrong.

**Acceptance Criteria:**

**Given** the AI teacher triggers an artifact generation that fails
**When** the error occurs
**Then** the AI sends a friendly inline message: "I had trouble with that. Let me try another way."
**And** the conversation continues without interruption

**Given** any API call fails on the frontend
**When** the error is caught
**Then** a toast notification (sonner) shows a user-friendly message — no technical details exposed to the learner

**Given** an error occurs in the learner interface
**When** the error is displayed
**Then** error states use warm amber color, never red

**Given** a component crashes in the frontend
**When** the React ErrorBoundary catches it
**Then** a fallback UI is shown with a friendly message and option to reload

*Extends: Existing React ErrorBoundary, axios error interceptor. Creates: AI chat error recovery logic in chat graph nodes, learner-facing error message patterns*

### Story 7.2: Structured Contextual Error Logging

As a **system administrator**,
I want all errors captured with structured contextual logs,
So that I can diagnose issues quickly without reproducing them.

**Acceptance Criteria:**

**Given** any error occurs in the API
**When** the error is caught
**Then** a structured log entry is created containing: error type, message, stack trace, rolling context buffer (last N operations), user_id, company_id, endpoint, timestamp

**Given** the rolling context buffer
**When** operations execute during a request
**Then** each operation (DB query, AI call, tool invocation) is appended to the buffer

**Given** a request completes successfully
**When** the response is sent
**Then** the context buffer is discarded (not logged)

**Given** a request fails
**When** the error handler runs
**Then** the full context buffer is flushed to the structured log alongside the error

**Given** the API
**When** any HTTPException is raised
**Then** `logger.error()` is called before the exception is raised

*Creates: Rolling context buffer middleware, structured error response format `{ error, code, detail, context }`, global FastAPI exception handlers*

### Story 7.3: Admin Error Notifications

As a **system administrator**,
I want to be automatically notified when errors occur,
So that I can respond to issues without manually reviewing logs.

**Acceptance Criteria:**

**Given** an error with severity ERROR or higher occurs
**When** the structured log is created
**Then** a notification is sent to the configured admin webhook (Slack, email, or custom endpoint)

**Given** the notification
**When** it is received
**Then** it includes: error summary, affected user/company, timestamp, and a link or reference to the full log entry

**Given** the webhook is not configured or fails
**When** an error occurs
**Then** the error is still logged normally — notification failure does not block error handling

*Creates: Admin notification service with webhook integration, notification configuration via environment variables*

### Story 7.4: LangSmith LLM Tracing Integration

As a **system administrator**,
I want all LLM interactions traced end-to-end via LangSmith,
So that I can debug AI behavior, monitor retrieval quality, and track token usage.

**Acceptance Criteria:**

**Given** any LangGraph workflow is invoked (chat, quiz generation, podcast, transformation)
**When** the graph runs
**Then** a LangSmithCallbackHandler is attached tracing the full chain: prompts, LLM calls, tool calls, RAG retrieval steps, token counts

**Given** a trace is captured
**When** it is sent to LangSmith
**Then** it includes metadata tags: user_id, company_id, notebook_id, operation_type

**Given** LangSmith is not configured (no API key)
**When** workflows run
**Then** they execute normally without tracing — LangSmith is optional

*Creates: LangSmith callback handler setup as reusable utility, metadata tag injection on all graph invocations*

### Story 7.5: Per-Company Data Isolation Audit

As a **platform operator**,
I want to verify that all learner-scoped endpoints enforce per-company data isolation,
So that no cross-company data leakage exists before go-live.

**Acceptance Criteria:**

**Given** the `get_current_learner()` dependency was created in Story 1.2
**When** an audit of all learner-scoped endpoints is performed
**Then** every endpoint that returns learner data uses `get_current_learner()` and scopes queries with `WHERE company_id = $user.company_id`

**Given** a learner
**When** they attempt to access data belonging to another company (modules, sources, artifacts, chat history) via any endpoint
**Then** the data is not returned — the query filters it out

**Given** an admin makes a request
**When** the request reaches an admin endpoint
**Then** no company filter is applied — admin sees all data

**Given** the audit is complete
**When** any endpoint is found missing company scoping
**Then** the scoping is added and a regression test is created for that endpoint

*Note: The `get_current_learner()` dependency with company_id extraction was created in Story 1.2. This story audits that all learner endpoints built in Epics 2-6 correctly use it. Creates: Integration tests verifying company isolation across all learner endpoints.*

### Story 7.6: User & Company Data Deletion

As a **platform operator**,
I want to completely delete all data for a specific user or company,
So that the platform supports GDPR-aware data management.

**Acceptance Criteria:**

**Given** an admin requests deletion of a user
**When** the deletion is executed
**Then** all user data is removed: profile, conversations (LangGraph checkpoints), learning progress, quiz results, token usage records
**And** no orphaned records remain

**Given** an admin requests deletion of a company
**When** the deletion is executed
**Then** all company data is removed: company record, all member users (and their data per above), all module assignments
**And** the admin is warned and must confirm before proceeding

**Given** a deletion request
**When** it targets a company with active learners
**Then** a confirmation prompt lists the number of users and records that will be deleted

*Creates: User cascade deletion endpoint, company cascade deletion endpoint, deletion confirmation logic*

### Story 7.7: Token Usage Tracking

As a **platform operator**,
I want AI token usage tracked per operation,
So that future per-company spending visibility can be built on captured data.

**Acceptance Criteria:**

**Given** any LLM call is made (chat, quiz generation, podcast, embedding, etc.)
**When** the call completes
**Then** a TokenUsage record is created with: user_id, company_id, notebook_id, model_provider, model_name, input_tokens, output_tokens, operation_type, timestamp

**Given** token usage data exists
**When** an admin queries token usage
**Then** aggregated data can be retrieved per company, per time period

**Given** the token tracking
**When** it runs
**Then** it adds negligible overhead — tracking is async and does not block the main operation

*Creates: TokenUsage domain model, token_usage migration (24), token_usage_service, token capture hook in Esperanto/LangGraph callbacks, token_usage router (admin-only)*

### Story 7.8: Learner Transparency — Details View

As a **learner**,
I want to toggle a details view showing the AI's function calls and thinking tokens,
So that I can understand how the AI arrived at its responses if I'm curious.

**Acceptance Criteria:**

**Given** an AI message in the chat
**When** the learner clicks the optional "Details" toggle on the message
**Then** a collapsible section expands showing: tool calls made, sources consulted, reasoning steps

**Given** the details view is expanded
**When** the learner clicks the toggle again
**Then** the details section collapses

**Given** the details toggle
**When** rendered by default
**Then** it is subtle and unobtrusive — a small icon or text link below the message, not prominent

*Creates: DetailsToggle component, assistant-ui tool call visualization configuration, structured tool call data in SSE message format*
