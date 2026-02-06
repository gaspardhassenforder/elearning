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
            SELECT id, title, questions_json
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
            SELECT id, title, length, speaker_format, status
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
        logger.error(f"Error loading artifacts for notebook {notebook_id}: {e}")
        # Return empty string on error - don't break prompt assembly
        return ""


async def assemble_system_prompt(
    notebook_id: str,
    learner_profile: Optional[dict] = None,
    objectives_with_status: Optional[list[dict]] = None,
    context: Optional[str] = None,
    current_focus_objective: Optional[str] = None  # Story 4.2: Explicit focus objective
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
        learner_profile: Dict with 'role', 'ai_familiarity', 'job' (optional)
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
        logger.error(f"Failed to render global template: {e}")
        raise

    # 2. Load and render per-module prompt (if exists)
    try:
        module_prompt = await ModulePrompt.get_by_notebook(notebook_id)
    except Exception as e:
        logger.error(f"Error loading module prompt for {notebook_id}: {e}")
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
            logger.error(f"Failed to render module template: {e}")
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
