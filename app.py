
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import tempfile
import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "MP3 Converter API is running!"

@app.route("/convert", methods=["POST"])
def convert():
    if "video" not in request.files:
        return jsonify({"error": "Upload a video file"}), 400

    video = request.files["video"]

    if not video.filename:
        return jsonify({"error": "No file selected"}), 400

    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, "input_video")
    output_path = os.path.join(temp_dir, "audio.mp3")

    try:
        video.save(input_path)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vn",
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                output_path
            ],
            check=True,
            capture_output=True
        )

        return send_file(
            output_path,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="converted_audio.mp3"
        )

    except Exception:
        return jsonify({"error": "Conversion failed"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
