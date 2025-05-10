# Campus Guide AI Backend

This is the backend server for the Campus Guide AI application, built with FastAPI and LangChain, using completely free models and tools.

## Features
- Uses Hugging Face's free models for text generation
- Uses Sentence Transformers for embeddings
- FAISS for local vector storage (no external API needed)
- Built with FastAPI for high performance

## Prerequisites

- Python 3.10+
- Poetry (dependency management)

## Installation

```bash
cd backend
poetry install
```

This will create a virtual environment and install all dependencies from the poetry.lock file.

## Environment Variables (Optional)

Create a `.env` file in the `backend/` directory with any of these optional settings:

```
# API Configuration (optional)
API_KEY=your-optional-api-key-for-security

# Model Settings (optional - defaults will be used if not set)
LLM_MODEL=google/flan-t5-small
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Vector Store Configuration (optional)
VECTOR_STORE_PATH=data/faiss_index
```

## Running the Server

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `POST /api/chat` - Send chat messages
- `POST /api/upload-handbook` - Upload PDF documents
- `GET /api/health` - Health check endpoint
- `GET /metrics` - Prometheus metrics

## Development

For development tasks:

```bash
# Run tests
poetry run pytest

# Format code (optional)
poetry run black .
``` 