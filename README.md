<a id="readme-top"></a>

<!-- [![Contributors][contributors-shield]][contributors-url] -->
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
<!-- [![LinkedIn][linkedin-shield]][linkedin-url] -->


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/lfnovo/open-notebook">
    <img src="docs/assets/hero.svg" alt="Logo">
  </a>

  <h3 align="center">Open Notebook</h3>

  <p align="center">
    Open-source B2B interactive learning platform - Privacy-first alternative to Google's Notebook LM!
    <br /><strong>Join our <a href="https://discord.gg/37XJPXfz2w">Discord server</a> for help, to share workflow ideas, and suggest features!</strong>
    <br />
    <a href="https://www.open-notebook.ai"><strong>Checkout our website »</strong></a>
    <br />
    <br />
    <a href="docs/0-START-HERE/index.md">📚 Get Started</a>
    ·
    <a href="docs/3-USER-GUIDE/index.md">📖 User Guide</a>
    ·
    <a href="docs/2-CORE-CONCEPTS/index.md">✨ Features</a>
    ·
    <a href="docs/1-INSTALLATION/index.md">🚀 Deploy</a>
  </p>
</div>

<p align="center">
<a href="https://trendshift.io/repositories/14536" target="_blank"><img src="https://trendshift.io/api/badge/repositories/14536" alt="lfnovo%2Fopen-notebook | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  <a href="https://zdoc.app/de/lfnovo/open-notebook">Deutsch</a> |
  <a href="https://zdoc.app/es/lfnovo/open-notebook">Español</a> |
  <a href="https://zdoc.app/fr/lfnovo/open-notebook">français</a> |
  <a href="https://zdoc.app/ja/lfnovo/open-notebook">日本語</a> |
  <a href="https://zdoc.app/ko/lfnovo/open-notebook">한국어</a> |
  <a href="https://zdoc.app/pt/lfnovo/open-notebook">Português</a> |
  <a href="https://zdoc.app/ru/lfnovo/open-notebook">Русский</a> |
  <a href="https://zdoc.app/zh/lfnovo/open-notebook">中文</a>
</div>

## B2B Interactive Learning Platform - Privacy-First, Multi-Model, Self-Hosted

![New Notebook](docs/assets/asset_list.png)

**Open Notebook** transforms educational content delivery by enabling organizations to create AI-guided, interactive learning experiences. From personal research assistant to enterprise learning platform - all while keeping your data private and under your control.

**Perfect for:**
- 🏢 **Companies** - Employee training and onboarding programs
- 🎓 **Educational Institutions** - Course content and study materials
- 📚 **Training Organizations** - Professional development courses
- 🔬 **Research Teams** - Collaborative knowledge management

**What makes Open Notebook unique:**
- 🔒 **Privacy-First** - Self-hosted, complete data control
- 🤖 **AI Provider Freedom** - Support for 16+ providers (OpenAI, Anthropic, Ollama, LM Studio, and more)
- 📚 **Interactive Learning** - AI acts as a guide, not an answer key
- 🎙️ **Multi-Modal Content** - PDFs, videos, audio, podcasts, quizzes, and more
- 🔍 **Intelligent Search** - Full-text and vector search across all content
- 🌐 **Multi-Language** - English, Portuguese, and Chinese (Simplified & Traditional)

Learn more at [https://www.open-notebook.ai](https://www.open-notebook.ai)

---

## 🆕 What's New - Enterprise B2B Learning Platform

Open Notebook has evolved from a personal research tool into a **full-featured enterprise B2B learning platform**:

**Latest in v1.5+ (20,000+ lines of new code):**
- ✅ **Multi-Tenancy (Companies)** - Complete per-company data isolation and management
- ✅ **Module Assignments** - Assign learning modules to specific companies
- ✅ **Learning Objectives & Progress** - Track learner goals and completion
- ✅ **Token Usage Tracking** - Monitor AI costs per company, user, and module
- ✅ **GDPR Compliance** - User and company data deletion endpoints
- ✅ **LangSmith Integration** - Advanced LLM tracing and debugging
- ✅ **Admin Error Notifications** - Real-time error monitoring for administrators
- ✅ **AI Navigation Assistant** - Platform-wide AI help and guidance
- ✅ **Module Prompts** - Custom AI prompts per learning module
- ✅ **Enhanced Podcasts** - Speaker and episode profiles for customized audio
- ✅ **Source Chat** - Chat with individual documents separately
- ✅ **Separate Chat Interfaces** - Dedicated admin and learner chat experiences
- ✅ **User Management** - Admin and Learner roles with authentication
- ✅ **AI Guide Mode** - Socratic learning approach (hints, not answers)
- ✅ **Quiz Generation** - AI-powered multiple-choice quiz creation from content
- ✅ **Artifacts System** - Unified view of quizzes, podcasts, and notes
- ✅ **3-Column Interface** - Document reader, chat guide, and artifacts panel

**In Development:**
- 🚧 Advanced Learning Analytics - Detailed engagement metrics and reporting
- 🚧 Progress Dashboards - Visual learner progress tracking
- 🚧 Certificate Generation - Course completion certificates

---

## 💼 Platform Architecture

Open Notebook uses a modern three-tier architecture:

```
┌─────────────────────────────────────────────────────────┐
│     Frontend (React/Next.js) - 3-Column Learning UI     │
│              http://localhost:3000 (dev)                 │
│              http://localhost:8502 (prod)                │
├─────────────────────────────────────────────────────────┤
│ • Document Reader (left)                                │
│ • AI Chat Guide (center) - Admin, Learner, Source modes│
│ • Artifacts Panel (right) - quizzes, podcasts, notes    │
│ • AI Navigation Assistant (platform-wide help)          │
│ • Learning Objectives & Progress Display                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST + JWT Auth
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI) - 33+ Routers                │
│              http://localhost:5055                      │
├─────────────────────────────────────────────────────────┤
│ • Multi-tenant company management                       │
│ • User authentication & role-based access (Admin/Learner)│
│ • Module assignments to companies                       │
│ • Learning objectives & progress tracking               │
│ • Token usage tracking (per company/user/module)        │
│ • Quiz generation (LangGraph workflows)                 │
│ • Custom podcast generation (speaker/episode profiles)  │
│ • AI chat guide mode (Socratic learning)                │
│ • GDPR-compliant data deletion                          │
│ • LangSmith LLM tracing integration                     │
│ • Admin error notifications                             │
│ • Multi-provider AI via Esperanto (16+ providers)       │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                            │
│         http://localhost:8000                           │
├─────────────────────────────────────────────────────────┤
│ • Graph database with vector embeddings                 │
│ • Enterprise models: Company, ModuleAssignment          │
│ • User models: User, TokenUsage                         │
│ • Learning models: Notebook, LearningObjective, Progress│
│ • Content models: Source, Note, Quiz, Podcast, Artifact │
│ • Built-in semantic search & relationships              │
└─────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend**: Next.js 16, React 19, TypeScript, TanStack Query, Zustand, Shadcn/ui
- **Backend**: FastAPI, Python 3.11+, LangGraph, Esperanto (multi-provider AI), 33+ API routers
- **Database**: SurrealDB (graph database with vector search)
- **Integrations**: LangSmith (LLM tracing), Surreal-Commands (async jobs)

## 🏢 Enterprise Features

Open Notebook v1.5+ includes comprehensive enterprise capabilities for B2B deployments:

### Multi-Tenancy & Data Isolation
- **Company Management**: Create and manage multiple client organizations
- **Per-Company Data Isolation**: Complete data segregation between companies (CRITICAL security feature)
- **Module Assignments**: Assign specific learning modules to specific companies
- **Locked Modules**: Prevent companies from modifying assigned modules

### Cost Management & Monitoring
- **Token Usage Tracking**: Monitor AI costs at multiple levels:
  - Per company: Total AI usage across all users
  - Per user: Individual learner AI consumption
  - Per module: Cost per learning module
  - Per interaction: Detailed token counts for every AI call
- **Budget Alerts**: Set limits and receive notifications (in development)
- **Cost Transparency**: Learners can view their own token usage

### Learning Analytics & Progress
- **Learning Objectives**: Define measurable goals for each module
- **Progress Tracking**: Monitor learner completion of objectives
- **Engagement Metrics**: Track quiz attempts, chat interactions, podcast listens
- **Completion Reports**: Generate reports per company or learner (in development)

### Compliance & Security
- **GDPR-Compliant Data Deletion**: Complete user and company data removal endpoints
- **Role-Based Access Control**: Admin and Learner roles with fine-grained permissions
- **Security Patterns**: Per-company endpoints with automatic isolation enforcement
- **Audit Logging**: Comprehensive logging of all system operations
- **Error Notifications**: Admin alerts for system errors and security events

### Administration & Management
- **Admin Dashboard**: Manage companies, users, and module assignments
- **Error Monitoring**: Real-time error notifications with detailed context
- **LangSmith Integration**: Advanced LLM debugging and performance monitoring
- **System Configuration**: Per-module AI prompts and behavior settings
- **Speaker/Episode Profiles**: Custom podcast voice and format configurations

## 🆚 Open Notebook vs Google Notebook LM

| Feature | Open Notebook | Google Notebook LM | Advantage |
|---------|---------------|--------------------|-----------|
| **Privacy & Control** | Self-hosted, your data | Google cloud only | Complete data sovereignty |
| **Use Case** | Enterprise B2B learning platform | Personal research only | Multi-tenant enterprise-ready |
| **Multi-Tenancy** | Full company management + isolation | Single user | Serve multiple organizations |
| **User Management** | Admin/Learner roles + permissions | Single user | Team collaboration |
| **Cost Tracking** | Per-company/user/module token tracking | None | Budget management & transparency |
| **Learning Features** | Objectives, progress, quizzes, AI guide | Basic chat only | Structured learning paths |
| **GDPR Compliance** | Full data deletion capabilities | Google's policy | EU/enterprise compliance |
| **AI Provider Choice** | 16+ providers (OpenAI, Anthropic, Ollama, etc.) | Google models only | Flexibility and cost optimization |
| **Podcast Speakers** | 1-4 speakers, custom topics/length/voices | 2 speakers, fixed format | Extreme flexibility |
| **Content Transformations** | Custom and built-in | Limited options | Unlimited processing power |
| **API Access** | Full REST API (33+ routers) | No API | Complete automation |
| **LLM Tracing** | LangSmith integration | None | Performance monitoring |
| **Deployment** | Docker, cloud, or local | Google hosted only | Deploy anywhere |
| **Customization** | Open source, fully customizable | Closed system | Unlimited extensibility |
| **Cost** | Pay only for AI usage | Free tier + limits | Transparent and controllable |

**Why Choose Open Notebook?**
- 🏢 **Built for Organizations**: User management, role-based access, content curation
- 🎓 **Active Learning**: AI guide mode encourages critical thinking, not passive consumption
- 🔒 **Privacy First**: Sensitive training materials stay completely private
- 💰 **Cost Control**: Choose cheaper providers or run locally with Ollama
- 🎙️ **Better Podcasts**: Full control over topic, length, and speakers
- 🔧 **Unlimited Customization**: Modify, extend, and integrate as needed
- 🌐 **No Vendor Lock-in**: Switch providers, deploy anywhere, own your data

### Built With

[![Python][Python]][Python-url] [![Next.js][Next.js]][Next-url] [![React][React]][React-url] [![SurrealDB][SurrealDB]][SurrealDB-url] [![LangChain][LangChain]][LangChain-url]

## 🚀 Quick Start

Choose your installation method:

### 🐳 **Docker (Recommended for Production)**

**Best for deployment** - Fast setup with Docker Compose:

→ **[Docker Compose Installation Guide](docs/1-INSTALLATION/docker-compose.md)**
- Multi-container setup
- 5-10 minutes setup time
- Requires Docker Desktop

**Quick Start:**

1. Get an API key (OpenAI, Anthropic, Google, etc.) or setup Ollama
2. Create `docker-compose.yml`:

```yaml
services:
  surrealdb:
    image: surrealdb/surrealdb:v2
    volumes:
      - ./surreal_data:/mydata
    environment:
      - SURREAL_EXPERIMENTAL_GRAPHQL=true
    ports:
      - "8000:8000"
    command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
    pull_policy: always
    restart: always

  open_notebook:
    image: lfnovo/open_notebook:v1-latest
    ports:
      - "8502:8502"
      - "5055:5055"
    environment:
      - OPENAI_API_KEY=your-api-key-here
      - SURREAL_URL=ws://surrealdb:8000/rpc
      - SURREAL_USER=root
      - SURREAL_PASS=root
      - SURREAL_NS=open_notebook
      - SURREAL_DB=open_notebook
    depends_on:
      - surrealdb
    volumes:
      - ./notebook_data:/app/data
    restart: always
```

3. Start the services:

```bash
docker compose up -d
```

4. Access at **http://localhost:8502**

---

### 💻 **From Source (Recommended for Development)**

**For developers and contributors:**

→ **[From Source Installation Guide](docs/1-INSTALLATION/from-source.md)**
- Clone and run locally
- 10-15 minutes setup time
- Requires: Python 3.11+, Node.js 18+, Docker, uv

**Quick Start:**

```bash
# Step 1: Clone the repository
git clone https://github.com/lfnovo/open-notebook.git
cd open-notebook

# Step 2: Install dependencies
uv sync
cd frontend && npm install && cd ..

# Step 3: Configure environment
cp .env.example .env
# Edit .env and add your API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

**Step 4: Start Docker Desktop (CRITICAL)**

⚠️ **You MUST start Docker Desktop BEFORE proceeding!**

- **macOS**: Open Docker Desktop, wait for whale icon in menu bar to be steady (not animated)
- **Windows**: Open Docker Desktop, wait for icon in system tray to stabilize
- **Linux**: Ensure daemon is running: `sudo systemctl start docker`

Verify Docker is ready:
```bash
docker ps
# Should show: CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty list is OK, just shouldn't error)
```

**Step 5: Start all services**

```bash
make start-all
```

This command will:
1. Start SurrealDB in Docker (wait 3 seconds)
2. Start FastAPI backend (wait 3 seconds)
3. Start background worker (wait 2 seconds)
4. Start Next.js frontend (interactive mode)

**⚠️ Common Error**: If you get "Cannot connect to the Docker daemon", you skipped Step 4. Start Docker Desktop and retry.


**Access:**
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5055
- **API Docs**: http://localhost:5055/docs

**Step 6: Verify installation**

Wait 10-15 seconds for all services to start, then verify:

```bash
# Check all services are running
make status

# Expected output:
# 📊 Open Notebook Service Status:
# Database (SurrealDB):
#   ✅ Running
# API Backend:
#   ✅ Running
# Background Worker:
#   ✅ Running
# Next.js Frontend:
#   ✅ Running
```

Test each service:

```bash
# Test API health endpoint
curl http://localhost:5055/health
# Expected: {"status":"ok"}

# Test API docs (in browser)
open http://localhost:5055/docs

# Test frontend (in browser)
open http://localhost:3000
```

**Success Indicators:**
- ✅ SurrealDB container running in Docker Desktop
- ✅ API responds at http://localhost:5055/docs
- ✅ Frontend loads at http://localhost:3000
- ✅ No error messages in terminal where `make start-all` is running

**If anything fails**, see the [Troubleshooting](#-troubleshooting) section below.

**Alternative - Start services individually:**

```bash
# Terminal 1: Database
make database

# Terminal 2: API
make api

# Terminal 3: Background Worker
make worker

# Terminal 4: Frontend
cd frontend && npm run dev
```

### ⚙️ Environment Configuration

**Required Environment Variables** (in `.env` file):

```bash
# AI Provider (choose one or more)
OPENAI_API_KEY=sk-...                    # For OpenAI models
ANTHROPIC_API_KEY=sk-ant-...             # For Claude models
GROQ_API_KEY=gsk_...                     # For Groq (fast inference)
GOOGLE_API_KEY=...                       # For Google/Gemini
# Or use Ollama (free, local) - no API key needed

# Database (automatically configured with docker-compose)
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_NS=open_notebook
SURREAL_DB=open_notebook

# API (optional)
API_URL=http://localhost:5055           # Frontend API connection
API_HOST=127.0.0.1
API_PORT=5055
```

**See `.env.example` for complete configuration options including:**
- Multiple AI provider configurations
- Custom model selection
- TTS/STT provider settings
- Advanced database configuration
- User authentication settings

**First Run - What Happens:**
On first startup, the API will automatically:
1. ✅ Run database migrations (check API terminal for "Migration successful")
2. ✅ Create all database tables (Company, User, Notebook, ModuleAssignment, etc.)
3. ✅ Initialize indexes and relationships
4. ✅ Set up vector embeddings infrastructure
5. ✅ Create default system configuration

**No manual database setup needed!** Just watch the API terminal for confirmation messages.

**Optional - Create First Admin User:**
After startup, create your first admin user via API:

```bash
curl -X POST http://localhost:5055/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin",
    "role": "admin"
  }'
```

Then log in at http://localhost:3000

### 🛠️ Common Commands

Once installed from source, use these commands to manage your installation:

```bash
# Start all services (recommended)
make start-all

# Stop all services
make stop-all

# Check service status
make status

# Start services individually
make database    # Start SurrealDB only
make api         # Start API backend
make worker      # Start background worker
make frontend    # Start frontend dev server

# Development
make ruff        # Format and lint Python code
make lint        # Type checking with mypy
make clean-cache # Clean Python cache files

# Docker
make dev         # Start with docker-compose.dev.yml
make full        # Start with docker-compose.full.yml
```

---

### 📖 Need Help?

- **🤖 AI Installation Assistant**: [CustomGPT to help you install](https://chatgpt.com/g/g-68776e2765b48191bd1bae3f30212631-open-notebook-installation-assistant)
- **🆘 Troubleshooting**: [5-minute troubleshooting guide](docs/6-TROUBLESHOOTING/quick-fixes.md)
- **💬 Community Support**: [Discord Server](https://discord.gg/37XJPXfz2w)
- **🐛 Report Issues**: [GitHub Issues](https://github.com/lfnovo/open-notebook/issues)
- **📚 Full Documentation**: [docs/](docs/)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lfnovo/open-notebook&type=date&legend=top-left)](https://www.star-history.com/#lfnovo/open-notebook&type=date&legend=top-left)


## Provider Support Matrix

Thanks to the [Esperanto](https://github.com/lfnovo/esperanto) library, we support this providers out of the box!

| Provider     | LLM Support | Embedding Support | Speech-to-Text | Text-to-Speech |
|--------------|-------------|------------------|----------------|----------------|
| OpenAI       | ✅          | ✅               | ✅             | ✅             |
| Anthropic    | ✅          | ❌               | ❌             | ❌             |
| Groq         | ✅          | ❌               | ✅             | ❌             |
| Google (GenAI) | ✅          | ✅               | ❌             | ✅             |
| Vertex AI    | ✅          | ✅               | ❌             | ✅             |
| Ollama       | ✅          | ✅               | ❌             | ❌             |
| Perplexity   | ✅          | ❌               | ❌             | ❌             |
| ElevenLabs   | ❌          | ❌               | ✅             | ✅             |
| Azure OpenAI | ✅          | ✅               | ❌             | ❌             |
| Mistral      | ✅          | ✅               | ❌             | ❌             |
| DeepSeek     | ✅          | ❌               | ❌             | ❌             |
| Voyage       | ❌          | ✅               | ❌             | ❌             |
| xAI          | ✅          | ❌               | ❌             | ❌             |
| OpenRouter   | ✅          | ❌               | ❌             | ❌             |
| OpenAI Compatible* | ✅          | ❌               | ❌             | ❌             |

*Supports LM Studio and any OpenAI-compatible endpoint

## ✨ Key Features

### Enterprise Learning Platform
- **🏢 Multi-Tenancy**: Full company management with per-company data isolation
- **📊 Module Assignments**: Assign learning modules to specific companies
- **🎯 Learning Objectives**: Define and track measurable learning goals
- **📈 Progress Tracking**: Monitor learner progress through objectives
- **💰 Token Usage Tracking**: Monitor AI costs per company, user, and module
- **🔐 GDPR Compliance**: Complete user and company data deletion capabilities
- **🔔 Admin Notifications**: Real-time error and system event notifications
- **🗺️ AI Navigation**: Platform-wide AI assistant for help and guidance

### Learning Experience
- **🎓 Interactive Learning**: AI guide mode provides hints and encouragement, not direct answers
- **👥 User Management**: Admin and Learner roles with fine-grained permissions
- **📖 3-Column Learning Interface**: Document reader, AI chat guide, and artifacts panel
- **❓ AI-Powered Quizzes**: Generate custom multiple-choice quizzes from your content
- **🎙️ Custom Podcasts**: Create topic-specific podcasts with speaker and episode profiles
- **💬 Multiple Chat Modes**: Source chat, learner chat, admin chat
- **📚 Artifact Management**: Track all quizzes, podcasts, notes, and transformations
- **📝 Module Prompts**: Custom AI behavior per learning module

### Core Platform Features
- **🔒 Privacy-First**: Self-hosted, complete data control - no cloud dependencies required
- **🤖 AI Provider Freedom**: 16+ providers (OpenAI, Anthropic, Ollama, Google, Groq, Mistral, DeepSeek, xAI, LM Studio)
- **📚 Universal Content Support**: PDFs, videos, audio, web pages, Office documents, and more
- **🎯 Multi-Notebook Organization**: Manage multiple learning modules or research projects
- **🔍 Intelligent Search**: Full-text and vector search across all content
- **💬 Context-Aware Chat**: AI conversations powered by your curated sources

### Advanced Features
- **⚡ Reasoning Model Support**: Full support for thinking models like DeepSeek-R1 and o1
- **🔧 Content Transformations**: Customizable actions to summarize and extract insights
- **🌐 Comprehensive REST API**: Full programmatic access for integrations
- **📊 Fine-Grained Context Control**: Choose exactly what to share with AI models
- **📎 Citations**: Answers with proper source references
- **🌐 Multi-Language UI**: English, Portuguese, and Chinese (Simplified & Traditional)


## 🎓 How It Works

### For Learners

1. **📚 Access Your Modules** - Log in and see learning modules assigned to your company
2. **🎯 Review Objectives** - See learning goals and track your progress
3. **📖 Read & Explore** - View documents, PDFs, videos in the reader panel
4. **💬 Ask Questions** - Chat with AI guide for hints (not direct answers)
5. **❓ Test Yourself** - Generate custom quizzes to validate understanding
6. **🎙️ Listen & Learn** - Create topic-specific podcasts for passive learning
7. **📊 Track Progress** - View your artifacts, objectives completion, and token usage
8. **🗺️ Get Help** - Use AI Navigation Assistant for platform guidance

### For Admins

1. **🏢 Create Companies** - Set up client organizations
2. **📚 Create Modules** - Organize learning content by topic
3. **📄 Upload Sources** - Add PDFs, videos, documents, web pages
4. **🎯 Define Objectives** - Set measurable learning goals per module
5. **📝 Configure Prompts** - Customize AI behavior per module
6. **🎙️ Pre-Generate Content** - Create overview podcasts and base quizzes
7. **🔗 Assign Modules** - Link modules to specific companies
8. **👥 Manage Users** - Add learners to companies
9. **💰 Monitor Costs** - Track token usage per company/user/module
10. **🔔 Receive Alerts** - Get notified of errors and system events

### AI Guide Mode - Socratic Learning

The AI guide is prompt-engineered to encourage critical thinking:
- Provides **hints** instead of direct answers
- Asks **follow-up questions** to deepen understanding
- References **specific document sections** to review
- Encourages **active exploration** over passive consumption

## 🎙️ Podcast Feature Demo

[![Check out our podcast sample](https://img.youtube.com/vi/D-760MlGwaI/0.jpg)](https://www.youtube.com/watch?v=D-760MlGwaI)

## 📚 Documentation

### Getting Started
- **[📖 Introduction](docs/0-START-HERE/index.md)** - Learn what Open Notebook offers
- **[⚡ Quick Start](docs/0-START-HERE/quick-start.md)** - Get up and running in 5 minutes
- **[🔧 Installation](docs/1-INSTALLATION/index.md)** - Comprehensive setup guide
- **[🎯 Your First Notebook](docs/0-START-HERE/first-notebook.md)** - Step-by-step tutorial

### User Guide
- **[📱 Interface Overview](docs/3-USER-GUIDE/interface-overview.md)** - Understanding the layout
- **[📚 Notebooks](docs/3-USER-GUIDE/notebooks.md)** - Organizing your research
- **[📄 Sources](docs/3-USER-GUIDE/sources.md)** - Managing content types
- **[📝 Notes](docs/3-USER-GUIDE/notes.md)** - Creating and managing notes
- **[💬 Chat](docs/3-USER-GUIDE/chat.md)** - AI conversations
- **[🔍 Search](docs/3-USER-GUIDE/search.md)** - Finding information

### Advanced Topics
- **[🎙️ Podcast Generation](docs/2-CORE-CONCEPTS/podcasts.md)** - Create professional podcasts
- **[🔧 Content Transformations](docs/2-CORE-CONCEPTS/transformations.md)** - Customize content processing
- **[🤖 AI Models](docs/4-AI-PROVIDERS/index.md)** - AI model configuration
- **[🔌 MCP Integration](docs/5-CONFIGURATION/mcp-integration.md)** - Connect with Claude Desktop, VS Code and other MCP clients
- **[🔧 REST API Reference](docs/7-DEVELOPMENT/api-reference.md)** - Complete API documentation
- **[🔐 Security](docs/5-CONFIGURATION/security.md)** - Password protection and privacy
- **[🚀 Deployment](docs/1-INSTALLATION/index.md)** - Complete deployment guides for all scenarios

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🎯 Use Cases

### For Organizations

**Employee Training & Onboarding**
- Upload training materials, SOPs, and documentation
- New hires learn interactively with AI guidance
- Generate quizzes to validate understanding
- Create orientation podcasts for passive learning

**Educational Institutions**
- Curate course materials into interactive notebooks
- AI guide helps students think critically
- Auto-generate study quizzes and review podcasts
- Track student engagement with learning artifacts

**Professional Development**
- Deliver certification training content
- AI-guided learning paths through complex topics
- Custom podcasts for on-the-go learning
- Practical quizzes to reinforce key concepts

### For Individuals

**Research & Knowledge Management**
- Organize research papers and web content
- Chat with AI about your sources
- Generate summaries and insights
- Create personal study materials

## 🗺️ Roadmap

### In Development 🚧
- **Advanced Learning Analytics Dashboard**: Visual engagement metrics and reporting
- **Certificate Generation**: Course completion certificates
- **Budget Alerts**: Token usage limits and notifications
- **Advanced Quiz Types**: Short answer, essay questions, auto-grading
- **Mobile App**: Native iOS/Android applications
- **SSO Integration**: SAML/OAuth for enterprise authentication

### Recently Completed ✅ (v1.5+ - 20,000+ lines)

**Enterprise Features**:
- **Multi-Tenancy (Companies)**: Complete per-company data isolation (Story 7.5)
- **Module Assignments**: Assign learning modules to specific companies (Story 2.2)
- **Learning Objectives & Progress**: Track learner goals and completion (Story 3.3)
- **Token Usage Tracking**: Monitor AI costs per company/user/module (Story 7.7)
- **Learner Transparency**: Detailed token usage view for learners (Story 7.8)
- **GDPR Compliance**: User and company data deletion endpoints (Story 7.6)
- **Admin Error Notifications**: Real-time error monitoring (Story 7.3)
- **Structured Error Logging**: Comprehensive system logging (Story 7.2)

**AI & Learning Features**:
- **LangSmith Integration**: Advanced LLM tracing and debugging (Story 7.4)
- **AI Navigation Assistant**: Platform-wide AI help system (Story 6.1)
- **Module Prompts**: Custom AI behavior per module (Story 3.4)
- **Source Chat**: Chat with individual documents
- **Admin/Learner Chat Modes**: Separate chat interfaces
- **Speaker/Episode Profiles**: Enhanced podcast customization
- **AI Guide Mode**: Socratic learning approach (hints, not answers)
- **Quiz Generation**: AI-powered multiple-choice quiz creation
- **Custom Podcasts**: Topic-specific podcast generation

**Platform & Architecture**:
- **3-Column Learning Interface**: Document reader, AI chat guide, artifacts panel
- **Next.js 16 Frontend**: Modern React 19-based UI with improved performance
- **33+ API Routers**: Comprehensive REST API coverage
- **Multi-Model Support**: 16+ AI providers including OpenAI, Anthropic, Ollama, LM Studio
- **Artifacts System**: Unified view of all generated content
- **Content Transformations**: Powerful customizable actions for content processing

See the [open issues](https://github.com/lfnovo/open-notebook/issues) for a full list of proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 🔧 Troubleshooting

### Docker daemon not running

**Issue**: `Cannot connect to the Docker daemon at unix:///Users/.../.docker/run/docker.sock`

**Solution**:
```bash
# 1. Open Docker Desktop application
# 2. Wait for Docker to fully start (whale icon in menu bar should be steady)
# 3. Verify Docker is running:
docker ps

# 4. Then retry:
make start-all
```

**On macOS**: Look for the Docker whale icon in the menu bar (top right). It should be steady, not animated.
**On Windows**: Check system tray for Docker icon.
**On Linux**: Ensure Docker daemon is running: `sudo systemctl status docker`

### Services won't start

**Issue**: `make start-all` fails or services crash

**Solutions**:
```bash
# Check if ports are already in use
lsof -i :3000  # Frontend
lsof -i :5055  # API
lsof -i :8000  # Database

# Stop any running services
make stop-all

# Verify Docker is running
docker ps

# Start database separately first
make database
# Wait 5 seconds, then start API
make api
```

### Frontend can't connect to API

**Issue**: "Network Error" or "Cannot connect to API"

**Solutions**:
1. Verify API is running: `curl http://localhost:5055/health`
2. Check `.env` file has correct `API_URL=http://localhost:5055`
3. Check CORS settings in `api/main.py`
4. Restart both API and frontend

### Python version errors

**Issue**: "Python 3.13 not supported" or similar

**Solutions**:
```bash
# Check Python version
python --version

# Use specific Python version with uv
uv sync --python 3.11
```

### npm install fails

**Issue**: Package installation errors in frontend

**Solutions**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Database connection errors

**Issue**: "Cannot connect to SurrealDB"

**Solutions**:
```bash
# Check SurrealDB is running
docker ps | grep surrealdb

# Check logs
docker logs surrealdb

# Restart database
docker compose down
make database
```

### Background worker not processing jobs

**Issue**: Podcasts or async tasks stuck in "processing"

**Solutions**:
```bash
# Check worker is running
pgrep -f "surreal-commands-worker"

# Restart worker
make worker-restart

# Check worker logs
# Look for error messages in terminal where worker is running
```

## 📖 Need Help?
- **🤖 AI Installation Assistant**: [CustomGPT to help you install](https://chatgpt.com/g/g-68776e2765b48191bd1bae3f30212631-open-notebook-installation-assistant) - it will guide you through each step!
- **🆘 Troubleshooting Guide**: [5-minute troubleshooting guide](docs/6-TROUBLESHOOTING/quick-fixes.md)
- **New to Open Notebook?** Start with our [Getting Started Guide](docs/0-START-HERE/index.md)
- **Need installation help?** Check our [Installation Guide](docs/1-INSTALLATION/index.md)
- **Want to see it in action?** Try our [Quick Start Tutorial](docs/0-START-HERE/quick-start.md)

## 💻 System Requirements

### For Docker Deployment
- **Docker Desktop** or Docker Engine
- **4GB RAM minimum** (8GB recommended)
- **10GB disk space** for images and data
- Any OS that supports Docker (Windows, macOS, Linux)

### For Development (From Source)
- **Python 3.11 or 3.12** (3.13 not yet supported)
- **Node.js 18+** and npm
- **Docker** (for SurrealDB)
- **uv** package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **8GB RAM recommended**
- **Git** for cloning the repository

## 🤝 Community & Contributing

### Join the Community
- 💬 **[Discord Server](https://discord.gg/37XJPXfz2w)** - Get help, share ideas, and connect with other users
- 🐛 **[GitHub Issues](https://github.com/lfnovo/open-notebook/issues)** - Report bugs and request features
- ⭐ **Star this repo** - Show your support and help others discover Open Notebook

### Contributing
We welcome contributions! We're building the future of enterprise learning platforms together. With 20,000+ lines of new code in v1.5, there's plenty to explore. We're especially looking for help with:

**High-Priority Areas**:
- **Learning Analytics Dashboard**: Visual progress tracking and reporting
- **Certificate Generation**: Course completion certificates
- **Budget Alerts**: Token usage limits and notifications
- **Advanced Quiz Types**: Short answer, essay questions, auto-grading
- **Mobile Responsiveness**: Optimize 3-column layout for tablets/mobile
- **Testing**: Unit tests for 33+ API routers
- **Documentation**: User guides for enterprise features

**Good First Issues**:
- UI/UX improvements for learner interface
- Additional AI prompt templates
- Bug fixes and edge case handling
- Documentation updates
- Translation support

**Current Tech Stack**:
- Backend: Python 3.11+, FastAPI, LangGraph, SurrealDB, 33+ API routers
- Frontend: Next.js 16, React 19, TypeScript, TanStack Query, Zustand
- AI: Esperanto (multi-provider), LangChain, LangSmith
- Infrastructure: Docker, Surreal-Commands (async jobs)

**Architecture**: See [CLAUDE.md](CLAUDE.md) for comprehensive architectural guidance

**Recent Additions** (good places to contribute):
- `api/routers/companies.py` - Company management
- `api/routers/module_assignments.py` - Module assignments
- `api/routers/learning_objectives.py` - Learning objectives
- `api/routers/token_usage.py` - Token usage tracking
- `frontend/src/components/admin/` - Admin UI components
- `frontend/src/components/learner/` - Learner UI components

See our [Contributing Guide](CONTRIBUTING.md) for detailed information on how to get started.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 📄 License

Open Notebook is MIT licensed. See the [LICENSE](LICENSE) file for details.


**Community Support**:
- 💬 [Discord Server](https://discord.gg/37XJPXfz2w) - Get help, share ideas, and connect with users
- 🐛 [GitHub Issues](https://github.com/lfnovo/open-notebook/issues) - Report bugs and request features
- 🌐 [Website](https://www.open-notebook.ai) - Learn more about the project

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/lfnovo/open-notebook.svg?style=for-the-badge
[contributors-url]: https://github.com/lfnovo/open-notebook/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/lfnovo/open-notebook.svg?style=for-the-badge
[forks-url]: https://github.com/lfnovo/open-notebook/network/members
[stars-shield]: https://img.shields.io/github/stars/lfnovo/open-notebook.svg?style=for-the-badge
[stars-url]: https://github.com/lfnovo/open-notebook/stargazers
[issues-shield]: https://img.shields.io/github/issues/lfnovo/open-notebook.svg?style=for-the-badge
[issues-url]: https://github.com/lfnovo/open-notebook/issues
[license-shield]: https://img.shields.io/github/license/lfnovo/open-notebook.svg?style=for-the-badge
[license-url]: https://github.com/lfnovo/open-notebook/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/lfnovo
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white
[Next-url]: https://nextjs.org/
[React]: https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black
[React-url]: https://reactjs.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[LangChain]: https://img.shields.io/badge/LangChain-3A3A3A?style=for-the-badge&logo=chainlink&logoColor=white
[LangChain-url]: https://www.langchain.com/
[SurrealDB]: https://img.shields.io/badge/SurrealDB-FF5E00?style=for-the-badge&logo=databricks&logoColor=white
[SurrealDB-url]: https://surrealdb.com/
