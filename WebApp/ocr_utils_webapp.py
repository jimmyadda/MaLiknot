import json
import os
from google.cloud import vision
from google.oauth2 import service_account
import numpy as np
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

def preprocess_image_for_ocr(image_bytes: bytes) -> bytes:
    from PIL import ImageOps

    # Load and convert to grayscale
    image = Image.open(BytesIO(image_bytes)).convert("L")  # "L" = grayscale

    # Enhance contrast
    image = ImageOps.autocontrast(image)

    # Binarize (simple threshold)
    threshold = 100
    binarized = image.point(lambda x: 255 if x > threshold else 0, '1')

    # Convert to bytes
    buffer = BytesIO()
    binarized.convert("L").save(buffer, format="JPEG")
    return buffer.getvalue()

# Initialize Vision client once
client = build_google_vision_client()

# ✅ Final OCR function
def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    # Preprocess the image before OCR
    clean_image_bytes = preprocess_image_for_ocr(image_bytes)

    image = vision.Image(content=clean_image_bytes)
    context = vision.ImageContext(language_hints=["he"])
    response = client.text_detection(image=image, image_context=context)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()
