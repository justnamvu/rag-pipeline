from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RAG"
    environment: str = "development"
    opensearch_url: str
    opensearch_index_name: str = "rag_vectors"
    embeddings_api_key: str = ""
    embeddings_model: str = "text-embedding-3-small"
    llm_api_key: str = ""
    llm_model_name: str = "gpt-5.4-nano"
    max_file_size_mb: int = 10
    allowed_file_types: str = "pdf,txt,docx"


settings = Settings()
