"""Configuration management for the Socratic Learning Companion."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Google Gemini API Configuration
    gemini_api_key: str

    # Database Configuration
    database_url: str = "sqlite:///./learning_companion.db"

    # ChromaDB Configuration
    chroma_persist_dir: str = "./data/embeddings/chroma_db"

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # Application Configuration
    app_name: str = "Socratic Learning Companion"
    app_version: str = "0.1.0"
    debug: bool = False

    # PDF Processing Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_chunk_size: int = 1000

    # Embedding Configuration
    embedding_model: str = "models/embedding-001"
    embedding_dimension: int = 768

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Paths
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory."""
        return self.project_root / "data"

    @property
    def raw_pdfs_dir(self) -> Path:
        """Get raw PDFs directory."""
        return self.data_dir / "raw_pdfs"

    @property
    def processed_dir(self) -> Path:
        """Get processed data directory."""
        return self.data_dir / "processed"

    @property
    def kleinberg_tardos_dir(self) -> Path:
        """Get Kleinberg-Tardos PDFs directory."""
        return self.raw_pdfs_dir / "kleinberg_tardos"

    @property
    def mit_lectures_dir(self) -> Path:
        """Get MIT lecture notes directory."""
        return self.raw_pdfs_dir / "mit_6006_lectures"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Export for convenience
settings = get_settings()
