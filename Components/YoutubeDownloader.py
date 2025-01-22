import os
from pytubefix import YouTube, helpers
import ffmpeg
import subprocess
import random
import string
import time
import yt_dlp


def generate_po_token():
    """Generate a unique PO token."""
    try:
        timestamp = str(int(time.time()))
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        return f"po_token_{timestamp}_{random_str}"
    except Exception as e:
        print(f"Error generating token: {e}")
        return None


def try_ytdlp_download(url: str, resolution: str = "720"):
    """Attempt to download a YouTube video using yt-dlp."""
    try:
        print("Attempting download with yt-dlp...")
        ydl_opts = {
            'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
            'outtmpl': 'videos/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [lambda d: print(
                f"Downloading... {d.get('_percent_str', 'N/A')} at {d.get('_speed_str', 'N/A')}"
            ) if d['status'] == 'downloading' else None]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Starting yt-dlp download...")
            info_dict = ydl.extract_info(url, download=True)
            output_file = ydl.prepare_filename(info_dict)
            print(f"yt-dlp download completed successfully! File: {output_file}")
            return output_file

    except Exception as e:
        print(f"yt-dlp download failed: {str(e)}")
        return False


def try_pytubefix_download(url: str, resolution: str):
    """Fallback to downloading a YouTube video using pytubefix."""
    try:
        po_token = generate_po_token()
        if not po_token:
            print("Failed to generate PO token. Aborting...")
            return None

        helpers.token = po_token
        yt = YouTube(url, use_po_token=True)
        
        video_stream = yt.streams.filter(res=resolution+"p", type="video").first()
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not video_stream:
            print(f"No video streams found with resolution {resolution}.")
            return None

        if not os.path.exists('videos'):
            os.makedirs('videos')

        print(f"Downloading video: {yt.title}")
        video_file = video_stream.download(output_path='videos', filename_prefix="video_")

        if not video_stream.is_progressive:
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
        return None


def download_youtube_video(url, resolution="720"):
    """Main function to download a YouTube video, trying yt-dlp first, then pytubefix."""
    try:
        # Try downloading with yt-dlp
        yt_dlp_file = try_ytdlp_download(url, resolution)
        if yt_dlp_file:
            return yt_dlp_file

        # Fallback to pytubefix
        print("Falling back to pytubefix...")
        pytubefix_file = try_pytubefix_download(url, resolution)
        if pytubefix_file:
            return pytubefix_file
        else:
            print("Failed to download with both yt-dlp and pytubefix.")
            return None

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None



if __name__ == "__main__":
    youtube_url = input("Enter YouTube video URL: ")
    resolution = input("Enter desired resolution (e.g., 720): ") or "720"
    download_youtube_video(youtube_url, resolution)
