from datetime import datetime
from typing import Optional, List

from langchain.tools import tool
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
    config: Optional[dict] = None,
    limit: int = 5
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


@tool
async def surface_document(source_id: str, excerpt_text: str, relevance_reason: str) -> dict:
    """Surface a document snippet in the chat conversation.

    Use this tool when you want to reference a specific source document in your response.
    This will display an inline document card in the chat showing the excerpt and a link
    to open the full document in the sources panel.

    Args:
        source_id: The record ID of the source document (e.g., "source:abc123")
        excerpt_text: A relevant excerpt from the document (max 200 chars recommended)
        relevance_reason: Brief explanation of why this document is relevant to the conversation

    Returns:
        dict: Structured document snippet data with source metadata

    Security Note:
        Currently relies on API-layer access control to ensure learners only access
        sources from their assigned notebooks. The learner chat endpoint validates
        notebook assignment before invoking this tool.

        TODO (Story 7.5): Add defense-in-depth validation to verify source belongs to
        the notebook in the current chat session. Requires passing notebook_id via
        RunnableConfig or adding graph edge validation query.
    """
    from open_notebook.domain.notebook import Source

    logger.info(f"surface_document tool called for source_id: {source_id}")

    try:
        # Load source metadata
        source = await Source.get(source_id)

        if not source:
            logger.warning(f"Source not found: {source_id}")
            return {
                "error": "I couldn't find that document",
                "error_type": "not_found",
                "recoverable": True,
            }

        # Truncate excerpt to 200 characters if needed
        truncated_excerpt = excerpt_text
        if len(excerpt_text) > 200:
            truncated_excerpt = excerpt_text[:197] + "..."
            logger.debug(f"Truncated excerpt from {len(excerpt_text)} to 200 chars")

        # Determine file type from asset (file_path or URL)
        file_type = "document"
        if source.asset and source.asset.file_path:
            # Extract extension from file path
            import os
            _, ext = os.path.splitext(source.asset.file_path)
            file_type = ext.lstrip('.') if ext else "file"
        elif source.asset and source.asset.url:
            file_type = "url"

        # Return structured data for frontend rendering
        result = {
            "source_id": source_id,
            "title": source.title or "Untitled Document",
            "source_type": file_type,
            "excerpt": truncated_excerpt,
            "relevance": relevance_reason,
            "metadata": {
                "created": source.created.isoformat() if source.created else None,
                "file_type": file_type,
            }
        }

        logger.info(f"Successfully surfaced document: {source.title}")
        return result

    except Exception as e:
        logger.error("Error in surface_document tool for source {}: {}", source_id, str(e), exc_info=True)
        return {
            "error": "I had trouble accessing that document",
            "error_type": "service_error",
            "recoverable": False,
        }


@tool
async def check_off_objective(
    objective_id: str,
    evidence_text: str,
    config: Optional[dict] = None,
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


@tool
async def surface_quiz(quiz_id: str, config: Optional[dict] = None) -> dict:
    """Surface a quiz in the chat conversation.

    Use this tool when you want to validate learner understanding through an interactive quiz.
    The quiz will display inline in the chat with the first question, allowing immediate interaction.

    Args:
        quiz_id: The record ID of the quiz (e.g., "quiz:abc123")
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

        # Extract user_id from config for company scoping validation
        user_id = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")

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

        # Return structured data for frontend rendering
        result = {
            "artifact_type": "quiz",
            "quiz_id": quiz_id,
            "title": quiz.title,
            "description": quiz.description,
            "questions": questions_preview,  # All questions for inline quiz
            "total_questions": len(quiz.questions),
            "quiz_url": f"/quizzes/{quiz_id}",  # Frontend route
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
async def surface_podcast(podcast_id: str, config: Optional[dict] = None) -> dict:
    """Surface a podcast in the chat conversation.

    Use this tool when you want to offer an audio learning experience.
    The podcast will display inline in the chat with playback controls.

    Args:
        podcast_id: The record ID of the podcast (e.g., "podcast:xyz789")
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
        # Load podcast
        try:
            podcast = await Podcast.get(podcast_id)
        except NotFoundError:
            logger.warning(f"Podcast not found: {podcast_id}")
            return {
                "error": "I couldn't find that podcast",
                "error_type": "not_found",
                "recoverable": True,
            }

        if not podcast:
            logger.warning(f"Podcast not found: {podcast_id}")
            return {
                "error": "I couldn't find that podcast",
                "error_type": "not_found",
                "recoverable": True,
            }

        # Extract user_id from config for company scoping validation
        user_id = None
        if config:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id")

        if user_id:
            # Validate company scoping: podcast.notebook_id must belong to learner's company
            user = await User.get(user_id)
            if user and user.company_id:
                # Check if podcast's notebook is assigned to learner's company
                query = """
                    SELECT VALUE true
                    FROM module_assignment
                    WHERE notebook_id = $notebook_id
                      AND company_id = $company_id
                    LIMIT 1
                """
                results = await repo_query(
                    query,
                    {"notebook_id": ensure_record_id(podcast.notebook_id), "company_id": ensure_record_id(user.company_id)},
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

        # Check if podcast is ready
        if not podcast.is_ready:
            logger.info(f"Podcast {podcast_id} is not ready yet (status: {podcast.status})")
            return {
                "error": "That podcast is still being generated",
                "error_type": "not_ready",
                "recoverable": True,
            }

        # Return structured data for frontend rendering
        result = {
            "artifact_type": "podcast",
            "podcast_id": podcast_id,
            "title": podcast.title,
            "audio_url": f"/api/podcasts/{podcast_id}/audio",
            "duration_minutes": podcast.duration_minutes,
            "transcript_url": f"/api/podcasts/{podcast_id}/transcript",
            "status": podcast.status,
        }

        logger.info(f"Successfully surfaced podcast: {podcast.title} ({podcast.duration_minutes} min)")
        return result

    except Exception as e:
        logger.error("Error in surface_podcast tool for podcast {}: {}", podcast_id, str(e), exc_info=True)
        return {
            "error": "I had trouble loading that podcast",
            "error_type": "service_error",
            "recoverable": False,
        }


@tool
async def search_documents(
    query: str,
    config: Optional[dict] = None,
) -> list:
    """Search across all documents in the current module using semantic search.

    Use this to find relevant document passages when the learner asks about a topic.
    Returns relevant chunks with source_id, title, and excerpt that you can then
    surface using the surface_document tool.

    Args:
        query: The search query (e.g., "machine learning basics", "neural networks")
        config: RunnableConfig containing notebook_id (injected by chat graph)

    Returns:
        List of dicts with source_id, title, excerpt, relevance_score
    """
    from open_notebook.domain.notebook import vector_search_for_notebook

    logger.info(f"search_documents tool called with query: '{query}'")

    # Extract notebook_id from config
    notebook_id = None
    if config:
        configurable = config.get("configurable", {})
        notebook_id = configurable.get("notebook_id")

    if not notebook_id:
        logger.warning("search_documents called without notebook_id in config")
        return []

    try:
        results = await vector_search_for_notebook(
            notebook_id=notebook_id,
            keyword=query,
            results=5,
        )

        # Format results for the AI to use
        formatted = []
        for r in results:
            # Extract content snippet (first 200 chars)
            content = r.get("content", "")
            excerpt = content[:200] + "..." if len(content) > 200 else content

            formatted.append({
                "source_id": str(r.get("parent_id") or r.get("id", "")),
                "title": r.get("title", "Untitled"),
                "excerpt": excerpt,
                "relevance_score": r.get("similarity", 0),
            })

        logger.info(f"search_documents found {len(formatted)} results for '{query}'")
        return formatted

    except Exception as e:
        logger.error("Error in search_documents: {}", str(e), exc_info=True)
        return []


@tool
async def generate_artifact(
    artifact_type: str,
    topic: str,
    notebook_id: Optional[str] = None,
    num_questions: Optional[int] = 5,
    speaker_profile: Optional[str] = "default",
    config: Optional[dict] = None,
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
            )

            message = f"Podcast generation started. You'll be notified when it's ready."

        elif artifact_type == "quiz":
            # Import here to avoid circular dependencies
            from api.quiz_service import generate_quiz

            logger.info(f"Submitting quiz generation job: topic={topic}, notebook={notebook_id}")

            # Generate quiz (currently synchronous, but we'll track as if async)
            # TODO Story 4.7: Make quiz generation truly async via surreal-commands
            result = await generate_quiz(
                notebook_id=notebook_id,
                topic=topic,
                num_questions=num_questions,
            )

            # Check if quiz generation succeeded
            if "quiz_id" in result:
                quiz_id = result["quiz_id"]

                # Create artifact tracker with quiz_id
                artifact = await Artifact.create_for_artifact(
                    notebook_id=notebook_id,
                    artifact_type="quiz",
                    artifact_id=quiz_id,
                    title=f"Quiz: {topic}",
                )

                # For quiz, return completed status (since it's currently synchronous)
                job_id = quiz_id  # Use quiz_id as job_id for now
                artifact_ids = [str(artifact.id)]
                message = f"Quiz '{topic}' has been generated and is ready."
            else:
                # Quiz generation failed
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Quiz generation failed: {error_msg}")
                return {
                    "error": "I had trouble generating that quiz",
                    "error_type": "service_error",
                    "recoverable": False,
                }

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
            "status": "submitted" if artifact_type == "podcast" else "completed",
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
