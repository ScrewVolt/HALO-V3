from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import tempfile
import os
import time
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root folder
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = Flask(__name__)
CORS(app)  # Allow requests from frontend (localhost, Netlify, etc.)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_URL = "https://api.replicate.com/v1/predictions"
REPLICATE_VERSION = "cfe465e163c985e9e7c4b9e52ed31c65b6d9b4e23509212efb00f002902586e8"  # Whisper v1.4.0

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "HALO Whisper backend is running!"})

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            file.save(tmp.name)
            temp_audio_path = tmp.name

        # Upload to file.io
        with open(temp_audio_path, 'rb') as audio_file:
            upload_response = requests.post("https://file.io", files={"file": audio_file})
        os.remove(temp_audio_path)

        if not upload_response.ok:
            print("❌ Upload failed:", upload_response.text)
            return jsonify({"error": "Failed to upload audio"}), 500

        audio_url = upload_response.json().get("link")
        print("🎧 Uploaded to:", audio_url)

        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        data = {
            "version": REPLICATE_VERSION,
            "input": { "audio": audio_url }
        }

        replicate_response = requests.post(REPLICATE_URL, json=data, headers=headers)
        if not replicate_response.ok:
            print("❌ Replicate error:", replicate_response.text)
            return jsonify({"error": "Replicate API call failed"}), 500

        prediction = replicate_response.json()
        prediction_id = prediction["id"]
        result_url = f"{REPLICATE_URL}/{prediction_id}"

        # Poll for result
        while True:
            time.sleep(1.5)
            poll = requests.get(result_url, headers=headers).json()
            status = poll.get("status")

            if status == "succeeded":
                print("✅ Transcription:", poll["output"])
                return jsonify({"text": poll["output"]})

            if status == "failed":
                print("❌ Whisper failed:", poll)
                return jsonify({"error": "Transcription failed"}), 500

    except Exception as e:
        print("🔥 Unexpected error:", e)
        return jsonify({"error": "Server error"}), 500

# Bind to Render port or default local port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
