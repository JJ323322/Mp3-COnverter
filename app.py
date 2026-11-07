
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
import requests
import socket
import ipaddress
from urllib.parse import urlparse
from io import BytesIO

app = Flask(__name__)
CORS(app)

MAX_SIZE = 100 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_SIZE

@app.route("/")
def home():
    return "MP3 Converter is online!"

def download_video(url, destination):
    parsed = urlparse(url)

    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only HTTPS links are supported.")

    addresses = socket.getaddrinfo(
        parsed.hostname, 443, type=socket.SOCK_STREAM
    )

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("This address is not allowed.")

    response = requests.get(
        url,
        stream=True,
        timeout=30,
        allow_redirects=False
    )

    response.raise_for_status()

    if response.headers.get("Content-Type", "").split(";")[0] not in (
        "video/mp4", "application/octet-stream"
    ):
        raise ValueError("Please provide a direct MP4 video link.")

    total = 0
    with open(destination, "wb") as output:
        for chunk in response.iter_content(8192):
            total += len(chunk)
            if total > MAX_SIZE:
                raise ValueError("Video is too large.")
            output.write(chunk)

    response.close()

@app.route("/convert", methods=["POST"])
def convert():
    temp_dir = tempfile.mkdtemp()

    try:
        input_path = os.path.join(temp_dir, "input.mp4")
        output_path = os.path.join(temp_dir, "audio.mp3")

        if "video" in request.files:
            request.files["video"].save(input_path)

        elif request.is_json and request.json.get("url"):
            download_video(request.json["url"], input_path)

        else:
            return jsonify({"error": "Provide a video file or direct MP4 URL."}), 400

        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-vn",
            "-codec:a", "libmp3lame",
            "-b:a", "192k",
            output_path
        ], check=True, capture_output=True, timeout=300)

        with open(output_path, "rb") as audio:
            data = BytesIO(audio.read())

        return send_file(
            data,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="converted_audio.mp3"
        )

    except Exception as error:
        return jsonify({"error": str(error)}), 400

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
