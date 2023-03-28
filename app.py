from flask import Flask, request, jsonify
from main import process_image, save_to_google_drive, get_credentials
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        image_file = request.files.get("image")
        if image_file:
            image = Image.open(image_file.stream)
            sub_images = process_image(image)
            saved_file_ids = save_to_google_drive(sub_images, OUTPUT_FOLDER_ID, credentials)
            return jsonify({"file_ids": saved_file_ids})
        else:
            return jsonify({"error": "No image file found in the request"})
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
