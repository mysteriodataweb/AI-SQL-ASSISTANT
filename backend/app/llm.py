from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import get_settings


def get_chat_model(provider: str | None = None) -> tuple[object, str, str]:
    """Build a LangChain chat model for the configured provider.

    Returns (model, provider_name, model_name).
    """
    settings = get_settings()
    provider = (provider or settings.llm_provider).lower()

    if provider == "nvidia":
        if not settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. Get a free key at https://build.nvidia.com "
                "or switch back to the local Ollama provider."
            )
        model = ChatOpenAI(
            model=settings.nvidia_model,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            temperature=settings.nvidia_temperature,
        )
        return model, "nvidia", settings.nvidia_model

    if provider == "ollama":
        model = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.ollama_temperature,
            num_ctx=8192,
            reasoning=False,
        )
        return model, "ollama", settings.ollama_model

    raise ValueError(f"Unknown LLM provider '{provider}' (use 'ollama' or 'nvidia')")
