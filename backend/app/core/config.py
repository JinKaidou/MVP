"""Configuration settings loaded from environment variables."""
from typing import List
from pydantic import validator, field_validator
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # Project info
    PROJECT_NAME: str = "Campus Guide AI Backend"
    PROJECT_DESCRIPTION: str = "AI-powered campus guide using RAG"
    VERSION: str = "0.1.0"
    
    # API settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_KEY: str = os.getenv("API_KEY", "")
    
    # AI model settings
    # Default to a small, free Hugging Face model
    LLM_MODEL: str = os.getenv("LLM_MODEL", "google/flan-t5-small")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Vector store settings
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "data/faiss_index")
    
    # Optional OpenAI settings (not required)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"

settings = Settings() 