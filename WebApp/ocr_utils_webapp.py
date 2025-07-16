import json
import os
from google.cloud import vision
from google.oauth2 import service_account
import cv2
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

# ✅ Preprocess image before OCR (improves handwriting recognition)
def preprocess_image_for_ocr(image_bytes: bytes) -> bytes:
    # Load image from bytes
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    open_cv_image = np.array(image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()  # Convert RGB to BGR for OpenCV

    # Convert to grayscale
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive thresholding (for uneven lighting/handwriting)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    # Invert for OCR: black text on white background
    inverted = cv2.bitwise_not(thresh)

    # Convert back to bytes
    processed_pil = Image.fromarray(inverted)
    buffer = BytesIO()
    processed_pil.save(buffer, format="JPEG")
    return buffer.getvalue()

# Initialize Vision client once
client = build_google_vision_client()

# ✅ Final OCR function
def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    # Preprocess the image before OCR
    clean_image_bytes = preprocess_image_for_ocr(image_bytes)

    image = vision.Image(content=clean_image_bytes)

    image_context = vision.ImageContext(
        language_hints=["he"]  # Target Hebrew handwriting
    )

    response = client.document_text_detection(image=image, image_context=image_context)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()
