# Potential Improvements — Product Feedback Synthesis

Captured from stakeholder feedback session (2026-02-26) + architectural review (2026-03-04).

---

## AI Teacher — Remaining Work

The AI Teacher Refactor sprint is largely complete. Items 1–5 are done. Item 6 remains.

### ✅ Done
1. **Remove mandatory RAG directive** — Prompt no longer forces search on every turn
2. **Radically simplified system prompt** — Cut from ~600 lines to ~150 lines
3. **Unified greeting into main chat flow** — `stream_proactive_greeting`, `generate_re_engagement_greeting` removed; hidden HumanMessage triggers natural greeting
4. **Fix quick replies language** — `language` param now passed to quick replies LLM call
5. **Better LangSmith trace naming** — ContextLoggingCallback handles non-dict inputs/outputs

### 🔜 Remaining

#### 6. Lesson Plan as the Conversation Driver (Medium Effort, Core Product Value)

The lesson plan is injected into the prompt and the current step is identified. The next step is making it actually drive the conversation:

- The system prompt tells the AI: "Your current job is to guide the learner through [current_step]. Call `surface_document` with the source, then discuss it."
- The AI opens the conversation by presenting the current step, not by "greeting" in the generic sense
- When the learner completes a step, the step is marked done and the next step becomes `current`
- The AI naturally transitions: "Great. Now let's look at..."

This is the structural enforcement from the product feedback — achieved through the existing LangGraph + lesson plan infrastructure, not by building a separate gating system.

---

## Previous Stakeholder Feedback (2026-02-26)

### 1. Videos as a Source Type

Add video as a first-class source type alongside PDFs and URLs. Learners should be able to watch embedded videos directly within the platform. Videos (like other sources) could be:
- Uploaded directly
- Linked from external platforms (YouTube, Vimeo, etc.)

The critical shift: **watching a video becomes a required step**, not optional enrichment.

---

### 2. Mandatory Content Consumption Before Free Interaction

When a learner opens a module, they are presented with a structured checklist of required content:
- Videos to watch
- Documents to read
- Any other obligatory sources

**Option B — Chatbot as enforcer (preferred)**: The chatbot is the interface from the start, but it actively directs the learner: "Before we continue, watch this video. Once you've done that, come back and we'll discuss it." The chatbot only moves forward once the learner has confirmed consumption.

This is directly enabled by the lesson plan + refactored AI teacher (item 6 above).

---

### 3. Proactive, Directive Chatbot

The AI guide needs to **lead the session**, not respond to it:
- "Start by reading section 2 of this document."
- "Watch the first video before we continue."
- "Now that you've seen that, here's what I want you to think about."

The chatbot should drive the learning sequence. Learner questions are welcome and the bot should answer them, but the default flow is chatbot-led.

This is what the simplified prompt + lesson plan achieves (item 6 above).

---

### 4. ✅ Dynamic Quick-Reply Buttons After Every Message

Already implemented. Language bug fixed.

---

### 5. Mini-Quizzes After Each Resource (or Group of Resources)

Rather than a single quiz at the end of a module, introduce **checkpoint quizzes** after each resource or logical group of resources. This:
- Confirms the learner actually absorbed the content
- Gives the admin signal on where learners are struggling
- Makes the experience feel more like a real course

The quiz can be short (2–3 questions) and generated automatically from the source content using the existing LangGraph quiz workflow.

---

### 6. Admin Content Creation — Minimal Effort, Maximum Output

Admins should be able to build a full module by just dropping in raw resources (links, files, videos). The platform handles the rest:

- **Ingest a URL** → extract content, generate lesson structure
- **Upload a PDF** → extract text, create key points, generate quiz questions
- **Add a video link** → index transcript (if available), flag as required viewing

Admins can optionally define the high-level learning objectives and the rough flow, but they should not need to write any text content themselves. The AI generates:
- Module overview
- Key takeaways per source
- Discussion prompts for the chatbot
- Quiz questions
- Podcast summary (already partially built)

The admin role becomes **curator and flow designer**, not content writer.

#### Proposed Solution: MCP Server + Claude Code as Admin Agent

Rather than building a custom ingestion agent, expose platform capabilities as an MCP server and let Claude Code act as the orchestrator. This gives us a capable, maintained deep agent for free.

**Architecture:**

```
Admin gives Claude Code a goal:
  "Here's this tutorial website. Build a module from it."

Claude Code (agent):
  1. Scrapes pages, detects embedded videos, finds linked PDFs
  2. Downloads videos locally via yt-dlp (bash)
  3. Calls MCP tools to upload sources and create the module
  4. Polls job status until transcription/embedding is done
  5. Reviews the assembled sources and suggests a lesson plan
  6. Waits for human approval before publishing

Platform MCP Server (thin API wrapper):
  - Source tools: create_source_from_url, create_source_from_file, get_job_status
  - Module tools: create_notebook, add_source_to_notebook, get_notebook
  - Lesson plan tools: get_lesson_plan, suggest_lesson_plan, publish_notebook
```

**Key design decisions:**

- **MCP stays thin** — no orchestration logic in the tools; Claude reasons about the flow
- **Sources are flat** — a complex website becomes N individual sources (one per page/video), not a nested hierarchy; a `origin_url` metadata field is sufficient to track provenance
- **Async jobs need polling** — `create_source_from_file` returns a `job_id`; Claude polls `get_job_status` until transcription/embedding completes before moving on
- **Publish is always manual** — Claude prepares everything but never publishes autonomously; admin reviews and confirms
- **Resumable sessions** — MCP tools are stateless; if a Claude session drops mid-crawl, a new session can call `list_sources(notebook_id)` to see what was already imported and continue

**Why this beats a custom agent:**
- Claude's web browsing, bash execution, and reasoning come for free
- Failure recovery and edge case handling are Claude's problem, not ours
- We maintain a clean API surface (~10 tools) instead of a fragile bespoke crawler
- The same MCP could later be used by other AI tools or automation pipelines

**Open questions:**
- Where do downloaded video files land temporarily before upload? (temp storage on API server vs. direct stream)
- Should `create_source_from_file` block until transcription is done, or always return a job_id?
- Auth: admin JWT passed as MCP config, not per-call — is that acceptable?

---

### 7. Video Generation via NotebookLM (or Similar)

Creating original video content is complex. A pragmatic shortcut:
- Use **Google NotebookLM** (or its API/MCP if available) to generate audio deep-dives from source material
- Download the resulting audio or video and store it as a generated artifact in the platform
- Present it to learners as a "generated podcast" or "overview video"

This leverages an existing high-quality external tool without us building video synthesis from scratch.

---

## Open Questions / Design Decisions

- **How strict is "mandatory"?** Can admins mark some content as optional? Can learners skip with a warning?
- **Progress tracking** — do we need a visible progress bar or checklist UI for learners?
- **NotebookLM integration** — is the MCP available and reliable enough? What's the fallback?
- **Mini-quiz timing** — after every single source, or after logical sections defined by the admin?
- **Video playback tracking** — do we detect whether a video was actually watched (e.g. completion event) or trust the learner's self-report?
- **Examiner efficiency** — should the examiner also run on shorter messages? Currently skipped if < 20 chars.

---

## Summary

The platform has strong building blocks. The AI teacher refactor is complete — the orchestration is now leaner and more natural. The next major step is **lesson plan as conversation driver** (item 6 in AI Teacher section), which enables mandatory content consumption and directive chatbot behavior.
