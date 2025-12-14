"""
Application Configuration Settings

Manages environment variables, API configurations, and application settings.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class AppConfig:
    """Application configuration manager"""

    def __init__(self):
        """Initialize configuration from environment variables"""

        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.VECTOR_STORE_DIR = self.DATA_DIR / "vectorstore"

        # Training documents path
        self.TRAINING_DOCS_PATH = Path("/Users/wbo7/Library/CloudStorage/Box-Box/INFO 5940 - Fall 2025/Final Project/Front Desk Training Docs")

        # Create directories if they don't exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.VECTOR_STORE_DIR.mkdir(exist_ok=True)

        # LLM Configuration
        self.LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY", "")

        # Model Configuration - Using different models for different agents to optimize cost
        self.FAST_MODEL = os.getenv("FAST_MODEL", "gpt-3.5-turbo")  # For quick responses
        self.BALANCED_MODEL = os.getenv("BALANCED_MODEL", "gpt-4")  # For guest agent
        self.SMART_MODEL = os.getenv("SMART_MODEL", "gpt-4")  # For coach and report agents
        self.DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")

        # Vector Database Configuration
        self.VECTOR_DB_TYPE = "chromadb"
        self.CHROMA_PERSIST_DIR = str(self.VECTOR_STORE_DIR)
        self.CHROMA_COLLECTION_NAME = "hotel_training_docs"

        # Embedding Configuration
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        self.EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "https://api.openai.com/v1/embeddings")

        # RAG Configuration
        self.RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
        self.RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

        # Application Settings
        self.APP_NAME = "Hotel Guest Service Training System"
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"

        # Streamlit Configuration
        self.STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
        self.STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "localhost")

        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Session Management
        self.SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
        self.MAX_MESSAGE_HISTORY = int(os.getenv("MAX_MESSAGE_HISTORY", "50"))

        # Document Processing
        self.SUPPORTED_DOCUMENT_TYPES = [".txt", ".pdf", ".doc", ".docx", ".xlsx", ".xls"]
        self.MAX_DOCUMENT_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))

        # Validate critical settings
        self._validate_settings()

    def _validate_settings(self) -> None:
        """Validate critical configuration settings"""

        # Check for required API key
        if not self.LLM_API_KEY:
            print("WARNING: LLM_API_KEY not set. Please configure your API key in the .env file.")

        # Check if training documents directory exists
        if not self.TRAINING_DOCS_PATH.exists():
            print(f"WARNING: Training documents directory not found at {self.TRAINING_DOCS_PATH}")
            print("Please ensure the training documents are in the correct location.")

        # Validate model names are set
        models = [self.FAST_MODEL, self.BALANCED_MODEL, self.SMART_MODEL, self.DEFAULT_MODEL]
        if not all(models):
            print("WARNING: Some model names are not configured properly.")

    def get_current_timestamp(self) -> datetime:
        """Get current timestamp"""
        return datetime.now()

    def get_model_config(self, agent_type: str = "default") -> dict:
        """
        Get model configuration for specific agent type

        Args:
            agent_type: Type of agent (guest, coach, report, default)

        Returns:
            dict: Model configuration
        """
        model_map = {
            "guest": self.BALANCED_MODEL,
            "coach": self.SMART_MODEL,
            "report": self.SMART_MODEL,
            "default": self.DEFAULT_MODEL
        }

        return {
            "model": model_map.get(agent_type, self.DEFAULT_MODEL),
            "api_url": self.LLM_API_URL,
            "api_key": self.LLM_API_KEY
        }

    def get_rag_config(self) -> dict:
        """Get RAG system configuration"""
        return {
            "top_k": self.RAG_TOP_K,
            "similarity_threshold": self.RAG_SIMILARITY_THRESHOLD,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "collection_name": self.CHROMA_COLLECTION_NAME,
            "persist_dir": self.CHROMA_PERSIST_DIR
        }

    def get_embedding_config(self) -> dict:
        """Get embedding configuration"""
        return {
            "model": self.EMBEDDING_MODEL,
            "api_url": self.EMBEDDING_API_URL,
            "api_key": self.LLM_API_KEY
        }

    def is_debug_mode(self) -> bool:
        """Check if application is in debug mode"""
        return self.DEBUG

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"{self.APP_NAME} v{self.VERSION} - Debug: {self.DEBUG}"