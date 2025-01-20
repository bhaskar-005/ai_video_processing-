from flask import Flask, jsonify
from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
import os
import urllib.request
import tarfile
import subprocess
import sys

app = Flask(__name__)

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"Successfully installed/updated {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

def install_ffmpeg():
    ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    ffmpeg_archive = "ffmpeg-release-amd64-static.tar.xz"
    install_path = os.path.expanduser("~/ffmpeg")

    try:
        # Download FFmpeg
        print(f"Downloading FFmpeg from {ffmpeg_url}...")
        urllib.request.urlretrieve(ffmpeg_url, ffmpeg_archive)

        # Extract FFmpeg
        print("Extracting FFmpeg...")
        with tarfile.open(ffmpeg_archive, "r:xz") as tar:
            tar.extractall(install_path)

        # Locate the ffmpeg binary
        ffmpeg_bin = os.path.join(install_path, os.listdir(install_path)[0], "ffmpeg")
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_bin)
        print(f"FFmpeg installed successfully at: {os.path.dirname(ffmpeg_bin)}")

    except Exception as e:
        print(f"Failed to install FFmpeg: {e}")


# Install Python packages
install_package("pytube")
install_package("ffmpeg-python")
# Install FFmpeg
install_ffmpeg()
print("All dependencies are installed/updated!")

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "The server is running!"}), 200

# Main logic
@app.route('/process', methods=['POST'])
def process_video():
    url = "https://www.youtube.com/watch?v=MiA-DsGumxQ&pp=ygURM21pbiBwb2RjYXN0IGNsaXA%3D"
    Vid = download_youtube_video(url)
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

                start, stop = GetHighlight(TransText)
                if start != 0 and stop != 0:
                    print(f"Start: {start} , End: {stop}")

                    Output = "Out.mp4"

                    crop_video(Vid, Output, start, stop)
                    cropped = "cropped.mp4"

                    crop_to_vertical("Out.mp4", cropped)
                    combine_videos("Out.mp4", cropped, "Final.mp4")
                else:
                    return jsonify({"error": "Error in getting highlight"}), 500
            else:
                return jsonify({"error": "No transcriptions found"}), 500
        else:
            return jsonify({"error": "No audio file found"}), 500
    else:
        return jsonify({"error": "Unable to download the video"}), 500

    return jsonify({"message": "Processing complete!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
