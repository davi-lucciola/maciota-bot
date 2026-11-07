from langchain.chat_models import BaseChatModel, init_chat_model

from maciota_bot.config import settings


def get_chat_model(model: str, *, temperature: float) -> BaseChatModel:
    return init_chat_model(
        model,
        model_provider='openai',
        base_url=settings.openrouter_api_url,
        api_key=settings.openrouter_api_key.get_secret_value(),
        temperature=temperature,
        disable_streaming=True,
    )
