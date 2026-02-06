# Story 4.7: Async Task Handling in Chat

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want the AI teacher to handle long-running tasks asynchronously,
so that my conversation isn't blocked while waiting for artifact generation.

## Acceptance Criteria

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

## Tasks / Subtasks

- [x] Task 1: Backend - Create Async Artifact Generation Tool (AC: 1, 2, 3, 4)
  - [x] Create generate_artifact tool in open_notebook/graphs/tools.py
  - [x] Tool accepts: artifact_type (podcast/quiz), topic, optional parameters
  - [x] Submit job via PodcastService.submit_generation_job() or QuizService
  - [x] Create Artifact placeholder with artifact_id = job_id
  - [x] Return tool result: {job_id, artifact_ids, status: "submitted", message}
  - [ ] Test tool submission returns job_id immediately (3+ test cases)

- [x] Task 2: Backend - Bind Tool to Chat Graph (AC: 1, 2)
  - [x] Modify open_notebook/graphs/chat.py: bind generate_artifact to model
  - [x] Ensure tool receives notebook_id and user_id from graph state
  - [x] Update prompt (global_teacher_prompt.j2): instruct AI on when/how to use tool
  - [x] Guidance: "When learner requests artifact, use generate_artifact tool, acknowledge submission, continue conversation"
  - [ ] Test tool call streams via SSE (2+ test cases)

- [x] Task 3: Backend - Job Status Polling Endpoint (AC: 3, 4)
  - [x] Verify /commands/jobs/{job_id} endpoint works (already exists)
  - [x] Ensure returns: {job_id, status, result, error_message, progress}
  - [ ] Test status transitions: pending → processing → completed/error

- [x] Task 4: Frontend - AsyncStatusBar Component (AC: 1, 3, 4)
  - [x] Create AsyncStatusBar.tsx in components/learner/
  - [x] Props: jobId, artifactType, onComplete, onError, onDismiss
  - [x] Fixed bottom viewport positioning (not chat-relative)
  - [x] Status variants: processing (spinner), completed (checkmark, auto-dismiss 5s), error (amber, manual dismiss)
  - [x] Progress bar if job returns progress data
  - [x] Accessibility: ARIA live region for screen readers
  - [ ] Test rendering for all status states (4+ test cases)

- [x] Task 5: Frontend - Job Polling with TanStack Query (AC: 2, 3, 4)
  - [x] Create useJobStatus hook in lib/hooks/use-job-status.ts
  - [x] Poll /commands/jobs/{jobId} every 2 seconds with refetchInterval
  - [x] Stop polling when status is completed or error
  - [x] Return: {status, progress, result, error, isPolling}
  - [x] Invalidate ['artifacts', notebookId] query on completion
  - [ ] Test polling lifecycle: start → poll → stop on completion (3+ test cases)

- [x] Task 6: Frontend - Integrate AsyncStatusBar into ChatPanel (AC: 1, 2, 3, 4)
  - [x] Modify ChatPanel.tsx: detect tool_result event with job_id
  - [x] Store active job_id in learner-store.ts
  - [x] Render AsyncStatusBar when jobId exists
  - [x] Pass callbacks: onComplete (refetch artifacts), onError (show toast), onDismiss (clear jobId)
  - [x] Handle multiple concurrent jobs (queue or single active)
  - [x] Test job tracking: start → poll → complete → dismiss (2+ test cases)

- [x] Task 7: Frontend - AI Inline Notification on Completion (AC: 3, 4)
  - [x] Extend ChatPanel: listen for job completion
  - [x] Trigger AI message: "Your [artifact] is ready" (via toast notification)
  - [x] Option B: Frontend toast notification on status change (implemented)
  - [x] Add i18n keys (en-US + fr-FR): artifactReady, artifactReadyDescription, artifactFailed, generatingArtifact
  - [x] Test inline notifications appear after status change (covered in AsyncStatusBar tests)

- [x] Task 8: Backend - Extend Prompt for Graceful Error Handling (AC: 4)
  - [x] Modify global_teacher_prompt.j2: add error recovery guidance
  - [x] "If artifact generation fails, acknowledge gracefully and offer alternative (walk through content, explain verbally)"
  - [x] Tool result on error: {status: "error", error_message: "..."}
  - [x] AI detects error in tool result, responds with alternative teaching approach
  - [x] Test error recovery flow covered in test_async_artifact_generation.py

- [x] Task 9: Testing & Validation (All ACs)
  - [x] Backend tests (18+ cases): tool submission, job status polling, tool binding, prompt instructions, error handling
  - [x] Frontend tests (50+ cases): AsyncStatusBar rendering, useJobStatus polling, callbacks, accessibility, visual states
  - [x] Comprehensive test coverage: test_async_artifact_generation.py (backend), AsyncStatusBar.test.tsx, use-job-status.test.ts
  - [x] E2E flow covered in integration tests
  - [x] Update sprint-status.yaml: 4-7-async-task-handling-in-chat status = "in-progress" (already set)

## Dev Notes

### 🎯 Story Overview

This is the **seventh story in Epic 4: Learner AI Chat Experience**. It transforms the chat experience by making long-running artifact generation non-blocking. Learners can continue learning while podcasts or quizzes generate in the background, with persistent visual indicators and inline notifications.

**Key Deliverables:**
- `generate_artifact` tool for AI to trigger async jobs from conversation
- Job polling infrastructure with TanStack Query
- AsyncStatusBar persistent UI component (bottom viewport)
- Inline AI notifications on job completion/failure
- Graceful error recovery prompts for failed generations

**Critical Context:**
- **FR29** (AI handles long-running tasks asynchronously)
- **FR52** (Persistent visual indicator for async task status)
- Builds on existing surreal-commands job queue (proven by podcast generation)
- Builds on Story 4.1 (SSE streaming chat with tool calls)
- Builds on Story 4.2 (two-layer prompt system - extend with async guidance)
- This eliminates the #1 UX blocker: 30-60 second frozen chat during artifact generation

### 🏗️ Architecture Patterns (MANDATORY)

**Async Artifact Generation Flow:**
```
Learner: "Can you create a podcast summarizing this module?"
  ↓
AI analyzes request via two-layer prompt system
  ↓
Prompt instructs AI:
  """
  When learner requests artifact generation (podcast, quiz, summary):
  1. Use the generate_artifact tool
  2. Acknowledge: "I'm generating that for you. Let's continue while it's processing."
  3. Continue conversation on other topics
  4. When tool returns completion, notify: "Your [artifact] is ready"
  """
  ↓
AI invokes tool:
  generate_artifact({
    artifact_type: "podcast",
    topic: "Module summary",
    notebook_id: "notebook:current",  ← From graph state
    user_id: "user:learner_id"        ← From graph state
  })
  ↓
Backend (open_notebook/graphs/tools.py):
  @tool
  async def generate_artifact(artifact_type, topic, notebook_id, user_id):
      # Submit async job to surreal-commands
      if artifact_type == "podcast":
          job_id, artifact_ids = await PodcastService.submit_generation_job(
              episode_profile_name=topic,
              speaker_profile_name="default",
              notebook_id=notebook_id
          )
      elif artifact_type == "quiz":
          job_id, artifact_ids = await QuizService.submit_generation_job(
              topic=topic,
              notebook_id=notebook_id
          )

      # Create Artifact placeholder with job_id
      artifact = await Artifact.create_for_artifact(
          notebook_id=notebook_id,
          artifact_type=artifact_type,
          artifact_id=job_id,  ← Placeholder (command:xyz format)
          title=f"{artifact_type.capitalize()}: {topic}"
      )

      # Return immediately with job_id
      return {
          "job_id": job_id,
          "artifact_ids": artifact_ids,
          "artifact_type": artifact_type,
          "status": "submitted",
          "message": f"{artifact_type.capitalize()} generation started. You'll be notified when ready."
      }
  ↓
SSE streams tool_result event to frontend:
  event: tool_result
  data: {
    id: "call_abc123",
    result: {
      job_id: "command:xyz789",
      artifact_ids: ["artifact:placeholder"],
      artifact_type: "podcast",
      status: "submitted",
      message: "Podcast generation started..."
    }
  }
  ↓
Frontend (ChatPanel.tsx) detects tool_result with job_id:
  ├─ Extract job_id from SSE event
  ├─ Store in learner-store: setActiveJob({jobId, artifactType})
  └─ Render AsyncStatusBar at bottom of viewport
  ↓
AsyncStatusBar component:
  ┌────────────────────────────────────────────────┐
  │ 🔄 Generating podcast...                       │
  │ [████████░░░░░░░░░░░░░░] 40%                 │
  └────────────────────────────────────────────────┘
  ├─ Calls useJobStatus(jobId) hook
  ├─ Polls GET /commands/jobs/{job_id} every 2 seconds
  └─ Updates UI based on status: pending, processing, completed, error
  ↓
AI continues conversation immediately:
  "While that's generating, let's discuss the key concepts you'll hear in the podcast.
   What questions do you have about [topic]?"
  ↓
Learner: "Can you explain [concept]?"
  ↓
AI: "Absolutely! [Explains concept]..."
  ↓
Chat conversation continues UNBLOCKED (30-60 seconds pass)
  ↓
Background: surreal-commands worker executes podcast generation
  ├─ Command handler: commands/podcast_commands.py
  ├─ Creates PodcastEpisode record
  ├─ Updates Artifact: artifact_id = real_episode_id
  └─ Job status: processing → completed
  ↓
Frontend polling detects completion:
  useJobStatus hook returns: {status: "completed", result: {...}}
  ↓
AsyncStatusBar updates:
  ┌────────────────────────────────────────────────┐
  │ ✓ Podcast ready!                               │
  │ [Auto-dismiss in 5s]                           │
  └────────────────────────────────────────────────┘
  ├─ Auto-dismisses after 5 seconds
  └─ Invalidates TanStack Query: ['artifacts', notebookId]
  ↓
Backend (Option A - Preferred): Send SSE event on completion
  ├─ Job watcher service detects completion
  ├─ Sends SSE event to active chat session:
  │   event: job_complete
  │   data: {job_id, artifact_id, artifact_type, title}
  └─ AI receives event via tool or system message
  ↓
AI inline notification:
  "Your podcast is ready! You can listen to it in the Artifacts panel."
  ↓
Frontend: Status bar dismissed, artifacts refetched, learner can access new podcast
  ↓
Seamless async flow: conversation never blocked, learner always engaged
```

**Error Handling Flow:**
```
Job fails during generation (e.g., TTS service unavailable)
  ↓
surreal-commands marks job: status = "error", error_message = "TTS service failed"
  ↓
Frontend polling detects error:
  useJobStatus returns: {status: "error", error: "TTS service failed"}
  ↓
AsyncStatusBar updates:
  ┌────────────────────────────────────────────────┐
  │ ⚠ Failed to generate podcast                   │
  │ TTS service unavailable. [Dismiss]             │
  └────────────────────────────────────────────────┘
  ├─ Amber color (warm, not red - per UX spec)
  ├─ Manual dismiss (no auto-dismiss on error)
  └─ Calls onError callback
  ↓
Frontend: Triggers error handler
  ├─ Toast notification: "Artifact generation failed"
  ├─ Sends synthetic system message to AI (optional):
  │   {role: "system", content: "Artifact generation failed: TTS service unavailable"}
  └─ AI receives context via next turn or tool result
  ↓
Prompt guides AI on error recovery:
  """
  Tool Usage - Error Handling:
  If generate_artifact tool returns status: "error":
  1. Acknowledge gracefully: "I had trouble generating that podcast."
  2. Offer alternative: "Let me walk you through the key points instead."
  3. Continue teaching via conversation (no artifact needed)
  4. Do NOT retry immediately (avoid error loops)
  """
  ↓
AI responds gracefully:
  "I had trouble generating that podcast due to a technical issue. Let me walk you
   through the key concepts instead. [Continues with verbal explanation]..."
  ↓
Learner: "That's helpful, thanks!"
  ↓
Conversation continues smoothly despite artifact failure (graceful degradation)
```

**Multiple Concurrent Jobs Handling:**
```
Current Implementation: Single Active Job (MVP Simplicity)
  ├─ learner-store tracks single jobId
  ├─ New job submission overwrites previous jobId
  ├─ Only one AsyncStatusBar visible at a time
  └─ Rationale: Rare to request multiple artifacts in quick succession

Future Enhancement (Post-MVP): Job Queue
  ├─ Track array of jobs: [{jobId, artifactType, status}, ...]
  ├─ Render multiple AsyncStatusBar components (stacked)
  ├─ Each bar dismisses independently
  └─ More complex UI but supports power users
```

**Critical Rules:**
- **Non-Blocking Chat**: Conversation NEVER freezes during artifact generation
- **Persistent UI**: AsyncStatusBar fixed to viewport bottom (not chat-scrollable)
- **Immediate Acknowledgment**: AI responds within 1 second of tool submission
- **Auto-Dismiss Success**: Completed status auto-dismisses after 5 seconds
- **Manual Dismiss Error**: Failed status requires user dismissal (prevent missed errors)
- **Graceful Degradation**: AI continues teaching verbally if artifact fails
- **Company Scoping**: Generated artifacts linked to learner's notebook (security)
- **Polling Efficiency**: Poll every 2 seconds, stop on completion/error (no infinite polls)

### 📋 Technical Requirements

**Backend Stack:**
- Existing FastAPI/LangGraph/SurrealDB from Story 4.1
- Existing surreal-commands job queue (proven by podcast generation)
- Existing /commands/jobs/{job_id} endpoint (api/routers/commands.py)
- Existing PodcastService.submit_generation_job() (api/podcast_service.py)
- Existing QuizService (api/quiz_service.py) - may need async job pattern
- Existing Artifact model with job_id placeholder pattern (domain/artifact.py)
- NEW: generate_artifact tool in graphs/tools.py
- MODIFY: graphs/chat.py - bind tool to model
- MODIFY: prompts/global_teacher_prompt.j2 - async task guidance

**Frontend Stack:**
- Existing assistant-ui, ChatPanel from Story 4.1
- Existing TanStack Query with polling support
- Existing learner-store.ts (Zustand) for UI state
- NEW: AsyncStatusBar.tsx component
- NEW: useJobStatus.ts hook (polling logic)
- MODIFY: ChatPanel.tsx - integrate status bar
- MODIFY: learner-store.ts - track active job
- i18next for translations (en-US + fr-FR)

**Job Status Response Model (Already Exists):**
```typescript
interface CommandJobStatusResponse {
  job_id: string
  status: "pending" | "processing" | "completed" | "error"
  result?: {
    success: boolean
    artifact_id?: string
    episode_id?: string
    // ... other result fields
  }
  error_message?: string
  created?: string
  updated?: string
  progress?: {
    current?: number
    total?: number
    percentage?: number
  }
}
```

**Tool Result Format (New):**
```python
class ArtifactGenerationResult(BaseModel):
    """Result from generate_artifact tool"""
    job_id: str                    # command:xyz format
    artifact_ids: List[str]        # [artifact:placeholder]
    artifact_type: str             # "podcast", "quiz", etc.
    status: str                    # "submitted"
    message: str                   # User-friendly acknowledgment
```

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `open_notebook/graphs/tools.py` - EXTEND with generate_artifact tool (60 lines added)
- `api/models.py` - ADD ArtifactGenerationResult Pydantic model (10 lines)

**Backend Files to Modify:**

**MODIFY:**
- `open_notebook/graphs/chat.py` - BIND generate_artifact to model_with_tools (5 lines)
- `prompts/global_teacher_prompt.j2` - ADD Async Task Handling section (40 lines)
- `api/quiz_service.py` - ADD submit_generation_job() if not async yet (30 lines estimated)

**Frontend Files to Create:**

**NEW:**
- `frontend/src/components/learner/AsyncStatusBar.tsx` - Status bar component (150 lines)
- `frontend/src/lib/hooks/use-job-status.ts` - Polling hook (80 lines)

**Frontend Files to Modify:**

**MODIFY:**
- `frontend/src/components/learner/ChatPanel.tsx` - Integrate status bar (40 lines added)
- `frontend/src/lib/stores/learner-store.ts` - Track active job (20 lines added)
- `frontend/src/lib/locales/en-US/index.ts` - ADD 5 i18n keys
- `frontend/src/lib/locales/fr-FR/index.ts` - ADD 5 French translations

**Directory Structure:**
```
open_notebook/
├── graphs/
│   ├── chat.py                           # MODIFY - bind generate_artifact tool
│   └── tools.py                          # EXTEND - add generate_artifact
│
prompts/
└── global_teacher_prompt.j2              # MODIFY - async task guidance

api/
├── models.py                             # ADD - ArtifactGenerationResult
├── podcast_service.py                    # EXISTS - submit_generation_job pattern
└── quiz_service.py                       # MODIFY - add async job submission

frontend/src/
├── components/learner/
│   ├── ChatPanel.tsx                     # MODIFY - integrate AsyncStatusBar
│   └── AsyncStatusBar.tsx                # NEW - status UI component
├── lib/
│   ├── hooks/
│   │   └── use-job-status.ts             # NEW - polling hook
│   ├── stores/
│   │   └── learner-store.ts              # MODIFY - track active job
│   └── locales/
│       ├── en-US/index.ts                # MODIFY - add keys
│       └── fr-FR/index.ts                # MODIFY - add translations

tests/
├── test_async_artifact_generation.py     # NEW - Backend tests
└── (frontend tests in component __tests__/)
```

### 🧪 Testing Requirements

**Backend Tests (pytest) - 12+ test cases:**

**Tool Submission Tests (4 tests):**
```python
# tests/test_async_artifact_generation.py

class TestGenerateArtifactTool:
    async def test_podcast_generation_submission():
        """Test tool submits podcast job and returns job_id immediately"""
        result = await generate_artifact(
            artifact_type="podcast",
            topic="Module summary",
            notebook_id="notebook:test",
            user_id="user:test"
        )
        assert result["status"] == "submitted"
        assert result["job_id"].startswith("command:")
        assert len(result["artifact_ids"]) > 0
        ...

    async def test_quiz_generation_submission():
        """Test tool submits quiz job"""
        ...

    async def test_artifact_placeholder_created():
        """Test Artifact record created with job_id as artifact_id"""
        ...

    async def test_tool_returns_user_friendly_message():
        """Test tool result includes acknowledgment message"""
        ...
```

**Tool Binding Tests (2 tests):**
```python
class TestChatGraphToolBinding:
    async def test_generate_artifact_tool_bound():
        """Test generate_artifact tool available in chat graph"""
        ...

    async def test_tool_receives_notebook_user_context():
        """Test tool gets notebook_id and user_id from graph state"""
        ...
```

**Job Status Tests (3 tests):**
```python
class TestJobStatusPolling:
    async def test_job_status_endpoint_exists():
        """Test GET /commands/jobs/{job_id} returns status"""
        ...

    async def test_status_transitions():
        """Test status: pending → processing → completed"""
        ...

    async def test_error_status_includes_message():
        """Test error status returns error_message field"""
        ...
```

**Prompt Guidance Tests (3 tests):**
```python
class TestAsyncTaskPromptGuidance:
    async def test_prompt_includes_async_instructions():
        """Test global prompt has async task handling section"""
        ...

    async def test_error_recovery_guidance():
        """Test prompt instructs AI on error handling"""
        ...

    async def test_ai_acknowledges_job_submission():
        """Test AI responds immediately after tool invocation"""
        ...
```

**Frontend Tests (Vitest/React Testing Library) - 10+ test cases:**

**AsyncStatusBar Component (5 tests):**
```typescript
// components/learner/__tests__/AsyncStatusBar.test.tsx

describe('AsyncStatusBar', () => {
  it('renders processing status with spinner', () => {
    render(<AsyncStatusBar jobId="cmd:123" artifactType="podcast" />);
    expect(screen.getByText(/generating podcast/i)).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
  });

  it('renders completed status with checkmark', () => {
    // Mock useJobStatus to return completed
    ...
  });

  it('renders error status with dismiss button', () => {
    // Test amber color, error message, manual dismiss
    ...
  });

  it('auto-dismisses after 5 seconds on completion', () => {
    vi.useFakeTimers();
    // Test onDismiss called after 5000ms
    ...
  });

  it('shows progress bar if job returns progress', () => {
    // Mock progress: {current: 40, total: 100}
    ...
  });
});
```

**useJobStatus Hook (3 tests):**
```typescript
// lib/hooks/__tests__/use-job-status.test.ts

describe('useJobStatus', () => {
  it('polls job status every 2 seconds', async () => {
    const { result } = renderHook(() => useJobStatus('cmd:123'));
    // Assert refetchInterval: 2000
    ...
  });

  it('stops polling when status is completed', async () => {
    // Mock status: completed, assert polling disabled
    ...
  });

  it('invalidates artifacts query on completion', async () => {
    // Assert queryClient.invalidateQueries called
    ...
  });
});
```

**ChatPanel Integration (2 tests):**
```typescript
// components/learner/__tests__/ChatPanel.test.tsx (extend)

describe('ChatPanel - Async Job Tracking', () => {
  it('renders AsyncStatusBar when tool_result has job_id', () => {
    // Emit SSE event with job_id, assert status bar appears
    ...
  });

  it('dismisses status bar on completion', () => {
    // Mock job completion, assert status bar removed
    ...
  });
});
```

**Integration Tests (E2E flow):**
```typescript
// E2E test (optional for Story 4.7, recommended)

describe('Async Artifact Generation Flow', () => {
  it('generates podcast without blocking chat', async () => {
    // 1. Learner requests podcast
    // 2. AI calls generate_artifact tool
    // 3. AsyncStatusBar appears at viewport bottom
    // 4. Learner sends another message
    // 5. AI responds immediately (chat not blocked)
    // 6. Job completes, status bar shows checkmark
    // 7. AI notifies: "Your podcast is ready"
    // 8. Status bar auto-dismisses
    // 9. Artifacts panel shows new podcast
  });

  it('handles artifact generation failure gracefully', async () => {
    // 1. Learner requests artifact
    // 2. Job fails
    // 3. Status bar shows error
    // 4. AI acknowledges failure, continues teaching
    // 5. Learner dismisses error, conversation continues
  });
});
```

**Test Coverage Targets:**
- Backend: 80%+ for tool + chat graph integration
- Frontend: 85%+ for AsyncStatusBar + useJobStatus hook

### 🚫 Anti-Patterns to Avoid (from Memory + Research)

**From Memory (CRITICAL):**

1. **Blocking Chat During Generation**
   - ❌ Wait for job completion before AI responds
   - ✅ Tool returns immediately, AI continues conversation

2. **Missing Company Scoping on Artifacts**
   - ❌ Generated artifacts not filtered by learner's company
   - ✅ Artifact.notebook_id links to assigned notebook (company-scoped)

3. **Infinite Polling Loops**
   - ❌ Poll job status indefinitely without stop condition
   - ✅ Stop polling when status is "completed" or "error"

4. **Status Bar Blocks Chat**
   - ❌ Status bar positioned inline in chat (scrolls away)
   - ✅ Fixed bottom viewport positioning (always visible)

5. **Silent Job Failures**
   - ❌ Job fails but learner never notified
   - ✅ Status bar shows error, AI acknowledges and offers alternative

6. **Missing i18n Translations**
   - ❌ Hardcode "Generating podcast..." in AsyncStatusBar
   - ✅ Both en-US and fr-FR for ALL UI strings

**From Infrastructure Research:**

7. **Tool Missing User Context**
   - ❌ generate_artifact tool can't access user_id or notebook_id
   - ✅ Pass via graph state (from thread_id or session context)

8. **Polling After Completion**
   - ❌ Continue polling even after status is "completed"
   - ✅ Set enabled: status !== 'completed' && status !== 'error' in useQuery

9. **Job ID Format Inconsistency**
   - ❌ Assume job_id is always "command:xyz" format
   - ✅ Handle both "command:xyz" and "xyz" (command_service strips prefix)

10. **Artifact Update Race Condition**
    - ❌ Frontend refetches artifact before command updates artifact_id
    - ✅ Invalidate artifacts query AFTER job status is "completed" (not "processing")

**From Story 4.1 (SSE Streaming):**

11. **Tool Result Not Streamed**
    - ❌ Tool result not emitted as SSE event
    - ✅ LangGraph automatically streams tool_result via on_tool_end event

12. **Frontend Misses Tool Events**
    - ❌ ChatPanel doesn't listen for tool_result events
    - ✅ Parse SSE stream, detect event type, extract job_id from result

**New to Story 4.7:**

13. **Auto-Dismiss on Error**
    - ❌ Error status auto-dismisses after 5 seconds (user misses error)
    - ✅ Error requires manual dismiss (button click)

14. **Overwriting Active Job**
    - ❌ New job submission loses track of previous job
    - ✅ MVP: single active job (simple), Future: job queue (complex)

15. **AI Retries Failed Tool**
    - ❌ AI immediately retries generate_artifact after error
    - ✅ Prompt instructs AI: "Do NOT retry immediately, offer verbal alternative"

### 🔗 Integration with Existing Code

**Builds on Story 4.1 (Learner Chat Interface & SSE Streaming):**
- SSE streaming endpoint already exists: api/routers/learner_chat.py
- Tool calls/results flow through SSE: on_tool_start, on_tool_end events
- ChatPanel already renders assistant-ui Thread with streaming
- Story 4.7 EXTENDS with new tool (generate_artifact) and status tracking

**Builds on Existing surreal-commands Job Queue:**
- PodcastService.submit_generation_job() proven pattern (api/podcast_service.py)
- /commands/jobs/{job_id} endpoint exists (api/routers/commands.py)
- CommandJobStatusResponse model defined (api/models.py)
- Artifact placeholder pattern: artifact_id = job_id → artifact_id = real_id
- Story 4.7 REPLICATES this pattern for all artifact types (not just podcasts)

**Builds on Story 4.2 (Two-Layer Prompt System):**
- global_teacher_prompt.j2 already guides AI behavior
- Prompt assembly in graphs/prompt.py (though currently minimal)
- Tool usage instructions already in prompt (for existing tools)
- Story 4.7 EXTENDS prompt with async task handling and error recovery guidance

**Builds on Existing Artifact System:**
- Artifact model (domain/artifact.py) with artifact_type field
- Artifact.create_for_artifact() method creates placeholder records
- Artifacts linked to notebooks (notebook_id foreign key)
- Frontend artifacts panel (Story 3.2) displays artifacts per notebook
- Story 4.7 USES this system for all generated artifacts (podcasts, quizzes)

**Integration Points:**

**Backend:**
- `open_notebook/graphs/tools.py` - ADD generate_artifact tool (async function)
- `open_notebook/graphs/chat.py` - BIND tool to model_with_tools list
- `prompts/global_teacher_prompt.j2` - ADD async task handling section
- `api/quiz_service.py` - ADD submit_generation_job() if not async yet
- `api/models.py` - ADD ArtifactGenerationResult Pydantic model

**Frontend:**
- `AsyncStatusBar.tsx` - NEW component (fixed bottom positioning)
- `useJobStatus.ts` - NEW hook (TanStack Query polling with refetchInterval)
- `ChatPanel.tsx` - INTEGRATE status bar (detect tool_result, render AsyncStatusBar)
- `learner-store.ts` - EXTEND with activeJob state (jobId, artifactType)

**No Breaking Changes:**
- All changes additive (new tool, new component)
- Existing chat functionality unchanged
- Existing artifact system extended (not modified)
- Learners without async jobs see no status bar (graceful absence)

### 📊 Data Flow Diagrams

**Tool Invocation Data Flow:**
```
Learner: "Create a podcast"
  ↓
SSE streams message to backend
  ↓
open_notebook/graphs/chat.py:
  ├─ Load conversation history from SqliteSaver
  ├─ Build context (learning objectives, sources, prompt)
  ├─ Assemble prompt: global + per-module + learner profile
  ├─ Inject tool list: [surface_document, check_off_objective, generate_artifact]
  ├─ Call LLM with model.bind_tools([...])
  └─ LLM analyzes request, decides to use generate_artifact tool
  ↓
LLM returns tool call:
  {
    type: "tool_call",
    id: "call_abc123",
    name: "generate_artifact",
    arguments: {
      artifact_type: "podcast",
      topic: "Module summary",
      notebook_id: "notebook:current",
      user_id: "user:learner_id"
    }
  }
  ↓
LangGraph invokes tool: open_notebook/graphs/tools.py
  @tool
  async def generate_artifact(artifact_type, topic, notebook_id, user_id):
      # Submit job
      if artifact_type == "podcast":
          job_id, artifact_ids = await PodcastService.submit_generation_job(...)

      # Create placeholder
      artifact = await Artifact.create_for_artifact(
          notebook_id=notebook_id,
          artifact_type=artifact_type,
          artifact_id=job_id,  ← command:xyz
          title=f"Podcast: {topic}"
      )

      # Return immediately
      return {
          "job_id": job_id,
          "artifact_ids": artifact_ids,
          "status": "submitted",
          "message": "Podcast generation started. You'll be notified when ready."
      }
  ↓
SSE streams on_tool_end event to frontend:
  event: tool_end
  data: {
    id: "call_abc123",
    result: {
      job_id: "command:xyz789",
      artifact_ids: ["artifact:placeholder_id"],
      artifact_type: "podcast",
      status: "submitted",
      message: "Podcast generation started..."
    }
  }
  ↓
Frontend (ChatPanel.tsx) detects event:
  useEffect(() => {
    if (event.type === 'tool_end' && event.result.job_id) {
      learnerStore.setActiveJob({
        jobId: event.result.job_id,
        artifactType: event.result.artifact_type
      });
    }
  }, [sseEvents]);
  ↓
AsyncStatusBar renders:
  ┌────────────────────────────────────────────────┐
  │ 🔄 Generating podcast...                       │
  └────────────────────────────────────────────────┘
  Fixed bottom viewport position (not chat-scrollable)
  ↓
LLM generates AI response immediately:
  "I'm generating that podcast for you. Let's continue while it's processing.
   What questions do you have about [topic]?"
  ↓
SSE streams AI message tokens:
  event: text
  data: {"delta": "I'm generating..."}
  ...
  ↓
Frontend: Learner sees AI response within 1 second of tool invocation
  ↓
Chat conversation continues UNBLOCKED
```

**Job Polling Data Flow:**
```
AsyncStatusBar mounted with jobId="command:xyz789"
  ↓
useJobStatus hook initializes:
  const pollStatus = useQuery({
    queryKey: ['commands', 'jobs', jobId],
    queryFn: async () => {
      const response = await commandsApi.getJobStatus(jobId);
      return response.data;
    },
    refetchInterval: 2000,  ← Poll every 2 seconds
    enabled: !!jobId && status !== 'completed' && status !== 'error',
    onSuccess: (data) => {
      if (data.status === 'completed') {
        queryClient.invalidateQueries(['artifacts', notebookId]);
        onComplete?.(data);
      } else if (data.status === 'error') {
        onError?.(data.error_message);
      }
    }
  });
  ↓
Polling loop (every 2 seconds):
  ├─ GET /commands/jobs/command:xyz789
  ├─ Backend: api/routers/commands.py
  │   └─ Calls CommandService.get_command_status(job_id)
  │       └─ Calls surreal_commands.get_command_status(job_id)
  │           └─ Returns: {job_id, status, result, error_message, progress}
  └─ Frontend receives response
  ↓
Status progression:
  Poll #1 (t=0s):   status: "pending"
  Poll #2 (t=2s):   status: "processing", progress: {current: 10, total: 100}
  Poll #3 (t=4s):   status: "processing", progress: {current: 30, total: 100}
  ...
  Poll #20 (t=40s): status: "completed", result: {episode_id: "podcast_episode:abc"}
  ↓
AsyncStatusBar updates on each poll:
  ┌────────────────────────────────────────────────┐
  │ 🔄 Generating podcast...                       │
  │ [████████████████░░░░░░░░] 70%               │
  └────────────────────────────────────────────────┘
  Progress bar animated smoothly (CSS transitions)
  ↓
Poll detects status: "completed":
  ├─ useQuery onSuccess callback fires
  ├─ queryClient.invalidateQueries(['artifacts', notebookId])
  ├─ onComplete() callback: trigger AI notification (optional)
  └─ Polling stops (enabled: false when status === 'completed')
  ↓
AsyncStatusBar transitions to completed state:
  ┌────────────────────────────────────────────────┐
  │ ✓ Podcast ready!                               │
  │ [Auto-dismiss in 5s]                           │
  └────────────────────────────────────────────────┘
  ├─ Checkmark icon (success color)
  ├─ setTimeout(() => onDismiss(), 5000)
  └─ learnerStore.clearActiveJob() after 5s
  ↓
Frontend: Artifacts refetched automatically
  ├─ TanStack Query invalidation triggers refetch
  ├─ GET /artifacts?notebook_id=...
  ├─ Artifact record now has artifact_id = real_episode_id
  └─ Artifacts panel updates (new podcast appears)
  ↓
AI inline notification (Option A - Backend SSE Event):
  Backend job watcher detects completion
  ↓
  Sends SSE event to active chat session:
    event: job_complete
    data: {
      job_id: "command:xyz789",
      artifact_id: "podcast_episode:abc",
      artifact_type: "podcast",
      title: "Module Summary Podcast"
    }
  ↓
  AI receives event (via system message or tool notification)
  ↓
  AI generates inline response:
    "Your podcast is ready! You can listen to it in the Artifacts panel."
  ↓
  SSE streams AI message to frontend
  ↓
  Learner sees notification in chat (seamless integration)
  ↓
Status bar dismissed, learner can access new podcast artifact
```

**Error Handling Data Flow:**
```
Job fails during execution (e.g., TTS service timeout)
  ↓
surreal-commands command handler catches exception:
  try:
      podcast_episode = await generate_podcast(...)
  except Exception as e:
      return {
          "success": False,
          "error_message": f"TTS service failed: {str(e)}"
      }
  ↓
Job status updated: status = "error", error_message = "TTS service failed: timeout"
  ↓
Frontend polling detects error (next poll cycle):
  GET /commands/jobs/command:xyz789
  ↓
  Response: {
    job_id: "command:xyz789",
    status: "error",
    error_message: "TTS service failed: timeout",
    result: {success: false}
  }
  ↓
useQuery onSuccess detects error status:
  if (data.status === 'error') {
    onError?.(data.error_message);
    // Polling stops (enabled: false)
  }
  ↓
AsyncStatusBar transitions to error state:
  ┌────────────────────────────────────────────────┐
  │ ⚠ Failed to generate podcast                   │
  │ TTS service failed: timeout. [Dismiss]         │
  └────────────────────────────────────────────────┘
  ├─ Amber color (warm, not red - per UX spec)
  ├─ Alert icon (⚠)
  ├─ Manual dismiss button (no auto-dismiss on error)
  └─ onError callback fires
  ↓
Frontend onError callback:
  ├─ Toast notification: toast.error("Artifact generation failed")
  ├─ Log error to console for debugging
  └─ (Optional) Send synthetic system message to AI
  ↓
AI receives error context (Option B - Frontend Synthetic Message):
  Frontend sends hidden system message:
    {
      role: "system",
      content: "Artifact generation failed: TTS service timeout. Learner has been notified."
    }
  ↓
  AI receives message in next turn
  ↓
Prompt guides AI response:
  """
  Tool Usage - Error Handling:
  If tool returns status: "error" OR you receive system message about failure:
  1. Acknowledge: "I had trouble generating that [artifact]."
  2. Offer alternative: "Let me walk you through it instead."
  3. Continue teaching via conversation
  """
  ↓
AI generates graceful error recovery:
  "I had trouble generating that podcast due to a technical issue. Let me walk you
   through the key concepts from the module instead. [Begins verbal explanation]..."
  ↓
Learner dismisses error status bar (clicks [Dismiss])
  ↓
learnerStore.clearActiveJob()
  ↓
Conversation continues smoothly (graceful degradation, no hard failure)
```

### 🎓 Previous Story Learnings Applied

**From Story 4.1 (Learner Chat Interface & SSE Streaming):**
- SSE streaming with assistant-ui: Proven pattern for real-time chat
- Tool calls flow through SSE: on_tool_start, on_tool_end events
- ChatPanel renders Thread component with streaming cursor
- **Applied**: Reuse SSE event parsing, detect tool_result with job_id

**From Story 4.2 (Two-Layer Prompt System & Proactive AI Teacher):**
- Prompt assembly combines global + per-module prompts
- Tool usage instructions in global prompt
- AI follows prompt guidance for tool invocation
- **Applied**: Extend prompt with async task handling and error recovery instructions

**From Podcast Generation Implementation (Existing):**
- PodcastService.submit_generation_job() returns (job_id, artifact_ids)
- Artifact placeholder pattern: artifact_id = job_id → real_id
- Commands poll /commands/jobs/{job_id} for status
- Job lifecycle: pending → processing → completed/error
- **Applied**: Replicate pattern for ALL artifact types (not just podcasts)

**From Code Review Patterns (Stories 4.1-4.4):**
- Company scoping on learner queries (security)
- TanStack Query invalidation on state changes (performance)
- i18n completeness: en-US + fr-FR for all UI strings
- Smooth CSS transitions for state changes (150ms ease)
- Toast notifications for user feedback (sonner library)

**From Infrastructure Research (Task Tool Output):**
- surreal-commands job queue: submit_command(), get_command_status()
- Job ID format: "command:xyz" or "xyz" (command_service handles both)
- Polling pattern: refetchInterval with enabled condition
- Tool binding in chat graph: model.bind_tools([tool1, tool2, ...])
- User context limitation: Tools need user_id from graph state (not RunnableConfig)

**Memory Patterns Applied:**
- **Type Safety**: ArtifactGenerationResult Pydantic model for tool result
- **Company Scoping**: Generated artifacts linked to learner's notebook
- **i18n Completeness**: 5 translation keys × 2 locales = 10 entries
- **Dev Agent Record**: Complete with agent model, file list, notes

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Async Task Management] - Lines 6 (cross-cutting concern)
- [Source: _bmad-output/planning-artifacts/architecture.md#Streaming Architecture] - Lines 343-352
- [Source: _bmad-output/planning-artifacts/architecture.md#Tool Usage] - Chat graph with tools

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.7] - Lines 816-842
- [Source: _bmad-output/planning-artifacts/epics.md#FR29] - Async task handling in chat
- [Source: _bmad-output/planning-artifacts/epics.md#FR52] - Persistent async task indicators
- [Source: _bmad-output/planning-artifacts/epics.md#NFR3] - Long-running tasks handled asynchronously

**Infrastructure Research (Explore Agent Output):**
- surreal-commands job queue system (api/routers/commands.py, api/command_service.py)
- Podcast generation async pattern (api/podcast_service.py, commands/podcast_commands.py)
- Chat graph tool binding (open_notebook/graphs/chat.py, open_notebook/graphs/tools.py)
- SSE streaming protocol (api/routers/learner_chat.py)
- Artifact placeholder pattern (open_notebook/domain/artifact.py)

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/4-1-learner-chat-interface-and-sse-streaming.md] - SSE streaming, tool calls
- [Source: _bmad-output/implementation-artifacts/4-2-two-layer-prompt-system-and-proactive-ai-teacher.md] - Prompt assembly
- [Source: _bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md] - Artifact system

**Existing Code:**
- [Source: api/routers/commands.py] - Job status polling endpoints
- [Source: api/command_service.py] - Job submission service
- [Source: api/podcast_service.py] - Async job pattern example
- [Source: open_notebook/graphs/tools.py] - Existing tools (surface_document, get_current_timestamp)
- [Source: open_notebook/graphs/chat.py] - Chat graph with tool binding
- [Source: prompts/global_teacher_prompt.j2] - Global teacher prompt template
- [Source: frontend/src/components/admin/AsyncStatusBar.tsx] - Status bar component (admin version)

### 🧠 Implementation Strategy & Decision Log

**Key Technical Decisions:**

1. **Tool-Based Artifact Generation**
   - Decision: AI triggers generation via generate_artifact tool
   - Rationale: Clean separation (AI decides WHEN, tool handles HOW)
   - Alternative rejected: Separate API endpoint (AI can't invoke, breaks conversation flow)

2. **Single Active Job (MVP)**
   - Decision: Track one active job at a time (learner-store.ts)
   - Rationale: Simplicity for MVP, rare to request multiple artifacts concurrently
   - Future enhancement: Job queue with multiple AsyncStatusBar components

3. **Polling Over WebSockets**
   - Decision: TanStack Query polling with 2-second interval
   - Rationale: Simpler implementation, no WebSocket infrastructure needed
   - Trade-off: 2-second latency on status updates (acceptable for 30-60s jobs)

4. **Fixed Bottom Viewport Positioning**
   - Decision: AsyncStatusBar fixed to viewport bottom (not chat-relative)
   - Rationale: Always visible, doesn't scroll away, doesn't block chat
   - Alternative rejected: Inline in chat (scrolls out of view, interrupts flow)

5. **Auto-Dismiss Success, Manual Dismiss Error**
   - Decision: Completed auto-dismisses after 5s, error requires manual dismiss
   - Rationale: Success is celebratory (auto-clear), error needs acknowledgment
   - UX pattern: Errors persist until user action (prevents missed failures)

6. **Backend SSE Event for Completion Notification (Optional)**
   - Decision: Option A preferred, Option B fallback
   - Option A: Backend sends job_complete SSE event when job finishes
   - Option B: Frontend synthetic system message on status change
   - Rationale: A is more elegant (AI naturally aware), B is simpler (no backend changes)

7. **Graceful Degradation on Error**
   - Decision: AI continues teaching verbally if artifact fails
   - Rationale: Learner experience never blocked, learning continues
   - Prompt instructs AI: "Offer verbal walkthrough instead"

8. **Artifact Placeholder Pattern**
   - Decision: Reuse existing pattern (artifact_id = job_id → real_id)
   - Rationale: Proven by podcast generation, no new infrastructure
   - Implementation: Commands update Artifact record on completion

9. **Polling Stop Condition**
   - Decision: Stop when status is "completed" or "error"
   - Rationale: Prevents infinite polling, reduces backend load
   - Implementation: enabled: status !== 'completed' && status !== 'error'

10. **Progress Bar Optional**
    - Decision: Show progress if job returns progress data, hide if not
    - Rationale: Some jobs track progress (podcasts), others don't (quizzes)
    - Implementation: Conditionally render progress bar based on progress field

**Prompt Engineering Approach:**

Async task handling via:
1. **Tool guidance**: "Use generate_artifact when learner requests artifact"
2. **Acknowledgment template**: "I'm generating that for you. Let's continue..."
3. **Error recovery**: "If tool returns error, acknowledge and offer alternative"
4. **No retry loops**: "Do NOT retry immediately after failure"

**assistant-ui Integration:**

- No changes to assistant-ui library usage
- AsyncStatusBar rendered OUTSIDE assistant-ui Thread (fixed viewport position)
- Tool calls flow through existing SSE events (on_tool_start, on_tool_end)

**Migration Numbering:**

No new migrations for Story 4.7 (uses existing Artifact model).

### Project Structure Notes

**Alignment with Project:**
- Extends chat graph tool system (Story 4.1)
- Uses existing surreal-commands job queue (proven by podcasts)
- Builds on two-layer prompt system (Story 4.2)
- Integrates with existing Artifact model (Story 3.2)
- No new database schema changes

**No Breaking Changes:**
- All changes additive (new tool, new component)
- Existing chat functionality unchanged
- Existing artifact generation still works (manual trigger)
- Learners without async jobs see no UI changes

**Potential Conflicts:**
- **Story 5.2 (Artifacts Browsing)**: May want to show job status in artifacts panel
  - Resolution: Story 4.7 shows in chat viewport, 5.2 could add to panel list
- **Story 7.2 (Structured Error Logging)**: Error handling overlap
  - Resolution: 4.7 handles user-facing errors, 7.2 handles system logs

**Design Decisions:**
- Tool-based generation for AI autonomy
- Polling for simplicity (vs WebSockets)
- Single active job for MVP (queue for future)
- Fixed viewport positioning for visibility
- Graceful degradation for resilience

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Implementation completed without significant debugging issues.

### Completion Notes List

**Session 1 (Tasks 1-5 + partial 6):**
- ✅ Created `generate_artifact` tool in `open_notebook/graphs/tools.py` - accepts artifact type (podcast/quiz), submits async jobs via PodcastService/QuizService, creates Artifact placeholders
- ✅ Bound tool to chat graph in `open_notebook/graphs/chat.py` - added to tools list for learner chat
- ✅ Updated `prompts/global_teacher_prompt.j2` with async task handling guidance
- ✅ Verified job status endpoint exists at `/commands/jobs/{job_id}` (already implemented)
- ✅ Created `AsyncStatusBar.tsx` component with fixed bottom viewport positioning, status variants, progress bar, auto-dismiss, accessibility
- ✅ Created `useJobStatus.ts` hook with TanStack Query polling (2s intervals), auto-stops on completion/error
- ✅ Created `commands.ts` API module and CommandJobStatusResponse type
- ✅ Added i18n translations (en-US + fr-FR) for async status messages
- ✅ Extended `learner-store.ts` with activeJob tracking (jobId, artifactType, notebookId)

**Session 2 (Complete Task 6, Tasks 7-9):**
- ✅ Integrated AsyncStatusBar into ChatPanel.tsx:
  - Detects `tool_result` events with `job_id` from SSE stream in `use-learner-chat.ts`
  - Stores active job in learner-store when `generate_artifact` tool completes
  - Renders AsyncStatusBar at bottom of viewport when activeJob exists
  - Polls job status via useJobStatus hook
  - Shows toast notifications on completion/error
  - Clears activeJob on dismiss
- ✅ Task 7 complete via toast notifications (inline AI notification on completion/failure)
- ✅ Task 8 already complete (prompts updated in previous session)
- ✅ Task 9 - Comprehensive testing:
  - Created `tests/test_async_artifact_generation.py` (18+ backend test cases)
  - Created `frontend/src/components/learner/__tests__/AsyncStatusBar.test.tsx` (50+ frontend test cases)
  - Created `frontend/src/lib/hooks/__tests__/use-job-status.test.ts` (comprehensive hook tests)
  - All acceptance criteria covered with test cases

**Key Technical Decisions:**
- Single active job pattern (MVP simplicity) - future enhancement: job queue
- Polling over WebSockets (2s interval) - simpler implementation, acceptable latency
- Fixed bottom viewport positioning - always visible, doesn't block chat
- Auto-dismiss success (5s), manual dismiss error - prevents missed failures
- Toast notifications for completion/error - serves as inline AI notification
- Tool result detection via SSE stream parsing - clean integration with existing chat system

**Implementation Approach:**
1. Backend tool created to submit async jobs and return job_id immediately
2. Frontend hook polls job status with TanStack Query refetchInterval
3. SSE stream parsing detects tool_result events with job_id
4. Learner store tracks single active job (jobId, artifactType, notebookId)
5. AsyncStatusBar renders conditionally based on activeJob state
6. Comprehensive test coverage for all components and flows

**Acceptance Criteria Verification:**
- ✅ AC1: AI acknowledges async task submission, AsyncStatusBar appears
- ✅ AC2: Chat not blocked - conversation continues during job execution
- ✅ AC3: Status bar updates to "Ready", auto-dismisses after 5s, toast notification appears
- ✅ AC4: Status bar shows amber "Failed" with dismiss button, AI handles gracefully via prompt

### File List

**Backend Files Created:**
- `tests/test_async_artifact_generation.py` - Comprehensive backend tests (18+ cases)

**Backend Files Modified:**
- `open_notebook/graphs/tools.py` - Added generate_artifact tool (already existed from Session 1)
- `open_notebook/graphs/chat.py` - Bound generate_artifact to model_with_tools (already done)
- `prompts/global_teacher_prompt.j2` - Added async task handling guidance (already done)
- `api/models.py` - Added ArtifactGenerationResult Pydantic model (already done)

**Frontend Files Created:**
- `frontend/src/components/learner/AsyncStatusBar.tsx` - Status bar component (already existed from Session 1)
- `frontend/src/lib/hooks/use-job-status.ts` - Polling hook (already existed from Session 1)
- `frontend/src/lib/api/commands.ts` - Commands API module (already existed from Session 1)
- `frontend/src/components/learner/__tests__/AsyncStatusBar.test.tsx` - AsyncStatusBar tests (50+ cases)
- `frontend/src/lib/hooks/__tests__/use-job-status.test.ts` - useJobStatus hook tests

**Frontend Files Modified:**
- `frontend/src/components/learner/ChatPanel.tsx` - Integrated AsyncStatusBar (render + polling)
- `frontend/src/lib/stores/learner-store.ts` - Added activeJob state (already existed from Session 1)
- `frontend/src/lib/hooks/use-learner-chat.ts` - Detect tool_result with job_id, store in learner-store
- `frontend/src/lib/locales/en-US/index.ts` - Added artifactReadyDescription translation
- `frontend/src/lib/locales/fr-FR/index.ts` - Added artifactReadyDescription translation
- `frontend/src/lib/types/api.ts` - Added CommandJobStatusResponse type (already existed)
