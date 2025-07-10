# telegram_utils.py
import re
import requests

TELEGRAM_BOT_TOKEN = '7807618025:AAGKA3jxR2qFsA1F5yfkbaJuqJo40GW5kFs'

def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()

def extract_chat_id(list_name):
    match = re.search(r'\b\d{7,}\b', list_name)
    return match.group() if match else None
