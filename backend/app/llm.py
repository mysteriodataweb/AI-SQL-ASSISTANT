from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import get_settings


def get_chat_model(provider: str | None = None) -> tuple[object, str, str]:
    """Build a LangChain chat model for the configured provider.

    Returns (model, provider_name, model_name).
    """
    settings = get_settings()
    provider = (provider or settings.llm_provider).lower()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey "
                "or switch back to the local Ollama provider."
            )
        model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.gemini_temperature,
        )
        return model, "gemini", settings.gemini_model

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
            num_gpu=settings.ollama_num_gpu,
            reasoning=False,
        )
        return model, "ollama", settings.ollama_model

    raise ValueError(f"Unknown LLM provider '{provider}' (use 'ollama', 'nvidia' or 'gemini')")


def build_fallback_providers(provider: str | None = None) -> list[tuple[str, object, str]]:
    """Ordered list of (provider_name, model, model_name) to try in sequence.

    The configured provider comes first, then local Ollama, then any other
    configured cloud provider. Used to fail over automatically (e.g. quota).
    """
    settings = get_settings()
    primary = (provider or settings.llm_provider).lower()

    names: list[str] = []
    for name in (primary, "ollama", "nvidia", "gemini"):
        if name in names:
            continue
        if name == "nvidia" and not settings.nvidia_api_key:
            continue
        if name == "gemini" and not settings.gemini_api_key:
            continue
        names.append(name)

    return [(provider_name, model, model_name) for model, provider_name, model_name in map(get_chat_model, names)]
