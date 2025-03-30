import os
import uuid
import time
import threading
import logging
from flask import Flask, request, jsonify, send_file
from pytubefix import YouTube
import ffmpeg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("python_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("youtube-downloader")

app = Flask(__name__)

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio_files")
os.makedirs(AUDIO_DIR, exist_ok=True)

# In-memory store for download status
download_status = {}

def download_audio_task(youtube_url, audio_id):
    try:
        logger.info(f"Starting download task for audio_id: {audio_id}")
        output_path = os.path.join(AUDIO_DIR, f"{audio_id}.mp3")
        
        # Update status to processing
        download_status[audio_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Download started"
        }
        
        def progress_callback(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            progress = ((total_size - bytes_remaining) / total_size) * 100
            logger.info(f"Download progress for {audio_id}: {round(progress, 2)}%")
            download_status[audio_id].update({
                "progress": round(progress, 2),
                "message": f"Downloading: {round(progress, 2)}%"
            })
        
        logger.info(f"Initializing YouTube object for URL: {youtube_url}")
        yt = YouTube(youtube_url, on_progress_callback=progress_callback)
        
        logger.info(f"Fetching audio stream for {audio_id}")
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            logger.error(f"No audio stream found for {audio_id}")
            download_status[audio_id] = {
                "status": "error",
                "message": "No audio stream found"
            }
            return
        
        logger.info(f"Starting download of '{yt.title}' for {audio_id}")
        temp_file = audio_stream.download(output_path=AUDIO_DIR, filename_prefix=f"temp_{audio_id}_")
        logger.info(f"Download completed to temp file: {temp_file}")
        
        # Convert to MP3 if needed
        logger.info(f"Converting file to MP3 for {audio_id}")
        download_status[audio_id]["message"] = "Converting to MP3"
        
        try:
            if not temp_file.endswith('.mp3'):
                logger.info(f"Running ffmpeg conversion for {audio_id}")
                ffmpeg.input(temp_file).output(output_path).run(overwrite_output=True, quiet=True)
                logger.info(f"Removing temp file: {temp_file}")
                os.remove(temp_file)
            else:
                logger.info(f"Renaming temp file to final output: {output_path}")
                os.rename(temp_file, output_path)
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            download_status[audio_id] = {
                "status": "error",
                "message": f"Conversion error: {str(e)}"
            }
            return
        
        # Update status to completed
        logger.info(f"Download and conversion completed for {audio_id}")
        download_status[audio_id] = {
            "status": "pending",
            "progress": 100,
            "message": "Download completed"
        }
        
        # If webhook URL is configured, notify Node.js server
        node_webhook_url = os.environ.get('NODE_WEBHOOK_URL')
        metadata = {
                    "video_id": yt.video_id,
                    "title": yt.title,
                    "author": yt.author,
                    "length": yt.length,
                    "views": yt.views,
                    "thumbnail_url": yt.thumbnail_url,
                    "publish_date": str(yt.publish_date) if yt.publish_date else None,
                    "description": yt.description,
                    "keywords": yt.keywords,
                    "channel_url": yt.channel_url,
                    "channel_id": yt.channel_id
                }
        if node_webhook_url:
            try:
                import requests
                logger.info(f"Sending webhook notification for {audio_id}")
                logger.info(f"yt data {yt}")
                requests.post(node_webhook_url, json={
                    "audio_id": audio_id,
                    "status": "pending",
                    "title": yt.title,
                    "download_url": f"/audio/{audio_id}",
                    "originalMetadata": metadata
                })
                logger.info(f"req sent.")
            except Exception as e:
                logger.error(f"Failed to send webhook: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in download task for {audio_id}: {str(e)}")
        download_status[audio_id] = {
            "status": "error",
            "message": str(e)
        }

@app.route('/download-audio', methods=['POST'])
def download_audio():
    try:
        data = request.json
        logger.info(f"Received download request: {data}")
        
        youtube_url = data.get('youtube_url')
        
        if not youtube_url:
            logger.error("Missing YouTube URL in request")
            return jsonify({"error": "YouTube URL is required"}), 400
        
        # Generate unique ID for this download
        audio_id = str(uuid.uuid4())
        logger.info(f"Generated audio_id: {audio_id} for URL: {youtube_url}")
        
        # Initialize download status
        download_status[audio_id] = {
            "status": "downloading",
            "progress": 0,
            "message": "Download queued"
        }
        
        # Start download in background thread
        thread = threading.Thread(
            target=download_audio_task,
            args=(youtube_url, audio_id),
            daemon=True
        )
        thread.start()
        logger.info(f"Started background download thread for {audio_id}")
        
        # Return the audio_id immediately
        return jsonify({
            "audio_id": audio_id,
            "status": "downloading",
            "message": "Download queued successfully"
        }), 202
    
    except Exception as e:
        logger.error(f"Error in download-audio endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download-status/<audio_id>', methods=['GET'])
def check_download_status(audio_id):
    logger.info(f"Status check for audio_id: {audio_id}")
    
    if audio_id not in download_status:
        logger.warning(f"Audio ID not found: {audio_id}")
        return jsonify({"error": "Download ID not found"}), 404
    
    status = download_status[audio_id]
    logger.info(f"Returning status for {audio_id}: {status['status']}")
    return jsonify(status), 200

@app.route('/audio/<audio_id>', methods=['GET'])
def serve_audio(audio_id):
    file_path = os.path.join(AUDIO_DIR, f"{audio_id}.mp3")
    logger.info(f"Request to serve audio file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.warning(f"Audio file not found: {file_path}")
        return jsonify({"error": "File not found"}), 404
    
    logger.info(f"Serving audio file: {file_path}")
    return send_file(file_path, mimetype="audio/mpeg")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "active_downloads": len(download_status)}), 200

if __name__ == '__main__':
    logger.info("Starting YouTube audio downloader service")
    app.run(debug=True, host='0.0.0.0', port=5000)