"""Learning objectives generation workflow using LangGraph.

Story 3.3: Learning Objectives Configuration

This workflow generates measurable learning objectives from notebook sources
using AI analysis. It follows a 3-node pattern:
1. analyze_sources: Extract content summary from sources
2. generate_objectives: LLM generates 3-5 objectives with structured output
3. save_objectives: Persist to database with auto_generated=true
"""

from typing import Literal, Optional, TypedDict

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.notebook import Notebook
from open_notebook.utils import clean_thinking_content


class ObjectiveGenerationState(TypedDict):
    """State for learning objectives generation workflow."""

    notebook_id: str
    num_objectives: Optional[int]  # Default 4 if not specified
    sources_summary: Optional[str]
    generated_objectives: list[dict]
    objective_ids: list[str]
    error: Optional[str]
    status: Literal["pending", "analyzing", "generating", "saving", "completed", "failed"]


class GeneratedObjectives(BaseModel):
    """Structured output from LLM for learning objectives."""

    objectives: list[str] = Field(
        description="List of 3-5 measurable learning objectives using action verbs"
    )


async def analyze_sources(state: ObjectiveGenerationState) -> dict:
    """Build summary from notebook sources for LLM context.

    Extracts titles and excerpts from notebook sources to provide
    content overview for objective generation.

    Args:
        state: Workflow state with notebook_id

    Returns:
        Dict with sources_summary and status update
    """
    logger.info(f"Analyzing sources for notebook {state['notebook_id']}")

    try:
        # Load notebook
        notebook = await Notebook.get(state["notebook_id"])
        if not notebook:
            return {
                "error": f"Notebook {state['notebook_id']} not found",
                "status": "failed",
            }

        # Load sources
        sources = await notebook.get_sources()
        if not sources:
            return {
                "error": "No sources found in notebook",
                "status": "failed",
            }

        logger.info(f"Found {len(sources)} sources for objective generation")

        # Build concise summary (titles + excerpts)
        # Limit to first 10 sources to keep prompt size manageable
        summary_parts = []
        for idx, source in enumerate(sources[:10], 1):
            # Get first 200 chars of content as excerpt
            excerpt = source.full_text[:200] if source.full_text else "(no content)"
            summary_parts.append(f"{idx}. {source.title}: {excerpt}...")

        sources_summary = "\n".join(summary_parts)

        logger.info(f"Generated sources summary ({len(sources_summary)} chars)")

        return {
            "sources_summary": sources_summary,
            "status": "generating",
        }

    except Exception as e:
        logger.error(f"Error analyzing sources: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to analyze sources: {str(e)}",
            "status": "failed",
        }


async def generate_objectives(state: ObjectiveGenerationState) -> dict:
    """Generate learning objectives using LLM with structured output.

    Uses PydanticOutputParser to ensure reliable JSON extraction.
    Generates 3-5 measurable objectives with action verbs.

    Args:
        state: Workflow state with sources_summary

    Returns:
        Dict with generated_objectives list and status update
    """
    if state.get("error"):
        return {}

    logger.info("Generating learning objectives with LLM")

    try:
        # Setup parser for structured output
        parser = PydanticOutputParser(pydantic_object=GeneratedObjectives)

        # Render prompt template
        prompter = Prompter(
            prompt_template="learning_objectives/generate.jinja",
            parser=parser
        )

        num_objectives = state.get("num_objectives", 4)

        system_prompt = prompter.render(data={
            "sources_summary": state["sources_summary"],
            "num_objectives": num_objectives
        })

        # Provision model with structured output support
        model = await provision_langchain_model(
            content=system_prompt,
            model_id=None,
            default_type="default",
            max_tokens=2000,
            structured=dict(type="json"),
        )

        # Invoke LLM
        ai_message = await model.ainvoke(system_prompt)

        # Clean thinking content (<think>...</think> tags)
        message_content = (
            ai_message.content
            if isinstance(ai_message.content, str)
            else str(ai_message.content)
        )
        cleaned_content = clean_thinking_content(message_content)

        # Parse structured output
        result = parser.parse(cleaned_content)

        logger.info(f"Generated {len(result.objectives)} learning objectives")

        # Format objectives with order and auto_generated flag
        objectives_list = [
            {
                "text": obj,
                "order": idx,
                "auto_generated": True
            }
            for idx, obj in enumerate(result.objectives)
        ]

        return {
            "generated_objectives": objectives_list,
            "status": "saving",
        }

    except Exception as e:
        logger.error(f"Error generating objectives: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to generate objectives: {str(e)}",
            "status": "failed",
        }


async def save_objectives(state: ObjectiveGenerationState) -> dict:
    """Save generated objectives to database.

    Creates LearningObjective records with auto_generated=True.

    Args:
        state: Workflow state with generated_objectives and notebook_id

    Returns:
        Dict with objective_ids list and status update
    """
    if state.get("error"):
        return {}

    logger.info(f"Saving {len(state['generated_objectives'])} objectives to database")

    try:
        objective_ids = []

        for obj_data in state["generated_objectives"]:
            objective = LearningObjective(
                notebook_id=state["notebook_id"],
                text=obj_data["text"],
                order=obj_data["order"],
                auto_generated=True
            )
            await objective.save()
            objective_ids.append(objective.id)

            logger.debug(f"Saved objective: {obj_data['text'][:50]}...")

        logger.info(f"Successfully saved {len(objective_ids)} learning objectives")

        return {
            "objective_ids": objective_ids,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Error saving objectives: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to save objectives: {str(e)}",
            "status": "failed",
        }


# Build the workflow graph
workflow = StateGraph(ObjectiveGenerationState)

# Add nodes
workflow.add_node("analyze_sources", analyze_sources)
workflow.add_node("generate_objectives", generate_objectives)
workflow.add_node("save_objectives", save_objectives)

# Define edges
workflow.set_entry_point("analyze_sources")
workflow.add_edge("analyze_sources", "generate_objectives")
workflow.add_edge("generate_objectives", "save_objectives")
workflow.add_edge("save_objectives", END)

# Compile graph
objectives_generation_graph = workflow.compile()
