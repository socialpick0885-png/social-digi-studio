import os
import requests
from gtts import gTTS
from moviepy.editor import *
from PIL import Image
from io import BytesIO

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def get_images_from_pexels(query, limit=5):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={limit}"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)

    data = response.json()
    return [photo["src"]["large"] for photo in data["photos"]]

def generate_slideshow_video(script, output_path="static/video.mp4"):
    paragraphs = script.split(".")
    queries = [p.strip() for p in paragraphs if len(p.strip()) > 3]

    images = []
    for q in queries:
        urls = get_images_from_pexels(q, 1)
        if urls:
            images.append(urls[0])

    clips = []
    for img_url in images:
        img = Image.open(BytesIO(requests.get(img_url).content))
        img = img.convert("RGB")
        temp = "temp.jpg"
        img.save(temp)
        clip = ImageClip(temp).set_duration(3)
        clips.append(clip)

    audio = gTTS(script, lang="hi")
    audio_file = "voice.mp3"
    audio.save(audio_file)

    slideshow = concatenate_videoclips(clips, method="compose")
    audio_clip = AudioFileClip(audio_file)
    slideshow = slideshow.set_audio(audio_clip)

    slideshow.write_videofile(output_path, fps=30)
    return output_path
