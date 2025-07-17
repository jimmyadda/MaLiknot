import os
import openai
from dotenv import load_dotenv
from io import BytesIO
import base64

load_dotenv()

# ✅ Setup OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Main function to send image to GPT
def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    # המרה ל-Base64 לתמיכה בשליחה ב-GPT API
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-vision-preview",  # חשוב: ודא שיש לך גישה למודל הזה
            messages=[
                {
                    "role": "system",
                    "content": "אתה מזהה טקסט מתמונה של רשימת קניות בכתב יד בעברית. החזר את שמות הפריטים המופיעים ברשימה בלבד, מופרדים בפסיקים."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ שגיאה בקריאת טקסט מהתמונה: {e}"
