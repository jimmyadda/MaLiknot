# ocr_utils.py
import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
# Load credentials
json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if not json_creds:
    raise ValueError("GOOGLE_CREDENTIALS_JSON not set")

credentials_info = json.loads(json_creds)
credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

def extract_text_from_image_bytes(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f'Google Vision Error: {response.error.message}')

    return response.full_text_annotation.text
