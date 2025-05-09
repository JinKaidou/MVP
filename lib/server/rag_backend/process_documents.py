import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import re

# Define the embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def preprocess_text(text):
    # Clean and structure text
    text = re.sub(r'\s+', ' ', text)
    return text

def process_handbook():
    # Load the handbook
    with open("../venv/documents/cleaned_full.txt", "r", encoding="utf-8") as f:
        handbook_text = f.read()
    
    # Split by chapter or sections to preserve structure
    chapter_pattern = r'(Chapter \d+\.\s+[\w\s-]+)'
    article_pattern = r'(Art\.\s+\d+\.\s+[\w\s-]+)'
    
    # Create metadata-rich chunks with LARGER chunks and more overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,  # Increased from 1000
        chunk_overlap=500,  # Increased from 200
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    documents = text_splitter.create_documents([handbook_text])
    
    # Add section metadata
    for i, doc in enumerate(documents):
        chapter_match = re.search(chapter_pattern, doc.page_content)
        article_match = re.search(article_pattern, doc.page_content)
        
        doc.metadata["source"] = "USTP Student Handbook 2021"
        if chapter_match:
            doc.metadata["chapter"] = chapter_match.group(1)
        if article_match:
            doc.metadata["article"] = article_match.group(1)
        doc.metadata["chunk_id"] = i
    
    # Create and save the vector database
    db = FAISS.from_documents(documents, embeddings)
    db.save_local("faiss_index")
    print(f"Processed {len(documents)} document chunks")

if __name__ == "__main__":
    process_handbook()