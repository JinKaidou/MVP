"""Vector database operations and connection management."""
from typing import Optional, Dict, Any, List
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain.vectorstores import FAISS
from langchain.schema import Document
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Wrapper for vector database operations."""
    
    def __init__(self, index_name: str = "campus_guide"):
        """Initialize FAISS vector store."""
        self.index_name = index_name
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index_path = f"data/{index_name}"
        self._initialize_faiss()
        
    def _initialize_faiss(self):
        """Initialize FAISS index or create if it doesn't exist."""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Check if index exists
            if os.path.exists(self.index_path):
                self.index = FAISS.load_local(self.index_path, self.embedding_model)
                logger.info(f"Loaded existing FAISS index from {self.index_path}")
            else:
                # Create an empty index with a placeholder document
                # This will be replaced when actual documents are added
                self.index = FAISS.from_texts(
                    ["This is a placeholder document"],
                    self.embedding_model
                )
                self.index.save_local(self.index_path)
                logger.info(f"Created new FAISS index at {self.index_path}")
                
        except Exception as e:
            logger.error(f"Error initializing FAISS: {str(e)}")
            raise ValueError(f"Failed to initialize FAISS: {str(e)}")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, query: str, top_k: int = 5, namespace: Optional[str] = None) -> List[Document]:
        """
        Search for similar documents in the vector store.
        
        Args:
            query: The query string to search for
            top_k: Number of results to return
            namespace: Ignored for FAISS (kept for compatibility)
            
        Returns:
            List of Document objects
        """
        try:
            # Create query embedding
            documents_with_scores = self.index.similarity_search_with_score(
                query, 
                k=top_k
            )
            
            # Extract just the documents
            documents = [doc for doc, score in documents_with_scores]
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise ValueError(f"Failed to search vector store: {str(e)}")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def upsert_documents(self, documents: List[Document], namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            namespace: Ignored for FAISS (kept for compatibility)
            
        Returns:
            Dict with operation status
        """
        try:
            # Add documents to FAISS index
            if not documents:
                return {"status": "success", "count": 0}
            
            # Create new index with the documents
            new_index = FAISS.from_documents(documents, self.embedding_model)
            
            # Merge with existing index if it exists
            if hasattr(self, 'index') and self.index is not None:
                self.index.merge_from(new_index)
            else:
                self.index = new_index
            
            # Save the updated index
            self.index.save_local(self.index_path)
            
            return {
                "status": "success",
                "count": len(documents),
                "namespace": namespace or "default"
            }
            
        except Exception as e:
            logger.error(f"Error upserting documents: {str(e)}")
            raise ValueError(f"Failed to upsert documents: {str(e)}")
    
    def get_langchain_retriever(self, namespace: Optional[str] = None):
        """Get a LangChain retriever for the vector store."""
        return self.index.as_retriever(search_kwargs={"k": 5})

def get_vector_store() -> VectorStore:
    """Factory function to get VectorStore instance."""
    return VectorStore() 