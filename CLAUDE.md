# Open Notebook - Root CLAUDE.md

This file provides architectural guidance for contributors working on Open Notebook at the project level.

## Project Overview

**Open Notebook** is evolving from a personal research assistant into a **B2B interactive learning platform**. Organizations can deliver curated educational content through AI-guided notebooks that combine reading materials, interactive AI chat, quizzes, and podcasts—all while maintaining privacy-first, self-hosted architecture.

### Product Vision
Enable organizations to provide structured, interactive learning experiences where:
- **Admins** curate educational notebooks with multi-modal content (PDFs, videos, documents)
- **Learners** engage with content through reading, AI-guided chat, self-generated quizzes, and custom podcasts
- **AI acts as a guide**, not an answer key—encouraging critical thinking and active learning

### Key Values
- **Privacy-first**: Self-hosted, complete data control
- **Multi-provider AI**: Support for 16+ AI providers (OpenAI, Anthropic, Ollama, etc.)
- **Interactive learning**: AI-guided exploration, not passive consumption
- **B2B focused**: Single-instance multi-tenancy with organization-level content
- **Open-source**: Transparent, customizable, community-driven

### Target Users
- **B2B Clients**: Companies, educational institutions, training organizations
- **Learners**: Employees/students consuming educational content
- **Admins**: Content creators managing notebooks and user access

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Frontend (React/Next.js) - Learning UI          │
│              frontend/ @ port 3000                       │
├─────────────────────────────────────────────────────────┤
│ - 3-Column Learning Interface:                          │
│   • Document Reader (sources viewer)                    │
│   • AI Chat Guide (interactive tutor)                   │
│   • Artifacts Panel (quizzes, podcasts, notes)          │
│ - User authentication & notebook assignment             │
│ - Zustand state management, TanStack Query (React Query)│
│ - Shadcn/ui component library with Tailwind CSS         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST + JWT Auth
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI)                              │
│              api/ @ port 5055                           │
├─────────────────────────────────────────────────────────┤
│ - User authentication & role-based access control       │
│ - Notebook assignment & access management               │
│ - Quiz generation workflow (LangGraph)                  │
│ - Custom podcast generation (topic + length + speakers) │
│ - AI chat guide mode (hints, not answers)               │
│ - Artifacts management (unified view)                   │
│ - Job queue for async operations (surreal-commands)     │
│ - Multi-provider AI provisioning via Esperanto          │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                            │
│         Graph database @ port 8000                      │
├─────────────────────────────────────────────────────────┤
│ - Core: User, Notebook, Source, Note, ChatSession       │
│ - Learning: Quiz, QuizQuestion, Podcast, Artifact       │
│ - Access: UserNotebookAssignment                        │
│ - Relationships: user-to-notebook, source-to-notebook   │
│ - Vector embeddings for semantic search                 │
└─────────────────────────────────────────────────────────┘
```

---

## Useful sources

User documentation is at @docs/

## Tech Stack

### Frontend (`frontend/`)
- **Framework**: Next.js 16 (React 19)
- **Language**: TypeScript
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Styling**: Tailwind CSS + Shadcn/ui
- **Build Tool**: Webpack (via Next.js)

### API Backend (`api/` + `open_notebook/`)
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Workflows**: LangGraph state machines
- **Database**: SurrealDB async driver
- **AI Providers**: Esperanto library (8+ providers: OpenAI, Anthropic, Google, Groq, Ollama, Mistral, DeepSeek, xAI)
- **Job Queue**: Surreal-Commands for async jobs (podcasts)
- **Logging**: Loguru
- **Validation**: Pydantic v2
- **Testing**: Pytest

### Database
- **SurrealDB**: Graph database with built-in embedding storage and vector search
- **Schema Migrations**: Automatic on API startup via AsyncMigrationManager

### Additional Services
- **Content Processing**: content-core library (file/URL extraction)
- **Prompts**: AI-Prompter with Jinja2 templating
- **Podcast Generation**: podcast-creator library
- **Embeddings**: Multi-provider via Esperanto

---

## Architecture Highlights

### 1. Learning Platform Architecture
- **3-Column Interface**: Document reader, AI chat guide, artifacts panel
- **User Management**: Authentication, role-based access (Admin/Learner)
- **Notebook Assignment**: Users see only assigned notebooks
- **Artifacts System**: Unified view of quizzes, podcasts, notes, transformations
- **AI Guide Mode**: Prompt-engineered to provide hints, not direct answers

### 2. Async-First Design
- All database queries, graph invocations, and API calls are async (await)
- SurrealDB async driver with connection pooling
- FastAPI handles concurrent requests efficiently
- Async job processing for quiz/podcast generation

### 3. LangGraph Workflows
- **source.py**: Content ingestion (extract → embed → save)
- **chat.py**: AI guide mode - conversational tutor with hints
- **ask.py**: Search + synthesis (retrieve relevant sources → LLM)
- **quiz_generation.py**: Generate MCQ quizzes from sources (NEW)
- **podcast.py**: Custom podcast generation with topic/length/speaker options (ENHANCED)
- **transformation.py**: Custom transformations on sources
- All use `provision_langchain_model()` for smart model selection

### 4. Multi-Provider AI
- **Esperanto library**: Unified interface to 16+ AI providers
- **ModelManager**: Factory pattern with fallback logic
- **Smart selection**: Detects large contexts, prefers long-context models
- **Override support**: Per-request model configuration
- **Cost optimization**: Cheaper models for quizzes, premium for podcasts

### 5. Database Schema
- **Automatic migrations**: AsyncMigrationManager runs on API startup
- **SurrealDB graph model**: Records with relationships and embeddings
- **Learning models**: User, Quiz, Podcast, Artifact, UserNotebookAssignment
- **Vector search**: Built-in semantic search across all content
- **Transactions**: Repo functions handle ACID operations

### 6. Authentication & Authorization
- **User Model**: Username/password authentication (JWT-based)
- **Roles**: Admin (content creator) vs. Learner (consumer)
- **Access Control**: Notebook assignment per user
- **Future**: Organization-based multi-tenancy, SSO/OAuth

---

## Security Patterns

### Per-Company Data Isolation (Story 7.5)

**CRITICAL:** All learner-scoped endpoints MUST enforce per-company data isolation to prevent cross-company data leakage.

#### Pattern 1: Learner-Only Endpoints (Preferred)

For endpoints accessible **only to learners**, use `get_current_learner()` dependency:

```python
# api/routers/learner.py
from api.auth import get_current_learner, LearnerContext

@router.get("/learner/modules")
async def list_modules(learner: LearnerContext = Depends(get_current_learner)):
    """List modules assigned to learner's company."""
    return await module_service.get_assigned_modules(
        company_id=learner.company_id,  # Automatically extracted from JWT
        user_id=learner.user.id,
    )
```

**Key Points:**
- `get_current_learner()` automatically extracts `company_id` from authenticated user
- Raises 403 if user is not a learner or has no company assignment
- Service layer MUST pass `company_id` to domain queries
- Domain queries MUST include `WHERE company_id = $company_id` filter

#### Pattern 2: Mixed Admin/Learner Endpoints (Quiz/Podcast Pattern)

For endpoints accessible to **both admins and learners**, use `get_current_user()` with manual role check:

```python
# api/routers/quizzes.py
from api.auth import get_current_user
from open_notebook.domain.user import User

@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str, user: User = Depends(get_current_user)):
    """
    Get quiz details.

    Story 7.5: Mixed admin/learner endpoint - manual company validation.
    Admins can access any quiz; learners only quizzes from assigned modules.
    """
    from open_notebook.database.repository import repo_query

    quiz = await quiz_service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Manual role-based company scoping
    if user.role == "learner":
        # Validate quiz's notebook is assigned to learner's company
        if not user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check module_assignment for company access
        result = await repo_query(
            """
            SELECT VALUE true
            FROM module_assignment
            WHERE notebook_id = $notebook_id
              AND company_id = $company_id
            LIMIT 1
            """,
            {"notebook_id": quiz.notebook_id, "company_id": user.company_id},
        )

        if not result:
            raise HTTPException(status_code=403, detail="Quiz not accessible")

    # Admin bypasses company check - can access any quiz
    return quiz
```

**When to Use This Pattern:**
- Endpoint serves both admin AND learner roles
- Admin needs unrestricted access to all data
- Learner needs company-scoped access

**Current Usage:**
- `GET /quizzes/{quiz_id}` - Quiz details
- `POST /quizzes/{quiz_id}/check` - Quiz answer checking
- `GET /podcasts/{podcast_id}` - Podcast details
- `GET /podcasts/{podcast_id}/audio` - Podcast audio streaming
- `GET /podcasts/{podcast_id}/transcript` - Podcast transcript

#### Pattern 3: Admin-Only Endpoints

For endpoints accessible **only to admins**, use `require_admin()` dependency:

```python
# api/routers/admin.py
from api.auth import require_admin
from open_notebook.domain.user import User

@router.get("/admin/modules")
async def list_all_modules(admin: User = Depends(require_admin)):
    """List ALL modules from all companies (admin-only)."""
    return await module_service.get_all_modules()  # No company filter
```

**Key Points:**
- Admin endpoints NEVER filter by company_id
- Admin sees data from all companies
- Use for management, reporting, and configuration endpoints

### Security Best Practices

1. **Consistent 403 for unauthorized access** - Don't leak resource existence with 404
2. **Always validate company access first** - Check assignment before loading resource
3. **Log security events** - Audit trail for access denials with company_id context
4. **Test cross-company isolation** - Regression tests for every learner endpoint
5. **Document mixed patterns** - Add comments explaining why admin bypasses company check

---

## Important Quirks & Gotchs

### Learning Platform Specifics
- **User roles**: Admin can create/edit notebooks; Learners are read-only
- **Notebook assignment**: Currently all users see all notebooks (MVP)
- **AI guide mode**: Prompt-engineered to give hints, not direct answers
- **Quiz generation**: Async job, may take 30-60 seconds
- **Custom podcasts**: User specifies topic, length, and speaker format
- **Artifacts**: All generated content (quizzes, podcasts, notes) stored per notebook

### API Startup
- **Migrations run automatically** on startup; check logs for errors
- **Must start API before UI**: UI depends on API for all data
- **SurrealDB must be running**: API fails without database connection
- **User seeding**: May need to create initial admin user manually

### Frontend-Backend Communication
- **Base API URL**: Configured in `.env.local` (default: http://localhost:5055)
- **CORS enabled**: Configured in `api/main.py` (allow all origins in dev)
- **Authentication**: JWT tokens stored in localStorage/cookies
- **Rate limiting**: Not built-in; add at proxy layer for production

### LangGraph Workflows
- **Blocking operations**: Chat/podcast/quiz workflows may take minutes
- **State persistence**: Uses SQLite checkpoint storage in `/data/sqlite-db/`
- **Model fallback**: If primary model fails, falls back to cheaper/smaller model
- **Quiz quality**: Depends on source content quality and LLM model

### Podcast Generation
- **Async job queue**: `podcast_service.py` submits jobs but doesn't wait
- **Track status**: Use `/commands/{command_id}` endpoint to poll status
- **TTS failures**: Fall back to silent audio if speech synthesis fails
- **Speaker format**: Single or multi-speaker (user choice)
- **Overview podcasts**: Pre-generated by admin when creating notebook

### Content Processing
- **File extraction**: Uses content-core library; supports 50+ file types
- **URL handling**: Extracts text + metadata from web pages
- **Large files**: Content processing is sync; may block API briefly
- **Embeddings**: Required for semantic search and AI chat context

---

## Component References

See dedicated CLAUDE.md files for detailed guidance:

- **[frontend/CLAUDE.md](frontend/CLAUDE.md)**: React/Next.js architecture, state management, API integration
- **[api/CLAUDE.md](api/CLAUDE.md)**: FastAPI structure, service pattern, endpoint development
- **[open_notebook/CLAUDE.md](open_notebook/CLAUDE.md)**: Backend core, domain models, LangGraph workflows, AI provisioning
- **[open_notebook/domain/CLAUDE.md](open_notebook/domain/CLAUDE.md)**: Data models, repository pattern, search functions
- **[open_notebook/ai/CLAUDE.md](open_notebook/ai/CLAUDE.md)**: ModelManager, AI provider integration, Esperanto usage
- **[open_notebook/graphs/CLAUDE.md](open_notebook/graphs/CLAUDE.md)**: LangGraph workflow design, state machines
- **[open_notebook/database/CLAUDE.md](open_notebook/database/CLAUDE.md)**: SurrealDB operations, migrations, async patterns

---

## Documentation Map

- **[README.md](README.md)**: Project overview, features, quick start
- **[PRD.md](PRD.md)**: Product Requirements Document for B2B learning platform transformation
- **[docs/index.md](docs/index.md)**: Complete user & deployment documentation
- **[CONFIGURATION.md](CONFIGURATION.md)**: Environment variables, model configuration
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines
- **[MAINTAINER_GUIDE.md](MAINTAINER_GUIDE.md)**: Release & maintenance procedures

---

## Testing Strategy

- **Unit tests**: `tests/test_domain.py`, `test_models_api.py`
- **Graph tests**: `tests/test_graphs.py` (workflow integration)
- **Utils tests**: `tests/test_utils.py`
- **Run all**: `uv run pytest tests/`
- **Coverage**: Check with `pytest --cov`

---

## Learning Platform Development

### Key Features to Implement

**User Authentication & Management**
- User model with roles (Admin/Learner)
- JWT-based authentication
- Notebook assignment logic
- Access control middleware

**3-Column Learning Interface**
- Document reader component (left column)
- AI chat guide component (middle column)
- Artifacts panel component (right column)
- Responsive layout for mobile/tablet

**Quiz System**
- Quiz generation workflow (LangGraph)
- MCQ question model and storage
- Quiz UI components (generator, viewer, results)
- Admin quiz pre-loading

**Enhanced Podcast System**
- Custom podcast generation with user options
- Single vs. multi-speaker selection
- Topic/length specification
- Overview podcast pre-generation

**Artifacts Management**
- Unified artifact model
- Artifacts list view
- Artifact type filtering
- Per-notebook artifact storage

**AI Guide Mode**
- Prompt engineering for hints vs. answers
- Socratic questioning patterns
- Document section references
- Context-aware guidance

### Development Priorities (MVP)

1. **Phase 1: Foundation** (Weeks 1-2)
   - User authentication system
   - Database schema updates (User, Quiz, Podcast, Artifact models)
   - Notebook assignment logic
   - API endpoints for auth and user management

2. **Phase 2: Learning Interface** (Weeks 3-4)
   - 3-column layout implementation
   - Document reader component
   - AI chat guide component
   - Artifacts panel component

3. **Phase 3: Interactive Features** (Weeks 5-6)
   - Quiz generation workflow
   - Custom podcast generation
   - AI guide mode prompt engineering
   - Artifact management

4. **Phase 4: Polish & Testing** (Week 7+)
   - Responsive design
   - UX refinement
   - Performance optimization
   - User testing

### Future Enhancements (Post-MVP)

- Admin dashboard for user/notebook management
- Organization-based access control
- Progress tracking and analytics
- Advanced quiz types (short answer, essay)
- Additional artifact types (slide decks, study guides)
- SSO/OAuth integration
- Onboarding questionnaire for user type detection

---

## Common Tasks

### Add a New API Endpoint
1. Create router in `api/routers/feature.py`
2. Create service in `api/feature_service.py`
3. Define schemas in `api/models.py`
4. Register router in `api/main.py`
5. Test via http://localhost:5055/docs

### Add a New LangGraph Workflow
1. Create `open_notebook/graphs/workflow_name.py`
2. Define StateDict and node functions
3. Build graph with `.add_node()` / `.add_edge()`
4. Invoke in service: `graph.ainvoke({"input": ...}, config={"..."})`
5. Test with sample data in `tests/`

### Add Database Migration
1. Create `migrations/XXX_description.surql`
2. Write SurrealQL schema changes
3. Create `migrations/XXX_description_down.surql` (optional rollback)
4. API auto-detects on startup; migration runs if newer than recorded version

### Deploy to Production
1. Review [CONFIGURATION.md](CONFIGURATION.md) for security settings
2. Use `make docker-release` for multi-platform image
3. Push to Docker Hub / GitHub Container Registry
4. Deploy `docker compose --profile multi up`
5. Verify migrations via API logs

---

## Support & Community

- **Documentation**: https://open-notebook.ai
- **Discord**: https://discord.gg/37XJPXfz2w
- **Issues**: https://github.com/lfnovo/open-notebook/issues
- **License**: MIT (see LICENSE)

---

**Last Updated**: January 2026 | **Project Version**: 1.2.4+
