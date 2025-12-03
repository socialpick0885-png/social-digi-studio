import os
import requests
from gtts import gTTS
import ffmpeg

def download_image(prompt, index):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        filepath = f"image_{index}.jpg"
        img = requests.get(url)
        with open(filepath, "wb") as f:
            f.write(img.content)
        return filepath
    except:
        return None

def generate_video_from_text(text):
    lines = [line.strip() for line in text.split(".") if line.strip()]
    image_files = []

    print("🖼 Downloading AI images...")
    for i, line in enumerate(lines):
        img = download_image(line, i)
        if img:
            image_files.append(img)

    if not image_files:
        raise Exception("❌ No images downloaded. Check internet connection.")

    print("🎤 Generating Voice...")
    tts = gTTS(text, lang="en")
    audio_path = "audio.mp3"
    tts.save(audio_path)

    print("🎬 Creating Video...")
    inputs = []
    for img in image_files:
        inputs.extend(["-loop", "1", "-t", "3", "-i", img])

    filter_complex = ""
    for i in range(len(image_files)):
        filter_complex += f"[{i}:v]scale=1280:720,setsar=1[v{i}];"

    for i in range(len(image_files)):
        if i == 0:
            filter_complex += f"[v{i}]"
        else:
            filter_complex += f"[v{i}]"
    filter_complex += f"concat=n={len(image_files)}:v=1:a=0,format=yuv420p[v]"

    out = ffmpeg.output(
        ffmpeg.input(audio_path),  # Audio
        v=filter_complex,
        filename="video_output.mp4",
        shortest=None
    )
    out.run(overwrite_output=True)

    return "video_output.mp4"
