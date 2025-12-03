import os
from flask import Flask, request, jsonify, send_from_directory
from video_generator import generate_slideshow_video

app = Flask(__name__, static_folder="static", static_url_path="")

@app.route("/")
def index():
    # Serve the frontend from /static/index.html
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/generate-video", methods=["POST"])
def api_generate_video():
    data = request.get_json() or {}
    script = (data.get("script") or "").strip()

    if not script:
        return jsonify({"status": "error", "message": "Script is required."}), 400

    try:
        video_path = generate_slideshow_video(script)

        # Convert absolute path -> relative URL
        rel_path = os.path.relpath(video_path, os.getcwd())
        url = "/" + rel_path.replace("\\", "/")

        return jsonify({"status": "ok", "videoUrl": url})
    except Exception as e:
        print("Error generating video:", e, flush=True)
        return jsonify({"status": "error", "message": "Failed to generate video."}), 500


# Serve files from the media/ folder (important!)
@app.route("/media/<path:filename>")
def media_files(filename):
    media_path = os.path.join(os.getcwd(), "media")
    return send_from_directory(media_path, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
