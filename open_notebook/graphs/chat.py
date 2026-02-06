import asyncio
import sqlite3
from typing import Annotated, Optional

from ai_prompter import Prompter
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
from open_notebook.domain.notebook import Notebook
from open_notebook.graphs.tools import (
    surface_document,
    check_off_objective,
    surface_quiz,
    surface_podcast,
)
from open_notebook.utils import clean_thinking_content


class ThreadState(TypedDict):
    messages: Annotated[list, add_messages]
    notebook: Optional[Notebook]
    context: Optional[str]
    context_config: Optional[dict]
    model_override: Optional[str]
    system_prompt_override: Optional[str]  # Story 4.1: For learner chat with assembled prompts
    user_id: Optional[str]  # Story 4.4: For objective progress tracking


def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    # Story 4.1: Use system_prompt_override if provided (for learner chat)
    # Otherwise fall back to default admin chat prompt
    if state.get("system_prompt_override"):
        system_prompt = state["system_prompt_override"]
    else:
        system_prompt = Prompter(prompt_template="chat/system").render(data=state)  # type: ignore[arg-type]

    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    model_id = config.get("configurable", {}).get("model_id") or state.get(
        "model_override"
    )

    # Story 4.4: Pass user_id through config for check_off_objective tool
    # Extract from state if present, or from existing config
    user_id = state.get("user_id") or config.get("configurable", {}).get("user_id")
    if user_id:
        # Update config to include user_id for tool access
        configurable = config.get("configurable", {})
        configurable["user_id"] = user_id

    # Handle async model provisioning from sync context
    def run_in_new_loop():
        """Run the async function in a new event loop"""
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(
                provision_langchain_model(
                    str(payload), model_id, "chat", max_tokens=8192
                )
            )
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    # Determine which tools to bind based on context
    # Story 4.3: surface_document for document references
    # Story 4.4: check_off_objective for progress tracking (learner chat only)
    # Story 4.6: surface_quiz and surface_podcast for artifact surfacing
    tools = [surface_document, surface_quiz, surface_podcast]
    if user_id:
        # Only bind check_off_objective for learner chat (has user_id)
        tools.append(check_off_objective)

    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in an event loop, run in a thread with a new loop
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            model = future.result()

        # Story 4.3 + 4.4: Bind tools to the model
        model_with_tools = model.bind_tools(tools)
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        model = asyncio.run(
            provision_langchain_model(
                str(payload),
                model_id,
                "chat",
                max_tokens=8192,
            )
        )

        # Story 4.3 + 4.4: Bind tools to the model
        model_with_tools = model.bind_tools(tools)

    ai_message = model_with_tools.invoke(payload)

    # Extract text content from potentially structured response
    content = ai_message.content
    
    # Handle structured content (list of dictionaries with 'text' field)
    if isinstance(content, list):
        # Extract text from structured content (e.g., [{'type': 'text', 'text': '...'}])
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if 'text' in item:
                    text_parts.append(item['text'])
                elif 'type' in item and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
        content = '\n'.join(text_parts) if text_parts else str(content)
    elif not isinstance(content, str):
        content = str(content)
    
    # Clean thinking content from AI response (e.g., <think>...</think> tags)
    cleaned_content = clean_thinking_content(content)
    cleaned_message = ai_message.model_copy(update={"content": cleaned_content})

    return {"messages": cleaned_message}


conn = sqlite3.connect(
    LANGGRAPH_CHECKPOINT_FILE,
    check_same_thread=False,
)
memory = SqliteSaver(conn)

agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)
graph = agent_state.compile(checkpointer=memory)
