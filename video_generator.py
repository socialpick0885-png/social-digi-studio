import os
import requests
from gtts import gTTS
import imageio_ffmpeg

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

# media folder hamesha bana rehna chahiye
os.makedirs(MEDIA_DIR, exist_ok=True)


def generate_video_from_text(text: str, output_filename: str) -> str:
    """
    Main function: text se slideshow + voice-over video banata hai.
    final video ka FULL path return karta hai.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty")

    # 1) Text ko sentences me tod do
    cleaned = text.replace("\n", " ")
    sentences = [s.strip() for s in cleaned.split(".") if s.strip()]
    if not sentences:
        sentences = [cleaned]

    # 2) Har sentence ke liye AI image URL
    image_urls = _generate_image_urls(sentences)

    # 3) Images download
    image_paths = _download_images(image_urls)
    if not image_paths:
        raise RuntimeError("Koi bhi image download nahi hui. Internet check karo.")

    # 4) Voice-over audio
    audio_path = _text_to_audio(text)

    # 5) Slideshow video (sirf images se)
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    slideshow_path = os.path.join(MEDIA_DIR, "slideshow.mp4")
    _create_slideshow(image_paths, slideshow_path, ffmpeg_bin)

    # 6) Slideshow + audio merge karke final video
    final_path = os.path.join(MEDIA_DIR, output_filename)
    _merge_audio_video(slideshow_path, audio_path, final_path, ffmpeg_bin)

    return final_path


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def _generate_image_urls(sentences):
    urls = []
    for s in sentences:
        prompt = s + ", cinematic, high quality, illustration"
        prompt = prompt.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        urls.append(url)
    return urls


def _download_images(urls):
    paths = []
    for i, url in enumerate(urls):
        try:
            print("Downloading:", url, flush=True)
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            path = os.path.join(MEDIA_DIR, f"slide{i}.jpg")
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
            print("Saved image:", path, flush=True)
        except Exception as e:
            print("Image download error:", e, flush=True)
    return paths


def _text_to_audio(text):
    print("Generating voice...", flush=True)
    audio_path = os.path.join(MEDIA_DIR, "voice.mp3")
    # Hinglish ke liye Hindi voice thik rahegi
    tts = gTTS(text=text, lang="hi")
    tts.save(audio_path)
    return audio_path


def _create_slideshow(image_paths, output_video, ffmpeg_bin):
    """
    FFmpeg concat file use karke simple slideshow banata hai.
    Har image ~4 second ke liye dikhegi.
    """
    print("Creating slideshow video...", flush=True)

    list_file = os.path.join(MEDIA_DIR, "images.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in image_paths:
            f.write(f"file '{p}'\n")
            f.write("duration 4\n")
        # last frame ko hold karne ke liye ek extra line
        f.write(f"file '{image_paths[-1]}'\n")

    cmd = (
        f'"{ffmpeg_bin}" -y '
        f'-f concat -safe 0 -i "{list_file}" '
        f'-vsync vfr -pix_fmt yuv420p "{output_video}"'
    )
    print("Running:", cmd, flush=True)
    exit_code = os.system(cmd)
    if exit_code != 0:
        raise RuntimeError("Slideshow video banane me error aaya.")


def _merge_audio_video(video_path, audio_path, final_path, ffmpeg_bin):
    print("Merging slideshow + audio...", flush=True)
    cmd = (
        f'"{ffmpeg_bin}" -y '
        f'-i "{video_path}" -i "{audio_path}" '
        f'-c:v copy -c:a aac -shortest "{final_path}"'
    )
    print("Running:", cmd, flush=True)
    exit_code = os.system(cmd)
    if exit_code != 0:
        raise RuntimeError("Final video merge karte waqt error aaya.")
