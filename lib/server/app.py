from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain.llms import HuggingFacePipeline

load_dotenv()

app = Flask(__name__)
CORS(app)

# Set your Hugging Face API key
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Load a smaller model locally instead of using API
model_id = "google/flan-t5-base"  # Smaller model that can run locally
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

pipe = pipeline(
    "text2text-generation",
    model=model, 
    tokenizer=tokenizer, 
    max_length=512
)

llm = HuggingFacePipeline(pipeline=pipe)

# Load the vector database
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_db = FAISS.load_local("rag_backend/faiss_index", embeddings)
retriever = vector_db.as_retriever(search_kwargs={"k": 5})  # Increased from 3

# Create prompt template
template = """You are CampusGuide AI, a helpful assistant for USTP university students.
You provide DETAILED and COMPREHENSIVE information based ONLY on the USTP Student Handbook.
When answering questions about processes like enrollment, registration, or applications:
- Include ALL steps in the correct order
- List ALL required documents and requirements
- Mention deadlines and important dates if available
- Explain the complete procedure in detail

Be friendly but thorough. Focus on giving complete information.
If the handbook doesn't contain the answer, say so politely.

Context information from the handbook:
{context}

Question: {question}

Detailed Answer:"""


PROMPT = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

# Create the RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": PROMPT}
)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get response from the RAG system
        response = qa_chain.run(user_message)
        
        return jsonify({
            'response': response
        })
    except Exception as e:
        import traceback
        print(f"DETAILED ERROR: {str(e)}")
        print(traceback.format_exc())  # This prints the full stack trace
        return jsonify({
            'response': f"Error: {str(e)}"  # Return the actual error for debugging
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)