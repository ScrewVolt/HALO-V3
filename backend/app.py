from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import tempfile
import os
import time
from dotenv import load_dotenv
from pathlib import Path

print("🔥 Launching HALO Whisper backend")

# Load .env from root folder
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_URL = "https://api.replicate.com/v1/predictions"
REPLICATE_VERSION = "cfe465e163c985e9e7c4b9e52ed31c65b6d9b4e23509212efb00f002902586e8"  # Whisper model version

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "HALO Whisper backend is running!"})

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        # Save temp audio file locally
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            file.save(tmp.name)
            temp_audio_path = tmp.name

        # Upload to temp.sh
        print("⬆️ Uploading to temp.sh...")
        try:
            with open(temp_audio_path, 'rb') as audio_file:
                upload_response = requests.put(
                    f"https://temp.sh/{os.path.basename(temp_audio_path)}",
                    data=audio_file.read(),
                    headers={"Content-Type": "application/octet-stream"}
                )
            os.remove(temp_audio_path)  # Remove only once, after successful read
        except Exception as e:
            print("❌ Upload to temp.sh crashed:", e)
            return jsonify({"error": "Upload exception occurred"}), 500

        print("📦 temp.sh response:", upload_response.status_code, upload_response.text)

        if upload_response.status_code != 200:
            print("❌ temp.sh upload failed:", upload_response.text)
            return jsonify({"error": "Upload to temp.sh failed"}), 500

        audio_url = upload_response.url
        print("✅ Uploaded audio URL:", audio_url)

        # Call Replicate
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
                transcription = poll.get("output")
                print("✅ Transcription:", transcription)
                return jsonify({"text": transcription})
            if status == "failed":
                print("❌ Whisper failed:", poll)
                return jsonify({"error": "Transcription failed"}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
