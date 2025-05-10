"""Dependency injection for FastAPI routes."""
from typing import Generator

from app.services.chat import ChatService
from app.services.ingest import IngestService
from app.db.vector_store import get_vector_store
from app.core.config import settings

def get_chat_service() -> ChatService:
    """Provide ChatService instance for dependency injection."""
    vector_store = get_vector_store()
    return ChatService(vector_store=vector_store, model_name=settings.LLM_MODEL)

def get_ingest_service() -> IngestService:
    """Provide IngestService instance for dependency injection."""
    vector_store = get_vector_store()
    return IngestService(vector_store=vector_store) 