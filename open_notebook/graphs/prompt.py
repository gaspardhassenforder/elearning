from typing import Any, Optional

from ai_prompter import Prompter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.utils import extract_text_from_response


class PatternChainState(TypedDict):
    prompt: str
    parser: Optional[Any]
    input_text: str
    output: str


async def call_model(state: dict, config: RunnableConfig) -> dict:
    content = state["input_text"]
    system_prompt = Prompter(
        template_text=state["prompt"], parser=state.get("parser")
    ).render(data=state)
    payload = [SystemMessage(content=system_prompt)] + [HumanMessage(content=content)]
    chain = await provision_langchain_model(
        str(payload),
        config.get("configurable", {}).get("model_id"),
        "transformation",
        max_tokens=5000,
    )

    response = await chain.ainvoke(payload)

    # Extract text from response (handles string, list of content blocks, etc.)
    output_content = extract_text_from_response(response.content)

    return {"output": output_content}


agent_state = StateGraph(PatternChainState)
agent_state.add_node("agent", call_model)  # type: ignore[type-var]
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)

graph = agent_state.compile()


# ==============================================================================
# Story 3.4: AI Teacher Prompt Configuration
# Two-layer prompt system: Global + Per-Module
# ==============================================================================

from pathlib import Path

from jinja2 import Template
from loguru import logger

from open_notebook.domain.module_prompt import ModulePrompt
from open_notebook.domain.quiz import Quiz
from open_notebook.domain.podcast import Podcast
from open_notebook.database.repository import repo_query


async def _load_available_artifacts(notebook_id: str) -> str:
    """Load available artifacts (quizzes and podcasts) for a notebook.

    Story 4.6: Artifacts surfacing in chat.
    Loads all completed quizzes and ready podcasts for the notebook,
    formats them as a list for injection into the global teacher prompt.

    Args:
        notebook_id: Notebook/module record ID

    Returns:
        Formatted string listing available artifacts with IDs,
        or empty string if no artifacts found.
    """
    logger.info(f"Loading available artifacts for notebook {notebook_id}")

    artifacts_text_parts = []

    try:
        # Load quizzes for this notebook
        quiz_query = """
            SELECT id, title, questions_json, created
            FROM quiz
            WHERE notebook_id = $notebook_id
            ORDER BY created DESC
        """
        quiz_results = await repo_query(quiz_query, {"notebook_id": notebook_id})

        if quiz_results:
            artifacts_text_parts.append("**Quizzes:**")
            for quiz_row in quiz_results:
                quiz_id = quiz_row.get("id")
                title = quiz_row.get("title", "Untitled Quiz")
                # Count questions from JSON
                import json
                questions_json = quiz_row.get("questions_json", "[]")
                try:
                    questions = json.loads(questions_json) if questions_json else []
                    question_count = len(questions)
                except (json.JSONDecodeError, TypeError):
                    question_count = 0

                artifacts_text_parts.append(
                    f"  - Quiz: \"{title}\" (ID: {quiz_id}) - {question_count} questions"
                )

        # Load completed podcasts for this notebook
        podcast_query = """
            SELECT id, title, length, speaker_format, status, created
            FROM podcast
            WHERE notebook_id = $notebook_id
              AND status = 'completed'
            ORDER BY created DESC
        """
        podcast_results = await repo_query(podcast_query, {"notebook_id": notebook_id})

        if podcast_results:
            if artifacts_text_parts:
                artifacts_text_parts.append("")  # Blank line between sections
            artifacts_text_parts.append("**Podcasts:**")
            for podcast_row in podcast_results:
                podcast_id = podcast_row.get("id")
                title = podcast_row.get("title", "Untitled Podcast")
                length = podcast_row.get("length", "medium")
                speaker_format = podcast_row.get("speaker_format", "multi")

                # Map length to duration
                duration_map = {"short": 3, "medium": 7, "long": 15}
                duration = duration_map.get(length, 7)

                artifacts_text_parts.append(
                    f"  - Podcast: \"{title}\" (ID: {podcast_id}) - {duration} minutes, {speaker_format}-speaker"
                )

        if artifacts_text_parts:
            logger.info(
                f"Found {len([p for p in artifacts_text_parts if 'Quiz:' in p])} quizzes and "
                f"{len([p for p in artifacts_text_parts if 'Podcast:' in p])} podcasts for notebook {notebook_id}"
            )
            return "\n".join(artifacts_text_parts)
        else:
            logger.debug(f"No artifacts found for notebook {notebook_id}")
            return ""

    except Exception as e:
        logger.error("Error loading artifacts for notebook {}: {}", notebook_id, str(e))
        # Return empty string on error - don't break prompt assembly
        return ""


async def assemble_system_prompt(
    notebook_id: str,
    learner_profile: Optional[dict] = None,
    objectives_with_status: Optional[list[dict]] = None,
    context: Optional[str] = None,
    current_focus_objective: Optional[str] = None,  # Story 4.2: Explicit focus objective
    language: Optional[str] = None,  # UI language code for response language
) -> str:
    """Assemble final system prompt from global + per-module templates.

    This function implements the two-layer prompt system:
    1. Global template (pedagogical principles, always included)
    2. Per-module template (optional customization for topic/industry/tone)

    Called for each learner chat turn to ensure latest objectives status.

    Story 4.2 Enhancement:
    - Determines "current focus objective" (next incomplete objective)
    - Injects focus objective into template for AI guidance
    - Supports conversation state hints for teaching flow

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Dict with 'name', 'role', 'ai_familiarity', 'job_description' (optional)
        objectives_with_status: List of dicts with 'text' and 'status'
        context: Optional context string (available documents, etc.)
        current_focus_objective: Optional explicit focus objective (auto-determined if None)

    Returns:
        Final assembled system prompt string

    Raises:
        FileNotFoundError: If global template file not found
        Exception: If template rendering fails
    """
    logger.info(f"Assembling system prompt for notebook {notebook_id}")

    # Default empty values if not provided
    learner_profile = learner_profile or {}
    objectives_with_status = objectives_with_status or []

    # Story 4.2: Determine current focus objective if not explicitly provided
    if current_focus_objective is None and objectives_with_status:
        # Find first objective that is NOT completed
        for obj in objectives_with_status:
            if obj.get("status") != "completed":
                current_focus_objective = obj.get("text", "")
                logger.info(f"Auto-selected focus objective: {current_focus_objective}")
                break

        # If all completed, focus on first objective (for review/discussion)
        if current_focus_objective is None and objectives_with_status:
            current_focus_objective = objectives_with_status[0].get("text", "")
            logger.info(f"All objectives completed - focusing on first objective for review")

    logger.debug(f"Current focus objective: {current_focus_objective}")

    # 1. Load and render global template
    global_template_path = Path("prompts/global_teacher_prompt.j2")
    if not global_template_path.exists():
        logger.error(f"Global teacher prompt template not found at {global_template_path}")
        raise FileNotFoundError(f"Global template not found: {global_template_path}")

    with open(global_template_path, "r", encoding="utf-8") as f:
        global_template = f.read()

    # Story 4.5: Extract ai_familiarity for adaptive teaching
    ai_familiarity = learner_profile.get("ai_familiarity", "intermediate") if learner_profile else "intermediate"

    # Story 4.6: Load available artifacts (quizzes and podcasts) for surfacing in chat
    artifacts_list = await _load_available_artifacts(notebook_id)

    global_context = {
        "learner_profile": learner_profile,
        "objectives": objectives_with_status,
        "current_focus_objective": current_focus_objective,  # Story 4.2: Focus objective for AI
        "context": context,
        "ai_familiarity": ai_familiarity,  # Story 4.5: For adaptive teaching strategy
        "artifacts_list": artifacts_list  # Story 4.6: Available quizzes and podcasts
    }

    try:
        global_rendered = Template(global_template).render(global_context)
        logger.debug(f"Global template rendered ({len(global_rendered)} chars)")
    except Exception as e:
        logger.error("Failed to render global template: {}", str(e))
        raise

    # 2. Load and render per-module prompt (if exists)
    try:
        module_prompt = await ModulePrompt.get_by_notebook(notebook_id)
    except Exception as e:
        logger.error("Error loading module prompt for {}: {}", notebook_id, str(e))
        # Continue with global-only if module prompt fetch fails
        module_prompt = None

    if module_prompt and module_prompt.system_prompt:
        logger.info(f"Found per-module prompt for notebook {notebook_id}")
        try:
            # Render module template with same context (can reference variables)
            module_rendered = Template(module_prompt.system_prompt).render(global_context)
            logger.debug(f"Module template rendered ({len(module_rendered)} chars)")

            # Merge: global + separator + module
            final_prompt = f"{global_rendered}\n\n---\n\n# MODULE-SPECIFIC CUSTOMIZATION\n\n{module_rendered}"
            logger.info(f"Assembled final prompt: {len(final_prompt)} chars (global + module)")
        except Exception as e:
            logger.error("Failed to render module template: {}", str(e))
            # Fall back to global-only if module rendering fails
            final_prompt = global_rendered
            logger.warning("Falling back to global-only prompt due to module template error")
    else:
        # Admin left prompt empty or prompt doesn't exist → use global only
        if module_prompt:
            logger.info(f"Module prompt exists but system_prompt is None - using global only")
        else:
            logger.info(f"No module prompt configured for notebook {notebook_id} - using global only")
        final_prompt = global_rendered

    # Append language instruction if specified
    if language and language != "en-US":
        language_map = {
            "fr-FR": "French (Français)",
            "pt-BR": "Brazilian Portuguese (Português)",
            "zh-CN": "Simplified Chinese (简体中文)",
            "zh-TW": "Traditional Chinese (繁體中文)",
        }
        language_name = language_map.get(language, language)
        language_instruction = (
            f"\n\n# RESPONSE LANGUAGE\n\n"
            f"IMPORTANT: You MUST respond in {language_name}. "
            f"All your messages, questions, feedback, and guidance should be in {language_name}. "
            f"Only use English for technical terms that have no common translation."
        )
        final_prompt += language_instruction
        logger.info(f"Added language instruction for {language_name}")

    return final_prompt


async def get_default_template() -> str:
    """Get default per-module prompt template for pre-population.

    Returns a starter template that admins can customize. Demonstrates
    available Jinja2 variables and provides guidance on customization.

    Returns:
        Default template string with explanatory comments
    """
    return """# Module-Specific Teaching Focus

Focus this module on [TOPIC/INDUSTRY - e.g., "AI applications in logistics"].
The learners are [ROLE/AUDIENCE - e.g., "supply chain managers"].

## Teaching Approach
[Describe desired teaching style - e.g., "Keep explanations concrete with real-world examples"]

## Emphasis Areas
- [Area 1 - e.g., "Warehouse automation"]
- [Area 2 - e.g., "Predictive shipping optimization"]
- [Area 3 - e.g., "Inventory forecasting"]

## Specific Examples to Reference
{% if context %}
When appropriate, reference these real-world applications:
- [Example 1 - e.g., "Amazon's fulfillment center automation"]
- [Example 2 - e.g., "DHL's predictive shipping"]
{% endif %}

## Tone & Language
[Describe desired tone - e.g., "Professional but approachable, avoid overly technical jargon"]

---

**Available Template Variables:**
- `learner_profile.role` - Learner's job role
- `learner_profile.ai_familiarity` - AI experience level
- `objectives` - List of learning objectives with status
- `context` - Available source documents

**Example Usage:**
```
{% if learner_profile.ai_familiarity == "beginner" %}
Avoid technical AI terminology unless explaining it.
{% endif %}
```
"""


# ==============================================================================
# Story 4.8: Persistent Chat History & Re-engagement Messages
# ==============================================================================


async def generate_re_engagement_greeting(
    thread_id: str,
    learner_profile: dict,
    objectives_with_status: list[dict],
    notebook_id: str,
    language: str = "en-US",
) -> str:
    """Generate contextual welcome-back message for returning learners.

    Story 4.8: Re-engagement message generation.
    Analyzes recent conversation history from checkpoint to generate a personalized
    greeting that references previous topics discussed and learning progress.

    Args:
        thread_id: Thread ID for checkpoint lookup
        learner_profile: Dict with 'name', 'role', 'job_description' (optional)
        objectives_with_status: List of dicts with 'text' and 'status' for progress context
        notebook_id: Notebook/module record ID for context

    Returns:
        Contextual greeting string (under 3 sentences)

    Example Output:
        "Welcome back! Last time we were discussing AI applications in project management,
        and you had great insights on automation. Ready to continue, or would you like
        to explore a different application?"
    """
    logger.info(f"Generating re-engagement greeting for thread {thread_id}")

    # Import async memory getter to avoid circular dependency
    from open_notebook.graphs.chat import get_async_memory

    # Load checkpoint history
    try:
        config = {"configurable": {"thread_id": thread_id}}
        async_memory = await get_async_memory()
        checkpoint_tuple = await async_memory.aget(config)

        if not checkpoint_tuple:
            logger.warning(f"No checkpoint found for thread {thread_id}, falling back to standard greeting")
            # Fallback to standard greeting from Story 4.2
            return await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                objectives_with_status=objectives_with_status
            )

        # Extract messages from checkpoint (SqliteSaver returns dict directly)
        if not isinstance(checkpoint_tuple, dict):
            logger.error(f"Unexpected checkpoint type: {type(checkpoint_tuple)}")
            # Fallback to standard greeting on unexpected format
            return await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                objectives_with_status=objectives_with_status
            )

        # SqliteSaver structure: {"channel_values": {"messages": [...]}}
        if "channel_values" in checkpoint_tuple and "messages" in checkpoint_tuple["channel_values"]:
            messages = checkpoint_tuple["channel_values"]["messages"]
        else:
            messages = checkpoint_tuple.get("messages", [])

        if not messages:
            logger.warning(f"Empty message history for thread {thread_id}, falling back to standard greeting")
            return await generate_proactive_greeting(
                notebook_id=notebook_id,
                learner_profile=learner_profile,
                objectives_with_status=objectives_with_status
            )

        # Get last 3-5 messages for topic analysis
        recent_messages = messages[-5:] if len(messages) >= 5 else messages

        # Extract conversation topics from recent messages
        conversation_summary = await _analyze_conversation_topics(recent_messages)

        # Count completed objectives for progress context
        completed_count = sum(1 for obj in objectives_with_status if obj.get("status") == "completed")
        total_count = len(objectives_with_status)

        # Generate re-engagement prompt
        learner_name = learner_profile.get("name", "there")
        learner_role = learner_profile.get("role", "")

        # Language instruction for non-English greetings
        language_names = {
            "fr-FR": "French (Français)",
            "en-US": "English",
            "pt-BR": "Brazilian Portuguese (Português)",
            "zh-CN": "Simplified Chinese (简体中文)",
            "zh-TW": "Traditional Chinese (繁體中文)",
        }
        language_display = language_names.get(language, "English")
        language_instruction = f"\n6. IMPORTANT: You MUST respond in {language_display}." if language != "en-US" else ""

        prompt_template = """Generate a warm, personalized welcome-back message for a returning learner.

**Learner Context:**
- Name: {{ learner_name }}
- Role: {{ learner_role }}
- Learning progress: {{ completed_count }}/{{ total_count }} objectives completed

**Previous Conversation:**
{{ conversation_summary }}

**Guidelines:**
1. Reference specific topic from last conversation (be concrete, not generic)
2. Acknowledge their progress made (if progress > 0)
3. Invite them to continue OR shift focus (give them agency)
4. Keep under 3 sentences, conversational and warm tone
5. Use their name once at the beginning{{ language_instruction }}

**Examples of good re-engagement messages:**
- "Welcome back, Alice! Last time we were discussing AI applications in logistics, specifically around predictive shipping. You had some great insights on automation. Ready to continue where we left off?"
- "Hi again, Bob! We were talking about natural language processing for meeting notes last session. You've completed 5 of 12 objectives so far—nice progress! Want to dive deeper into NLP, or explore something new?"
- "Great to see you back! Last time we covered the basics of neural networks, and you seemed particularly interested in image recognition. Ready to continue?"

Now generate the welcome-back message:
"""

        prompt_context = {
            "learner_name": learner_name,
            "learner_role": learner_role,
            "completed_count": completed_count,
            "total_count": total_count,
            "conversation_summary": conversation_summary,
            "language_instruction": language_instruction,
        }

        rendered_prompt = Template(prompt_template).render(prompt_context)

        # Use fast small model for cost optimization (re-engagement greeting doesn't need premium model)
        model = await provision_langchain_model(
            rendered_prompt,
            model_name="gpt-4o-mini",  # Fast, cheap for greetings
            model_type="chat",
            max_tokens=150,  # Keep it short
        )

        response = await model.ainvoke([SystemMessage(content=rendered_prompt)])

        # Extract greeting text from response
        greeting = extract_text_from_response(response.content)

        logger.info(f"Generated re-engagement greeting ({len(greeting)} chars)")
        return greeting.strip()

    except Exception as e:
        logger.error("Error generating re-engagement greeting: {}", str(e), exc_info=True)
        # Fallback to standard greeting on error
        logger.warning("Falling back to standard greeting due to error")
        return await generate_proactive_greeting(
            notebook_id=notebook_id,
            learner_profile=learner_profile,
            objectives_with_status=objectives_with_status
        )


async def _analyze_conversation_topics(messages: list) -> str:
    """Extract main topics/concepts discussed from recent conversation messages.

    Analyzes message content to identify key topics for re-engagement context.

    Args:
        messages: List of LangChain message objects (HumanMessage, AIMessage)

    Returns:
        Summary string of discussed topics (1-2 sentences)
    """
    logger.debug(f"Analyzing {len(messages)} messages for conversation topics")

    # Extract text content from messages
    message_texts = []
    for msg in messages:
        if hasattr(msg, "content"):
            content = msg.content
            # Handle structured content (list of content blocks)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                content = " ".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)

            message_texts.append(content)

    if not message_texts:
        return "general discussion about the module content"

    # Join recent messages for topic extraction
    conversation_text = "\n\n".join(message_texts[-3:])  # Last 3 messages most relevant

    # Use fast model for topic extraction (optimization)
    extraction_prompt = f"""Analyze this conversation and extract the main topic in 1-2 sentences.
Be specific about what concepts or applications were discussed.

Conversation excerpt:
{conversation_text}

Topic summary (1-2 sentences):"""

    try:
        model = await provision_langchain_model(
            extraction_prompt,
            model_name="gpt-4o-mini",
            model_type="chat",
            max_tokens=100,
        )

        response = await model.ainvoke([SystemMessage(content=extraction_prompt)])
        topic_summary = extract_text_from_response(response.content).strip()

        logger.debug(f"Extracted topic summary: {topic_summary}")
        return topic_summary

    except Exception as e:
        logger.error("Error extracting conversation topics: {}", str(e))
        # Fallback to generic summary
        return "discussing the module content and learning objectives"


async def generate_proactive_greeting(
    notebook_id: str,
    learner_profile: dict,
    objectives_with_status: list[dict],
) -> str:
    """Generate proactive greeting for first-time visitors.

    Story 4.2: Original greeting generation for new conversations.
    Used as fallback if re-engagement greeting generation fails.

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Dict with 'name', 'role', 'job_description'
        objectives_with_status: List of dicts with 'text' and 'status'

    Returns:
        Personalized greeting string introducing the module
    """
    logger.info(f"Generating proactive greeting for notebook {notebook_id}")

    learner_name = learner_profile.get("name", "there")
    learner_role = learner_profile.get("role", "your role")

    # Get first 3 objectives as preview
    preview_objectives = objectives_with_status[:3] if objectives_with_status else []
    objectives_preview = "\n".join([f"- {obj.get('text', '')}" for obj in preview_objectives])

    greeting_template = """Hi {{ learner_name }}! I'm your AI teaching assistant for this module.

I see you're {{ learner_role }}. We'll be exploring these learning objectives together:

{{ objectives_preview }}

I'm here to guide you through the material, answer questions, and help you apply these concepts to your work. Feel free to ask anything!

Where would you like to start?"""

    context = {
        "learner_name": learner_name,
        "learner_role": learner_role,
        "objectives_preview": objectives_preview if objectives_preview else "the module content"
    }

    greeting = Template(greeting_template).render(context)
    logger.debug(f"Generated proactive greeting ({len(greeting)} chars)")

    return greeting.strip()
