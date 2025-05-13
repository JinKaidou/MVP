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
from datetime import datetime  # For time-based greetings

app = Flask(__name__)
CORS(app)

# Global variables
csv_data = None
vectorizer = None
tfidf_matrix = None
index_ready = False
content_column = None  # Will be determined automatically
OLLAMA_URL = "http://localhost:11434/api/generate"  # Default Ollama API URL

# Facebook page links dictionary
FACEBOOK_PAGES = {
    "main": "https://www.facebook.com/USTPcagayan",
    "admission": "https://www.facebook.com/USTPAdScho",
    "student_affairs": "https://www.facebook.com/ustposacdo",
    "registrar": "https://www.facebook.com/registrarcdo",
    "library": "https://www.facebook.com/UstpLibrary",
    "guidance": "https://www.facebook.com/ustpgsucdo"
}

# Common FAQs that don't require handbook lookup
COMMON_FAQS = {
    "when is enrollment": "Enrollment dates are typically announced on the official USTP Facebook page. Please check https://www.facebook.com/USTPcagayan for the most current information.",
    "where is the registrar": "The Registrar's Office is located on Building 23 - LRC. For more information, contact them through https://www.facebook.com/registrarcdo",
    "library hours": "For current library hours and services, please visit the USTP Library Facebook page: https://www.facebook.com/UstpLibrary",
    "wifi access": "The current password for USTP WiFi is: [IloveUSTP!] for more information about campus WiFi access and IT services, please contact the IT department or visit the main USTP page: https://www.facebook.com/USTPcagayan",
    "lost and found": "Lost and found items are usually managed by the Office of Student Affairs. Please check with their Facebook page: https://www.facebook.com/ustposacdo"
}

# Usage tips to help users get better responses
USAGE_TIPS = [
    "💡 **Tip:** Ask specific questions for better answers (e.g., 'What is the grading system?' instead of 'Tell me about grades').",
    "💡 **Tip:** You can ask about specific sections of the handbook like 'What does the handbook say about student organizations?'",
    "💡 **Tip:** If my answer isn't helpful, try rephrasing your question with more details.",
    "💡 **Tip:** I work best with clear, direct questions about USTP policies and procedures.",
    "💡 **Tip:** You can ask follow-up questions to get more specific information about a topic."
]

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

def get_time_greeting():
    """Returns a time-appropriate greeting based on current hour."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning! "
    elif 12 <= hour < 17:
        return "Good afternoon! "
    else:
        return "Good evening! "

def detect_sentiment(query):
    """Detects negative sentiment in user queries and provides supportive responses."""
    query_lower = query.lower()
    
    # Detect frustration or negative emotions
    negative_terms = ["frustrated", "annoyed", "angry", "upset", "terrible", 
                      "awful", "worst", "bad experience", "complaint", "stupid", 
                      "useless", "not helpful", "doesn't work"]
    
    if any(term in query_lower for term in negative_terms):
        return """I understand this might be frustrating. Let me try to help you better.

For immediate assistance with urgent matters, please contact the relevant office directly:
- Student Affairs: https://www.facebook.com/ustposacdo
- Guidance Office: https://www.facebook.com/ustpgsucdo

Could you please try rephrasing your question with more specific details?"""
    
    return None

def handle_special_queries(query):
    """Handle special queries with guided responses."""
    query_lower = query.lower().strip()
    
    # Check for negative sentiment first
    sentiment_response = detect_sentiment(query_lower)
    if sentiment_response:
        return sentiment_response
    
    # Greeting and general help with time-based greeting
    if query_lower in ["hello", "hi", "start", "hey", "good morning", "good afternoon", "good evening"]:
        greeting = get_time_greeting()
        return f"""# {greeting}Welcome to CampusGuide AI! 👋
        
I can help answer questions about:
- Academic policies and requirements
- Student services and organizations
- Campus facilities and resources
- Student rights and responsibilities

{random.choice(USAGE_TIPS)}

How can I assist you today?"""
    
    # Help command
    if query_lower in ["help", "help me", "i need help", "what can you do"]:
        return """# How I Can Help You
        
I'm CampusGuide AI, your USTP Student Handbook assistant. Here are topics I can provide information about:

1. **Academic Regulations** - Admission, registration, grading system, attendance
2. **Student Rights** - Rights and responsibilities as outlined in the handbook
3. **Student Code of Conduct** - Rules and expectations for USTP students
4. **Student Organizations and Activities** - Information about campus groups
5. **Student Services** - Available services for students
6. **USTP Vision, Mission, and Core Values**

Try asking specific questions like "What is the grading system?" or "What are the admission requirements?"
"""
    
    # Personal state queries
    if query_lower in ["i am tired", "tired", "stressed", "stressed out"]:
        return """# USTP Student Support Information

I understand student life can be demanding. While the handbook doesn't specifically address feeling tired or stressed, I can guide you to relevant student services mentioned in the handbook.

If you're feeling overwhelmed, consider speaking with the Guidance and Counseling Services.

For more information, please visit: https://www.facebook.com/ustpgsucdo
"""
    
    # Enhanced FAQ matching with relevant keywords for each category
    # WiFi related queries
    if any(word in query_lower for word in ["wifi", "password", "internet", "connection", "network"]):
        return COMMON_FAQS["wifi access"]
        
    # Enrollment related queries
    if any(word in query_lower for word in ["enrollment", "enroll", "register", "registration", "when is class", "school start"]):
        return COMMON_FAQS["when is enrollment"]
        
    # Registrar location queries
    if any(word in query_lower for word in ["registrar", "where is registrar", "registrar office", "registrar location", "where to get transcript"]):
        return COMMON_FAQS["where is the registrar"]
        
    # Library hours queries
    if any(word in query_lower for word in ["library", "library hour", "when library open", "library schedule", "library timing"]):
        return COMMON_FAQS["library hours"]
        
    # Lost and found queries
    if any(word in query_lower for word in ["lost", "found", "lost item", "missing", "lost and found", "where to find lost"]):
        return COMMON_FAQS["lost and found"]
    
    # Standard key-in-query check as fallback
    for key, response in COMMON_FAQS.items():
        if key in query_lower:
            return response
    
    # Return None if not a special query
    return None

def get_rag_response(query, context_chunks, metadata=None):
    """Use Ollama to generate a RAG response based on retrieved context."""
    try:
        # Check if Ollama is running and mistral is available
        ollama_available = check_ollama()
        
        # Handle special queries first before checking Ollama
        special_response = handle_special_queries(query)
        if special_response:
            return special_response
        
        # If Ollama isn't available, fall back to a template-based response
        if not ollama_available:
            # System status message for technical difficulties
            if context_chunks:
                response = f"""⚠️ I'm currently experiencing technical difficulties with my AI system. Here's the basic information I found:

{' '.join(context_chunks[:3])}

For more detailed assistance, please contact the relevant office directly."""
                return response
            else:
                # Add a random usage tip for empty results
                tip = random.choice(USAGE_TIPS)
                return f"""⚠️ I'm currently experiencing technical difficulties with my AI system and couldn't find information about your query.

{tip}

For urgent matters, please contact the relevant office directly or check the USTP Facebook page: https://www.facebook.com/USTPcagayan"""
        
        # Prepare metadata string
        metadata_str = ""
        if metadata and isinstance(metadata, list):
            metadata_str = "Relevant sections: " + ", ".join(metadata[:3])
        
        # Join context chunks with clear separators
        context_text = ""
        for i, chunk in enumerate(context_chunks[:5]):
            context_text += f"\n\n[CHUNK {i+1}]\n{chunk}"
        
        # Prepare improved RAG prompt for better formatting and accuracy
        prompt = f"""You are CampusGuide AI, a helpful assistant exclusively for USTP (University of Science and Technology of the Philippines) students.
Your knowledge comes from the USTP Student Handbook. You must follow these guidelines carefully:

1. ONLY use information from the provided handbook context
2. If the handbook doesn't contain the answer, say "I don't have that information in the Student Handbook."
3. NEVER make up information not present in the context
4. Present information in a structured, easy-to-read format
5. Use markdown for formatting (headings, lists, emphasis)
6. For procedures or requirements, always present them as numbered steps
7. At the end of your response, if appropriate for the query, add: "For more information and updates, please visit the official USTP Facebook page: https://www.facebook.com/ustpofficial"

Below is the relevant information from the handbook:
---
{context_text}
---

{metadata_str}

Student Question: {query}

Provide a comprehensive, well-formatted answer based ONLY on the handbook information above.
For lists and procedures, use proper numbered or bulleted markdown formatting."""
        
        # Query Ollama with the RAG prompt
        response = query_ollama(prompt)
        
        if not response:
            # Fallback if Ollama fails, add usage tip
            tip = random.choice(USAGE_TIPS)
            return f"Based on the USTP Student Handbook:\n\n{context_chunks[0]}\n\n{tip}"
        
        # Add suggested follow-up questions based on topic
        query_lower = query.lower()
        if "admission" in query_lower or "enroll" in query_lower:
            response += "\n\n**Related questions you might ask:**\n- What are the admission requirements?\n- How do I apply for a scholarship?\n- What documents do I need for enrollment?"
        elif "grade" in query_lower or "academic" in query_lower:
            response += "\n\n**Related questions you might ask:**\n- What is the grading system?\n- What happens if I fail a subject?\n- What are the retention policies?"
        elif "organization" in query_lower or "club" in query_lower:
            response += "\n\n**Related questions you might ask:**\n- How do I join a student organization?\n- What student organizations are available?\n- What are the requirements for establishing a new organization?"
        
        # Add relevant Facebook page link if not already included in the response
        response_lower = response.lower()
        if not "facebook.com" in response_lower:
            # Determine which Facebook page to include based on query keywords
            fb_link = FACEBOOK_PAGES["main"]  # Default to main page
            
            if any(word in query_lower for word in ["admission", "application", "apply", "enroll"]):
                fb_link = FACEBOOK_PAGES["admission"]
            elif any(word in query_lower for word in ["student affairs", "organization", "club", "activity"]):
                fb_link = FACEBOOK_PAGES["student_affairs"]
            elif any(word in query_lower for word in ["registrar", "transcript", "record", "credential"]):
                fb_link = FACEBOOK_PAGES["registrar"]
            elif any(word in query_lower for word in ["library", "book", "borrow"]):
                fb_link = FACEBOOK_PAGES["library"]
            elif any(word in query_lower for word in ["guidance", "counseling", "mental health", "stress", "tired", "help", "advice", "personal problem"]):
                fb_link = FACEBOOK_PAGES["guidance"]
                
            # Only add Facebook link to relatively long responses (indicates it found information)
            if len(response) > 100 and not "i don't have that information" in response_lower:
                response += f"\n\nFor more information and updates, please visit the relevant USTP Facebook page: {fb_link}"
            
        # Only add a random usage tip to shorter or potentially unhelpful responses
        if len(response) < 200 and "i don't have that information" in response_lower:
            response += f"\n\n{random.choice(USAGE_TIPS)}"
            
        return response
    except Exception as e:
        print(f"Error in RAG: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple response with tip
        tip = random.choice(USAGE_TIPS)
        if context_chunks:
            return f"Based on the handbook: {context_chunks[0]}\n\n{tip}"
        else:
            return f"I don't have information about that in the Student Handbook.\n\n{tip}"

def get_response_from_query(query, top_k=6):
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
        
        # Check if we have relevant responses - lower threshold for better recall
        if similarity_scores[top_indices[0]] < 0.03:
            return "I don't have specific information about that in the Student Handbook. Can you please rephrase your question or ask about a different topic?"
        
        # Create context chunks for RAG
        context_chunks = []
        section_info = []
        
        for idx in top_indices:
            if similarity_scores[idx] > 0.03:  # Only include somewhat relevant results
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
                'response': "⚠️ I'm having trouble accessing my knowledge base. Please check with your administrator or try again later."
            }), 500
    
    # Get user message
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        start_time = time.time()
        
        # Check for special queries first
        special_response = handle_special_queries(user_message)
        if special_response:
            return jsonify({
                'response': special_response
            })
        
        # Get response from handbook
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
            'response': "⚠️ I apologize, but I encountered an error processing your request. Please try again or contact technical support if the problem persists."
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