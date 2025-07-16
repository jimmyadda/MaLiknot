import os
import json
import openai
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image, ImageOps
from io import BytesIO
from dotenv import load_dotenv
import numpy as np

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setup Vision client
def build_google_vision_client():
    creds = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials = service_account.Credentials.from_service_account_info(creds, scopes=scopes)
    return vision.ImageAnnotatorClient(credentials=credentials)

client = build_google_vision_client()

# Light preprocessing using PIL (no OpenCV)
def preprocess_image_for_ocr(image_bytes: bytes) -> bytes:
    image = Image.open(BytesIO(image_bytes)).convert("L")  # grayscale
    image = ImageOps.autocontrast(image, cutoff=2)        # boost contrast gently

    # No binarization — just enhanced grayscale
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()

# ChatGPT cleanup for OCR mess
def refine_ocr_with_chatgpt(ocr_text: str) -> str:
    system_prompt = (
        "אתה מנקה טקסט בעברית שהתקבל מתמונה של רשימת קניות. "
        "תחזיר רק שמות פריטים, מופרדים בפסיקים."
    )
    user_input = f"טקסט מהתמונה:\n{ocr_text}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message["content"].strip()

# Final OCR function
def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    processed = preprocess_image_for_ocr(image_bytes)
    image = vision.Image(content=processed)
    context = vision.ImageContext(language_hints=["he"])
    with open("/tmp/debug-upload.jpg", "wb") as f:
        f.write(image_bytes)

    with open("/tmp/debug-cleaned.jpg", "wb") as f:
        f.write(processed)
    response = client.text_detection(image=image, image_context=context)
    raw_text = response.full_text_annotation.text.strip() if response.full_text_annotation.text else ""


    if not raw_text:
        return "[לא זוהה טקסט]"

    # Clean with GPT
    refined = refine_ocr_with_chatgpt(raw_text)
    return refined
