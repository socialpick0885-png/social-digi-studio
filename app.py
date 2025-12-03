from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from video_generator import generate_video_from_text
import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return send_file("static/index.html")

@app.route("/api/generate-video", methods=["POST"])
def generate_video():
    try:
        data = request.get_json() or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Text is required"}), 400

        video_filename = f"{uuid.uuid4()}.mp4"
        video_path = generate_video_from_text(text, video_filename)

        if not os.path.exists(video_path):
            return jsonify({"error": "Video not generated"}), 500

        return send_file(video_path, mimetype="video/mp4", as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
