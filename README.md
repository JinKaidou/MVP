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
- **Intuitive Interface**: Simple chat-based interaction

## 💻 System Architecture

- **Backend**: Python Flask server with advanced TF-IDF retrieval system
- **AI Engine**: Integrates with Ollama/Mistral for natural language understanding
- **Frontend**: Responsive Flutter web application with clean UI
- **Database**: Pre-processed handbook data in optimized CSV format

## 🚀 Installation & Setup

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space
- **OS**: Windows 10/11, macOS, or Linux

### Prerequisites

1. **Python Environment**
   - Python 3.9+ required
   - Install dependencies:
     ```
     pip install flask flask-cors pandas scikit-learn numpy requests
     ```

2. **Ollama Setup**
   - Download from [ollama.com/download](https://ollama.com/download)
   - Pull the Mistral model:
     ```
     ollama pull mistral
     ```

3. **Data Preparation**
   - Ensure handbook data is available at:
     ```
     lib/server/data/handbook.csv
     ```

4. **Flutter Setup**
   - Install from [flutter.dev](https://flutter.dev/docs/get-started/install)
   - Enable web support:
     ```
     flutter config --enable-web
     ```

## 🔧 Running the Application

### Launch Sequence

1. **Start Ollama**
   - Launch the Ollama application

2. **Start the Backend**
   ```
   cd lib/server
   python app.py
   ```
   - Server will run on http://localhost:8000

3. **Launch the Frontend**
   ```
   flutter run -d chrome
   ```

## 🧪 Testing

The system has been thoroughly tested using:

- **Python requests library** - For API endpoint validation
- **curl** - For HTTP request testing
- **PowerShell commands** - For environment verification
- **Direct server execution** - For validating server functionality
- **Manual code review** - For quality assurance

## 📚 Documentation

### API Endpoints

- `GET /api/health` - Check server status
- `POST /api/chat` - Submit questions and receive answers

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

- **Server Connection Issues**: Ensure Ollama is running and ports are not blocked
- **Slow Responses**: First query is typically slower as the AI model loads
- **Missing Information**: Verify the handbook CSV is properly formatted

## 👥 Credits

Developed by **AbatuComp** for the USTP community.

## 📝 License

This project is intended for educational purposes at the University of Science and Technology of the Philippines (USTP).
