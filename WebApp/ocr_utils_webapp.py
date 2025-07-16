# ocr_utils.py
import json
import os
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv


load_dotenv()

def _load_google_credentials():
    path = "/tmp/gcloud-key.json"

    # Skip if the file already exists
    if not os.path.exists(path):
        raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not raw:
            raise EnvironmentError("❌ GOOGLE_CREDENTIALS_JSON is not set")

        try:
            creds = json.loads(raw)  # Validate JSON
        except Exception as e:
            raise ValueError(f"❌ Invalid JSON format: {e}")

        with open(path, "w") as f:
            f.write(json.dumps(creds))

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

_load_google_credentials()  # Run immediately when file is imported
try:
    #credentials_info = json.loads(json_creds)
    #credentials = service_account.Credentials.from_service_account_info(credentials_info)
    #client = vision.ImageAnnotatorClient(credentials=credentials)
    client = vision.ImageAnnotatorClient()
    print("🔍 Google Vision Client:", client)
    print("🔍 GOOGLE_APPLICATION_CREDENTIALS =", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    print("📄 Credentials file exists:", os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")))

except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Google Vision client: {e}")

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from an image using Google Cloud Vision OCR."""

    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Google Vision Error: {response.error.message}")

    return response.full_text_annotation.text.strip()