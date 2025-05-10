"""API routes definition for chat and document operations."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, status
from typing import List, Optional, Dict, Any

from app.models.schema import ChatRequest, ChatResponse, IngestResponse
from app.services.chat import ChatService
from app.services.ingest import IngestService
from app.api.deps import get_chat_service, get_ingest_service
from app.core.config import settings

router = APIRouter()

# Request/Response models
class UploadHandbookResponse(IngestResponse):
    """Response model for handbook upload."""
    count: int

class ChatRequestModel(ChatRequest):
    """Request model for chat endpoint."""
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponseModel(ChatResponse):
    """Response model for chat endpoint."""
    reply: str

# Authentication dependency
async def verify_api_key(x_api_key: str = Header(..., description="API Key")):
    """Verify the API key."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

@router.post("/upload-handbook", response_model=UploadHandbookResponse, status_code=status.HTTP_201_CREATED)
async def upload_handbook(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
    ingest_service: IngestService = Depends(get_ingest_service)
):
    """Upload and process a student handbook PDF."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    result = await ingest_service.process_file(file)
    
    return {
        "status": "ok", 
        "document_id": result["document_id"],
        "num_chunks": result["num_chunks"],
        "count": result["num_chunks"]
    }

@router.post("/chat", response_model=ChatResponseModel)
async def chat(
    request: ChatRequestModel,
    api_key: str = Depends(verify_api_key),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Process a chat message and return a response."""
    # Convert history format if provided
    history = []
    if request.history:
        for msg in request.history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                history.append({"role": msg["role"], "content": msg["content"]})
    
    # Call the chat service
    result = await chat_service.query(request.message, history)
    
    return {
        "response": result["response"],
        "reply": result["response"],
        "sources": result.get("sources", [])
    }

@router.get("/health")
async def health_check():
    """Check if the API is running."""
    return {"status": "healthy"} 