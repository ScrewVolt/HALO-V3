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
REPLICATE_VERSION = "cfe465e163c985e9e7c4b9e52ed31c65b6d9b4e23509212efb00f002902586e8"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "HALO Whisper backend is running!"})

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        # Save audio locally
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            file.save(tmp.name)
            temp_audio_path = tmp.name

        print("⬆️ Uploading to Replicate upload API...")
        try:
            with open(temp_audio_path, 'rb') as audio_file:
                upload_response = requests.post(
                    "https://dreambooth-api-experimental.replicate.com/v1/upload",
                    headers={
                        "Authorization": f"Token {REPLICATE_API_TOKEN}",
                    },
                    files={"file": (os.path.basename(temp_audio_path), audio_file, "audio/webm")}
                )
            os.remove(temp_audio_path)
        except Exception as e:
            print("❌ Upload to Replicate failed:", e)
            return jsonify({"error": "Upload to Replicate failed"}), 500

        if not upload_response.ok:
            print("❌ Replicate upload failed")
            print("🔁 Response status:", upload_response.status_code)
            print("🔁 Response body:", upload_response.text)
            return jsonify({"error": f"Upload failed: {upload_response.text}"}), 500


        audio_url = upload_response.json().get("url")
        print("✅ Uploaded to Replicate:", audio_url)

        # Call Replicate Whisper
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
            print("❌ Replicate Whisper request failed:", replicate_response.text)
            return jsonify({"error": "Replicate Whisper API call failed"}), 500

        prediction = replicate_response.json()
        prediction_id = prediction["id"]
        result_url = f"{REPLICATE_URL}/{prediction_id}"

        print(f"📡 Polling transcription from: {result_url}")

        while True:
            time.sleep(1.5)
            poll = requests.get(result_url, headers=headers).json()
            status = poll.get("status")
            if status == "succeeded":
                transcription = poll.get("output")
                print("✅ Transcription:", transcription)
                return jsonify({"text": transcription})
            if status == "failed":
                print("❌ Whisper transcription failed:", poll)
                return jsonify({"error": "Transcription failed"}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
