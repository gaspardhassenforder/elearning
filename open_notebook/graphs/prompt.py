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


async def assemble_system_prompt(
    notebook_id: str,
    learner_profile: Optional[dict] = None,
    objectives_with_status: Optional[list[dict]] = None,
    context: Optional[str] = None
) -> str:
    """Assemble final system prompt from global + per-module templates.

    This function implements the two-layer prompt system:
    1. Global template (pedagogical principles, always included)
    2. Per-module template (optional customization for topic/industry/tone)

    Called for each learner chat turn to ensure latest objectives status.

    Args:
        notebook_id: Notebook/module record ID
        learner_profile: Dict with 'role', 'ai_familiarity', 'job' (optional)
        objectives_with_status: List of dicts with 'text' and 'status'
        context: Optional context string (available documents, etc.)

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

    # 1. Load and render global template
    global_template_path = Path("prompts/global_teacher_prompt.j2")
    if not global_template_path.exists():
        logger.error(f"Global teacher prompt template not found at {global_template_path}")
        raise FileNotFoundError(f"Global template not found: {global_template_path}")

    with open(global_template_path, "r", encoding="utf-8") as f:
        global_template = f.read()

    global_context = {
        "learner_profile": learner_profile,
        "objectives": objectives_with_status,
        "context": context
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
