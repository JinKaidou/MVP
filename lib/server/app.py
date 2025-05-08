# server/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from langchain.llms import Ollama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Ollama with Mistral model (you can change to any model you have)
llm = Ollama(model="mistral")

# Create a conversation template
template = """You are CampusGuide AI, a helpful assistant for university students.
You provide information about campus navigation, event schedules, and administrative processes.
You are knowledgeable, friendly, and concise in your responses.

Current conversation:
{history}
Human: {input}
AI Assistant:"""

prompt = PromptTemplate(
    input_variables=["history", "input"], 
    template=template
)

# Initialize conversation memory
memory = ConversationBufferMemory(return_messages=True)

# Create conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=prompt,
    verbose=True
)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get response from the model
    response = conversation.predict(input=user_message)
    
    return jsonify({
        'response': response
    })

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    global memory
    memory.clear()
    return jsonify({'status': 'Conversation reset successfully'})

@app.route('/api/models', methods=['GET'])
def get_models():
    # You can expand this to actually fetch from Ollama
    models = [
        {"id": "mistral", "name": "Mistral 7B"},
        {"id": "llama2", "name": "Llama 2 7B"}
    ]
    return jsonify(models)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)