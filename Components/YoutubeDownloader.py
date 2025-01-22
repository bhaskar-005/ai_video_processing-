import os
from pytubefix import YouTube, helpers
import ffmpeg
import subprocess
import random
import string
import time

def generate_po_token():
    """Generate PO token using the local function."""
    try:
        timestamp = str(int(time.time()))
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        return f"po_token_{timestamp}_{random_str}"
    except Exception as e:
        print(f"Error generating token: {e}")
        return None
def get_video_size(stream):

    return stream.filesize / (1024 * 1024)

def download_youtube_video(url, resolution):
    try:
        po_token = generate_po_token()
        print(f"Generated PO token: {po_token}")
        if not po_token:
            print("Failed to generate PO Token. Aborting...")
            return
        
        helpers.token = po_token

        yt = YouTube(url, use_po_token=True)
        print("----------------------") 
        print(yt,"youtube data") 
        print("----------------------") 
        
        video_streams = yt.streams.filter(res=resolution, type="video").first()
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not video_streams:
            print(f"No video streams found with resolution {resolution}.")
            return

        if not os.path.exists('videos'):
            os.makedirs('videos')

        print(f"Downloading video: {yt.title}")
        video_file = video_streams.download(output_path='videos', filename_prefix="video_")
        print("----------------------") 
        print(video_streams.is_progressive)
        print("----------------------") 
        print(video_streams)
        print("----------------------") 
        if not video_streams.is_progressive:
            print("Downloading audio...")
            audio_file = audio_stream.download(output_path='videos', filename_prefix="audio_")

            print("Merging video and audio...")
            output_file = os.path.join('videos', f"{yt.title}.mp4")
            stream = ffmpeg.input(video_file)
            audio = ffmpeg.input(audio_file)
            stream = ffmpeg.output(stream, audio, output_file, vcodec='libx264', acodec='aac', strict='experimental')
            ffmpeg.run(stream, overwrite_output=True)

            os.remove(video_file)
            os.remove(audio_file)
        else:
            output_file = video_file

        
        print(f"Downloaded: {yt.title} to 'videos' folder")
        print(f"File path: {output_file}")
        return output_file

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please make sure you have the latest version of pytube and ffmpeg-python installed.")
        print("You can update them by running:")
        print("pip install --upgrade pytube ffmpeg-python")
        print("Also, ensure that ffmpeg is installed on your system and available in your PATH.")

if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    download_youtube_video(youtube_url)
