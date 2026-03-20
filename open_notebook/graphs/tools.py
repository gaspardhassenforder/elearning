from datetime import datetime
from typing import Optional, List, Tuple

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from loguru import logger


async def _fetch_suggested_modules(user_id: str, current_notebook_id: str) -> List[dict]:
    """Fetch suggested modules for learner on module completion.

    Queries available modules for learner's company, excluding the current module.
    Returns up to 3 suggested modules with id, title, and description.

    Args:
        user_id: Learner's user ID
        current_notebook_id: Current notebook ID to exclude

    Returns:
        List of suggested module dicts with id, title, description
    """
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.domain.user import User

    try:
        # Get learner's company_id
        user = await User.get(user_id)
        if not user or not user.company_id:
            logger.warning(f"User {user_id} has no company_id - cannot suggest modules")
            return []

        # Query available modules for learner's company
        # Filter: published + unlocked + assigned to company + exclude current module
        query = """
            SELECT id, title, description
            FROM notebook
            WHERE id IN (
                SELECT VALUE notebook_id FROM module_assignment
                WHERE company_id = $company_id AND is_locked = false
            )
              AND published = true
              AND id != $current_notebook_id
            ORDER BY created DESC
            LIMIT 3
        """

        results = await repo_query(
            query,
            {"company_id": ensure_record_id(user.company_id), "current_notebook_id": ensure_record_id(current_notebook_id)},
        )

        # Format results
        suggestions = []
        for row in results:
            suggestions.append({
                "id": row.get("id"),
                "title": row.get("title", "Untitled Module"),
                "description": row.get("description", ""),
            })

        logger.info(f"Found {len(suggestions)} suggested modules for user {user_id}")
        return suggestions

    except Exception as e:
        logger.error("Error fetching suggested modules: {}", str(e))
        return []


@tool
async def search_available_modules(
    query: str,
    config: RunnableConfig,
    limit: int = 5,
) -> list:
    """Search across modules assigned to learner's company.

    Use this tool to help learners find relevant modules based on topic keywords.
    Searches module titles and descriptions for matches.

    Args:
        query: Search keywords (e.g., "machine learning", "AI logistics")
        config: RunnableConfig containing company_id and current_notebook_id (injected by navigation graph)
        limit: Max results to return (default: 5)

    Returns:
        List of ModuleSuggestion dicts with id, title, description, relevance_score

    Security Note:
        Company scoping is enforced by extracting company_id from the authenticated user context
        passed via RunnableConfig. The navigation endpoint validates authentication before invoking.
    """
    from open_notebook.database.repository import repo_query, ensure_record_id

    # Extract company_id and current_notebook_id from config (passed by navigation graph)
    company_id = None
    current_notebook_id = None
    if config:
        configurable = config.get("configurable", {})
        company_id = configurable.get("company_id")
        current_notebook_id = configurable.get("current_notebook_id")

    if not company_id:
        logger.warning("search_available_modules called without company_id in config")
        return []

    logger.info(f"search_available_modules: query='{query}', company={company_id}, exclude={current_notebook_id}")

    try:
        query_lower = query.lower()

        # Build query with company scoping and published/unlocked filters
        # Uses subquery instead of JOIN (SurrealDB doesn't support SQL-style JOINs)
        surql = """
            SELECT id, title, description, created
            FROM notebook
            WHERE id IN (
                SELECT VALUE notebook_id FROM module_assignment
                WHERE company_id = $company_id AND is_locked = false
            )
              AND published = true
              AND (
                string::lowercase(title) CONTAINS $query OR
                string::lowercase(description) CONTAINS $query
              )
        """

        # Optionally exclude current module
        if current_notebook_id:
            surql += " AND id != $current_notebook_id"

        # Priority: title matches first, then by creation date
        surql += """
            ORDER BY
              (string::lowercase(title) CONTAINS $query) DESC,
              created DESC
            LIMIT $limit;
        """

        params = {
            "company_id": ensure_record_id(company_id),
            "query": query_lower,
            "current_notebook_id": ensure_record_id(current_notebook_id) if current_notebook_id else None,
            "limit": limit
        }

        results = await repo_query(surql, params)

        # Map to ModuleSuggestion format with relevance scoring
        module_suggestions = []
        for row in results:
            # Title match gets higher relevance score
            title_lower = row.get("title", "").lower()
            relevance_score = 1.0 if query_lower in title_lower else 0.5

            module_suggestions.append({
                "id": row.get("id"),
                "title": row.get("title", "Untitled Module"),
                "description": row.get("description", ""),
                "relevance_score": relevance_score
            })

        logger.info(f"Found {len(module_suggestions)} modules for query '{query}'")
        return module_suggestions

    except Exception as e:
        logger.error("Error in search_available_modules: {}", str(e), exc_info=True)
        raise  # Re-raise to let caller handle gracefully


# todo: turn this into a system prompt variable
@tool
def get_current_timestamp() -> str:
    """
    name: get_current_timestamp
    Returns the current timestamp in the format YYYYMMDDHHmmss.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


@tool(response_format="content_and_artifact")
async def surface_document(
    source_id: str,
    excerpt_text: str,
    relevance_reason: str,
    page_number: Optional[int] = None,
    timestamp_seconds: Optional[float] = None,
) -> Tuple[str, dict]:
    """Surface a document snippet in the chat conversation.

    Use this tool when you want to reference a specific source document in your response.
    This will display an inline document card in the chat showing the excerpt and a link
    to open the full document in the sources panel.

    Args:
        source_id: The record ID of the source document (e.g., "source:abc123")
        excerpt_text: A relevant excerpt from the document (max 200 chars recommended)
        relevance_reason: Brief explanation of why this document is relevant to the conversation
        page_number: Optional PDF page number where the excerpt is found (1-indexed). Pass this when
            the excerpt comes from search_knowledge_base results that include page_number.
        timestamp_seconds: Optional video timestamp in seconds where the excerpt is found. Pass this
            when the excerpt comes from search_knowledge_base results that include timestamp_seconds
            (for YouTube/video sources).

    Returns:
        Tuple of (llm_content, ui_artifact):
        - llm_content: String summary for the LLM to reason over
        - ui_artifact: Dict for frontend rendering (extracted by SSE handler via ToolMessage.artifact)
    """
    from open_notebook.domain.notebook import Source

    logger.info(f"surface_document tool called for source_id: {source_id}")

    try:
        writer = get_stream_writer()
        writer({"type": "tool_progress", "tool": "surface_document", "status": "Loading document..."})
    except Exception:
        pass  # Streaming not available (e.g. sync invoke)

    try:
        # Load source metadata
        source = await Source.get(source_id)

        if not source:
            logger.warning(f"Source not found: {source_id}")
            return (
                f"Document {source_id} not found.",
                {"error": "not_found", "source_id": source_id},
            )

        # Truncate excerpt to 200 characters if needed
        truncated_excerpt = excerpt_text
        if len(excerpt_text) > 200:
            truncated_excerpt = excerpt_text[:197] + "..."
            logger.debug(f"Truncated excerpt from {len(excerpt_text)} to 200 chars")

        # Determine file type from asset (file_path or URL)
        file_type = "document"
        if source.asset and source.asset.file_path:
            import os
            _, ext = os.path.splitext(source.asset.file_path)
            file_type = ext.lstrip('.') if ext else "file"
        elif source.asset and source.asset.url:
            file_type = "url"

        # Load actual content for LLM reasoning
        try:
            source_context = await source.get_context("short")
            insights = source_context.get("insights", [])
            content_parts = []
            for insight in insights[:3]:
                content_parts.append(
                    f"{insight.get('insight_type', '')}: {insight.get('content', '')[:300]}"
                )
            content_summary = "\n".join(content_parts) if content_parts else truncated_excerpt
        except Exception:
            content_summary = truncated_excerpt

        # String for LLM (content) — LLM sees this in the next agent turn
        llm_content = (
            f'Displayed document "{source.title}" [source:{source_id}].\n'
            f"Content:\n{content_summary}"
        )

        # Dict for frontend (artifact) — extracted by SSE handler
        ui_artifact = {
            "source_id": source_id,
            "title": source.title or "Untitled Document",
            "source_type": file_type,
            "excerpt": truncated_excerpt,
            "relevance": relevance_reason,
            "page_number": page_number,  # PDF page for navigation (None for non-PDF)
            "timestamp_seconds": timestamp_seconds,  # Video timestamp in seconds (None for non-video)
            "asset_url": source.asset.url if source.asset else None,  # For inline video/PDF detection
            "asset_file_path": source.asset.file_path if source.asset else None,  # For getVideoType()
            "metadata": {
                "created": source.created.isoformat() if source.created else None,
                "file_type": file_type,
            },
        }

        logger.info(f"Successfully surfaced document: {source.title}")
        return llm_content, ui_artifact

    except Exception as e:
        logger.error(
            "Error in surface_document tool for source {}: {}",
            source_id, str(e), exc_info=True,
        )
        return (
            "I had trouble accessing that document.",
            {"error": "service_error", "source_id": source_id},
        )


@tool
async def check_off_objective(
    objective_id: str,
    evidence_text: str,
    config: RunnableConfig,
) -> dict:
    """Check off a learning objective when learner demonstrates understanding.

    Use this tool when you assess that the learner has demonstrated comprehension
    of a specific learning objective through their conversation. The evidence text
    should explain what the learner said or did that demonstrates understanding.

    Args:
        objective_id: The record ID of the learning objective (e.g., "learning_objective:abc123")
        evidence_text: Your reasoning explaining why this objective is now complete
            (e.g., "Learner correctly explained the difference between supervised and unsupervised learning")
        config: RunnableConfig containing user_id (injected by chat graph)

    Returns:
        dict: Progress data including completion counts and all_complete flag

    Security Note:
        Relies on API-layer access control via notebook assignment.
        The learner chat endpoint validates notebook assignment before invoking this tool.
        User ID is passed via RunnableConfig from the authenticated session.
    """
    from open_notebook.domain.learning_objective import LearningObjective
    from open_notebook.domain.learner_objective_progress import (
        LearnerObjectiveProgress,
        ProgressStatus,
        CompletedVia,
    )

    logger.info(f"check_off_objective tool called for objective_id: {objective_id}")

    try:
        # Load objective to validate it exists
        objective = await LearningObjective.get(objective_id)

        if not objective:
            logger.warning(f"Learning objective not found: {objective_id}")
            return {
                "error": "I couldn't find that learning objective",
                "error_type": "not_found",
                "recoverable": True,
            }

        # Extract user_id from config (passed by learner chat service)
        # Config is injected via RunnableConfig in chat graph
        user_id = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")

        if not user_id:
            logger.warning("check_off_objective called without user_id in config")
            return {
                "error": "I couldn't record your progress right now",
                "error_type": "service_error",
                "recoverable": False,
            }

        # Create or retrieve progress record (handles duplicates gracefully)
        progress = await LearnerObjectiveProgress.create(
            user_id=user_id,
            objective_id=objective_id,
            status=ProgressStatus.COMPLETED,
            completed_via=CompletedVia.CONVERSATION,
            evidence=evidence_text,
        )

        # Count total completed vs total objectives for this notebook
        total_completed = await LearnerObjectiveProgress.count_completed_for_notebook(
            user_id=user_id, notebook_id=objective.notebook_id
        )
        total_objectives = await LearningObjective.count_for_notebook(objective.notebook_id)

        # Determine if all objectives are complete
        all_complete = total_completed >= total_objectives

        result = {
            "objective_id": objective_id,
            "objective_text": objective.text,
            "evidence": evidence_text,
            "total_completed": total_completed,
            "total_objectives": total_objectives,
            "all_complete": all_complete,
        }

        # Story 4.5: When all objectives complete, suggest next modules
        if all_complete:
            suggested_modules = await _fetch_suggested_modules(
                user_id=user_id, current_notebook_id=objective.notebook_id
            )
            result["suggested_modules"] = suggested_modules
            logger.info(f"Module completion: suggested {len(suggested_modules)} modules")
        else:
            result["suggested_modules"] = []

        logger.info(
            f"Checked off objective {objective_id}: {total_completed}/{total_objectives} complete"
        )
        return result

    except Exception as e:
        logger.error("Error in check_off_objective tool for objective {}: {}", objective_id, str(e), exc_info=True)
        return {
            "error": "I had trouble recording your progress",
            "error_type": "service_error",
            "recoverable": False,
        }


async def _resolve_artifact_id(
    content_id: str, expected_type: str
) -> tuple[str | None, object | None, dict | None]:
    """Resolve an artifact:xxx tracker ID to the actual content ID.

    Returns (resolved_id, artifact, error_dict).
    - If content_id is not an artifact ID, returns (content_id, None, None).
    - If resolved successfully, returns (actual_id, artifact_object, None).
    - On error, returns (None, None, error_dict).
    """
    if not content_id.startswith("artifact:"):
        return content_id, None, None

    from open_notebook.database.repository import ensure_record_id, repo_query
    from open_notebook.domain.artifact import Artifact

    rows = await repo_query("SELECT * FROM $id", {"id": ensure_record_id(content_id)})
    if not rows:
        return None, None, {
            "error": f"I couldn't find that {expected_type}",
            "error_type": "not_found",
            "recoverable": True,
        }
    artifact = Artifact(**rows[0])
    if artifact.artifact_type != expected_type:
        return None, None, {
            "error": f"I couldn't find that {expected_type}",
            "error_type": "not_found",
            "recoverable": True,
        }
    if artifact._is_job_id():
        return None, None, {
            "error": f"That {expected_type} is still being generated",
            "error_type": "not_ready",
            "recoverable": True,
        }
    return artifact.artifact_id, artifact, None


@tool
async def surface_quiz(quiz_id: str, config: RunnableConfig) -> dict:
    """Surface a quiz in the chat conversation.

    Use this tool when you want to validate learner understanding through an interactive quiz.
    The quiz will display inline in the chat with the first question, allowing immediate interaction.

    Args:
        quiz_id: The record ID of the quiz (e.g., "quiz:abc123") or artifact tracker (e.g., "artifact:xyz")
        config: RunnableConfig containing user_id and notebook_id (injected by chat graph)

    Returns:
        dict: Quiz preview data with questions (WITHOUT correct_answer field for security)

    Security Note:
        Company scoping is validated by checking that the quiz's notebook belongs to
        the learner's company via module assignments. User context passed via RunnableConfig.
    """
    from open_notebook.domain.quiz import Quiz
    from open_notebook.domain.user import User
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.exceptions import NotFoundError

    logger.info(f"surface_quiz tool called for quiz_id: {quiz_id}")

    try:
        quiz_id, _, error = await _resolve_artifact_id(quiz_id, "quiz")
        if error:
            return error

        # Load quiz
        try:
            quiz = await Quiz.get(quiz_id)
        except NotFoundError:
            logger.warning(f"Quiz not found: {quiz_id}")
            return {
                "error": "I couldn't find that quiz",
                "error_type": "not_found",
                "recoverable": True,
            }

        if not quiz:
            logger.warning(f"Quiz not found: {quiz_id}")
            return {
                "error": "I couldn't find that quiz",
                "error_type": "not_found",
                "recoverable": True,
            }

        # Extract user_id and notebook_id from config
        user_id = None
        notebook_id_cfg = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")
            notebook_id_cfg = configurable.get("notebook_id")

        if user_id:
            # Validate company scoping: quiz.notebook_id must belong to learner's company
            user = await User.get(user_id)
            if user and user.company_id:
                # Check if quiz's notebook is assigned to learner's company
                query = """
                    SELECT VALUE true
                    FROM module_assignment
                    WHERE notebook_id = $notebook_id
                      AND company_id = $company_id
                    LIMIT 1
                """
                results = await repo_query(
                    query,
                    {"notebook_id": ensure_record_id(quiz.notebook_id), "company_id": ensure_record_id(user.company_id)},
                )

                if not results:
                    logger.warning(
                        f"Company scoping violation: Quiz {quiz_id} not accessible to user {user_id}"
                    )
                    return {
                        "error": "That quiz isn't available for you",
                        "error_type": "access_denied",
                        "recoverable": True,
                    }

        # Prepare questions WITHOUT correct_answer field (security - no cheating)
        questions_preview = []
        for q in quiz.questions:
            questions_preview.append({
                "text": q.question,
                "options": q.options,
                # Intentionally exclude correct_answer
            })

        # Look up associated lesson step so the frontend can auto-complete it on quiz submission.
        # Quiz lesson steps do not have artifact_id set (only podcast steps do), so we simply
        # find the quiz-type step for this notebook.
        step_id = None
        if notebook_id_cfg:
            step_result = await repo_query(
                "SELECT VALUE type::string(id) FROM lesson_step WHERE notebook_id = $notebook_id AND step_type = 'quiz' LIMIT 1",
                {"notebook_id": ensure_record_id(notebook_id_cfg)},
            )
            if step_result:
                step_id = step_result[0]

        # Return structured data for frontend rendering
        result = {
            "artifact_type": "quiz",
            "quiz_id": quiz_id,
            "title": quiz.title,
            "description": quiz.description,
            "questions": questions_preview,  # All questions for inline quiz
            "total_questions": len(quiz.questions),
            "step_id": step_id,  # Lesson step to auto-complete after quiz submission (or None)
        }

        logger.info(f"Successfully surfaced quiz: {quiz.title} ({len(quiz.questions)} questions)")
        return result

    except Exception as e:
        logger.error("Error in surface_quiz tool for quiz {}: {}", quiz_id, str(e), exc_info=True)
        return {
            "error": "I had trouble loading that quiz",
            "error_type": "service_error",
            "recoverable": False,
        }


@tool
async def surface_podcast(podcast_id: str, config: RunnableConfig) -> dict:
    """Surface a podcast in the chat conversation.

    Use this tool when you want to offer an audio learning experience.
    The podcast will display inline in the chat with playback controls.

    Args:
        podcast_id: The record ID of the podcast (e.g., "podcast:xyz789") or artifact tracker (e.g., "artifact:xyz")
        config: RunnableConfig containing user_id and notebook_id (injected by chat graph)

    Returns:
        dict: Podcast metadata with audio URL and playback information

    Security Note:
        Company scoping is validated by checking that the podcast's notebook belongs to
        the learner's company via module assignments. User context passed via RunnableConfig.
    """
    from open_notebook.domain.podcast import Podcast
    from open_notebook.domain.user import User
    from open_notebook.database.repository import repo_query, ensure_record_id
    from open_notebook.exceptions import NotFoundError

    logger.info(f"surface_podcast tool called for podcast_id: {podcast_id}")

    try:
        # Resolve artifact:xxx tracker to actual content ID.
        # Keep artifact reference for notebook_id (used in company scoping for episodes).
        podcast_id, artifact, error = await _resolve_artifact_id(podcast_id, "podcast")
        if error:
            return error

        # Load the podcast — two possible models depending on which generation system was used:
        #   podcast:xxx  → Podcast (domain/podcast.py) — older system
        #   episode:xxx  → PodcastEpisode (podcasts/models.py) — podcast-creator library
        notebook_id_for_scoping = None
        title = None
        audio_url = None
        transcript_url = None
        status = "unknown"
        duration_minutes = 0

        if podcast_id.startswith("episode:"):
            from open_notebook.podcasts.models import PodcastEpisode
            try:
                episode = await PodcastEpisode.get(podcast_id)
            except NotFoundError:
                episode = None
            if not episode:
                logger.warning(f"PodcastEpisode not found: {podcast_id}")
                return {
                    "error": "I couldn't find that podcast",
                    "error_type": "not_found",
                    "recoverable": True,
                }
            if not episode.audio_file:
                job_status = await episode.get_job_status()
                logger.info(f"Episode {podcast_id} not ready yet (job status: {job_status})")
                return {
                    "error": "That podcast is still being generated",
                    "error_type": "not_ready",
                    "recoverable": True,
                }
            title = episode.name
            audio_url = f"/api/podcasts/episodes/{podcast_id}/audio"
            transcript_url = f"/api/podcasts/{podcast_id}/transcript"
            status = "completed"
            # notebook_id lives on the artifact tracker, not on the episode
            notebook_id_for_scoping = artifact.notebook_id if artifact else None
            # Derive duration from episode_profile if available
            ep = episode.episode_profile or {}
            num_segments = ep.get("num_segments", 5)
            duration_minutes = max(1, num_segments * 2)
        else:
            # podcast:xxx — original Podcast model
            try:
                podcast = await Podcast.get(podcast_id)
            except NotFoundError:
                podcast = None
            if not podcast:
                logger.warning(f"Podcast not found: {podcast_id}")
                return {
                    "error": "I couldn't find that podcast",
                    "error_type": "not_found",
                    "recoverable": True,
                }
            if not podcast.is_ready:
                logger.info(f"Podcast {podcast_id} is not ready yet (status: {podcast.status})")
                return {
                    "error": "That podcast is still being generated",
                    "error_type": "not_ready",
                    "recoverable": True,
                }
            title = podcast.title
            audio_url = f"/api/podcasts/{podcast_id}/audio"
            transcript_url = f"/api/podcasts/{podcast_id}/transcript"
            status = podcast.status
            duration_minutes = podcast.duration_minutes
            notebook_id_for_scoping = podcast.notebook_id

        # Extract user_id from config for company scoping validation
        user_id = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")

        if user_id and notebook_id_for_scoping:
            user = await User.get(user_id)
            if user and user.company_id:
                query = """
                    SELECT VALUE true
                    FROM module_assignment
                    WHERE notebook_id = $notebook_id
                      AND company_id = $company_id
                    LIMIT 1
                """
                results = await repo_query(
                    query,
                    {"notebook_id": ensure_record_id(notebook_id_for_scoping), "company_id": ensure_record_id(user.company_id)},
                )
                if not results:
                    logger.warning(
                        f"Company scoping violation: Podcast {podcast_id} not accessible to user {user_id}"
                    )
                    return {
                        "error": "That podcast isn't available for you",
                        "error_type": "access_denied",
                        "recoverable": True,
                    }

        result = {
            "artifact_type": "podcast",
            "podcast_id": podcast_id,
            "title": title,
            "audio_url": audio_url,
            "duration_minutes": duration_minutes,
            "transcript_url": transcript_url,
            "status": status,
        }

        logger.info(f"Successfully surfaced podcast: {title} ({duration_minutes} min)")
        return result

    except Exception as e:
        logger.error("Error in surface_podcast tool for podcast {}: {}", podcast_id, str(e), exc_info=True)
        return {
            "error": "I had trouble loading that podcast",
            "error_type": "service_error",
            "recoverable": False,
        }


@tool
async def search_knowledge_base(
    query: str,
    config: RunnableConfig,
) -> list:
    """Search the module's knowledge base for relevant information.
    Use this to find content related to the learner's question.
    Returns text passages from source documents and insights.

    Args:
        query: Natural language search query
    """
    from open_notebook.domain.notebook import vector_search_for_notebook

    logger.info(f"search_knowledge_base tool called with query: '{query}'")

    try:
        writer = get_stream_writer()
        writer({"type": "tool_progress", "tool": "search_knowledge_base", "status": "Searching knowledge base..."})
    except Exception:
        pass  # Streaming not available (e.g. sync invoke)

    # Extract notebook_id from config (auto-injected by LangChain)
    notebook_id = config.get("configurable", {}).get("notebook_id")

    if not notebook_id:
        logger.warning("search_knowledge_base called without notebook_id in config")
        return [{"error": "Search temporarily unavailable"}]

    try:
        results = await vector_search_for_notebook(
            notebook_id=notebook_id,
            keyword=query,
            results=8,
        )

        # Format results with actual content (up to 1000 chars) for LLM reasoning
        formatted = []
        for r in results:
            content = r.get("content", "")
            truncated = content[:1000] + "..." if len(content) > 1000 else content

            entry = {
                "source_id": str(r.get("parent_id") or r.get("id", "")),
                "title": r.get("title", "Untitled"),
                "content": truncated,
                "similarity": r.get("similarity", 0),
            }
            # Include page_number when available (from PDF source embeddings)
            page_number = r.get("page_number")
            if page_number is not None:
                entry["page_number"] = page_number

            # Include timestamp_seconds when available (from video source embeddings)
            timestamp_seconds = r.get("timestamp_seconds")
            if timestamp_seconds is not None:
                entry["timestamp_seconds"] = timestamp_seconds

            formatted.append(entry)

        logger.info(
            f"search_knowledge_base found {len(formatted)} results for '{query}'"
        )

        try:
            writer = get_stream_writer()
            writer({"type": "tool_progress", "tool": "search_knowledge_base", "status": f"Found {len(formatted)} results"})
        except Exception:
            pass

        return formatted

    except Exception as e:
        logger.error(
            "Error in search_knowledge_base: {}", str(e), exc_info=True
        )
        return [{"error": "Search temporarily unavailable"}]


@tool
async def get_objectives(config: RunnableConfig) -> list:
    """Return the current list of learning objectives with completion status.
    Call this when you need to know which objectives the learner has completed
    and which still need to be addressed.

    Returns:
        List of objective dicts with 'id', 'text', 'status' (not_started/completed), 'order'
    """
    return config.get("configurable", {}).get("objectives", [])


@tool
async def get_lesson_steps(config: RunnableConfig) -> list:
    """Return the current lesson plan steps with completion status.
    Call this to see where the learner is in the structured lesson plan.

    Returns:
        List of step dicts with 'id', 'title', 'step_type', 'status' (completed/current/upcoming).
        Future steps (after current) only show title and step_type to prevent skipping ahead.
    """
    steps = config.get("configurable", {}).get("lesson_steps", [])
    if not steps:
        return steps

    # Find the current step (first non-completed); mask details for future steps
    current_found = False
    result = []
    for step in steps:
        status = step.get("status", "upcoming")
        if status == "completed" or (status == "current" and not current_found):
            # Completed and current steps: return full details
            if status == "current":
                current_found = True
            result.append(step)
        else:
            # Future steps: only show title and step_type to prevent skipping
            result.append({
                "id": step.get("id"),
                "title": step.get("title"),
                "step_type": step.get("step_type"),
                "status": step.get("status", "upcoming"),
                "order": step.get("order"),
                "required": step.get("required"),
            })
    return result


@tool
async def complete_lesson_step(step_id: str, config: RunnableConfig) -> dict:
    """Mark a lesson step as completed.

    Use this for 'discuss' type steps when the learner has engaged meaningfully
    with the topic. For 'read' steps, they are marked complete by the frontend
    when the learner opens the document.

    Args:
        step_id: The record ID of the lesson step (e.g., "lesson_step:abc123")

    Returns:
        dict with step_id, step_title, confirmation message, and next_step
        (full details of the next step including discussion_prompt and ai_instructions,
        or None if all steps are completed)
    """
    from open_notebook.domain.learner_step_progress import LearnerStepProgress

    logger.info(f"complete_lesson_step tool called for step_id: {step_id}")

    configurable = config.get("configurable", {}) if config else {}
    user_id = configurable.get("user_id")

    if not user_id:
        logger.warning("complete_lesson_step called without user_id in config")
        return {
            "error": "I couldn't record your progress right now",
            "error_type": "service_error",
            "recoverable": False,
        }

    # Resolve step title from preloaded lesson_steps (avoids extra DB query)
    lesson_steps = configurable.get("lesson_steps", [])
    step_title = next(
        (s.get("title", step_id) for s in lesson_steps if s.get("id") == step_id),
        step_id,
    )

    # Find the next step after the completed one
    next_step = None
    found_current = False
    for s in lesson_steps:
        if found_current:
            next_step = s
            break
        if s.get("id") == step_id:
            found_current = True

    try:
        # Delegate step completion + objective auto-completion to service
        notebook_id = configurable.get("notebook_id")
        all_objectives_completed = False
        if notebook_id:
            from api.lesson_plan_service import complete_step_with_objectives
            result = await complete_step_with_objectives(user_id, step_id, notebook_id)
            all_objectives_completed = result.get("all_objectives_completed", False)
        else:
            await LearnerStepProgress.mark_complete(user_id=user_id, step_id=step_id)

        logger.info(f"Marked step {step_id} complete for user {user_id}")

        response = {
            "step_id": step_id,
            "step_title": step_title,
            "message": "Step marked complete",
            "all_objectives_completed": all_objectives_completed,
        }

        if next_step:
            response["next_step"] = {
                "id": next_step.get("id"),
                "title": next_step.get("title"),
                "step_type": next_step.get("step_type"),
                "source_id": next_step.get("source_id"),
                "discussion_prompt": next_step.get("discussion_prompt"),
                "ai_instructions": next_step.get("ai_instructions"),
                "artifact_id": next_step.get("artifact_id"),
                "order": next_step.get("order"),
                "required": next_step.get("required"),
            }
        else:
            response["next_step"] = None
            response["message"] = "All lesson steps completed!"

        return response

    except Exception as e:
        logger.error("Error in complete_lesson_step for step {}: {}", step_id, str(e), exc_info=True)
        return {
            "error": "I had trouble recording your progress",
            "error_type": "service_error",
            "recoverable": False,
        }


@tool
async def generate_artifact(
    artifact_type: str,
    topic: str,
    notebook_id: Optional[str] = None,
    num_questions: Optional[int] = 5,
    speaker_profile: Optional[str] = "default",
    config: RunnableConfig = None,
) -> dict:
    """Generate an artifact (podcast or quiz) asynchronously.

    Use this tool when the learner requests artifact generation (e.g., "create a podcast about X").
    The artifact generation will run in the background, allowing the conversation to continue
    without blocking. The learner will be notified when the artifact is ready.

    Args:
        artifact_type: Type of artifact to generate ("podcast", "quiz", or "transformation")
        topic: Topic or title for the artifact
        notebook_id: Notebook ID for the artifact (optional - from config if not provided)
        num_questions: Number of questions for quiz (default: 5, only used for quizzes)
        speaker_profile: Speaker profile name for podcast (default: "default", only used for podcasts)
        config: RunnableConfig containing user_id and notebook_id (injected by chat graph)

    Returns:
        dict: Job submission result with job_id, artifact_ids, status, and message

    Example:
        When learner says: "Can you create a podcast summarizing this module?"
        AI responds: "I'm generating that podcast for you. Let's continue while it's processing."

    Security Note:
        Artifact is created for the notebook from the current chat session (from config).
        User context passed via RunnableConfig ensures company scoping.
    """
    from open_notebook.domain.artifact import Artifact

    logger.info(f"generate_artifact tool called: {artifact_type} on topic '{topic}'")

    try:
        writer = get_stream_writer()
        writer({"type": "tool_progress", "tool": "generate_artifact", "status": f"Generating {artifact_type}..."})
    except Exception:
        pass  # Streaming not available (e.g. sync invoke)

    try:
        # Extract notebook_id and user_id from config
        if config:
            configurable = config.get("configurable", {})
            if not notebook_id:
                notebook_id = configurable.get("notebook_id")
            user_id = configurable.get("user_id")
        else:
            user_id = None

        if not notebook_id:
            logger.warning("generate_artifact called without notebook_id")
            return {
                "error": "I couldn't determine which module to use",
                "error_type": "service_error",
                "recoverable": False,
            }

        # Submit async job based on artifact type
        if artifact_type == "podcast":
            # Import here to avoid circular dependencies
            from api.podcast_service import PodcastService

            logger.info(f"Submitting podcast generation job: topic={topic}, notebook={notebook_id}")

            # Submit podcast generation job (returns job_id, artifact_ids)
            job_id, artifact_ids = await PodcastService.submit_generation_job(
                episode_profile_name=topic,
                speaker_profile_name=speaker_profile,
                episode_name=f"Podcast: {topic}",
                notebook_id=notebook_id,
                created_by=user_id,
            )

            message = f"Podcast generation started. You'll be notified when it's ready."

        elif artifact_type == "quiz":
            from api.quiz_service import generate_quiz
            from open_notebook.database.repository import ensure_record_id, repo_query
            from open_notebook.domain.lesson_step import LessonStep

            logger.info(f"Generating quiz synchronously: topic={topic}, notebook={notebook_id}")

            result = await generate_quiz(
                notebook_id=notebook_id,
                topic=topic,
                num_questions=num_questions,
                created_by=user_id,
            )
            if "quiz_id" not in result:
                return {
                    "error": "I had trouble generating that quiz",
                    "error_type": "service_error",
                    "recoverable": False,
                }
            quiz_id = result["quiz_id"]

            # The workflow already created the artifact tracker — look it up instead of duplicating it
            tracker_rows = await repo_query(
                "SELECT VALUE type::string(id) FROM artifact WHERE artifact_id = $qid AND artifact_type = 'quiz' LIMIT 1",
                {"qid": ensure_record_id(quiz_id)},
            )
            artifact_tracker_id = tracker_rows[0] if tracker_rows else quiz_id

            # Persist artifact_id on the lesson step so next visit uses the live reference
            step_rows = await repo_query(
                "SELECT VALUE type::string(id) FROM lesson_step WHERE notebook_id = $nb AND step_type = 'quiz' LIMIT 1",
                {"nb": ensure_record_id(notebook_id)},
            )
            if step_rows:
                step = await LessonStep.get(step_rows[0])
                if step:
                    step.artifact_id = artifact_tracker_id
                    await step.save()

            job_id = artifact_tracker_id
            artifact_ids = [artifact_tracker_id]
            message = f"Quiz '{topic}' has been generated."

        elif artifact_type == "transformation":
            # Import here to avoid circular dependencies
            from open_notebook.graphs.transformation import graph as transformation_graph
            from open_notebook.domain.notebook import Source
            from open_notebook.domain.transformation import Transformation
            from open_notebook.database.repository import repo_query, ensure_record_id

            logger.info(f"Running transformation: topic={topic}, notebook={notebook_id}")

            # Find a suitable source from the notebook
            source_results = await repo_query(
                """
                SELECT VALUE ->has->source FROM notebook
                WHERE id = $notebook_id
                LIMIT 1
                """,
                {"notebook_id": ensure_record_id(notebook_id)},
            )

            source = None
            if source_results and source_results[0]:
                source_ids = source_results[0]
                if source_ids:
                    source = await Source.get(str(source_ids[0]))

            if not source:
                return {
                    "error": "No source documents found to transform",
                    "error_type": "not_found",
                    "recoverable": True,
                }

            # Create an ad-hoc transformation with the topic as prompt
            transformation = Transformation(
                name=f"chat_{topic[:30]}",
                title=f"Summary: {topic}",
                prompt=f"Based on the following content, create a comprehensive summary focused on: {topic}",
            )

            # Run the transformation graph
            result = await transformation_graph.ainvoke({
                "input_text": source.full_text or "",
                "source": source,
                "transformation": transformation,
                "output": "",
            })

            output_text = result.get("output", "")

            # Create artifact tracker
            artifact = await Artifact.create_for_artifact(
                notebook_id=notebook_id,
                artifact_type="transformation",
                artifact_id=str(source.id),
                title=f"Summary: {topic}",
                content=output_text,
            )

            job_id = str(artifact.id)
            artifact_ids = [str(artifact.id)]
            message = f"Summary on '{topic}' has been generated."

        else:
            logger.warning(f"Unsupported artifact type: {artifact_type}")
            return {
                "error": "I can only generate quizzes, podcasts, and transformations",
                "error_type": "validation",
                "recoverable": True,
            }

        # Return tool result with job tracking info
        result = {
            "job_id": job_id,
            "artifact_ids": artifact_ids,
            "artifact_type": artifact_type,
            "status": "completed" if artifact_type == "transformation" else "submitted",
            "message": message,
            "topic": topic
        }

        logger.info(f"Artifact generation job submitted: {result}")
        return result

    except Exception as e:
        logger.error("Error in generate_artifact tool: {}", str(e), exc_info=True)
        return {
            "error": "I had trouble creating that for you",
            "error_type": "service_error",
            "recoverable": False,
        }
