# Complete Environment Reference

Comprehensive list of all environment variables available in Open Notebook.

---

## API Configuration

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `API_URL` | No | Auto-detected | URL where frontend reaches API (e.g., http://localhost:5055) |
| `INTERNAL_API_URL` | No | http://localhost:5055 | Internal API URL for Next.js server-side proxying |
| `API_CLIENT_TIMEOUT` | No | 300 | Client timeout in seconds (how long to wait for API response) |
| `OPEN_NOTEBOOK_PASSWORD` | No | None | Password to protect Open Notebook instance |

---

## AI Provider: OpenAI

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `OPENAI_API_KEY` | If using OpenAI | None | OpenAI API key (starts with `sk-`) |

**Setup:** Get from https://platform.openai.com/api-keys

---

## AI Provider: Anthropic (Claude)

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `ANTHROPIC_API_KEY` | If using Anthropic | None | Claude API key (starts with `sk-ant-`) |

**Setup:** Get from https://console.anthropic.com/

---

## AI Provider: Google Gemini

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `GOOGLE_API_KEY` | If using Google | None | Google API key for Gemini |
| `GEMINI_API_BASE_URL` | No | Default endpoint | Override Gemini API endpoint |
| `VERTEX_PROJECT` | If using Vertex AI | None | Google Cloud project ID |
| `VERTEX_LOCATION` | If using Vertex AI | us-east5 | Vertex AI location |
| `GOOGLE_APPLICATION_CREDENTIALS` | If using Vertex AI | None | Path to service account JSON |

**Setup:** Get from https://aistudio.google.com/app/apikey

---

## AI Provider: Groq

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `GROQ_API_KEY` | If using Groq | None | Groq API key (starts with `gsk_`) |

**Setup:** Get from https://console.groq.com/keys

---

## AI Provider: Mistral

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `MISTRAL_API_KEY` | If using Mistral | None | Mistral API key |

**Setup:** Get from https://console.mistral.ai/

---

## AI Provider: DeepSeek

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `DEEPSEEK_API_KEY` | If using DeepSeek | None | DeepSeek API key |

**Setup:** Get from https://platform.deepseek.com/

---

## AI Provider: xAI

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `XAI_API_KEY` | If using xAI | None | xAI API key |

**Setup:** Get from https://console.x.ai/

---

## AI Provider: Ollama (Local)

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `OLLAMA_API_BASE` | If using Ollama | None | Ollama endpoint (e.g., http://localhost:11434) |

**Setup:** Install from https://ollama.ai

---

## AI Provider: OpenRouter

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `OPENROUTER_API_KEY` | If using OpenRouter | None | OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | https://openrouter.ai/api/v1 | OpenRouter endpoint |

**Setup:** Get from https://openrouter.ai/

---

## AI Provider: OpenAI-Compatible

For self-hosted LLMs, LM Studio, or OpenAI-compatible endpoints:

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `OPENAI_COMPATIBLE_BASE_URL` | If using compatible | None | Base URL for OpenAI-compatible endpoint |
| `OPENAI_COMPATIBLE_API_KEY` | If using compatible | None | API key for endpoint |
| `OPENAI_COMPATIBLE_BASE_URL_LLM` | No | Uses generic | Language model endpoint (overrides generic) |
| `OPENAI_COMPATIBLE_API_KEY_LLM` | No | Uses generic | Language model API key (overrides generic) |
| `OPENAI_COMPATIBLE_BASE_URL_EMBEDDING` | No | Uses generic | Embedding endpoint (overrides generic) |
| `OPENAI_COMPATIBLE_API_KEY_EMBEDDING` | No | Uses generic | Embedding API key (overrides generic) |
| `OPENAI_COMPATIBLE_BASE_URL_STT` | No | Uses generic | Speech-to-text endpoint (overrides generic) |
| `OPENAI_COMPATIBLE_API_KEY_STT` | No | Uses generic | STT API key (overrides generic) |
| `OPENAI_COMPATIBLE_BASE_URL_TTS` | No | Uses generic | Text-to-speech endpoint (overrides generic) |
| `OPENAI_COMPATIBLE_API_KEY_TTS` | No | Uses generic | TTS API key (overrides generic) |

**Setup:** For LM Studio, typically: `OPENAI_COMPATIBLE_BASE_URL=http://localhost:1234/v1`

---

## AI Provider: Azure OpenAI

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | If using Azure | None | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | If using Azure | None | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_VERSION` | No | 2024-12-01-preview | Azure OpenAI API version |
| `AZURE_OPENAI_API_KEY_LLM` | No | Uses generic | LLM-specific API key |
| `AZURE_OPENAI_ENDPOINT_LLM` | No | Uses generic | LLM-specific endpoint |
| `AZURE_OPENAI_API_VERSION_LLM` | No | Uses generic | LLM-specific API version |
| `AZURE_OPENAI_API_KEY_EMBEDDING` | No | Uses generic | Embedding-specific API key |
| `AZURE_OPENAI_ENDPOINT_EMBEDDING` | No | Uses generic | Embedding-specific endpoint |
| `AZURE_OPENAI_API_VERSION_EMBEDDING` | No | Uses generic | Embedding-specific API version |

---

## AI Provider: VoyageAI (Embeddings)

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `VOYAGE_API_KEY` | If using Voyage | None | Voyage AI API key (for embeddings) |

**Setup:** Get from https://www.voyageai.com/

---

## Text-to-Speech (TTS)

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `ELEVENLABS_API_KEY` | If using ElevenLabs TTS | None | ElevenLabs API key for voice generation |
| `TTS_BATCH_SIZE` | No | 5 | Concurrent TTS requests (1-5, depends on provider) |

**Setup:** Get from https://elevenlabs.io/

---

## Database: SurrealDB

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `SURREAL_URL` | Yes | ws://surrealdb:8000/rpc | SurrealDB WebSocket connection URL |
| `SURREAL_USER` | Yes | root | SurrealDB username |
| `SURREAL_PASSWORD` | Yes | root | SurrealDB password |
| `SURREAL_NAMESPACE` | Yes | open_notebook | SurrealDB namespace |
| `SURREAL_DATABASE` | Yes | open_notebook | SurrealDB database name |

---

## Database: Retry Configuration

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `SURREAL_COMMANDS_RETRY_ENABLED` | No | true | Enable retries on failure |
| `SURREAL_COMMANDS_RETRY_MAX_ATTEMPTS` | No | 3 | Maximum retry attempts |
| `SURREAL_COMMANDS_RETRY_WAIT_STRATEGY` | No | exponential_jitter | Retry wait strategy (exponential_jitter/exponential/fixed/random) |
| `SURREAL_COMMANDS_RETRY_WAIT_MIN` | No | 1 | Minimum wait time between retries (seconds) |
| `SURREAL_COMMANDS_RETRY_WAIT_MAX` | No | 30 | Maximum wait time between retries (seconds) |

---

## Database: Concurrency

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `SURREAL_COMMANDS_MAX_TASKS` | No | 5 | Maximum concurrent database tasks |

---

## LLM Timeouts

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `ESPERANTO_LLM_TIMEOUT` | No | 60 | LLM inference timeout in seconds |
| `ESPERANTO_SSL_VERIFY` | No | true | Verify SSL certificates (false = development only) |
| `ESPERANTO_SSL_CA_BUNDLE` | No | None | Path to custom CA certificate bundle |

---

## Content Extraction

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `FIRECRAWL_API_KEY` | No | None | Firecrawl API key for advanced web scraping |
| `JINA_API_KEY` | No | None | Jina AI API key for web extraction |

**Setup:**
- Firecrawl: https://firecrawl.dev/
- Jina: https://jina.ai/

---

## Debugging & Monitoring: LangSmith LLM Tracing

LangSmith provides end-to-end tracing for all AI interactions in Open Notebook, enabling debugging of AI behavior, monitoring retrieval quality, and tracking token usage.

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `LANGCHAIN_TRACING_V2` | No | false | Enable LangSmith tracing (set to `true` to activate) |
| `LANGCHAIN_ENDPOINT` | No | https://api.smith.langchain.com | LangSmith API endpoint |
| `LANGCHAIN_API_KEY` | No | None | LangSmith API key (get from dashboard) |
| `LANGCHAIN_PROJECT` | No | Open Notebook | LangSmith project name (for organizing traces) |

**Setup Guide:**

1. **Get LangSmith API Key:**
   - Sign up at https://smith.langchain.com/
   - Go to Settings → API Keys
   - Create a new API key

2. **Enable Tracing:**
   ```bash
   # In your .env file:
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_api_key_here
   LANGCHAIN_PROJECT="Open Notebook"  # Optional: customize project name
   ```

3. **Restart API:**
   ```bash
   # Docker:
   docker compose restart api

   # Local development:
   # Stop and restart your API server
   ```

4. **Verify Tracing:**
   - Perform any AI interaction (chat, quiz generation, etc.)
   - Open https://smith.langchain.com/
   - Navigate to your project → Traces
   - You should see traces with metadata tags (user_id, company_id, notebook_id, workflow_name)

**What Gets Traced:**

LangSmith automatically traces all AI workflows:
- **Learner Chat** - Full conversation chains with tool calls (surface_document, check_off_objective)
- **Admin Chat** - Module creation assistant conversations
- **Navigation Assistant** - Cross-module search queries and suggestions
- **Source Processing** - Content ingestion and transformation workflows
- **Quiz Generation** - (Not currently traced - uses direct LLM calls)
- **Learning Objectives** - Auto-generation from module content
- **Transformations** - Custom content transformations
- **RAG Retrieval** - Semantic search queries and results
- **Tool Calls** - All AI tool invocations with parameters and results

**Metadata Tags for Filtering:**

Each trace includes metadata tags for easy filtering in LangSmith UI:
- `user:<user_id>` - User who triggered the action
- `company:<company_id>` - Company context (multi-tenancy)
- `notebook:<notebook_id>` - Module context
- `workflow:<workflow_name>` - Type of workflow (learner_chat, navigation_assistant, etc.)

**Example Filtering:**
- View all traces for a specific user: `user:user_abc123`
- View all navigation assistant traces: `workflow:navigation_assistant`
- View all traces for a module: `notebook:notebook_xyz789`

**Troubleshooting:**

**Tracing not appearing?**
- Verify `LANGCHAIN_TRACING_V2=true` (not "True" or "1")
- Check `LANGCHAIN_API_KEY` is set correctly
- Restart API server after changing environment variables
- Check API logs for LangSmith connection errors

**Too many traces?**
- LangSmith has free tier limits - check your plan
- Traces are sent asynchronously and don't block workflows
- Consider using selective tracing (e.g., only in staging)

**Optional - Workflows Run Normally Without LangSmith:**
- If `LANGCHAIN_TRACING_V2` is not set to "true", all workflows continue normally
- No performance impact when tracing is disabled
- Safe to enable/disable at any time

---

## Error Notifications: Admin Alert System

Configure automatic admin notifications when errors occur in production. Supports webhook, Slack, and email backends.

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `ERROR_NOTIFICATION_BACKEND` | No | none | Notification backend: `none`, `webhook`, `slack`, or `email` |
| `WEBHOOK_URL` | If backend=webhook | None | Generic webhook endpoint (receives JSON POST) |
| `SLACK_WEBHOOK_URL` | If backend=slack | None | Slack Incoming Webhook URL (Slack Block Kit format) |
| `SMTP_HOST` | If backend=email | None | SMTP server hostname (e.g., smtp.gmail.com) |
| `SMTP_PORT` | If backend=email | 587 | SMTP server port (587 for TLS, 465 for SSL, 25 for plain) |
| `SMTP_USER` | If backend=email | None | SMTP authentication username |
| `SMTP_PASSWORD` | If backend=email | None | SMTP authentication password |
| `SMTP_USE_TLS` | If backend=email | true | Use TLS encryption (recommended) |
| `ADMIN_EMAIL` | If backend=email | None | Admin email address to receive notifications |

**Setup Guide:**

**Option 1: Webhook (Generic HTTP Endpoint)**
```bash
# In your .env file:
ERROR_NOTIFICATION_BACKEND=webhook
WEBHOOK_URL=https://your-webhook-endpoint.com/notifications
```

Webhook receives JSON POST with error details:
```json
{
  "error": {"summary": "...", "type": "...", "severity": "ERROR"},
  "request": {"id": "...", "endpoint": "...", "timestamp": "..."},
  "affected": {"user_id": "...", "company_id": "..."},
  "context": {"recent_operations": [...], "stack_trace_preview": "..."}
}
```

**Option 2: Slack (Incoming Webhooks)**
```bash
# In your .env file:
ERROR_NOTIFICATION_BACKEND=slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

1. Create Slack Incoming Webhook:
   - Go to https://api.slack.com/messaging/webhooks
   - Create webhook for your workspace
   - Copy webhook URL
2. Notifications sent as rich Slack Block Kit messages with color coding

**Option 3: Email (SMTP)**
```bash
# In your .env file:
ERROR_NOTIFICATION_BACKEND=email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
ADMIN_EMAIL=admin@your-domain.com
```

**Gmail SMTP Setup:**
1. Enable 2-factor authentication on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password as `SMTP_PASSWORD`

**SendGrid SMTP Setup:**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

**What Gets Notified:**

Notifications are triggered for:
- **5xx Server Errors** - Unhandled exceptions, database failures
- **ERROR Severity** - Critical application errors
- Includes request context (user, company, endpoint)
- Includes last 3 operations from rolling context buffer
- Includes stack trace preview (first 500 chars)

**Deduplication:**
- Duplicate errors within 5-minute window are suppressed
- Notification includes count of suppressed duplicates
- Cache size: 100 unique errors (LRU eviction)

**Graceful Failure:**
- Notification delivery failures never block error handling
- Failed notifications logged as warnings
- API continues normally if backend is misconfigured

**Health Check:**
- Admin endpoint: `GET /api/debug/notification-health`
- Test notifications: `POST /api/debug/test-notification`
- Requires admin authentication

**Disable Notifications:**
```bash
# Default - no notifications sent
ERROR_NOTIFICATION_BACKEND=none
```

**Troubleshooting:**

**Notifications not arriving?**
- Check `ERROR_NOTIFICATION_BACKEND` is set correctly
- Verify backend-specific credentials (webhook URL, SMTP password)
- Test notification: `curl -X POST http://localhost:5055/api/debug/test-notification` (requires admin auth)
- Check API logs for notification delivery warnings

**Webhook failures?**
- Verify webhook endpoint is reachable from API server
- Check webhook endpoint accepts JSON POST
- Notification retries 4 times with exponential backoff

**Email failures?**
- Verify SMTP credentials and server settings
- Check firewall allows outbound SMTP connections
- Gmail: Use App Password, not regular password
- Check spam folder if emails not in inbox

**Too many notifications?**
- Deduplication active (5-minute window)
- Consider filtering by error type in your backend
- Review application logs to fix root cause

---

## Environment Variables by Use Case

### Minimal Setup (Cloud Provider)
```
OPENAI_API_KEY (or ANTHROPIC_API_KEY, etc.)
```

### Local Development (Ollama)
```
OLLAMA_API_BASE=http://localhost:11434
```

### Production (OpenAI + Custom Domain)
```
OPENAI_API_KEY=sk-proj-...
API_URL=https://mynotebook.example.com
SURREAL_USER=production_user
SURREAL_PASSWORD=secure_password
```

### Self-Hosted Behind Reverse Proxy
```
OPENAI_COMPATIBLE_BASE_URL=http://localhost:1234/v1
API_URL=https://mynotebook.example.com
```

### High-Performance Deployment
```
OPENAI_API_KEY=sk-proj-...
SURREAL_COMMANDS_MAX_TASKS=10
TTS_BATCH_SIZE=5
API_CLIENT_TIMEOUT=600
```

### Debugging
```
OPENAI_API_KEY=sk-proj-...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
```

---

## Validation

Check if a variable is set:

```bash
# Check single variable
echo $OPENAI_API_KEY

# Check multiple
env | grep -E "OPENAI|API_URL"

# Print all config
env | grep -E "^[A-Z_]+=" | sort
```

---

## Notes

- **Case-sensitive:** `OPENAI_API_KEY` ≠ `openai_api_key`
- **No spaces:** `OPENAI_API_KEY=sk-proj-...` not `OPENAI_API_KEY = sk-proj-...`
- **Quote values:** Use quotes for values with spaces: `API_URL="http://my server:5055"`
- **Restart required:** Changes take effect after restarting services
- **Secrets:** Don't commit API keys to git

---

## Quick Setup Checklist

- [ ] Choose AI provider (OpenAI, Anthropic, Ollama, etc.)
- [ ] Get API key if cloud provider
- [ ] Add to .env or docker.env
- [ ] Set `API_URL` if behind reverse proxy
- [ ] Change `SURREAL_PASSWORD` in production
- [ ] Verify with: `docker compose logs api | grep -i "error"`
- [ ] Test in browser: Go to Settings → Models
- [ ] Try a test chat

Done!
