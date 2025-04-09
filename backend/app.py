from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import tempfile
import os

app = Flask(__name__)
CORS(app)

model = whisper.load_model("tiny")  # Options: tiny, base, small, medium, large

@app.route("/transcribe", methods=["POST"])
def transcribe():
    print("📥 Request received!")

    if 'file' not in request.files:
        print("❌ No file in request")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    print("✅ File received:", file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file.save(tmp.name)
        print("💾 Saved temp file:", tmp.name)

        result = model.transcribe(tmp.name)
        print("🧠 Whisper result:", result)

        os.remove(tmp.name)

    return jsonify({"text": result["text"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
