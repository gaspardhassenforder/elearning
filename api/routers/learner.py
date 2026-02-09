from typing import List

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from loguru import logger

from api import assignment_service
from api.auth import LearnerContext, get_current_learner
from api.models import (
    LearnerModuleResponse,
    ModuleSuggestion,
    NavigationChatRequest,
    NavigationChatResponse,
    NavigationMessage,
)
from open_notebook.domain.module_assignment import ModuleAssignment
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.user import User
from open_notebook.observability.langsmith_handler import get_langsmith_callback
from open_notebook.observability.langgraph_context_callback import ContextLoggingCallback

router = APIRouter()


@router.get("/learner/modules", response_model=List[LearnerModuleResponse])
async def get_learner_modules(
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get modules assigned to the learner's company (unlocked only).

    Automatically scoped to learner's company via get_current_learner() dependency.
    Returns only modules that are:
    - Assigned to learner's company
    - NOT locked (is_locked = false)

    Args:
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        List of LearnerModuleResponse with learner-safe fields:
        - id: Notebook ID
        - name: Module name
        - description: Module description
        - is_locked: Lock status (always False in this endpoint)
        - source_count: Number of sources in module
        - assigned_at: ISO timestamp of assignment

    Note:
        Admin-only fields (assigned_by) are NOT included.
        Company scoping is AUTOMATICALLY enforced by get_current_learner().
    """
    logger.info(f"Fetching modules for learner {learner.user.id} (company {learner.company_id})")
    modules = await assignment_service.get_learner_modules(learner.company_id)
    # Service already returns List[LearnerModuleResponse], no reconstruction needed
    return modules


@router.get("/learner/modules/{notebook_id}", response_model=LearnerModuleResponse)
async def get_learner_module(
    notebook_id: str,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Validate learner access to a specific module (direct URL protection).

    Used for direct URL navigation protection. If a learner tries to access
    a module directly via URL, this endpoint validates they have permission.

    Validation rules:
    1. Module must be assigned to learner's company
    2. Module must NOT be locked (is_locked = false)

    Args:
        notebook_id: Notebook (module) record ID (path parameter)
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        LearnerModuleResponse with module details if accessible

    Raises:
        HTTPException 403: Module not assigned, locked, or access denied
        HTTPException 404: Module doesn't exist

    Note:
        Company scoping is AUTOMATICALLY enforced by get_current_learner().
        This endpoint is the SINGLE enforcement point for direct module access.
    """
    logger.info(
        f"Validating access for learner {learner.user.id} (company {learner.company_id}) to module {notebook_id}"
    )

    # Check if module is assigned to learner's company
    assignment = await ModuleAssignment.get_by_company_and_notebook(
        learner.company_id, notebook_id
    )

    if not assignment:
        logger.warning(
            f"Module {notebook_id} not assigned to company {learner.company_id} - access denied"
        )
        raise HTTPException(
            status_code=403, detail="This module is not accessible to you"
        )

    # Check if module is locked
    if assignment.is_locked:
        logger.warning(
            f"Module {notebook_id} is locked for company {learner.company_id} - access denied"
        )
        raise HTTPException(
            status_code=403, detail="This module is currently locked"
        )

    # Fetch notebook details
    try:
        notebook = await Notebook.get(notebook_id)
    except Exception:
        logger.error(f"Notebook {notebook_id} not found")
        raise HTTPException(status_code=404, detail="Module not found")

    # Check if module is published (Story 3.5 enforcement)
    is_published = getattr(notebook, "published", False)
    if not is_published:
        logger.warning(
            f"Module {notebook_id} is not published - access denied for learner {learner.user.id}"
        )
        raise HTTPException(
            status_code=403, detail="This module is not accessible to you"
        )

    # Count sources
    source_count = len(getattr(notebook, "sources", []))

    logger.info(f"Access granted for learner {learner.user.id} to module {notebook_id}")

    return LearnerModuleResponse(
        id=notebook_id,
        name=notebook.name,
        description=notebook.description,
        is_locked=assignment.is_locked,
        source_count=source_count,
        assigned_at=assignment.assigned_at or "",
    )


# ==============================================================================
# Story 6.1: Platform-Wide AI Navigation Assistant
# ==============================================================================


@router.post("/learner/navigation/chat", response_model=NavigationChatResponse)
async def navigation_chat(
    request: NavigationChatRequest,
    learner: LearnerContext = Depends(get_current_learner),
):
    """Send message to navigation assistant (Story 6.1).

    Returns assistant response with optional module suggestions.

    Navigation assistant helps learners find modules across their assigned content.
    It does NOT teach - it redirects learning questions to module AI teachers.

    Args:
        request: NavigationChatRequest with message and optional current_notebook_id
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        NavigationChatResponse with assistant message and suggested_modules list

    Note:
        - Thread ID pattern: nav:user:{user_id} (persistent conversation history)
        - Company scoping enforced via learner.company_id
        - search_available_modules tool automatically excludes current_notebook_id
    """
    from open_notebook.graphs.navigation import navigation_graph

    logger.info(f"Navigation chat for learner {learner.user.id}: '{request.message[:50]}...'")

    # Get current module title for prompt context (if learner is in a module)
    current_module_title = None
    if request.current_notebook_id:
        try:
            notebook = await Notebook.get(request.current_notebook_id)
            current_module_title = notebook.name if notebook else None
        except Exception as e:
            logger.warning(f"Failed to load current module {request.current_notebook_id}: {e}")

    # Count available modules for prompt context
    try:
        assignments = await ModuleAssignment.get_by_company(learner.company_id)
        available_modules_count = len(
            [a for a in assignments if not a.is_locked]  # Only count unlocked modules
        )
    except Exception:
        available_modules_count = 0

    # Get company name for prompt context
    company_name = "Unknown Company"
    if learner.user.company_id:
        try:
            from open_notebook.domain.company import Company
            company = await Company.get(learner.user.company_id)
            company_name = company.name if company else "Unknown Company"
        except Exception:
            pass

    # Build navigation state
    state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": learner.user.id,
        "company_id": learner.company_id,
        "current_notebook_id": request.current_notebook_id,
        "company_name": company_name,
        "current_module_title": current_module_title,
        "available_modules_count": available_modules_count,
    }

    # Thread ID for conversation persistence
    thread_id = f"nav:user:{learner.user.id}"

    # Story 7.4: Create LangSmith callback for tracing (or None if not configured)
    langsmith_callback = get_langsmith_callback(
        user_id=learner.user.id,
        company_id=learner.company_id,
        notebook_id=request.current_notebook_id,
        workflow_name="navigation_assistant",
        run_name=f"nav:{learner.user.id}",
    )

    # Story 7.2: Add context logging callback for error diagnostics
    context_callback = ContextLoggingCallback()

    # Build callbacks list (Story 7.2 + Story 7.4)
    callbacks = [context_callback]
    if langsmith_callback:
        callbacks.append(langsmith_callback)

    config = {
        "configurable": {
            "thread_id": thread_id,
            "company_id": learner.company_id,  # For search_available_modules tool
            "current_notebook_id": request.current_notebook_id,  # For search exclusion
        },
        "callbacks": callbacks,  # Story 7.4: LangSmith tracing
    }

    try:
        # Invoke navigation graph
        result = await navigation_graph.ainvoke(state, config)

        # Extract assistant message
        messages = result.get("messages", [])
        assistant_message = messages[-1].content if messages else "I'm here to help you find modules!"

        # Extract suggested modules from tool calls (if any)
        # The search_available_modules tool returns list of dicts
        # We need to check if the AI message has tool_calls and extract results
        suggested_modules = []
        if messages:
            last_message = messages[-1]
            # Check for tool_calls attribute (LangChain AIMessage structure)
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    if tool_call.get("name") == "search_available_modules":
                        # Tool result should be in tool_call or in subsequent messages
                        # For now, we'll leave this empty and let the narrative response suffice
                        pass

        logger.info(f"Navigation assistant response generated for learner {learner.user.id}")

        return NavigationChatResponse(
            message=assistant_message,
            suggested_modules=[
                ModuleSuggestion(**mod) for mod in suggested_modules
            ]
        )

    except Exception as e:
        logger.error(f"Navigation assistant error for learner {learner.user.id}: {e}", exc_info=True)
        return NavigationChatResponse(
            message="I'm having trouble searching right now. Please try again in a moment.",
            suggested_modules=[]
        )


@router.get("/learner/navigation/history", response_model=List[NavigationMessage])
async def get_navigation_history(
    learner: LearnerContext = Depends(get_current_learner),
):
    """Get navigation conversation history (Story 6.1).

    Returns last 10 navigation messages for continuity.

    Args:
        learner: LearnerContext with user and company_id (auto-injected)

    Returns:
        List of NavigationMessage (last 10 messages)

    Note:
        Thread ID pattern: nav:user:{user_id}
        History persists across sessions via LangGraph checkpointer.
    """
    from open_notebook.graphs.navigation import navigation_graph

    logger.info(f"Fetching navigation history for learner {learner.user.id}")

    thread_id = f"nav:user:{learner.user.id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Load checkpoint state
        state = navigation_graph.get_state(config)
        messages = state.values.get("messages", []) if state and state.values else []

        # Take last 10 messages
        recent_messages = messages[-10:] if len(messages) > 10 else messages

        # Convert to NavigationMessage format
        history = []
        for msg in recent_messages:
            role = "user" if msg.type == "human" else "assistant"
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            timestamp = None  # LangGraph messages don't have timestamps by default

            history.append(
                NavigationMessage(
                    role=role,
                    content=content,
                    timestamp=timestamp
                )
            )

        logger.info(f"Returning {len(history)} navigation history messages for learner {learner.user.id}")
        return history

    except Exception as e:
        logger.error(f"Error fetching navigation history for learner {learner.user.id}: {e}", exc_info=True)
        # Return empty history on error (graceful fallback)
        return []
