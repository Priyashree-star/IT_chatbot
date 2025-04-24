from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-1.5-flask')

# In-memory store for image context and history
image_context_store = {}

# Utility: Encode image as base64
def encode_image(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

@app.route('/upload-image', methods=['POST'])
def upload_image():
    image = request.files.get('image')
    if not image:
        return jsonify({"error": "Image file is required"}), 400

    filepath = os.path.join("uploads", image.filename)
    os.makedirs("uploads", exist_ok=True)
    image.save(filepath)

    image_base64 = encode_image(filepath)

    response = model.generate_content([
        {"mime_type": "image/png", "data": image_base64},
        "You are a scientific visual analysis expert. Analyze the image and describe everything you observe clearly. Store this as context for further questions."
    ])

    result_text = response.text.strip()

    image_context_store[image.filename] = {
        "description": result_text,
        "timestamp": datetime.now().isoformat(),
        "history": []
    }

    return jsonify({
        "filename": image.filename,
        "summary": result_text
    })

@app.route('/ask-image/<filename>', methods=['POST'])
def ask_image_question(filename):
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    context = image_context_store.get(filename)
    if not context:
        return jsonify({"error": "No context found for that image"}), 404

    history = context.get("history", [])
    history_text = "\n".join([f"Q: {pair['q']}\nA: {pair['a']}" for pair in history])

    full_prompt = f"""You previously analyzed this image as:
{context['description']}

Continue answering questions about this image.
Here is a summary of past questions and answers:
{history_text}

Now, answer clearly and completely:
Q: {question}
A:"""

    response = model.generate_content(full_prompt)
    answer = response.text

    context["history"].append({ "q": question, "a": answer })

    return jsonify({ "answer": answer })

@app.route('/image-context/<filename>', methods=['GET'])
def get_image_context(filename):
    context = image_context_store.get(filename)
    if not context:
        return jsonify({"error": "No context found for that image"}), 404
    return jsonify(context)

@app.route('/reset-image/<filename>', methods=['POST'])
def reset_image_memory(filename):
    if filename in image_context_store:
        image_context_store[filename]["history"] = []
        return jsonify({"status": "context cleared"})
    return jsonify({"error": "Image not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "image-analyzer"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
