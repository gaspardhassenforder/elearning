"""Admin chat router for admin assistant chatbot."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from loguru import logger
from ai_prompter import Prompter
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from api.auth import require_admin
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.learning_objective import LearningObjective
from open_notebook.domain.module_prompt import ModulePrompt
from open_notebook.graphs.chat import graph as chat_graph
from open_notebook.domain.user import User
from open_notebook.observability.langsmith_handler import get_langsmith_callback


router = APIRouter(dependencies=[Depends(require_admin)])


# Request/Response models
class AdminChatRequest(BaseModel):
    """Request model for admin chat."""
    message: str = Field(..., description="Admin's message to the assistant")
    notebook_id: str = Field(..., description="Notebook ID for context")
    model_override: Optional[str] = Field(None, description="Optional model override")


class AdminChatResponse(BaseModel):
    """Response model for admin chat."""
    message: str = Field(..., description="Assistant's response")
    context_used: Dict[str, Any] = Field(..., description="Context that was used")


async def assemble_admin_context(notebook_id: str) -> Dict[str, Any]:
    """
    Assemble module context for admin assistant prompt.

    Args:
        notebook_id: ID of the notebook/module

    Returns:
        Dictionary with module context (title, documents, objectives, prompt)

    Raises:
        HTTPException: If notebook not found
    """
    # Load notebook
    notebook = await Notebook.get(notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    # Load sources (documents) with content summaries for RAG grounding
    sources = await notebook.get_sources()
    documents = []
    for source in sources:
        # Use get_context() to get formatted summary with key excerpts
        source_context = await source.get_context(context_size="short")
        documents.append({
            "title": source.title,
            "summary": source_context.get("summary", "No summary available"),
            "excerpt": source_context.get("content", "")[:500]  # First 500 chars for context
        })

    # Load learning objectives
    objectives = await LearningObjective.get_for_notebook(notebook_id, ordered=True)
    objectives_list = [{"text": obj.text} for obj in objectives]

    # Load module prompt if exists
    module_prompt = await ModulePrompt.get_by_notebook(notebook_id)
    prompt_text = module_prompt.system_prompt if module_prompt else None

    return {
        "module_title": notebook.title,
        "documents": documents,
        "objectives": objectives_list,
        "module_prompt": prompt_text
    }


@router.post("/admin/chat", response_model=AdminChatResponse)
async def admin_chat(
    request: AdminChatRequest,
    admin_user: User = Depends(require_admin)
):
    """
    Admin assistant chat endpoint.

    Provides AI assistance for module creation, prompt writing, and content decisions.
    Reuses existing LangGraph chat workflow with custom admin_assistant_prompt.

    Args:
        request: Chat request with message and notebook_id
        admin_user: Current admin user (from dependency)

    Returns:
        Assistant's response with context used

    Raises:
        HTTPException: 404 if notebook not found, 500 on errors
    """
    try:
        # Assemble module context
        context = await assemble_admin_context(request.notebook_id)

        # Render admin assistant prompt with context
        prompter = Prompter(prompt_template="admin_assistant_prompt")
        system_prompt = prompter.render(data=context)

        # Prepare chat graph state
        from langchain_core.messages import SystemMessage

        state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.message)
            ],
            "model_override": request.model_override
        }

        # Story 7.4: Create LangSmith callback for tracing (or None if not configured)
        langsmith_callback = get_langsmith_callback(
            user_id=admin_user.id,
            company_id=None,  # Admin user - no company context
            notebook_id=request.notebook_id,
            workflow_name="admin_assistant",
            run_name=f"admin_assistant:{admin_user.id}:{request.notebook_id}",
        )

        # Build callbacks list (empty if LangSmith not configured)
        callbacks = [langsmith_callback] if langsmith_callback else []

        # Invoke chat graph
        result = chat_graph.invoke(
            input=state,
            config=RunnableConfig(
                configurable={
                    "thread_id": f"admin_{admin_user.id}_{request.notebook_id}",
                    "model_id": request.model_override
                },
                callbacks=callbacks,  # Story 7.4: LangSmith tracing
            )
        )

        # Extract AI response
        messages = result.get("messages", [])
        ai_message = messages[-1] if messages else None

        if not ai_message:
            raise HTTPException(status_code=500, detail="No response from assistant")

        response_text = ai_message.content if hasattr(ai_message, "content") else str(ai_message)

        return AdminChatResponse(
            message=response_text,
            context_used={
                "module_title": context["module_title"],
                "documents_count": len(context["documents"]),
                "objectives_count": len(context["objectives"]),
                "has_module_prompt": context["module_prompt"] is not None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing admin chat: {str(e)}")
