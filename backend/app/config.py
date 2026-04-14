# Application settings loaded from environment variables via pydantic-settings.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "gemini"

    # Google AI Studio / Gemini (free tier)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    # Groq (free tier — uses Gemini for embeddings)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Anthropic (paid)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # OpenAI (paid)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Vector dimensions must match the embedding model output:
    #   gemini-embedding-001  → 3072
    #   text-embedding-3-small → 1536
    #   text-embedding-3-large → 3072
    embedding_dimensions: int = 768

    # RAG
    chunk_max_chars: int = 1600
    chunk_overlap_sentences: int = 1
    rag_top_k: int = 5

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/research_assistant"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "documents"

    # Server
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"


settings = Settings()
