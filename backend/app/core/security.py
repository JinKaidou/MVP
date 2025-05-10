"""Security and authentication utilities."""
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> bool:
    """
    Validate the API key if it's configured.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        bool: True if valid, raises exception otherwise
    
    Raises:
        HTTPException: If the API key is invalid
    """
    # If no API key is set in settings, skip validation
    if not settings.API_KEY:
        return True
        
    # If API key is required but not provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
        
    # Check if the API key is valid
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
        
    return True

async def get_current_api_user(valid: bool = Depends(validate_api_key)):
    """
    Dependency to get current API user with valid key.
    
    Args:
        valid: Result from validate_api_key dependency
        
    Returns:
        dict: User information (currently just a placeholder)
    """
    # This is a placeholder for potential user info in the future
    return {"authenticated": True} 