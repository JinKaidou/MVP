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

# Campus locations dictionary with detailed information about buildings and directions
CAMPUS_LOCATIONS = {
    "arts_culture": "The Arts and Culture Building (ArCU, BLDG 1) is located in the northwestern section of campus near the sports facilities. From the main entrance, take the first right and follow the path past the tennis courts. The building will be on your left. It's in the Auxiliary Services Zone (Gray).",
    "integrated_tech": "Integrated Technology Building (BLDG 3) is found in the western part of campus. From the main entrance on Claro M. Recto Avenue, proceed straight and take the first left turn. The building will be on your right in the Academic Core Zone (Blue).",
    "rotc": "ROTC Building (BLDG 4) is located near the western boundary of campus. From the main gate, go straight and take the first left, then immediate left again. The building will be on your right beside the Old Engineering Building. It's in the Academic Core Zone (Blue).",
    "ict": "The ICT Building (BLDG 9) is situated in the southwestern quadrant of campus. From the main entrance, proceed straight until you reach the main campus intersection, then turn left. The ICT Building will be on your right after the Administration Building. This building houses the College of Information Technology and Computer Studies (CITC) and is in the Academic Core Zone (Blue).",
    "admin": "Administration Building (BLDG 10) is located in the central-western area of campus. From the main entrance, proceed straight until you reach the first major intersection and the building will be visible on your right in the Administration/Operation Zone (Purple).",
    "cafeteria": "Cafeteria (BLDG 20) is found in the southeastern area of campus. From the main entrance, follow the main road through campus, past the Science Complex, and continue until you reach the Commercial Zone. The Cafeteria will be on your left, marked in the Commercial Zone (Red).",
    "lrc": "Learning Resource Center (BLDG 23) is located in the central area of campus. From the main entrance, follow the main path straight ahead until you reach the second intersection, then turn right. The LRC will be on your left in the Academic Core Zone (Blue).",
    "science": "Science Complex (BLDG 36) is situated in the eastern part of campus. From the main entrance, follow the main road through campus and turn right at the second major intersection. The Science Complex will be ahead on your right. It's in the Administration/Operation Zone (Purple).",
    "student_center": "Student Center & Education Complex (BLDG 44) is located in the eastern section of campus. From the main gate, follow the main road through campus, past the Science Complex, and it will be on your right before reaching the Commercial Zone. It's in the Academic Core Zone (Blue).",
    "sports": "Sports Complex (BLDG 49) is situated in the northern area of campus. From the main entrance, take the first right and follow the curved path around the sports field. The Sports Complex will be visible on the north side of the track and field area. It's in the Sports and Recreation Zone (Light Green).",
    "dormitory": "Dormitory (BLDG 51) is located in the northeastern section of campus in the Residential Zone (Yellow). From the main entrance, follow the main path through campus, pass the Science Complex, then take the northeastern path to find it on your right.",
    "finance": "Finance and Accounting Building (BLDG 14) is located in the central area. From the main entrance, follow the main path until you reach the central square, then proceed north, and the building will be on your left. It's in the Academic Core Zone (Blue).",
    "hrm": "HRM Building (BLDG 15) is situated in the central campus area. From the main entrance, follow the main path to the central square, then go northwest, and you'll find the building on your right. It's in the Academic Core Zone (Blue).",
    "culinary": "Culinary Building (BLDG 18) is located in the western campus area. From the main entrance, take the first left at the major intersection, then proceed north, and the building will be on your left. It's in the Academic Core Zone (Blue).",
    "science_centrum": "Science Centrum Building (BLDG 19) is found in the central campus. From the main entrance, proceed straight ahead to the central square, then continue north, and it will be on your right. It's in the Academic Core Zone (Blue).",
    "foods": "Foods Trade Building (BLDG 24) is situated in the eastern side of campus. From the main entrance, head straight, then take the eastern path at the central intersection, and you'll find it on your right. It's in the Academic Core Zone (Blue).",
    "old_education": "Old Education Building (BLDG 35) is located in the central area. From the main entrance, proceed straight to the central square, then head northeast, and the building will be on your left. It's in the Academic Core Zone (Blue).",
    "engineering": "Engineering Complex (BLDG 42 & 43) is located in the southeastern area. From the main entrance, head straight, pass the central square, and take the southeastern path to find it on your right. It's in the Academic Core Zone (Blue).",
    "technology": "Technology Building (BLDG 47) is found in the northeastern section. From the main entrance, follow the main path to the central square, then take the northeastern path to find it on your left. It's in the Academic Core Zone (Blue).",
    "basketball": "Basketball Court is located near the Sports Complex in the northern section of campus. It's in the Sports and Recreation Zone (Light Green).",
    "tennis": "Tennis Court is situated in the northwestern corner of campus. From the main entrance, head straight, then take the first right to find the tennis courts. It's in the Sports and Recreation Zone (Light Green).",
    "food_innovation": "Food Innovation Center (BLDG 25 & 26) is located in the eastern section. From the main entrance, proceed straight, pass the central square, and take the eastern path to find it on your left. It's in the Research Zone (Teal).",
    "fab_lab": "Fabrication Laboratory (BLDG 48) is found in the northeastern section. From the main entrance, proceed to the central square, then take the northeastern path to find it on your right. It's in the Research Zone (Teal).",
    "residences": "Residences (BLDG 53) are situated in the eastern section of campus. From the main entrance, proceed straight, pass the central square, and take the eastern path to find the residences on your right. They're in the Residential/Dormitory Zone (Yellow).",
    "rer_hall": "RER Memorial Hall (BLDG 16) is situated in the western area. From the main entrance, follow the main path and take the first left to find it on your left. It's in the Auxiliary Services Zone (Gray).",
    "guard_house": "Guard House (BLDG 21) is located near the southern entrance of the campus on Claro M. Recto Avenue. It's in the Auxiliary Services Zone (Gray).",
    "old_medical": "Old Medical Building (BLDG 27) is found in the central campus area. From the main entrance, proceed to the central square and take the eastern path to find it on your left. It's in the Auxiliary Services Zone (Gray).",
    "old_science": "Old Science Building (BLDG 28) is located in the central-eastern section. From the main entrance, proceed to the central square and take the eastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
    "supply": "Supply Office (BLDG 45) is situated in the eastern section. From the main entrance, follow the main path straight, pass the central square, and continue east to find it on your left. It's in the Auxiliary Services Zone (Gray).",
    "faculty_lrc": "Faculty Learning Resource Center (BLDG 50) is located in the northeastern area. From the main entrance, proceed to the central square, then take the northeastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
    "sped": "SPED Building (BLDG G) is located in the southeastern area. From the main entrance, follow the main path straight, pass the central square, and take the southeastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
    "map": "To view a physical map of the USTP campus, please visit the Administration Building or the Guard House at the main entrance. Digital maps are available on the official USTP website and at kiosk stations around campus.",
    "registrar": "The Registrar's Office is located in the Learning Resource Center (LRC) Building 23, on the ground floor. From the main entrance, follow the main path straight ahead until you reach the second intersection, then turn right. The LRC will be on your left in the Academic Core Zone (Blue).",
    "old_engineering": "The Old Engineering Building (BLDG 5) is located beside the ROTC Building in the western section of campus. From the main entrance, proceed straight, take the second left, and it will be directly ahead of you. It's in the Academic Core Zone (Blue).",
    "sports_field": "The Sports Field and Track are found in the northern section of campus, visible from most areas. From the main entrance, proceed straight, then take the northern path at the central square. It's in the Sports and Recreation Zone (Light Green).",
    "sump_pit": "The Sump Pit (BLDG 52) is found in the eastern section of campus. From the main entrance, proceed straight, pass the central square, and take the eastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
    "fic_extension": "The FIC Extension (BLDG 54) is located in the eastern area of campus. From the main entrance, follow the main path straight, pass the central square, and take the eastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
    "toilet": "The Toilet facilities (BLDG F) are situated in the northeastern section of campus. From the main entrance, proceed to the central square, then take the northeastern path to find them on your right. They're in the Auxiliary Services Zone (Gray).",
    "citc": "The College of Information Technology and Computer Studies (CITC) is located in the ICT Building (BLDG 9) in the southwestern quadrant of campus. From the main entrance, proceed straight until you reach the main campus intersection, then turn left. The ICT Building will be on your right after the Administration Building. It's in the Academic Core Zone (Blue).",
    "cea": "The College of Engineering and Architecture (CEA) is housed in the Engineering Complex (BLDG 42 & 43) in the southeastern area of campus. From the main entrance, head straight, pass the central square, and take the southeastern path to find it on your right. It's in the Academic Core Zone (Blue).",
    "coed": "The College of Education (COED) is housed in the Education Complex (BLDG 44) in the eastern section of campus. From the main gate, follow the main road through campus, past the Science Complex, and it will be on your right before reaching the Commercial Zone. It's in the Academic Core Zone (Blue).",
    "cas": "The College of Arts and Sciences (CAS) is primarily located in the Science Complex (BLDG 36) in the eastern part of campus. From the main entrance, follow the main road through campus and turn right at the second major intersection. The Science Complex will be ahead on your right. It's in the Administration/Operation Zone (Purple).",
    "pat_avr": "The PAT-AVR (Physics, Architecture and Technology Audio-Visual Room) is located in the College of Engineering and Architecture (CEA) Building (Buildings 42 & 43) in the southeastern area of campus. From the main entrance, head straight, pass the central square, and take the southeastern path to find it on your right. This multi-purpose AVR is commonly used for presentations, seminars, and college activities in the Academic Core Zone (Blue).",
    "ict_avr": "The ICT-AVR (Information and Communications Technology Audio-Visual Room) is located in the ICT Building (BLDG 9) in the southwestern quadrant of campus. From the main entrance, proceed straight until you reach the main campus intersection, then turn left. The ICT Building will be on your right after the Administration Building. The AVR is on the second floor and is commonly used for IT-related presentations and activities. It's in the Academic Core Zone (Blue)."
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
    """Clean and normalize text while preserving important context."""
    if not isinstance(text, str):
        return ""
    
    # Updated preserved terms with the correct abbreviations
    preserved_terms = {
        "ICT": "_ICT_MARKER_",
        "CITC": "_CITC_MARKER_",
        "LRC": "_LRC_MARKER_",
        "ROTC": "_ROTC_MARKER_",
        "NSTP": "_NSTP_MARKER_",
        "CEA": "_CEA_MARKER_",
        "ArCU": "_ARCU_MARKER_",
        "COED": "_COED_MARKER_", 
        "CAS": "_CAS_MARKER_",
        "USTP": "_USTP_MARKER_",
        "FIC": "_FIC_MARKER_",
        "SPED": "_SPED_MARKER_",
        "CSM": "_CSM_MARKER_",
        "COT": "_COT_MARKER_",
        "SHS": "_SHS_MARKER_",
        "OSA": "_OSA_MARKER_"
    }
    
    # Preserve building numbers
    bldg_pattern = re.compile(r'(building|bldg\.?|b\.?)\s*(\d+)', re.IGNORECASE)
    matches = bldg_pattern.findall(text)
    building_markers = {}
    
    for match in matches:
        building_num = match[1]
        marker = f"_BUILDING_{building_num}_MARKER_"
        building_markers[f"{match[0]} {building_num}"] = marker
    
    # Apply all markers to preserve important terms
    processed_text = text
    for term, marker in {**preserved_terms, **building_markers}.items():
        # Case-insensitive replacement but preserve the original casing
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        processed_text = pattern.sub(marker, processed_text)
    
    # Convert to lowercase and remove special chars with some exceptions
    processed_text = re.sub(r'[^\w\s\-]', ' ', processed_text.lower())
    
    # Remove extra whitespace
    processed_text = re.sub(r'\s+', ' ', processed_text).strip()
    
    # Restore the preserved terms
    for term, marker in {**preserved_terms, **building_markers}.items():
        processed_text = processed_text.replace(marker.lower(), term.lower())
    
    return processed_text

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

def analyze_query_context(query):
    """Deeply analyze query context to understand user intent and entities."""
    query_lower = query.lower().strip()
    
    # Extract potential building names and abbreviations that might not be in our dictionary
    words = query_lower.split()
    potential_buildings = []
    
    # Look for building numbers
    bldg_number_pattern = re.compile(r'(building|bldg\.?|b\.?)\s*(\d+)', re.IGNORECASE)
    matches = bldg_number_pattern.findall(query_lower)
    for match in matches:
        potential_buildings.append(f"building {match[1]}")
    
    # Look for common building abbreviations (3-4 letter acronyms)
    abbreviation_pattern = re.compile(r'\b([a-z]{2,4})\b\s*(building|bldg|center|complex)?', re.IGNORECASE)
    matches = abbreviation_pattern.findall(query_lower)
    for match in matches:
        if len(match[0]) >= 2:  # Only consider abbreviations with 2+ characters
            potential_buildings.append(match[0])
    
    # Extract query type (question vs statement)
    is_question = any(q in query_lower for q in ["where", "how", "when", "what", "which", "?"])
    
    # Look for specific building-related context
    context = {
        "is_question": is_question,
        "potential_buildings": potential_buildings,
        "has_location_terms": any(term in query_lower for term in ["locate", "find", "get to", "direction", "where"]),
    }
    
    return context

def handle_campus_location_query(query):
    """Handle queries about campus locations with detailed directions."""
    query_lower = query.lower().strip()
    
    # Get deeper query context
    query_context = analyze_query_context(query)
    
    # Updated location keywords with the correct abbreviations and college names
    buildings = {
        "administration": ["admin", "administration", "admin building", "administration building", "bldg 10", "building 10"],
        "arts_culture": ["arcu", "arts and culture", "arts building", "bldg 1", "building 1", "arcu building"],
        "integrated_tech": ["integrated technology", "integrated tech", "bldg 3", "building 3", "technology building"],
        "rotc": ["rotc", "rotc building", "bldg 4", "building 4"],
        "ict": ["ict", "ict building", "bldg 9", "building 9", "information technology", "computer", "it building", "citc", "college of information technology and computer studies"],
        "cafeteria": ["cafeteria", "canteen", "food court", "bldg 20", "building 20", "where to eat", "dining", "lunch"],
        "lrc": ["lrc", "learning resource center", "library", "bldg 23", "building 23", "resource center"],
        "science": ["science complex", "science building", "bldg 36", "building 36", "old student center"],
        "student_center": ["student center", "education complex", "bldg 44", "building 44"],
        "sports": ["sports complex", "gym", "gymnasium", "bldg 49", "building 49", "sports center"],
        "dormitory": ["dorm", "dormitory", "residence hall", "bldg 51", "building 51", "where to stay"],
        "engineering": ["engineering", "engineering complex", "engineering building", "bldg 42", "building 42", "bldg 43", "building 43"],
        "registrar": ["registrar", "registrar's office", "registration", "transcript", "records"],
        "map": ["map", "campus map", "directions", "layout", "overview"],
        # Update college abbreviations
        "cea": ["cea", "cea building", "college of engineering and architecture", "engineering and architecture"],
        "citc": ["citc", "citc building", "college of information technology and computer studies", "information technology and computer studies"],
        "coed": ["coed", "coed building", "college of education", "education building"],
        "cas": ["cas", "cas building", "college of arts and sciences", "arts and sciences"],
        "old_engineering": ["old engineering", "old engineering building", "bldg 5", "building 5"],
        "finance": ["finance", "accounting", "finance and accounting", "bldg 14", "building 14", "shs", "senior high school", "senior high"],
        "hrm": ["hrm", "hrm building", "bldg 15", "building 15"],
        "culinary": ["culinary", "culinary building", "bldg 18", "building 18"],
        "science_centrum": ["science centrum", "centrum", "bldg 19", "building 19"],
        "foods": ["foods", "foods trade", "foods trade building", "bldg 24", "building 24"],
        "old_education": ["old education", "old education building", "bldg 35", "building 35"],
        "technology": ["technology", "technology building", "bldg 47", "building 47", "cot", "college of technology"],
        "sports_field": ["sports field", "track", "field", "sports track"],
        "basketball": ["basketball", "basketball court", "court"],
        "tennis": ["tennis", "tennis court"],
        "food_innovation": ["food innovation", "food innovation center", "fic", "bldg 25", "building 25", "bldg 26", "building 26"],
        "fab_lab": ["fab lab", "fabrication laboratory", "fabrication", "bldg 48", "building 48"],
        "residences": ["residences", "bldg 53", "building 53"],
        "rer_hall": ["rer", "rer hall", "rer memorial hall", "bldg 16", "building 16"],
        "guard_house": ["guard house", "guard", "security", "bldg 21", "building 21"],
        "old_medical": ["old medical", "medical", "old medical building", "bldg 27", "building 27", "clinic", "osa", "office of student affairs", "student affairs"],
        "old_science": ["old science", "old science building", "bldg 28", "building 28"],
        "supply": ["supply", "supply office", "bldg 45", "building 45"],
        "faculty_lrc": ["faculty lrc", "faculty learning resource center", "bldg 50", "building 50"],
        "sump_pit": ["sump pit", "bldg 52", "building 52"],
        "fic_extension": ["fic extension", "bldg 54", "building 54"],
        "toilet": ["toilet", "restroom", "bathroom", "bldg f", "building f"],
        "sped": ["sped", "sped building", "bldg g", "building g"],
        "science_complex_41": ["csm", "college of science and mathematics", "bldg 41", "building 41"],
        "pat_avr": ["pat-avr", "pat avr", "physics avr", "architecture avr", "technology avr", "cea avr", "engineering avr"],
        "ict_avr": ["ict-avr", "ict avr", "information technology avr", "computer avr", "citc avr"]
    }
    
    # Update CAMPUS_LOCATIONS with the complete information provided by the user
    # First, update existing entries with any corrections
    CAMPUS_LOCATIONS["arts_culture"] = "The Arts and Culture Building (ArCU, BLDG 1) is located in the northwestern section of campus near the sports facilities. From the main entrance, take the first right and follow the path past the tennis courts. The building will be on your left. It's in the Auxiliary Services Zone (Gray)."
    
    CAMPUS_LOCATIONS["ict"] = "The ICT Building (BLDG 9) is situated in the southwestern quadrant of campus. From the main entrance, proceed straight until you reach the main campus intersection, then turn left. The ICT Building will be on your right after the Administration Building. This building houses the College of Information Technology and Computer Studies (CITC) and is in the Academic Core Zone (Blue)."
    
    # Add CITC reference
    if "citc" not in CAMPUS_LOCATIONS:
        CAMPUS_LOCATIONS["citc"] = "The College of Information Technology and Computer Studies (CITC) is located in the ICT Building (BLDG 9) in the southwestern quadrant of campus. From the main entrance, proceed straight until you reach the main campus intersection, then turn left. The ICT Building will be on your right after the Administration Building. It's in the Academic Core Zone (Blue)."
    
    # Update college references
    if "cea" in CAMPUS_LOCATIONS:
        CAMPUS_LOCATIONS["cea"] = "The College of Engineering and Architecture (CEA) is housed in the Engineering Complex (BLDG 42 & 43) in the southeastern area of campus. From the main entrance, head straight, pass the central square, and take the southeastern path to find it on your right."
    
    # Add missing buildings that aren't in the CAMPUS_LOCATIONS dictionary
    new_locations = {
        "old_engineering": "The Old Engineering Building (BLDG 5) is located beside the ROTC Building in the western section of campus. From the main entrance, proceed straight, take the second left, and it will be directly ahead of you. It's in the Academic Core Zone (Blue).",
        
        "sports_field": "The Sports Field and Track are found in the northern section of campus, visible from most areas. From the main entrance, proceed straight, then take the northern path at the central square. It's in the Sports and Recreation Zone (Light Green).",
        
        "sump_pit": "The Sump Pit (BLDG 52) is found in the eastern section of campus. From the main entrance, proceed straight, pass the central square, and take the eastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
        
        "fic_extension": "The FIC Extension (BLDG 54) is located in the eastern area of campus. From the main entrance, follow the main path straight, pass the central square, and take the eastern path to find it on your right. It's in the Auxiliary Services Zone (Gray).",
        
        "toilet": "The Toilet facilities (BLDG F) are situated in the northeastern section of campus. From the main entrance, proceed to the central square, then take the northeastern path to find them on your right. They're in the Auxiliary Services Zone (Gray).",
        
        "science_complex_41": "The College of Science and Mathematics (CSM) is located in Building 41 in the eastern part of campus. From the main entrance, follow the main road through campus, past the central square, and take the eastern path to find it on your right. It's in the Academic Core Zone (Blue).",
        
        "old_medical": "Building 27 houses multiple facilities, including the Clinic on the ground floor and the Office of Student Affairs (OSA) on the second floor. From the main entrance, proceed to the central square and take the eastern path to find it on your left. It's in the Auxiliary Services Zone (Gray)."
    }
    
    # Update CAMPUS_LOCATIONS with new entries
    for key, value in new_locations.items():
        if key not in CAMPUS_LOCATIONS:
            CAMPUS_LOCATIONS[key] = value
    
    # ONLY match these explicit location question patterns
    strict_location_patterns = [
        "where is", "where are", "where can i find", "how do i get to", 
        "how to find", "how to get to", "location of", "directions to",
        "where's the", "where's", "tell me where", "show me where", 
        "how to reach", "how can i find", "i can't find", "i can not find",
        "can you tell me where", "need to find", "looking for the location",
        "i need to locate", "i need to find", "where exactly is", "give me directions to",
        "need directions to", "i need the location of", "where would i find"
    ]
    
    # More general location-related words, used only in conjunction with building names
    # and absence of non-location patterns
    location_related_words = [
        "located", "situated", "find", "location", "where", "building", 
        "directions", "map", "address", "place", "area", "room", "floor", 
        "near", "beside", "next to", "across from"
    ]
    
    # Patterns that strongly suggest the query is NOT about location
    non_location_patterns = [
        "report", "contact", "email", "call", "phone", "complain", "file", 
        "submit", "send", "process", "apply", "requirements", "working hours",
        "who is", "what does", "when does", "why is", "services", "provide",
        "function", "job", "role", "responsibility", "office hours", "open",
        "open hours", "close", "closed", "available", "schedule", "appointment",
        "document", "form", "payment", "pay", "fee", "cost", "how do i", 
        "how to", "help me", "assist", "registration", "enroll", "what is the",
        "how much", "when will", "inquiry", "inquire", "question about",
        "information about", "who should i", "who do i"
    ]
    
    # First check if the query contains a potential building abbreviation from our analysis
    for building_abbr in query_context["potential_buildings"]:
        for key, keywords in buildings.items():
            if building_abbr.lower() in [k.lower() for k in keywords]:
                # Check if it's a location question
                if query_context["is_question"] and query_context["has_location_terms"]:
                    return CAMPUS_LOCATIONS[key]
    
    # First, strictly check if the query contains non-location patterns
    # These would indicate the query is about something other than finding a location
    if any(pattern in query_lower for pattern in non_location_patterns):
        return None
    
    # Direct building reference check - improved to catch abbreviations like "CEA building"
    for key, keywords in buildings.items():
        for keyword in keywords:
            if keyword in query_lower:
                # If we have a strict location pattern, immediately return the location
                if any(pattern in query_lower for pattern in strict_location_patterns):
                    return CAMPUS_LOCATIONS[key]
                
                # If no explicit question pattern but still has location words, could be implicit
                if any(word in query_lower for word in location_related_words):
                    return CAMPUS_LOCATIONS[key]
    
    # Check if query exactly matches our strict location question patterns
    # This is the most reliable way to identify a true location question
    has_strict_location_pattern = any(pattern in query_lower for pattern in strict_location_patterns)
    
    if has_strict_location_pattern:
        # If we have a strict location pattern, look for building references
        for key, keywords in buildings.items():
            for keyword in keywords:
                # Look for the building name in the query
                if keyword in query_lower:
                    return CAMPUS_LOCATIONS[key]
    
    # If no strict pattern match, check for building name + location word proximity
    # This catches less explicit location questions
    building_mentioned = False
    building_key = None
    
    for key, keywords in buildings.items():
        for keyword in keywords:
            # Check if the keyword is mentioned as a complete word
            if (f" {keyword} " in f" {query_lower} " or 
                query_lower.startswith(f"{keyword} ") or 
                query_lower.endswith(f" {keyword}")):
                building_mentioned = True
                building_key = key
                # Check if any location words are in close proximity to the building name
                query_words = query_lower.split()
                keyword_words = keyword.split()
                
                # Find position of the keyword in the query
                for i in range(len(query_words) - len(keyword_words) + 1):
                    if ' '.join(query_words[i:i+len(keyword_words)]) == keyword:
                        # Check words before and after the keyword for location indicators
                        window_start = max(0, i - 3)
                        window_end = min(len(query_words), i + len(keyword_words) + 3)
                        context_window = ' '.join(query_words[window_start:window_end])
                        
                        if any(word in context_window for word in location_related_words):
                            return CAMPUS_LOCATIONS[key]
    
    # If the query is just "CEA building" or similar - handle these direct references
    query_words = query_lower.split()
    if len(query_words) <= 3:  # Short queries like "CEA building" or "where's CCS"
        for key, keywords in buildings.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return CAMPUS_LOCATIONS[key]
    
    # General campus map or building question (if no specific building but asking about locations)
    if has_strict_location_pattern and any(word in query_lower for word in ["building", "bldg", "room", "place", "area", "campus", "map"]):
        return """The USTP campus is organized into several zones:
        
- Academic Core Zone (Blue): Contains most teaching buildings including the LRC (Building 23)
- Sports and Recreation Zone (Light Green): Located in the northern area with the Sports Complex
- Research Zone (Teal): Located in the eastern section with the Food Innovation Center
- Administration Zone (Purple): Located in the central-western area with the Admin Building
- Residential Zone (Yellow): Located in the northeastern section with the Dormitory
- Commercial Zone (Red): Located in the southeastern area with the Cafeteria

For specific building directions, please ask about a particular building by name or number (e.g., "Where is the ICT Building?" or "How do I find Building 23?").

For a campus map, visit the Guard House at the main entrance or the Administration Building (BLDG 10)."""
    
    # Return None if we can't confidently identify this as a location query
    return None

def handle_special_queries(query):
    """Handle special queries with guided responses."""
    query_lower = query.lower().strip()
    
    # First pass: Check for WiFi or password specific queries
    # These are high-priority instant responses
    if "wifi" in query_lower or "password" in query_lower or "internet" in query_lower:
        wifi_patterns = ["password", "wifi password", "connect to wifi", "internet access"]
        if any(pattern in query_lower for pattern in wifi_patterns):
            return COMMON_FAQS["wifi access"]
    
    # Second pass: Check for campus location queries
    # This should only respond to very clear location questions
    location_response = handle_campus_location_query(query)
    if location_response:
        return location_response
    
    # Third pass: Check for sentiment/emotional queries
    sentiment_response = detect_sentiment(query_lower)
    if sentiment_response:
        return sentiment_response
    
    # Fourth pass: Check for greetings and help requests
    if query_lower in ["hello", "hi", "start", "hey", "good morning", "good afternoon", "good evening"]:
        greeting = get_time_greeting()
        return f"""# {greeting}Welcome to CampusGuide AI! 👋
        
I can help answer questions about:
- Academic policies and requirements
- Student services and organizations
- Campus facilities and resources
- Student rights and responsibilities
- Campus building locations and directions

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
7. **Campus Locations** - How to find buildings and facilities on campus

Try asking specific questions like "What is the grading system?", "Where is the ICT Building?", or "What are the admission requirements?"
"""
    
    # Personal state queries
    if query_lower in ["i am tired", "tired", "stressed", "stressed out"]:
        # Choose a random library to recommend from the available buildings
        libraries = {
            "LRC": "The Learning Resource Center (LRC, Building 23) has quiet study spaces and comfortable seating where you can relax and recharge. From the main entrance, follow the main path straight ahead until you reach the second intersection, then turn right. The LRC will be on your left in the Academic Core Zone (Blue).",
            "COT": "The College of Technology (COT, Building 47) library provides a peaceful environment away from the busy areas of campus. Located in the northeastern section, it has comfortable seating and good lighting. From the main entrance, follow the main path to the central square, then take the northeastern path to find it on your left.",
            "CEA": "The College of Engineering and Architecture (CEA) library in the Engineering Complex (Buildings 42 & 43) offers a calming atmosphere with study carrels and lounge areas. Located in the southeastern area, it's a great place to take a break and recharge. From the main entrance, head straight, pass the central square, and take the southeastern path to find it on your right.",
            "CSM": "The College of Science and Mathematics (CSM) library in Building 41 provides a serene environment with natural lighting and comfortable seating. Located in the eastern part of campus, it's perfect for relaxing while surrounded by books. From the main entrance, follow the main road through campus, past the central square, and take the eastern path to find it on your right."
        }
        
        # Select a random library
        library_key = random.choice(list(libraries.keys()))
        library_info = libraries[library_key]
        
        return f"""# Need a Break? Visit the {library_key} Library

I understand student life can be demanding. When you're feeling tired, sometimes a change of environment can help:

{library_info}

This quiet space is perfect for:
- Taking a short break from a busy schedule
- Finding a comfortable spot to relax and recharge
- Reading in a peaceful environment
- Having a quiet moment to yourself

If you're feeling overwhelmed beyond needing a short break, consider speaking with the Guidance and Counseling Services: https://www.facebook.com/ustpgsucdo
"""
    
    # Handle hungry queries
    elif any(word in query_lower for word in ["hungry", "food", "eat", "i am hungry", "starving", "need to eat", "want food"]):
        cafeteria_info = CAMPUS_LOCATIONS["cafeteria"]
        return f"""# Hungry? Head to the Cafeteria!

{cafeteria_info}

The cafeteria (Building 20) offers a variety of food options to satisfy your hunger:
- Full meals
- Snacks and quick bites
- Beverages and refreshments
- Affordable student-friendly prices

There are also several food stalls around campus that offer different food options.

Typical cafeteria hours are from 7:00 AM to 7:00 PM on weekdays, but some food stalls may have different operating hours.
"""
    
    # Fifth pass: Check for specific FAQ patterns with enhanced pattern matching
    # WiFi related queries - Enhanced pattern matching
    if any(word in query_lower for word in ["wifi", "password", "internet", "connection", "network"]):
        # Check for common WiFi question patterns
        wifi_patterns = [
            "what is the wifi", "what's the wifi", "wifi password", "password for wifi", 
            "connect to wifi", "internet password", "ustp wifi", "campus wifi",
            "wifi access", "access the wifi", "where can i find the wifi",
            "how do i get wifi", "how to connect", "how to access"
        ]
        if any(pattern in query_lower for pattern in wifi_patterns) or ("wifi" in query_lower and any(word in query_lower for word in ["what", "how", "where", "tell", "know", "get"])):
            return COMMON_FAQS["wifi access"]
    
    # Enrollment related queries - Enhanced pattern matching
    if any(word in query_lower for word in ["enrollment", "enroll", "register", "registration", "admit", "admission"]):
        # Check for common enrollment question patterns
        enrollment_patterns = [
            "when is enrollment", "enrollment period", "enrollment date", "enrollment schedule",
            "when can i enroll", "when does enrollment", "enrollment start", "start of enrollment",
            "how to enroll", "process of enrollment", "enrollment process", "where to enroll",
            "when is registration", "registration date", "registration period", "when can i register",
            "when is the start of classes", "when do classes begin", "school start"
        ]
        if any(pattern in query_lower for pattern in enrollment_patterns) or (any(word in query_lower for word in ["enrollment", "enroll", "register", "registration"]) and any(word in query_lower for word in ["when", "how", "where", "date", "schedule", "time", "start"])):
            return COMMON_FAQS["when is enrollment"]
    
    # Library hours queries - Enhanced pattern matching
    if "library" in query_lower:
        # Check for common library hours question patterns
        library_patterns = [
            "library hours", "library schedule", "library timing", "when is the library",
            "when does the library", "library open", "library close", "library time",
            "what time is the library", "what are the library hours", "library operation",
            "when can i go to the library", "is the library open", "library availability",
            "the hours of the library", "tell me about library hours"
        ]
        if any(pattern in query_lower for pattern in library_patterns) or ("library" in query_lower and any(word in query_lower for word in ["when", "hour", "time", "open", "close", "schedule", "available"])):
            return COMMON_FAQS["library hours"]
    
    # Lost and found queries - Enhanced pattern matching
    if any(word in query_lower for word in ["lost", "found", "missing", "misplaced", "dropped"]):
        # Check for common lost and found question patterns
        lost_patterns = [
            "lost and found", "lost something", "found something", "if i lost", "where to go if i lost",
            "what if i found", "how to find lost", "where to report lost", "where to claim found",
            "where to go for lost", "i lost my", "found a", "missing item", "misplaced my",
            "someone lost", "where to find lost", "how to recover lost"
        ]
        if any(pattern in query_lower for pattern in lost_patterns) or (any(word in query_lower for word in ["lost", "found", "missing"]) and any(word in query_lower for word in ["where", "how", "what", "report", "item", "object", "belonging"])):
            return COMMON_FAQS["lost and found"]
    
    # Add more exceptions for question keywords that might lead to misunderstanding
    if "example" in query_lower or "like" in query_lower or "such as" in query_lower:
        # Treat as a regular query, not a special one
        pass
    
    # Final pass: Check for any exact matches in our FAQ dictionary
    for key, response in COMMON_FAQS.items():
        if key in query_lower:
            return response
    
    # Return None if not a special query - will fall back to RAG
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
            
        # Analyze query for better understanding
        query_analysis = analyze_query_intent(query)
        query_type = query_analysis["query_type"]
        focus_areas = query_analysis["focus_areas"]
            
        # Create a system prompt that helps the model better understand how to respond
        system_prompt = """You are CampusGuide AI, a helpful assistant exclusively for USTP (University of Science and Technology of the Philippines) students.
Your knowledge comes from the USTP Student Handbook. Follow these guidelines carefully:

1. ONLY use information from the provided handbook context
2. If the handbook doesn't contain the answer, say "I don't have that information in the Student Handbook."
3. NEVER make up information not present in the context
4. Present information in a structured, easy-to-read format
5. Use markdown for formatting (headings, lists, emphasis)
6. For procedures or requirements, always present them as numbered steps
7. At the end of your response, if appropriate for the query, add a relevant USTP Facebook page link
8. Be direct and responsive - address exactly what was asked"""
        
        # Customize the prompt based on query analysis
        if query_type == "location":
            system_prompt += """
9. For location questions, include specific directions with landmark references
10. Mention which campus zone (color-coded area) the location is in
11. Be precise about building numbers"""
        elif query_type == "procedure":
            system_prompt += """
9. For procedure questions, present steps in a clear, numbered format
10. Include any deadlines, requirements, or forms needed
11. Specify where/who to contact for each step"""
        elif query_type == "policy":
            system_prompt += """
9. For policy questions, cite specific handbook sections
10. Explain the rationale and implications when possible
11. Clarify any conditions or exceptions to the policy"""
        
        # Focus area customization
        focus_instructions = {
            "academic": "When discussing academic matters, include grading policies, class attendance, and academic requirements.",
            "administrative": "For administrative topics, mention relevant offices, contact methods, and processing times.",
            "student_life": "When covering student life, emphasize student rights, responsibilities, and available resources.",
            "facilities": "When describing facilities, mention operating hours, access procedures, and usage policies."
        }
        
        for area in focus_areas:
            if area in focus_instructions:
                system_prompt += f"\n• {focus_instructions[area]}"
        
        # Prepare improved RAG prompt for better formatting and accuracy
        prompt = f"""{system_prompt}

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

def analyze_query_intent(query):
    """Analyzes the query to determine its type and focus areas."""
    query_lower = query.lower().strip()
    
    # Determine query type
    query_type = "general"
    
    # Check for location queries
    location_indicators = ["where", "location", "find", "building", "office", "campus", "room", "area"]
    if any(indicator in query_lower for indicator in location_indicators):
        query_type = "location"
    
    # Check for procedure queries
    procedure_indicators = ["how to", "how do i", "steps", "process", "procedure", "apply", "register", "submit", "enroll"]
    if any(indicator in query_lower for indicator in procedure_indicators):
        query_type = "procedure"
    
    # Check for policy queries
    policy_indicators = ["policy", "rule", "regulation", "allow", "permit", "prohibited", "requirement", "code of conduct"]
    if any(indicator in query_lower for indicator in policy_indicators):
        query_type = "policy"
    
    # Determine focus areas
    focus_areas = []
    
    # Academic focus
    academic_indicators = ["class", "course", "grade", "academic", "subject", "degree", "thesis", "study", "faculty", "professor", "instructor", "exam", "test"]
    if any(indicator in query_lower for indicator in academic_indicators):
        focus_areas.append("academic")
    
    # Administrative focus
    administrative_indicators = ["form", "office", "document", "deadline", "submission", "request", "administration", "requirement", "application", "enroll", "register", "payment", "fee"]
    if any(indicator in query_lower for indicator in administrative_indicators):
        focus_areas.append("administrative")
    
    # Student life focus
    student_life_indicators = ["organization", "club", "activity", "event", "dormitory", "housing", "dorm", "residence", "cafeteria", "food", "service", "scholarship", "financial", "stipend"]
    if any(indicator in query_lower for indicator in student_life_indicators):
        focus_areas.append("student_life")
    
    # Facilities focus
    facilities_indicators = ["library", "gym", "laboratory", "lab", "computer", "internet", "wifi", "facility", "room", "building", "sports", "equipment"]
    if any(indicator in query_lower for indicator in facilities_indicators):
        focus_areas.append("facilities")
    
    return {
        "query_type": query_type,
        "focus_areas": focus_areas
    }

def get_response_from_query(query, top_k=6):
    """Get response from the CSV data based on the query."""
    global csv_data, vectorizer, tfidf_matrix, content_column
    
    if not index_ready:
        return "I'm still loading my knowledge base. Please try again in a moment."
    
    try:
        # First check for any direct location queries which we want to handle specially 
        location_response = handle_campus_location_query(query)
        if location_response:
            return location_response
            
        # Check for any special queries before using the vector search
        special_response = handle_special_queries(query)
        if special_response:
            return special_response
            
        # Create expanded query with additional context if needed
        expanded_query = query
        
        # Expand abbreviations in the query to improve search results
        abbr_expansions = {
            "ict": "information and communications technology ict",
            "citc": "college of information technology and computer studies citc",
            "lrc": "learning resource center lrc library",
            "rotc": "reserve officers training corps rotc",
            "nstp": "national service training program nstp",
            "cea": "college of engineering and architecture cea",
            "arcu": "arts and culture building arcu",
            "coed": "college of education coed",
            "cas": "college of arts and sciences cas",
            "fic": "food innovation center fic",
            "csm": "college of science and mathematics csm",
            "cot": "college of technology cot",
            "shs": "senior high school shs",
            "osa": "office of student affairs osa"
        }
        
        # Check if query contains any abbreviations
        query_lower = query.lower()
        for abbr, expansion in abbr_expansions.items():
            if abbr in query_lower:
                expanded_query = f"{query} {expansion}"
                break
        
        # Preprocess the query
        processed_query = preprocess_text(expanded_query)
        
        # Transform the query using the vectorizer
        query_vector = vectorizer.transform([processed_query])
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get the top K most similar documents
        top_indices = similarity_scores.argsort()[-top_k:][::-1]
        
        # Check if we have relevant responses - lower threshold for better recall
        if similarity_scores[top_indices[0]] < 0.03:
            # Try to offer a helpful suggestion for a better query
            query_words = query_lower.split()
            suggestion = ""
            
            # Suggest more specific queries if the query is too short
            if len(query_words) < 3:
                suggestion = "Please try asking a more specific question. "
                
            # Suggest removing special characters if present
            if re.search(r'[^\w\s]', query):
                suggestion += "Try removing special characters from your query. "
            
            return f"I don't have specific information about that in the Student Handbook. {suggestion}Can you please rephrase your question or ask about a different topic?"
        
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