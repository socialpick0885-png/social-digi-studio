import os
import uuid
import requests

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import imageio_ffmpeg
from openai import OpenAI

# Use imageio-ffmpeg's ffmpeg binary
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

# OpenAI client (for voice)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pexels API key from environment
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def fetch_images_from_pexels(prompt: str, count: int = 3):
    """
    Search images from Pexels based on the script text.
    Falls back to a default image if anything fails.
    """
    fallback = [
        "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg"
    ]

    if not PEXELS_API_KEY:
        print("PEXELS_API_KEY not set, using fallback image.", flush=True)
        return fallback

    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": prompt, "per_page": count},
            headers={"Authorization": PEXELS_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos") or []

        urls = []
        for p in photos:
            src = p.get("src") or {}
            url = src.get("large") or src.get("medium") or src.get("original")
            if url:
                urls.append(url)

        if not urls:
            print("No images from Pexels, using fallback.", flush=True)
            return fallback

        return urls[:count]
    except Exception as e:
        print("Error fetching from Pexels:", e, flush=True)
        return fallback


def download_image(url: str, dest_path: str):
    resp = requests.get(url, stream=True, timeout=20)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)


def generate_voice(script: str, out_path: str):
    """
    Generate speech audio from script using OpenAI TTS.
    """
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=script,
        format="mp3",
    ) as response:
        response.stream_to_file(out_path)


def generate_slideshow_video(script: str) -> str:
    """
    Main function:
    - creates media/ folder
    - fetches images from Pexels
    - generates voice audio
    - builds slideshow video
    - returns absolute path of final mp4
    """
    media_dir = os.path.join(os.getcwd(), "media")
    os.makedirs(media_dir, exist_ok=True)

    video_id = uuid.uuid4().hex[:16]

    # 1) Generate voice
    audio_path = os.path.join(media_dir, f"voice_{video_id}.mp3")
    print("Generating voice...", flush=True)
    generate_voice(script, audio_path)

    # 2) Get images
    print("Fetching images from Pexels...", flush=True)
    image_urls = fetch_images_from_pexels(script, count=3)

    clips = []
    # Simple duration rule: at least 4s per slide
    slide_duration = max(4, int(len(script.split()) / 10))

    for idx, url in enumerate(image_urls):
        img_path = os.path.join(media_dir, f"slide_{video_id}_{idx}.jpg")
        try:
            print(f"Downloading image {idx+1}: {url}", flush=True)
            download_image(url, img_path)
            clip = ImageClip(img_path).set_duration(slide_duration)
            clips.append(clip)
        except Exception as e:
            print("Failed to download/use image:", e, flush=True)

    if not clips:
        raise RuntimeError("No images available for slideshow")

    print("Creating video clips...", flush=True)
    video = concatenate_videoclips(clips, method="compose")

    # 3) Attach audio
    print("Attaching audio...", flush=True)
    audio_clip = AudioFileClip(audio_path)
    video = video.set_audio(audio_clip)

    # 4) Export final video
    video_path = os.path.join(media_dir, f"video_{video_id}.mp4")
    print(f"Writing final video to {video_path}", flush=True)
    video.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=os.path.join(media_dir, f"temp-audio-{video_id}.m4a"),
        remove_temp=True,
        ffmpeg_params=["-loglevel", "error"],
    )

    # Cleanup moviepy objects
    video.close()
    audio_clip.close()
    for c in clips:
        c.close()

    return video_path
