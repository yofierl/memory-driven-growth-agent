from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="memory-driven-growth-agent", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="growth_agent", alias="MONGODB_DATABASE")
    mongodb_collection_prefix: str = Field(default="", alias="MONGODB_COLLECTION_PREFIX")

    vector_backend: str = Field(default="milvus", alias="VECTOR_BACKEND")
    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    milvus_collection: str = Field(default="memory_embeddings", alias="MILVUS_COLLECTION")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")

    langgraph_checkpoint_dir: Path = Field(
        default=Path(".checkpoints"),
        alias="LANGGRAPH_CHECKPOINT_DIR",
    )
    agent_node_timeout_seconds: int = Field(default=60, alias="AGENT_NODE_TIMEOUT_SECONDS")

    disclaimer_text_path: Path = Field(
        default=Path("app/agent/prompts/disclaimer.md"),
        alias="DISCLAIMER_TEXT_PATH",
    )
    risk_keywords_path: Path = Field(
        default=Path("app/agent/prompts/risk_keywords.md"),
        alias="RISK_KEYWORDS_PATH",
    )
    prompt_dir: Path = Field(default=Path("app/agent/prompts"), alias="PROMPT_DIR")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "test", "production"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("vector_backend")
    @classmethod
    def validate_vector_backend(cls, value: str) -> str:
        if value != "milvus":
            raise ValueError("MVP supports VECTOR_BACKEND=milvus only")
        return value

    @field_validator("embedding_dimension")
    @classmethod
    def validate_embedding_dimension(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("EMBEDDING_DIMENSION must be a positive integer")
        return value

    @model_validator(mode="after")
    def validate_prompt_paths(self) -> "Settings":
        if not self.prompt_dir.exists():
            raise ValueError(f"PROMPT_DIR does not exist: {self.prompt_dir}")
        for path_value, label in (
            (self.disclaimer_text_path, "DISCLAIMER_TEXT_PATH"),
            (self.risk_keywords_path, "RISK_KEYWORDS_PATH"),
        ):
            if not path_value.exists():
                raise ValueError(f"{label} does not exist: {path_value}")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
