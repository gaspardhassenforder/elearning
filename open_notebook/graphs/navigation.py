import asyncio
import sqlite3
from typing import Annotated, Optional

from ai_prompter import Prompter
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from loguru import logger
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
from open_notebook.graphs.tools import search_available_modules
from open_notebook.utils import clean_thinking_content


class NavigationState(TypedDict):
    """State for navigation assistant workflow.

    Thread ID pattern: nav:user:{user_id}
    """
    messages: Annotated[list, add_messages]
    user_id: str
    company_id: str
    current_notebook_id: Optional[str]  # If learner is in a module conversation
    company_name: Optional[str]  # For prompt context
    current_module_title: Optional[str]  # For prompt context
    available_modules_count: int  # For prompt context


def navigation_node(state: NavigationState, config: RunnableConfig) -> dict:
    """Navigation assistant node.

    Assembles navigation prompt, invokes model with search_available_modules tool,
    and returns assistant response with module suggestions.
    """
    logger.info(f"navigation_node invoked for user {state.get('user_id')}")

    # Assemble navigation prompt with learner context
    prompt_data = {
        "company_name": state.get("company_name", "Unknown Company"),
        "current_module_title": state.get("current_module_title"),  # None if not in module
        "available_modules_count": state.get("available_modules_count", 0),
    }

    try:
        system_prompt = Prompter(prompt_template="navigation_assistant_prompt").render(
            data=prompt_data
        )
    except Exception as e:
        logger.error("Failed to render navigation prompt: {}", str(e), exc_info=True)
        # Fallback to minimal prompt
        system_prompt = "You are a helpful navigation assistant. Help learners find the right module."

    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    # Pass company_id and current_notebook_id through config for search_available_modules tool
    # Update config to include these for tool access
    company_id = state.get("company_id")
    current_notebook_id = state.get("current_notebook_id")

    configurable = config.get("configurable", {}) if config else {}
    if company_id:
        configurable["company_id"] = company_id
    if current_notebook_id:
        configurable["current_notebook_id"] = current_notebook_id

    # Update config dict (modify in place)
    if config:
        config["configurable"] = configurable
    else:
        config = {"configurable": configurable}

    # Handle async model provisioning from sync context (LangGraph node pattern)
    def run_in_new_loop():
        """Run the async function in a new event loop."""
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(
                provision_langchain_model(
                    str(payload),
                    model_id=None,  # Use default chat model
                    default_type="chat",
                    max_tokens=4096  # Navigation responses should be short
                )
            )
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in an event loop, run in a thread with a new loop
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            model = future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        model = asyncio.run(
            provision_langchain_model(
                str(payload),
                model_id=None,
                default_type="chat",
                max_tokens=4096,
            )
        )

    # Bind search_available_modules tool to model
    # Tool needs company_id and current_notebook_id from state, but LangChain tools
    # don't support passing these as context. We'll need to inject them via config.
    # For now, bind the tool and rely on the tool implementation to handle missing params.
    model_with_tools = model.bind_tools([search_available_modules])

    # Invoke model
    ai_message = model_with_tools.invoke(payload, config=config)

    # Extract text content from potentially structured response
    content = ai_message.content

    # Handle structured content (list of dictionaries with 'text' field)
    if isinstance(content, list):
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

    logger.info(f"Navigation assistant response generated (length: {len(cleaned_content)})")

    return {"messages": cleaned_message}


# Initialize SQLite checkpoint storage for conversation persistence
# Thread ID pattern: nav:user:{user_id}
conn = sqlite3.connect(
    LANGGRAPH_CHECKPOINT_FILE,
    check_same_thread=False,
)
memory = SqliteSaver(conn)

# Build navigation graph
navigation_state = StateGraph(NavigationState)
navigation_state.add_node("navigate", navigation_node)
navigation_state.add_edge(START, "navigate")
navigation_state.add_edge("navigate", END)
navigation_graph = navigation_state.compile(checkpointer=memory)
