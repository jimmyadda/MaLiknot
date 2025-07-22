# telegram_utils.py
import os
import re
import requests
from dotenv import load_dotenv

from messages import get_message
from user_settings import get_user_language

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_telegram_message(chat_id, message=None, key=None, lang=None, **kwargs):
    if not message and key:
        lang = lang or get_user_language(chat_id)
        message = get_message(key, lang, **kwargs)
        print("send_telegram_message",key, lang,message)

        if not message:
            print(f"❌ No message found for key={key}, lang={lang}, chat_id={chat_id}")
            return {"error": "no_message"}
    if not chat_id:
        print("❌ Missing chat_id")
        return {"error": "missing_chat_id"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    print("response : ",response , url, payload)
    return response.json()

def extract_chat_id(list_name):
    match = re.search(r'\b\d{7,}\b', list_name)
    return match.group() if match else None
