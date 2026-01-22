from esperanto import LanguageModel
from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger

from open_notebook.ai.models import model_manager
from open_notebook.utils import token_count


async def provision_langchain_model(
    content, model_id, default_type, **kwargs
) -> BaseChatModel:
    """
    Returns the best model to use based on the context size and on whether there is a specific model being requested in Config.
    If context > 105_000, returns the large_context_model
    If model_id is specified in Config, returns that model
    Otherwise, returns the default model for the given type
    """
    # HARDCODED: Always use Gemini Flash 1.5 (Flash 3)
    # This bypasses the database model configuration entirely
    from esperanto import AIFactory
    
    logger.debug("Using hardcoded Gemini Flash 3 model")
    model = AIFactory.create_language(
        model_name="gemini-3-flash-preview",
        provider="google",
        config=kwargs,
    )
    
    # Original code (commented out - dynamic model selection from database)
    # tokens = token_count(content)
    # if tokens > 105_000:
    #     logger.debug(
    #         f"Using large context model because the content has {tokens} tokens"
    #     )
    #     model = await model_manager.get_default_model("large_context", **kwargs)
    # elif model_id:
    #     model = await model_manager.get_model(model_id, **kwargs)
    # else:
    #     model = await model_manager.get_default_model(default_type, **kwargs)
    # 
    # logger.debug(f"Using model: {model}")
    # 
    # if model is None:
    #     error_msg = (
    #         f"No default {default_type} model configured. "
    #         "Please go to Settings → Models and configure a default chat model before using the chat feature."
    #     )
    #     logger.error(error_msg)
    #     raise ValueError(error_msg)
    # 
    # if not isinstance(model, LanguageModel):
    #     error_msg = f"Model is not a LanguageModel: {model}"
    #     logger.error(error_msg)
    #     raise ValueError(error_msg)
    
    return model.to_langchain()
