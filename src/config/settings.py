"""
Configuration settings for the code-to-documentation system.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="code_to_doc", env="DB_NAME")
    user: str = Field(default=os.getenv("USER", ""), env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    url: Optional[str] = Field(default=None, env="DATABASE_URL")

    @property
    def connection_url(self) -> str:
        """Get the database connection URL."""
        if self.url:
            return self.url
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class LLMSettings(BaseSettings):
    """LLM configuration settings."""

    openai_api_key: str = Field(env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    temperature: float = Field(default=0.1, env="TEMPERATURE")

class VectorSettings(BaseSettings):
    """Vector search configuration."""

    embedding_dimensions: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")

class AppSettings(BaseSettings):
    """Application configuration."""

    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)

    # LangChain settings
    langchain_tracing: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")

class Settings:
    """Main settings container."""

    def __init__(self):
        self.database = DatabaseSettings()
        self.llm = LLMSettings()
        self.vector = VectorSettings()
        self.app = AppSettings()

# Global settings instance
settings = Settings()

# Convenience functions
def get_db_config() -> dict:
    """Get database configuration as dictionary."""
    return {
        'host': settings.database.host,
        'port': settings.database.port,
        'database': settings.database.name,
        'user': settings.database.user,
        'password': settings.database.password
    }