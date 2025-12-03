from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
from video_generator import generate_video_from_text

app = Flask(__name__, static_folder="static")
CORS(app)


@app.route("/")
def index():
    # serve the frontend page
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/generate-video", methods=["POST"])
def generate_video():
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Text is required"}), 400

    try:
        video_path = generate_video_from_text(text, base_dir=".")
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

    filename = os.path.basename(video_path)
    return send_file(
        video_path,
        as_attachment=True,
        download_name=filename,
        mimetype="video/mp4",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
