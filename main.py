from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
import os
import subprocess
import sys

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"Successfully installed/updated {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

def install_ffmpeg():
    """Download and install FFmpeg automatically."""
    import platform
    import shutil
    import urllib.request
    import zipfile

    # Determine the OS
    system = platform.system().lower()
    ffmpeg_url = ""

    if system == "windows":
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    elif system == "darwin":  # macOS
        ffmpeg_url = "https://evermeet.cx/ffmpeg/ffmpeg.zip"
    elif system == "linux":
        ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    else:
        print("Unsupported OS for automatic FFmpeg installation.")
        return

    try:
        # Download FFmpeg
        print("Downloading FFmpeg...")
        ffmpeg_archive = "ffmpeg_download"
        urllib.request.urlretrieve(ffmpeg_url, ffmpeg_archive)

        # Extract FFmpeg
        print("Extracting FFmpeg...")
        if ffmpeg_url.endswith(".zip"):
            with zipfile.ZipFile(ffmpeg_archive, "r") as zip_ref:
                zip_ref.extractall("ffmpeg")
        elif ffmpeg_url.endswith(".xz"):
            import tarfile
            with tarfile.open(ffmpeg_archive, "r:xz") as tar_ref:
                tar_ref.extractall("ffmpeg")

        # Move FFmpeg binary to PATH
        ffmpeg_dir = os.path.join("ffmpeg", "ffmpeg") if system == "darwin" else "ffmpeg"
        ffmpeg_bin = os.path.join(ffmpeg_dir, "bin", "ffmpeg") if os.path.exists(os.path.join(ffmpeg_dir, "bin")) else os.path.join(ffmpeg_dir, "ffmpeg")

        # Move to a directory in PATH (e.g., /usr/local/bin or ~/.local/bin)
        target_dir = os.path.expanduser("~/.local/bin")
        os.makedirs(target_dir, exist_ok=True)
        shutil.move(ffmpeg_bin, os.path.join(target_dir, "ffmpeg"))
        print("FFmpeg installed successfully!")

        # Add FFmpeg to PATH
        os.environ["PATH"] += os.pathsep + target_dir
        print("FFmpeg has been added to PATH.")
    except Exception as e:
        print(f"Failed to install FFmpeg: {e}")
    finally:
        # Cleanup
        if os.path.exists(ffmpeg_archive):
            os.remove(ffmpeg_archive)
        if os.path.exists("ffmpeg"):
            shutil.rmtree("ffmpeg")


# Install Python packages
install_package("pytube")
install_package("ffmpeg-python")
# Install FFmpeg
install_ffmpeg()
print("All dependencies are installed/updated!")

url = "https://www.youtube.com/watch?v=y5MVHmMJ-8o"
Vid= download_youtube_video(url)
if Vid:
    Vid = Vid.replace(".webm", ".mp4")
    print(f"Downloaded video and audio files successfully! at {Vid}")

    Audio = extractAudio(Vid)
    if Audio:

        transcriptions = transcribeAudio(Audio)
        if len(transcriptions) > 0:
            TransText = ""

            for text, start, end in transcriptions:
                TransText += (f"{start} - {end}: {text}")

            start , stop = GetHighlight(TransText)
            if start != 0 and stop != 0:
                print(f"Start: {start} , End: {stop}")

                Output = "Out.mp4"

                crop_video(Vid, Output, start, stop)
                croped = "croped.mp4"

                crop_to_vertical("Out.mp4", croped)
                combine_videos("Out.mp4", croped, "Final.mp4")
            else:
                print("Error in getting highlight")
        else:
            print("No transcriptions found")
    else:
        print("No audio file found")
else:
    print("Unable to Download the video")
