---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments:
  - "product-brief-open-notebook-2026-02-04.md"
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 45
classification:
  projectType: saas_b2b
  domain: edtech
  complexity: medium
  projectContext: brownfield
---

# Product Requirements Document - open-notebook

**Author:** Gaspard.hassenforder
**Date:** 2026-02-04

## Executive Summary

An AI-native interactive learning platform built on the open-notebook open-source codebase, operated by a consulting firm that trains organizations on AI adoption. The platform extends in-person workshops by preparing learners beforehand and reinforcing knowledge afterward through a proactive AI teacher that leads conversations, assesses comprehension through natural dialogue, and generates personalized learning artifacts.

**Two-sided platform:**
- **Admins (Consultants):** Curate modules by uploading documents, generating artifacts (quizzes, podcasts, summaries), configuring learning objectives, and writing AI teacher prompts. Modules map 1:1 to open-notebook notebooks.
- **Learners:** Access assigned modules through a minimalist, chat-first interface. A proactive AI teacher guides learning, surfaces relevant documents inline, and tracks soft progress against learning objectives.

**Key Differentiator:** A proactive AI teacher that drives learning conversations toward objectives rather than passively waiting for questions. Combined with phased module availability tied to consulting engagement timelines, the platform keeps the firm embedded in client organizations long after workshops end.

**Target deployment:** Internal first (consultant team validates teaching quality), then client companies.

## Success Criteria

### User Success

**Learner:**
- Learning objectives checked off through natural conversation - learner feels taught, not tested
- AI teacher guides thinking rather than providing answers; learners discover concepts, not receive lectures
- Interactions are smooth and responsive; no frustrating waits
- Long-running tasks (podcast generation, etc.) handled asynchronously - AI acknowledges, backgrounds, continues conversation
- Source documents and artifacts easily accessible from within chat
- Learners return to the platform voluntarily after the workshop

**Consultant:**
- Documents-in to module-published in a single sitting without friction
- Admin interface feels familiar (built on open-notebook) and requires no training
- Module-to-company assignment visible at a glance
- AI teacher behavior configurable per module via prompts and learning objectives

### Business Success

- **Client retention on platform** - Companies continue using the platform beyond the initial consulting engagement
- **Internal deployment first** - Platform deployed internally for direct user feedback before client rollout
- **Teaching quality validated** - Internal users confirm AI teacher is effective, accurate, and pedagogically sound
- **Lead generation** - Natural consequence; learners discover AI use cases and engage the firm for implementation

### Technical Success

- **AI accuracy** - The AI teacher does not provide incorrect information. Absolute requirement. Responses grounded in module source documents, no hallucination.
- **Function reliability** - All chatbot tool calls (quiz generation, document retrieval, artifact surfacing) succeed without errors or confusion
- **Pedagogical discipline** - AI teacher does not give direct answers; guides, hints, uses Socratic methods
- **Smooth interactions** - Responses feel fast and conversational; no blocking on long tasks
- **Async task handling** - Long-running operations start in background; AI acknowledges, continues conversation, notifies on completion
- **Scalability baseline** - 5-10 concurrent users smoothly, architecture that scales beyond

### Measurable Outcomes

- At least one consultant creates and publishes a module in a single sitting
- At least one learner completes a full module (all learning objectives checked off) without errors
- Internal users report satisfaction with AI teaching quality (qualitative feedback)
- Zero factually incorrect AI responses from module source material
- All chatbot tool calls succeed reliably
- Response times feel conversational (no perceptible lag in chat turns)

## Product Scope

### MVP Strategy

**Approach:** Experience MVP - deliver the core learning experience (proactive AI teacher + module content) end-to-end for one learner journey and one admin journey. Prove AI teaching quality before adding operational features.

**Resources:** Solo developer with AI development tools + product manager for vision. The open-notebook codebase provides the foundation (document processing, artifact generation, RAG, chat infrastructure, database). Primary new engineering:
- Learner frontend (new, minimalist, chat-first)
- Proactive AI teacher behavior (prompt engineering + two-layer prompt system)
- Module assignment and company grouping (extending existing models)
- Basic authentication with roles

### MVP Feature Set

**Core User Journeys Supported:**
- Journey 1: Consultant creates and publishes a module
- Journey 2: Learner engages with AI teacher and progresses through a module
- Journey 3: Advanced learner fast-tracks through a module
- Journey 5: Graceful error handling with contextual logging

**Admin Side (modified open-notebook):**
- Upload documents into a module (1:1 module-to-notebook)
- Generate artifacts (quizzes, podcasts, summaries, transformations)
- Review and edit learning objectives checklist
- Write per-module AI teacher prompt (layered on global system prompt)
- Publish module
- Assign modules to companies, lock/unlock availability
- AI chatbot assistant for module creation help

**Learner Side (new frontend):**
- Login + basic onboarding questionnaire (first login only)
- Module selection screen (available/locked)
- Proactive AI chat teacher as primary interface
- Left side panel: browsable sources and artifacts
- Inline document snippets in chat, "open full" to side panel
- Soft learning objectives progress tracking
- Platform-wide AI navigation assistant (bottom-right bubble)
- Voice-to-text input (record, transcribe, review/edit, send)
- Details view toggle (function calls, thinking tokens)
- Async task handling with persistent visual indicators

**Platform:**
- Simple authentication (two roles: admin, learner)
- Company as database label for grouping
- Global AI teacher system prompt + per-module prompt
- Structured contextual error logging with admin notification
- GDPR-aware data model (per-company isolation, clean deletion capability)
- Basic token spending tracking (data capture, no UI)
- AI observability via LangSmith or equivalent (full conversation chains, RAG retrieval, function calls)

### Post-MVP Roadmap

**Phase 2 (Growth):**
- Admin progress dashboard (per company, per user, learning objectives status)
- On-the-fly artifact generation by AI teacher during learner conversations
- Questionnaire-driven module recommendations based on role/profile
- Per-profile module assignment within companies
- Token spending visibility dashboard
- Individual admin accounts

**Phase 3 (Expansion):**
- Decision-maker reporting and ROI dashboards
- Internal consultant upskilling workflows
- Expanded subject matter beyond AI training
- SSO/OAuth and enterprise identity integration
- Advanced analytics on learning patterns and AI teaching effectiveness
- Multi-language support
- API for integration with client LMS systems

### Risk Mitigation

**Technical Risks:**
- *Proactive AI teacher quality* - The hardest technical challenge. Mitigation: two-layer prompt system gives control; internal deployment provides rapid feedback; iterative prompt engineering. LangSmith observability enables real-time debugging. Start simple, refine.
- *AI may feel pushy* - The proactive teacher must be persistent but not annoying; read conversational cues and back off when appropriate. Tune through internal testing.
- *Open-notebook integration complexity* - Maximize reuse of existing backend; modify rather than rebuild. Admin interface stays close to original open-notebook UI.
- *Solo developer bottleneck* - AI development tools accelerate coding; open-notebook provides substantial foundation; MVP tightly scoped.

**Market Risks:**
- *AI teacher doesn't feel useful* - Internal deployment validates before client rollout. If the team finds it useful, clients will too.
- *Learners don't return after workshop* - Proactive AI teacher and long-term reference value designed for this. Validate with internal users first.

**Resource Risks:**
- *Limited capacity* - Leverage open-notebook heavily; keep MVP features minimal; defer non-essential features. If further constrained, Journey 4 (editing live modules) can be deferred.

## User Journeys

### Journey 1: Marc Creates and Publishes a Module (Consultant - Success Path)

Marc has just signed a new client engagement with a mid-size logistics company. He needs to prepare two modules: "AI Fundamentals" (pre-workshop) and "AI in Operations" (post-workshop).

**Opening Scene:** Marc sits down with his laptop, a folder of PDFs he's curated, a couple of slide decks, and notes from his pre-sales call. He logs into the admin interface.

**Rising Action:** He creates a new module called "AI Fundamentals." He drags and drops five PDFs and two articles into the module. The platform processes and indexes them. He clicks "Generate Artifacts" - the system produces a quiz, a podcast overview, and a summary document. He reviews each one, tweaks the quiz slightly. He then looks at the auto-generated learning objectives checklist - 12 items covering what a learner should understand after this module. He removes two that feel too advanced for a pre-workshop module and rewords one. He writes a master prompt for the AI teacher: "You are a friendly, patient AI guide introducing professionals to AI for the first time. Focus on practical examples from logistics and supply chain. Never give direct answers - guide them to discover concepts themselves." He hits Publish.

**Climax:** Marc navigates to the assignment dashboard, selects the logistics company, and assigns "AI Fundamentals" as available now, with "AI in Operations" locked until after the workshop. He sees the module appear in the company's assigned list.

**Resolution:** The next morning, Marc checks back and sees that three employees from the logistics company have already started the module. He's confident they'll arrive at the workshop with a solid foundation.

**Capabilities revealed:** Document upload & processing, artifact generation, learning objectives editor, master prompt configuration, module publish flow, company assignment dashboard, module lock/unlock.

---

### Journey 2: Sophie Learns Through the AI Teacher (Learner - Success Path)

Sophie is a project manager at the logistics company. Her boss told her the team has access to a new AI learning platform ahead of next week's workshop.

**Opening Scene:** Sophie receives an email with a link and login credentials. She's curious but skeptical - she's sat through corporate training platforms before and found them dull. She logs in and is greeted by a short questionnaire: "What's your role?", "How familiar are you with AI?", "What kind of work do you do day-to-day?" She answers honestly: project manager, heard of ChatGPT but never used it seriously, spends most of her time coordinating teams and tracking deliverables.

**Rising Action:** She sees one module available: "AI Fundamentals." She clicks into it. Instead of a wall of text, the AI teacher greets her: "Hi Sophie! I see you're a project manager - that's great, because AI has some really interesting applications for coordination and planning. Before we dive in, tell me - what's the most tedious part of your workday?" Sophie types: "Status reports. I spend hours compiling them." The AI responds: "That's a perfect example of something AI can help with. Let me show you why..." and surfaces a short snippet from one of Marc's PDFs about AI summarization. The conversation flows naturally - the AI asks questions, gives her things to think about, and occasionally shows her document snippets or suggests she listen to the podcast overview.

**Climax:** Twenty minutes in, Sophie realizes she's not just reading about AI - she's having a genuine conversation about how it applies to *her* work. The AI asks: "Based on what we've discussed about natural language processing, can you think of another part of your job where you're essentially summarizing or extracting information?" Sophie thinks for a moment and types: "Meeting notes! I always have to write up action items from meetings." The AI confirms she's understood the concept and checks off a learning objective.

**Resolution:** Sophie closes the platform feeling energized about the upcoming workshop. Over the next few days, she returns twice more, completing 10 of 12 learning objectives through natural conversation. She arrives at the workshop already understanding the basics, eager to go deeper.

**Capabilities revealed:** Login, questionnaire, module selection, proactive AI chat, document snippet surfacing, inline artifacts, learning objectives tracking through conversation, persistent chat history across sessions.

---

### Journey 3: David Is Already Advanced (Learner - Edge Case)

David is a data analyst at the same logistics company. He uses Python, has built a few ML models, and already uses AI tools daily.

**Opening Scene:** David logs in skeptically, expecting basics he already knows. He completes the questionnaire: data analyst, very familiar with AI, writes code daily.

**Rising Action:** The AI teacher picks up on his background immediately: "David, it looks like you already have solid AI experience. Let's see where you stand on the concepts in this module." The AI engages him in a quick technical conversation, asking a few targeted questions about how AI models work, what prompting techniques he uses, and how he'd approach a specific scenario.

**Climax:** Within five minutes of conversation, the AI has confirmed David understands all 12 learning objectives. It doesn't waste his time going through material he already knows.

**Resolution:** The AI marks the module as complete: "Looks like you've already got a strong handle on these fundamentals. Module complete! When the post-workshop modules unlock, I think you'll find those more interesting - they go deeper into operational AI applications." David is pleasantly surprised - the platform respected his time instead of forcing him through content he didn't need.

**Capabilities revealed:** AI adapts to user level, rapid competency assessment through conversation, fast-track module completion for advanced users, learning objectives bulk check-off.

---

### Journey 4: Marc Updates a Live Module (Consultant - Edge Case)

Marc realizes mid-engagement that one of his source documents in "AI Fundamentals" has an outdated statistic. He also wants to add a new PDF he found.

**Opening Scene:** Marc logs into the admin interface and opens the published "AI Fundamentals" module.

**Rising Action:** He removes the outdated document and uploads the replacement. He also adds a new PDF. The platform reprocesses and re-indexes the sources. He regenerates the podcast to include the new content. He reviews the learning objectives - no changes needed.

**Resolution:** The updated module is live. Learners who access it next will see the updated sources. Existing conversations aren't disrupted - the AI teacher simply has access to the new material going forward.

**Capabilities revealed:** Edit published module, replace/add sources to live module, regenerate artifacts, no disruption to existing learner sessions.

---

### Journey 5: An Error Occurs During Artifact Generation (System Error Path)

Sophie is chatting with the AI teacher, which decides to generate a summary artifact for her. The underlying service fails.

**Opening Scene:** During a learning conversation, the AI teacher determines Sophie would benefit from a focused summary of a complex topic they've been discussing. It triggers artifact generation.

**Rising Action:** The backend encounters an error - the AI model service is temporarily unavailable. This could happen during any artifact creation: a quiz, a podcast, a summary, a transformation, or any other AI-generated content. The system captures a structured log: the full context trail (user action, function called, parameters, preceding steps) plus the error details. This is logged with severity and routed to the system administrator's error monitoring.

**Climax:** Sophie sees a friendly message: "I tried to generate that for you, but something went wrong on my end. This has been reported automatically. In the meantime, let's continue our conversation - I can walk you through the key points myself."

**Resolution:** The platform continues functioning. Sophie's learning isn't blocked - the AI teacher adapts and continues the conversation without the failed artifact. The system administrator receives a detailed error log showing the full context chain leading to the failure, making diagnosis straightforward. The error is isolated; no other features or users are affected.

**Capabilities revealed:** Graceful error handling for any artifact generation failure, non-breaking failures, structured contextual error logging (rolling context buffer flushed on error), automatic error notification to system admin, user-friendly error messages, conversation continuity after errors, AI teacher adapts when tools fail.

---

### Journey Requirements Summary

| Capability Area | Revealed By Journeys |
|----------------|---------------------|
| Document upload & processing | Journey 1, 4 |
| Artifact generation (quiz, podcast, summary, transformation) | Journey 1, 4 |
| Learning objectives editor | Journey 1 |
| Master prompt configuration | Journey 1 |
| Module publish/edit flow | Journey 1, 4 |
| Company assignment dashboard | Journey 1 |
| Module lock/unlock | Journey 1 |
| Authentication & questionnaire | Journey 2, 3 |
| Proactive AI chat teacher | Journey 2, 3 |
| Document snippet surfacing in chat | Journey 2 |
| Learning objectives tracking (natural conversation) | Journey 2, 3 |
| Adaptive difficulty / fast-track completion | Journey 3 |
| Persistent chat history | Journey 2 |
| Edit published modules without disruption | Journey 4 |
| Graceful error handling (any artifact) | Journey 5 |
| Structured contextual error logging | Journey 5 |
| Error notification to system admin | Journey 5 |
| Non-breaking failures with user messaging | Journey 5 |

## Domain-Specific Requirements

### Data Privacy (GDPR-Aware Architecture)

The platform handles personal data of European professionals (learner profiles, conversations, quiz results, learning progress). Full GDPR compliance tooling is not MVP scope, but the architecture must avoid creating constraints:

- **Per-company data isolation** - Learner data, conversations, and progress architecturally separated per company. No cross-company leakage.
- **Traceable operations** - Data operations on personal data traceable (who accessed what, when). Supports future right-of-access requests.
- **Clean deletion** - Data model supports complete deletion of a user's or company's data without orphaned records.
- **Data minimization** - Only collect what's needed. Questionnaire captures role and AI familiarity, not unnecessary personal information.

### AI Content Safety

- AI teacher grounds all responses in module source material - no hallucination
- AI must not generate inappropriate, offensive, or misleading content

### Architectural Principle

Design for GDPR compliance to be layered on later without rearchitecting: per-company data isolation, traceable operations, and deletable records as architectural defaults.

## Innovation & Novel Patterns

### Proactive AI Teacher (Core Innovation)

The primary innovation: an AI that leads learning conversations rather than waiting for questions. This challenges the fundamental assumption of chatbot-based learning tools - that the user drives the interaction. The AI:
- Initiates topics and guides conversation toward learning goals
- Adapts teaching approach based on learner responses and level
- Decides when to surface documents, suggest artifacts, or shift topics
- Maintains pedagogical discipline (Socratic method, hints over answers)
- Behavior governed by two-layer prompt system: global system prompt defines core proactive teaching behavior across all modules; per-module prompt lets consultants add topic-specific instructions, industry context, and tone adjustments

This is closer to an AI agent with a teaching mission than a traditional Q&A chatbot.

### Soft Progress Tracking via Learning Objectives

The learning objectives list is not a formal assessment - it's a loose structure giving the AI direction and providing a general progress indicator. Completing 3 of 4 objectives is sufficient. The AI checks items off organically as topics are covered in conversation, giving consultants a rough sense of learner progress without creating a rigid test environment.

### Competitive Context

Existing e-learning platforms (Coursera, LMS tools, corporate training) are content-delivery systems with passive consumption and mechanical quizzes. AI-assisted learning tools that exist are predominantly reactive chatbots layered on content. A proactive AI teacher that drives learning conversations with pedagogical intent is a genuinely differentiated approach.

### Validation Approach

- Internal deployment as both validation and real usage - team uses the platform to upskill, providing direct feedback
- Qualitative feedback on whether the AI feels like a useful teacher vs. annoying chatbot
- Iterative prompt engineering based on real conversations

## SaaS B2B Specific Requirements

### Platform Model

Single-instance multi-tenant B2B platform operated by the consulting firm. Not sold as SaaS - the firm runs the platform and provides access to client companies as part of consulting engagements. Simplicity prioritized over enterprise-grade multi-tenancy.

### Tenant Model

- **Company as database label** - Companies are a grouping mechanism, not separate data stores. Learners belong to a company. Modules assigned to companies.
- **Application-level isolation** - Learners see only modules assigned to their company. No cross-company visibility.
- **No self-service management** - Admin creates companies and assigns modules. No company self-registration.

### Permission Model (RBAC)

| Role | Capabilities |
|------|-------------|
| **Admin** | Create/edit/publish modules, generate artifacts, manage learning objectives, configure AI teacher prompts, assign modules to companies, lock/unlock modules, view all companies and modules. Shared account among consultant team. |
| **Learner** | Log in, complete questionnaire, access assigned modules only, interact with AI teacher, browse sources and artifacts within assigned modules. No admin visibility. |

Two roles only. Shared admin account for MVP. No fine-grained permissions.

### Billing & Integrations

Not applicable for MVP. Platform operated as part of consulting service. No subscriptions, no external system integrations.

### Implementation Considerations

- Keep tenant model simple - company as database label is sufficient for MVP
- Shared admin account acceptable for 2-5 consultants; individual accounts added later
- Leverage open-notebook's existing authentication; extend with company assignment and role-based access
- Track AI token usage at a level supporting future per-company spending visibility. Implementation approach determined during architecture design. No reporting UI for MVP, but data must be captured.

## Functional Requirements

### Authentication & User Management

- **FR1:** Learners can create an account and log into the platform
- **FR2:** Admins can log into the platform with a shared admin account
- **FR3:** The system distinguishes between Admin and Learner roles and restricts access accordingly
- **FR4:** Learners complete an onboarding questionnaire on first login (AI familiarity, job type)
- **FR5:** Admins can create and manage company groups
- **FR6:** Admins can create learner accounts and assign them to a company

### Module Management (Admin)

- **FR7:** Admins can create a new module (1:1 mapped to a notebook)
- **FR8:** Admins can upload documents and resources into a module
- **FR9:** Admins can generate artifacts within a module (quizzes, podcasts, summaries, transformations)
- **FR10:** Admins can review and edit the auto-generated learning objectives checklist for a module
- **FR11:** Admins can write and edit a per-module prompt for the AI teacher
- **FR12:** Admins can publish a module, making it available for assignment
- **FR13:** Admins can edit a published module (add/remove sources, regenerate artifacts, update learning objectives)
- **FR14:** Admins can interact with an AI chatbot assistant within the admin interface for help with module creation

### Module Assignment & Availability

- **FR15:** Admins can assign modules to specific companies
- **FR16:** Admins can lock or unlock modules per company (phased availability for pre/post-workshop)
- **FR17:** Learners can only see and access modules assigned to their company that are unlocked

### Learner AI Chat Experience

- **FR18:** Learners can engage in conversation with a proactive AI teacher within a module
- **FR19:** The AI teacher proactively leads the learning conversation toward module learning objectives
- **FR20:** The AI teacher adapts its teaching approach based on the learner's responses and demonstrated level
- **FR21:** The AI teacher surfaces relevant document snippets inline within the chat conversation
- **FR22:** Learners can click an inline snippet to open the full source document in the side panel
- **FR23:** The AI teacher suggests and surfaces artifacts (quizzes, podcasts, summaries) during conversation
- **FR24:** The AI teacher uses Socratic methods - guiding and hinting rather than providing direct answers
- **FR25:** The AI teacher grounds all responses in the module's source documents and does not hallucinate
- **FR26:** The AI teacher assesses learner comprehension through natural conversation and checks off learning objectives
- **FR27:** The AI teacher generates quizzes to validate remaining learning objectives when natural assessment is insufficient
- **FR28:** The AI teacher fast-tracks advanced learners by rapidly confirming comprehension and completing learning objectives
- **FR29:** The AI teacher handles long-running tasks asynchronously - acknowledges the task, continues the conversation, notifies when complete
- **FR30:** The AI teacher's behavior is governed by a two-layer prompt system: global system prompt (pedagogical personality) plus per-module prompt (consultant customization)
- **FR31:** Learners can resume a previous conversation when returning to a module (persistent chat history)

### Learner Content Browsing

- **FR32:** Learners can browse all source documents for a module in a side panel
- **FR33:** Learners can browse all artifacts for a module in a side panel
- **FR34:** Learners can open and view full source documents in the side panel
- **FR35:** Learners can view their soft progress on learning objectives for a module

### Learner Platform Navigation

- **FR36:** Learners can access a platform-wide AI navigation assistant from any screen (bottom-right bubble)
- **FR37:** The navigation assistant helps learners find the right module or locate specific information across assigned modules
- **FR38:** The navigation assistant directs learners to relevant modules or content - it does not teach or answer learning questions directly

### Learner Voice Input

- **FR39:** Learners can initiate voice recording within the chat interface via a dedicated button
- **FR40:** The system automatically transcribes the voice recording into text when recording stops
- **FR41:** Learners can review and edit the transcribed text before sending it to the AI teacher

### Error Handling & Observability

- **FR42:** The system handles errors in any artifact generation gracefully without breaking the user's experience
- **FR43:** The system displays a user-friendly error message when a feature fails and the AI teacher continues the conversation
- **FR44:** The system captures structured contextual error logs (rolling context buffer flushed on error) for all failures
- **FR45:** The system automatically notifies the system administrator when errors occur
- **FR46:** The system integrates with LLM monitoring/tracing (LangSmith or equivalent) to capture full AI conversation chains, RAG retrieval steps, and function calls

### Data Privacy & Architecture

- **FR47:** Learner data (conversations, progress, quiz results) is isolated per company at the application level
- **FR48:** The system supports complete deletion of all data for a specific user
- **FR49:** The system supports complete deletion of all data for a specific company
- **FR50:** The system tracks AI token usage at a level that supports future spending visibility per company

### Learner Transparency & Async Feedback

- **FR51:** Learners can toggle a "details" view showing the AI's function calls and thinking tokens for each conversation step
- **FR52:** When a long-running task starts asynchronously, the system displays a persistent visual indicator (progress bar or status badge) showing task status, updated upon completion

## Non-Functional Requirements

### Performance

- **NFR1:** AI teacher responses stream tokens as generated, providing immediate visual feedback
- **NFR2:** Function calls (RAG retrieval, artifact surfacing, quiz generation) execute without blocking the streaming response where possible
- **NFR3:** Long-running tasks (podcast generation, complex artifact creation) handled asynchronously with persistent visual indicator; AI continues conversation; indicator updates on completion or failure
- **NFR4:** Side panel content (document loading, artifact browsing) loads without perceptible delay under normal conditions
- **NFR5:** Platform remains responsive during concurrent AI conversations (5-10 simultaneous users)

### Security

- **NFR6:** Authentication follows standard security best practices (hashed passwords, secure session management, HTTPS)
- **NFR7:** Learner data isolated per company at the application level - no cross-company data leakage
- **NFR8:** All data in transit encrypted (TLS/HTTPS)
- **NFR9:** API endpoints enforce role-based access control (admin vs. learner)
- **NFR10:** Session tokens expire after a reasonable inactivity period

### Scalability

- **NFR11:** Architecture supports 5-10 concurrent users for MVP without performance degradation
- **NFR12:** No patterns that prevent scaling beyond MVP levels (no single-user assumptions, no blocking global state)
- **NFR13:** Database queries and AI operations handle growing data volumes without architectural changes

### Observability

- **NFR14:** All errors captured with structured contextual logs (rolling context buffer) sufficient for system administrator diagnosis
- **NFR15:** LLM interactions traced end-to-end via LangSmith or equivalent, including function calls and retrieval steps
- **NFR16:** Error notifications reach system administrator automatically without requiring log review
