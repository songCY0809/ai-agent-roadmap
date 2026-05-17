"""Configuration loaded from .env / env vars via pydantic-settings.

Usage:
    from codemate.settings import settings
    print(settings.deepseek_api_key)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    local_llm_base_url: str = "http://localhost:8080"
    local_llm_model: str = "qwen2.5-coder-7b-q4_k_m"

    llm_default_backend: Literal["deepseek", "local"] = "deepseek"
    llm_fallback_backend: Literal["deepseek", "local"] = "local"

    embedding_backend: Literal["local", "openai"] = "local"
    embedding_model: str = "BAAI/bge-m3"

    vector_store: Literal["chroma", "milvus"] = "chroma"
    chroma_persist_dir: Path = Path("./data/chroma")
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    sqlite_path: Path = Path("./data/codemate.db")

    redis_url: str = "redis://localhost:6379/0"
    semantic_cache_threshold: float = 0.92

    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    leetcode_session: str = ""
    leetcode_csrftoken: str = ""
    leetcode_use_cn: bool = False

    log_level: str = "INFO"
    app_port: int = 8000


settings = Settings()
