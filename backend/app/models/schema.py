"""Pydantic models for request and response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    """Chat message model."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Chat request model."""
    query: str = Field(..., description="User's question or message")
    chat_history: Optional[List[Message]] = Field([], description="Previous messages in the conversation")
    
class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response to the user query")
    sources: Optional[List[Dict[str, Any]]] = Field([], description="Source documents used for the response")

class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    status: str
    document_id: str
    num_chunks: int 