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

## 💼 Platform Architecture

Open Notebook uses a modern three-tier architecture:

```
┌─────────────────────────────────────────────────────────┐
│     Frontend (React/Next.js) - 3-Column Learning UI     │
│              http://localhost:3000 (dev)                 │
│              http://localhost:8502 (prod)                │
├─────────────────────────────────────────────────────────┤
│ • Document Reader (left)                                │
│ • AI Chat Guide (center)                                │
│ • Artifacts Panel (right) - quizzes, podcasts, notes    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST + JWT Auth
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI)                              │
│              http://localhost:5055                      │
├─────────────────────────────────────────────────────────┤
│ • User authentication & role-based access               │
│ • Quiz generation (LangGraph workflows)                 │
│ • Custom podcast generation                             │
│ • AI chat guide mode (Socratic learning)                │
│ • Multi-provider AI via Esperanto                       │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                            │
│         http://localhost:8000                           │
├─────────────────────────────────────────────────────────┤
│ • Graph database with vector embeddings                 │
│ • User, Notebook, Quiz, Podcast, Artifact models        │
│ • Built-in semantic search                              │
└─────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend**: Next.js 16, React 19, TypeScript, TanStack Query, Zustand, Shadcn/ui
- **Backend**: FastAPI, Python 3.11+, LangGraph, Esperanto (multi-provider AI)
- **Database**: SurrealDB (graph database with vector search)

## 🆚 Open Notebook vs Google Notebook LM

| Feature | Open Notebook | Google Notebook LM | Advantage |
|---------|---------------|--------------------|-----------|
| **Privacy & Control** | Self-hosted, your data | Google cloud only | Complete data sovereignty |
| **Use Case** | B2B learning platform + research | Personal research only | Enterprise-ready |
| **User Management** | Admin/Learner roles, assignments | Single user | Multi-user organizations |
| **AI Provider Choice** | 16+ providers (OpenAI, Anthropic, Ollama, etc.) | Google models only | Flexibility and cost optimization |
| **Learning Features** | Quizzes, AI guide mode, custom podcasts | Limited | Interactive learning experience |
| **Podcast Speakers** | 1-4 speakers, custom topics/length | 2 speakers, fixed format | Extreme flexibility |
| **Content Transformations** | Custom and built-in | Limited options | Unlimited processing power |
| **API Access** | Full REST API | No API | Complete automation |
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
# 1. Clone the repository
git clone https://github.com/lfnovo/open-notebook.git
cd open-notebook

# 2. Install dependencies
uv sync
cd frontend && npm install && cd ..

# 3. Configure environment
cp .env.example .env
# Edit .env and add your API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)

# 4. Start all services (Database + API + Worker + Frontend)
make start-all
```

**Access:**
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5055
- **API Docs**: http://localhost:5055/docs

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

### Learning Platform Capabilities
- **🎓 Interactive Learning**: AI guide mode provides hints and encouragement, not direct answers
- **👥 User Management**: Admin and Learner roles with notebook assignment system
- **📖 3-Column Learning Interface**: Document reader, AI chat guide, and artifacts panel
- **❓ AI-Powered Quizzes**: Generate custom multiple-choice quizzes from your content
- **🎙️ Custom Podcasts**: Create topic-specific podcasts with configurable length and speakers
- **📚 Artifact Management**: Track all quizzes, podcasts, notes, and transformations
- **🔒 Per-Company Data Isolation**: Secure multi-tenant architecture (in development)

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


## Podcast Feature

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
- **Organization Multi-Tenancy**: Complete per-company data isolation
- **Progress Tracking**: Track learner progress through notebooks
- **Admin Dashboard**: User and content management interface
- **Advanced Quiz Types**: Short answer, essay questions, auto-grading
- **Learning Analytics**: Engagement metrics and completion tracking

### Recently Completed ✅
- **B2B Learning Platform**: User management, role-based access, notebook assignments
- **3-Column Learning Interface**: Document reader, AI chat guide, artifacts panel
- **AI Guide Mode**: Socratic learning approach (hints, not answers)
- **Quiz Generation**: AI-powered multiple-choice quiz creation
- **Custom Podcasts**: Topic-specific podcast generation with speaker options
- **Artifacts System**: Unified view of all generated content
- **Token Usage Tracking**: Monitor AI costs per company and user
- **Next.js Frontend**: Modern React-based frontend with improved performance
- **Multi-Model Support**: 16+ AI providers including OpenAI, Anthropic, Ollama, LM Studio
- **Content Transformations**: Powerful customizable actions for content processing

See the [open issues](https://github.com/lfnovo/open-notebook/issues) for a full list of proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## 📖 Need Help?
- **🤖 AI Installation Assistant**: We have a [CustomGPT built to help you install Open Notebook](https://chatgpt.com/g/g-68776e2765b48191bd1bae3f30212631-open-notebook-installation-assistant) - it will guide you through each step!
- **New to Open Notebook?** Start with our [Getting Started Guide](docs/0-START-HERE/index.md)
- **Need installation help?** Check our [Installation Guide](docs/1-INSTALLATION/index.md)
- **Want to see it in action?** Try our [Quick Start Tutorial](docs/0-START-HERE/quick-start.md)

## 🤝 Community & Contributing

### Join the Community
- 💬 **[Discord Server](https://discord.gg/37XJPXfz2w)** - Get help, share ideas, and connect with other users
- 🐛 **[GitHub Issues](https://github.com/lfnovo/open-notebook/issues)** - Report bugs and request features
- ⭐ **Star this repo** - Show your support and help others discover Open Notebook

### Contributing
We welcome contributions! We're especially looking for help with:
- **Frontend Development**: Help improve our modern Next.js/React UI
- **Testing & Bug Fixes**: Make Open Notebook more robust
- **Feature Development**: Build the coolest research tool together
- **Documentation**: Improve guides and tutorials

**Current Tech Stack**: Python, FastAPI, Next.js, React, SurrealDB
**Future Roadmap**: Real-time updates, enhanced async processing

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
