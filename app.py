import os
from flask import Flask, request, jsonify, send_from_directory
import tensorflow as tf
import numpy as np
import pickle
import traceback
import re

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Configure app using environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

# Common programming language patterns
LANGUAGE_PATTERNS = {
    'Python': r'(def\s+\w+|import\s+\w+|from\s+\w+\s+import|class\s+\w+)',
    'Javascript': r'(function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+|class\s+\w+)',
    'Java': r'(public\s+class|private\s+\w+|protected\s+\w+|class\s+\w+)',
    'Cpp': r'(#include|using\s+namespace|void\s+\w+|int\s+main)',
    'Ruby': r'(def\s+\w+|require|module\s+\w+|class\s+\w+)',
'Go': r'(func\s+\w+|package\s+\w+|import\s+"|type\s+\w+)',
'Php': r'(<\?php|\$\w+|function\s+\w+|class\s+\w+)',
'Csharp': r'(namespace\s+\w+|using\s+\w+|class\s+\w+|public\s+\w+)',
'Typescript': r'(interface\s+\w+|type\s+\w+|class\s+\w+|function\s+\w+)',
'Swift': r'(func\s+\w+|var\s+\w+|class\s+\w+|import\s+\w+)'
}

def detect_language(code):
    max_matches = 0
    detected_lang = 'Unknown'
    
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(re.findall(pattern, code))
        if matches > max_matches:
            max_matches = matches
            detected_lang = lang
    
    return detected_lang

# Load the model and vectorizer
try:
    print("Attempting to load model...")
    model = tf.keras.models.load_model('best_ai_code_model.h5')
    print("Model loaded successfully")
    print("Attempting to load vectorizer...")
    with open('tfidf_vectorizer.pkl', 'rb') as file:
        vectorizer = pickle.load(file)
    print("Vectorizer loaded successfully!")
except Exception as e:
    print(f"Error loading model or vectorizer: {str(e)}")
    print(f"Full traceback: {traceback.format_exc()}")
    model = None
    vectorizer = None

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or vectorizer is None:
        return jsonify({
            "error": "Model or vectorizer not loaded properly. Check server logs."
        }), 500

    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({"error": "No code provided in request"}), 400
            
        code_snippet = data['code']
        print(f"Received code snippet of length: {len(code_snippet)}")
        
        # Detect programming language
        language = detect_language(code_snippet)
        
        # Vectorize the input code snippet
        print("Vectorizing code...")
        code_vectorized = vectorizer.transform([code_snippet]).toarray()
        print(f"Vectorized shape: {code_vectorized.shape}")
        
        # Make prediction
        print("Making prediction...")
        prediction = model.predict(code_vectorized)
        print(f"Raw prediction: {prediction}")
        predicted_probability = float(prediction[0][0])
        predicted_class = 1 if predicted_probability > 0.5 else 0
        
        # Calculate confidence
        confidence = predicted_probability * 100 if predicted_class == 1 else (1 - predicted_probability) * 100
        
        # Generate explanations
        explanations = []
        if predicted_class == 1:
            explanations.append(f"The model predicts this {language} code is AI-generated.")
            if len(code_snippet.split('\n')) > 10:
                explanations.append("The code is relatively long, which is common in AI-generated code.")
            if code_snippet.count('#') == 0 and language == 'python':
                explanations.append("The code lacks comments, which is sometimes characteristic of AI-generated code.")
            elif code_snippet.count('//') == 0 and language in ['javascript', 'java', 'cpp', 'typescript']:
                explanations.append("The code lacks comments, which is sometimes characteristic of AI-generated code.")
        else:
            explanations.append(f"The model predicts this {language} code is human-written.")
            if code_snippet.count('def ') > 0 and language == 'python':
                explanations.append("The code contains function definitions, which is common in human-written code.")
            elif code_snippet.count('function ') > 0 and language in ['javascript', 'typescript']:
                explanations.append("The code contains function definitions, which is common in human-written code.")
            if code_snippet.count('#') > 0 and language == 'python':
                explanations.append("The code contains comments, which is typical of human-written code.")
            elif code_snippet.count('//') > 0 and language in ['javascript', 'java', 'cpp', 'typescript']:
                explanations.append("The code contains comments, which is typical of human-written code.")
        
        return jsonify({
            'prediction': "AI Generated" if predicted_class == 1 else "Human Written",
            'confidence': float(confidence),
            'explanations': explanations,
            'language': language
        })
    
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Error during prediction: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port)
