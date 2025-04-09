from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import tempfile
import os
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = Flask(__name__)
CORS(app)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

REPLICATE_URL = "https://api.replicate.com/v1/predictions"
REPLICATE_VERSION = "cfe465e163c985e9e7c4b9e52ed31c65b6d9b4e23509212efb00f002902586e8"  # Whisper model version

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    # Save temp audio file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        temp_audio_path = tmp.name

    # Upload the file to file.io (or use your own uploader if needed)
    with open(temp_audio_path, 'rb') as audio_file:
        upload_response = requests.post("https://file.io", files={"file": audio_file})

    os.remove(temp_audio_path)  # clean up

    if not upload_response.ok:
        return jsonify({"error": "Failed to upload audio file"}), 500

    audio_url = upload_response.json().get("link")
    print("🎧 Uploaded audio URL:", audio_url)

    # Call Replicate Whisper
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "version": REPLICATE_VERSION,
        "input": {
            "audio": audio_url
        }
    }

    replicate_response = requests.post(REPLICATE_URL, json=data, headers=headers)
    if not replicate_response.ok:
        print("❌ Replicate request failed:", replicate_response.text)
        return jsonify({"error": "Replicate API call failed"}), 500

    prediction = replicate_response.json()
    prediction_id = prediction["id"]

    # Poll until transcription is complete
    result_url = f"{REPLICATE_URL}/{prediction_id}"

    while True:
        status_response = requests.get(result_url, headers=headers).json()
        status = status_response.get("status")

        if status == "succeeded":
            transcription = status_response["output"]
            print("✅ Transcription result:", transcription)
            return jsonify({"text": transcription})

        elif status == "failed":
            print("❌ Transcription failed:", status_response)
            return jsonify({"error": "Whisper failed"}), 500
import os
port = int(os.environ.get("PORT", 5000))  # fallback to 5000 for local dev
app.run(host="0.0.0.0", port=port)
