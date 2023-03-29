import io
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
OUTPUT_FOLDER_ID = os.getenv('OUTPUT_FOLDER_ID')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE')

POLL_INTERVAL = 60  # Time in seconds between folder polls

# Function to split and upscale images
def process_image(image):
    width, height = image.size
    sub_images = []

    for i in range(2):
        for j in range(2):
            box = (j * width // 2, i * height // 2, (j + 1) * width // 2, (i + 1) * height // 2)
            sub_image = image.crop(box).resize((2480, 2480), Image.LANCZOS)
            sub_images.append(sub_image)

    return sub_images

# Function to save images to Google Drive
def save_to_google_drive(images, original_filename, folder_id, credentials):
    service = build('drive', 'v3', credentials=credentials)

    for i, image in enumerate(images):
        file_metadata = {
            'name': f'{original_filename}{i+1}.png',
            'parents': [folder_id],
        }

        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        media = MediaIoBaseUpload(image_bytes, mimetype='image/png', resumable=True)

        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f'Saved file {file.get("id")}')

def listen_and_process_images(main_folder_id, output_folder_id, to_send_printful_folder_id, credentials, private_token):
    processed_files = set()

    while True:
        service = build('drive', 'v3', credentials=credentials)

        # Listen to the main_folder_id for new images to split and upscale
        query_main = f"'{main_folder_id}' in parents"
        process_main_folder_images(service, query_main, output_folder_id, processed_files, credentials)

        time.sleep(POLL_INTERVAL)

def process_main_folder_images(service, query, output_folder_id, processed_files, credentials):
    results = service.files().list(q=query, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found in the main folder.')
    else:
        for item in items:
            file_id = item['id']
            file_name = item['name']
            if file_id not in processed_files:
                request = service.files().get_media(fileId=file_id)
                file_data = io.BytesIO(request.execute())

                image = Image.open(file_data)
                sub_images = process_image(image)
                save_to_google_drive(sub_images, file_name, output_folder_id, credentials)

                processed_files.add(file_id)

def get_credentials():
    return service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE)

# Main function
def main():
    credentials = get_credentials()
    listen_and_process_images(GOOGLE_DRIVE_FOLDER_ID, OUTPUT_FOLDER_ID, credentials)

if __name__ == '__main__':
    main()