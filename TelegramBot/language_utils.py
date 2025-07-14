import logging
import requests
from dotenv import load_dotenv

import os



logging.basicConfig(level=logging.INFO)
load_dotenv()

FLASK_API_URL = os.getenv("FLASK_API_URL")

def get_user_language(chat_id):
    try:
        resp = requests.get(f"{FLASK_API_URL}/get_user_lang", params={"chat_id": chat_id})
        return resp.json().get("lang", "en")
    except Exception as e:
        print("❌ Failed to get language:", e)
        return "en"

def save_user_language(chat_id, lang):
    try:
        requests.post(f"{FLASK_API_URL}/set_user_lang", json={
            "chat_id": chat_id,
            "lang": lang
        })
    except Exception as e:
        print("❌ Failed to save language:", e)
