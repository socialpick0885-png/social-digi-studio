import os
import requests
from gtts import gTTS
import imageio_ffmpeg


def generate_video_from_text(text: str, output_filename: str) -> str:
    """
    Main function jo text se slideshow + voice-over video banata hai.
    Return: final video ka full path.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Text is empty")

    # Work folder
    folder = "media"
    os.makedirs(folder, exist_ok=True)

    # 1) Text ko chhote sentences me tod do
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if not sentences:
        sentences = [text]

    # 2) Har sentence ke liye AI image URL banao
    img_urls = _generate_image_urls(sentences)

    # 3) Images download karo
    image_paths = _download_images(img_urls, folder)
    if not image_paths:
        raise RuntimeError("Koi bhi image download nahi hui. Internet check karo.")

    # 4) Voice-over (audio) banao
    audio_path = _text_to_audio(text, os.path.join(folder, "voice.mp3"))

    # 5) Slideshow video banao (sirf images se)
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    slideshow_path = os.path.join(folder, "slideshow.mp4")
    _create_slideshow(image_paths, slideshow_path, ffmpeg_bin)

    # 6) Slideshow + audio merge karke final video
    final_path = os.path.join(folder, output_filename)
    _merge_audio_video(slideshow_path, audio_path, final_path, ffmpeg_bin)

    return final_path


def _generate_image_urls(sentences):
    urls = []
    for s in sentences:
        prompt = s + ", cinematic, high quality, illustration"
        # spaces ko %20 se replace karne ke liye simple trick
        prompt = prompt.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        urls.append(url)
    return urls


def _download_images(urls, folder):
    paths = []
    for i, url in enumerate(urls):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            path = os.path.join(folder, f"slide{i}.jpg")
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
            print("Downloaded image:", path)
        except Exception as e:
            print("Image download error:", e)
    return paths


def _text_to_audio(text, output_audio):
    print("Generating voice...")
    tts = gTTS(text=text, lang="hi")  # Hinglish style Hindi
    tts.save(output_audio)
    return output_audio


def _create_slideshow(image_paths, output_video, ffmpeg_bin):
    """
    FFmpeg ke concat file list se slideshow banata hai.
    Har image ~4 seconds ke liye dikhegi.
    """
    print("Creating slideshow...")
    folder = os.path.dirname(output_video)
    list_file = os.path.join(folder, "images.txt")

    with open(list_file, "w", encoding="utf-8") as f:
        for p in image_paths:
            f.write(f"file '{p}'\n")
            f.write("duration 4\n")
        # last frame ko hold karne ke liye ek extra 'file' line
        f.write(f"file '{image_paths[-1]}'\n")

    cmd = (
        f'"{ffmpeg_bin}" -y -f concat -safe 0 -i "{list_file}" '
        f'-vsync vfr -pix_fmt yuv420p "{output_video}"'
    )
    print("Running:", cmd)
    os.system(cmd)


def _merge_audio_video(video_path, audio_path, final_path, ffmpeg_bin):
    print("Merging video + audio...")
    cmd = (
        f'"{ffmpeg_bin}" -y '
        f'-i "{video_path}" -i "{audio_path}" '
        f'-c:v copy -c:a aac -shortest "{final_path}"'
    )
    print("Running:", cmd)
    os.system(cmd)
