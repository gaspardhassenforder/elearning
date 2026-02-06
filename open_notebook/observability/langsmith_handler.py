"""
LangSmith callback handler utility for tracing LLM interactions.

Provides optional LangSmith integration for all LangGraph workflows,
enabling end-to-end tracing of AI conversations, RAG retrieval, tool calls,
and token usage monitoring.
"""

import os
from typing import Optional

from langchain_core.tracers import LangChainTracer
from loguru import logger


def get_langsmith_callback(
    user_id: Optional[str] = None,
    company_id: Optional[str] = None,
    notebook_id: Optional[str] = None,
    workflow_name: str = "unknown",
    run_name: Optional[str] = None,
) -> Optional[LangChainTracer]:
    """
    Create LangSmith callback handler with metadata tagging.

    Returns None if LangSmith not configured - workflows continue normally.

    This function checks the LANGCHAIN_TRACING_V2 environment variable to determine
    if LangSmith tracing is enabled. If enabled, it creates a LangChainTracer with
    metadata tags for filtering and attribution.

    Args:
        user_id: User performing action (for attribution)
        company_id: Company context (for multi-tenancy filtering)
        notebook_id: Module context (for content attribution)
        workflow_name: Type of workflow (chat, quiz, podcast, navigation, etc.)
        run_name: Custom run identifier (defaults to None, tracer will auto-generate)

    Returns:
        LangChainTracer with metadata tags, or None if tracing not configured

    Example:
        >>> # Create callback for learner chat
        >>> callback = get_langsmith_callback(
        ...     user_id="user:abc123",
        ...     company_id="company:xyz789",
        ...     notebook_id="notebook:456",
        ...     workflow_name="learner_chat",
        ...     run_name="chat:session:789"
        ... )
        >>> # Use in graph invocation
        >>> config = RunnableConfig(callbacks=[callback] if callback else [])
        >>> result = await graph.ainvoke(state, config)
    """
    # Check if LangSmith is enabled
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    if not tracing_enabled:
        logger.debug("LangSmith tracing disabled - skipping callback handler")
        return None

    # Build metadata tags for filtering
    tags = []
    metadata = {}

    if user_id:
        tags.append(f"user:{user_id}")
        metadata["user_id"] = user_id

    if company_id:
        tags.append(f"company:{company_id}")
        metadata["company_id"] = company_id

    if notebook_id:
        tags.append(f"notebook:{notebook_id}")
        metadata["notebook_id"] = notebook_id

    # Always include workflow name
    tags.append(f"workflow:{workflow_name}")
    metadata["workflow_name"] = workflow_name

    # Get project name from environment or use default
    project_name = os.getenv("LANGCHAIN_PROJECT", "Open Notebook")

    # Create tracer with metadata
    tracer = LangChainTracer(
        project_name=project_name,
        tags=tags,
        metadata=metadata,
    )

    # Set custom run name if provided
    if run_name:
        tracer.run_name = run_name

    logger.debug(f"LangSmith tracer created: {workflow_name} (tags: {tags})")
    return tracer
