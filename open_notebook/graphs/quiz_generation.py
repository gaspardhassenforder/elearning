"""Quiz generation workflow using LangGraph."""

import asyncio
import hashlib
import json
import re
from typing import List, Literal, Optional, TypedDict

from langchain_core.runnables import RunnableConfig

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.artifact import Artifact
from open_notebook.domain.notebook import Notebook, vector_search_for_notebook
from open_notebook.domain.quiz import Quiz, QuizQuestion
from open_notebook.observability.token_tracking_callback import TokenTrackingCallback
from open_notebook.utils import clean_thinking_content


class QuizGenerationState(TypedDict):
    """State for quiz generation workflow."""

    notebook_id: str
    topic: Optional[str]
    num_questions: int
    source_ids: Optional[List[str]]
    instructions: Optional[str]
    rag_queries: Optional[List[str]]
    retrieved_chunks: List[dict]
    sources_content: str
    generated_questions: List[dict]
    quiz_id: Optional[str]
    error: Optional[str]
    status: Literal["pending", "gathering", "generating", "saving", "completed", "failed"]
    # Story 7.7: Token tracking context
    user_id: Optional[str]
    company_id: Optional[str]


class QuizSearch(BaseModel):
    """A search query for quiz generation."""

    term: str
    instructions: str = Field(
        description="What information should be extracted from this search for quiz generation"
    )


class QuizStrategy(BaseModel):
    """Strategy for generating quiz search queries."""

    reasoning: str
    searches: List[QuizSearch] = Field(
        default_factory=list,
        description="Generate 2-5 search queries optimized for retrieving quiz-worthy content",
    )


async def generate_rag_queries(state: QuizGenerationState) -> dict:
    """Generate optimized RAG search queries using LLM."""
    logger.info("Generating RAG queries for quiz generation")

    try:
        parser = PydanticOutputParser(pydantic_object=QuizStrategy)
        prompt_data = {
            "topic": state.get("topic"),
            "instructions": state.get("instructions"),
            "num_questions": state["num_questions"],
        }

        prompter = Prompter(prompt_template="quiz/rag_queries.jinja", parser=parser)
        system_prompt = prompter.render(data=prompt_data)

        model = await provision_langchain_model(
            content=system_prompt,
            model_id=None,
            default_type="default",
            max_tokens=2000,
            structured=dict(type="json"),
        )

        # Story 7.7: Token tracking for quiz generation
        callbacks = []
        if state.get("user_id") or state.get("company_id"):
            callbacks.append(
                TokenTrackingCallback(
                    user_id=state.get("user_id"),
                    company_id=state.get("company_id"),
                    notebook_id=state.get("notebook_id"),
                    operation_type="quiz_generation",
                )
            )

        config = RunnableConfig(callbacks=callbacks) if callbacks else None
        ai_message = await model.ainvoke(system_prompt, config=config)

        # Extract text from response (handles string, list of content blocks, etc.)
        from open_notebook.utils import extract_text_from_response

        raw_content = ai_message.content
        message_content = extract_text_from_response(raw_content)
        cleaned_content = clean_thinking_content(message_content)

        # Parse the cleaned JSON content
        strategy = parser.parse(cleaned_content)

        queries = [search.term for search in strategy.searches]

        logger.info(f"Generated {len(queries)} RAG queries: {queries}")

        return {
            "rag_queries": queries,
            "status": "gathering",
        }

    except Exception as e:
        logger.error("Error generating RAG queries: {}", str(e))
        logger.exception(e)
        return {
            "error": f"Failed to generate RAG queries: {str(e)}",
            "status": "failed",
        }


async def retrieve_relevant_chunks(state: QuizGenerationState) -> dict:
    """Retrieve relevant chunks using RAG queries."""
    if state.get("error") or not state.get("rag_queries"):
        return {}

    logger.info(f"Retrieving chunks for {len(state['rag_queries'])} queries")

    try:
        all_chunks = []
        seen_content_hashes = set()

        for query in state["rag_queries"]:
            try:
                # Get top 15 chunks per query (no similarity threshold)
                chunks = await vector_search_for_notebook(
                    notebook_id=state["notebook_id"],
                    keyword=query,
                    results=15,
                    source_ids=state.get("source_ids"),
                )

                # Deduplicate chunks by content hash
                for chunk in chunks:
                    content = chunk.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(str(c) for c in content)
                    content_str = str(content)
                    content_hash = hashlib.md5(content_str.encode()).hexdigest()

                    if content_hash not in seen_content_hashes:
                        seen_content_hashes.add(content_hash)
                        all_chunks.append(chunk)

                logger.debug(f"Retrieved {len(chunks)} chunks for query: {query[:50]}...")

            except Exception as e:
                logger.warning("Error retrieving chunks for query '{}': {}", query, str(e))
                continue

        logger.info(f"Retrieved {len(all_chunks)} unique chunks total")

        return {
            "retrieved_chunks": all_chunks,
            "status": "gathering",
        }

    except Exception as e:
        logger.error("Error retrieving relevant chunks: {}", str(e))
        logger.exception(e)
        return {
            "error": f"Failed to retrieve relevant chunks: {str(e)}",
            "status": "failed",
        }


async def gather_sources(state: QuizGenerationState) -> dict:
    """Gather relevant source content from the notebook using RAG or fallback to full sources."""
    logger.info(f"Gathering sources for notebook {state['notebook_id']}")

    try:
        from open_notebook.database.repository import repo_query, ensure_record_id
        from open_notebook.domain.notebook import Source
        
        notebook = await Notebook.get(state["notebook_id"])
        if not notebook:
            return {
                "error": "Notebook not found",
                "status": "failed",
            }
        
        # Check if we have retrieved chunks from RAG
        if state.get("retrieved_chunks"):
            logger.info(f"Using RAG-retrieved chunks: {len(state['retrieved_chunks'])} chunks")
            
            # Format retrieved chunks similar to current format
            content_parts = []
            for chunk in state["retrieved_chunks"]:
                title = chunk.get("title", "Untitled")
                content = chunk.get("content", "")
                
                # Handle content that might be a list
                if isinstance(content, list):
                    content = " ".join(str(c) for c in content)
                content_str = str(content)
                
                if content_str:
                    content_parts.append(f"## Source: {title}\n\n{content_str}")
            
            if not content_parts:
                logger.warning("No content found in retrieved chunks, falling back to full sources")
                # Fall through to full source retrieval
            else:
                combined_content = "\n\n---\n\n".join(content_parts)
                logger.info(f"Formatted {len(content_parts)} chunks into {len(combined_content)} characters")
                
                return {
                    "sources_content": combined_content,
                    "status": "generating",
                }
        
        # Fallback: Check if embeddings exist, if not use full sources
        logger.info("Checking for embeddings or using full source fallback")
        
        # Fetch sources WITH full_text (notebook.get_sources() omits it for performance)
        srcs = await repo_query(
            """
            select in as source from reference where out=$id
            fetch source
            """,
            {"id": ensure_record_id(state["notebook_id"])},
        )
        sources = [Source(**src["source"]) for src in srcs] if srcs else []

        if not sources:
            return {
                "error": "No sources found in notebook",
                "status": "failed",
            }

        # Filter by source_ids if specified
        if state.get("source_ids"):
            sources = [s for s in sources if s.id in state["source_ids"]]
            if not sources:
                return {
                    "error": "Specified sources not found",
                    "status": "failed",
                }

        # Check if any sources have embeddings
        has_embeddings = False
        try:
            embedding_check = await repo_query(
                """
                SELECT VALUE count() FROM source_embedding 
                WHERE source IN (SELECT VALUE in FROM reference WHERE out=$notebook_id)
                GROUP ALL
                """,
                {"notebook_id": ensure_record_id(state["notebook_id"])},
            )
            if embedding_check and embedding_check[0] and embedding_check[0].get("count", 0) > 0:
                has_embeddings = True
        except Exception as e:
            logger.debug("Could not check embeddings: {}", str(e))

        if has_embeddings:
            logger.info("Sources have embeddings but RAG retrieval was not used, using full sources as fallback")

        # Combine source content with source titles for context
        content_parts = []
        for source in sources:
            if source.full_text:
                # Limit each source to prevent context overflow
                text = source.full_text[:8000] if len(source.full_text) > 8000 else source.full_text
                content_parts.append(f"## Source: {source.title or 'Untitled'}\n\n{text}")

        if not content_parts:
            return {
                "error": "No text content found in sources",
                "status": "failed",
            }

        combined_content = "\n\n---\n\n".join(content_parts)
        
        # Limit total content to prevent context overflow
        max_content_length = 30000
        if len(combined_content) > max_content_length:
            combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"

        logger.info(f"Gathered {len(sources)} sources with {len(combined_content)} characters (fallback mode)")

        return {
            "sources_content": combined_content,
            "status": "generating",
        }

    except Exception as e:
        logger.error("Error gathering sources: {}", str(e))
        return {
            "error": f"Failed to gather sources: {str(e)}",
            "status": "failed",
        }


async def generate_questions(state: QuizGenerationState) -> dict:
    """Use LLM to generate quiz questions from source content."""
    if state.get("error"):
        return {}

    logger.info(f"Generating {state['num_questions']} quiz questions")

    try:
        # Prepare prompt data
        prompt_data = {
            "sources_content": state["sources_content"],
            "topic": state.get("topic"),
            "num_questions": state["num_questions"],
            "instructions": state.get("instructions"),
        }

        # Render prompt using Prompter
        prompter = Prompter(prompt_template="quiz/generate.md")
        prompt = prompter.render(data=prompt_data)

        # Get model for quiz generation
        model = await provision_langchain_model(
            content=prompt,
            model_id=None,
            default_type="default",
            max_tokens=4096,
        )

        # Story 7.7: Token tracking for quiz generation
        callbacks = []
        if state.get("user_id") or state.get("company_id"):
            callbacks.append(
                TokenTrackingCallback(
                    user_id=state.get("user_id"),
                    company_id=state.get("company_id"),
                    notebook_id=state.get("notebook_id"),
                    operation_type="quiz_generation",
                )
            )

        config = RunnableConfig(callbacks=callbacks) if callbacks else None
        # Generate questions
        response = await model.ainvoke(prompt, config=config)
        
        # Extract text from response (handles string, list of content blocks, etc.)
        from open_notebook.utils import extract_text_from_response
        raw_content = response.content if hasattr(response, "content") else response
        response_text = extract_text_from_response(raw_content)

        # Parse JSON response
        logger.debug(f"Response text to parse (first 500 chars): {response_text[:500]}")
        questions = _parse_quiz_response(response_text)
        logger.info(f"Parsed {len(questions)} questions from response")
        
        if questions:
            logger.debug(f"First parsed question: {questions[0]}")

        if not questions:
            logger.error(f"Failed to parse questions. Full response: {response_text}")
            return {
                "error": "Failed to parse quiz questions from LLM response",
                "status": "failed",
            }

        logger.info(f"Successfully generated {len(questions)} questions")

        return {
            "generated_questions": questions,
            "status": "saving",
        }

    except Exception as e:
        logger.error("Error generating questions: {}", str(e))
        logger.exception(e)
        return {
            "error": f"Failed to generate questions: {str(e)}",
            "status": "failed",
        }


def _parse_quiz_response(response_text: str) -> List[dict]:
    """Parse LLM response to extract quiz questions."""
    # Try to find JSON in the response
    try:
        # First, try direct JSON parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"\[\s*\{[\s\S]*\}\s*\]",
    ]

    for pattern in json_patterns:
        match = re.search(pattern, response_text)
        if match:
            try:
                json_str = match.group(1) if "```" in pattern else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue

    logger.warning(f"Could not parse quiz response: {response_text[:500]}")
    return []


async def save_quiz(state: QuizGenerationState) -> dict:
    """Save generated quiz to database and create artifact tracker."""
    if state.get("error"):
        return {}

    logger.info(f"Saving quiz with {len(state['generated_questions'])} questions")

    try:
        # Convert dicts to QuizQuestion objects
        questions = []
        for q in state["generated_questions"]:
            question = QuizQuestion(
                question=q.get("question", ""),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", 0),
                explanation=q.get("explanation"),
                source_reference=q.get("source_reference"),
            )
            questions.append(question)

        # Create quiz title
        topic_suffix = f": {state['topic']}" if state.get("topic") else ""
        title = f"Quiz{topic_suffix}"

        # Create and save quiz
        quiz = Quiz(
            notebook_id=state["notebook_id"],
            title=title,
            questions=questions,
            source_ids=state.get("source_ids"),
            created_by="user",
        )
        
        # Debug logging
        logger.debug(f"Quiz before save: questions count = {len(quiz.questions)}")
        logger.debug(f"Quiz questions type: {type(quiz.questions)}")
        if quiz.questions:
            logger.debug(f"First question: {quiz.questions[0]}")
        
        # Check what will be saved
        save_data = quiz._prepare_save_data()
        logger.debug(f"Save data questions: {save_data.get('questions')}")
        
        await quiz.save()
        
        logger.debug(f"Quiz after save: ID = {quiz.id}, questions count = {len(quiz.questions)}")

        # Create artifact tracker
        await Artifact.create_for_artifact(
            notebook_id=state["notebook_id"],
            artifact_type="quiz",
            artifact_id=quiz.id,
            title=quiz.title,
        )

        logger.info(f"Quiz saved with ID: {quiz.id}")

        return {
            "quiz_id": quiz.id,
            "status": "completed",
        }

    except Exception as e:
        logger.error("Error saving quiz: {}", str(e))
        logger.exception(e)
        return {
            "error": f"Failed to save quiz: {str(e)}",
            "status": "failed",
        }


async def generate_quiz(
    notebook_id: str,
    topic: Optional[str] = None,
    num_questions: int = 5,
    source_ids: Optional[List[str]] = None,
    instructions: Optional[str] = None,
    user_id: Optional[str] = None,  # Story 7.7: Token tracking context
    company_id: Optional[str] = None,  # Story 7.7: Token tracking context
) -> dict:
    """
    Main entry point for quiz generation.

    Args:
        notebook_id: ID of the notebook to generate quiz for
        topic: Optional topic to focus questions on
        num_questions: Number of questions to generate (default: 5)
        source_ids: Optional list of specific source IDs to use
        instructions: Optional specific instructions for quiz generation
        user_id: Optional user ID for token tracking (Story 7.7)
        company_id: Optional company ID for token tracking (Story 7.7)

    Returns:
        dict with quiz_id if successful, or error message if failed
    """
    logger.info(f"Starting quiz generation for notebook {notebook_id}")

    # Initialize state
    state: QuizGenerationState = {
        "notebook_id": notebook_id,
        "topic": topic,
        "num_questions": min(num_questions, 20),  # Cap at 20 questions
        "source_ids": source_ids,
        "instructions": instructions,
        "rag_queries": None,
        "retrieved_chunks": [],
        "sources_content": "",
        "generated_questions": [],
        "quiz_id": None,
        "error": None,
        "status": "pending",
        "user_id": user_id,  # Story 7.7: Token tracking context
        "company_id": company_id,  # Story 7.7: Token tracking context
    }

    # Run workflow steps sequentially
    # Step 1: Generate RAG queries
    state.update(await generate_rag_queries(state))
    if state.get("error"):
        logger.warning(f"RAG query generation failed: {state['error']}, continuing with fallback")
        # Continue with fallback - clear error to allow fallback
        state["error"] = None
        state["rag_queries"] = None

    # Step 2: Retrieve relevant chunks (if RAG queries were generated)
    if state.get("rag_queries"):
        state.update(await retrieve_relevant_chunks(state))
        if state.get("error"):
            logger.warning(f"Chunk retrieval failed: {state['error']}, falling back to full sources")
            # Continue with fallback - clear error and chunks
            state["error"] = None
            state["retrieved_chunks"] = []

    # Step 3: Gather sources (uses RAG chunks if available, otherwise full sources)
    state.update(await gather_sources(state))
    if state.get("error"):
        return {"error": state["error"], "status": state["status"]}

    # Step 4: Generate questions
    state.update(await generate_questions(state))
    logger.info(f"After generate_questions: generated_questions count = {len(state.get('generated_questions', []))}")
    if state.get("error"):
        logger.error(f"generate_questions failed: {state['error']}")
        return {"error": state["error"], "status": state["status"]}

    # Step 5: Save quiz
    logger.info(f"Proceeding to save_quiz with {len(state['generated_questions'])} questions")
    state.update(await save_quiz(state))
    if state.get("error"):
        return {"error": state["error"], "status": state["status"]}

    return {
        "quiz_id": state["quiz_id"],
        "status": state["status"],
        "num_questions": len(state["generated_questions"]),
    }
