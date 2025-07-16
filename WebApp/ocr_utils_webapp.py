# ocr_utils.py
import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv


load_dotenv()


# ✅ Build credentials from JSON string directly
def build_google_vision_client():
    creds_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_raw:
        raise RuntimeError("❌ GOOGLE_CREDENTIALS_JSON is not set")

    try:
        creds_dict = json.loads(creds_raw)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        print("✅ Google Vision Client initialized")
        return client
    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize Google Vision client: {e}")

# Initialize client ONCE
client = build_google_vision_client()


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from an image using Google Cloud Vision OCR."""

    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()

