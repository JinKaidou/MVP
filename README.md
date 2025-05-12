# CampusGuide AI

A smart AI assistant for USTP students that provides instant, accurate information from the Student Handbook.

<p align="center">
  <i>Developed by AbatuComp</i>
</p>

## 🌟 Overview

CampusGuide AI uses Retrieval Augmented Generation (RAG) technology to deliver precise answers to student queries about USTP policies, procedures, and guidelines. The system intelligently searches through the official Student Handbook to provide reliable information.

### Key Features

- **Instant Answers**: Get immediate responses to handbook-related questions
- **Accurate Information**: All answers sourced directly from official USTP documentation
- **24/7 Availability**: Access information anytime, anywhere
- **Intuitive Interface**: Modern UI with chat history and interactive campus map
- **API Key Authentication**: Secure access control system

## 💻 System Architecture

The system offers dual implementations for flexibility:

### Standard Implementation
- **Backend**: Python Flask server with TF-IDF retrieval system
- **AI Engine**: Integrates with Ollama/Mistral for natural language understanding
- **Frontend**: Responsive Flutter mobile application with modern UI
- **Database**: Pre-processed handbook data in optimized CSV format

### Advanced Implementation
- **Backend**: FastAPI server with LangChain for advanced RAG pipeline
- **Vector Database**: FAISS for efficient semantic searching
- **AI Engine**: Compatible with multiple LLM providers
- **Authentication**: Secure API key system

## 🔄 UI Features

- **Chat Interface**: Clean, modern messaging UI with conversation bubbles
- **History Sidebar**: Access previous questions through convenient drawer menu
- **Campus Map**: Interactive map with custom theme color integration
- **Responsive Design**: Optimized for Android devices

## 🚀 Installation & Setup

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space
- **OS**: Windows 10/11, macOS, or Linux
- **Mobile**: Android 6.0+ (for mobile app)

### Prerequisites

1. **Python Environment**
   - Python 3.9+ required
   - Basic Flask implementation:
     ```
     pip install flask flask-cors pandas scikit-learn numpy requests
     ```
   - Advanced FastAPI implementation:
     ```
     pip install fastapi uvicorn langchain sentence-transformers faiss-cpu
     ```

2. **LLM Setup**
   - Basic: Download Ollama from [ollama.com/download](https://ollama.com/download)
     ```
     ollama pull mistral
     ```
   - Advanced: Configure API key for chosen LLM provider

3. **Data Preparation**
   - Basic: Ensure handbook data is available at:
     ```
     lib/server/data/handbook.csv
     ```
   - Advanced: Process documents for vector embedding:
     ```
     python vector_ingestion.py
     ```

4. **Flutter Setup**
   - Install from [flutter.dev](https://flutter.dev/docs/get-started/install)
   - Get dependencies:
     ```
     flutter pub get
     ```

## 🔧 Running the Application

### Basic Implementation

1. **Start Ollama**
   - Launch the Ollama application

2. **Start the Flask Backend**
   ```
   cd lib/server
   python app.py
   ```
   - Server will run on http://localhost:8000

### Advanced Implementation

1. **Start the FastAPI Backend**
   ```
   cd backend
   uvicorn main:app --reload
   ```
   - Server will run on http://localhost:8000

### Launch the Frontend

```
flutter run
```

## 🧪 Testing

The system has been thoroughly tested using:

- **Python requests library** - For API endpoint validation
- **curl** - For HTTP request testing
- **PowerShell commands** - For environment verification
- **Direct server execution** - For validating server functionality
- **Manual code review** - For quality assurance
- **Flutter testing** - For UI validation

## 📚 Documentation

### Basic API Endpoints

- `GET /api/health` - Check server status
- `POST /api/chat` - Submit questions and receive answers

### Advanced API Endpoints

- `GET /docs` - FastAPI auto-generated documentation
- `POST /api/query` - RAG-based question answering with vector search
- `GET /api/validate` - Validate API key authentication

### Sample Usage

```json
// Request
POST /api/chat
{
  "message": "What are the admission requirements?"
}

// Response
{
  "response": "Based on the USTP Student Handbook:\n\nFollowing the selective admission policy of the university, students must satisfy all the requirements prescribed by their college/department, aside from the minimum requirements for each level as indicated below:\n1. Pass the Admission Test\n2. With Good Moral Character"
}
```

## 🔍 Troubleshooting

- **Server Connection Issues**: Ensure backend server is running and ports are not blocked
- **Slow Responses**: First query is typically slower as the AI model loads
- **Authentication Errors**: Verify API key is properly configured
- **UI Issues**: Ensure Flutter dependencies are up to date

## 👥 Credits

Developed by **AbatuComp** for the USTP community.

## 📝 License

This project is intended for educational purposes at the University of Science and Technology of the Philippines (USTP).
