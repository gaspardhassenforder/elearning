"""Learning objectives generation workflow using LangGraph.

Per-source/per-artifact architecture:
1. analyze_all_content: Analyze each source and artifact individually (with caching)
2. aggregate_objectives: Synthesize global objectives with provenance tracking
3. save_objectives: Persist to database with source_refs
"""

from typing import Literal, Optional, TypedDict

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.database.repository import repo_query
from open_notebook.domain.content_analysis import ContentAnalysis
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.notebook import Notebook
from open_notebook.utils import clean_thinking_content, extract_text_from_response


# --- Structured output models ---


class ContentAnalysisOutput(BaseModel):
    """Structured output from LLM for per-content analysis."""

    summary: str = Field(description="2-3 sentence summary of the content")
    objectives: list[str] = Field(
        description="2-4 specific learning objectives from this content"
    )


class AggregatedObjective(BaseModel):
    """Single synthesized learning objective with provenance."""

    text: str = Field(description="Learning objective text")
    source_refs: list[str] = Field(
        description="Content IDs supporting this objective (e.g., source:abc, quiz:xyz)"
    )


class AggregatedObjectives(BaseModel):
    """Structured output from LLM for aggregated objectives."""

    objectives: list[AggregatedObjective] = Field(
        description="Synthesized learning objectives with provenance"
    )


# --- State ---


class ObjectiveGenerationState(TypedDict):
    """State for learning objectives generation workflow."""

    notebook_id: str
    num_objectives: Optional[int]
    content_analyses: list[dict]
    generated_objectives: list[dict]
    objective_ids: list[str]
    error: Optional[str]
    status: Literal[
        "pending", "analyzing", "generating", "saving", "completed", "failed"
    ]


# --- Helper functions ---


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3].rstrip()
    return stripped


def _extract_quiz_text(quiz) -> str:
    """Extract text content from a Quiz for analysis."""
    parts = []
    for q in quiz.questions:
        part = q.question
        if q.options:
            part += " Options: " + ", ".join(q.options)
        if q.explanation:
            part += f" ({q.explanation})"
        parts.append(part)
    return "\n".join(parts)


async def _analyze_single_content(
    content_id: str,
    content_type: str,
    title: str,
    text: str,
) -> dict:
    """Analyze a single piece of content with LLM and cache the result.

    Checks cache first. On miss, calls LLM and saves ContentAnalysis.

    Returns:
        Dict with content_id, content_type, title, summary, objectives
    """
    # Cache check
    cached = await ContentAnalysis.get_for_content(content_id)
    if cached:
        logger.info(f"Cache hit for {content_id}")
        return {
            "content_id": cached.content_id,
            "content_type": cached.content_type,
            "title": title,
            "summary": cached.summary,
            "objectives": cached.objectives,
        }

    logger.info(f"Cache miss for {content_id}, calling LLM")

    # Truncate content for prompt
    truncated_text = text[:3000] if text else "(no content)"

    # Setup parser
    parser = PydanticOutputParser(pydantic_object=ContentAnalysisOutput)

    # Render prompt
    prompter = Prompter(
        prompt_template="learning_objectives/analyze_content.jinja",
        parser=parser,
    )
    prompt = prompter.render(
        data={
            "content_type": content_type,
            "title": title,
            "content": truncated_text,
        }
    )

    # Provision model
    model = await provision_langchain_model(
        content=prompt,
        model_id=None,
        default_type="default",
        max_tokens=1000,
        structured=dict(type="json"),
    )

    # Call LLM
    ai_message = await model.ainvoke(prompt)
    message_content = extract_text_from_response(ai_message.content)
    cleaned = clean_thinking_content(message_content)
    cleaned = _strip_code_fences(cleaned)

    # Parse
    result = parser.parse(cleaned)

    # Save to cache
    analysis = ContentAnalysis(
        content_id=content_id,
        content_type=content_type,
        summary=result.summary,
        objectives=result.objectives,
    )
    await analysis.save()
    logger.info(f"Cached analysis for {content_id}")

    return {
        "content_id": content_id,
        "content_type": content_type,
        "title": title,
        "summary": result.summary,
        "objectives": result.objectives,
    }


# --- Workflow nodes ---


async def analyze_all_content(state: ObjectiveGenerationState) -> dict:
    """Analyze each source and artifact individually.

    For each content item:
    - Check ContentAnalysis cache (skip LLM if cached)
    - On cache miss: call LLM with analyze_content.jinja, save result
    - Collect all analyses into state

    Args:
        state: Workflow state with notebook_id

    Returns:
        Dict with content_analyses list and status update
    """
    logger.info(f"Analyzing all content for notebook {state['notebook_id']}")

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
        analyses = []

        # Analyze each source
        # Note: get_sources() omits full_text, so we re-fetch each source
        for source in sources:
            try:
                from open_notebook.domain.notebook import Source

                full_source = await Source.get(source.id)
                text = full_source.full_text or ""
            except Exception:
                text = ""

            if not text:
                logger.warning(f"Source {source.id} has no text, skipping")
                continue

            analysis = await _analyze_single_content(
                content_id=source.id,
                content_type="source",
                title=source.title or "Untitled Source",
                text=text,
            )
            analyses.append(analysis)

        # Load artifacts for this notebook
        from open_notebook.database.repository import ensure_record_id

        artifact_records = await repo_query(
            """
            SELECT * FROM artifact
            WHERE notebook_id = $notebook_id
            ORDER BY created DESC
            """,
            {"notebook_id": ensure_record_id(state["notebook_id"])},
        )

        if artifact_records:
            for artifact_record in artifact_records:
                artifact_type = artifact_record.get("artifact_type")
                artifact_id = artifact_record.get("artifact_id")
                artifact_title = artifact_record.get("title", "Untitled")

                if not artifact_id:
                    continue

                # Skip job IDs (command:xxx)
                if isinstance(artifact_id, str) and artifact_id.startswith("command:"):
                    continue

                try:
                    text = ""
                    if artifact_type == "quiz":
                        from open_notebook.domain.quiz import Quiz

                        quiz = await Quiz.get(artifact_id)
                        text = _extract_quiz_text(quiz)
                    elif artifact_type == "podcast":
                        from open_notebook.podcasts.models import PodcastEpisode

                        podcast = await PodcastEpisode.get(artifact_id)
                        if podcast.transcript:
                            # Transcript is a dict, extract text content
                            text = str(podcast.transcript)
                    elif artifact_type in ("note", "summary"):
                        from open_notebook.domain.notebook import Note

                        note = await Note.get(artifact_id)
                        text = note.content or ""

                    if text:
                        analysis = await _analyze_single_content(
                            content_id=artifact_id,
                            content_type=artifact_type,
                            title=artifact_title,
                            text=text,
                        )
                        analyses.append(analysis)
                except Exception as e:
                    logger.warning(
                        f"Failed to analyze artifact {artifact_id}: {e}"
                    )
                    continue

        if not analyses:
            return {
                "error": "No analyzable content found in notebook",
                "status": "failed",
            }

        logger.info(f"Completed {len(analyses)} content analyses")

        return {
            "content_analyses": analyses,
            "status": "generating",
        }

    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to analyze content: {str(e)}",
            "status": "failed",
        }


async def aggregate_objectives(state: ObjectiveGenerationState) -> dict:
    """Synthesize global objectives from per-content analyses.

    Feeds all content analyses to LLM with aggregation prompt.
    Each objective includes source_refs for provenance tracking.

    Args:
        state: Workflow state with content_analyses

    Returns:
        Dict with generated_objectives list and status update
    """
    if state.get("error"):
        return {}

    logger.info("Aggregating objectives from content analyses")

    try:
        parser = PydanticOutputParser(pydantic_object=AggregatedObjectives)

        prompter = Prompter(
            prompt_template="learning_objectives/generate.jinja",
            parser=parser,
        )

        num_objectives = state.get("num_objectives", 4)

        prompt = prompter.render(
            data={
                "analyses": state["content_analyses"],
                "num_objectives": num_objectives,
            }
        )

        model = await provision_langchain_model(
            content=prompt,
            model_id=None,
            default_type="default",
            max_tokens=2000,
            structured=dict(type="json"),
        )

        ai_message = await model.ainvoke(prompt)
        message_content = extract_text_from_response(ai_message.content)
        cleaned = clean_thinking_content(message_content)
        cleaned = _strip_code_fences(cleaned)

        result = parser.parse(cleaned)

        logger.info(f"Aggregated {len(result.objectives)} learning objectives")

        objectives_list = [
            {
                "text": obj.text,
                "order": idx,
                "auto_generated": True,
                "source_refs": obj.source_refs,
            }
            for idx, obj in enumerate(result.objectives)
        ]

        return {
            "generated_objectives": objectives_list,
            "status": "saving",
        }

    except Exception as e:
        logger.error(f"Error aggregating objectives: {e}")
        logger.exception(e)
        return {
            "error": f"Failed to aggregate objectives: {str(e)}",
            "status": "failed",
        }


async def save_objectives(state: ObjectiveGenerationState) -> dict:
    """Save generated objectives to database with provenance.

    Creates LearningObjective records with auto_generated=True and source_refs.

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
                auto_generated=True,
                source_refs=obj_data.get("source_refs", []),
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
workflow.add_node("analyze_all_content", analyze_all_content)
workflow.add_node("aggregate_objectives", aggregate_objectives)
workflow.add_node("save_objectives", save_objectives)

# Define edges
workflow.set_entry_point("analyze_all_content")
workflow.add_edge("analyze_all_content", "aggregate_objectives")
workflow.add_edge("aggregate_objectives", "save_objectives")
workflow.add_edge("save_objectives", END)

# Compile graph
objectives_generation_graph = workflow.compile()
