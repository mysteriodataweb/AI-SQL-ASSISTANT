from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings. Overridable via .env / environment variables."""

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

    # --- Database ---
    database_path: str = "data/sales.db"

    # --- LLM provider: "ollama", "nvidia" or "gemini" ---
    llm_provider: str = "ollama"

    # Ollama (local, free)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M"
    ollama_temperature: float = 0.0
    # 0 = CPU only (reliable), 1+ = layers on GPU, -1 = default behavior
    ollama_num_gpu: int = 0

    # NVIDIA NIM on build.nvidia.com (free API credits)
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str = ""
    nvidia_model: str = "meta/llama-3.3-70b-instruct"
    nvidia_temperature: float = 0.0

    # Google Gemini (Gemini Developer API)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.0

    # --- Misc ---
    cors_origins: list[str] = ["http://localhost:3000"]
    max_rows_for_answer: int = 30

    @property
    def db_uri(self) -> str:
        return f"sqlite:///{BASE_DIR / self.database_path}"

    @property
    def db_path(self) -> Path:
        return BASE_DIR / self.database_path


@lru_cache
def get_settings() -> Settings:
    return Settings()
