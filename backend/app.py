import os
import json
import pickle
import re
import ollama
import numpy as np
import fitz  # PyMuPDF for PDF text extraction
import whisper
import subprocess  # For FFmpeg conversion
from pydub import AudioSegment
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ✅ Load ML Model
with open("optimized_xgb_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# ✅ Initialize Flask
app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ✅ Allowed file types
ALLOWED_PDF = {"pdf"}
ALLOWED_AUDIO = {"mp3", "wav", "flac", "ogg", "m4a", "mp4", "dat", "unknown"}  # Support more raw audio extensions

# ✅ Required Order of Keys
REQUIRED_KEYS = ["PRG", "PL", "PR", "SK", "TS", "M11", "BD2", "Age", "Insurance"]

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# ✅ Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)
        return text, None  # Success
    except Exception as e:
        return None, str(e)  # Error

# ✅ Convert MP4 to WAV using PyDub (fallback if needed)
def convert_mp4_to_wav(mp4_path):
    print("Enter3")
    wav_path = mp4_path.replace(".mp4", ".converted.wav")
    try:
        audio = AudioSegment.from_file(mp4_path)
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        print(f"[ERROR] MP4 conversion failed: {e}")
        return None

# ✅ Convert Unknown Audio to WAV using PyDub
def convert_unknown_to_wav(input_path):
    output_path = os.path.splitext(input_path)[0] + ".converted.wav"
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        print(f"[ERROR] PyDub conversion failed: {e}")
        return None

# ✅ Extract Text from Audio
def extract_text_from_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

# ✅ Process Extracted Text with LLM
def process_with_llm(text):
    prompt = f"""
    Extract only the medical test results from the report below in structured JSON format.
    Ensure strict order: {REQUIRED_KEYS}

    Report:
    {text}

    JSON Output:
    """
    response = ollama.chat(model="llama2", messages=[{"role": "user", "content": prompt}])
    json_text = response["message"]["content"]
    match = re.search(r"\{.*?\}", json_text, re.DOTALL)
    if not match:
        return None, "Failed to extract JSON from LLM response"

    try:
        extracted_data = json.loads(match.group())
        feature_values = [
            float(extracted_data.get(key, 0.0)) if extracted_data.get(key, 0.0) not in [None, "", "NaN"]
            else 0.0 for key in REQUIRED_KEYS
        ]
        feature_values = np.array(feature_values, dtype=np.float32).reshape(1, -1)
        print(feature_values)
        prediction = model.predict(feature_values)
        print("extracted_data", extracted_data, "prediction", prediction.tolist())
        return {"extracted_data": extracted_data, "prediction": prediction.tolist()}, None
    
    except json.JSONDecodeError:
        return None, "Failed to parse JSON from LLM"

# ✅ Upload and Process PDF
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(pdf_path)

    extracted_text, error = extract_text_from_pdf(pdf_path)
    if error:
        return jsonify({"error": error}), 500

    result, error = process_with_llm(extracted_text)
    if error:
        return jsonify({"error": error}), 500

    return jsonify(result)

# ✅ Upload and Process Audio with MP4 + unknown extension Support
@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    print("Enter1")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename, ALLOWED_AUDIO):
        return jsonify({"error": "Only audio or MP4 files are allowed"}), 400

    filename = secure_filename(file.filename)
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(audio_path)

    file_extension = filename.split(".")[-1].lower()
    if file_extension == "mp4":
        print("Enter2")
        audio_path = convert_mp4_to_wav(audio_path)
    elif file_extension in ["dat", "unknown"]:
        audio_path = convert_unknown_to_wav(audio_path)

    if not audio_path or not os.path.exists(audio_path):
        return jsonify({"error": "Failed to convert audio to WAV"}), 500

    try:
        extracted_text = extract_text_from_audio(audio_path)
        result, error = process_with_llm(extracted_text)
        if error:
            return jsonify({"error": error}), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
