# Story 4.6: AI Surfaces Artifacts in Conversation

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **learner**,
I want the AI teacher to suggest and surface artifacts (quizzes, podcasts, summaries) during conversation,
so that I can engage with varied learning materials in context.

## Acceptance Criteria

**Criterion 1: Quiz Surfacing**
- **Given** the AI determines a quiz would help validate understanding
- **When** it triggers quiz surfacing
- **Then** an InlineQuizWidget renders in the chat with question, options, and submit button

**Criterion 2: Correct Answer Response**
- **Given** the learner submits a quiz answer
- **When** the answer is correct
- **Then** the correct option is highlighted in success color with an explanation

**Criterion 3: Incorrect Answer Response**
- **Given** the learner submits a quiz answer
- **When** the answer is incorrect
- **Then** the selected option shows amber, the correct option is revealed, and an explanation is shown

**Criterion 4: Podcast Surfacing**
- **Given** the AI references a podcast
- **When** the podcast is surfaced
- **Then** an InlineAudioPlayer renders in chat with play/pause, progress bar, and speed control

## Tasks / Subtasks

- [x] Task 1: Backend - Artifact Surfacing Tools in LangGraph (AC: 1, 4)
  - [x] Create `surface_quiz` async tool in open_notebook/graphs/tools.py
  - [x] Tool parameters: quiz_id (required)
  - [x] Tool execution: Fetch quiz with questions from domain, validate exists and belongs to learner's company
  - [x] Return structured data: {artifact_type: "quiz", quiz_id, title, questions: [{text, options}], quiz_url}
  - [x] Create `surface_podcast` async tool in open_notebook/graphs/tools.py
  - [x] Tool parameters: podcast_id (required)
  - [x] Tool execution: Fetch podcast from domain, validate exists and is ready (status="completed")
  - [x] Return structured data: {artifact_type: "podcast", podcast_id, title, audio_url, duration_minutes, transcript_url}
  - [x] Bind both tools to model in graphs/chat.py (follow surface_document pattern from Story 4.3)
  - [x] Test tool invocation with 7 test cases (valid quiz, valid podcast, invalid IDs, company scoping, not ready podcast)

- [x] Task 2: Backend - Extend Chat Graph for Artifact Availability (AC: 1, 4)
  - [x] Modify graphs/prompt.py: inject available artifacts into prompt context
  - [x] Load all artifacts for current notebook (quizzes + podcasts)
  - [x] Filter by notebook_id (company scoping enforced at API layer)
  - [x] Add artifacts list to prompt assembly: "Available learning materials: Quiz 'X' (ID: quiz:123), Podcast 'Y' (ID: podcast:456)"
  - [x] Update prompts/global_teacher_prompt.j2: Add section "Artifact Surfacing Guidance"
  - [x] Instruct AI when to surface quizzes (validate understanding, reinforce concepts)
  - [x] Instruct AI when to surface podcasts (introduce topic, provide different medium)
  - [x] Implemented _load_available_artifacts function with quiz count and podcast details

- [x] Task 3: Frontend - InlineQuizWidget Component (AC: 1, 2, 3)
  - [x] Create InlineQuizWidget.tsx in components/learner/
  - [x] Props: {quizId, title, questions: [{text, options}], quizUrl}
  - [x] Display: Card with question text, radio button options, "Submit Answer" button
  - [x] State: Track selected option index
  - [x] Submit handler: Call quiz API /api/quizzes/{quizId}/score with answer
  - [x] Render feedback after submit:
    - Correct: Green background, checkmark icon, explanation text
    - Incorrect: Amber background, X icon on selection, green highlight on correct option, explanation text
  - [x] "View Full Quiz" link to quiz_url
  - [x] Add i18n keys (en-US + fr-FR): submitAnswer, submitting, viewFullQuiz, question/questions, noQuestions, submissionError
  - [x] Component implemented with full state management and feedback display

- [x] Task 4: Frontend - InlineAudioPlayer Component (AC: 4)
  - [x] Create InlineAudioPlayer.tsx in components/learner/
  - [x] Props: {podcastId, title, audioUrl, durationMinutes, transcriptUrl, status}
  - [x] Use HTML5 <audio> element with controls
  - [x] Display: Card with title, play/pause button (Play/Pause icons from lucide-react), progress bar, speed control (1x/1.25x/1.5x/2x buttons)
  - [x] Progress bar: Track currentTime and duration, visualize with Radix Progress primitive
  - [x] Speed control: Buttons to set audio.playbackRate (1, 1.25, 1.5, 2)
  - [x] Show loading state if status !== "completed"
  - [x] "View Transcript" link to transcript_url
  - [x] Add i18n keys (en-US + fr-FR): play, pause, speed, minutes, viewTranscript, generating
  - [x] Component implemented with full audio playback state management

- [x] Task 5: Frontend - Integrate Custom Message Parts with assistant-ui (AC: 1, 4)
  - [x] Extend ChatPanel.tsx: Register InlineQuizWidget and InlineAudioPlayer as custom message parts
  - [x] Map tool call results to components:
    - "surface_quiz" → InlineQuizWidget
    - "surface_podcast" → InlineAudioPlayer
  - [x] Integrated into existing tool call rendering section alongside DocumentSnippetCard
  - [x] Custom message parts render inline in chat when AI invokes surface tools

- [x] Task 6: Backend - API Endpoints for Artifact Data (AC: 1, 4)
  - [x] Extended GET /quizzes/{quiz_id} in api/routers/quizzes.py
  - [x] Added learner access control with company scoping validation
  - [x] Company scoping: Validate quiz.notebook_id belongs to learner's company via module_assignment
  - [x] Quiz questions returned WITHOUT correct_answer for security (unless quiz completed)
  - [x] Extended POST /quizzes/{quiz_id}/check with company scoping
  - [x] Added GET /podcasts/{podcast_id} for Podcast model artifacts
  - [x] Added GET /podcasts/{podcast_id}/audio with company scoping
  - [x] Added GET /podcasts/{podcast_id}/transcript with company scoping
  - [x] All endpoints validate learner access via module_assignment table

- [x] Task 7: Testing & Validation (All ACs)
  - [x] Backend tests (7 cases): surface_quiz tool (3), surface_podcast tool (4) - ALL PASSING
  - [x] Frontend tests (42 cases): InlineQuizWidget (17 tests), InlineAudioPlayer (25 tests) - ALL PASSING
  - [x] Unit tests cover: rendering, user interactions, API calls, state management, error handling
  - [x] Integration verified through component tests (quiz submission flow, audio playback flow)
  - [x] Update sprint-status.yaml: 4-6-ai-surfaces-artifacts-in-conversation status = "complete"

## Dev Notes

### 🎯 Story Overview

This is the **sixth story in Epic 4: Learner AI Chat Experience**. It extends the inline rendering pattern from Story 4.3 (document snippets) to include interactive learning artifacts—quizzes and podcasts—directly in the chat conversation.

**Key Deliverables:**
- Two new LangGraph tools: `surface_quiz` and `surface_podcast`
- InlineQuizWidget component with interactive quiz submission
- InlineAudioPlayer component with playback controls
- Artifact availability injected into AI prompt context
- Enhanced global teacher prompt with artifact surfacing guidance
- Company-scoped artifact endpoints for learner access

**Critical Context:**
- **FR23** (AI surfaces artifacts in conversation)
- Builds on Story 4.3 (inline document snippets - establishes custom message part pattern)
- Builds on Story 4.2 (two-layer prompt system - extend with artifact context)
- Builds on Story 3.2 (artifact generation - quizzes and podcasts already exist)
- Sets foundation for Story 4.7 (async task handling - podcast generation status)
- This transforms AI from text-only teacher to multi-modal learning guide

### 🏗️ Architecture Patterns (MANDATORY)

**Quiz Surfacing Flow:**
```
AI conversation with learner reaches comprehension check point
  ↓
AI analyzes: "Learner has covered supervised learning concepts"
  ↓
Prompt context includes: "Available learning materials: Quiz 'Supervised Learning Quiz' (ID: quiz:abc123)"
  ↓
AI decides to surface quiz for validation
  ↓
LangGraph chat.py: AI invokes surface_quiz tool
  ↓ Tool call parameters: {
      quiz_id: "quiz:abc123"
    }
  ↓
graphs/tools.py: surface_quiz() async function executes
  ↓ Load Quiz by ID from domain
  ↓ Validate quiz exists
  ↓ Validate quiz.notebook_id belongs to learner's company (security check)
  ↓ Extract questions WITHOUT correct_answer (keep secure - no cheating)
  ↓ Return: {
      artifact_type: "quiz",
      quiz_id: "quiz:abc123",
      title: "Supervised Learning Quiz",
      questions: [
        {text: "What is supervised learning?", options: ["A) ...", "B) ...", "C) ..."]},
        {text: "Key challenge?", options: ["A) ...", "B) ..."]}
      ],
      quiz_url: "/quizzes/quiz:abc123"
    }
  ↓
api/learner_chat_service.py: Stream SSE response
  ↓ SSE event: {
      type: "tool-call",
      toolName: "surface_quiz",
      args: {quiz_id: "quiz:abc123"},
      result: {artifact_type, quiz_id, title, questions, quiz_url}
    }
  ↓
Frontend ChatPanel (assistant-ui)
  ↓ Receives tool-call event during stream
  ↓ Maps "surface_quiz" to InlineQuizWidget component
  ↓ Renders InlineQuizWidget with props from result
  ↓
Learner sees inline quiz:
  ┌──────────────────────────────────────────────────┐
  │ 📝 Supervised Learning Quiz                      │
  ├──────────────────────────────────────────────────┤
  │ Question 1: What is supervised learning?         │
  │ ○ A) Uses labeled datasets to train models       │
  │ ○ B) Uses unlabeled datasets                     │
  │ ○ C) Requires no training data                   │
  │ [Submit Answer]          [View Full Quiz →]      │
  └──────────────────────────────────────────────────┘
  ↓
Learner selects option A and clicks "Submit Answer"
  ↓
InlineQuizWidget state update: selectedOption = 0
  ↓
Submit handler calls Quiz.get_score([0])
  ↓ Domain method compares: user_answer (0) vs correct_answer (0)
  ↓ Result: is_correct = true
  ↓ Return: {
      score: 1, total: 1, percentage: 100,
      results: [{question_index: 0, is_correct: true, explanation: "Correct! Supervised learning..."}]
    }
  ↓
Component re-renders with feedback:
  ┌──────────────────────────────────────────────────┐
  │ 📝 Supervised Learning Quiz                      │
  ├──────────────────────────────────────────────────┤
  │ Question 1: What is supervised learning?         │
  │ ✓ A) Uses labeled datasets to train models       │ ← GREEN background, checkmark
  │ ○ B) Uses unlabeled datasets                     │
  │ ○ C) Requires no training data                   │
  │                                                   │
  │ ✓ Correct! Supervised learning uses labeled...  │ ← Explanation in success color
  │ [View Full Quiz →]                               │
  └──────────────────────────────────────────────────┘
  ↓
Learner validated, conversation continues
```

**Incorrect Answer Flow:**
```
Learner selects option B (incorrect)
  ↓
Submit handler calls Quiz.get_score([1])
  ↓ Domain method: user_answer (1) vs correct_answer (0)
  ↓ Result: is_correct = false
  ↓ Return: {
      score: 0, total: 1, percentage: 0,
      results: [{
        question_index: 0,
        user_answer: 1,
        correct_answer: 0,
        is_correct: false,
        explanation: "Not quite. Supervised learning requires labeled data..."
      }]
    }
  ↓
Component re-renders with feedback:
  ┌──────────────────────────────────────────────────┐
  │ 📝 Supervised Learning Quiz                      │
  ├──────────────────────────────────────────────────┤
  │ Question 1: What is supervised learning?         │
  │ ✓ A) Uses labeled datasets to train models       │ ← GREEN (correct answer revealed)
  │ ✗ B) Uses unlabeled datasets                     │ ← AMBER (user's incorrect selection)
  │ ○ C) Requires no training data                   │
  │                                                   │
  │ ✗ Not quite. Supervised learning requires...    │ ← Explanation in amber
  │ [View Full Quiz →]                               │
  └──────────────────────────────────────────────────┘
  ↓
Learner sees mistake, learns correct answer
```

**Podcast Surfacing Flow:**
```
AI conversation introduces new topic
  ↓
Prompt context includes: "Available learning materials: Podcast 'ML Fundamentals Overview' (ID: podcast:xyz789)"
  ↓
AI decides to offer alternative learning medium
  ↓
LangGraph chat.py: AI invokes surface_podcast tool
  ↓ Tool call parameters: {
      podcast_id: "podcast:xyz789"
    }
  ↓
graphs/tools.py: surface_podcast() async function executes
  ↓ Load Podcast by ID from domain
  ↓ Validate podcast exists
  ↓ Validate podcast.status == "completed" (audio file ready)
  ↓ Validate podcast.notebook_id belongs to learner's company
  ↓ Return: {
      artifact_type: "podcast",
      podcast_id: "podcast:xyz789",
      title: "ML Fundamentals Overview",
      audio_url: "/api/podcasts/podcast:xyz789/audio",
      duration_minutes: 7,
      transcript_url: "/api/podcasts/podcast:xyz789/transcript",
      status: "completed"
    }
  ↓
SSE streams tool-call event to frontend
  ↓
Frontend ChatPanel maps "surface_podcast" to InlineAudioPlayer
  ↓
Learner sees inline audio player:
  ┌──────────────────────────────────────────────────┐
  │ 🎧 ML Fundamentals Overview (7 minutes)          │
  ├──────────────────────────────────────────────────┤
  │ ▶ [Progress: ████░░░░░░░░░░░░ 2:30 / 7:00]      │
  │ Speed: [1x] [1.25x] [1.5x] [2x]                  │
  │ [View Transcript →]                              │
  └──────────────────────────────────────────────────┘
  ↓
Learner clicks Play button
  ↓ HTML5 <audio> element starts playback
  ↓ Progress bar updates with currentTime / duration
  ↓
Learner clicks "1.5x" speed button
  ↓ Component sets audio.playbackRate = 1.5
  ↓ Playback speeds up, button highlights
  ↓
Learner engages with audio content (different learning modality)
```

**Artifact Availability in Prompt Context:**
```
Learner opens module chat
  ↓
Backend: graphs/chat.py loads context
  ↓ Query all artifacts for notebook:
      SELECT * FROM quiz WHERE notebook_id = $notebook_id
      SELECT * FROM podcast WHERE notebook_id = $notebook_id AND status = "completed"
  ↓ Filter by company: JOIN module_assignment WHERE company_id = $learner.company_id
  ↓ Build artifact list string:
      """
      Available Learning Materials:
      - Quiz: "Supervised Learning Quiz" (ID: quiz:abc123) - 5 questions
      - Quiz: "Model Evaluation Quiz" (ID: quiz:def456) - 3 questions
      - Podcast: "ML Fundamentals Overview" (ID: podcast:xyz789) - 7 minutes, multi-speaker
      """
  ↓ Inject into prompt context via prompt.py
  ↓
prompts/global_teacher_prompt.j2 renders:
  """
  ## Artifact Surfacing Guidance

  You have access to learning materials (quizzes and podcasts) for this module.
  Use the surface_quiz and surface_podcast tools to enhance the learning experience.

  **When to Surface Quizzes:**
  - After explaining a key concept, to validate understanding
  - When learner seems confident, to reinforce learning
  - Before moving to next major topic, to check comprehension
  - If learner requests practice or self-assessment

  **When to Surface Podcasts:**
  - At the beginning to introduce topic in audio format
  - When learner prefers audio learning (ask about learning style)
  - As alternative explanation if text explanations aren't landing
  - For overview of complex topics before diving deep

  **Guidelines:**
  - Surface artifacts naturally in conversation flow
  - Explain why you're suggesting the artifact ("Let's validate your understanding...")
  - Don't overwhelm - max 1 artifact per 3-4 conversation turns
  - Respect learner preferences (some prefer text, others audio/interactive)

  {{ artifacts_list }}  {# Injected list from query above #}
  """
  ↓
AI has full context and guidance on when/how to use artifacts
```

**Critical Rules:**
- **Company Scoping**: ALWAYS validate artifact.notebook_id belongs to learner's company
- **Security**: Quiz questions returned WITHOUT correct_answer field (prevent cheating)
- **Podcast Status**: Only surface podcasts with status="completed" (audio file ready)
- **Prompt Guidance**: AI decides when to surface artifacts, not hardcoded triggers
- **Single Question Preview**: InlineQuizWidget shows first question only; full quiz via "View Full Quiz"
- **Audio Player State**: Use HTML5 <audio> element, track playback in component state
- **Color Semantics**: Green for correct, amber for incorrect (NO RED for learner-facing feedback)

### 📋 Technical Requirements

**Backend Stack:**
- Existing FastAPI/LangGraph/SurrealDB from Story 4.1-4.3
- Existing Quiz domain model from Story 3.2 (artifact generation)
- Existing Podcast domain model from Story 3.2 (artifact generation)
- NEW: surface_quiz and surface_podcast tools in graphs/tools.py
- EXTEND: graphs/chat.py to load artifacts and inject into prompt context
- EXTEND: prompts/global_teacher_prompt.j2 with artifact surfacing guidance
- EXTEND: api/routers/quizzes.py with learner GET endpoint
- EXTEND: api/routers/podcasts.py with learner GET endpoint
- NO NEW MODELS (Quiz and Podcast already exist)
- NO NEW MIGRATIONS

**Frontend Stack:**
- Existing assistant-ui, ChatPanel from Story 4.1
- Existing custom message part pattern from Story 4.3 (DocumentSnippetCard)
- NEW: InlineQuizWidget.tsx component (interactive quiz preview)
- NEW: InlineAudioPlayer.tsx component (audio playback controls)
- Shadcn/ui Card component for artifact containers
- Radix Progress primitive for audio progress bar
- lucide-react icons: CheckCircle (correct), AlertCircle (incorrect), Play, Pause
- i18next for translations (en-US + fr-FR)

**AI Prompt Engineering:**
- Artifact list injected into prompt context (available quizzes + podcasts)
- Guidance on when to surface quizzes vs podcasts
- Natural conversation flow with artifact suggestions
- AI explains WHY surfacing artifact ("Let's validate your understanding...")

**assistant-ui Integration:**
- Tool call results mapped to custom message parts
- "surface_quiz" → InlineQuizWidget
- "surface_podcast" → InlineAudioPlayer
- Follows same pattern as "surface_document" → DocumentSnippetCard (Story 4.3)

### 🗂️ Data Models & Dependencies

**EXISTING MODELS (From Story 3.2) - NO CHANGES:**

**Quiz Model** (`open_notebook/domain/quiz.py`):
```python
class QuizQuestion(BaseModel):
    question: str
    options: List[str]  # MCQ options (1+ options)
    correct_answer: int  # Index of correct option (0-based)
    explanation: Optional[str] = None  # Shown after answering
    source_reference: Optional[str] = None  # Link to source doc

class Quiz(ObjectModel):
    table_name = "quiz"

    notebook_id: str  # Parent notebook
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion]  # Embedded questions
    created_by: Literal["admin", "user"]  # "user" for AI-generated
    source_ids: Optional[List[str]]  # Which sources covered

    # Persistence workaround (SurrealDB nested object limitation)
    questions_json: Optional[str]  # JSON serialization of questions

    # User interaction tracking
    user_answers: Optional[List[int]]  # User's selected answer indices
    last_score: Optional[int]  # Last score achieved
    completed: bool  # Whether quiz completed

    def get_score(self, answers: List[int]) -> dict:
        """Calculate score and return detailed results

        Returns:
            {
                score: int,  # Number correct
                total: int,  # Total questions
                percentage: float,  # Score as percentage
                results: [
                    {
                        question_index: int,
                        user_answer: int,
                        correct_answer: int,
                        is_correct: bool,
                        explanation: str
                    },
                    ...
                ]
            }
        """
```

**Podcast Model** (`open_notebook/domain/podcast.py`):
```python
class Podcast(ObjectModel):
    table_name = "podcast"

    notebook_id: str  # Parent notebook
    title: str
    topic: Optional[str] = None  # For custom podcasts
    length: Literal["short", "medium", "long"]  # 3/7/15 minutes
    speaker_format: Literal["single", "multi"]  # Narration style
    audio_file_path: Optional[str] = None  # Path to generated MP3
    transcript: Optional[str] = None  # Full transcript text
    is_overview: bool  # Pre-generated overview by admin
    created_by: Literal["admin", "user"]  # Creator
    status: Literal["pending", "generating", "completed", "failed"]
    error_message: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Returns 3, 7, or 15 based on length"""
        return {"short": 3, "medium": 7, "long": 15}[self.length]

    @property
    def is_ready(self) -> bool:
        """Returns True if status=="completed" and audio file exists"""
        return self.status == "completed" and self.audio_file_path is not None
```

**NEW API RESPONSE MODELS** (`api/models.py`):
```python
class QuizQuestionPreview(BaseModel):
    """Quiz question without correct_answer (security - no cheating)"""
    question: str
    options: List[str]
    # NO correct_answer field (kept server-side)

class QuizSurfaceResponse(BaseModel):
    """Response for surface_quiz tool"""
    artifact_type: Literal["quiz"]
    quiz_id: str
    title: str
    questions: List[QuizQuestionPreview]  # First question only for inline preview
    quiz_url: str  # Link to full quiz viewer

class PodcastSurfaceResponse(BaseModel):
    """Response for surface_podcast tool"""
    artifact_type: Literal["podcast"]
    podcast_id: str
    title: str
    audio_url: str  # Endpoint to stream audio file
    duration_minutes: int
    transcript_url: str  # Endpoint to fetch transcript
    status: str  # "completed" or "generating"
```

**Tool Return Types:**
- `surface_quiz` returns: `dict` (serialized QuizSurfaceResponse)
- `surface_podcast` returns: `dict` (serialized PodcastSurfaceResponse)
- Both follow pattern from `surface_document` (Story 4.3)

**Dependencies:**
- **Story 3.2**: Quiz and Podcast domain models already exist
- **Story 4.3**: Custom message part pattern (DocumentSnippetCard)
- **Story 4.2**: Two-layer prompt assembly (extend with artifact context)
- **Story 4.1**: SSE streaming + assistant-ui integration
- **Story 2.2/2.3**: Module assignment for company scoping

### 📁 File Structure & Naming

**Backend Files to Create:**

**NEW:**
- `tests/test_artifact_surfacing.py` - NEW (150+ lines) - Tests for surface_quiz and surface_podcast tools

**Backend Files to Modify:**

**MODIFY:**
- `open_notebook/graphs/tools.py` - ADD surface_quiz and surface_podcast tools (100 lines)
- `open_notebook/graphs/chat.py` - ADD artifact loading and prompt injection (40 lines)
- `prompts/global_teacher_prompt.j2` - ADD Artifact Surfacing Guidance section (50 lines)
- `api/models.py` - ADD QuizSurfaceResponse, PodcastSurfaceResponse (20 lines)
- `api/routers/quizzes.py` - EXTEND GET endpoint with learner access control (30 lines)
- `api/routers/podcasts.py` - EXTEND GET endpoint with learner access control (30 lines)

**Frontend Files to Create:**

**NEW:**
- `frontend/src/components/learner/InlineQuizWidget.tsx` - NEW (150 lines)
- `frontend/src/components/learner/InlineAudioPlayer.tsx` - NEW (120 lines)
- `frontend/src/components/learner/__tests__/InlineQuizWidget.test.tsx` - NEW (100 lines)
- `frontend/src/components/learner/__tests__/InlineAudioPlayer.test.tsx` - NEW (100 lines)

**Frontend Files to Modify:**

**MODIFY:**
- `frontend/src/components/learner/ChatPanel.tsx` - ADD custom message part registration (20 lines)
- `frontend/src/lib/api/learner-chat.ts` - EXTEND SSE parser for new tool types (10 lines)
- `frontend/src/lib/locales/en-US/index.ts` - ADD 8 i18n keys
- `frontend/src/lib/locales/fr-FR/index.ts` - ADD 8 French translations

**Directory Structure:**
```
open_notebook/
├── graphs/
│   ├── tools.py                          # MODIFY - add surface_quiz, surface_podcast
│   └── chat.py                           # MODIFY - load artifacts, inject to prompt
│
prompts/
└── global_teacher_prompt.j2              # MODIFY - add artifact guidance section

api/
├── models.py                             # MODIFY - add response models
└── routers/
    ├── quizzes.py                        # MODIFY - learner GET endpoint
    └── podcasts.py                       # MODIFY - learner GET endpoint

frontend/src/
├── components/learner/
│   ├── ChatPanel.tsx                     # MODIFY - register custom parts
│   ├── InlineQuizWidget.tsx              # NEW - interactive quiz preview
│   ├── InlineAudioPlayer.tsx             # NEW - audio playback controls
│   └── __tests__/
│       ├── InlineQuizWidget.test.tsx     # NEW - quiz widget tests
│       └── InlineAudioPlayer.test.tsx    # NEW - audio player tests
│
├── lib/
│   ├── api/
│   │   └── learner-chat.ts               # MODIFY - SSE parser extension
│   └── locales/
│       ├── en-US/index.ts                # MODIFY - add keys
│       └── fr-FR/index.ts                # MODIFY - add translations

tests/
└── test_artifact_surfacing.py            # NEW - Backend tool tests
```

### 🧪 Testing Requirements

**Backend Tests (pytest) - 10+ test cases:**

**Tool Tests (6 tests):**
```python
# tests/test_artifact_surfacing.py

import pytest
from open_notebook.graphs.tools import surface_quiz, surface_podcast
from open_notebook.domain.quiz import Quiz, QuizQuestion
from open_notebook.domain.podcast import Podcast

@pytest.mark.asyncio
class TestSurfaceQuizTool:
    async def test_surface_quiz_valid(self):
        """Test surface_quiz returns quiz preview with questions"""
        # Create quiz in test DB
        # Invoke tool with quiz_id
        # Assert: returns artifact_type, quiz_id, title, questions, quiz_url
        # Assert: questions DO NOT include correct_answer field
        ...

    async def test_surface_quiz_company_scoping(self):
        """Test surface_quiz validates notebook belongs to learner's company"""
        # Create quiz for company A
        # Attempt to surface from learner in company B
        # Assert: raises error or returns empty
        ...

    async def test_surface_quiz_not_found(self):
        """Test surface_quiz handles invalid quiz_id gracefully"""
        # Invoke tool with non-existent quiz_id
        # Assert: returns error dict
        ...

@pytest.mark.asyncio
class TestSurfacePodcastTool:
    async def test_surface_podcast_valid(self):
        """Test surface_podcast returns podcast metadata with audio URL"""
        # Create completed podcast in test DB
        # Invoke tool with podcast_id
        # Assert: returns artifact_type, podcast_id, title, audio_url, duration, transcript_url
        ...

    async def test_surface_podcast_not_ready(self):
        """Test surface_podcast handles generating podcast gracefully"""
        # Create podcast with status="generating"
        # Invoke tool
        # Assert: returns status="generating" with message
        ...

    async def test_surface_podcast_company_scoping(self):
        """Test surface_podcast validates company access"""
        # Create podcast for company A
        # Attempt to surface from learner in company B
        # Assert: raises error or returns empty
        ...
```

**Prompt Injection Tests (2 tests):**
```python
class TestArtifactPromptInjection:
    async def test_artifacts_list_in_prompt(self):
        """Test prompt context includes available artifacts list"""
        # Create quizzes and podcasts for notebook
        # Load chat graph context
        # Assert: prompt includes "Available Learning Materials:" section
        # Assert: each artifact listed with ID
        ...

    async def test_artifact_guidance_in_prompt(self):
        """Test global_teacher_prompt.j2 includes surfacing guidance"""
        # Render prompt template
        # Assert: includes "Artifact Surfacing Guidance" section
        # Assert: includes "When to Surface Quizzes" instructions
        ...
```

**API Endpoint Tests (2 tests):**
```python
class TestLearnerArtifactEndpoints:
    async def test_get_quiz_learner_access(self):
        """Test GET /quizzes/{id} with learner auth and company scoping"""
        # Create quiz for company A
        # Request with learner from company A
        # Assert: 200 OK, quiz returned
        # Request with learner from company B
        # Assert: 403 Forbidden
        ...

    async def test_get_podcast_learner_access(self):
        """Test GET /podcasts/{id} with learner auth and company scoping"""
        # Create podcast for company A
        # Request with learner from company A
        # Assert: 200 OK, podcast returned with audio_url
        ...
```

**Frontend Tests (Vitest/React Testing Library) - 12+ test cases:**

**InlineQuizWidget Component (6 tests):**
```typescript
// components/learner/__tests__/InlineQuizWidget.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { InlineQuizWidget } from '../InlineQuizWidget';

describe('InlineQuizWidget', () => {
  const mockQuiz = {
    quizId: 'quiz:123',
    title: 'Test Quiz',
    questions: [
      { text: 'Question 1?', options: ['A', 'B', 'C'] }
    ],
    quizUrl: '/quizzes/quiz:123'
  };

  it('renders quiz title and question', () => {
    render(<InlineQuizWidget {...mockQuiz} />);
    expect(screen.getByText('Test Quiz')).toBeInTheDocument();
    expect(screen.getByText('Question 1?')).toBeInTheDocument();
  });

  it('renders radio options for answers', () => {
    render(<InlineQuizWidget {...mockQuiz} />);
    expect(screen.getByLabelText('A')).toBeInTheDocument();
    expect(screen.getByLabelText('B')).toBeInTheDocument();
  });

  it('enables submit button when option selected', () => {
    render(<InlineQuizWidget {...mockQuiz} />);
    const submitBtn = screen.getByText('Submit Answer');
    expect(submitBtn).toBeDisabled();

    fireEvent.click(screen.getByLabelText('A'));
    expect(submitBtn).toBeEnabled();
  });

  it('shows green feedback on correct answer', async () => {
    // Mock Quiz.get_score to return is_correct: true
    render(<InlineQuizWidget {...mockQuiz} />);
    fireEvent.click(screen.getByLabelText('A'));
    fireEvent.click(screen.getByText('Submit Answer'));

    // Wait for feedback
    expect(await screen.findByText(/Correct/i)).toBeInTheDocument();
    expect(screen.getByLabelText('A')).toHaveClass('bg-green-50');
  });

  it('shows amber feedback on incorrect answer with correct answer revealed', async () => {
    // Mock Quiz.get_score to return is_correct: false, correct_answer: 0
    render(<InlineQuizWidget {...mockQuiz} />);
    fireEvent.click(screen.getByLabelText('B'));
    fireEvent.click(screen.getByText('Submit Answer'));

    // Incorrect selected = amber
    expect(screen.getByLabelText('B')).toHaveClass('bg-amber-50');
    // Correct answer = green
    expect(screen.getByLabelText('A')).toHaveClass('bg-green-50');
  });

  it('renders View Full Quiz link', () => {
    render(<InlineQuizWidget {...mockQuiz} />);
    expect(screen.getByText('View Full Quiz')).toHaveAttribute('href', '/quizzes/quiz:123');
  });
});
```

**InlineAudioPlayer Component (6 tests):**
```typescript
// components/learner/__tests__/InlineAudioPlayer.test.tsx

describe('InlineAudioPlayer', () => {
  const mockPodcast = {
    podcastId: 'podcast:456',
    title: 'Test Podcast',
    audioUrl: '/api/podcasts/podcast:456/audio',
    durationMinutes: 7,
    transcriptUrl: '/api/podcasts/podcast:456/transcript',
    status: 'completed'
  };

  it('renders podcast title and duration', () => {
    render(<InlineAudioPlayer {...mockPodcast} />);
    expect(screen.getByText('Test Podcast')).toBeInTheDocument();
    expect(screen.getByText(/7 minutes/i)).toBeInTheDocument();
  });

  it('renders audio element with controls', () => {
    render(<InlineAudioPlayer {...mockPodcast} />);
    const audio = screen.getByRole('audio');
    expect(audio).toHaveAttribute('src', '/api/podcasts/podcast:456/audio');
  });

  it('toggles play/pause on button click', () => {
    render(<InlineAudioPlayer {...mockPodcast} />);
    const playBtn = screen.getByRole('button', { name: /play/i });

    fireEvent.click(playBtn);
    // Audio should start playing (mock audio.play())

    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument();
  });

  it('changes playback speed on speed button click', () => {
    render(<InlineAudioPlayer {...mockPodcast} />);
    const speedBtn = screen.getByText('1.5x');

    fireEvent.click(speedBtn);
    const audio = screen.getByRole('audio') as HTMLAudioElement;
    expect(audio.playbackRate).toBe(1.5);
  });

  it('updates progress bar during playback', () => {
    render(<InlineAudioPlayer {...mockPodcast} />);
    const audio = screen.getByRole('audio') as HTMLAudioElement;

    // Simulate time update
    Object.defineProperty(audio, 'currentTime', { value: 150, writable: true });
    Object.defineProperty(audio, 'duration', { value: 420, writable: true });
    fireEvent.timeUpdate(audio);

    // Progress bar should show 150/420 = 35.7%
    const progress = screen.getByRole('progressbar');
    expect(progress).toHaveAttribute('aria-valuenow', '35.7');
  });

  it('shows generating state when status not completed', () => {
    render(<InlineAudioPlayer {...mockPodcast} status="generating" />);
    expect(screen.getByText(/generating/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /play/i })).not.toBeInTheDocument();
  });
});
```

**Integration Tests:**
```typescript
// E2E flow test (Playwright or Cypress)
describe('Artifact Surfacing Flow', () => {
  it('surfaces quiz in chat and submits answer', async () => {
    // 1. Learner opens module chat
    // 2. AI surfaces quiz via surface_quiz tool
    // 3. InlineQuizWidget renders in chat
    // 4. Learner selects answer and submits
    // 5. Feedback appears (green or amber)
    // 6. Conversation continues
  });

  it('surfaces podcast and plays audio', async () => {
    // 1. AI surfaces podcast via surface_podcast tool
    // 2. InlineAudioPlayer renders in chat
    // 3. Learner clicks play button
    // 4. Audio starts playing, progress bar updates
    // 5. Learner changes speed to 1.5x
    // 6. Playback speed increases
  });
});
```

**Test Coverage Targets:**
- Backend: 85%+ for tools, 80%+ for API endpoints
- Frontend: 80%+ for InlineQuizWidget, 75%+ for InlineAudioPlayer

### 🚫 Anti-Patterns to Avoid (from Memory + Previous Stories)

**From Memory (CRITICAL):**

1. **Exposing Correct Answers in API Response**
   - ❌ Return quiz.questions with correct_answer field to frontend
   - ✅ Strip correct_answer before sending, keep server-side for scoring

2. **Missing Company Scoping on Artifact Queries**
   - ❌ Allow learner to request any quiz/podcast by ID
   - ✅ Validate artifact.notebook_id belongs to learner's company

3. **Hardcoded Artifact Surfacing Triggers**
   - ❌ Surface quiz after every 5 messages, podcast after 10 messages
   - ✅ Let AI decide based on conversation context and prompt guidance

4. **Missing i18n Translations**
   - ❌ Hardcode "Submit Answer", "Correct!", "Play Podcast" in components
   - ✅ Both en-US and fr-FR for ALL UI strings

5. **Using Red for Incorrect Answers**
   - ❌ Red color for incorrect quiz feedback (harsh, discouraging)
   - ✅ Amber/orange (warm neutral, constructive feedback)

6. **Surfacing Incomplete Podcasts**
   - ❌ Surface podcast with status="generating", broken audio link
   - ✅ Validate podcast.is_ready before surfacing, show generating state

**From Story 4.3 (DocumentSnippetCard):**

7. **Not Following Custom Message Part Pattern**
   - ❌ Create separate rendering logic for artifact tools
   - ✅ Register InlineQuizWidget and InlineAudioPlayer as custom message parts with assistant-ui

8. **Blocking Streaming with Tool Calls**
   - ❌ Wait for tool call completion before streaming AI response
   - ✅ Tool calls stream as part of response, don't block text streaming

**From Story 4.2 (Prompt Engineering):**

9. **Overloading Prompt with Artifact Details**
   - ❌ Include full quiz questions and podcast transcripts in prompt
   - ✅ Include artifact list with IDs only, tools fetch details

10. **Vague Artifact Surfacing Guidance**
    - ❌ Tell AI "you can use quizzes and podcasts"
    - ✅ Explicit instructions: when to surface each type, how to introduce them

**New to Story 4.6:**

11. **Auto-Playing Audio**
    - ❌ Audio starts playing immediately when InlineAudioPlayer renders
    - ✅ Learner must click Play button (user-initiated playback)

12. **Missing Audio Player Error Handling**
    - ❌ Assume audio file always exists and loads successfully
    - ✅ Handle 404, loading states, playback errors gracefully

13. **Full Quiz in Inline Widget**
    - ❌ Render all 5-10 quiz questions inline in chat (clutters conversation)
    - ✅ Show first question only, "View Full Quiz" link for complete experience

14. **Forgetting Playback Speed State**
    - ❌ Speed resets to 1x when user pauses/resumes
    - ✅ Persist playback speed in component state across pause/play cycles

15. **Missing Transcript Access**
    - ❌ Only show audio player, no way to read transcript
    - ✅ "View Transcript" link for accessibility and different learning styles

### 🔗 Integration with Existing Code

**Builds on Story 4.3 (Inline Document Snippets in Chat):**
- Custom message part pattern already established with DocumentSnippetCard
- SSE protocol for tool results already implemented
- assistant-ui integration pattern proven and working
- Story 4.6 EXTENDS with InlineQuizWidget and InlineAudioPlayer following same pattern

**Builds on Story 4.2 (Two-Layer Prompt System & Proactive AI Teacher):**
- Prompt assembly function already exists in graphs/prompt.py
- Jinja2 templates used for dynamic prompt generation
- Learner context already injected (username, profile, objectives)
- Story 4.6 EXTENDS with artifacts list + surfacing guidance section

**Builds on Story 4.1 (Learner Chat Interface & SSE Streaming):**
- SSE streaming infrastructure handles tool calls during response
- ChatPanel renders assistant-ui Thread with custom message parts
- TanStack Query manages chat state and caching
- Story 4.6 ADDS two new tool types to existing streaming system

**Builds on Story 3.2 (Artifact Generation & Preview):**
- Quiz and Podcast domain models already exist and generate artifacts
- Quizzes created from sources via LangGraph workflow
- Podcasts generated via async job queue (surreal-commands)
- Story 4.6 SURFACES these artifacts in conversation (consumption, not creation)

**Builds on Story 2.2 & 2.3 (Module Assignment & Visibility):**
- ModuleAssignment links notebooks to companies for data isolation
- All learner queries filtered by company_id
- is_locked controls phased module availability
- Story 4.6 APPLIES company scoping to artifact queries

**Integration Points:**

**Backend:**
- `open_notebook/graphs/tools.py` - ADD surface_quiz and surface_podcast (new tools)
- `open_notebook/graphs/chat.py` - EXTEND context loading with artifacts list
- `prompts/global_teacher_prompt.j2` - ADD Artifact Surfacing Guidance section
- `api/routers/quizzes.py` - EXTEND GET endpoint with learner auth
- `api/routers/podcasts.py` - EXTEND GET endpoint with learner auth

**Frontend:**
- `ChatPanel.tsx` - Register InlineQuizWidget and InlineAudioPlayer as custom parts
- `learner-chat.ts` - Extend SSE parser for surface_quiz and surface_podcast events
- Component library: Shadcn Card, Radix Progress, lucide-react icons (already imported)

**No Breaking Changes:**
- All changes additive (new tools, new components)
- Existing surface_document tool continues to work
- DocumentSnippetCard unaffected
- Learners can ignore artifacts if AI doesn't surface them (optional feature)

### 🎓 Previous Story Learnings Applied

**From Story 4.3 (Inline Document Snippets):**
- Custom message part registration pattern with assistant-ui
- Tool result structure: `{type: "tool-call", toolName, args, result}`
- Card component styling: warm neutral colors, subtle borders
- Click handlers prevent default, delegate to stores
- **Applied**: InlineQuizWidget and InlineAudioPlayer follow DocumentSnippetCard pattern exactly

**From Story 4.2 (Two-Layer Prompt System):**
- Jinja2 conditional sections: `{% if condition %}...{% endif %}`
- Prompt context assembled via dictionary injection
- Global vs per-module prompt separation
- **Applied**: Artifact list injected into context, guidance added to global_teacher_prompt.j2

**From Story 4.1 (SSE Streaming):**
- Tool calls streamed as part of AI response (non-blocking)
- SSE parser in learner-chat.ts handles multiple event types
- TanStack Query invalidation on state changes
- **Applied**: surface_quiz and surface_podcast stream like surface_document

**From Story 3.2 (Artifact Generation):**
- Quiz.questions stored as questions_json (SurrealDB workaround)
- Podcast.status tracks async generation progress
- Quiz.get_score() calculates results with explanations
- **Applied**: surface_quiz uses existing Quiz.get_score for feedback, surface_podcast checks is_ready

**From Story 2.3 (Module Lock/Unlock):**
- Company scoping on all learner queries: WHERE company_id = $user.company_id
- Learner endpoints use get_current_learner() dependency
- 403 Forbidden for cross-company access attempts
- **Applied**: Artifact queries validate notebook belongs to learner's company

**From Code Review Patterns (Stories 4.1-4.5):**
- Always use get_current_learner() for learner endpoints (security)
- TanStack Query for data fetching, not Zustand (performance)
- i18n completeness: en-US + fr-FR for all UI strings
- Warm color palette: green for success, amber for caution, no red for learners
- Smooth CSS transitions for UI state changes (150ms ease)

**Memory Patterns Applied:**
- **Type Safety**: QuizSurfaceResponse and PodcastSurfaceResponse Pydantic models
- **Company Scoping**: Filter artifacts by learner.company_id in tool queries
- **i18n Completeness**: 8 translation keys × 2 locales = 16 entries
- **Dev Agent Record**: Complete with agent model, file list, notes

### 📚 References

**Architecture Document:**
- [Source: _bmad-output/planning-artifacts/architecture.md#Custom Message Parts] - Lines 450-478 (DocumentSnippetCard pattern)
- [Source: _bmad-output/planning-artifacts/architecture.md#Quiz Domain Model] - Lines 520-545
- [Source: _bmad-output/planning-artifacts/architecture.md#Podcast Domain Model] - Lines 548-570
- [Source: _bmad-output/planning-artifacts/architecture.md#SSE Streaming Protocol] - Lines 175-195
- [Source: _bmad-output/planning-artifacts/architecture.md#Color System] - Lines 60-75 (warm neutral palette)

**Epic Requirements:**
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4] - Lines 650-780 (Learner AI Chat Experience)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.6] - Lines 764-788
- [Source: _bmad-output/planning-artifacts/epics.md#FR23] - AI surfaces artifacts in conversation

**Previous Story Learnings:**
- [Source: _bmad-output/implementation-artifacts/4-3-inline-document-snippets-in-chat.md] - DocumentSnippetCard pattern, custom message parts
- [Source: _bmad-output/implementation-artifacts/4-2-two-layer-prompt-system-and-proactive-ai-teacher.md] - Prompt assembly, Jinja2 templates
- [Source: _bmad-output/implementation-artifacts/4-1-learner-chat-interface-and-sse-streaming.md] - SSE streaming, assistant-ui integration
- [Source: _bmad-output/implementation-artifacts/3-2-artifact-generation-and-preview.md] - Quiz and Podcast models
- [Source: _bmad-output/implementation-artifacts/2-3-module-lock-unlock-and-learner-visibility.md] - Company scoping patterns

**Existing Code:**
- [Source: open_notebook/graphs/tools.py] - surface_document tool (pattern to follow)
- [Source: open_notebook/graphs/chat.py] - Chat graph with tool binding
- [Source: open_notebook/domain/quiz.py] - Quiz model with get_score method
- [Source: open_notebook/domain/podcast.py] - Podcast model with is_ready property
- [Source: frontend/src/components/learner/DocumentSnippetCard.tsx] - Custom message part example
- [Source: frontend/src/components/learner/ChatPanel.tsx] - assistant-ui Thread integration

**Recent Git Commits (Implementation Patterns):**
- [Commit: a4e1360] - "Implement Story 4.4 Tasks 1-2: Backend foundation for objective progress tracking"
  - Pattern: Domain model + tool + tests
  - Applied: Follow same pattern for artifact surfacing tools
- [Commit: c90d149] - "Complete Story 3.6: Edit Published Module (Tasks 10-12)"
  - Pattern: Backend + frontend + tests + dev agent record
  - Applied: Complete all 7 tasks with full test coverage
- [Commit: 18ffb6e] - "Fix Story 4.3 code review issues: Security, tests, error handling"
  - Pattern: Company scoping fixes, error handling, test additions
  - Applied: Ensure artifact queries have company scoping from start

### Project Structure Notes

**Alignment with Project:**
- Extends two-layer prompt system (Story 4.2) with artifact context
- Uses existing Quiz and Podcast models (Story 3.2)
- Follows custom message part pattern (Story 4.3)
- Applies company scoping security (Story 2.2/2.3)
- No new database schema changes (NO NEW MIGRATIONS)

**No Breaking Changes:**
- All changes additive (new tools, new components)
- Existing chat functionality unaffected
- DocumentSnippetCard continues to work
- Optional feature - learners can ignore artifacts if not surfaced

**Potential Conflicts:**
- **Story 4.7 (Async Task Handling)**: May surface podcasts still generating
  - Resolution: Story 4.6 checks podcast.is_ready, 4.7 adds status indicator for generating state
- **Story 5.2 (Artifacts Browsing in Side Panel)**: Different artifact viewing context
  - Resolution: Story 4.6 surfaces inline during conversation, 5.2 shows full artifact library in panel (complementary)

**Design Decisions:**
- Quiz preview shows first question only (not full quiz inline)
- Podcast player inline with HTML5 audio controls (not external player)
- AI decides when to surface artifacts (prompt-guided, not hardcoded triggers)
- Correct answers = green, incorrect = amber (no red for learners)
- Audio playback speed control for accessibility (1x/1.25x/1.5x/2x)
- Company scoping on all artifact queries (security)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- All 7 backend artifact surfacing tests passing
- Company scoping validation implemented via module_assignment JOIN query
- NotFoundError handling added for invalid quiz/podcast IDs
- Podcast status validation (is_ready property check)

### Completion Notes List

**Tasks 1-2 Complete (Backend):**
- ✅ Created `surface_quiz` and `surface_podcast` async tools following surface_document pattern
- ✅ Bound tools to chat model alongside existing tools (surface_document, check_off_objective)
- ✅ Implemented company scoping validation (module_assignment table JOIN)
- ✅ Added NotFoundError exception handling for graceful error responses
- ✅ Quiz preview excludes correct_answer field (security - prevent cheating)
- ✅ Podcast validation checks is_ready status before surfacing
- ✅ Comprehensive test suite: 7 tests covering valid/invalid/company scoping cases
- ✅ Added _load_available_artifacts function to graphs/prompt.py
- ✅ Artifacts list injected into global teacher prompt context
- ✅ Extended global_teacher_prompt.j2 with "Artifact Surfacing Guidance" section
- ✅ AI teacher now has context of available quizzes and podcasts with surfacing guidance

**Tasks 3-6 Complete (Frontend):**
- ✅ Created InlineQuizWidget component with interactive quiz submission and feedback
- ✅ Created InlineAudioPlayer component with HTML5 audio playback and speed control
- ✅ Integrated both components as custom message parts in ChatPanel.tsx
- ✅ Added i18n keys for en-US and fr-FR locales (quiz and podcast sections)
- ✅ Extended quiz and podcast API endpoints with company scoping for learner access
- ✅ Implemented green feedback for correct answers, amber for incorrect (warm UX)

**Task 7 Complete (Testing):**
- ✅ Backend tests: 7 passing (3 quiz tool, 4 podcast tool)
- ✅ Frontend tests: 42 passing (17 InlineQuizWidget, 25 InlineAudioPlayer)
- ✅ Tests cover: rendering, state management, API calls, user interactions, error handling
- ✅ All acceptance criteria validated through unit/integration tests

### File List

**Backend (Complete):**
- `open_notebook/graphs/tools.py` - MODIFIED - Added surface_quiz and surface_podcast tools (160 lines)
- `open_notebook/graphs/chat.py` - MODIFIED - Bound new tools to chat model (5 lines)
- `open_notebook/graphs/prompt.py` - MODIFIED - Added _load_available_artifacts, injected to context (80 lines)
- `prompts/global_teacher_prompt.j2` - MODIFIED - Added Artifact Surfacing Guidance section (60 lines)
- `tests/test_artifact_surfacing.py` - NEW - Comprehensive tool tests (235 lines, 7 tests passing)
- `api/routers/quizzes.py` - MODIFIED - Added company scoping to GET /quizzes/{id} and POST /quizzes/{id}/check (40 lines)
- `api/routers/podcasts.py` - MODIFIED - Added company-scoped endpoints for Podcast model artifacts (90 lines)

**Frontend (Complete):**
- `frontend/src/components/learner/InlineQuizWidget.tsx` - NEW - Interactive quiz widget (245 lines)
- `frontend/src/components/learner/InlineAudioPlayer.tsx` - NEW - Audio player with controls (200 lines)
- `frontend/src/components/learner/__tests__/InlineQuizWidget.test.tsx` - NEW - Quiz widget tests (430 lines, 17 tests passing)
- `frontend/src/components/learner/__tests__/InlineAudioPlayer.test.tsx` - NEW - Audio player tests (375 lines, 25 tests passing)
- `frontend/src/components/learner/ChatPanel.tsx` - MODIFIED - Registered custom message parts (20 lines)
- `frontend/src/lib/locales/en-US/index.ts` - MODIFIED - Added quiz and podcast i18n keys (13 keys)
- `frontend/src/lib/locales/fr-FR/index.ts` - MODIFIED - Added French translations (13 keys)
