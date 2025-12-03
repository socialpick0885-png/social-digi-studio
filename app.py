from flask import Flask, request, jsonify
from video_generator import generate_slideshow_video
import uuid
import os

app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    script = data.get("script")

    if not script:
        return jsonify({"error": "Script missing"}), 400

    filename = f"static/video_{uuid.uuid4()}.mp4"
    video_path = generate_slideshow_video(script, filename)

    return jsonify({
        "status": "ok",
        "videoUrl": request.host_url + video_path
    })

@app.route("/")
def home():
    return "Video generator is running!"

if __name__ == "__main__":
    app.run()
