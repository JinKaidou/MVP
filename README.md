# Campus Guide AI

A smart AI assistant for USTP students that answers questions based on the Student Handbook.

## Overview

This application uses RAG (Retrieval Augmented Generation) to provide accurate information from the USTP Student Handbook. The system consists of:

- **Backend**: Python Flask server with TF-IDF retrieval and Ollama/Mistral for AI responses
- **Frontend**: Flutter web app with a chat interface

## System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space for models and code
- **OS**: Windows 10/11, macOS, or Linux

## Prerequisites

### 1. Python Setup
- Install Python 3.9 or newer
- Install required packages:
  ```
  pip install flask flask-cors pandas scikit-learn numpy requests
  ```

### 2. Ollama Setup
- Download Ollama from [ollama.com/download](https://ollama.com/download)
- Install and launch the application
- Download the Mistral model:
  ```
  ollama pull mistral
  ```

### 3. Data Setup
- Place the CSV handbook data in this location:
  ```
  lib/server/data/handbook.csv
  ```
  (The CSV should have columns like Title, Chapter, Article, Section, Content)

### 4. Flutter Setup (for frontend)
- Install Flutter SDK from [flutter.dev](https://flutter.dev/docs/get-started/install)
- Enable web support:
  ```
  flutter config --enable-web
  ```

## Running the Application

### Step 1: Start Ollama
- Launch Ollama from your applications menu
- Verify it's running (usually shows in system tray)

### Step 2: Start the Backend Server
```
cd lib/server
python app.py
```
The server will start on http://localhost:8000

### Step 3: Start the Flutter Frontend
In a new terminal:
```
flutter run -d chrome
```
This will open the app in Chrome browser.

## Troubleshooting

### Backend Issues
- **"Ollama server is not accessible"**: Make sure Ollama is running
- **"Mistral model not found"**: Run `ollama pull mistral`
- **CSV loading error**: Check the CSV file exists and has the right columns

### Frontend Issues
- **Connection error**: Ensure the backend server is running on port 8000
- **UI not loading**: Make sure Flutter web support is enabled

## Project Structure

- `lib/server/` - Backend Flask server
  - `app.py` - Main server code
  - `data/` - CSV handbook data
- `lib/` - Flutter frontend
  - `main.dart` - Main entry point
  - `screens/` - App screens
  - `services/` - API services

## Performance Notes

- First query might be slow as the model loads
- Subsequent queries should be faster
- If you experience out-of-memory errors, reduce the Ollama model parameters in app.py

## License

This project is for educational purposes at USTP.
