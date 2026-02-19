import asyncio
import sqlite3
from typing import Annotated, Optional

import aiosqlite
from ai_prompter import Prompter
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
from open_notebook.domain.notebook import Notebook
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode

from open_notebook.graphs.tools import (
    surface_document,
    check_off_objective,
    surface_quiz,
    surface_podcast,
    search_knowledge_base,
    generate_artifact,
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


async def _prepare_model_and_payload(
    state: ThreadState, config: RunnableConfig
) -> tuple:
    """Shared logic: build system prompt, select tools, provision model.

    Used by the async learner node (call_model_async). Extracted so the sync
    admin node (call_model_with_messages) can stay untouched.
    """
    # System prompt selection (override vs template)
    if state.get("system_prompt_override"):
        system_prompt = state["system_prompt_override"]
    else:
        system_prompt = Prompter(prompt_template="chat/system").render(data=state)

    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    model_id = config.get("configurable", {}).get("model_id") or state.get("model_override")

    # Propagate user_id into config for tools
    user_id = state.get("user_id") or config.get("configurable", {}).get("user_id")
    if user_id:
        config.get("configurable", {})["user_id"] = user_id

    # Tool selection
    tools = [surface_document, surface_quiz, surface_podcast]
    if user_id:
        tools.extend([search_knowledge_base, generate_artifact])

    # Provision model (async — no ThreadPoolExecutor needed)
    model = await provision_langchain_model(str(payload), model_id, "chat", max_tokens=8192)
    model_with_tools = model.bind_tools(tools)

    return model_with_tools, payload


async def call_model_async(state: ThreadState, config: RunnableConfig) -> dict:
    """Async node for learner ReAct graph — enables proper token streaming.

    Unlike the sync call_model_with_messages, this node:
    - Calls provision_langchain_model() directly (no ThreadPoolExecutor hack)
    - Passes config to ainvoke() so LangGraph can intercept callbacks/streaming
    """
    model_with_tools, payload = await _prepare_model_and_payload(state, config)

    # KEY: pass config to enable LangGraph callback/streaming interception
    ai_message = await model_with_tools.ainvoke(payload, config=config)

    # Content extraction + thinking tag cleanup (same as sync version)
    content = ai_message.content
    if isinstance(content, list):
        text_parts = [item.get('text', '') for item in content if isinstance(item, dict) and 'text' in item]
        content = '\n'.join(text_parts) if text_parts else str(content)
    elif not isinstance(content, str):
        content = str(content)

    cleaned_content = clean_thinking_content(content)
    cleaned_message = ai_message.model_copy(update={"content": cleaned_content})
    return {"messages": cleaned_message}


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
    # Admin chat: surface tools only (no ToolNode execution, single-pass graph)
    # Learner chat: surface tools + search_knowledge_base + generate_artifact
    #   (executed via ToolNode in ReAct loop)
    tools = [surface_document, surface_quiz, surface_podcast]
    if user_id:
        # Learner chat gets retrieval and artifact generation tools
        tools.extend([search_knowledge_base, generate_artifact])

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


# Sync checkpointer for admin chat (graph.invoke)
conn = sqlite3.connect(LANGGRAPH_CHECKPOINT_FILE, check_same_thread=False)
memory = SqliteSaver(conn)

agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)
graph = agent_state.compile(checkpointer=memory)


# ---------------------------------------------------------------------------
# Learner ReAct graph: agent -> tools -> agent loop with safety limit
# ---------------------------------------------------------------------------

MAX_TOOL_ITERATIONS = 5

LEARNER_TOOLS = [
    surface_document,
    surface_quiz,
    surface_podcast,
    search_knowledge_base,
    generate_artifact,
]
# NOTE: check_off_objective removed from learner tools — handled by background examiner

tool_executor = ToolNode(tools=LEARNER_TOOLS, handle_tool_errors=True, name="tools")


def should_continue(state: ThreadState) -> str:
    """Route to tools node or end based on last message tool_calls."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"

    last_message = messages[-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "__end__"

    # Count consecutive tool rounds to enforce safety limit
    tool_rounds = 0
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            continue
        elif isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            tool_rounds += 1
        else:
            break

    if tool_rounds >= MAX_TOOL_ITERATIONS:
        return "__end__"

    return "tools"


learner_state = StateGraph(ThreadState)
learner_state.add_node("agent", call_model_async)
learner_state.add_node("tools", tool_executor)
learner_state.add_edge(START, "agent")
learner_state.add_conditional_edges(
    "agent", should_continue, {"tools": "tools", "__end__": END}
)
learner_state.add_edge("tools", "agent")


# ---------------------------------------------------------------------------
# Async checkpointer for learner chat (graph.astream_events)
# Must be initialized lazily because AsyncSqliteSaver requires a running event loop
# ---------------------------------------------------------------------------
_async_memory: Optional[AsyncSqliteSaver] = None
_async_graph = None


async def get_async_memory() -> AsyncSqliteSaver:
    """Get or create the async checkpoint saver (lazy singleton)."""
    global _async_memory
    if _async_memory is None:
        aconn = await aiosqlite.connect(LANGGRAPH_CHECKPOINT_FILE)
        # Patch for aiosqlite 0.22+ which removed is_alive() needed by AsyncSqliteSaver.setup()
        if not hasattr(aconn, "is_alive"):
            aconn.is_alive = lambda: True
        _async_memory = AsyncSqliteSaver(conn=aconn)
        await _async_memory.setup()
    return _async_memory


async def get_async_graph():
    """Get or create the async-compatible learner chat graph (lazy singleton).

    Uses the learner_state ReAct graph (agent <-> tools loop) instead of the
    single-pass admin agent_state graph.
    """
    global _async_graph
    if _async_graph is None:
        amemory = await get_async_memory()
        _async_graph = learner_state.compile(checkpointer=amemory)
    return _async_graph
