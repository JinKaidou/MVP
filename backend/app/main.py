"""Entrypoint: configures FastAPI, includes routers, and starts Uvicorn server."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import router as api_router
from app.core.config import settings

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_request_total", 
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Prometheus middleware
    Instrumentator().instrument(application).expose(application, endpoint="/metrics")
    
    # Include routers
    application.include_router(api_router, prefix="/api")
    
    @application.on_event("startup")
    async def startup_db_client():
        """Initialize database connections on startup."""
        # Add any startup logic here (e.g., initialize vector store)
        pass

    @application.on_event("shutdown")
    async def shutdown_db_client():
        """Close database connections on shutdown."""
        # Add any cleanup logic here
        pass
    
    return application

app = create_application()

# Custom middleware for request metrics
@app.middleware("http")
async def add_metrics(request, call_next):
    """Add metrics for requests."""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method, 
        endpoint=request.url.path
    ).observe(duration)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True) 