# Story 4.8: Persistent Chat History

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want to resume my previous conversation when returning to a module,
so that I don't lose context and can continue learning where I left off.

## Acceptance Criteria

**Given** a learner has had a previous conversation in a module
**When** they return to the module
**Then** the chat history loads with all previous messages scrolled to the end

**Given** a learner returns to a module
**When** the history is loaded
**Then** the AI sends a re-engagement message: "Welcome back. Last time we were discussing..."

**Given** conversation history exists
**When** loading the chat
**Then** the thread_id `user:{user_id}:notebook:{notebook_id}` ensures isolation per user per module

## Tasks / Subtasks

- [x] Task 1: Backend - Verify Thread ID Pattern & Checkpoint Storage (AC: 3)
  - [x] Verify thread_id format in api/routers/learner_chat.py: `user:{user_id}:notebook:{notebook_id}` ✅ Line 159
  - [x] Verify SqliteSaver checkpoint storage location: /data/sqlite-db/ ✅ chat.py lines 132-136
  - [x] Test conversation persistence: Thread ID format and determinism verified ✅ 4 tests passing
  - [x] Verify isolation: Thread isolation tests passing ✅ 4 tests passing
  - [x] Document checkpoint storage lifecycle: tests/test_chat_history.py created with 11 test cases

- [x] Task 2: Backend - Implement Re-engagement Message Generator (AC: 2)
  - [x] Create generate_re_engagement_greeting() function in open_notebook/graphs/prompt.py ✅
  - [x] Analyze last 3-5 messages from checkpoint history ✅ _analyze_conversation_topics()
  - [x] Extract topic/concept discussed (use LLM with small model for speed) ✅ gpt-4o-mini
  - [x] Generate contextual greeting: "Welcome back. Last time we were discussing [topic]..." ✅
  - [x] Fallback if history empty: use standard greeting from Story 4.2 ✅ generate_proactive_greeting()
  - [x] Test re-engagement with various conversation histories ✅ 3 tests passing

- [x] Task 3: Backend - Modify Chat Graph for History Loading (AC: 1, 2)
  - [x] Modified api/routers/learner_chat.py: detect returning vs new conversation ✅
  - [x] Check if checkpoint exists for thread_id ✅ Lines 165-191
  - [x] If history exists AND no messages in current turn → trigger re-engagement ✅ is_returning_user flag
  - [x] Load full conversation history from SqliteSaver ✅ Extract messages from checkpoint
  - [x] Pass history to re-engagement greeting generator ✅ generate_re_engagement_greeting()
  - [x] Import generate_re_engagement_greeting() from prompt.py ✅ Line 25

- [x] Task 4: Backend - Extend Prompt for Re-engagement Context (AC: 2)
  - [x] Modified prompts/global_teacher_prompt.j2: add re-engagement guidance ✅
  - [x] Instruct AI: "When learner returns, reference previous conversation naturally" ✅ New section added
  - [x] Conversation summary injected via generate_re_engagement_greeting() ✅ Already done in Task 2
  - [x] Ensure learning objectives progress carries over ✅ Passed to re-engagement generator
  - [x] Re-engagement examples for beginner/intermediate/expert learners ✅

- [x] Task 5: Frontend - Load Chat History from Backend (AC: 1)
  - [x] Created GET /chat/learner/{notebook_id}/history endpoint ✅ api/routers/learner_chat.py
  - [x] Backend endpoint: return all messages from thread checkpoint ✅ Transforms LangChain → assistant-ui format
  - [x] Transform checkpoint format to assistant-ui message format ✅ ChatHistoryMessage model
  - [x] Created getChatHistory() API function ✅ frontend/src/lib/api/learner-chat.ts
  - [x] Created useChatHistory() hook ✅ frontend/src/lib/hooks/use-learner-chat.ts
  - [ ] Modify ChatPanel.tsx: use hook and pass to Thread (Task 6)

- [ ] Task 6: Frontend - Initialize Thread with History (AC: 1)
  - [ ] Pass history to assistant-ui Thread component via initialMessages prop
  - [ ] Ensure message order: oldest first
  - [ ] Auto-scroll to bottom after history loads
  - [ ] Handle loading state: skeleton messages while fetching
  - [ ] Test scroll behavior: history loads → scrolls to end (2+ test cases)

- [ ] Task 7: Frontend - Smooth Scroll to End Behavior (AC: 1)
  - [ ] Implement auto-scroll with smooth animation (150ms ease per UX spec)
  - [ ] Scroll after history renders AND after re-engagement message streams
  - [ ] Preserve scroll position if user manually scrolled up (don't force to bottom)
  - [ ] Add scroll-to-bottom button if user scrolled away from end
  - [ ] Test scroll interactions: auto-scroll, manual scroll, button (3+ test cases)

- [ ] Task 8: Frontend - Handle Empty History vs Returning User (AC: 2)
  - [ ] Detect first visit: no history endpoint returns empty array
  - [ ] Detect returning visit: history has messages
  - [ ] Show standard greeting on first visit (from Story 4.2)
  - [ ] Show re-engagement greeting on return
  - [ ] Add i18n keys (en-US + fr-FR): welcomeBack, continueDiscussion
  - [ ] Test both scenarios: first visit vs return (2+ test cases)

- [ ] Task 9: Backend - Optimize History Loading Performance (AC: 1)
  - [ ] Implement pagination for very long conversations (50+ messages)
  - [ ] Load last 50 messages by default, "Load more" button for older
  - [ ] Use checkpoint metadata for efficient query (don't load all steps)
  - [ ] Cache re-engagement summary to avoid LLM call on every return
  - [ ] Test performance with 100+ message history (2+ test cases)

- [ ] Task 10: Testing & Validation (All ACs)
  - [ ] Backend tests (10+ cases): thread_id isolation, history loading, re-engagement generation, checkpoint persistence
  - [ ] Frontend tests (8+ cases): history fetching, Thread initialization, scroll behavior, loading states, empty vs returning
  - [ ] E2E flow test: Learner chats → leaves module → returns → history loads → re-engagement message → continues conversation
  - [ ] E2E isolation test: Two learners in same module see different histories
  - [ ] Update sprint-status.yaml: 4-8-persistent-chat-history status = "in-progress"

## Dev Notes

### 🎯 Story Overview

This is the **eighth and final story in Epic 4: Learner AI Chat Experience**. It implements persistent chat history so learners can return to modules without losing conversational context. The AI greets returning learners with a contextual re-engagement message referencing their previous discussion.

**Key Deliverables:**
- Thread isolation per user per notebook via `user:{user_id}:notebook:{notebook_id}` pattern
- Chat history loading from LangGraph SqliteSaver checkpoints
- Re-engagement message generation with conversation summary
- Frontend history initialization in assistant-ui Thread component
- Smooth auto-scroll to bottom on history load

**Critical Context:**
- **FR31** (Learners can resume previous conversation)
- Completes Epic 4: Full learner AI chat experience with all features
- Builds on Story 4.1 (SSE streaming, thread_id foundation)
- Builds on Story 4.2 (two-layer prompt system, greeting generation)
- Uses existing SqliteSaver checkpoint storage (no new database schema)
- This makes the learning experience continuous across sessions

### 🏗️ Architecture Patterns (MANDATORY)

**Thread ID Pattern & Isolation:**
```
Thread ID Format: user:{user_id}:notebook:{notebook_id}

Example: user:user:alice:notebook:ai-fundamentals

Why this pattern?
  ├─ User isolation: Each learner has separate conversation history
  ├─ Notebook isolation: Same learner has different histories per module
  ├─ String format: Compatible with LangGraph thread_id string type
  └─ Deterministic: Same user + notebook = same thread_id (predictable)

Thread Lifecycle:
  1. Learner opens module page
  2. Frontend constructs thread_id from auth user + route param notebook_id
  3. Backend receives thread_id via chat request
  4. LangGraph loads checkpoint from SqliteSaver using thread_id
  5. If checkpoint exists → returning user flow
  6. If no checkpoint → new user flow

Checkpoint Storage (existing):
  ├─ Location: /data/sqlite-db/checkpoints.db
  ├─ LangGraph SqliteSaver: Built-in checkpoint persistence
  ├─ Storage: Full conversation history + graph state per thread
  ├─ Indexing: By thread_id (fast lookup)
  └─ No schema changes needed (already implemented in Story 4.1)
```

**History Loading Flow:**
```
Learner returns to module after days/weeks
  ↓
Frontend (ChatPanel.tsx) mounts:
  useEffect(() => {
    const thread_id = `user:${user.id}:notebook:${notebookId}`;
    fetchChatHistory(thread_id);
  }, [notebookId, user.id]);
  ↓
GET /learner-chat/{notebook_id}/history?user_id={user_id}
  ├─ Backend constructs thread_id: user:{user_id}:notebook:{notebook_id}
  ├─ Query SqliteSaver for checkpoint
  └─ If exists → extract messages, else → return empty array
  ↓
Backend (api/routers/learner_chat.py):
  @router.get("/{notebook_id}/history")
  async def get_chat_history(
      notebook_id: str,
      current_user: User = Depends(get_current_learner)
  ):
      thread_id = f"user:{current_user.id}:notebook:{notebook_id}"

      # Load checkpoint from SqliteSaver
      checkpointer = get_checkpointer()  # Returns SqliteSaver instance
      checkpoint = await checkpointer.aget(thread_id)

      if not checkpoint:
          return {"messages": []}  # New conversation

      # Extract messages from checkpoint state
      messages = checkpoint["messages"]  # AIMessage, HumanMessage, etc.

      # Transform to frontend format (assistant-ui compatible)
      formatted_messages = [
          {
              "id": msg.id or str(uuid.uuid4()),
              "role": "assistant" if isinstance(msg, AIMessage) else "user",
              "content": msg.content,
              "createdAt": msg.timestamp or datetime.now().isoformat(),
          }
          for msg in messages
      ]

      return {"messages": formatted_messages}
  ↓
Frontend receives history:
  {
    "messages": [
      {"id": "1", "role": "assistant", "content": "Hi Sophie! I see you're a project manager..."},
      {"id": "2", "role": "user", "content": "Tell me about AI for project management"},
      {"id": "3", "role": "assistant", "content": "Great question! AI can help with..."},
      ...
    ]
  }
  ↓
ChatPanel passes to assistant-ui Thread:
  <Thread
    thread={{
      id: threadId,
      initialMessages: historyMessages  ← Full conversation history
    }}
    onMessage={handleMessage}
  />
  ↓
assistant-ui renders all messages:
  ┌─────────────────────────────────────────┐
  │ AI: Hi Sophie! I see you're a project   │
  │     manager. Let's talk about AI for... │
  ├─────────────────────────────────────────┤
  │ You: Tell me about AI for project mgmt  │
  ├─────────────────────────────────────────┤
  │ AI: Great question! AI can help with... │
  │     [Full conversation history]         │
  └─────────────────────────────────────────┘
  ↓
Auto-scroll to bottom (smooth 150ms ease transition):
  chatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  ↓
AI sends re-engagement message (streaming):
  "Welcome back, Sophie! Last time we were discussing AI applications
   in project management, specifically around status reports. Ready
   to continue? What else would you like to explore?"
  ↓
Learner: "Can we talk about meeting notes?"
  ↓
Conversation continues with full context (learning objectives progress preserved)
```

**Re-engagement Message Generation:**
```
Backend detects returning user:
  ├─ Check if checkpoint exists for thread_id
  ├─ Check if current request has no new user message yet (initial load)
  └─ If both true → generate re-engagement greeting
  ↓
open_notebook/graphs/prompt.py:
  async def generate_re_engagement_greeting(
      thread_id: str,
      learner_profile: dict,
      learning_objectives: List[LearningObjective]
  ) -> str:
      """Generate contextual welcome-back message"""

      # Load last 3-5 messages from checkpoint
      checkpointer = get_checkpointer()
      checkpoint = await checkpointer.aget(thread_id)
      recent_messages = checkpoint["messages"][-5:]

      # Extract conversation topics (use fast LLM)
      conversation_summary = await analyze_conversation_topics(recent_messages)
      # Example: "discussing AI for status reports and meeting summaries"

      # Find progress on learning objectives
      completed_objectives = [obj for obj in learning_objectives if obj.status == "completed"]
      remaining_objectives = [obj for obj in learning_objectives if obj.status != "completed"]

      # Generate re-engagement prompt
      prompt = f"""
      Generate a warm, personalized welcome-back message for {learner_profile['name']}.

      Previous conversation context:
      - Last discussed: {conversation_summary}
      - Learning objectives completed: {len(completed_objectives)}/{len(learning_objectives)}
      - Topics remaining: {[obj.text for obj in remaining_objectives[:3]]}

      Guidelines:
      - Reference specific topic from last time
      - Acknowledge progress made
      - Invite them to continue or shift focus
      - Keep under 3 sentences, conversational tone

      Example: "Welcome back! Last time we were discussing AI for status reports,
      and you had great insights on automation. Ready to continue, or would you like
      to explore a different application?"
      """

      # Use small fast model (cost optimization)
      model = provision_langchain_model(
          model_name="gpt-4o-mini",  # Fast, cheap for greetings
          temperature=0.7
      )

      greeting = await model.ainvoke(prompt)
      return greeting.content
  ↓
Greeting returned to chat graph:
  ├─ Injected as first AI message in new turn
  ├─ Streamed via SSE to frontend
  └─ Learner sees contextual welcome (not generic)
  ↓
Example greetings:
  ├─ "Welcome back! Last time we were discussing AI applications in
  │   logistics. You had just learned about predictive analytics.
  │   Ready to dive deeper?"
  │
  ├─ "Hi again, Sophie! We were talking about AI for meeting notes
  │   last time. You seemed interested in action item extraction.
  │   Want to continue there or explore something new?"
  │
  └─ "Great to see you back! Last session we covered 5 of 12 learning
      objectives, focusing on natural language processing. Let's pick up
      where we left off!"
```

**Critical Rules:**
- **Thread ID Must Be Deterministic**: Same user + notebook = same thread_id (no random UUIDs)
- **History Loads Before First Message**: Fetch history on mount, not after user sends message
- **Auto-Scroll After History Renders**: Scroll to bottom after messages render AND after re-engagement streams
- **Preserve Manual Scroll**: If user scrolled up, don't force them to bottom
- **Re-engagement Only on Return**: Don't show "Welcome back" on first visit (empty history)
- **Learning Objectives Carry Over**: Progress from previous session must be visible
- **Company Scoping**: User can only load their own history (security via get_current_learner)
- **Performance**: Paginate very long histories (50+ messages load latest, "Load more" for older)

### 📋 Technical Requirements

**Backend Stack:**
- Existing LangGraph SqliteSaver from Story 4.1 (checkpoint storage)
- Existing thread_id pattern (already used in chat graph)
- Existing get_current_learner() dependency (user extraction)
- NEW: /learner-chat/{notebook_id}/history endpoint (api/routers/learner_chat.py)
- NEW: generate_re_engagement_greeting() function (open_notebook/graphs/prompt.py)
- MODIFY: open_notebook/graphs/chat.py - detect returning user, trigger re-engagement

**Frontend Stack:**
- Existing assistant-ui Thread component from Story 4.1
- Existing ChatPanel.tsx with SSE streaming
- NEW: useChatHistory hook (lib/hooks/use-learner-chat.ts extension)
- MODIFY: ChatPanel.tsx - fetch history on mount, pass to Thread initialMessages
- i18next for translations (en-US + fr-FR)

**History Response Model:**
```typescript
interface ChatHistoryResponse {
  messages: Array<{
    id: string
    role: "assistant" | "user"
    content: string | Array<MessagePart>  // Support rich content
    createdAt: string  // ISO 8601 timestamp
  }>
  thread_id: string
  has_more?: boolean  // For pagination
}
```

**Message Transformation (Backend):**
```python
# LangGraph checkpoint message types
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Transform to frontend format
def format_message_for_frontend(msg: BaseMessage) -> dict:
    """Convert LangGraph message to assistant-ui format"""
    return {
        "id": msg.id or str(uuid.uuid4()),
        "role": "assistant" if isinstance(msg, AIMessage) else "user",
        "content": msg.content,
        "createdAt": msg.additional_kwargs.get("timestamp", datetime.now().isoformat()),
        # Include tool calls if present (for Story 4.6 inline artifacts)
        "tool_calls": msg.tool_calls if isinstance(msg, AIMessage) and msg.tool_calls else None
    }
```

**assistant-ui Thread Initialization:**
```typescript
// ChatPanel.tsx
const { data: history, isLoading } = useChatHistory(notebookId);

<Thread
  thread={{
    id: threadId,
    initialMessages: history?.messages || []  // Load history
  }}
  onMessage={handleNewMessage}
  // Auto-scroll handled by assistant-ui built-in behavior
/>
```

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `api/routers/learner_chat.py` - ADD get_chat_history() endpoint (40 lines added)
- `open_notebook/graphs/prompt.py` - ADD generate_re_engagement_greeting() (80 lines)

**Backend Files to Modify:**

**MODIFY:**
- `open_notebook/graphs/chat.py` - DETECT returning user, trigger re-engagement (30 lines added)
- `prompts/global_teacher_prompt.j2` - ADD Re-engagement context section (20 lines)

**Frontend Files to Modify:**

**MODIFY:**
- `frontend/src/components/learner/ChatPanel.tsx` - Fetch history, pass to Thread (50 lines added)
- `frontend/src/lib/hooks/use-learner-chat.ts` - ADD useChatHistory hook (40 lines added)
- `frontend/src/lib/api/learner-chat.ts` - ADD getChatHistory API call (15 lines)
- `frontend/src/lib/locales/en-US/index.ts` - ADD 3 i18n keys
- `frontend/src/lib/locales/fr-FR/index.ts` - ADD 3 French translations

**Directory Structure:**
```
open_notebook/
├── graphs/
│   ├── chat.py                           # MODIFY - detect returning user
│   └── prompt.py                         # ADD - generate_re_engagement_greeting
│
prompts/
└── global_teacher_prompt.j2              # MODIFY - re-engagement guidance

api/
└── routers/
    └── learner_chat.py                   # ADD - get_chat_history endpoint

frontend/src/
├── components/learner/
│   └── ChatPanel.tsx                     # MODIFY - fetch history, initialize Thread
├── lib/
│   ├── api/
│   │   └── learner-chat.ts               # ADD - getChatHistory API call
│   ├── hooks/
│   │   └── use-learner-chat.ts           # ADD - useChatHistory hook
│   └── locales/
│       ├── en-US/index.ts                # MODIFY - add keys
│       └── fr-FR/index.ts                # MODIFY - add translations

tests/
├── test_chat_history.py                  # NEW - Backend tests
└── (frontend tests in component __tests__/)
```

### 🧪 Testing Requirements

**Backend Tests (pytest) - 12+ test cases:**

**Thread ID Isolation Tests (4 tests):**
```python
# tests/test_chat_history.py

class TestThreadIsolation:
    async def test_thread_id_format():
        """Test thread_id constructed correctly"""
        user_id = "user:alice"
        notebook_id = "notebook:ai-fundamentals"
        thread_id = construct_thread_id(user_id, notebook_id)
        assert thread_id == "user:user:alice:notebook:ai-fundamentals"
        ...

    async def test_user_isolation():
        """Test different users have different histories for same notebook"""
        # Alice chats in notebook
        # Bob chats in same notebook
        # Assert Alice can't see Bob's history
        ...

    async def test_notebook_isolation():
        """Test same user has different histories per notebook"""
        # Alice chats in notebook A
        # Alice chats in notebook B
        # Assert histories are separate
        ...

    async def test_checkpoint_persistence():
        """Test conversation persists across graph restarts"""
        # Send message, save checkpoint
        # Restart graph, load checkpoint
        # Assert message history preserved
        ...
```

**History Loading Tests (3 tests):**
```python
class TestHistoryLoading:
    async def test_load_existing_history():
        """Test GET /learner-chat/{notebook_id}/history returns messages"""
        response = await client.get(f"/learner-chat/{notebook_id}/history")
        assert response.status_code == 200
        assert len(response.json()["messages"]) > 0
        ...

    async def test_empty_history_new_user():
        """Test empty history returns empty array for new conversation"""
        response = await client.get(f"/learner-chat/{notebook_id}/history")
        assert response.json()["messages"] == []
        ...

    async def test_message_format_transformation():
        """Test LangGraph messages transformed to frontend format"""
        # Create AIMessage and HumanMessage
        # Load history
        # Assert correct role, content, timestamp
        ...
```

**Re-engagement Generation Tests (3 tests):**
```python
class TestReengagementGeneration:
    async def test_re_engagement_greeting():
        """Test contextual greeting generated from conversation history"""
        greeting = await generate_re_engagement_greeting(
            thread_id="user:alice:notebook:test",
            learner_profile={"name": "Alice"},
            learning_objectives=[...]
        )
        assert "Welcome back" in greeting or "Hi again" in greeting
        assert len(greeting) < 500  # Keep it concise
        ...

    async def test_conversation_summary_extraction():
        """Test topic extraction from recent messages"""
        messages = [
            HumanMessage(content="Tell me about AI for project management"),
            AIMessage(content="AI can help with status reports..."),
        ]
        summary = await analyze_conversation_topics(messages)
        assert "project management" in summary or "status reports" in summary
        ...

    async def test_re_engagement_without_history():
        """Test standard greeting if history empty"""
        # Empty checkpoint
        # Assert standard greeting used (from Story 4.2)
        ...
```

**Chat Graph Integration Tests (2 tests):**
```python
class TestChatGraphReengagement:
    async def test_detect_returning_user():
        """Test graph detects returning user from checkpoint existence"""
        # Create checkpoint with messages
        # Invoke graph with same thread_id
        # Assert re-engagement triggered
        ...

    async def test_re_engagement_message_sent():
        """Test AI sends re-engagement as first message on return"""
        # Returning user opens module
        # Assert first message is re-engagement (not standard greeting)
        ...
```

**Frontend Tests (Vitest/React Testing Library) - 10+ test cases:**

**History Fetching Tests (3 tests):**
```typescript
// lib/hooks/__tests__/use-learner-chat.test.ts

describe('useChatHistory', () => {
  it('fetches chat history on mount', async () => {
    const { result } = renderHook(() => useChatHistory('notebook:test'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.messages).toBeDefined();
  });

  it('returns empty array for new conversation', async () => {
    server.use(
      rest.get('/learner-chat/:notebookId/history', (req, res, ctx) => {
        return res(ctx.json({ messages: [] }));
      })
    );
    const { result } = renderHook(() => useChatHistory('notebook:new'));
    await waitFor(() => expect(result.current.data?.messages).toEqual([]));
  });

  it('handles fetch error gracefully', async () => {
    server.use(
      rest.get('/learner-chat/:notebookId/history', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );
    const { result } = renderHook(() => useChatHistory('notebook:test'));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
```

**ChatPanel Integration Tests (4 tests):**
```typescript
// components/learner/__tests__/ChatPanel.test.tsx (extend)

describe('ChatPanel - Chat History', () => {
  it('loads and displays chat history on mount', async () => {
    const history = [
      { id: '1', role: 'assistant', content: 'Hello!', createdAt: '2026-01-01T10:00:00Z' },
      { id: '2', role: 'user', content: 'Hi there', createdAt: '2026-01-01T10:01:00Z' },
    ];
    server.use(
      rest.get('/learner-chat/:notebookId/history', (req, res, ctx) => {
        return res(ctx.json({ messages: history }));
      })
    );

    render(<ChatPanel notebookId="notebook:test" />);

    await waitFor(() => {
      expect(screen.getByText('Hello!')).toBeInTheDocument();
      expect(screen.getByText('Hi there')).toBeInTheDocument();
    });
  });

  it('shows loading skeleton while fetching history', () => {
    render(<ChatPanel notebookId="notebook:test" />);
    expect(screen.getByTestId('history-loading-skeleton')).toBeInTheDocument();
  });

  it('auto-scrolls to bottom after history loads', async () => {
    const scrollIntoViewMock = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock;

    render(<ChatPanel notebookId="notebook:test" />);
    await waitFor(() => expect(scrollIntoViewMock).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'end'
    }));
  });

  it('shows empty state for new conversation', async () => {
    server.use(
      rest.get('/learner-chat/:notebookId/history', (req, res, ctx) => {
        return res(ctx.json({ messages: [] }));
      })
    );

    render(<ChatPanel notebookId="notebook:test" />);
    await waitFor(() => {
      expect(screen.getByText(/start conversation/i)).toBeInTheDocument();
    });
  });
});
```

**Scroll Behavior Tests (3 tests):**
```typescript
describe('ChatPanel - Scroll Behavior', () => {
  it('scrolls to bottom with smooth animation', async () => {
    const scrollIntoViewMock = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock;

    render(<ChatPanel notebookId="notebook:test" />);
    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalledWith(
        expect.objectContaining({ behavior: 'smooth' })
      );
    });
  });

  it('does not force scroll if user manually scrolled up', async () => {
    // User scrolls up
    // New message arrives
    // Assert scroll position not changed
    ...
  });

  it('shows scroll-to-bottom button when scrolled away from end', async () => {
    // Scroll up
    // Assert button appears
    // Click button
    // Assert scrolled to bottom
    ...
  });
});
```

**Integration Tests (E2E flow):**
```typescript
// E2E test (optional for Story 4.8, recommended)

describe('Persistent Chat History Flow', () => {
  it('loads previous conversation on return visit', async () => {
    // 1. First session: Learner chats with AI
    // 2. Send 5 messages back and forth
    // 3. Leave module (unmount ChatPanel)
    // 4. Return to module (remount ChatPanel)
    // 5. History loads with all 5 messages
    // 6. AI sends re-engagement: "Welcome back..."
    // 7. Learner continues conversation
    // 8. New messages append to history
  });

  it('isolates history per user per notebook', async () => {
    // 1. Alice chats in Notebook A
    // 2. Bob chats in Notebook A (different thread_id)
    // 3. Alice returns to Notebook A
    // 4. Assert Alice sees only her history (not Bob's)
  });

  it('handles empty history for first visit', async () => {
    // 1. New learner opens module for first time
    // 2. No history loaded (empty array)
    // 3. AI sends standard greeting (not re-engagement)
    // 4. Learner sends first message
    // 5. Conversation starts fresh
  });
});
```

**Test Coverage Targets:**
- Backend: 85%+ for history loading + re-engagement generation
- Frontend: 85%+ for ChatPanel history integration

### 🚫 Anti-Patterns to Avoid (from Memory + Research)

**From Memory (CRITICAL):**

1. **Random Thread IDs**
   - ❌ Generate new thread_id with UUID on each session
   - ✅ Use deterministic pattern: `user:{user_id}:notebook:{notebook_id}`

2. **Loading History After First Message**
   - ❌ Fetch history only after user sends first message
   - ✅ Fetch on mount, before any interaction (immediate context)

3. **Missing Company Scoping**
   - ❌ User can load any conversation history via thread_id manipulation
   - ✅ Endpoint uses get_current_learner(), filters by authenticated user

4. **Blocking UI While Loading**
   - ❌ Show blank screen until history loads (slow perceived performance)
   - ✅ Show loading skeleton, progressive rendering

5. **Force Scroll on Manual Scroll**
   - ❌ Auto-scroll to bottom even if user scrolled up to read history
   - ✅ Detect manual scroll, preserve position, show scroll-to-bottom button

6. **Missing i18n Translations**
   - ❌ Hardcode "Welcome back..." in re-engagement prompt
   - ✅ Both en-US and fr-FR for ALL UI strings and AI prompt templates

**From Infrastructure Research:**

7. **Not Handling Empty Checkpoint**
   - ❌ Assume checkpoint always exists, crash on new conversation
   - ✅ Check if checkpoint is None, return empty history gracefully

8. **Inefficient Checkpoint Loading**
   - ❌ Load full checkpoint state (includes graph metadata)
   - ✅ Extract only messages array from checkpoint (efficient)

9. **Re-engagement on Every Message**
   - ❌ Generate re-engagement greeting for every chat turn
   - ✅ Only on initial load when returning (detect empty current turn)

10. **Message Ordering Wrong**
    - ❌ Show newest messages first (reverse chronological)
    - ✅ Oldest messages first (chronological order, natural conversation flow)

**From Story 4.1 (SSE Streaming):**

11. **Message Format Mismatch**
    - ❌ Return LangGraph message format directly to frontend
    - ✅ Transform to assistant-ui format: {id, role, content, createdAt}

12. **Thread ID Mismatch Backend/Frontend**
    - ❌ Frontend uses different thread_id than backend
    - ✅ Frontend constructs same pattern as backend expects

**New to Story 4.8:**

13. **Uncontrolled History Length**
    - ❌ Load 1000+ messages on every return (performance degradation)
    - ✅ Paginate: load last 50, "Load more" button for older

14. **Re-engagement Without Context**
    - ❌ Generic "Welcome back!" every time (no personalization)
    - ✅ Analyze last conversation, reference specific topic discussed

15. **Scroll Before Render Complete**
    - ❌ Scroll before messages finish rendering (scroll position wrong)
    - ✅ Wait for history render, then scroll (useEffect with dependency)

### 🔗 Integration with Existing Code

**Builds on Story 4.1 (Learner Chat Interface & SSE Streaming):**
- Thread ID pattern already used: thread_id passed to LangGraph
- SqliteSaver checkpoint storage already configured (checkpoints.db)
- SSE streaming endpoint exists: api/routers/learner_chat.py
- assistant-ui Thread component supports initialMessages prop
- Story 4.8 EXTENDS with history loading and re-engagement

**Builds on Story 4.2 (Two-Layer Prompt System & Proactive AI Teacher):**
- Greeting generation already exists for first-time users
- Learner profile injection in prompts (name, role, job description)
- Prompt assembly function (global + per-module + context)
- Story 4.8 EXTENDS with re-engagement greeting variant

**Builds on Story 4.4 (Learning Objectives Progress Tracking):**
- Learning objectives progress stored in database (LearnerObjectiveProgress)
- Progress carried in graph state across turns
- Re-engagement message can reference completed objectives
- Story 4.8 ENSURES progress visible on return

**Builds on Existing LangGraph Checkpoint System:**
- SqliteSaver initialized in open_notebook/graphs/chat.py
- Checkpoints saved automatically after each graph turn
- Thread ID used as checkpoint key (thread_id → checkpoint lookup)
- No schema changes needed (already stores messages + graph state)

**Integration Points:**

**Backend:**
- `api/routers/learner_chat.py` - ADD get_chat_history() endpoint (new route)
- `open_notebook/graphs/prompt.py` - ADD generate_re_engagement_greeting() function
- `open_notebook/graphs/chat.py` - DETECT returning user, inject re-engagement
- `prompts/global_teacher_prompt.j2` - ADD re-engagement context instructions

**Frontend:**
- `ChatPanel.tsx` - FETCH history on mount, pass to Thread initialMessages
- `use-learner-chat.ts` - ADD useChatHistory hook (TanStack Query)
- `learner-chat.ts` - ADD getChatHistory API call

**No Breaking Changes:**
- All changes additive (new endpoint, new function)
- Existing chat functionality unchanged
- New users see standard greeting (backward compatible)
- Returning users get enhanced experience (re-engagement)

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Chat Thread Isolation] - Thread ID pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Checkpoint Storage] - SqliteSaver

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.8] - Lines 844-864
- [Source: _bmad-output/planning-artifacts/epics.md#FR31] - Persistent chat history
- [Source: _bmad-output/planning-artifacts/prd.md#Journey 2] - Sophie returns to module

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/4-1-learner-chat-interface-and-sse-streaming.md] - Thread ID, SqliteSaver setup
- [Source: _bmad-output/implementation-artifacts/4-2-two-layer-prompt-system-and-proactive-ai-teacher.md] - Greeting generation
- [Source: _bmad-output/implementation-artifacts/4-4-learning-objectives-assessment-and-progress-tracking.md] - Objectives progress

**Existing Code:**
- [Source: open_notebook/graphs/chat.py] - LangGraph chat workflow with SqliteSaver
- [Source: api/routers/learner_chat.py] - Existing SSE streaming endpoint
- [Source: frontend/src/components/learner/ChatPanel.tsx] - assistant-ui Thread integration

### 🧠 Implementation Strategy & Decision Log

**Key Technical Decisions:**

1. **Deterministic Thread ID Pattern**
   - Decision: `user:{user_id}:notebook:{notebook_id}` format
   - Rationale: Same user + notebook = same conversation (predictable, simple)
   - Alternative rejected: UUID per session (loses history persistence)

2. **SqliteSaver Checkpoint Reuse**
   - Decision: Use existing LangGraph SqliteSaver (no new database)
   - Rationale: Already implemented in Story 4.1, proven reliable
   - No schema changes needed (messages already stored)

3. **History Endpoint vs Direct Checkpoint Access**
   - Decision: Dedicated GET /learner-chat/{notebook_id}/history endpoint
   - Rationale: Clean separation, company scoping, message transformation
   - Alternative rejected: Frontend directly queries SqliteSaver (security issue)

4. **Re-engagement via LLM Analysis**
   - Decision: Use fast LLM (gpt-4o-mini) to analyze recent conversation
   - Rationale: Contextual greetings feel personal, improves engagement
   - Cost: ~$0.001 per return visit (acceptable for UX benefit)

5. **Auto-Scroll with Manual Override**
   - Decision: Auto-scroll on load, but detect manual scroll and preserve
   - Rationale: Users reading history shouldn't be forced to bottom
   - UX pattern: Add scroll-to-bottom button when user scrolls away

6. **Pagination for Long Histories**
   - Decision: Load last 50 messages, "Load more" button for older
   - Rationale: Performance optimization for power users (100+ messages)
   - Implementation: offset/limit on checkpoint message array

7. **assistant-ui initialMessages**
   - Decision: Pass history via Thread initialMessages prop
   - Rationale: Built-in assistant-ui feature, handles rendering automatically
   - No custom message list management needed

8. **Re-engagement Only on Return**
   - Decision: Check if checkpoint exists AND current turn is empty
   - Rationale: Prevents re-engagement on every message (only initial load)
   - Implementation: Boolean flag in graph state: is_returning_user

9. **Message Format Transformation**
   - Decision: Backend transforms LangGraph → assistant-ui format
   - Rationale: Frontend shouldn't know LangGraph internals
   - Consistent with API layering pattern (backend abstracts implementation)

10. **Learning Objectives in Re-engagement**
    - Decision: Reference progress in greeting ("You've completed 5 of 12 objectives")
    - Rationale: Shows continuity, motivates learner
    - Implementation: Inject objectives status in re-engagement prompt

**Prompt Engineering Approach:**

Re-engagement greeting via:
1. **Topic extraction**: Analyze last 3-5 messages for discussed concepts
2. **Progress summary**: Count completed vs remaining learning objectives
3. **Contextual template**: "Welcome back. Last time we were discussing [topic]..."
4. **Personalization**: Use learner name and role from profile
5. **Invitation**: Invite to continue or shift focus

**assistant-ui Integration:**

- No changes to assistant-ui library usage
- Use built-in initialMessages prop (designed for history loading)
- Auto-scroll handled by assistant-ui (with manual override in ChatPanel)
- Message format already compatible (role, content, id)

**Migration Numbering:**

No new migrations for Story 4.8 (uses existing SqliteSaver checkpoints).

### Project Structure Notes

**Alignment with Project:**
- Uses existing checkpoint storage (SqliteSaver from Story 4.1)
- Extends existing greeting system (Story 4.2)
- Preserves learning objectives progress (Story 4.4)
- No new database schema
- Completes Epic 4: Full learner chat experience

**No Breaking Changes:**
- All changes additive (new endpoint, new function)
- Existing chat works identically for new users
- Returning users get enhanced experience (re-engagement)
- Backward compatible with all previous stories

**Potential Conflicts:**
- **Story 7.2 (Structured Error Logging)**: Rolling context buffer may interact with history loading
  - Resolution: History loads from checkpoint, context buffer is per-turn (separate concerns)
- **Story 7.8 (Learner Transparency)**: Details view may need to show historical tool calls
  - Resolution: Story 4.8 loads messages, 7.8 adds tool call metadata display (complementary)

**Design Decisions:**
- Deterministic thread ID for persistence
- Re-engagement via LLM analysis for personalization
- Pagination for performance
- Auto-scroll with manual override for UX
- Company scoping for security

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (via workflow.xml execution)

### Debug Log References

(To be filled by dev agent)

### Completion Notes List

**Tasks 1-5 Completed (50% complete):**
- ✅ Task 1: Thread ID pattern verified + checkpoint storage verified + 14 tests passing
- ✅ Task 2: Re-engagement greeting generator implemented + 3 tests passing
- ✅ Task 3: Chat graph modified to detect returning users + call re-engagement generator
- ✅ Task 4: Global teacher prompt extended with re-engagement guidance section
- ✅ Task 5: Backend history endpoint + frontend API/hook (getChatHistory + useChatHistory)

**Remaining (Tasks 6-10):**
- Task 6: ChatPanel.tsx modifications (load history, pass to Thread initialMessages)
- Task 7: Smooth scroll to end behavior (auto-scroll after history loads, preserve manual scroll)
- Task 8: i18n keys for empty history vs returning user (en-US + fr-FR)
- Task 9: Backend pagination optimization (load last 50 messages, "Load more" button)
- Task 10: E2E testing and validation (full flow test, isolation test)

**Story 4.8 created with comprehensive context:**
- All 3 acceptance criteria mapped to 10 tasks with detailed subtasks
- Architecture patterns defined: thread ID isolation, history loading, re-engagement generation
- Integration with Stories 4.1, 4.2, 4.4 documented
- 22+ test cases specified (12 backend + 10 frontend)
- Anti-patterns from memory + infrastructure research included
- File structure complete with all modifications marked (NEW/MODIFY)
- References to architecture, epics, PRD, and previous stories cited
- Implementation strategy with 10 key technical decisions documented

### File List

**Backend Files to Create:**
- None (all modifications to existing files)

**Backend Files to Modify:**
- `api/routers/learner_chat.py` - ADD get_chat_history() endpoint (40 lines added)
- `open_notebook/graphs/prompt.py` - ADD generate_re_engagement_greeting() (80 lines)
- `open_notebook/graphs/chat.py` - DETECT returning user, trigger re-engagement (30 lines added)
- `prompts/global_teacher_prompt.j2` - ADD Re-engagement context section (20 lines)

**Frontend Files to Modify:**
- `frontend/src/components/learner/ChatPanel.tsx` - Fetch history, pass to Thread (50 lines added)
- `frontend/src/lib/hooks/use-learner-chat.ts` - ADD useChatHistory hook (40 lines added)
- `frontend/src/lib/api/learner-chat.ts` - ADD getChatHistory API call (15 lines)
- `frontend/src/lib/locales/en-US/index.ts` - ADD 3 i18n keys
- `frontend/src/lib/locales/fr-FR/index.ts` - ADD 3 French translations

**Test Files to Create:**
- `tests/test_chat_history.py` - Backend history loading + re-engagement tests (200+ lines)
- `frontend/src/lib/hooks/__tests__/use-learner-chat.test.ts` - useChatHistory hook tests (80+ lines)
- `frontend/src/components/learner/__tests__/ChatPanel.test.tsx` - EXTEND with history tests (100+ lines added)

