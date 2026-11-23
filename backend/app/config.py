"""Configuration de l'application, lue depuis le fichier .env (ou les variables d'environnement)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de données PostgreSQL (avec l'extension pgvector)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/documind"

    # JWT
    jwt_secret: str = "change-moi-en-production-avec-une-longue-cle-secrete"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # Embeddings : "local" (sentence-transformers, gratuit, tourne sur CPU) ou "fake" (tests)
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # LLM : "groq", "gemini" ou "fake" (tests / démo sans clé)
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # RAG
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5

    # Fichiers
    upload_dir: str = "uploads"
    max_upload_mb: int = 20

    # Frontend autorisé (CORS)
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
