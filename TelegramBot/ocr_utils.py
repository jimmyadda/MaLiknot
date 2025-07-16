# ocr_utils.py
import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv


load_dotenv()

# Load credentials from environment variable
json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not json_creds:
    raise EnvironmentError("❌ GOOGLE_CREDENTIALS_JSON not set")

try:
    credentials_info = json.loads(json_creds)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    print("🔍 Google Vision Client:", client)
    print("Type:", credentials_info.get("type"))
    print("Email:", credentials_info.get("client_email"))
    print("Project ID:", credentials_info.get("project_id"))
    print("Scopes:", credentials_info.get("scopes", "default"))
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Google Vision client: {e}")

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from an image using Google Cloud Vision OCR."""

    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()