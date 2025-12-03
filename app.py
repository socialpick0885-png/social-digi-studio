import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from video_generator import generate_video_from_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

os.makedirs(MEDIA_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static")
CORS(app)


@app.route("/api/generate-video", methods=["POST"])
def api_generate_video():
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Text is required"}), 400

    try:
        filename = f"video_{uuid.uuid4().hex}.mp4"
        video_path = generate_video_from_text(text, filename)

        # sirf filename browser ko denge
        video_url = "/media/" + os.path.basename(video_path)
        return jsonify({"status": "ok", "videoUrl": video_url})
    except Exception as e:
        # Render logs me dekhne ke liye
        print("Error while generating video:", repr(e), flush=True)
        return jsonify({"error": "Video not generated"}), 500


@app.route("/media/<path:filename>")
def media_files(filename):
    # yahi se video download hoga
    return send_from_directory(MEDIA_DIR, filename, as_attachment=True)


@app.route("/")
def index():
    # static/index.html
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
