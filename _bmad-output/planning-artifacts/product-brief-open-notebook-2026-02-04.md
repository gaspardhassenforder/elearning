---
stepsCompleted: [1, 2, 3, 4, 5, 6]
status: complete
inputDocuments:
  - "Verbal overview from user (collaborative discovery)"
  - "Reference: open-notebook codebase (building block, not target product)"
  - "Reference: PRD.md (existing vision document for context)"
date: 2026-02-04
author: Gaspard.hassenforder
---

# Product Brief: open-notebook

## Executive Summary

An AI-native interactive learning platform built for a consulting firm that trains organizations on AI adoption. The platform extends the value of in-person workshops by preparing learners before sessions, reinforcing knowledge after, and providing long-term access to AI-guided learning. At its core is a proactive AI teacher that leads conversations, assesses comprehension through natural dialogue, and generates personalized learning artifacts on the fly. Built on top of the open-notebook open-source project, it serves as both a training tool and a demonstration of the firm's AI capabilities, keeping the company embedded in client organizations long after workshops conclude.

---

## Core Vision

### Problem Statement

Consulting-led AI training workshops are point-in-time events. Significant workshop time is consumed bringing learners to a baseline understanding of AI fundamentals. After the workshop, knowledge decays rapidly with no structured way to revisit or reinforce what was learned. Most critically, learners struggle to internalize AI concepts - they can appreciate impressive use cases but fail to translate that understanding into actionable applications within their own workflows.

### Problem Impact

- **Wasted workshop time**: Consultants spend hours on basics instead of high-value, tailored content
- **Knowledge decay**: Without reinforcement, training ROI diminishes within weeks
- **Internalization failure**: The gap between "I see what AI can do" and "I know how to use AI in my work" remains the biggest barrier to AI adoption
- **Lost business opportunity**: Once the workshop ends, the consulting firm loses its touchpoint with the client organization
- **No visibility**: Consultants have no way to track whether training actually stuck or where learners are struggling

### Why Existing Solutions Fall Short

Current approach is one-time workshops supplemented by static PDFs and slide decks. Traditional e-learning platforms (LMS, MOOCs) offer passive content consumption - videos, readings, and mechanical quizzes. None of these:
- Actively guide learners through a personalized learning journey
- Assess comprehension through natural conversation rather than rigid testing
- Generate learning materials dynamically based on individual needs
- Maintain a persistent, intelligent learning companion that adapts over time
- Serve as a strategic business development tool for the training provider

### Proposed Solution

A two-sided platform built on the open-notebook open-source project:

**For Consultants (Admin):** A modified open-notebook interface where consultants curate modules by selecting documents, generating artifacts (quizzes, podcasts, summaries), and configuring AI teacher prompts. Modules map 1:1 to notebooks. Consultants control which modules are available to which client companies and can phase availability around workshop timelines.

**For Learners:** A minimalist, AI-chatbot-first interface. Upon login, learners complete a brief profiling questionnaire, then access their available modules. Each module features a proactive AI teacher as the primary interaction point, with source documents and artifacts accessible in a side panel. The AI teacher:
- Leads the learning conversation proactively, not reactively
- Assesses comprehension through natural dialogue against a per-module competency checklist
- Generates artifacts on the fly (summaries, podcasts, custom quizzes) based on learner needs
- Falls back to formal quizzes only when natural assessment isn't sufficient
- Surfaces relevant document snippets inline, with full document viewing available on demand

**Phased module availability** supports the consulting engagement lifecycle: foundational modules before the workshop, deeper modules unlocked after.

### Key Differentiators

1. **Proactive AI Teacher** - Not a passive Q&A chatbot but an active learning guide that leads conversations and drives toward learning objectives
2. **Natural Competency Assessment** - Hybrid system that checks off learning objectives through organic dialogue, resorting to formal quizzes only as needed
3. **On-the-fly Artifact Generation** - The AI teacher can create podcasts, summaries, and custom quizzes personalized to the learner's gaps in real-time
4. **Strategic Business Flywheel** - Platform keeps the consulting firm embedded in client organizations, and as learners discover AI possibilities, it generates demand for the firm's AI product services
5. **Built on Proven Open-Source** - Leverages open-notebook's existing artifact generation, RAG, and content processing capabilities, reducing build effort
6. **Subject-Agnostic Architecture** - While initially focused on AI training, the platform is modular enough to teach any subject matter

## Target Users

### Primary Users

#### 1. The Consultant (Admin)

**Profile:** A small team (2-5) of tech-savvy AI consultants who already prepare training materials as part of their consulting practice. They're comfortable with AI tools and familiar with interfaces like open-notebook.

**Name & Context:** *Marc, Senior AI Consultant* - Marc runs AI adoption workshops for corporate clients. He's already created slide decks, compiled PDFs, and gathered resources for his engagements. He needs a platform to package these into interactive, AI-guided learning modules without adding significant prep work.

**Current Workflow:** Marc prepares training materials independently, delivers workshops in person, then leaves clients with PDFs and slides. He has no way to reinforce learning afterward or track whether the training stuck.

**Platform Experience:**
- Uploads existing documents and resources into a module
- Generates artifacts (quizzes, podcasts, summaries) using the platform's AI tools
- Reviews and adjusts the auto-generated learning objectives checklist
- Writes or tweaks the AI teacher's master prompt to set the tone and focus
- Publishes the module
- Assigns modules to specific companies or user profiles via a dashboard
- Has access to an AI chatbot within the admin interface to help with module creation

**Success Moment:** Marc checks his dashboard weeks after a workshop and sees that 80% of learners completed the post-workshop modules, quiz scores are strong, and a client reached out asking about automating a workflow they discovered through the platform.

#### 2. The Learner

**Profile:** Intentionally broad. Learners range across roles (project managers, analysts, executives, operational staff), industries, and AI comfort levels. The platform adapts to them via an onboarding questionnaire and the AI teacher's ability to personalize conversation - the persona is not narrow by design.

**Name & Context:** *Any professional whose organization has engaged the consulting firm for AI training.* They may be curious, skeptical, or anxious about AI. They're fitting this learning around their main job.

**Current Experience:** Attended or will attend an in-person workshop. Before the platform, their only learning materials were static slides and PDFs that gather dust after the session.

**Platform Experience:**
- Receives a link/account from their company
- Logs in, completes a brief profiling questionnaire (AI level, job type)
- Sees available modules - some open now, others locked until after the workshop
- Selects a module and is immediately engaged by a proactive AI teacher
- The AI teacher leads the conversation, surfaces documents and artifacts inline, generates custom content when needed
- Over time, more modules unlock post-workshop
- Returns weeks or months later to revisit concepts, ask new questions, or explore further

**Success Moment:** Months after the workshop, the learner remembers "I can do something with AI for this" - they open the platform, chat with the AI teacher, and within minutes have a concrete approach for their specific workflow.

### Secondary Users

#### The Client Organization Decision-Maker

Not a platform user directly. This is the person (e.g., Head of Innovation, HR Director, CTO) who purchases the consulting engagement. They care about:
- Measurable training outcomes (completion rates, quiz scores)
- Ongoing value for their teams beyond the workshop
- ROI justification for the training investment

They may eventually receive reports or dashboard access, but this is not an MVP concern.

### User Journey

**Learner Journey:**
1. **Discovery** - Receives platform access from their company as part of the consulting engagement
2. **Onboarding** - Logs in, completes questionnaire, sees their module landscape
3. **Pre-Workshop** - Works through foundational modules guided by the AI teacher; arrives at the workshop with baseline AI understanding
4. **Workshop** - In-person sessions with the consultant (off-platform)
5. **Post-Workshop** - New modules unlock; revisits workshop topics with AI-guided depth, explores further
6. **Long-term** - Platform becomes a reference tool and AI learning companion; returns whenever they need to apply AI to a new challenge

**Consultant Journey:**
1. **Module Creation** - Uploads documents, generates artifacts, configures learning objectives and AI teacher prompt
2. **Publishing** - Finalizes module, assigns to client companies/profiles via dashboard
3. **Pre-Workshop** - Foundational modules available to learners; consultant can check engagement
4. **Workshop Delivery** - Off-platform
5. **Post-Workshop** - Unlocks remaining modules for learners
6. **Ongoing** - Monitors learner progress via dashboard; platform keeps the firm visible to the client

## Success Metrics

### User Success Metrics

**Learner Success:**
- **Learning Objectives Completion Rate** - Percentage of learning objectives checked off per module per learner. The AI validates comprehension through natural conversation and, when needed, targeted quizzes. This is the primary measure of whether a learner has absorbed the material.
- **Module Completion** - A module is "complete" when all its learning objectives are checked off for a given learner - not when they finish a quiz or reach the end of content.
- **Platform Return Rate** - Learners returning to the platform after the workshop period, indicating it has become a lasting reference tool rather than a one-time obligation.
- **Pre-Workshop Readiness** - Learners arriving at workshops with foundational modules completed, demonstrable through their learning objectives status.

**Consultant Success:**
- **Learner Adoption Rate** - Percentage of invited learners who actively use the platform (log in, engage with modules, interact with the AI teacher).
- **Pre-Workshop Engagement** - Evidence that learners used the platform before the workshop, resulting in a higher baseline during in-person sessions.
- **Post-Workshop Continued Usage** - Learners continuing to engage with modules after the consulting engagement, confirming lasting value.
- **Ease of Module Creation** - Consultants can go from uploaded documents to published module with minimal friction.

### Business Objectives

- **Client Retention on Platform** - The primary business metric. Clients keep using the platform long after the initial engagement. The platform becomes embedded in how the client organization learns about AI.
- **Inbound Lead Generation** - A natural consequence of platform success, not a forced metric. As learners internalize AI capabilities, they identify use cases that require the consulting firm's AI product services.
- **Client Companies Onboarded** - Number of organizations actively using the platform, indicating market traction.
- **Platform as Proof of Capability** - The platform itself serves as a demonstration of the firm's AI expertise, supporting sales conversations.

### Key Performance Indicators

| KPI | Measurement | Target Signal |
|-----|-------------|---------------|
| Learning objectives completion rate | % of objectives checked off per learner per module | High completion = effective AI teaching |
| Active learner rate | % of invited users who engage with at least 1 module | High adoption = platform is accessible and compelling |
| Pre-workshop module completion | % of learners who complete foundational modules before workshop | Consultants can skip basics in workshops |
| Post-workshop return rate | % of learners who return to platform 30+ days after workshop | Platform has lasting value |
| Long-term platform usage | Learner logins 3+ months after initial engagement | Platform is a reference tool, not a one-time event |
| Module creation efficiency | Consultant time from documents-in to module-published | Low friction admin experience |
| Client company retention | % of client companies with active users after 6 months | The flywheel is working |

## MVP Scope

### Core Features

**Learner Interface:**
- Simple authentication (login)
- Onboarding questionnaire (AI level, job type)
- Module selection screen showing available/locked modules
- AI chatbot teacher as the primary interaction - proactive, guiding, leading the conversation
- Left side panel with browsable sources and artifacts per module
- Inline document snippets in chat with "open full document" action to the side panel
- Learning objectives tracked through natural conversation by the AI teacher, with quiz fallback

**Admin Interface (Modified Open-Notebook):**
- Upload documents and resources into a module (1:1 module-to-notebook mapping)
- Generate artifacts: quizzes, podcasts, summaries, transformations
- Review and edit auto-generated learning objectives checklist
- Write/tweak master prompt for the AI teacher per module
- Publish module
- AI chatbot assistant within admin interface for module creation help

**Module Assignment:**
- Basic dashboard to assign modules to client companies
- Ability to lock/unlock modules (phased availability for pre/post-workshop)

**Authentication:**
- Simple login system for both learner and admin roles

### Out of Scope for MVP

- Progress tracking dashboard for admins (per company, per user analytics)
- Questionnaire-driven module recommendations (learners just see their available modules)
- On-the-fly artifact generation by the AI teacher during learner chat sessions
- Per-profile module assignment within a company (assignment is per company only)
- Decision-maker reporting or ROI dashboards
- Internal consultant training workflows
- SSO/OAuth integration
- Mobile-optimized responsive design

### MVP Success Criteria

- **Consultant can create and publish a module in a single sitting** - The admin workflow from documents-in to module-published is smooth and completable without interruption
- **At least one user can go through a module without encountering errors and is satisfied with the quality of the teaching, material, and platform** - End-to-end learner experience works reliably with good AI teaching quality

### Future Vision

**Near-term (post-MVP):**
- Admin progress tracking dashboard (per company, per user, learning objectives completion status)
- On-the-fly artifact generation by the AI teacher during learner conversations (custom quizzes, podcasts, summaries based on learner gaps)
- Questionnaire-driven module recommendations based on role/profile
- Per-profile module assignment within companies

**Medium-term:**
- Decision-maker reporting and ROI dashboards
- Internal use for consultant upskilling
- Expanded subject matter beyond AI training

**Long-term:**
- SSO/OAuth and enterprise identity integration
- Advanced analytics on learning patterns and AI teaching effectiveness
- Multi-language support
- API for integration with client LMS systems
