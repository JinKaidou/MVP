import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader

# Define the embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def preprocess_text(text):
    # Clean and structure text
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_documents():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    pdf_path = "data/USTP Student Handbook 2023 Edition.pdf"
    
    # Check if the PDF exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: {pdf_path} not found. Please make sure it exists.")
        return
    
    # Load the PDF
    print(f"Loading PDF from {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    # Print the first few pages to debug content
    print(f"Loaded {len(pages)} pages from PDF")
    if len(pages) > 0:
        print(f"First page preview: {pages[0].page_content[:200]}...")
    
    # Pre-process text to improve content
    processed_pages = []
    for page in pages:
        # Remove extra whitespace and clean page content
        cleaned_text = preprocess_text(page.page_content)
        
        # Skip pages with minimal content (headers, footers, blank pages)
        if len(cleaned_text) > 100:
            page.page_content = cleaned_text
            processed_pages.append(page)
    
    print(f"Processed {len(processed_pages)} content-rich pages")
    
    # Create smaller chunks with more overlap for better context
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Smaller chunks for more precise retrieval
        chunk_overlap=100,  # Good overlap to maintain context
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        length_function=len
    )
    
    documents = text_splitter.split_documents(processed_pages)
    
    # Add metadata and improve chunk quality
    quality_documents = []
    for i, doc in enumerate(documents):
        # Skip very short chunks (likely headers or footers)
        if len(doc.page_content) < 50:
            continue
            
        doc.metadata["source"] = "USTP Student Handbook"
        doc.metadata["chunk_id"] = i
        
        # Try to extract section headings
        lines = doc.page_content.split('\n')
        for line in lines[:3]:  # Check first few lines for headings
            heading_match = re.search(r'^[IVX]+\.|\b(MISSION|VISION|SECTION|ARTICLE|CHAPTER)\b', line, re.IGNORECASE)
            if heading_match:
                doc.metadata["section"] = line.strip()
                break
        
        quality_documents.append(doc)
    
    # Print chunk stats
    print(f"Created {len(quality_documents)} quality chunks from {len(pages)} pages")
    if len(quality_documents) > 0:
        print(f"Sample chunk: {quality_documents[0].page_content[:150]}...")
    
    # Create and save the vector database
    db = FAISS.from_documents(quality_documents, embeddings)
    db.save_local("faiss_index")
    print(f"Vector database saved to 'faiss_index' folder")

if __name__ == "__main__":
    process_documents()