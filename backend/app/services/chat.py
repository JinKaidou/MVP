"""Service for handling chat interactions with the AI model."""
from typing import List, Dict, Any, Optional, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import os

from langchain.prompts import PromptTemplate
from langchain.schema import Document
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer

from app.models.schema import Message
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat operations with AI models."""
    
    def __init__(self, vector_store, model_name: str = settings.LLM_MODEL):
        """Initialize with vector store and model configuration."""
        self.vector_store = vector_store
        self.model_name = model_name
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize LLM with HuggingFace
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.llm = pipeline(
            "text-generation",
            model=model_name,
            tokenizer=self.tokenizer,
            max_length=1024,
            temperature=0.3,
            top_k=50,
            top_p=0.95,
            do_sample=True,
        )
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def query(self, query: str, chat_history: Optional[List[Message]] = None) -> Dict[str, Any]:
        """Process a query and return an AI response with sources."""
        if chat_history is None:
            chat_history = []
            
        try:
            # Convert to the format expected by the chat function
            history_tuples = [(msg.role, msg.content) for msg in chat_history]
            
            # Get response from chat function
            response_text = self.chat(query, history_tuples)
            
            # Get source documents
            query_embedding = self.embedding_model.encode(query)
            source_documents = self.vector_store.search(
                query=query,
                top_k=5,
                namespace="student_handbook"
            )
            
            formatted_sources = self.format_sources(source_documents)
            
            return {
                "response": response_text,
                "sources": formatted_sources
            }
            
        except Exception as e:
            logger.error(f"Error in query: {str(e)}")
            raise ValueError(f"Failed to process query: {str(e)}")
    
    def chat(self, query: str, history: List[Tuple[str, str]]) -> str:
        """
        Generate a response based on query, history, and retrieved contexts.
        
        Args:
            query: The user's question
            history: List of (role, content) tuples representing chat history
            
        Returns:
            The assistant's response
        """
        try:
            # Retrieve relevant contexts from vector store
            results = self.vector_store.search(
                query=query,
                top_k=5,
                namespace="student_handbook"
            )
            
            # Format contexts into a single string
            contexts = "\n\n".join([doc.page_content for doc in results])
            
            # Create formatted prompt with contexts and history
            formatted_history = "\n".join([f"{role}: {content}" for role, content in history])
            
            prompt = f"""Instructions: You are CampusGuide AI, a helpful assistant for university students.
Based on the student handbook information below, provide accurate and helpful answers.
If the information is not in the handbook, politely say you don't have that information.

STUDENT HANDBOOK INFORMATION:
{contexts}

CHAT HISTORY:
{formatted_history}

USER: {query}

ASSISTANT:"""
            
            # Generate response with Hugging Face model
            response = self.llm(prompt, max_length=1024)[0]['generated_text']
            
            # Extract the assistant's reply from the response
            # Find where the assistant's response starts
            assistant_prefix = "ASSISTANT:"
            if assistant_prefix in response:
                answer = response.split(assistant_prefix)[-1].strip()
            else:
                # Fallback if the format isn't as expected
                answer = response.split(f"USER: {query}")[-1].strip()
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise ValueError(f"Failed to generate chat response: {str(e)}")
        
    def create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for the AI."""
        template = """You are CampusGuide AI, a helpful assistant for university students.
Answer the question based ONLY on the context provided below.
If the answer is not in the context, politely say you don't have that information.

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer:"""

        return PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=template
        )
        
    def format_sources(self, source_documents: List[Any]) -> List[Dict[str, Any]]:
        """Format source documents for the response."""
        formatted_sources = []
        
        for doc in source_documents:
            source = {
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata
            }
            formatted_sources.append(source)
            
        return formatted_sources 