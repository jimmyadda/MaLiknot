# ocr_utils.py
import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv


load_dotenv()


# ✅ Load credentials with scopes
def build_google_vision_client():
    creds_raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_raw:
        raise RuntimeError("❌ GOOGLE_CREDENTIALS_JSON is not set")

    creds_dict = json.loads(creds_raw)
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)

    return vision.ImageAnnotatorClient(credentials=credentials)



# Initialize once
client = build_google_vision_client()

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    image = vision.Image(content=image_bytes)

    image_context = vision.ImageContext(
        language_hints=["he"]  # ✅ ISO code for Hebrew
    )

    response = client.document_text_detection(image=image, image_context=image_context)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()
