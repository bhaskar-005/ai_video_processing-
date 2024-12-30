from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
import os
import platform
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
    """Install FFmpeg using system-specific commands."""
    system = platform.system().lower()

    try:
        if "linux" in system:
            print("Installing FFmpeg on Linux...")
            # Install using APT for Debian/Ubuntu or YUM for RHEL-based distros
            if os.path.exists("/etc/debian_version"):
                subprocess.check_call(["sudo", "apt-get", "update"])
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "ffmpeg"])
            elif os.path.exists("/etc/redhat-release"):
                subprocess.check_call(["sudo", "yum", "install", "-y", "epel-release"])
                subprocess.check_call(["sudo", "yum", "install", "-y", "ffmpeg"])
            else:
                raise Exception("Unsupported Linux distribution.")
            print("FFmpeg installed successfully on Linux!")

        elif "windows" in system:
            print("Installing FFmpeg on Windows...")
            # Download FFmpeg zip and extract
            ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            subprocess.check_call(["powershell", "-Command", f"Invoke-WebRequest -Uri {ffmpeg_url} -OutFile ffmpeg.zip"])
            subprocess.check_call(["powershell", "-Command", "Expand-Archive -Path ffmpeg.zip -DestinationPath C:\\ffmpeg -Force"])
            ffmpeg_bin = r"C:\ffmpeg\bin"
            os.environ["PATH"] += os.pathsep + ffmpeg_bin
            print(f"FFmpeg installed successfully! Make sure `{ffmpeg_bin}` is added to your system PATH.")

        elif "darwin" in system:  # macOS
            print("Installing FFmpeg on macOS...")
            # Install using Homebrew
            subprocess.check_call(["brew", "install", "ffmpeg"])
            print("FFmpeg installed successfully on macOS!")

        else:
            raise Exception("Unsupported operating system.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing FFmpeg: {e}")
    except Exception as e:
        print(f"Installation failed: {e}")


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
