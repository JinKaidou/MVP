from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pandas as pd
import time
import re
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random

app = Flask(__name__)
CORS(app)

# Global variables
csv_data = None
vectorizer = None
tfidf_matrix = None
index_ready = False
content_column = None  # Will be determined automatically
OLLAMA_URL = "http://localhost:11434/api/generate"  # Default Ollama API URL

def preprocess_text(text):
    """Clean and normalize text."""
    if not isinstance(text, str):
        return ""
    # Convert to lowercase and remove special chars
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_csv_data():
    """Load and preprocess the CSV data."""
    global csv_data, vectorizer, tfidf_matrix, index_ready, content_column
    
    try:
        csv_path = "data/handbook.csv"
        if not os.path.exists(csv_path):
            print(f"ERROR: CSV file not found at: {csv_path}")
            return False
        
        print(f"Loading CSV from {csv_path}...")
        csv_data = pd.read_csv(csv_path)
        print(f"Loaded {len(csv_data)} rows from CSV")
        
        # Print the columns to debug
        print(f"CSV columns: {csv_data.columns.tolist()}")
        
        # Determine which column contains the main content
        # Try common column names
        possible_content_columns = ['content', 'text', 'information', 'data', 'handbook', 'description', 'Content']
        
        # Check which column exists
        for col in csv_data.columns:
            if col.lower() in [c.lower() for c in possible_content_columns]:
                content_column = col
                break
        
        # If no standard column found, use the column with the most text
        if not content_column:
            # Pick the column with the longest average text length
            text_lengths = {}
            for col in csv_data.columns:
                if csv_data[col].dtype == 'object':  # Only check string columns
                    avg_length = csv_data[col].astype(str).apply(len).mean()
                    text_lengths[col] = avg_length
            
            if text_lengths:
                content_column = max(text_lengths, key=text_lengths.get)
            else:
                # Fallback to the first string column
                for col in csv_data.columns:
                    if csv_data[col].dtype == 'object':
                        content_column = col
                        break
        
        if not content_column:
            print("ERROR: Could not determine content column")
            return False
        
        print(f"Using '{content_column}' as content column")
        
        # Preprocess the content
        print("Preprocessing content...")
        processed_column = f"processed_{content_column}"
        csv_data[processed_column] = csv_data[content_column].astype(str).apply(preprocess_text)
        
        # Create TF-IDF vectorizer
        print("Building TF-IDF index...")
        vectorizer = TfidfVectorizer(
            min_df=1, 
            max_df=0.9,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Build the TF-IDF matrix
        tfidf_matrix = vectorizer.fit_transform(csv_data[processed_column])
        
        print(f"TF-IDF index built with {tfidf_matrix.shape[1]} features")
        index_ready = True
        return True
    
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ollama():
    """Check if Ollama is running and Mistral model is available."""
    try:
        # Check Ollama API connection
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            print("Warning: Ollama server is not accessible")
            return False
        
        # Check if mistral model is available
        models = response.json().get("models", [])
        mistral_available = any(model.get("name", "").startswith("mistral") for model in models)
        
        if not mistral_available:
            print("Warning: Mistral model not found in Ollama. Pulling it now...")
            # You could automatically pull the model here, but it's better to instruct the user
            return False
        
        return True
    except Exception as e:
        print(f"Error checking Ollama: {e}")
        return False

def query_ollama(prompt, model="mistral"):
    """Query the Ollama API with the given prompt."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"Error from Ollama API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

def get_rag_response(query, context_chunks, metadata=None):
    """Use Ollama to generate a RAG response based on retrieved context."""
    try:
        # Check if Ollama is running and mistral is available
        ollama_available = check_ollama()
        
        # If Ollama isn't available, fall back to a template-based response
        if not ollama_available:
            # Simple templated response as fallback
            if context_chunks:
                response = f"Based on the USTP Student Handbook:\n\n{' '.join(context_chunks[:3])}"
                return response
            else:
                return "I don't have information about that in the Student Handbook."
        
        # Prepare metadata string
        metadata_str = ""
        if metadata and isinstance(metadata, list):
            metadata_str = "Relevant sections: " + ", ".join(metadata[:3])
        
        # Join context chunks
        context_text = "\n\n".join(context_chunks[:5])  # Limit to top 5 chunks to avoid token limits
        
        # Prepare RAG prompt
        prompt = f"""You are CampusGuide AI, a helpful assistant for USTP (University of Science and Technology of the Philippines) students.
Your knowledge comes from the USTP Student Handbook.

Below is the relevant information from the handbook:
---
{context_text}
---

{metadata_str}

Question: {query}

Provide a clear, accurate, and well-formatted answer based ONLY on the information above.
If the information doesn't contain the answer, say: "I don't have that information in the Student Handbook."
Format your answer in markdown with proper sections and bullet points where appropriate."""
        
        # Query Ollama with the RAG prompt
        response = query_ollama(prompt)
        
        if not response:
            # Fallback if Ollama fails
            return f"Based on the USTP Student Handbook:\n\n{context_chunks[0]}"
            
        return response
    except Exception as e:
        print(f"Error in RAG: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple response
        if context_chunks:
            return f"Based on the handbook: {context_chunks[0]}"
        else:
            return "I don't have information about that in the Student Handbook."

def get_response_from_query(query, top_k=5):
    """Get response from the CSV data based on the query."""
    global csv_data, vectorizer, tfidf_matrix, content_column
    
    if not index_ready:
        return "I'm still loading my knowledge base. Please try again in a moment."
    
    try:
        # Preprocess the query
        processed_query = preprocess_text(query)
        
        # Transform the query using the vectorizer
        query_vector = vectorizer.transform([processed_query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get the top K most similar documents
        top_indices = similarity_scores.argsort()[-top_k:][::-1]
        
        # Check if we have relevant responses
        if similarity_scores[top_indices[0]] < 0.05:
            return "I don't have specific information about that in the Student Handbook. Can you please rephrase your question or ask about a different topic?"
        
        # Create context chunks for RAG
        context_chunks = []
        section_info = []
        
        for idx in top_indices:
            if similarity_scores[idx] > 0.05:  # Only include somewhat relevant results
                # Get content
                content = str(csv_data.iloc[idx][content_column])
                
                # Try to get section info
                section = ""
                article = ""
                chapter = ""
                
                # Try to extract section, article and chapter info
                for col in csv_data.columns:
                    if 'section' in col.lower() and not section:
                        section = str(csv_data.iloc[idx][col])
                    elif 'article' in col.lower() and not article:
                        article = str(csv_data.iloc[idx][col])
                    elif 'chapter' in col.lower() and not chapter:
                        chapter = str(csv_data.iloc[idx][col])
                    elif 'title' in col.lower() and not section:
                        section = str(csv_data.iloc[idx][col])
                
                metadata = []
                if chapter and chapter != "nan":
                    metadata.append(f"Chapter: {chapter}")
                if article and article != "nan":
                    metadata.append(f"Article: {article}")
                if section and section != "nan":
                    metadata.append(f"Section: {section}")
                
                # Add to context
                context_chunks.append(content)
                
                # Create section reference
                if chapter or article or section:
                    section_text = ""
                    if chapter and chapter != "nan":
                        section_text += f"Chapter {chapter}"
                    if article and article != "nan":
                        section_text += f", Article {article}"
                    if section and section != "nan":
                        section_text += f", Section {section}"
                    
                    if section_text:
                        section_info.append(section_text.strip(", "))
        
        # Use RAG to get the final response
        response = get_rag_response(query, context_chunks, section_info)
        
        return response
    
    except Exception as e:
        print(f"Error generating response: {e}")
        import traceback
        traceback.print_exc()
        return "I encountered an error while processing your request. Please try again."

# Load data on startup
load_csv_data()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests from the frontend."""
    global index_ready
    
    # Check if index is ready
    if not index_ready:
        success = load_csv_data()
        if not success:
            return jsonify({
                'response': "I'm having trouble accessing my knowledge base. Please check the server logs."
            }), 500
    
    # Get user message
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        start_time = time.time()
        
        # Get response
        response = get_response_from_query(user_message)
        
        end_time = time.time()
        print(f"Response generated in {end_time - start_time:.2f} seconds")
        
        return jsonify({
            'response': response
        })
    
    except Exception as e:
        import traceback
        print(f"Error processing request: {e}")
        traceback.print_exc()
        
        return jsonify({
            'response': "I apologize, but I encountered an error processing your request. Please try again."
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    global index_ready
    
    if index_ready:
        return jsonify({'status': 'ready'}), 200
    else:
        return jsonify({'status': 'initializing'}), 200

if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=8000, debug=False)