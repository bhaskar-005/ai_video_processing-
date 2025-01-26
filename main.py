import os
import urllib.request
import tarfile
import subprocess
import sys
import logging
import time
import platform


def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"Successfully installed/updated {package}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

def install_ffmpeg():
    # ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    # ffmpeg_archive = "ffmpeg-release-amd64-static.tar.xz"
    # install_path = os.path.expanduser("~/ffmpeg")

    try:
        # Download FFmpeg
        # print(f"Downloading FFmpeg from {ffmpeg_url}...")
        # urllib.request.urlretrieve(ffmpeg_url, ffmpeg_archive)

        # # Extract FFmpeg
        # print("Extracting FFmpeg...")
        # with tarfile.open(ffmpeg_archive, "r:xz") as tar:
        #     # Use extractall with a filter function to suppress the warning
        #     def no_filter(tarinfo):
        #         # This function does nothing, effectively bypassing filtering
        #         return tarinfo
        #     tar.extractall(install_path, filter=no_filter)

        # # Locate the ffmpeg binary
        # ffmpeg_bin = os.path.join(install_path, os.listdir(install_path)[0], "ffmpeg")
        # os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_bin)
        # print(f"FFmpeg installed successfully at: {os.path.dirname(ffmpeg_bin)}")
        os_name = platform.system()
        if os_name == "Linux":
            print("Installing ffmpeg on Linux...")
            # Install system dependencies for OpenCV
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
            subprocess.run(["ffmpeg", "-version"])

        elif os_name == "Windows":
            print("Windows detected. Please install ffmpeg manually or use a compatible method.")
            # Add Windows-specific instructions if needed
        elif os_name == "Darwin":
            print("macOS detected. Skipping ffmpeg setup as it is not typically required.")
        else:
            print(f"Unsupported OS: {os_name}")
        return True

    except Exception as e:
        print(f"Failed to install FFmpeg: {e}")


def install_opencv():
    """Install OpenCV with necessary dependencies"""
    try:
        os_name = platform.system()
        if os_name == "Linux":
            print("Installing OpenCV on Linux...")
            # Install system dependencies for OpenCV
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "libopencv-dev", "python3-opencv"], check=True)

            # Install Python dependencies
            install_package("opencv-python-headless")  # Headless version of OpenCV
        elif os_name == "Windows":
            print("Windows detected. Please install OpenCV manually or use a compatible method.")
            # Add Windows-specific instructions if needed
        elif os_name == "Darwin":
            print("macOS detected. Skipping libGL setup as it is not typically required.")
        else:
            print(f"Unsupported OS: {os_name}")
        return True
    except Exception as e:
        print(f"Error setting up OpenCV: {str(e)}")
        return False
    
def setup_libgl():
    try:
        os_name = platform.system()
        if os_name == "Linux":
            print("Installing libGL on Linux...")
            subprocess.run([ "sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "libgl1"], check=True)
        elif os_name == "Windows":
            print("Windows detected. Please install libGL manually or use a compatible method.")
            # Add Windows-specific instructions if needed
        elif os_name == "Darwin":
            print("macOS detected. Skipping libGL setup as it is not typically required.")
        else:
            print(f"Unsupported OS: {os_name}")
        return True
    except Exception as e:
        print(f"Error setting up libGL.so.1: {str(e)}")
        return False
    
# Install Python packages
install_package("pytube")
install_package("ffmpeg-python")
# Install FFmpeg
install_ffmpeg()
setup_libgl()
install_opencv()
print("All dependencies are installed/updated!")

print("test log store")


from flask import Flask, jsonify, send_from_directory
from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos

app = Flask(__name__)

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos")

# Configure the logging system
logging.basicConfig(
    filename='app.log',       # Log file where we store the captured output
    level=logging.INFO,       # Minimum level of logs to capture
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

class PrintCapture:
    def write(self, message):
        if message != '\n':  # To ignore empty lines
            logging.info(message)

    def flush(self):
        pass

# Redirecting stdout to capture all print statements
sys.stdout = PrintCapture()

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        # Open the log file and read its content
        with open('app.log', 'r') as file:
            logs = file.readlines()

        # Return logs as a JSON response
        return jsonify({"logs": logs})

    except Exception as e:
        return jsonify({"error": f"Could not read logs: {str(e)}"}), 500

@app.route('/videos', methods=['GET'])
def list_video_names():
    """
    Endpoint to list all video names in the video directory.
    """
    try:
        # Get the list of video files
        video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(('.mp4', '.webm'))]

        if not video_files:
            return jsonify({"message": "No videos available"}), 200

        # Return the list of video names
        return jsonify({
            "message": "Videos retrieved successfully!",
            "videos": video_files
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve videos: {str(e)}"}), 500


@app.route('/videos/<video_name>', methods=['GET'])
def serve_video(video_name):
    """
    Endpoint to serve a specific video file by name.
    """
    try:
        # Ensure the video exists
        video_path = os.path.join(VIDEO_DIR, video_name)
        if not os.path.exists(video_path):
            return jsonify({"error": "Video not found"}), 404

        # Serve the video file
        return send_from_directory(VIDEO_DIR, video_name, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Failed to serve the video: {str(e)}"}), 500


# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "The server is running!"}), 200

# Main logic
@app.route('/process', methods=['GET'])
def process_video():

    vidoeUrlType = "CUSTOM_URL" 
    videoUrl= "http://res.cloudinary.com/dcgkfql3l/video/upload/v1737891435/ybo0kxecbg3jqancog7q.mp4"
    videoResolution = "360"
    print(videoUrl)
    print("starting video download...")
    Vid = download_youtube_video(videoUrl, videoResolution, vidoeUrlType)
    print("donload status",Vid)
    if Vid:
        Vid = Vid.replace(".webm", ".mp4")
        print(f"Downloaded video and audio files successfully! at {Vid}")

        Audio = extractAudio(Vid)
        if Audio:
            print(Audio)
            transcriptions = transcribeAudio(Audio)
            print("__video Transcribe", transcriptions)
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
# process_video()