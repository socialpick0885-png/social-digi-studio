import os
import requests
from gtts import gTTS
import ffmpeg
import uuid

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def get_images_from_pexels(query):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, headers=headers)
    data = res.json()
    images = [photo["src"]["medium"] for photo in data["photos"]]
    return images

def generate_video(text):
    sentences = [s.strip() for s in text.split("\n") if s.strip()]
    media_folder = "media"
    os.makedirs(media_folder, exist_ok=True)

    # Create unique video name
    video_id = str(uuid.uuid4())
    audio_path = f"{media_folder}/voice_{video_id}.mp3"
    final_video = f"{media_folder}/video_{video_id}.mp4"

    # Generate voice
    tts = gTTS(text=text, lang='hi')
    tts.save(audio_path)

    # Download images
    image_list = []
    for i, line in enumerate(sentences):
        images = get_images_from_pexels(line)
        if not images:
            continue
        img_data = requests.get(images[0]).content
        img_path = f"{media_folder}/img_{i}.jpg"
        with open(img_path, "wb") as img_file:
            img_file.write(img_data)
        image_list.append(img_path)

    # Create slideshow
    input_txt = f"{media_folder}/images.txt"
    with open(input_txt, "w") as f:
        for img in image_list:
            f.write(f"file '{img}'\n")
            f.write("duration 2\n")

    slideshow = f"{media_folder}/slideshow_{video_id}.mp4"
    ffmpeg.input(input_txt, format="concat", safe=0).output(slideshow, vsync=2, pix_fmt="yuv420p").run()

    # Merge voice + video
    ffmpeg.input(slideshow).input(audio_path).output(final_video, vcodec="copy", acodec="aac", shortest=None).run()

    return final_video
