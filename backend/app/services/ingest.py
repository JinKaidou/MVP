"""Service for document ingestion and preprocessing."""
from typing import List, Dict, Any, Optional
import os
import tempfile
from fastapi import UploadFile, HTTPException
import uuid
import logging

from langchain.document_loaders import PyPDFium2Loader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document

from app.db.vector_store import get_vector_store
from app.core.config import settings

logger = logging.getLogger(__name__)

class IngestService:
    """Service for ingesting documents into the vector store."""
    
    def __init__(self, vector_store):
        """Initialize with vector store client."""
        self.vector_store = vector_store
        self.embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    async def process_file(self, file: UploadFile) -> Dict[str, Any]:
        """Process a file upload and ingest into vector store."""
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save file temporarily
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(await file.read())
                temp_path = temp_file.name
            
            # Process the saved PDF
            result = self.ingest_handbook(temp_path, original_filename=file.filename)
            
            return {
                "status": "success",
                "document_id": result["document_id"],
                "num_chunks": result["num_chunks"]
            }
        
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def ingest_handbook(self, pdf_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Load PDF handbook, split into chunks and store in vector database.
        
        Args:
            pdf_path: Path to the PDF file
            original_filename: Original filename for metadata
            
        Returns:
            Dict with document_id and num_chunks
        """
        try:
            # Generate a document ID
            document_id = str(uuid.uuid4())
            
            # Load the PDF
            documents = self.load_pdf(pdf_path)
            
            # Add metadata
            for doc in documents:
                doc.metadata.update({
                    "document_id": document_id,
                    "source": original_filename or os.path.basename(pdf_path),
                    "type": "student_handbook"
                })
            
            # Split the documents
            chunks = self.split_documents(documents)
            
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Store in vector database
            result = self.ingest_documents(chunks, namespace="student_handbook")
            
            return {
                "document_id": document_id,
                "num_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error ingesting handbook: {str(e)}")
            raise ValueError(f"Failed to ingest handbook: {str(e)}")
        
    def load_pdf(self, file_path: str) -> List[Document]:
        """Load a PDF file and return documents."""
        try:
            loader = PyPDFium2Loader(file_path)
            documents = loader.load()
            logger.info(f"Loaded PDF with {len(documents)} pages")
            return documents
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            raise ValueError(f"Failed to load PDF: {str(e)}")
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        try:
            chunks = self.text_splitter.split_documents(documents)
            return chunks
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            raise ValueError(f"Failed to split documents: {str(e)}")
        
    def ingest_documents(self, documents: List[Document], namespace: str) -> Dict[str, Any]:
        """Ingest documents into vector store."""
        try:
            # Use the vector store to upsert documents
            result = self.vector_store.upsert_documents(documents, namespace=namespace)
            logger.info(f"Ingested {len(documents)} documents to namespace '{namespace}'")
            return result
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            raise ValueError(f"Failed to ingest documents: {str(e)}") 